"""Thăm dò schema shard 0 của tmquan/vbpl-vn trước khi viết pipeline.

Đừng đoán dtype — đoán sai là hỏng cả 32 shard. Tải 1 shard, in schema + mẫu.
Chạy: uv run --python 3.11 --with pyarrow python scripts/probe_schema.py
"""

import os
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

URL = "https://huggingface.co/datasets/tmquan/vbpl-vn/resolve/main/documents-00000-of-00032.parquet"
TMP = Path("./data/_probe.parquet")


def main() -> None:
    TMP.parent.mkdir(parents=True, exist_ok=True)

    if not TMP.exists():
        print(f"Tải {URL}")
        req = urllib.request.Request(URL, headers={"User-Agent": "policyradar/0.1"})
        with urllib.request.urlopen(req) as r, TMP.open("wb") as f:
            total = 0
            while chunk := r.read(1 << 20):
                f.write(chunk)
                total += len(chunk)
                print(f"\r  {total / 1e6:.1f} MB", end="", flush=True)
        print()

    pf = pq.ParquetFile(TMP)
    print(f"\nrows={pf.metadata.num_rows}  row_groups={pf.num_row_groups}")
    print(f"file={TMP.stat().st_size / 1e6:.1f} MB\n")

    print("=== SCHEMA ===")
    for f in pf.schema_arrow:
        print(f"  {f.name:24} {f.type}")

    print("\n=== MẪU 2 DÒNG (cắt ngắn) ===")
    tbl = pf.read_row_group(0)
    for i in range(min(2, tbl.num_rows)):
        print(f"\n--- dòng {i} ---")
        for name in tbl.column_names:
            v = tbl[name][i].as_py()
            s = "None" if v is None else str(v).replace("\n", " ")
            print(f"  {name:24} {s[:110]}")

    # giá trị doc_type thực tế có gì
    if "doc_type" in tbl.column_names:
        import pyarrow.compute as pc

        vc = pc.value_counts(tbl["doc_type"])
        print("\n=== doc_type trong shard 0 ===")
        for x in vc:
            print(f"  {str(x['values'].as_py()):28} {x['counts'].as_py()}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
