"""ViFactCheck có khớp domain của mình không — và có dính điều 6 không?

Người dùng bắt đúng: "2 nguồn data nó phải khớp".
Mẫu đầu tiên đã lộ: Topic='Chính trị', nguồn baochinhphu.vn → TIN TỨC, không phải LUẬT.
Phải đo phân bố thật trước khi quyết dùng hay bỏ.

Chạy: uv run --python 3.11 python scripts/soi_vifactcheck.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

F = Path("./data/ngoai/vifactcheck_test.jsonl")

# đúng 5 phạm vi điều 6, không tự nới
RE_D6 = re.compile(
    r"biên giới|lãnh thổ|chủ quyền|biển đảo|hải đảo|quần đảo"
    r"|hoàng sa|trường sa|lãnh hải|thềm lục địa|địa giới hành chính",
    re.IGNORECASE,
)
# dấu hiệu văn bản pháp luật
RE_LUAT = re.compile(
    r"nghị định|thông tư|quyết định|nghị quyết|luật số|điều \d+|khoản \d+|/N[ĐD]-CP|/QH\d+|/TT-",
    re.IGNORECASE,
)


def main() -> None:
    rows = [json.loads(l) for l in F.read_text(encoding="utf-8").splitlines()]
    print(f"ViFactCheck test: {len(rows):,} dòng\n")

    print("=== CHỦ ĐỀ ===")
    for t, n in Counter(r.get("Topic") for r in rows).most_common():
        cd = " 🚩 vùng điều 6" if str(t).strip().lower() in ("chính trị", "chinh tri") else ""
        print(f"  {str(t):22} {n:5,}  ({n/len(rows)*100:4.1f}%){cd}")

    print("\n=== KHỚP DOMAIN LUẬT KHÔNG? ===")
    n_luat = sum(1 for r in rows if RE_LUAT.search((r.get("Context") or "") + (r.get("Statement") or "")))
    print(f"  có dấu hiệu văn bản pháp luật : {n_luat:,}/{len(rows):,} ({n_luat/len(rows)*100:.1f}%)")
    print(f"  ⇒ {'KHỚP' if n_luat/len(rows) > 0.5 else 'KHÔNG KHỚP — đây là tin tức, không phải luật'}")

    print("\n=== DÍNH ĐIỀU 6 KHÔNG? ===")
    d6 = [r for r in rows if RE_D6.search((r.get("Context") or "") + (r.get("Statement") or ""))]
    print(f"  chạm phạm vi điều 6 : {len(d6):,}/{len(rows):,} ({len(d6)/len(rows)*100:.1f}%)")
    for r in d6[:4]:
        print(f"    • [{r.get('Topic')}] {(r.get('Statement') or '')[:76]}")

    print("\n=== NGUỒN BÁO ===")
    for a, n in Counter(r.get("Author") for r in rows).most_common(6):
        print(f"  {str(a):24} {n:5,}")

    print("\n" + "=" * 66)
    print("KẾT LUẬN")
    print("=" * 66)
    print(f"  • Domain: TIN TỨC (chỉ {n_luat/len(rows)*100:.0f}% chạm văn bản luật) — KHÔNG khớp corpus của mình")
    print(f"  • Điều 6: {len(d6)/len(rows)*100:.1f}% dòng chạm phạm vi nhạy cảm")
    print("\n  ⇒ KHÔNG dùng để TRAIN (sai domain, và train xong khoe là ngụy biện)")
    print("  ⇒ CHỈ dùng làm phép thử CHUYỂN MIỀN (zero-shot), và phải nói rõ giới hạn:")
    print("     'guard train trên LUẬT, đem sang TIN TỨC chưa hề thấy, vẫn đạt X%")
    print("      → nó học GROUNDING chứ không học thuộc từ khoá luật'")
    print("     Đây là claim về TỔNG QUÁT HOÁ, KHÔNG phải claim về độ chính xác domain luật.")


if __name__ == "__main__":
    main()
