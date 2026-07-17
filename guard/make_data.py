"""Sinh dữ liệu train guard: corpus → cặp (premise, hypothesis, label) → JSONL.

Chạy: uv run --python 3.11 --with pyarrow python guard/make_data.py
      uv run --python 3.11 --with pyarrow python guard/make_data.py --xem   # chỉ in mẫu
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402
from guard.corrupt import (  # noqa: E402
    LTO_TEST_KIEU,
    LTO_TRAIN_KIEU,
    TrichDan,
    sinh_cap,
)

IN = Path("./data/splits_dn")
OUT = Path("./data/guard")
SEED = 7


def sinh_cho_phia(
    ten: str, gioi_han_vb: int | None = None, kieu_cho_phep: set[str] | None = None
) -> list:
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
                ra.extend(sinh_cap(k.text, cit, doc_id, rng, kieu_cho_phep))
    return ra


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xem", action="store_true", help="chỉ in mẫu, không ghi file")
    ap.add_argument("--gioi-han", type=int, default=None, help="giới hạn số văn bản/phía")
    ap.add_argument("--lto", choices=("off", "kieu"), default="off",
                    help="kieu = Leave-Templates-Out: train học 2 kiểu ngữ nghĩa, test 2 kiểu khác")
    args = ap.parse_args()

    # LTO: chia kiểu ngữ nghĩa RỜI train/test. calib theo train-side (chọn T/ngưỡng
    # không được rò template test-side vào). off → None (mọi kiểu, đường cũ tái lập).
    kieu_phia = (
        {"train": LTO_TRAIN_KIEU, "calib": LTO_TRAIN_KIEU, "test": LTO_TEST_KIEU}
        if args.lto == "kieu"
        else {"train": None, "calib": None, "test": None}
    )

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

    # sinh cả 3 phía TRƯỚC, rồi mới dọn — vì dọn cần biết test có gì.
    kho = {
        ten: sinh_cho_phia(ten, args.gioi_han, kieu_phia[ten])
        for ten in ("train", "calib", "test")
    }

    # ── GỠ RÒ RỈ PREMISE ────────────────────────────────────────
    # soi_data.py bắt: 9 đoạn nguồn nằm ở CẢ train lẫn test dù doc_id đã tách.
    # Vì sao: điều khoản mẫu ("Thông tư này có hiệu lực từ…") lặp NGUYÊN VĂN ở
    # nhiều văn bản khác nhau → doc_id khác nhau mà text y hệt. Tách theo doc_id
    # KHÔNG bắt được ca này.
    # Dọn ở TRAIN, TUYỆT ĐỐI không đụng test — test là thước đo; sửa thước đo
    # để nó vừa với mình là tự lừa mình.
    def bam(s: str) -> str:
        return hashlib.md5(s.strip().encode()).hexdigest()

    cam = {bam(c.premise) for c in kho["test"]} | {bam(c.premise) for c in kho["calib"]}
    truoc = len(kho["train"])
    kho["train"] = [c for c in kho["train"] if bam(c.premise) not in cam]
    bo = truoc - len(kho["train"])
    print(f"Gỡ rò rỉ premise: bỏ {bo} cặp khỏi TRAIN (nguồn trùng test/calib)\n")

    # ── CÂN NHÃN ────────────────────────────────────────────────
    # Hạ negative xuống ngang positive, hạ ĐỀU theo từng trục để giữ nguyên
    # tỉ lệ trục đã cân công phu (~40% định danh / 35% số / 25% ngữ nghĩa).
    # Chỉ cân TRAIN. test/calib giữ phân bố tự nhiên để đo cho thật.
    def can_bang(ds: list, rng: random.Random) -> list:
        pos = [c for c in ds if c.label == 1]
        neg = [c for c in ds if c.label == 0]
        if not pos or len(neg) <= len(pos):
            return ds
        ty = len(pos) / len(neg)  # hạ mỗi trục theo cùng một tỉ lệ
        theo: dict = {}
        for c in neg:
            theo.setdefault(c.corruption_type, []).append(c)
        giu = []
        for _, ds_t in sorted(theo.items(), key=lambda x: str(x[0])):
            k = max(1, round(len(ds_t) * ty))
            giu += rng.sample(ds_t, min(k, len(ds_t)))
        return pos + giu

    kho["train"] = can_bang(kho["train"], random.Random(SEED))

    for ten in ("train", "calib", "test"):
        cap = kho[ten]
        f = OUT / f"{ten}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for c in cap:
                fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

        pos = sum(1 for c in cap if c.label == 1)
        neg = len(cap) - pos
        print(f"{ten:6} {len(cap):7,} cặp  ({pos:6,} thật / {neg:6,} bịa"
              f" = {pos/max(len(cap),1)*100:.0f}%/{neg/max(len(cap),1)*100:.0f}%)  → {f.name}"
              f"  {f.stat().st_size / 1e6:.1f} MB")
        if ten == "train":
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

    # ── MANIFEST LTO cho giám khảo: chứng minh KHÔNG tra bảng ──
    if args.lto == "kieu":
        def kieu_trong(ten: str) -> set:
            return {c.corruption_type for c in kho[ten]
                    if c.corruption_type in (LTO_TRAIN_KIEU | LTO_TEST_KIEU)}
        k_tr, k_te = kieu_trong("train"), kieu_trong("test")
        giao = k_tr & k_te
        print("\n=== MANIFEST LEAVE-TEMPLATES-OUT ===")
        print(f"  kiểu ngữ nghĩa TRAIN-side: {sorted(k_tr)}")
        print(f"  kiểu ngữ nghĩa TEST-side : {sorted(k_te)}")
        print(f"  GIAO train∩test          : {sorted(giao)}  {'✓ RỖNG' if not giao else '✗ RÒ!'}")
        assert not giao, "LTO hỏng: kiểu ngữ nghĩa train và test trùng nhau"
        for ten in ("train", "test"):
            n_tc = sum(1 for c in kho[ten] if c.corruption_type == "bia_ngu_nghia_tai_cho")
            print(f"  trục phá-cue (bia_ngu_nghia_tai_cho) ở {ten}: {n_tc:,} cặp")


if __name__ == "__main__":
    main()
