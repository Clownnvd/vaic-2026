"""Train Guard NLI (PhoBERT) — chạy được trên CPU / Kaggle T4 / FPT H100.

CHẠY --smoke TRƯỚC KHI ĐỐT GIỜ GPU. Kho ghi rõ: 2 phút smoke bắt hết lỗi API
để không phí giờ GPU. Đã có người trả giá cho bài học này.

  uv run --python 3.11 --with torch --with transformers --with underthesea python \
      guard/train_phobert.py --smoke          # 40 mẫu, 1 epoch, ~2 phút CPU
  ... --nhe                                   # 2k mẫu CPU (~20 phút)
  ... --day-du                                # full, dành cho GPU

⛔ `vinai/phobert-base` = MIT. TUYỆT ĐỐI KHÔNG dùng `phobert-base-v2` = AGPL.
⛔ Không đẩy checkpoint lên GitHub (luật E2) — đã .gitignore.

Tách từ bằng `underthesea.word_tokenize` để NÉ VnCoreNLP (cần Java) — nguồn lỗi #1.
max_len = 256: đo thật trên khoản luật, 25,9% vượt 128 token.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, ".")

SEED = 7
# MODEL_DIR: đường model trên đĩa (lab FPT không ra được CDN HuggingFace →
# nạp từ /mnt/data/phobert đã đẩy sẵn). Không đặt thì tải từ HF như thường.
MODEL = os.environ.get("MODEL_DIR", "vinai/phobert-base")  # MIT — KHÔNG dùng v2 (AGPL)
MAX_LEN = 256  # đo thật: 25,9% khoản vượt 128 token
DATA = Path(os.environ.get("DATA_DIR", "./data/guard"))
OUT = Path(os.environ.get("OUT_DIR", "./artifacts/guard"))

# 4 trục NGỮ NGHĨA — thứ rule KHÔNG bắt được, đây là việc của model
TRUC_NGU_NGHIA = {
    "bia_tong_quat_hoa",
    "bia_tu_du_dieu_kien",
    "bia_bo_rang_buoc",
    "bia_suy_dien",
}


def dat_seed(s: int = SEED) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def nap(ten: str, chi_ngu_nghia: bool, gioi_han: int | None) -> list[dict]:
    """Nạp cặp. chi_ngu_nghia=True → chỉ giữ positive + 4 trục ngữ nghĩa.

    VÌ SAO lọc: lớp tất định đã bắt 6 trục kia với 0.977 và giải trình được.
    Bắt model học lại mấy trục đó = lãng phí + làm loãng. Giao đúng việc.
    """
    ra = []
    with (DATA / f"{ten}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if chi_ngu_nghia:
                if r["label"] == 0 and r["corruption_type"] not in TRUC_NGU_NGHIA:
                    continue
            ra.append(r)
            if gioi_han and len(ra) >= gioi_han:
                break
    return ra


def can_bang(rows: list[dict], rng: random.Random) -> list[dict]:
    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]
    n = min(len(pos), len(neg))
    ra = rng.sample(pos, n) + rng.sample(neg, n)
    rng.shuffle(ra)
    return ra


def tach_tu(s: str) -> str:
    """underthesea — né VnCoreNLP (cần Java). Lỗi thì trả nguyên, không chết."""
    try:
        from underthesea import word_tokenize

        return word_tokenize(s, format="text")
    except Exception:  # noqa: BLE001
        return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="40 mẫu 1 epoch — bắt lỗi trước khi đốt GPU")
    ap.add_argument("--nhe", action="store_true", help="2k mẫu, chạy CPU được")
    ap.add_argument("--day-du", action="store_true", help="full — dành cho GPU")
    ap.add_argument("--tat-ca-truc", action="store_true", help="train cả 6 trục rule đã bắt (mặc định KHÔNG)")
    args = ap.parse_args()

    if args.smoke:
        n_train, epochs, bs = 40, 1, 8
    elif args.nhe:
        n_train, epochs, bs = 2000, 3, 16
    else:
        n_train, epochs, bs = None, 4, 16

    dat_seed()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    chi_nn = not args.tat_ca_truc

    print(f"Model : {MODEL}  (MIT)")
    print(f"Chế độ: {'smoke' if args.smoke else ('nhẹ/CPU' if args.nhe else 'đầy đủ')}")
    print(f"Trục  : {'CHỈ ngữ nghĩa (rule không bắt được)' if chi_nn else 'tất cả'}")

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Thiết bị: {dev}" + ("  ⚠ CPU — chậm, cân nhắc GPU" if dev.type == "cpu" else ""))

    tr = can_bang(nap("train", chi_nn, None), rng)
    if n_train:
        tr = tr[:n_train]
    # TEST: dùng TOÀN BỘ, KHÔNG cân.
    # FPR/TPR là tỉ lệ TRONG TỪNG LỚP → không đổi khi tỉ lệ lớp đổi. Cân test
    # chỉ tổ vứt bớt câu đo → ước lượng lỏng hơn, chẳng được gì.
    # (Trước đây cân test rồi báo `acc`. acc trên test lệch 23/77 thì đoán bừa
    #  đã 77% — con số đó vô nghĩa. Nay báo FPR/TPR tách riêng theo trục.)
    # smoke chỉ cần bắt lỗi API → 400 câu là đủ; bản thật đo nguyên bộ.
    te = nap("test", chi_nn, 400 if args.smoke else None)
    print(f"\ntrain {len(tr):,} cặp (đã cân 1:1) · test {len(te):,}"
          f"{' (mẫu smoke)' if args.smoke else ' (nguyên bộ, KHÔNG cân)'}")
    if not tr:
        raise SystemExit("Không có dữ liệu — chạy guard/make_data.py trước.")

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    print("Nạp tokenizer + model…")
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2).to(dev)

    def batch(rows: list[dict]):
        p = [tach_tu(r["premise"][:1500]) for r in rows]
        h = [tach_tu(r["hypothesis"][:600]) for r in rows]
        enc = tok(p, h, truncation=True, max_length=MAX_LEN, padding=True, return_tensors="pt")
        y = torch.tensor([r["label"] for r in rows])
        return {k: v.to(dev) for k, v in enc.items()}, y.to(dev)

    opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
    ce = nn.CrossEntropyLoss()
    t0 = time.time()

    for ep in range(epochs):
        model.train()
        idx = list(range(len(tr)))
        rng.shuffle(idx)
        tong = 0.0
        for i in range(0, len(idx), bs):
            b = [tr[j] for j in idx[i : i + bs]]
            enc, y = batch(b)
            opt.zero_grad()
            out = model(**enc)
            loss = ce(out.logits, y)
            loss.backward()
            opt.step()
            tong += loss.item()
            if args.smoke:
                print(f"  step {i // bs}: loss {loss.item():.4f}")
        print(f"epoch {ep}: loss TB {tong / max(len(idx) // bs, 1):.4f}  ({time.time() - t0:.0f}s)")

    # ── đo trên test ──────────────────────────────────────────
    # KỶ LUẬT CHECKLIST (Ribeiro et al., ACL 2020): báo FAILURE RATE THEO TỪNG
    # CAPABILITY, KHÔNG gộp thành một con `acc`. Một số tổng che mất chỗ thủng.
    # Và BÁO ĐỘNG GIẢ phải đứng riêng, in đậm: guard chặn oan câu ĐÚNG thì
    # người dùng tắt guard → guard vô dụng dù bắt bịa giỏi đến đâu.
    # (Đây đúng bệnh GPT-4o mắc: đo được nó từ chối oan 62,5% câu đúng.)
    model.eval()
    theo_truc: dict[str, list[int]] = {}  # trục -> [bắt được, tổng]
    fp = 0
    n_that = 0
    with torch.no_grad():
        for i in range(0, len(te), 32):
            b = te[i : i + 32]
            enc, y = batch(b)
            pred = model(**enc).logits.argmax(1)
            for r, p_, y_ in zip(b, pred.tolist(), y.tolist()):
                if y_ == 1:  # câu ĐÚNG
                    n_that += 1
                    if p_ == 0:
                        fp += 1  # ← chặn oan
                else:  # câu bịa
                    t = r.get("corruption_type") or "(không rõ)"
                    d = theo_truc.setdefault(t, [0, 0])
                    d[1] += 1
                    if p_ == 0:
                        d[0] += 1

    fpr = fp / max(n_that, 1)
    tprs = [d[0] / max(d[1], 1) for d in theo_truc.values()]
    tb = sum(tprs) / max(len(tprs), 1)

    print(f"\n{'=' * 60}")
    print("GUARD NLI (PhoBERT) — failure rate theo TRỤC, không gộp 1 số")
    print("=" * 60)
    print(f"\n  🔴 BÁO ĐỘNG GIẢ (chặn oan câu ĐÚNG) = {fpr:.3f}  ({fp}/{n_that})")
    print(f"     → so chuẩn: GPT-4o tự kiểm chặn oan 0.625 · lớp tất định 0.000")
    print(f"\n  Bắt bịa theo trục:")
    for t in sorted(theo_truc, key=lambda x: theo_truc[x][0] / max(theo_truc[x][1], 1)):
        b_, n_ = theo_truc[t]
        r_ = b_ / max(n_, 1)
        cd = "🟢" if r_ > 0.9 else ("🟡" if r_ > 0.7 else "🔴")
        nn_ = " ← NGỮ NGHĨA (rule mù)" if t in TRUC_NGU_NGHIA else ""
        print(f"    {t:24} {r_:.3f}  ({b_:4}/{n_:4}) {cd}{nn_}")
    print(f"\n  TB các trục = {tb:.3f}   (KHÔNG phải accuracy — test lệch 23/77,")
    print(f"                          đoán bừa 'bịa' đã được 0.77)")
    print(f"  thời gian   = {time.time() - t0:.0f}s trên {dev}")

    if args.smoke:
        print("\n✓ SMOKE XANH — đường ống chạy được, giờ đẩy lên GPU chạy thật.")
        print("  (số trên vô nghĩa: 40 mẫu 1 epoch, chỉ để bắt lỗi)")
        return

    # so với lớp tất định — trục ngữ nghĩa nó ra 0.000
    print(f"\nSo sánh trên trục NGỮ NGHĨA:")
    print(f"  lớp tất định : 0.000  (rule KHÔNG THỂ bắt — không có số/mã nào sai)")
    print(f"  PhoBERT NLI  : {tb:.3f}  (TB các trục ngữ nghĩa)")
    if tb > 0.5:
        print(f"  ⇒ model VÁ được chỗ rule mù → PyTorch load-bearing, ablation có cái để nói.")
    else:
        print(f"  ⇒ model CHƯA vá được. Chưa có gì để khoe — nói thật, đừng ép số.")

    d = OUT / "phobert_guard"
    model.save_pretrained(d)
    tok.save_pretrained(d)
    (OUT / "phobert_ket_qua.json").write_text(
        json.dumps(
            {
                "bao_dong_gia": round(fpr, 4),
                "tb_bat_bia_ngu_nghia": round(tb, 4),
                "theo_truc": {t: round(v[0] / max(v[1], 1), 4) for t, v in theo_truc.items()},
                "n_train": len(tr),
                "n_test": len(te),
                "epochs": epochs,
                "device": str(dev),
                "chi_ngu_nghia": chi_nn,
                "luu_y": "F1/bắt-bịa cao trên test TỔNG HỢP (template). Con số thành thật "
                "cần đối chiếu output LLM thật — xem guard/eval_llm_that.py.",
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n✓ checkpoint → {d}  (đã .gitignore — luật E2 cấm publish weights)")


if __name__ == "__main__":
    main()
