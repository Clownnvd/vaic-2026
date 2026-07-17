"""Lọc corpus → chỉ giữ văn bản CHỦ ĐỀ doanh nghiệp/đầu tư/công nghệ, rồi chia lại.

VÌ SAO: audit cho thấy 9.299 văn bản khớp keyword-toàn-văn nhưng chỉ ~28% thật sự
về DN/đầu tư/công nghệ. Số còn lại là y tế, đất đai, nông nghiệp, người có công…
Keyword "ưu đãi" dính cả "trợ cấp ưu đãi người có công với cách mạng".
→ Lọc thêm theo TITLE. Guard train trên đúng phân bố nó sẽ gác lúc chạy thật.

Split giữ nguyên công thức md5(item_id) → văn bản nào ở phía nào vẫn y như cũ,
lọc chỉ bỏ bớt, KHÔNG xáo lại (nên vẫn không rò rỉ).

Chạy: uv run --python 3.11 --with pyarrow python scripts/filter_dn.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0, ".")
from corpus.parse_dieu import don_vi_trich_dan  # noqa: E402
from matcher.loc_dieu6 import nhay_cam  # noqa: E402
from scripts.split_corpus import bucket  # noqa: E402

# chủ đề DN/đầu tư/công nghệ — cùng regex đã dùng lúc audit
RE_DN = re.compile(
    r"doanh nghiệp|đầu tư|khởi nghiệp|công nghệ|khoa học|đổi mới sáng tạo"
    r"|chuyển đổi số|kinh tế|thuế|tín dụng|xuất khẩu|công nghiệp|hợp tác xã"
)

IN = Path("./data/vbpl_flagship.parquet")
OUT = Path("./data/splits_dn")


def main() -> None:
    tbl = pq.read_table(IN)
    print(f"corpus đầy đủ: {tbl.num_rows:,} văn bản")

    titles = tbl["title"].to_pylist()
    giu_chu_de = [bool(RE_DN.search((t or "").lower())) for t in titles]
    dn = tbl.filter(pa.array(giu_chu_de))
    print(f"chủ đề DN/đầu tư/công nghệ: {dn.num_rows:,} ({dn.num_rows / tbl.num_rows * 100:.1f}%)")

    # ── ĐIỀU 6 luật thi: loại văn bản nhạy cảm khỏi phạm vi matcher ──
    # "Đội thi có trách nhiệm KIỂM TRA KỸ... không chứa nội dung sai lệch hoặc không
    #  phù hợp liên quan đến chính trị, biên giới, lãnh thổ, chủ quyền quốc gia và biển đảo"
    # Đây là KIỂM TRA CHỦ ĐỘNG. Mấy văn bản này lọt vào vì đúng chủ đề kinh tế, nhưng
    # không liên quan ưu đãi DN → loại đi mất 0 giá trị, bớt 100% rủi ro.
    t_dn = dn["title"].to_pylist()
    d_dn = dn["doc_number_str"].to_pylist()
    mask6 = [not nhay_cam(t) for t in t_dn]
    bo6 = [(d_dn[i], t_dn[i]) for i, ok in enumerate(mask6) if not ok]

    dn = dn.filter(pa.array(mask6))
    print(f"sau lọc điều 6            : {dn.num_rows:,}  (loại {len(bo6)} văn bản nhạy cảm)")
    if bo6:
        print("  ĐÃ LOẠI theo điều 6 — ghi ra để GIẢI TRÌNH, không giấu:")
        for d, t in bo6:
            print(f"    • {str(d)[:22]:24} {(t or '')[:56]}")
    print()

    OUT.mkdir(parents=True, exist_ok=True)
    phia = [bucket(i) for i in dn["item_id"].to_pylist()]
    dn = dn.append_column("split", pa.array(phia, pa.string()))

    tap = {}
    for ten in ("train", "calib", "test"):
        con = dn.filter(pc.equal(dn["split"], ten))
        pq.write_table(con, OUT / f"{ten}.parquet", compression="zstd")
        tap[ten] = con

    # ── assert lại: lọc xong vẫn không rò rỉ ──────────────────
    ids = {k: set(v["item_id"].to_pylist()) for k, v in tap.items()}
    for a, b in (("train", "calib"), ("train", "test"), ("calib", "test")):
        assert not (ids[a] & ids[b]), f"RÒ RỈ {a}∩{b}"
    print("✓ assert chống rò rỉ: train∩calib = train∩test = calib∩test = ∅\n")

    # ── ĐO SẢN LƯỢNG KHOẢN — câu hỏi thật sự: có đủ để train không? ──
    print("=" * 58)
    print("SẢN LƯỢNG KHOẢN (đơn vị premise cho NLI)")
    print("=" * 58)
    print(f"{'phía':8} {'văn bản':>9} {'khoản':>10} {'khoản/vb':>9}")
    tong_k = 0
    for ten, con in tap.items():
        mds = con["markdown"].to_pylist()
        # đếm trên mẫu 200 vb rồi suy ra — chỉ để ƯỚC LƯỢNG, có ghi rõ
        mau = mds[:200]
        k_mau = sum(len(don_vi_trich_dan(m or "")) for m in mau)
        tb = k_mau / max(len(mau), 1)
        uoc = int(tb * con.num_rows)
        tong_k += uoc
        print(f"{ten:8} {con.num_rows:9,} {uoc:10,} {tb:9.1f}   (ước lượng từ {len(mau)} vb)")

    print(f"\nTổng ước lượng: ~{tong_k:,} khoản")
    print("\nKế hoạch cần: ~3-5k positive + ~5-10k hard-negative + 1k test.")
    print(f"⇒ {'ĐỦ XA' if tong_k > 50_000 else 'CẦN KIỂM LẠI'} — thừa sức train.")
    print(f"\nXong → {OUT}/")


if __name__ == "__main__":
    main()
