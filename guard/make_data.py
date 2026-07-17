"""Sinh dữ liệu train guard: corpus → cặp (premise, hypothesis, label) → JSONL.

Chạy: uv run --python 3.11 --with pyarrow python guard/make_data.py
      uv run --python 3.11 --with pyarrow python guard/make_data.py --xem   # chỉ in mẫu
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402
from guard.corrupt import TrichDan, sinh_cap  # noqa: E402

IN = Path("./data/splits_dn")
OUT = Path("./data/guard")
SEED = 7


def sinh_cho_phia(ten: str, gioi_han_vb: int | None = None) -> list:
    tbl = pq.read_table(
        IN / f"{ten}.parquet",
        columns=["item_id", "doc_number_str", "issuing_authority", "markdown"],
    )
    rng = random.Random(SEED)
    ra = []
    n = tbl.num_rows if gioi_han_vb is None else min(gioi_han_vb, tbl.num_rows)

    for i in range(n):
        md = tbl["markdown"][i].as_py()
        if not md:
            continue
        doc_id = tbl["item_id"][i].as_py()
        so_vb = tbl["doc_number_str"][i].as_py() or "(không rõ số)"
        co_quan = tbl["issuing_authority"][i].as_py() or "(không rõ cơ quan)"

        for d in parse(md):
            for k in d.khoan:
                if not (60 < len(k.text) < 3000):
                    continue
                cit = TrichDan(so_vb, co_quan, d.so, k.so)
                ra.extend(sinh_cap(k.text, cit, doc_id, rng))
    return ra


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xem", action="store_true", help="chỉ in mẫu, không ghi file")
    ap.add_argument("--gioi-han", type=int, default=None, help="giới hạn số văn bản/phía")
    args = ap.parse_args()

    if args.xem:
        cap = sinh_cho_phia("test", gioi_han_vb=12)
        rng = random.Random(1)
        print("=" * 70)
        print("ĐỌC BẰNG MẮT — hard-negative có ĐÁNG TIN không?")
        print("=" * 70)
        pos = [c for c in cap if c.label == 1]
        neg = [c for c in cap if c.label == 0]
        print(f"(sinh {len(cap)} cặp từ 12 văn bản: {len(pos)} thật / {len(neg)} bịa)\n")

        if pos:
            p = rng.choice(pos)
            print("── POSITIVE ─────────────────────────────────────────")
            print(f"  NGUỒN : {p.premise[:190]}…")
            print(f"  CLAIM : {p.hypothesis[:190]}…\n")

        loai = sorted({c.corruption_type for c in neg if c.corruption_type})
        for lo in loai:
            ds = [c for c in neg if c.corruption_type == lo]
            c = rng.choice(ds)
            print(f"── {lo}  (n={len(ds)}) ───────────────────")
            print(f"  CLAIM : {c.hypothesis[:190]}…")
            if c.gia_tri_goc:
                print(f"  gốc   : {c.gia_tri_goc}   →   bịa: {c.gia_tri_bia}")
            print()
        return

    OUT.mkdir(parents=True, exist_ok=True)
    tong = Counter()
    for ten in ("train", "calib", "test"):
        cap = sinh_cho_phia(ten, args.gioi_han)
        f = OUT / f"{ten}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for c in cap:
                fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

        pos = sum(1 for c in cap if c.label == 1)
        neg = len(cap) - pos
        print(f"{ten:6} {len(cap):7,} cặp  ({pos:6,} thật / {neg:6,} bịa)  → {f.name}"
              f"  {f.stat().st_size / 1e6:.1f} MB")
        for c in cap:
            tong[c.corruption_type or "(positive)"] += 1

    print("\n=== Phân bố theo trục ===")
    for k, v in tong.most_common():
        print(f"  {str(k):28} {v:7,}")

    # kiểm cân bằng — lệch quá thì model chỉ học 1 mẹo
    n_pos = tong["(positive)"]
    n_neg = sum(v for k, v in tong.items() if k != "(positive)")
    print(f"\n  positive:negative = 1 : {n_neg / max(n_pos, 1):.1f}")
    if n_neg / max(n_pos, 1) > 6:
        print("  ⚠ lệch nhiều — cân lại lúc train (undersample negative).")


if __name__ == "__main__":
    main()
