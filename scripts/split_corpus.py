"""Chia corpus flagship thành train / calib / test — CHIA THEO VĂN BẢN.

⚠️ VÌ SAO CHIA THEO VĂN BẢN CHỨ KHÔNG THEO DÒNG:
Guard được train trên các cặp (điều-khoản, claim). Một văn bản đẻ ra NHIỀU cặp.
Nếu Nghị định 80/2021 có mặt ở cả train lẫn test (dù là điều khác nhau), model
học thuộc nội dung văn bản đó → điểm test đẹp ảo. Đây là bẫy rò rỉ riêng của
domain luật, không có ở domain số tiền.
→ Một văn bản chỉ được nằm ở ĐÚNG MỘT phía.

Vì sao có tập CALIB riêng: temperature scaling (đòn #3) phải fit trên dữ liệu
KHÔNG dùng để train và KHÔNG phải test — nếu fit trên test thì ECE báo cáo là gian.

Băm bằng md5(item_id) chứ KHÔNG dùng hash() của Python — hash() bị salt ngẫu nhiên
mỗi lần chạy → split đổi sau mỗi lần chạy → không tái lập được.

Chạy: uv run --python 3.11 --with pyarrow python scripts/split_corpus.py
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

SEED = "policyradar-v1"  # đổi seed = đổi split; giữ cố định để tái lập
TY_LE = {"train": 0.80, "calib": 0.10, "test": 0.10}


def bucket(item_id: str) -> str:
    """md5(seed + item_id) → [0,1) → gán phía. Tất định, tái lập được."""
    h = hashlib.md5(f"{SEED}:{item_id}".encode()).hexdigest()
    x = int(h[:8], 16) / 0xFFFFFFFF
    if x < TY_LE["train"]:
        return "train"
    if x < TY_LE["train"] + TY_LE["calib"]:
        return "calib"
    return "test"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", type=Path, default=Path("./data/vbpl_flagship.parquet"))
    ap.add_argument("--out", type=Path, default=Path("./data/splits"))
    args = ap.parse_args()

    if not args.inp.exists():
        raise SystemExit(f"Chưa có {args.inp} — chạy build_corpus.py trước.")

    args.out.mkdir(parents=True, exist_ok=True)
    tbl = pq.read_table(args.inp)
    print(f"Corpus: {tbl.num_rows:,} văn bản\n")

    ids = tbl["item_id"].to_pylist()
    phia = [bucket(i) for i in ids]
    tbl = tbl.append_column("split", pa.array(phia, pa.string()))

    tong = {}
    for ten in ("train", "calib", "test"):
        m = pc.equal(tbl["split"], ten)
        con = tbl.filter(m)
        f = args.out / f"{ten}.parquet"
        pq.write_table(con, f, compression="zstd")
        tong[ten] = con
        print(
            f"  {ten:6} {con.num_rows:6,} văn bản  ({con.num_rows / tbl.num_rows * 100:4.1f}%)"
            f"  → {f.name}  {f.stat().st_size / 1e6:.1f} MB"
        )

    # ── KIỂM CHỨNG: không văn bản nào nằm 2 phía ─────────────────────────
    print("\n=== ASSERT chống rò rỉ ===")
    tap = {k: set(v["item_id"].to_pylist()) for k, v in tong.items()}
    for a, b in (("train", "calib"), ("train", "test"), ("calib", "test")):
        chung = tap[a] & tap[b]
        assert not chung, f"RÒ RỈ! {len(chung)} văn bản ở cả {a} và {b}: {list(chung)[:5]}"
        print(f"  ✓ {a} ∩ {b} = ∅")

    tong_id = sum(len(v) for v in tap.values())
    assert tong_id == tbl.num_rows, f"mất dòng: {tong_id} ≠ {tbl.num_rows}"
    print(f"  ✓ đủ dòng: {tong_id:,} = {tbl.num_rows:,}")

    # ── phân bố phải TƯƠNG ĐỒNG giữa các phía, kẻo test lệch chủ đề ──────
    print("\n=== Phân bố doc_type mỗi phía (%) ===")
    loai = sorted({x.as_py() for x in tbl["doc_type"]})
    print(f"  {'':6} " + " ".join(f"{l[:11]:>12}" for l in loai))
    for ten, con in tong.items():
        hang = []
        for l in loai:
            n = pc.sum(pc.cast(pc.equal(con["doc_type"], l), "int32")).as_py() or 0
            hang.append(f"{n / con.num_rows * 100:11.1f}%")
        print(f"  {ten:6} " + " ".join(hang))

    print("\n=== Năm trung vị mỗi phía ===")
    for ten, con in tong.items():
        ys = sorted(con["year"].to_pylist())
        print(f"  {ten:6} median={ys[len(ys) // 2]}  min={ys[0]}  max={ys[-1]}")

    print(f"\nXong → {args.out}/")


if __name__ == "__main__":
    main()
