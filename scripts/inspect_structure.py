"""Soi structure_json THẬT + đo token bằng tokenizer PhoBERT THẬT.

Hai câu phải trả lời chính xác, không ước lượng:
  1. structure_json có cây điều→khoản→điểm không, hay chỉ sections/paragraphs?
     → quyết định Citation trỏ vào đâu.
  2. Một KHOẢN dài bao nhiêu token PhoBERT thật? → chốt max_len.

Chạy: uv run --python 3.11 --with pyarrow --with transformers --with torch python scripts/inspect_structure.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pyarrow.parquet as pq

F = Path("./data/splits/train.parquet")


def phan_vi(xs: list[int], p: float) -> int:
    s = sorted(xs)
    return s[min(int(len(s) * p), len(s) - 1)] if s else 0


tbl = pq.read_table(F, columns=["structure_json", "markdown", "doc_number_str"])

# ── 1. CẤU TRÚC THẬT ────────────────────────────────────────────────
print("=" * 64)
print("1. structure_json — CẤU TRÚC THẬT")
print("=" * 64)
d = json.loads(tbl["structure_json"][0].as_py())
print("  Khoá gốc:", list(d.keys()))
print("  meta:", list(d.get("meta", {}).keys()))
print("  stats:", d.get("stats"))

for ten in ("sections", "paragraphs", "sentences"):
    v = d.get(ten)
    if isinstance(v, list) and v:
        print(f"\n  --- {ten}: {len(v)} phần tử, phần tử đầu ---")
        print(f"  {json.dumps(v[0], ensure_ascii=False)[:420]}")

# ── 2. CÓ ĐIỀU/KHOẢN TRONG MARKDOWN KHÔNG? ─────────────────────────
print("\n" + "=" * 64)
print("2. ĐIỀU / KHOẢN có trong markdown không?")
print("=" * 64)
RE_DIEU = re.compile(r"^\s*Điều\s+(\d+)[.\s]", re.M)
RE_KHOAN = re.compile(r"^\s*(\d+)\.\s+", re.M)

co_dieu = 0
tong_dieu = 0
mds = [x for x in tbl["markdown"][:500].to_pylist() if x]
for md in mds:
    n = len(RE_DIEU.findall(md))
    if n:
        co_dieu += 1
        tong_dieu += n
print(f"  {co_dieu}/{len(mds)} văn bản có 'Điều N' trong markdown ({co_dieu / len(mds) * 100:.0f}%)")
print(f"  Trung bình {tong_dieu / max(co_dieu, 1):.1f} điều/văn bản")

# ── 3. BÓC KHOẢN THẬT rồi ĐO TOKEN THẬT ────────────────────────────
print("\n" + "=" * 64)
print("3. ĐO TOKEN BẰNG PhoBERT THẬT (không ước lượng)")
print("=" * 64)


def boc_khoan(md: str) -> list[str]:
    """Cắt markdown theo 'Điều N', trong mỗi điều cắt tiếp theo '1. 2. 3.' = khoản."""
    ra = []
    phan = RE_DIEU.split(md)
    # phan = [đầu, so_dieu, than, so_dieu, than, ...]
    for i in range(1, len(phan) - 1, 2):
        than = phan[i + 1]
        khoan = RE_KHOAN.split(than)
        if len(khoan) > 1:
            for j in range(1, len(khoan) - 1, 2):
                t = khoan[j + 1].strip()
                if 30 < len(t) < 8000:
                    ra.append(t)
        else:
            t = than.strip()
            if 30 < len(t) < 8000:
                ra.append(t)
    return ra


khoan_all: list[str] = []
for md in mds[:300]:
    khoan_all.extend(boc_khoan(md))

print(f"  Bóc được {len(khoan_all):,} khoản từ 300 văn bản")
if not khoan_all:
    raise SystemExit("  ⚠ Không bóc được khoản — regex sai, xem lại.")

print(f"  Mẫu khoản:")
for k in khoan_all[:2]:
    print(f"    « {k[:130].replace(chr(10), ' ')}… »")

from transformers import AutoTokenizer  # noqa: E402

print("\n  Nạp vinai/phobert-base (MIT)…")
tok = AutoTokenizer.from_pretrained("vinai/phobert-base")

mau = khoan_all[:3000]
lens = [len(tok.encode(k, truncation=False)) for k in mau]

print(f"\n  Token/khoản THẬT (n={len(lens):,}):")
for p in (0.5, 0.75, 0.9, 0.95, 0.99):
    print(f"    p{int(p * 100):<3} = {phan_vi(lens, p):>5}")
print(f"    max  = {max(lens):>5}")

for n in (128, 256, 384, 512):
    qua = sum(1 for x in lens if x > n) / len(lens) * 100
    print(f"    vượt {n:>3} token: {qua:5.1f}%")

qua128 = sum(1 for x in lens if x > 128) / len(lens) * 100
qua256 = sum(1 for x in lens if x > 256) / len(lens) * 100
chot = 128 if qua128 <= 10 else (256 if qua256 <= 10 else 512)
print(f"\n  ⇒ CHỐT max_len = {chot}")
print(f"    (cắt ở 128 mất {qua128:.1f}% khoản; ở 256 mất {qua256:.1f}%)")
print("    Lưu ý: PhoBERT tối đa 256 token — muốn dài hơn phải cắt cửa sổ trượt.")
