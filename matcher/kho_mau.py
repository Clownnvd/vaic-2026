"""Kho chương trình — MỌI TRÍCH DẪN CHÉP NGUYÊN VĂN TỪ CORPUS.

⚠️ BẢN CŨ BỊA. Ghi lại đây để không ai lặp lại:
  ┌────────────────────────────────┬────────────────────────────────────────────┐
  │ bản cũ ghi                     │ luật THẬT nói (đã moi từ corpus)           │
  ├────────────────────────────────┼────────────────────────────────────────────┤
  │ "Tối thiểu 30 nhân sự"         │ 13/2019 Đ6 K1 KHÔNG có điều kiện nhân sự.  │
  │                                │ Chỉ 2 điều kiện: a) thành lập theo Luật DN │
  │                                │ b) có kết quả KH&CN được công nhận         │
  │ "Chi R&D ≥ 1% doanh thu"       │ 13/2019 Đ12 K3: doanh thu sản phẩm KH&CN   │
  │                                │ ≥ 30% TỔNG doanh thu. Khác hẳn.            │
  │ gia_tri_uoc = 480 triệu        │ 80/2021 Đ13 K2: trần CAO NHẤT là 200 triệu │
  │ "Nhân sự ≤ 200"                │ Đ5 K3: 200 với nông-CN-XD, 100 với TM-DV   │
  │ "Vốn ≤ 100 tỷ" (điều kiện rời) │ Đ5: doanh thu HOẶC vốn — là HOẶC           │
  │ trich = "[PLACEHOLDER]"        │ nay chép nguyên văn                        │
  └────────────────────────────────┴────────────────────────────────────────────┘
  Ba dòng đầu là BỊA TRẮNG — không tồn tại trong văn bản. Demo bản cũ =
  sản phẩm chống-bịa-luật đang bịa luật.

Nguồn: corpus vbpl-vn, item_id 158783 (80/2021/NĐ-CP) và 134061 (13/2019/NĐ-CP).
Moi bằng scripts/moi_nguyen_van.py — chạy lại được, không phải gõ tay.

⚠️ `trich` giữ NGUYÊN dạng trong corpus, kể cả lỗi chính tả nguồn ("khỏan",
   "họat động"). Sửa cho đẹp = không còn là nguyên văn → guard numdiff/lookup
   đối chiếu sẽ lệch.

(Tách khỏi test_match.py: import file test sẽ CHẠY test + gọi sys.exit() → chết server.)
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from matcher.schema import ChuongTrinh, Citation, DieuKien, ToanTu  # noqa: E402

# ══════════════════════════════════════════════════════════════════
#  80/2021/NĐ-CP — Hỗ trợ doanh nghiệp nhỏ và vừa
# ══════════════════════════════════════════════════════════════════

# Điều 5 định nghĩa QUY MÔ; logic bậc thang nằm ở matcher/quy_mo.py vì
# ngưỡng đổi theo lĩnh vực và có phép HOẶC — DieuKien phẳng không diễn tả nổi.
C_80_D5_K3 = Citation(
    so_vb="80/2021/NĐ-CP",
    co_quan="Chính phủ",
    dieu=5,
    khoan=3,
    trich=(
        "Doanh nghiệp vừa trong lĩnh vực nông nghiệp, lâm nghiệp, thủy sản; lĩnh vực "
        "công nghiệp và xây dựng sử dụng lao động có tham gia bảo hiểm xã hội bình quân "
        "năm không quá 200 người và tổng doanh thu của năm không quá 200 tỷ đồng hoặc "
        "tổng nguồn vốn của năm không quá 100 tỷ đồng, nhưng không phải là doanh nghiệp "
        "siêu nhỏ, doanh nghiệp nhỏ theo quy định tại khỏan 1, khỏan 2 Điều này."
    ),
    doc_id="158783",
)

C_80_D13_K2 = Citation(
    so_vb="80/2021/NĐ-CP",
    co_quan="Chính phủ",
    dieu=13,
    khoan=2,
    trich=(
        "Doanh nghiệp nhỏ và vừa tiếp cận mạng lưới tư vấn viên để được hỗ trợ sử dụng "
        "dịch vụ tư vấn về nhân sự, tài chính, sản xuất, bán hàng, thị trường, quản trị "
        "nội bộ và các nội dung khác liên quan tới họat động sản xuất - kinh doanh của "
        "doanh nghiệp (không bao gồm tư vấn về thủ tục hành chính, pháp lý theo quy định "
        "của pháp luật chuyên ngành) như sau: a) Hỗ trợ 100% giá trị hợp đồng tư vấn "
        "nhưng không quá 50 triệu đồng/năm/doanh nghiệp đối với doanh nghiệp siêu nhỏ [...]; "
        "b) Hỗ trợ tối đa 50% giá trị hợp đồng tư vấn nhưng không quá 100 triệu "
        "đồng/năm/doanh nghiệp đối với doanh nghiệp nhỏ [...]; c) Hỗ trợ tối đa 30% giá trị "
        "hợp đồng tư vấn nhưng không quá 150 triệu đồng/năm/doanh nghiệp đối với doanh "
        "nghiệp vừa hoặc không quá 200 triệu đồng/năm/doanh nghiệp đối với doanh nghiệp "
        "vừa do phụ nữ làm chủ, doanh nghiệp vừa sử dụng nhiều lao động nữ và doanh "
        "nghiệp vừa là doanh nghiệp xã hội."
    ),
    doc_id="158783",
)

CT_DNNVV_TU_VAN = ChuongTrinh(
    id="dnnvv-tuvan",
    ten="Hỗ trợ tư vấn cho doanh nghiệp nhỏ và vừa",
    co_quan="Chính phủ",
    loai="ho_tro_chi_phi",
    # mô tả CHÉP theo mức thật, không làm tròn cho kêu
    gia_tri_mo_ta=(
        "Hỗ trợ chi phí hợp đồng tư vấn theo quy mô: siêu nhỏ 100% (≤50 triệu/năm), "
        "nhỏ ≤50% (≤100 triệu/năm), vừa ≤30% (≤150 triệu/năm). "
        "Nâng trần cho DN do phụ nữ làm chủ / nhiều lao động nữ / DN xã hội."
    ),
    # 200 triệu = trần CAO NHẤT của Điều 13 K2 (DN vừa, nữ làm chủ).
    # Bản cũ ghi 480 triệu — bịa. Mức thật cho từng hồ sơ do quy_mo.muc_ho_tro_tu_van tính.
    gia_tri_uoc=200_000_000,
    han_nop=None,  # Điều 13 KHÔNG nêu hạn nộp. Bản cũ ghi "30/9 hằng năm" — không có trong văn bản.
    giay_to=["Giấy chứng nhận đăng ký doanh nghiệp", "Hợp đồng tư vấn", "Tờ khai xác định DNNVV"],
    citation_chinh=C_80_D13_K2,
    dieu_kien=[
        # quy_mo_dnnvv là field DẪN XUẤT — match.doi_chieu tính bằng
        # quy_mo.xac_dinh_quy_mo() theo đúng bậc thang Điều 5.
        DieuKien(
            "quy_mo_dnnvv",
            ToanTu.IN,
            ("sieu_nho", "nho", "vua"),
            "Thuộc diện doanh nghiệp nhỏ và vừa theo Điều 5",
            C_80_D5_K3,
        ),
    ],
)

# ══════════════════════════════════════════════════════════════════
#  13/2019/NĐ-CP — Doanh nghiệp khoa học và công nghệ
# ══════════════════════════════════════════════════════════════════

C_13_D6_K1 = Citation(
    so_vb="13/2019/NĐ-CP",
    co_quan="Chính phủ",
    dieu=6,
    khoan=1,
    trich=(
        "Doanh nghiệp được cấp Giấy chứng nhận doanh nghiệp khoa học và công nghệ khi "
        "đáp ứng các điều kiện sau: a) Được thành lập và họat động theo Luật doanh nghiệp; "
        "b) Có khả năng tạo ra hoặc ứng dụng kết quả khoa học và công nghệ được cơ quan "
        "có thẩm quyền đánh giá, thẩm định, công nhận theo quy định tại khỏan 2"
    ),
    doc_id="134061",
)

C_13_D12_K1 = Citation(
    so_vb="13/2019/NĐ-CP",
    co_quan="Chính phủ",
    dieu=12,
    khoan=1,
    trich=(
        "Thu nhập của doanh nghiệp khoa học và công nghệ từ họat động sản xuất, kinh doanh "
        "các sản phẩm hình thành từ kết quả khoa học và công nghệ được hưởng ưu đãi miễn, "
        "giảm thuế thu nhập doanh nghiệp như doanh nghiệp thực hiện dự án đầu tư mới thuộc "
        "lĩnh vực nghiên cứu khoa học và phát triển công nghệ, cụ thể: được miễn thuế 04 năm "
        "và giảm 50% số thuế phải nộp trong 09 năm tiếp theo."
    ),
    doc_id="134061",
)

C_13_D12_K3 = Citation(
    so_vb="13/2019/NĐ-CP",
    co_quan="Chính phủ",
    dieu=12,
    khoan=3,
    trich=(
        "Doanh nghiệp khoa học và công nghệ không được ưu đãi miễn, giảm thuế thu nhập "
        "doanh nghiệp đối với năm tài chính không đáp ứng được điều kiện về doanh thu của "
        "sản phẩm hình thành từ kết quả khoa học và công nghệ đạt tỷ lệ tối thiểu 30% trên "
        "tổng doanh thu của doanh nghiệp."
    ),
    doc_id="134061",
)

CT_KHCN_THUE = ChuongTrinh(
    id="khcn-thue",
    ten="Miễn, giảm thuế thu nhập doanh nghiệp cho doanh nghiệp khoa học và công nghệ",
    co_quan="Chính phủ",
    loai="uu_dai_thue",
    gia_tri_mo_ta="Miễn thuế 04 năm và giảm 50% số thuế phải nộp trong 09 năm tiếp theo",
    # None = CHƯA LƯỢNG HOÁ ĐƯỢC. Giá trị thật phụ thuộc thuế TNDN phải nộp của
    # từng DN — không biết thì KHÔNG ĐƯỢC bịa một con số cho đẹp bảng xếp hạng.
    # (Bản cũ ghi 3,4 tỷ — không có căn cứ nào trong văn bản.)
    gia_tri_uoc=None,
    han_nop=None,
    giay_to=[
        "Giấy chứng nhận doanh nghiệp khoa học và công nghệ",
        "Hồ sơ xác định doanh thu sản phẩm hình thành từ kết quả KH&CN",
    ],
    citation_chinh=C_13_D12_K1,
    dieu_kien=[
        DieuKien(
            "co_gcn_khcn",
            ToanTu.EQ,
            True,
            "Có Giấy chứng nhận doanh nghiệp khoa học và công nghệ",
            C_13_D6_K1,
        ),
        DieuKien(
            "ty_le_dt_khcn",
            ToanTu.GTE,
            30.0,
            "Doanh thu sản phẩm hình thành từ kết quả KH&CN đạt tối thiểu 30% tổng doanh thu",
            C_13_D12_K3,
        ),
    ],
)

KHO: list[ChuongTrinh] = [CT_DNNVV_TU_VAN, CT_KHCN_THUE]
