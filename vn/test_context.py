"""Test H1 (ngôn ngữ) + H2 (ngữ cảnh VN).
Chạy: uv run --python 3.11 python vn/test_context.py
"""

import sys

sys.path.insert(0, ".")
from vn.context import (  # noqa: E402
    bo_dau,
    che_pii,
    chuan_nfc,
    format_ngay,
    format_vnd,
    no_viet_tat,
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


print("=== H1: HIỂU VIẾT TẮT (domain chính sách) ===")
r = no_viet_tat("DN tôi là DNNVV, chi R&D 2%, xin ưu đãi theo NĐ 80/2021")
print(f"      {r}")
eq("doanh nghiệp nhỏ và vừa" in r, True, "DNNVV → nở đủ")
eq("nghiên cứu và phát triển" in r, True, "R&D → nở")
eq("nghị định" in r, True, "NĐ → nở")

r2 = no_viet_tat("cty CNC xin GCN, hỏi về KHCN và ĐMST")
print(f"      {r2}")
eq("công nghệ cao" in r2, True, "CNC → nở")
eq("đổi mới sáng tạo" in r2, True, "ĐMST → nở")

print("\n=== H1: GÕ KHÔNG DẤU (đề bắt buộc hỗ trợ) ===")
eq(bo_dau("Đổi mới sáng tạo"), "Doi moi sang tao", "bỏ dấu để so khớp")
eq(bo_dau("doanh nghiệp nhỏ và vừa"), "doanh nghiep nho va vua", "bỏ dấu")
r3 = no_viet_tat("dn toi la dnnvv")
eq("doanh nghiệp nhỏ và vừa" in r3, True, "gõ KHÔNG DẤU vẫn nở được viết tắt")
print(f"      'dn toi la dnnvv' → {r3}")

print("\n=== H2: PII — che TRƯỚC khi ra LLM ngoài ===")
t = ("Công ty ABC, MST 0123456789, người đại diện Nguyễn Văn An "
     "CCCD 001099012345, SĐT 0912345678, email an.nguyen@abc.vn")
che, bang = che_pii(t)
print(f"      gốc : {t}")
print(f"      che : {che}")
eq("0123456789" not in che, True, "mã số thuế bị che")
eq("001099012345" not in che, True, "CCCD bị che")
eq("0912345678" not in che, True, "SĐT bị che")
eq("an.nguyen@abc.vn" not in che, True, "email bị che")
eq("Nguyễn Văn An" in che, True, "tên GIỮ (không phải PII cần che ở ngữ cảnh này)")
eq(sorted(bang.keys()), ["cccd", "email", "mst", "phone"], "ghi lại đủ loại đã che")

print("\n=== H2: VND — dấu CHẤM ngăn nghìn, không có xu ===")
eq(format_vnd(20_000_000_000), "20 tỷ đ", "20 tỷ")
eq(format_vnd(1_500_000_000), "1,5 tỷ đ", "1,5 tỷ — phẩy là thập phân")
eq(format_vnd(480_000_000), "480 triệu đ", "480 triệu")
eq(format_vnd(20_000_000_000, rut_gon=False), "20.000.000.000 đ", "đầy đủ: chấm ngăn nghìn")

print("\n=== H2: ngày dd/MM/yyyy ===")
eq(format_ngay(30, 9, 2026), "30/09/2026", "dd/MM/yyyy")
eq(format_ngay(5, 3), "05/03", "không năm")

print("\n=== GOTCHA: NFC — tên có dấu phải nhất quán ===")
import unicodedata  # noqa: E402

nfd = unicodedata.normalize("NFD", "Đổi mới")
eq(chuan_nfc(nfd) == "Đổi mới", True, "NFD → NFC (kẻo so khớp trượt / thành tofu)")
eq(nfd == "Đổi mới", False, "→ NFD KHÁC NFC dù nhìn giống hệt (đây là bẫy)")

print("\n" + "=" * 58)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
