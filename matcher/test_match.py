"""Test matcher: chạy ngược + diff monitoring + kho THẬT.

⚠️ BẢN CŨ CÓ BẪY: fixture gán VĂN BẢN BỊA vào SỐ HIỆU THẬT —
     Citation("13/2019/NĐ-CP", …, 6, 1, "…chi R&D tối thiểu 1%…")
   Số hiệu thật, Điều/Khoản thật, nội dung bịa. Ai đọc test cũng tưởng luật nói
   vậy, và chính nó đẻ ra điều kiện bịa "Chi R&D ≥ 1%" trong kho_mau.

   Nay tách đôi:
     • TEST LOGIC     → dùng văn bản HƯ CẤU RÕ RÀNG (HU-CAU/0000/TEST) —
                        không ai nhầm được, và logic thì không cần luật thật
     • TEST KHO THẬT  → dùng matcher.kho_mau, đối chiếu nguyên văn corpus

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
TY = 1_000_000_000


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


# ══════════════════════════════════════════════════════════════
#  PHẦN 1 — LOGIC. Văn bản HƯ CẤU, không dính số hiệu thật.
# ══════════════════════════════════════════════════════════════
CH = Citation("HU-CAU/0000/TEST", "(cơ quan hư cấu — chỉ để test logic)", 1, 1,
              "Điều kiện hư cấu dùng cho test, không phải luật.", "test")

CT_HC = ChuongTrinh(
    id="hu-cau-1",
    ten="[HƯ CẤU] Chương trình test logic",
    co_quan="(hư cấu)",
    loai="test",
    gia_tri_mo_ta="(hư cấu)",
    gia_tri_uoc=100_000_000,
    han_nop=None,
    dieu_kien=[
        DieuKien("lao_dong_bhxh", ToanTu.LTE, 200, "[HƯ CẤU] Lao động ≤ 200", CH),
        DieuKien("fdi", ToanTu.EQ, False, "[HƯ CẤU] Không có vốn FDI", CH),
    ],
)

print("=== LOGIC: không gật bừa (anti-sycophancy) ===")
p_fdi = Profile(lao_dong_bhxh=45, fdi=True)
r = doi_chieu(p_fdi, CT_HC)
eq(r.du_dieu_kien, False, "DN khẳng định đủ nhưng thực tế không → KHÔNG gật")
eq(r.thieu, ["[HƯ CẤU] Không có vốn FDI"], "gọi ĐÍCH DANH điều kiện thiếu")

print("\n=== LOGIC: thiếu tin → HỎI, không đoán ===")
p_thieu = Profile(lao_dong_bhxh=45)  # chưa khai fdi
r = doi_chieu(p_thieu, CT_HC)
eq(r.can_hoi_them, ["fdi"], "biết phải hỏi field nào")
eq(r.chi_tiet[1].trang_thai, TrangThai.THIEU_TIN, "thiếu tin ≠ không đạt")
eq(r.du_dieu_kien, True, "chưa kết luận loại — vì chưa hỏi xong")

print("\n=== LOGIC: monitoring ② — diff 2 snapshot, không cần API ===")
truoc = quet_nguoc(Profile(lao_dong_bhxh=45, fdi=False), [CT_HC])
sau = quet_nguoc(Profile(lao_dong_bhxh=45, fdi=True), [CT_HC])
d = diff_ket_qua(truoc, sau)
eq(d["vua_mat"], ["hu-cau-1"], "phát hiện chương trình VỪA MẤT điều kiện")

# ══════════════════════════════════════════════════════════════
#  PHẦN 2 — KHO THẬT. Đối chiếu nguyên văn corpus.
# ══════════════════════════════════════════════════════════════
from matcher.kho_mau import KHO  # noqa: E402


def ct_id(cid: str) -> ChuongTrinh:
    """Lấy chương trình theo ID — KHÔNG theo chỉ số. Kho nở thêm chương trình thì
    thứ tự đổi; test bám chỉ số KHO[1] sẽ đối chiếu nhầm chương trình."""
    return next(c for c in KHO if c.id == cid)


print("\n=== KHO THẬT: mọi citation phải có nguyên văn, không placeholder ===")
for ct in KHO:
    cits = [dk.citation for dk in ct.dieu_kien] + (
        [ct.citation_chinh] if ct.citation_chinh else []
    )
    for c in cits:
        eq("PLACEHOLDER" in c.trich, False, f"{ct.id}: {c} có nguyên văn")
        eq(len(c.trich) > 80, True, f"{ct.id}: {c} trích đủ dài ({len(c.trich)} ký tự)")
        eq(c.doc_id is not None, True, f"{ct.id}: {c} trỏ về doc_id corpus")

print("\n=== KHO THẬT: DN vừa ngành CN-XD, 150 LĐ, doanh thu 50 tỷ ===")
p = Profile(
    nganh="Sản xuất phần mềm",
    linh_vuc="nong_lam_thuy_san__cong_nghiep_xay_dung",
    lao_dong_bhxh=150,
    doanh_thu=50 * TY,
    von=20 * TY,
    co_gcn_khcn=True,
    ty_le_dt_khcn=45.0,
    fdi=False,
)
kq = quet_nguoc(p, KHO)
for r in kq:
    ev = f"{r.gia_tri_ky_vong/1e6:8.1f}tr" if r.gia_tri_ky_vong else "  chưa lượng hoá"
    print(f"  {r.chuong_trinh.ten[:46]:48} EV={ev}  P={r.diem_phu_hop:.2f}  "
          f"{'ĐỦ' if r.du_dieu_kien else 'CHƯA'}")
eq(all(r.du_dieu_kien for r in kq), True, f"cả {len(kq)} chương trình đủ điều kiện")
eq(all(r.xac_quyet == "du" for r in kq), True, "hồ sơ đủ field → xác quyết 'du', không 'gần đạt'")

print("\n=== KHO THẬT: cùng hồ sơ nhưng THƯƠNG MẠI-DỊCH VỤ → mất DNNVV ===")
print("  (150 LĐ vượt ngưỡng 100 của TM-DV — bản cũ phẳng hoá '≤200' nên bỏ lọt)")
p_tm = Profile(**{**p.__dict__, "linh_vuc": "thuong_mai_dich_vu"})
r_tm = doi_chieu(p_tm, ct_id("dnnvv-tuvan"))
eq(r_tm.du_dieu_kien, False, "→ KHÔNG đủ điều kiện DNNVV")
eq(r_tm.thieu, ["Thuộc diện doanh nghiệp nhỏ và vừa theo Điều 5"], "→ nêu đích danh")

print("\n=== KHO THẬT: DN KH&CN doanh thu KH&CN chỉ 20% (<30%) ===")
p_20 = Profile(**{**p.__dict__, "ty_le_dt_khcn": 20.0})
r_20 = doi_chieu(p_20, ct_id("khcn-thue"))
eq(r_20.du_dieu_kien, False, "→ KHÔNG được ưu đãi thuế (Điều 12 K3)")
eq(
    r_20.thieu,
    ["Doanh thu sản phẩm hình thành từ kết quả KH&CN đạt tối thiểu 30% tổng doanh thu"],
    "→ nêu đích danh, đúng ngưỡng 30% của luật (không phải 'R&D 1%' bịa)",
)
# 30% CHỈ áp cho ưu đãi THUẾ (13/2019 Đ12 K3). Đất đai (Đ13) và tín dụng (Đ14)
# chỉ đòi 'là DN KH&CN' (có GCN) → ty_le 20% vẫn đủ. Không được áp nhầm 30% sang.
eq(doi_chieu(p_20, ct_id("khcn-datdai")).du_dieu_kien, True,
   "→ tiền thuê đất KHÔNG đòi 30% doanh thu KH&CN — vẫn đủ với GCN")
eq(doi_chieu(p_20, ct_id("khcn-tindung")).du_dieu_kien, True,
   "→ tín dụng KHÔNG đòi 30% doanh thu KH&CN — vẫn đủ với GCN")

print("\n" + "=" * 58)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
