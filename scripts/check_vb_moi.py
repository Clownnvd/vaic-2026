"""Corpus có chứa các văn bản MỚI 2025/2026 không?

Danh sách mẫu hồ sơ (VAIC-MAU-HO-SO-2026) trích một loạt văn bản mới. Nếu corpus
KHÔNG có chúng thì matcher sẽ trích luật CŨ/ĐÃ CHẾT — đúng thứ sản phẩm chống.
Đây là câu hỏi chặn, phải trả lời bằng số chứ không đoán.

Chạy: uv run --python 3.11 --with pyarrow python scripts/check_vb_moi.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pyarrow.parquet as pq

# văn bản mới mà danh sách mẫu hồ sơ viện dẫn
CAN_TIM = [
    ("Luật CNC 133/2025/QH15", r"133/2025/QH15", "BỎ Giấy chứng nhận DN CNC (1/7/2026)"),
    ("Luật Đầu tư 143/2025/QH15", r"143/2025/QH15", "thay Luật Đầu tư 2020 (1/3/2026)"),
    ("Luật TNDN 67/2025/QH15", r"67/2025/QH15", "ưu đãi thuế TNDN bản mới"),
    ("Luật KH,CN&ĐMST 93/2025/QH15", r"93/2025/QH15", "căn cứ NAFOSTED"),
    ("NĐ 267/2025", r"267/2025/N[ĐD]-CP", "hướng dẫn Luật 93/2025"),
    ("NĐ 320/2025", r"320/2025/N[ĐD]-CP", "hướng dẫn Luật TNDN 67/2025"),
    ("NĐ 239/2025", r"239/2025/N[ĐD]-CP", "sửa NĐ 31/2021"),
    ("TT 44/2025/TT-BKHCN", r"44/2025/TT-BKHCN", "mẫu NAFOSTED BM-02..09"),
    ("TT 36/2025", r"36/2025/TT-BKHCN", "thay Đề án 844 (BM-01..26)"),
    ("TT 38/2025", r"38/2025/TT-BKHCN", "tài chính, thay TT 45/2019"),
    ("TT 38/2026", r"38/2026/TT-BKHCN", "mẫu DNTLM, phân cấp UBND tỉnh"),
    ("TT 20/2026", r"20/2026/TT-BTC", "hướng dẫn TNDN"),
    ("NQ 190/2025/QH15", r"190/2025/QH15", "nguyên tắc kế thừa sau sáp nhập"),
    ("NQ 202/2025/QH15", r"202/2025/QH15", "34 tỉnh"),
    # đối chứng: văn bản CŨ mà kho mẫu của mình đang trích
    ("NĐ 80/2021 (đang dùng)", r"80/2021/N[ĐD]-CP", "DNNVV — còn hiệu lực"),
    ("NĐ 13/2019 (đang dùng)", r"13/2019/N[ĐD]-CP", "DN KH&CN"),
    ("TT 06/2022", r"06/2022/TT-BKH[ĐD]T", "mẫu DNNVV"),
    ("TT 80/2021/TT-BTC", r"80/2021/TT-BTC", "mẫu 03/TNDN"),
]

F = Path("./data/vbpl_flagship.parquet")
FULL = Path("./data/splits/train.parquet")


def main() -> None:
    src = F if F.exists() else FULL
    tbl = pq.read_table(src, columns=["doc_number_str", "title", "year", "issuing_authority"])
    print(f"Corpus: {src.name} — {tbl.num_rows:,} văn bản")

    dns = [d or "" for d in tbl["doc_number_str"].to_pylist()]
    titles = [t or "" for t in tbl["title"].to_pylist()]
    years = tbl["year"].to_pylist()
    kho = " || ".join(dns)

    print(f"Dải năm trong corpus: {min(years)}–{max(years)}")
    for y in (2024, 2025, 2026):
        n = sum(1 for x in years if x == y)
        print(f"  năm {y}: {n:,} văn bản")

    print("\n" + "=" * 74)
    print(f"{'văn bản':32} {'có?':>5}  ghi chú")
    print("=" * 74)

    thieu = []
    for ten, pat, ghi in CAN_TIM:
        m = re.search(pat, kho, re.IGNORECASE)
        co = m is not None
        if not co:
            thieu.append(ten)
        print(f"{ten:32} {'CÓ' if co else '—':>5}  {ghi}")
        if co:
            # in title để xác nhận đúng văn bản
            for d, t in zip(dns, titles):
                if re.search(pat, d, re.IGNORECASE):
                    print(f"{'':32}       ↳ {t[:60]}")
                    break

    print("\n" + "=" * 74)
    if thieu:
        print(f"⚠ THIẾU {len(thieu)}/{len(CAN_TIM)} văn bản trong corpus:")
        for t in thieu:
            print(f"    • {t}")
        print("\n→ Matcher KHÔNG thể trích các văn bản này. Nếu curate flagship theo")
        print("  danh sách mẫu hồ sơ thì citation sẽ trỏ vào chỗ corpus không có.")
    else:
        print("✓ Corpus có đủ — curate flagship theo danh sách mẫu hồ sơ được.")


if __name__ == "__main__":
    main()
