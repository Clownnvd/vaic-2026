"""Test guard tất định. Chạy:
uv run --python 3.11 python guard/test_vn_number.py
"""

import sys

sys.path.insert(0, ".")
from guard.vn_number import bóc_số, lech_so, normalize_vn_number, parse_gia_tri  # noqa: E402

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan:44} {thuc!r}" + ("" if ok else f"  ≠ {mong!r}"))


print("=== normalize_vn_number ===")
eq(normalize_vn_number("20"), 20.0, "'20'")
eq(normalize_vn_number("2,5"), 2.5, "'2,5' phẩy = thập phân")
eq(normalize_vn_number("1.234"), 1234.0, "'1.234' chấm = ngăn nghìn")
eq(normalize_vn_number("1.234.567"), 1234567.0, "'1.234.567'")
eq(normalize_vn_number("1.234,56"), 1234.56, "'1.234,56' cả hai")
eq(normalize_vn_number("2.5"), 2.5, "'2.5' KHÔNG phải nhóm 3 → thập phân")
eq(normalize_vn_number("abc"), None, "rác → None")

print("\n=== parse_gia_tri ===")
eq(parse_gia_tri("20 tỷ"), 2e10, "'20 tỷ'")
eq(parse_gia_tri("1,5 triệu"), 1_500_000.0, "'1,5 triệu'")
eq(parse_gia_tri("50%"), 50.0, "'50%'")
eq(parse_gia_tri("300 triệu đồng"), 3e8, "'300 triệu đồng'")

print("\n=== bóc_số ===")
s = "hỗ trợ 50% chi phí, vốn dưới 20 tỷ đồng, nộp trước 30/9"
got = [(x.raw, x.gia_tri, x.loai) for x in bóc_số(s)]
for r in got:
    print(f"    {r}")
eq(any(x[2] == "phan_tram" and x[1] == 50.0 for x in got), True, "bắt 50%")
eq(any(x[2] == "tien" and x[1] == 2e10 for x in got), True, "bắt 20 tỷ")
eq(any(x[2] == "ngay" for x in got), True, "bắt ngày 30/9")

print("\n=== lech_so — TRÁI TIM CỦA GUARD ===")
nguon = "DNNVV được hỗ trợ 50% chi phí tư vấn, áp dụng với DN vốn dưới 20 tỷ đồng."

that = "Doanh nghiệp được hỗ trợ 50% chi phí, vốn dưới 20 tỷ đồng."
eq([x.raw for x in lech_so(that, nguon)], [], "câu ĐÚNG → không lệch")

bia_pt = "Doanh nghiệp được hỗ trợ 30% chi phí, vốn dưới 20 tỷ đồng."
r = lech_so(bia_pt, nguon)
eq([x.raw for x in r], ["30%"], "bịa 30% (nguồn 50%) → BẮT")

bia_von = "Được hỗ trợ 50% chi phí, vốn dưới 100 tỷ đồng."
r = lech_so(bia_von, nguon)
eq([x.raw for x in r], ["100 tỷ đồng"], "bịa ngưỡng 100 tỷ (nguồn 20 tỷ) → BẮT")

# bẫy đơn vị: 20 triệu vs 20 tỷ — cùng chữ số, khác bậc 1000×
bia_dv = "Được hỗ trợ 50% chi phí, vốn dưới 20 triệu đồng."
r = lech_so(bia_dv, nguon)
eq([x.raw for x in r], ["20 triệu đồng"], "bẫy đơn vị: 20 triệu ≠ 20 tỷ → BẮT")

print("\n" + ("=" * 50))
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
