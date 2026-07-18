"""Tải 1 shard, in phễu lọc từng tầng để tìm chỗ chết.

Chạy: uv run --python 3.11 --with pyarrow python scripts/diag_shard.py 3
"""

import sys
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

I = int(sys.argv[1]) if len(sys.argv) > 1 else 3
URL = f"https://huggingface.co/datasets/tmquan/vbpl-vn/resolve/main/documents-{I:05d}-of-00032.parquet"
TMP = Path(f"./data/_diag_{I}.parquet")

TYPES = pa.array(["nghi_dinh", "thong_tu", "quyet_dinh", "nghi_quyet"])
KWS = [
    "ưu đãi",
    "công nghệ cao",
    "doanh nghiệp nhỏ và vừa",
    "đổi mới sáng tạo",
    "khởi nghiệp",
    "chuyển đổi số",
    "khoa học và công nghệ",
    "hỗ trợ doanh nghiệp",
]


def n(mask) -> int:
    return pc.sum(pc.cast(mask, "int32")).as_py() or 0


TMP.parent.mkdir(parents=True, exist_ok=True)
if not TMP.exists():
    print(f"tải shard {I}…")
    req = urllib.request.Request(URL, headers={"User-Agent": "policyradar/0.1"})
    with urllib.request.urlopen(req) as r, TMP.open("wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    print("xong")

tbl = pq.read_table(TMP, columns=["year", "doc_type", "markdown"])
print(f"\nshard {I}: {tbl.num_rows} dòng")

m_year = pc.fill_null(pc.greater_equal(tbl["year"], 2018), False)
m_type = pc.fill_null(pc.is_in(tbl["doc_type"], value_set=TYPES), False)

md_low = pc.utf8_lower(tbl["markdown"])
m_kw = None
print("\n-- keyword (toàn shard) --")
for k in KWS:
    m = pc.fill_null(pc.match_substring(md_low, k), False)
    print(f"   {k:26} {n(m):5}")
    m_kw = m if m_kw is None else pc.or_(m_kw, m)

print("\n-- phễu --")
print(f"   year>=2018                 {n(m_year):5}")
print(f"   doc_type hợp lệ            {n(m_type):5}")
print(f"   chạm >=1 keyword           {n(m_kw):5}")
print(f"   year & type                {n(pc.and_(m_year, m_type)):5}")
print(f"   year & type & kw   ==>     {n(pc.and_(pc.and_(m_year, m_type), m_kw)):5}")

print("\n-- phân bố year (top) --")
vc = pc.value_counts(tbl["year"])
rows = sorted(
    [(x["values"].as_py(), x["counts"].as_py()) for x in vc], key=lambda r: -r[1]
)[:8]
for y, c in rows:
    print(f"   {y}: {c}")
print(f"\n   year>=2018 chiếm {n(m_year)}/{tbl.num_rows}")
