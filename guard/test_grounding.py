"""Test enforce_grounding + citation binding.
Chạy: uv run --python 3.11 python guard/test_grounding.py
"""

import sys

sys.path.insert(0, ".")
from guard.grounding import (  # noqa: E402
    ModelRetry,
    NguonDaLay,
    TraLoi,
    VetTraCuu,
    kiem_tra_tra_loi,
    rang_citation,
)

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


# CODE ghi vết: đã thật sự lấy 2 khoản khỏi corpus
vet = VetTraCuu()
vet.ghi(NguonDaLay("d1", "80/2021/NĐ-CP", "Chính phủ", 5, 3, "…hỗ trợ 50%…"))
vet.ghi(NguonDaLay("d2", "80/2021/NĐ-CP", "Chính phủ", 6, 1, "…điều kiện…"))
print("Vết tra cứu thật:", sorted(vet.khoa_that), "\n")

print("=== enforce_grounding ===")
# THIẾT KẾ: citation = VẾT TRA CỨU, không phải lời LLM khai.
# LLM quên trích nhưng hệ thống CÓ tra thật → tự gắn nguồn thật, KHÔNG bắt viết lại.
r = kiem_tra_tra_loi(TraLoi("DN được hỗ trợ 50%.", grounded=True, citations=[]), vet)
eq(len(r.tra_loi.citations), 2, "LLM quên trích + vết CÓ nguồn → tự gắn 2 nguồn thật")
eq(sorted(r.da_them), sorted(vet.khoa_that), "nguồn gắn vào đúng bằng vết")

r = kiem_tra_tra_loi(TraLoi("Chưa đủ căn cứ.", grounded=False, citations=[]), vet)
eq(r.tra_loi.grounded, False, "không grounded + 0 citation → cho qua (từ chối là hợp lệ)")

# enforce chỉ nổ khi nói có-căn-cứ mà VẾT RỖNG — tức không hề tra gì
try:
    kiem_tra_tra_loi(TraLoi("DN được hỗ trợ 50%.", grounded=True, citations=[]), VetTraCuu())
    eq(True, False, "grounded + vết RỖNG → phải ném ModelRetry")
except ModelRetry:
    eq(True, True, "grounded + vết RỖNG → ModelRetry ✓")

print("\n=== citation binding — LOẠI nguồn LLM bịa ===")
tl = TraLoi(
    "DN được hỗ trợ 50%.",
    grounded=True,
    citations=["80/2021/NĐ-CP|Đ5|K3", "99/2026/NĐ-CP|Đ1|K1"],  # cái sau CHƯA HỀ tra
)
r = rang_citation(tl, vet)
eq(r.da_loai, ["99/2026/NĐ-CP|Đ1|K1"], "loại nguồn chưa hề tra")
eq("99/2026/NĐ-CP|Đ1|K1" in r.tra_loi.citations, False, "nguồn bịa KHÔNG lọt ra ngoài")

print("\n=== citation binding — THÊM nguồn LLM quên khai ===")
tl = TraLoi("DN được hỗ trợ 50%.", grounded=True, citations=["80/2021/NĐ-CP|Đ5|K3"])
r = rang_citation(tl, vet)
eq(r.da_them, ["80/2021/NĐ-CP|Đ6|K1"], "tự thêm nguồn đã tra mà LLM quên")
eq(len(r.tra_loi.citations), 2, "đủ 2 nguồn thật")

print("\n=== BẪY: grounded + citation TOÀN ĐỒ BỊA ===")
print("  (nếu enforce TRƯỚC khi ràng thì ca này LỌT — có citation, nhưng là citation ma)")
tl = TraLoi("DN đủ điều kiện.", grounded=True, citations=["99/2026/NĐ-CP|Đ1|K1"])
vet_rong = VetTraCuu()
try:
    kiem_tra_tra_loi(tl, vet_rong)
    eq(True, False, "phải ném ModelRetry")
except ModelRetry:
    eq(True, True, "ràng xong hết citation → ModelRetry ✓ (không lọt)")

print("\n" + "=" * 54)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
