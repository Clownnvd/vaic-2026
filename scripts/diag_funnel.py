"""Soi phễu lọc: vì sao shard có văn bản 2025 mà 0 khớp?

Đọc CHỈ cột year + doc_type qua HTTP range (parquet là định dạng cột) → không tải 70MB/shard.
Trả lời: mỗi shard có bao nhiêu văn bản ≥2018, trong đó bao nhiêu đúng doc_type.

Chạy: uv run --python 3.11 --with pyarrow --with fsspec --with aiohttp python scripts/diag_funnel.py
"""

import os

import fsspec
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

BASE = "https://huggingface.co/datasets/tmquan/vbpl-vn/resolve/main"
TONG = 32
DOC_TYPES = pa.array(["nghi_dinh", "thong_tu", "quyet_dinh", "nghi_quyet"])

fs = fsspec.filesystem("http")


def dem(mask) -> int:
    return pc.sum(pc.cast(mask, "int32")).as_py() or 0


def main() -> None:
    print(f"{'shard':>5} {'rows':>6} {'≥2018':>7} {'≥2018 & đúng type':>18}")
    print("-" * 42)

    tong_2018 = 0
    tong_ok = 0
    co_hang = []

    for i in range(TONG):
        url = f"{BASE}/documents-{i:05d}-of-{TONG:05d}.parquet"
        try:
            with fs.open(url, "rb") as f:
                tbl = pq.ParquetFile(f).read(columns=["year", "doc_type"])

            m_year = pc.fill_null(pc.greater_equal(tbl["year"], 2018), False)
            m_type = pc.fill_null(pc.is_in(tbl["doc_type"], value_set=DOC_TYPES), False)
            n_year = dem(m_year)
            n_ok = dem(pc.and_(m_year, m_type))

            tong_2018 += n_year
            tong_ok += n_ok
            if n_ok:
                co_hang.append(i)

            print(f"{i:>5} {tbl.num_rows:>6} {n_year:>7} {n_ok:>18}")
        except Exception as e:  # noqa: BLE001
            print(f"{i:>5}  lỗi: {type(e).__name__}: {str(e)[:50]}")

    print("-" * 42)
    print(f"TỔNG văn bản ≥2018            : {tong_2018:,}")
    print(f"TỔNG ≥2018 & doc_type hợp lệ  : {tong_ok:,}")
    print(f"Shard thực sự có hàng         : {co_hang}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
