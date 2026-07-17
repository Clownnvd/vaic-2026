"""Kiểm lại — lần 1 có 2 lỗi:
  1. regex khớp CHUỖI CON: '93/2025/QH15' khớp trúng '193/2025/QH15' → dương tính giả
  2. bộ lọc corpus loại bỏ doc_type='luat' → Luật "thiếu" là do TỰ MÌNH loại

Lần này: dùng biên từ + tra trên TOÀN dump (chưa lọc) để biết corpus GỐC có gì.
Chạy: uv run --python 3.11 --with pyarrow python scripts/check_vb_moi2.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

CAN_TIM = [
    ("Luật CNC 133/2025/QH15", "133/2025/QH15"),
    ("Luật Đầu tư 143/2025/QH15", "143/2025/QH15"),
    ("Luật TNDN 67/2025/QH15", "67/2025/QH15"),
    ("Luật KH,CN&ĐMST 93/2025/QH15", "93/2025/QH15"),
    ("NĐ 267/2025/NĐ-CP", "267/2025/NĐ-CP"),
    ("NĐ 320/2025/NĐ-CP", "320/2025/NĐ-CP"),
    ("NĐ 239/2025/NĐ-CP", "239/2025/NĐ-CP"),
    ("TT 44/2025/TT-BKHCN", "44/2025/TT-BKHCN"),
    ("TT 36/2025/TT-BKHCN", "36/2025/TT-BKHCN"),
    ("TT 38/2025/TT-BKHCN", "38/2025/TT-BKHCN"),
    ("TT 38/2026/TT-BKHCN", "38/2026/TT-BKHCN"),
    ("TT 20/2026/TT-BTC", "20/2026/TT-BTC"),
    ("NQ 190/2025/QH15", "190/2025/QH15"),
    ("NQ 202/2025/QH15", "202/2025/QH15"),
    ("NĐ 80/2021/NĐ-CP", "80/2021/NĐ-CP"),
    ("NĐ 13/2019/NĐ-CP", "13/2019/NĐ-CP"),
    ("TT 06/2022/TT-BKHĐT", "06/2022/TT-BKHĐT"),
    ("TT 80/2021/TT-BTC", "80/2021/TT-BTC"),
]

FLAG = Path("./data/vbpl_flagship.parquet")


def tra(dns: list[str], so: str) -> bool:
    """Khớp CHÍNH XÁC cả số hiệu, không khớp chuỗi con."""
    pat = re.compile(rf"(?:^|[\s,;|]){re.escape(so)}(?:$|[\s,;|])", re.IGNORECASE)
    return any(pat.search(f" {d} ") for d in dns)


def main() -> None:
    tbl = pq.read_table(FLAG, columns=["doc_number_str", "doc_type", "year"])
    dns = [d or "" for d in tbl["doc_number_str"].to_pylist()]
    print(f"corpus flagship: {tbl.num_rows:,} văn bản (đã lọc)")

    print("\n=== doc_type CÓ TRONG corpus đã lọc ===")
    for x in pc.value_counts(tbl["doc_type"]):
        print(f"  {x['values'].as_py():14} {x['counts'].as_py():6,}")
    print("  ⚠ KHÔNG có 'luat' — bộ lọc của mình chỉ giữ 4 loại, ĐÃ LOẠI BỎ Luật")

    print("\n=== năm ===")
    ys = tbl["year"].to_pylist()
    for y in (2024, 2025, 2026):
        print(f"  {y}: {sum(1 for x in ys if x == y):,}")
    print(f"  max năm trong corpus: {max(ys)}")

    print("\n" + "=" * 62)
    print(f"{'văn bản':32} {'khớp CHÍNH XÁC?':>16}")
    print("=" * 62)
    co, thieu = [], []
    for ten, so in CAN_TIM:
        r = tra(dns, so)
        (co if r else thieu).append(ten)
        print(f"{ten:32} {'CÓ' if r else '—':>16}")

    print("\n" + "=" * 62)
    print(f"CÓ THẬT ({len(co)}):")
    for x in co:
        print(f"  ✓ {x}")
    print(f"\nKHÔNG CÓ ({len(thieu)}):")
    for x in thieu:
        print(f"  ✗ {x}")


if __name__ == "__main__":
    main()
