"""'Điều N' có thật trong markdown không — hay chỉ regex của mình sai?

Kết luận sai ở đây là hỏng cả thiết kế Citation. Phải kiểm bằng nhiều cách.
Chạy: uv run --python 3.11 --with pyarrow python scripts/inspect_dieu.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pyarrow.parquet as pq

tbl = pq.read_table(Path("./data/splits/train.parquet"), columns=["markdown", "doc_number_str", "doc_type"])
mds = [x for x in tbl["markdown"][:500].to_pylist() if x]

print(f"{len(mds)} văn bản\n")

# ── markdown có xuống dòng không? ────────────────────────────
nl = [m.count("\n") for m in mds]
print("=== CÓ XUỐNG DÒNG KHÔNG? ===")
print(f"  số '\\n' trung vị: {sorted(nl)[len(nl) // 2]}")
print(f"  văn bản 0 xuống dòng: {sum(1 for x in nl if x == 0)}/{len(mds)}")

# ── 'Điều' đếm theo nhiều cách ───────────────────────────────
print("\n=== 'Điều' xuất hiện thế nào ===")
cach = {
    "^Điều N  (đầu dòng, re.M)": re.compile(r"^\s*Điều\s+\d+", re.M),
    "Điều N   (bất kỳ đâu)": re.compile(r"Điều\s+\d+"),
    "điều N   (không hoa)": re.compile(r"(?i)điều\s+\d+"),
    "Khoản N": re.compile(r"(?i)khoản\s+\d+"),
    "Chương N/La Mã": re.compile(r"(?i)chương\s+[IVXĐ\d]+"),
}
for ten, re_ in cach.items():
    co = sum(1 for m in mds if re_.search(m))
    tong = sum(len(re_.findall(m)) for m in mds)
    print(f"  {ten:30} {co:3}/{len(mds)} văn bản  |  tổng {tong:6,} lần")

# ── mẫu quanh chữ 'Điều' ─────────────────────────────────────
print("\n=== NGỮ CẢNH quanh 'Điều N' (3 mẫu) ===")
r = re.compile(r"Điều\s+\d+")
dem = 0
for md, dn in zip(mds, tbl["doc_number_str"][:500].to_pylist()):
    for m in r.finditer(md):
        a, b = max(0, m.start() - 90), min(len(md), m.end() + 150)
        print(f"\n  [{dn}]")
        print(f"  …{md[a:b]}…".replace("\n", " "))
        dem += 1
        break
    if dem >= 3:
        break

# ── văn bản dài nhất trông thế nào ───────────────────────────
print("\n\n=== MẪU đầu 1 văn bản (700 ký tự đầu) ===")
i = max(range(len(mds)), key=lambda i: len(mds[i]))
print(f"  [{tbl['doc_number_str'][i].as_py()}] dài {len(mds[i]):,} ký tự")
print(f"  {mds[i][:700]}")
