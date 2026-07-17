"""AUDIT CHẤT LƯỢNG corpus — 9.299 văn bản này có THẬT SỰ liên quan đề không?

Nghi ngờ: keyword "ưu đãi" trong luật VN phần lớn là "ưu đãi NGƯỜI CÓ CÔNG với
cách mạng", không phải ưu đãi doanh nghiệp. Nếu đúng thì corpus đầy rác và
matcher sẽ trả kết quả vô nghĩa.

Chạy: uv run --python 3.11 --with pyarrow python scripts/audit_corpus.py
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

tbl = pq.read_table(Path("./data/vbpl_flagship.parquet"))
print(f"corpus: {tbl.num_rows:,} văn bản\n")

titles = [t or "" for t in tbl["title"].to_pylist()]
dns = [d or "" for d in tbl["doc_number_str"].to_pylist()]
auth = [a or "" for a in tbl["issuing_authority"].to_pylist()]

# ── 1. TRÙNG LẶP ────────────────────────────────────────────────
print("=" * 66)
print("1. TRÙNG LẶP")
print("=" * 66)
c_dn = Counter(dns)
trung = [(k, v) for k, v in c_dn.most_common(8) if v > 1]
print(f"  doc_number trùng: {sum(v - 1 for _, v in c_dn.items() if v > 1):,} bản dư")
for k, v in trung[:6]:
    print(f"    {k:26} ×{v}")
print(f"  item_id duy nhất: {len(set(tbl['item_id'].to_pylist())):,}/{tbl.num_rows:,}")

# ── 2. CHỦ ĐỀ THẬT — đọc TITLE ─────────────────────────────────
print("\n" + "=" * 66)
print("2. CHỦ ĐỀ THẬT (đọc title, không tin keyword trong toàn văn)")
print("=" * 66)

CHUDE = {
    "DN/đầu tư/công nghệ ⭐": r"doanh nghiệp|đầu tư|khởi nghiệp|công nghệ|khoa học|đổi mới sáng tạo|chuyển đổi số|kinh tế|thuế|tín dụng|xuất khẩu|công nghiệp|hợp tác xã",
    "người có công/liệt sĩ": r"người có công|liệt sĩ|thương binh|cách mạng|chính sách xã hội",
    "y tế/giáo dục": r"y tế|bệnh viện|khám|chữa bệnh|giáo dục|trường|học sinh|sinh viên",
    "đất đai/xây dựng": r"đất đai|xây dựng|quy hoạch|nhà ở|bất động sản",
    "nông nghiệp": r"nông nghiệp|nông thôn|thủy sản|lâm nghiệp|chăn nuôi",
    "hành chính/tổ chức": r"tổ chức bộ máy|cán bộ|công chức|viên chức|thủ tục hành chính|quy chế làm việc",
}
dem = Counter()
for t in titles:
    tl = t.lower()
    khop = [k for k, p in CHUDE.items() if re.search(p, tl)]
    if not khop:
        dem["(khác/không rõ)"] += 1
    for k in khop:
        dem[k] += 1

for k, v in dem.most_common():
    print(f"  {k:26} {v:6,}  ({v / tbl.num_rows * 100:5.1f}%)")

# ── 3. "ưu đãi" thật sự nói về cái gì ──────────────────────────
print("\n" + "=" * 66)
print("3. 'ưu đãi' trong TITLE nói về gì?")
print("=" * 66)
uu = [t for t in titles if "ưu đãi" in t.lower()]
print(f"  {len(uu)} văn bản có 'ưu đãi' ngay trong title\n")
for t in uu[:12]:
    print(f"    • {t[:88]}")

# ── 4. CƠ QUAN BAN HÀNH ────────────────────────────────────────
print("\n" + "=" * 66)
print("4. CƠ QUAN BAN HÀNH (UBND tỉnh = chính sách địa phương)")
print("=" * 66)
ubnd = sum(1 for a in auth if "ủy ban nhân dân" in a.lower() or "uỷ ban nhân dân" in a.lower())
print(f"  UBND tỉnh/huyện: {ubnd:,} ({ubnd / tbl.num_rows * 100:.1f}%)")
for k, v in Counter(auth).most_common(10):
    print(f"    {str(k)[:46]:48} {v:5,}")

# ── 5. LỌC HẸP: title phải chạm chủ đề DN ─────────────────────
print("\n" + "=" * 66)
print("5. NẾU SIẾT: title phải chạm chủ đề doanh nghiệp/công nghệ")
print("=" * 66)
RE_DN = re.compile(CHUDE["DN/đầu tư/công nghệ ⭐"])
hep = [t for t in titles if RE_DN.search(t.lower())]
print(f"  Còn lại: {len(hep):,}/{tbl.num_rows:,}  ({len(hep) / tbl.num_rows * 100:.1f}%)")

RE_HEP = re.compile(
    r"ưu đãi|hỗ trợ doanh nghiệp|khởi nghiệp|đổi mới sáng tạo|công nghệ cao"
    r"|doanh nghiệp nhỏ và vừa|khoa học và công nghệ|chuyển đổi số|đầu tư"
)
hep2 = [t for t in titles if RE_HEP.search(t.lower())]
print(f"  Siết chặt hơn (title chạm keyword chính sách DN): {len(hep2):,}"
      f"  ({len(hep2) / tbl.num_rows * 100:.1f}%)")
print("\n  Mẫu 12 văn bản sau khi siết:")
for t in hep2[:12]:
    print(f"    • {t[:88]}")
