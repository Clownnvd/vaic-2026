"""Đo lớp TẤT ĐỊNH trên test set — per-axis. Đây là con số quyết định.

So với model char n-gram (bắt bịa 0.03–0.20), lớp tất định phải nhảy lên gần 1.0
ở 6/7 trục. Nếu không → kiến trúc sai, phải nghĩ lại.

Chạy: uv run --python 3.11 --with pyarrow python guard/eval_tat_dinh.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")
from guard.check import KetLuan, kiem_tra  # noqa: E402
from guard.lookup import IndexCorpus  # noqa: E402


def main() -> None:
    print("Nạp index corpus…")
    idx = IndexCorpus(Path("./data/splits_dn/test.parquet"))
    print(f"  {len(idx):,} văn bản · {idx.so_khoa:,} số hiệu\n")

    rows = [json.loads(l) for l in Path("./data/guard/test.jsonl").read_text(encoding="utf-8").splitlines()]
    print(f"Test: {len(rows):,} cặp\n")

    bat = defaultdict(lambda: [0, 0])  # trục → [bắt được, tổng]
    tang_dung = Counter()
    fp = 0
    n_pos = 0

    for r in rows:
        pq = kiem_tra(r["hypothesis"], r["premise"], idx)
        chan = pq.ket_luan == KetLuan.CHAN

        if r["label"] == 1:
            n_pos += 1
            if chan:
                fp += 1  # BÁO ĐỘNG GIẢ — câu thật bị chặn
        else:
            lo = r["corruption_type"] or "?"
            bat[lo][1] += 1
            if chan:
                bat[lo][0] += 1
                tang_dung[pq.tang] += 1

    print("=" * 62)
    print("BẮT BỊA THEO TRỤC — lớp TẤT ĐỊNH")
    print("=" * 62)
    print(f"  {'trục':30} {'bắt':>7} {'n':>6}")
    tong_b = tong_n = 0
    for lo in sorted(bat):
        b, n = bat[lo]
        tong_b += b
        tong_n += n
        cd = "🟢" if b / max(n, 1) > 0.9 else ("🟡" if b / max(n, 1) > 0.5 else "🔴")
        print(f"  {lo:30} {b / max(n, 1):7.3f} {n:6,} {cd}")
    print(f"  {'TỔNG':30} {tong_b / max(tong_n, 1):7.3f} {tong_n:6,}")

    print(f"\n  Báo động giả (câu THẬT bị chặn): {fp}/{n_pos} = {fp / max(n_pos, 1):.3f}")
    if fp / max(n_pos, 1) > 0.05:
        print("  ⚠ báo động giả cao — guard chặn nhầm câu đúng, phải soi lại.")

    print("\n  Tầng nào ra quyết định:")
    for k, v in tang_dung.most_common():
        print(f"    {k:24} {v:6,}")


if __name__ == "__main__":
    main()
