"""Moi NGUYÊN VĂN các khoản cần cho kho flagship.

Điều kiện và quyền lợi nằm ở HAI điều khác nhau:
  80/2021/NĐ-CP  Điều 5  = tiêu chí DNNVV (ĐIỀU KIỆN)
                 Điều 13 = Hỗ trợ tư vấn   (QUYỀN LỢI)
  13/2019/NĐ-CP  Điều 6  = điều kiện cấp GCN (ĐIỀU KIỆN)
                 Điều 12 = Miễn giảm thuế TNDN (QUYỀN LỢI)

kho_mau gộp cả hai vào một citation → citation trỏ sai chỗ.

Chạy: uv run --python 3.11 --with pyarrow python scripts/moi_nguyen_van.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402

CAN = {
    "80/2021/NĐ-CP": [5, 13],
    "13/2019/NĐ-CP": [6, 12],
}


def main() -> None:
    for ten in ("train", "calib", "test"):
        f = Path("./data/splits_dn") / f"{ten}.parquet"
        if not f.exists():
            continue
        tbl = pq.read_table(f, columns=["item_id", "doc_number_str", "issuing_authority", "markdown"])
        for i, dn in enumerate(tbl["doc_number_str"].to_pylist()):
            if not dn or dn.strip() not in CAN:
                continue
            s = dn.strip()
            md = tbl["markdown"][i].as_py()
            co_quan = tbl["issuing_authority"][i].as_py()
            item_id = tbl["item_id"][i].as_py()

            for d in parse(md or ""):
                if d.so not in CAN[s]:
                    continue
                print("=" * 78)
                print(f"  {s}  ·  {co_quan}  ·  item_id {item_id}")
                print(f"  ĐIỀU {d.so}: {(d.tieu_de or '').strip()[:66]}")
                print("=" * 78)
                for k in d.khoan:
                    print(f"\n  ── Khoản {k.so} ──  ({len(k.text)} ký tự)")
                    t = k.text.strip()
                    print("  " + (t[:900] + (" …" if len(t) > 900 else "")).replace("\n", "\n  "))
                print()


if __name__ == "__main__":
    main()
