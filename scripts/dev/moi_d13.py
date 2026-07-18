"""Moi ĐỦ Điều 13 Khoản 2 của 80/2021/NĐ-CP — mức hỗ trợ theo từng quy mô.

Bản in trước bị cắt ở "doanh nghiệp nhỏ …" nên chưa thấy mức của DN VỪA.
Không thấy thì KHÔNG ĐƯỢC ĐOÁN — phải in đủ rồi mới ghi vào kho.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402

for ten in ("train", "calib", "test"):
    f = Path("./data/splits_dn") / f"{ten}.parquet"
    if not f.exists():
        continue
    tbl = pq.read_table(f, columns=["doc_number_str", "markdown"])
    for i, dn in enumerate(tbl["doc_number_str"].to_pylist()):
        if (dn or "").strip() != "80/2021/NĐ-CP":
            continue
        for d in parse(tbl["markdown"][i].as_py() or ""):
            if d.so != 13:
                continue
            for k in d.khoan:
                if k.so != 2:
                    continue
                print(f"=== Điều 13 Khoản 2 — ĐỦ ({len(k.text)} ký tự) ===\n")
                print(k.text.strip())
        sys.exit(0)
print("KHÔNG THẤY")
