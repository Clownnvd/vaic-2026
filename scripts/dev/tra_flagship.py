"""Tra corpus lấy NGUYÊN VĂN điều–khoản cho chương trình flagship.

VÌ SAO: kho_mau.py đang để `trich="[PLACEHOLDER]"` và Điều/Khoản CHƯA ĐỐI CHIẾU.
Demo với citation bịa = bịa điều luật = ĐÚNG THỨ SẢN PHẨM NÀY SINH RA ĐỂ CHỐNG.
Không được gõ vào cái mình NGHĨ luật nói — phải TRA.

Chạy: uv run --python 3.11 --with pyarrow python scripts/tra_flagship.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402

# văn bản kho_mau đang trỏ tới
CAN_TRA = ["80/2021/NĐ-CP", "13/2019/NĐ-CP"]
SPLITS = Path("./data/splits_dn")


def main() -> None:
    tim = {s: None for s in CAN_TRA}

    for ten in ("train", "calib", "test"):
        f = SPLITS / f"{ten}.parquet"
        if not f.exists():
            continue
        tbl = pq.read_table(
            f, columns=["item_id", "doc_number_str", "issuing_authority", "title", "markdown"]
        )
        dns = tbl["doc_number_str"].to_pylist()
        for i, dn in enumerate(dns):
            if not dn:
                continue
            for s in CAN_TRA:
                # so khớp CHÍNH XÁC — "93/2025" từng khớp nhầm "193/2025" vì substring
                if dn.strip() == s and tim[s] is None:
                    tim[s] = {
                        "phia": ten,
                        "item_id": tbl["item_id"][i].as_py(),
                        "co_quan": tbl["issuing_authority"][i].as_py(),
                        "title": tbl["title"][i].as_py(),
                        "markdown": tbl["markdown"][i].as_py(),
                    }

    for s in CAN_TRA:
        d = tim[s]
        print("=" * 76)
        print(f"  {s}")
        print("=" * 76)
        if not d:
            print("  🔴 KHÔNG CÓ TRONG CORPUS")
            print("     → không được bịa. Hoặc bỏ chương trình này, hoặc lấy từ vbpl.vn API.")
            continue
        print(f"  phía   : {d['phia']}  ·  item_id {d['item_id']}")
        print(f"  cơ quan: {d['co_quan']}")
        print(f"  tên    : {(d['title'] or '')[:96]}")

        dieu = parse(d["markdown"] or "")
        print(f"  parse  : {len(dieu)} điều")
        for dd in dieu[:14]:
            tk = (dd.tieu_de or "").strip()[:62]
            print(f"    Điều {dd.so:<3} ({len(dd.khoan)} khoản)  {tk}")
        print()


if __name__ == "__main__":
    main()
