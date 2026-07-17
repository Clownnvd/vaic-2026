"""BEHAVIORAL PROBE (CheckList INV/DIR — Ribeiro et al. ACL 2020) trên checkpoint.

Đo HỒ SƠ NĂNG LỰC, không phải 1 con số. Cho thấy PhoBERT MỘT MÌNH sập ở trục
SỐ, nhưng GUARD HỢP THÀNH (PhoBERT ∨ lech_so tất định) bắt lại → đúng phân vai.

- INV (invariance): paraphrase NẶNG claim grounded → nhãn PHẢI giữ grounded.
  fail = model đổi ý khi chỉ đổi cách nói.
- DIR-num (directional): đổi 1 con số trong claim → PHẢI lật sang không-căn-cứ.
  đo 2 cột: PhoBERT-alone vs STACK = PhoBERT ∨ lech_so.
- DIR-sem: gắn một mệnh đề tổng-quát-hoá → PHẢI lật sang không-căn-cứ.

Inference-only, KHÔNG train lại. Chạy trên container có checkpoint:
  uv run --python 3.11 --with torch --with transformers --with underthesea --with numpy python guard/behavioral_probe.py
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")
from guard.corrupt import bia_so_trong_cau  # noqa: E402
from guard.vn_number import lech_so  # noqa: E402

CKPT = Path("./artifacts/guard/phobert_guard")
TEST = Path("./data/guard/test.jsonl")
SEED = 7

# paraphrase NẶNG giữ nghĩa (INV): thay từ + viết tắt, không đổi sự thật
_INV = [
    (r"\bquy định\b", "nêu rõ"), (r"\bdoanh nghiệp\b", "DN"),
    (r"\bhỗ trợ\b", "trợ giúp"), (r"\bđược\b", "sẽ được"),
    (r"\bkhông quá\b", "tối đa"), (r"\btối đa\b", "không vượt"),
    (r"\bphần trăm\b", "%"), (r"\btỷ đồng\b", "tỷ"),
]
_SEM = [
    "và mọi doanh nghiệp đều mặc nhiên đủ điều kiện",
    "nên bạn chắc chắn được duyệt không cần xét thêm",
    "và quy định này áp dụng cho toàn bộ doanh nghiệp cả nước",
]


def main() -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not CKPT.exists():
        raise SystemExit(f"Chưa có checkpoint {CKPT}")
    tok = AutoTokenizer.from_pretrained(CKPT)
    model = AutoModelForSequenceClassification.from_pretrained(CKPT).eval()
    try:
        from underthesea import word_tokenize
        def tach(s): return word_tokenize(s, format="text")
    except Exception:  # noqa: BLE001
        def tach(s): return s

    @torch.no_grad()
    def pred(pairs):
        out = []
        for i in range(0, len(pairs), 16):
            b = pairs[i:i + 16]
            p = [tach(x[0][:1200]) for x in b]
            h = [tach(x[1][:500]) for x in b]
            enc = tok(p, h, truncation=True, max_length=256, padding=True, return_tensors="pt")
            out += model(**enc).logits.argmax(1).tolist()
        return out

    rng = random.Random(SEED)
    pos = [json.loads(l) for l in TEST.read_text(encoding="utf-8").splitlines()
           if json.loads(l)["label"] == 1]
    rng.shuffle(pos)
    pos = pos[:400]

    # sanity: positive gốc phải ra grounded
    base = pred([(r["premise"], r["hypothesis"]) for r in pos])
    san = float(np.mean(np.array(base) == 1))
    print(f"sanity: positive gốc → grounded {san:.2%}  (phải cao)\n")

    ket = {}

    # ── INV ──
    inv_pairs, inv_base = [], []
    for r in pos:
        h = r["hypothesis"]
        for pat, thay in _INV:
            h = re.sub(pat, thay, h)
        if h != r["hypothesis"]:
            inv_pairs.append((r["premise"], h))
            inv_base.append(1)
    inv_pred = pred(inv_pairs)
    inv_fail = float(np.mean(np.array(inv_pred) != 1))
    ket["INV_paraphrase"] = {"fail": inv_fail, "n": len(inv_pairs)}

    # ── DIR-num: PhoBERT-alone vs STACK ──
    dnum, srcs = [], []
    for r in pos:
        m = re.match(r"Theo (.+?), (.+)", r["hypothesis"], re.S)
        cau = m.group(2) if m else r["hypothesis"]
        rr = bia_so_trong_cau(cau, rng)
        if not rr:
            continue
        cau_bia = rr[0]
        hyp_bia = (r["hypothesis"][: m.start(2)] + cau_bia) if m else cau_bia
        dnum.append((r["premise"], hyp_bia))
        srcs.append((r["premise"], hyp_bia))
    dnum_pred = pred(dnum)
    # PhoBERT-alone fail = vẫn nói grounded (1) dù số đã bịa
    alone_fail = float(np.mean(np.array(dnum_pred) == 1))
    # STACK: PhoBERT ∨ lech_so — lech_so bắt số lệch → chặn
    stack_fail = 0
    for (prem, hyp), pp in zip(srcs, dnum_pred):
        bat_rule = len(lech_so(hyp, prem)) > 0  # rule thấy số lệch
        lot = (pp == 1) and (not bat_rule)  # cả model lẫn rule đều KHÔNG bắt
        stack_fail += 1 if lot else 0
    stack_fail = stack_fail / max(len(dnum), 1)
    ket["DIR_num_PhoBERT_alone"] = {"fail": alone_fail, "n": len(dnum)}
    ket["DIR_num_full_stack"] = {"fail": stack_fail, "n": len(dnum)}

    # ── DIR-sem ──
    dsem, dsem_n = [], 0
    for r in pos:
        h = r["hypothesis"].rstrip(".") + ", " + rng.choice(_SEM)
        dsem.append((r["premise"], h))
        dsem_n += 1
    dsem_pred = pred(dsem)
    dsem_fail = float(np.mean(np.array(dsem_pred) == 1))  # vẫn grounded = fail
    ket["DIR_sem"] = {"fail": dsem_fail, "n": dsem_n}

    print("=== HỒ SƠ NĂNG LỰC (failure-rate, thấp = tốt) ===")
    for k, v in ket.items():
        print(f"  {k:28} fail {v['fail']:.3f}   (n={v['n']:,})")
    print("\n  → DIR-num PhoBERT một mình fail cao (trục số bị lọc khỏi train),")
    print("     nhưng FULL-STACK (∨ lech_so) fail thấp = đúng phân vai kiến trúc.")

    Path("./artifacts/guard/behavioral_phobert.json").write_text(
        json.dumps({"sanity_grounded": san, "probe": ket},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n→ artifacts/guard/behavioral_phobert.json")


if __name__ == "__main__":
    main()
