"""THANG BASELINE trên ViFactCheck (zero-shot) — để con số guard CÓ NGHĨA.

0.58 đứng một mình vô nghĩa. Đặt cạnh: Majority / Rule-only / Guard-PhoBERT /
GPT-4o / SOTA-in-domain → mới thấy guard hơn baseline mù ở đâu.

HEADLINE = macro-F1 (KHÔNG phải accuracy — tập lệch lớp, acc là số rác).
Ghi công: ViFactCheck arXiv:2412.15308 (AAAI 2025), MIT.

Chạy (trên container có checkpoint):
  uv run --python 3.11 --with torch --with transformers --with underthesea \
      --with numpy --with scikit-learn --with openai python guard/eval_ladder.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

CKPT = Path("./artifacts/guard/phobert_guard")
F = Path("./data/ngoai/vifactcheck_test.jsonl")
RE_D6 = re.compile(r"biên giới|lãnh thổ|chủ quyền|biển đảo|hải đảo|quần đảo|hoàng sa|"
                   r"trường sa|lãnh hải|thềm lục địa|địa giới hành chính", re.IGNORECASE)
MAP = {0: 1, 1: 0, 2: 0}  # Supported→1, Refuted/NEI→0
N_GPT = 300  # số câu gọi GPT-4o (chi phí + thời gian)


def macro_f1(y, p) -> float:
    from sklearn.metrics import f1_score
    return float(f1_score(y, p, average="macro"))


def rc(y, p, lop) -> float:
    y, p = np.array(y), np.array(p)
    m = y == lop
    return float((p[m] == lop).mean()) if m.sum() else 0.0


def main() -> None:
    rows = [json.loads(l) for l in F.read_text(encoding="utf-8").splitlines()]
    sach = [r for r in rows
            if not RE_D6.search((r.get("Context") or "") + (r.get("Statement") or ""))]
    y = [MAP[int(r["labels"])] for r in sach]
    print(f"ViFactCheck sạch: {len(sach):,} câu · phân bố lớp {dict(zip(*np.unique(y, return_counts=True)))}")

    ket = {}

    # ── 1) MAJORITY ──
    maj = max(set(y), key=y.count)
    p_maj = [maj] * len(y)
    ket["Majority"] = {"macro_f1": macro_f1(y, p_maj), "acc": float(np.mean(np.array(y) == maj))}

    # ── 2) RULE-ONLY (lech_so: số trong claim lệch nguồn → 0) ──
    from guard.vn_number import lech_so
    p_rule = []
    for r in sach:
        nguon = (r.get("Evidence") or r.get("Context") or "")
        claim = (r.get("Statement") or "")
        try:
            lech = lech_so(claim, nguon)
        except Exception:  # noqa: BLE001
            lech = []
        p_rule.append(0 if lech else 1)  # có số lệch → không căn cứ; không thì cho qua
    ket["Rule-only (lệch số)"] = {"macro_f1": macro_f1(y, p_rule),
                                  "acc": float(np.mean(np.array(y) == np.array(p_rule)))}

    # ── 3) GUARD-PhoBERT zero-shot ──
    if CKPT.exists():
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(CKPT)
        model = AutoModelForSequenceClassification.from_pretrained(CKPT).eval()
        try:
            from underthesea import word_tokenize
            def tach(s): return word_tokenize(s, format="text")
        except Exception:  # noqa: BLE001
            def tach(s): return s
        p_ph = []
        with torch.no_grad():
            for i in range(0, len(sach), 16):
                b = sach[i:i + 16]
                pp = [tach((r.get("Evidence") or r.get("Context") or "")[:1200]) for r in b]
                hh = [tach((r.get("Statement") or "")[:500]) for r in b]
                enc = tok(pp, hh, truncation=True, max_length=256, padding=True, return_tensors="pt")
                p_ph += model(**enc).logits.argmax(1).tolist()
        ket["Guard-PhoBERT (zero-shot)"] = {
            "macro_f1": macro_f1(y, p_ph), "acc": float(np.mean(np.array(y) == np.array(p_ph))),
            "R_grounded": rc(y, p_ph, 1), "R_ungrounded": rc(y, p_ph, 0)}

    # ── 4) GPT-4o zero-shot (mẫu N_GPT) ──
    if os.getenv("USE_LLM") == "1":
        try:
            from gateway.client import goi_llm
            rng_idx = list(range(len(sach)))[:N_GPT]
            p_gpt, y_gpt = [], []
            for i in rng_idx:
                r = sach[i]
                nguon = (r.get("Evidence") or r.get("Context") or "")[:1500]
                claim = (r.get("Statement") or "")[:400]
                pr = (f"Nguồn: {nguon}\n\nKhẳng định: {claim}\n\n"
                      "Khẳng định trên CÓ được nguồn ủng hộ không? Trả đúng 1 từ: CÓ hoặc KHÔNG.")
                try:
                    o = goi_llm(pr, muc_dich="ladder-gpt4o", tac_vu="task-fast",
                                temperature=0, max_tokens=5) or ""
                except Exception:  # noqa: BLE001
                    o = ""
                p_gpt.append(1 if "CÓ" in o.upper() or "CO" in o.upper() else 0)
                y_gpt.append(y[i])
            ket["GPT-4o (zero-shot, n=%d)" % len(y_gpt)] = {
                "macro_f1": macro_f1(y_gpt, p_gpt), "acc": float(np.mean(np.array(y_gpt) == np.array(p_gpt)))}
        except Exception as e:  # noqa: BLE001
            print("  (bỏ GPT-4o:", type(e).__name__, str(e)[:60], ")")

    # ── 5) SOTA tham chiếu ──
    ket["SOTA in-domain (Gemma, CÓ train)"] = {"macro_f1": 0.899, "tham_chieu": True,
                                               "ghi_chu": "CÓ train + macro-F1 3 lớp — KHÔNG so trực tiếp"}

    print("\n=== THANG BASELINE (macro-F1, zero-shot trừ SOTA) ===")
    for k, v in sorted(ket.items(), key=lambda x: x[1]["macro_f1"]):
        note = " (tham chiếu)" if v.get("tham_chieu") else ""
        print(f"  {k:36} macro-F1 {v['macro_f1']:.3f}{note}")

    Path("./artifacts/guard/eval_ladder.json").write_text(
        json.dumps({"n": len(sach), "thang": ket,
                    "ghi_chu": "macro-F1 headline; acc phụ. SOTA chỉ tham chiếu."},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n→ artifacts/guard/eval_ladder.json")


if __name__ == "__main__":
    main()
