"""Dò dải năm của cả 32 shard mà KHÔNG tải 1.8GB.

Parquet lưu min/max từng cột trong footer. Đọc footer qua HTTP range request
(fsspec) → biết ngay shard nào chứa văn bản 2018+. Vài KB thay vì 55MB/shard.

Chạy: uv run --python 3.11 --with pyarrow --with fsspec --with aiohttp python scripts/probe_years.py
"""

import os

import fsspec
import pyarrow.parquet as pq

BASE = "https://huggingface.co/datasets/tmquan/vbpl-vn/resolve/main"
TONG = 32

fs = fsspec.filesystem("http")


def main() -> None:
    print(f"{'shard':>5}  {'rows':>6}  {'năm min':>7}  {'năm max':>7}  {'≥2018?':>7}")
    print("-" * 44)

    co_2018 = []
    for i in range(TONG):
        url = f"{BASE}/documents-{i:05d}-of-{TONG:05d}.parquet"
        try:
            with fs.open(url, "rb") as f:
                pf = pq.ParquetFile(f)
                idx = pf.schema_arrow.get_field_index("year")

                lo, hi = None, None
                for rg in range(pf.num_row_groups):
                    st = pf.metadata.row_group(rg).column(idx).statistics
                    if st is None or not st.has_min_max:
                        continue
                    lo = st.min if lo is None else min(lo, st.min)
                    hi = st.max if hi is None else max(hi, st.max)

                moi = (hi or 0) >= 2018
                if moi:
                    co_2018.append(i)
                print(
                    f"{i:>5}  {pf.metadata.num_rows:>6}  {str(lo):>7}  {str(hi):>7}"
                    f"  {'CÓ' if moi else '—':>7}"
                )
        except Exception as e:  # noqa: BLE001
            print(f"{i:>5}  lỗi: {type(e).__name__}: {str(e)[:60]}")

    print("\nShard có văn bản ≥2018:", co_2018 or "KHÔNG CÓ SHARD NÀO")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
