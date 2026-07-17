"""Kiểm parser Điều/Khoản trên văn bản THẬT + đo token PhoBERT THẬT.

Không tin số suông — in ra để đọc bằng mắt.
Chạy: uv run --python 3.11 --with pyarrow --with transformers python corpus/test_parse.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, ".")

import pyarrow.parquet as pq  # noqa: E402

from corpus.parse_dieu import don_vi_trich_dan, parse  # noqa: E402


def pv(xs: list[int], p: float) -> int:
    s = sorted(xs)
    return s[min(int(len(s) * p), len(s) - 1)] if s else 0


tbl = pq.read_table(
    Path("./data/splits/train.parquet"), columns=["markdown", "doc_number_str", "title"]
)
mds = tbl["markdown"].to_pylist()
dns = tbl["doc_number_str"].to_pylist()

# ── 1. PHỦ ─────────────────────────────────────────────────────
print("=" * 66)
print("1. PARSER PHỦ ĐƯỢC BAO NHIÊU?")
print("=" * 66)
N = 800
co_dieu = 0
tong_dieu = 0
tong_khoan = 0
tong_diem = 0
for md in mds[:N]:
    ds = parse(md or "")
    if ds:
        co_dieu += 1
        tong_dieu += len(ds)
        tong_khoan += sum(len(d.khoan) for d in ds)
        tong_diem += sum(len(k.diem) for d in ds for k in d.khoan)

print(f"  {co_dieu}/{N} văn bản parse ra ≥1 Điều  ({co_dieu / N * 100:.0f}%)")
print(f"  Tổng: {tong_dieu:,} điều · {tong_khoan:,} khoản · {tong_diem:,} điểm")
print(f"  TB: {tong_dieu / max(co_dieu,1):.1f} điều/văn bản · {tong_khoan / max(tong_dieu,1):.1f} khoản/điều")

# ── 2. MẮT NGƯỜI ĐỌC ───────────────────────────────────────────
print("\n" + "=" * 66)
print("2. ĐỌC BẰNG MẮT — parser cắt ĐÚNG chỗ không?")
print("=" * 66)
dem = 0
for md, dn in zip(mds, dns):
    ds = parse(md or "")
    if len(ds) >= 3 and any(d.khoan for d in ds):
        print(f"\n  ┌─ [{dn}] → {len(ds)} điều")
        for d in ds[:3]:
            print(f"  │ Điều {d.so}. {d.tieu_de[:56]}")
            for k in d.khoan[:2]:
                print(f"  │    └ Khoản {k.so}: {k.text[:88]}…")
                for dm in k.diem[:1]:
                    print(f"  │        └ điểm {dm.ky_hieu}) {dm.text[:70]}…")
        dem += 1
    if dem >= 3:
        break

# ── 3. ĐO TOKEN THẬT ───────────────────────────────────────────
print("\n\n" + "=" * 66)
print("3. TOKEN THẬT trên ĐƠN VỊ TRÍCH DẪN (khoản)")
print("=" * 66)
units: list[str] = []
for md in mds[:600]:
    units.extend(t for _, t in don_vi_trich_dan(md or ""))
print(f"  Bóc {len(units):,} đơn vị trích dẫn từ 600 văn bản")

if not units:
    raise SystemExit("  ⚠ 0 đơn vị — parser hỏng!")

from transformers import AutoTokenizer  # noqa: E402

tok = AutoTokenizer.from_pretrained("vinai/phobert-base")
mau = units[:4000]
lens = [len(tok.encode(u, truncation=False)) for u in mau]

print(f"\n  Token/khoản (n={len(lens):,}) — tokenizer PhoBERT thật:")
for p in (0.5, 0.75, 0.9, 0.95, 0.99):
    print(f"    p{int(p*100):<3} = {pv(lens, p):>5}")
print(f"    max  = {max(lens):>5}")
print()
for n in (128, 256):
    print(f"    vượt {n:>3}: {sum(1 for x in lens if x > n) / len(lens) * 100:5.1f}%")

q128 = sum(1 for x in lens if x > 128) / len(lens) * 100
q256 = sum(1 for x in lens if x > 256) / len(lens) * 100
print(f"\n  ⇒ CHỐT max_len = {128 if q128 <= 10 else 256}")
print(f"    cắt ở 128 mất {q128:.1f}% · ở 256 mất {q256:.1f}%")
print("    (PhoBERT trần 256 token — dài hơn phải cửa sổ trượt)")
