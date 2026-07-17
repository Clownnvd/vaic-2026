"""Test tầng phòng ngừa. Chạy: uv run --python 3.11 python guard/test_fill.py"""

import sys

sys.path.insert(0, ".")
from guard.fill import dung_khung, mo_ta_slot, trich_slot  # noqa: E402

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


NGUON = (
    "Doanh nghiệp nhỏ và vừa được hỗ trợ 50% chi phí tư vấn, tối đa 20 triệu đồng/năm; "
    "hồ sơ nộp trước 30/9 hằng năm; áp dụng với doanh nghiệp có vốn điều lệ dưới 20 tỷ đồng."
)

print("=== BẢNG SLOT bóc từ nguồn ===")
slots = trich_slot(NGUON)
print(mo_ta_slot(slots))

print("\n=== LLM dùng slot ĐÚNG ===")
r = dung_khung("Doanh nghiệp được hỗ trợ {{s1}} chi phí tư vấn, nộp trước {{s3}}.", slots)
eq(r.ok, True, "khung hợp lệ → cho qua")
print(f"      → {r.text}")
eq("50%" in (r.text or ""), True, "số được CHÉP VERBATIM từ nguồn")

print("\n=== LLM TỰ GÕ SỐ (phải chặn) ===")
r = dung_khung("Doanh nghiệp được hỗ trợ 80% chi phí tư vấn.", slots)
eq(r.ok, False, "tự gõ '80%' → CHẶN")
print(f"      → {r.vi_pham}")

r = dung_khung("Vốn dưới 100 tỷ đồng là đủ điều kiện.", slots)
eq(r.ok, False, "tự gõ '100 tỷ đồng' → CHẶN")
print(f"      → {r.vi_pham}")

print("\n=== LLM gọi SLOT MA (phải chặn) ===")
r = dung_khung("Được hỗ trợ {{s99}} chi phí.", slots)
eq(r.ok, False, "gọi {{s99}} không có trong nguồn → CHẶN")
print(f"      → {r.vi_pham}")

print("\n=== ĐIỂM MẤU CHỐT ===")
print("  Với khung hợp lệ, số ra là bản SAO của nguồn.")
print("  Không có đường nào để '50%' biến thành '80%' — LLM không chạm vào số.")
r = dung_khung("Hỗ trợ {{s1}}, tối đa {{s2}}, hạn {{s3}}, vốn dưới {{s4}}.", slots)
if r.ok:
    print(f"  → {r.text}")
    tat_ca_tu_nguon = all(s.raw in NGUON for s in slots.values())
    eq(tat_ca_tu_nguon, True, "mọi slot đều là chuỗi có thật trong nguồn")

print("\n" + "=" * 52)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
