"""Test bóc citation — nhắm đúng 3 dạng bản cũ BỎ LỌT.

Bằng chứng bug: dao_bia_that.py báo 79/120 câu GPT-4o "không kèm trích dẫn"
trong khi câu RÕ RÀNG có "Theo Khoản 4 Điều 10 Nghị định 57/2018/NĐ-CP...".

Chạy: uv run --python 3.11 python guard/test_boc_citation.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from guard.lookup import boc_citation  # noqa: E402

loi = 0


def kt(ten: str, cau: str, mong_vb: str | None, mong_dieu=None, mong_khoan="_"):
    global loi
    c = boc_citation(cau)
    got_vb = c.so_vb if c else None
    ok = got_vb == mong_vb
    if mong_dieu is not None and c:
        ok = ok and c.dieu == mong_dieu
    if mong_khoan != "_" and c:
        ok = ok and c.khoan == mong_khoan
    loi += 0 if ok else 1
    print(f"  {'✓' if ok else '✗'} {ten}")
    if not ok:
        got = f"vb={got_vb} dieu={c.dieu if c else '-'} khoan={c.khoan if c else '-'}"
        print(f"      câu : {cau[:70]}")
        print(f"      mong: vb={mong_vb} dieu={mong_dieu} khoan={mong_khoan}  ·  được: {got}")


print("── 3 DẠNG BẢN CŨ BỎ LỌT (câu GPT-4o thật) ──")
# 1. tiền tố "Nghị định" trước số hiệu
kt("tiền tố 'Nghị định' + Khoản-Điều",
   "Theo Khoản 4 Điều 10 Nghị định 57/2018/NĐ-CP do Chính phủ ban hành, doanh nghiệp...",
   "57/2018/NĐ-CP", 10, 4)
# 2. ĐIỀU TRƯỚC KHOẢN — chính Citation.__str__ của mình
kt("Điều trước Khoản (dạng Citation.__str__)",
   "Theo Điều 5 Khoản 3 80/2021/NĐ-CP, doanh nghiệp vừa...",
   "80/2021/NĐ-CP", 5, 3)
# 3. thiếu 'do ... ban hành'
kt("thiếu 'do ... ban hành'",
   "Căn cứ Điều 12 Khoản 1 13/2019/NĐ-CP, được miễn thuế 04 năm.",
   "13/2019/NĐ-CP", 12, 1)

print("\n── các dạng số hiệu khác nhau ──")
kt("NQ-HĐND + tiền tố 'Nghị quyết'",
   "Theo Khoản 6 Điều 1 Nghị quyết 77/2018/NQ-HĐND do HĐND Tỉnh Lâm Đồng ban hành...",
   "77/2018/NQ-HĐND", 1, 6)
kt("QĐ-UBND + tiền tố 'văn bản'",
   "Theo Khoản 3 Điều 4 văn bản 01/2018/QĐ-UBND do UBND thành phố Đà Nẵng ban hành...",
   "01/2018/QĐ-UBND", 4, 3)
kt("Luật QH (2 chữ số năm khác)",
   "Theo Điều 5 15/2023/QH15, ...",
   "15/2023/QH15", 5)

print("\n── chỉ tới cấp Điều (không Khoản) → vẫn bóc được ──")
kt("không có Khoản → khoan=None",
   "Theo Điều 7 80/2021/NĐ-CP, cách xác định lao động...",
   "80/2021/NĐ-CP", 7, None)

print("\n── KHÔNG có số VB → None (đúng) ──")
c = boc_citation("Doanh nghiệp của bạn đủ điều kiện nhận hỗ trợ.")
print(f"  {'✓' if c is None else '✗'} câu không số VB → None  (được: {c})")
loi += 0 if c is None else 1

print("\n── cơ quan bóc đúng khi có 'do ... ban hành' ──")
c = boc_citation("Theo Khoản 4 Điều 10 Nghị định 57/2018/NĐ-CP do Chính phủ ban hành, ...")
ok = c and c.co_quan == "Chính phủ"
print(f"  {'✓' if ok else '✗'} cơ quan = 'Chính phủ'  (được: {c.co_quan if c else '-'})")
loi += 0 if ok else 1

print("\n" + "=" * 52)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} LỖI ✗")
sys.exit(1 if loi else 0)
