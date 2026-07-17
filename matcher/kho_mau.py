"""⚠️ KHO MẪU — 2 chương trình để chạy đường dây. KHÔNG PHẢI 10 FLAGSHIP THẬT.

Phải thay bằng 10 chương trình curate từ corpus vbpl-vn trước khi demo:
điều kiện thụ hưởng moi tay từ luật, citation trỏ về điều–khoản thật.

Số hiệu văn bản dưới đây là VĂN BẢN CÓ THẬT, nhưng `trich` là placeholder —
chưa đối chiếu corpus. Để nguyên mà demo = bịa điều luật = đúng thứ sản phẩm chống.

(Tách khỏi test_match.py: import file test sẽ CHẠY test + gọi sys.exit() → chết server.)
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from matcher.schema import ChuongTrinh, Citation, DieuKien, ToanTu  # noqa: E402

C_DNNVV = Citation(
    so_vb="80/2021/NĐ-CP",
    co_quan="Chính phủ",
    dieu=5,
    khoan=3,
    trich="[PLACEHOLDER — chờ trích nguyên văn từ corpus]",
    doc_id=None,
)
C_CNC = Citation(
    so_vb="13/2019/NĐ-CP",
    co_quan="Chính phủ",
    dieu=6,
    khoan=1,
    trich="[PLACEHOLDER — chờ trích nguyên văn từ corpus]",
    doc_id=None,
)

CT_DNNVV = ChuongTrinh(
    id="dnnvv-tuvan",
    ten="Hỗ trợ chi phí tư vấn cho doanh nghiệp nhỏ và vừa",
    co_quan="Chính phủ",
    loai="ho_tro_chi_phi",
    gia_tri_mo_ta="Hỗ trợ một phần chi phí tư vấn theo quy mô doanh nghiệp",
    gia_tri_uoc=480_000_000,
    han_nop="30/9 hằng năm",
    giay_to=["Giấy chứng nhận đăng ký doanh nghiệp", "Báo cáo tài chính năm gần nhất"],
    citation_chinh=C_DNNVV,
    dieu_kien=[
        DieuKien("nhan_su", ToanTu.LTE, 200, "Nhân sự không quá 200 người", C_DNNVV),
        DieuKien("von", ToanTu.LTE, 100_000_000_000, "Vốn điều lệ dưới 100 tỷ", C_DNNVV),
        DieuKien("fdi", ToanTu.EQ, False, "Không có vốn FDI", C_DNNVV),
    ],
)

CT_CNC = ChuongTrinh(
    id="cnc-thue",
    ten="Ưu đãi thuế cho doanh nghiệp khoa học và công nghệ",
    co_quan="Chính phủ",
    loai="uu_dai_thue",
    gia_tri_mo_ta="Miễn 4 năm, giảm 50% trong 9 năm tiếp theo (theo điều kiện chứng nhận)",
    gia_tri_uoc=3_400_000_000,
    han_nop=None,
    giay_to=["Giấy chứng nhận doanh nghiệp KH&CN", "Thuyết minh kết quả KH&CN"],
    citation_chinh=C_CNC,
    dieu_kien=[
        DieuKien("chi_rnd", ToanTu.GTE, 1.0, "Chi R&D ≥ 1% doanh thu", C_CNC),
        DieuKien("nhan_su", ToanTu.GTE, 30, "Tối thiểu 30 nhân sự", C_CNC),
    ],
)

KHO: list[ChuongTrinh] = [CT_DNNVV, CT_CNC]
