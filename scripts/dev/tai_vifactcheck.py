"""Tải ViFactCheck — thước đo NGOÀI để phá vòng tròn tự-ra-đề-tự-chấm.

VÌ SAO BỘ NÀY:
  • license MIT, khai trên card, `source_datasets: original` → là BẢN GỐC không phải mirror
  • nguồn khớp 3 tầng: HF tranthaihoa ↔ GitHub TTHHA ↔ tác giả paper Tran Thai Hoa
  • **7.232 cặp NGƯỜI GÁN NHÃN** — không phải máy sinh → thoát hẳn vòng tròn
  • SOTA công bố: Gemma macro-F1 89.90% (AAAI 2025) → có mốc để so
  • nhãn Supported / Refuted / NEI ↔ map thẳng sang du-can-cu / bia / chua-du-can-cu

ĐÃ LOẠI ViWikiFC: README trả HTTP 401 (repo khoá) + 19 lượt tải/tháng + 1 like
+ tác giả HF không khớp tác giả paper → nghi mirror không chính thức.

Chạy: uv run --python 3.11 --with datasets python scripts/tai_vifactcheck.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

OUT = Path("./data/ngoai")


def main() -> None:
    from datasets import load_dataset

    OUT.mkdir(parents=True, exist_ok=True)
    print("Tải tranthaihoa/vifactcheck …")
    ds = load_dataset("tranthaihoa/vifactcheck")

    print(f"\n=== SPLIT ===")
    for k, v in ds.items():
        print(f"  {k:8} {len(v):6,} dòng")

    cot = ds["train"].column_names
    print(f"\n=== CỘT ===\n  {cot}")

    print(f"\n=== NHÃN ===")
    for k in ds:
        nhan = [r for r in ds[k]["labels"]] if "labels" in cot else None
        if nhan:
            print(f"  {k:8} {dict(Counter(nhan))}")

    print(f"\n=== MẪU 1 DÒNG ===")
    r = ds["train"][0]
    for c in cot:
        v = str(r[c]).replace("\n", " ")
        print(f"  {c:12} : {v[:120]}")

    # xuất JSONL để guard đọc — cùng định dạng data của mình
    for k in ds:
        f = OUT / f"vifactcheck_{k}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for r in ds[k]:
                fh.write(json.dumps(dict(r), ensure_ascii=False) + "\n")
        print(f"\n  → {f}  ({f.stat().st_size / 1e6:.1f} MB)")

    print("\n" + "=" * 60)
    print("GHI CÔNG (điều 2 luật thi — BẮT BUỘC dù license MIT):")
    print("  ViFactCheck: A Multi-Domain Vietnamese News Fact-Checking Benchmark")
    print("  arXiv:2412.15308 (AAAI 2025) · HuggingFace: tranthaihoa/vifactcheck")
    print("  License: MIT (theo tag trên dataset card — repo KHÔNG có file LICENSE riêng)")


if __name__ == "__main__":
    main()
