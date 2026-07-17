"""Phép thử CHUYỂN MIỀN trên ViFactCheck — thước đo NGOÀI, phá vòng tròn tự-chấm.

⚠️ ĐỌC KỸ TRƯỚC KHI DÙNG SỐ NÀY:

Vấn đề gốc: guard đang đo trên data TỰ SINH — mình viết máy sinh câu bịa, rồi
cũng chính mình viết rule bắt. Vòng tròn. Giám khảo hỏi một câu là đứng hình.

ViFactCheck là bộ NGOÀI: 7.232 cặp **NGƯỜI gán nhãn**, MIT, SOTA công bố
(Gemma macro-F1 89.90%, AAAI 2025).

NHƯNG **KHÔNG KHỚP DOMAIN** — đã đo:
    chạm văn bản luật : 477/1.447 = 33%
    chủ đề            : THỂ THAO · HOA HẬU · Chính trị · Kinh doanh...
    → đây là TIN TỨC, không phải văn bản pháp luật.

⇒ TUYỆT ĐỐI KHÔNG train trên bộ này. Train xong khoe "guard bắt bịa điều luật
  tốt" là NGUỴ BIỆN.

⇒ CHỈ dùng ZERO-SHOT, và phát biểu phải chính xác từng chữ:
    ✅ "train trên LUẬT, đem sang TIN TỨC chưa hề thấy, vẫn đạt X%
        → model học CÁCH ĐỐI CHIẾU claim với nguồn, không học thuộc từ khoá luật"
       (claim về TỔNG QUÁT HOÁ)
    ❌ "guard đạt X% trên bài toán bịa điều luật"
       (ViFactCheck KHÔNG đo cái đó)

Lọc bỏ dòng chạm điều 6 (6,8%) — vừa rà điều 6 cả buổi rồi lại nạp tin chính trị
vào thì tự mâu thuẫn.

Ghi công (điều 2, bắt buộc dù MIT):
    ViFactCheck: A Multi-Domain Vietnamese News Fact-Checking Benchmark
    arXiv:2412.15308 (AAAI 2025) · HuggingFace: tranthaihoa/vifactcheck · MIT

Chạy: uv run --python 3.11 --with torch --with transformers --with underthesea \
        --with numpy python guard/eval_ngoai.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, ".")

CKPT = Path("./artifacts/guard/phobert_guard")
F = Path("./data/ngoai/vifactcheck_test.jsonl")

RE_D6 = re.compile(
    r"biên giới|lãnh thổ|chủ quyền|biển đảo|hải đảo|quần đảo"
    r"|hoàng sa|trường sa|lãnh hải|thềm lục địa|địa giới hành chính",
    re.IGNORECASE,
)
RE_LUAT = re.compile(
    r"nghị định|thông tư|quyết định|nghị quyết|luật số|điều \d+|khoản \d+|/N[ĐD]-CP|/QH\d+|/TT-",
    re.IGNORECASE,
)

# ViFactCheck: 0=Supported 1=Refuted 2=NEI
# Guard: 1=grounded (có căn cứ) · 0=không có căn cứ
# Supported → 1. Refuted → 0. NEI → 0 (không đủ căn cứ = không được khẳng định).
MAP = {0: 1, 1: 0, 2: 0}


def main() -> None:
    if not CKPT.exists():
        raise SystemExit(f"Chưa có checkpoint {CKPT} — chạy guard/don4_phobert.py trước.")

    rows = [json.loads(l) for l in F.read_text(encoding="utf-8").splitlines()]
    print(f"ViFactCheck test: {len(rows):,} dòng")

    # ── lọc điều 6 ────────────────────────────────────────────
    sach = [
        r for r in rows
        if not RE_D6.search((r.get("Context") or "") + (r.get("Statement") or ""))
    ]
    print(f"sau lọc điều 6  : {len(sach):,}  (bỏ {len(rows)-len(sach)})")

    # ── tách 2 nhóm: toàn bộ vs nhóm CÓ chạm văn bản luật ─────
    gan_luat = [
        r for r in sach
        if RE_LUAT.search((r.get("Context") or "") + (r.get("Statement") or ""))
    ]
    print(f"nhóm gần domain luật: {len(gan_luat):,}\n")

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(CKPT)
    model = AutoModelForSequenceClassification.from_pretrained(CKPT)
    model.eval()

    try:
        from underthesea import word_tokenize

        def tach(s):
            return word_tokenize(s, format="text")
    except Exception:  # noqa: BLE001
        def tach(s):
            return s

    @torch.no_grad()
    def chay(ds, nhan: str):
        y_true, y_pred = [], []
        for i in range(0, len(ds), 16):
            b = ds[i : i + 16]
            # premise = Evidence (đoạn trích nguồn) · hypothesis = Statement (claim)
            p = [tach((r.get("Evidence") or r.get("Context") or "")[:1200]) for r in b]
            h = [tach((r.get("Statement") or "")[:500]) for r in b]
            enc = tok(p, h, truncation=True, max_length=256, padding=True, return_tensors="pt")
            pr = model(**enc).logits.argmax(1).tolist()
            y_pred += pr
            y_true += [MAP[int(r["labels"])] for r in b]

        y_true, y_pred = np.array(y_true), np.array(y_pred)
        acc = float((y_true == y_pred).mean())
        bat = float(((y_pred == 0) & (y_true == 0)).sum() / max((y_true == 0).sum(), 1))
        print(f"  {nhan:34} acc {acc:.3f}   bắt-không-căn-cứ {bat:.3f}   (n={len(ds):,})")
        return acc, bat

    print("=" * 70)
    print("ZERO-SHOT — model CHƯA HỀ thấy bộ này, không train trên nó")
    print("=" * 70)
    a1, b1 = chay(sach, "toàn bộ tin tức")
    a2, b2 = chay(gan_luat, "riêng nhóm chạm văn bản luật")

    print("\n" + "=" * 70)
    print("ĐỌC SỐ CHO ĐÚNG — đừng overclaim")
    print("=" * 70)
    print(f"  SOTA ViFactCheck (Gemma, CÓ train): macro-F1 89.90%")
    print(f"  Guard mình (zero-shot, KHÔNG train): acc {a1:.3f}")
    print()
    print("  ✅ NÓI ĐƯỢC : 'train trên LUẬT, đem sang TIN TỨC chưa hề thấy vẫn đạt")
    print("               acc {:.2f} → model học CÁCH ĐỐI CHIẾU claim-nguồn,".format(a1))
    print("               không học thuộc từ khoá luật'   (claim về TỔNG QUÁT HOÁ)")
    print("  ❌ KHÔNG NÓI: 'guard đạt {:.2f} trên bài toán bịa điều luật'".format(a1))
    print("               — ViFactCheck KHÔNG đo cái đó, đây là TIN TỨC.")
    print()
    print("  ⚠️ So trực tiếp với SOTA 89.90% là KHÔNG CÔNG BẰNG cho cả hai phía:")
    print("     SOTA có train trên bộ này + đo macro-F1 3 lớp; mình zero-shot + gộp 2 lớp.")
    print("     Đưa lên slide phải ghi rõ hai điều kiện khác nhau.")

    Path("./artifacts/guard").mkdir(parents=True, exist_ok=True)
    Path("./artifacts/guard/eval_ngoai.json").write_text(
        json.dumps(
            {
                "bo": "ViFactCheck (tranthaihoa/vifactcheck, MIT, arXiv:2412.15308)",
                "che_do": "zero-shot — KHÔNG train trên bộ này",
                "toan_bo_tin_tuc": {"n": len(sach), "acc": a1, "bat": b1},
                "nhom_cham_van_ban_luat": {"n": len(gan_luat), "acc": a2, "bat": b2},
                "da_loc_dieu_6": len(rows) - len(sach),
                "sota_tham_chieu": "Gemma macro-F1 89.90% (AAAI 2025) — CÓ train, macro-F1 3 lớp, KHÔNG so trực tiếp được",
                "gioi_han": "domain TIN TỨC, chỉ 33% chạm văn bản luật → đo TỔNG QUÁT HOÁ, không đo độ chính xác domain luật",
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print("\n  → artifacts/guard/eval_ngoai.json")


if __name__ == "__main__":
    main()
