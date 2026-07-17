"""Test matcher chạy ngược + diff monitoring.
Chạy: uv run --python 3.11 python matcher/test_match.py
"""

import sys

sys.path.insert(0, ".")
from matcher.match import diff_ket_qua, doi_chieu, quet_nguoc  # noqa: E402
from matcher.schema import (  # noqa: E402
    ChuongTrinh,
    Citation,
    DieuKien,
    Profile,
    ToanTu,
    TrangThai,
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


C = Citation("80/2021/NĐ-CP", "Chính phủ", 5, 3, "…hỗ trợ 50% chi phí tư vấn…", "d1")
C2 = Citation("13/2019/NĐ-CP", "Chính phủ", 6, 1, "…chi R&D tối thiểu 1%…", "d2")

CT_DNNVV = ChuongTrinh(
    id="dnnvv-tuvan",
    ten="Hỗ trợ chi phí tư vấn cho DNNVV",
    co_quan="Chính phủ",
    loai="ho_tro_chi_phi",
    gia_tri_mo_ta="Hỗ trợ 50% chi phí tư vấn",
    gia_tri_uoc=480_000_000,
    han_nop="30/9 hằng năm",
    dieu_kien=[
        DieuKien("nhan_su", ToanTu.LTE, 200, "Nhân sự không quá 200 người", C),
        DieuKien("von", ToanTu.LTE, 100_000_000_000, "Vốn điều lệ dưới 100 tỷ", C),
        DieuKien("fdi", ToanTu.EQ, False, "Không có vốn FDI", C),
    ],
)

CT_CNC = ChuongTrinh(
    id="cnc-thue",
    ten="Ưu đãi thuế cho doanh nghiệp công nghệ cao",
    co_quan="Chính phủ",
    loai="uu_dai_thue",
    gia_tri_mo_ta="Miễn 4 năm, giảm 50% trong 9 năm tiếp",
    gia_tri_uoc=3_400_000_000,
    han_nop=None,
    dieu_kien=[
        DieuKien("chi_rnd", ToanTu.GTE, 1.0, "Chi R&D ≥ 1% doanh thu", C2),
        DieuKien("nhan_su", ToanTu.GTE, 30, "Tối thiểu 30 nhân sự", C2),
    ],
)

KHO = [CT_DNNVV, CT_CNC]

print("=== HỒ SƠ ĐẦY ĐỦ — DN phần mềm 45 người, vốn 20 tỷ, R&D 2,5% ===")
p = Profile("Sản xuất phần mềm", 20_000_000_000, 45, 2.5, "Hà Nội", False)
kq = quet_nguoc(p, KHO)
for r in kq:
    print(f"  {r.chuong_trinh.ten[:44]:46} EV={r.gia_tri_ky_vong/1e6:8.1f}tr  "
          f"P={r.diem_phu_hop:.2f}  {'ĐỦ' if r.du_dieu_kien else 'CHƯA'}")
eq(kq[0].chuong_trinh.id, "cnc-thue", "xếp hạng: EV cao nhất lên đầu")
eq(all(r.du_dieu_kien for r in kq), True, "cả 2 chương trình đều đủ điều kiện")

print("\n=== KHỐI DEMO 2 — KHÔNG GẬT BỪA (anti-sycophancy) ===")
print("  DN nói chắc 'bọn em đủ điều kiện công nghệ cao' nhưng R&D chỉ 0,3%:")
p2 = Profile("Sản xuất phần mềm", 20_000_000_000, 45, 0.3, "Hà Nội", False)
r = doi_chieu(p2, CT_CNC)
eq(r.du_dieu_kien, False, "→ bot KHÔNG gật bừa")
eq(r.thieu, ["Chi R&D ≥ 1% doanh thu"], "→ gọi ĐÍCH DANH điều kiện thiếu")
print(f"      thiếu: {r.thieu}")
print(f"      căn cứ: {r.chi_tiet[0].dieu_kien.citation}")
print(f"      đối chiếu: {r.chi_tiet[0].giai_thich}")

print("\n=== THIẾU THÔNG TIN → HỎI, KHÔNG ĐOÁN ===")
p3 = Profile(nganh="Sản xuất phần mềm", nhan_su=45)
r = doi_chieu(p3, CT_CNC)
eq(r.can_hoi_them, ["chi_rnd"], "biết phải hỏi thêm field nào")
eq(r.chi_tiet[0].trang_thai, TrangThai.THIEU_TIN, "thiếu tin ≠ không đạt")
eq(r.du_dieu_kien, True, "chưa kết luận loại — vì chưa hỏi xong")
print(f"      cần hỏi: {r.can_hoi_them}  ·  P={r.diem_phu_hop} (chưa chắc)")

print("\n=== MONITORING (② của đề) — diff 2 snapshot, KHÔNG cần API ===")
print("  Giả lập: quy định siết ngưỡng FDI → DN có FDI mất điều kiện DNNVV")
p_fdi = Profile("Sản xuất phần mềm", 20_000_000_000, 45, 2.5, "Hà Nội", True)
truoc = quet_nguoc(p, KHO)      # DN không FDI
sau = quet_nguoc(p_fdi, KHO)    # DN có FDI
d = diff_ket_qua(truoc, sau)
eq(d["vua_mat"], ["dnnvv-tuvan"], "phát hiện chương trình VỪA MẤT điều kiện")
print(f"      vừa mất: {d['vua_mat']}  ·  giữ nguyên: {d['giu_nguyen']}")

print("\n" + "=" * 56)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
