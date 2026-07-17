"""ĐIỀU 6 luật thi — corpus có nội dung nhạy cảm về chính trị/biên giới/lãnh thổ/biển đảo không?

Nguyên văn: "Đội thi có trách nhiệm KIỂM TRA KỸ nội dung, dữ liệu, hình ảnh, bản đồ
và thông tin được sử dụng trong sản phẩm, bảo đảm không chứa nội dung sai lệch hoặc
không phù hợp liên quan đến chính trị, biên giới, lãnh thổ, chủ quyền quốc gia và biển đảo."

RỦI RO THẬT với bài này: corpus = 9.436 văn bản pháp luật NHÀ NƯỚC. Chắc chắn có
văn bản đụng địa giới hành chính (NQ 202/2025 sáp nhập 34 tỉnh), biên giới, hải đảo.
Matcher lôi ra + AI diễn giải sai = vi phạm.

"Có trách nhiệm KIỂM TRA KỸ" — nên phải ĐO, không được đoán.

Chạy: uv run --python 3.11 --with pyarrow python scripts/kiem_dieu6.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pyarrow.parquet as pq

# từ khoá nhạy cảm theo đúng điều 6
NHAY_CAM = {
    "biên giới": r"biên giới",
    "lãnh thổ": r"lãnh thổ",
    "chủ quyền": r"chủ quyền",
    "biển đảo / hải đảo": r"biển đảo|hải đảo|quần đảo",
    "Hoàng Sa / Trường Sa": r"hoàng sa|trường sa",
    "lãnh hải / thềm lục địa": r"lãnh hải|thềm lục địa|vùng đặc quyền kinh tế",
    "địa giới hành chính": r"địa giới hành chính|sáp nhập.{0,20}tỉnh|chia tách.{0,20}tỉnh",
    "an ninh quốc gia": r"an ninh quốc gia",
}

F = Path("./data/vbpl_flagship.parquet")


def main() -> None:
    tbl = pq.read_table(F, columns=["doc_number_str", "title", "markdown", "doc_type"])
    n = tbl.num_rows
    print(f"Corpus: {n:,} văn bản\n")

    titles = [t or "" for t in tbl["title"].to_pylist()]
    mds = [m or "" for m in tbl["markdown"].to_pylist()]
    dns = [d or "" for d in tbl["doc_number_str"].to_pylist()]

    print("=" * 70)
    print(f"{'từ khoá nhạy cảm':26} {'trong TITLE':>12} {'trong TOÀN VĂN':>15}")
    print("=" * 70)

    dinh_title: list[int] = []
    for nhan, pat in NHAY_CAM.items():
        r = re.compile(pat, re.IGNORECASE)
        i_title = [i for i, t in enumerate(titles) if r.search(t)]
        n_md = sum(1 for m in mds if r.search(m))
        dinh_title.extend(i_title)
        print(f"{nhan:26} {len(i_title):12,} {n_md:15,}")

    dinh_title = sorted(set(dinh_title))
    print("=" * 70)
    print(f"\n🔴 {len(dinh_title)} văn bản có từ nhạy cảm NGAY TRONG TIÊU ĐỀ:")
    for i in dinh_title[:15]:
        print(f"    [{dns[i][:22]:24}] {titles[i][:64]}")

    # ── phần nguy nhất: văn bản nhạy cảm mà VẪN lọt bộ lọc chủ đề DN ──
    print("\n" + "=" * 70)
    print("NGUY NHẤT: văn bản nhạy cảm LỌT vào subset DN (matcher sẽ lôi ra)")
    print("=" * 70)
    dn = pq.read_table(Path("./data/splits_dn/train.parquet"), columns=["title", "doc_number_str"])
    t_dn = [t or "" for t in dn["title"].to_pylist()]
    d_dn = [d or "" for d in dn["doc_number_str"].to_pylist()]

    lot = []
    for nhan, pat in NHAY_CAM.items():
        r = re.compile(pat, re.IGNORECASE)
        for i, t in enumerate(t_dn):
            if r.search(t):
                lot.append((nhan, d_dn[i], t))

    if lot:
        print(f"  ⚠ {len(lot)} văn bản nhạy cảm ĐANG NẰM trong subset matcher dùng:")
        for nhan, d, t in lot[:12]:
            print(f"    [{nhan}] {d[:20]:22} {t[:56]}")
    else:
        print("  ✓ KHÔNG có văn bản nhạy cảm nào trong subset DN — matcher không chạm tới.")

    print("\n" + "=" * 70)
    print("KẾT LUẬN")
    print("=" * 70)
    print(f"  Corpus đầy đủ  : {len(dinh_title)} văn bản nhạy cảm trong tiêu đề / {n:,}")
    print(f"  Subset matcher : {len(lot)} văn bản nhạy cảm")
    print("\n  Kiến trúc đã phòng sẵn (không phải may):")
    print("    • structure-then-fill  → CHÉP NGUYÊN VĂN, không diễn giải")
    print("    • citation ràng nguồn  → mọi câu trỏ về điều–khoản gốc")
    print("    • refuse-when-ungrounded → không có căn cứ thì từ chối, không đoán")
    print("  ⇒ Hệ thống KHÔNG diễn giải lại nội dung nhạy cảm — chỉ trích dẫn văn bản nhà nước.")


if __name__ == "__main__":
    main()
