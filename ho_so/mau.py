"""③ HỖ TRỢ SOẠN HỒ SƠ — biểu mẫu thật, đã verify hiệu lực 2026.

Nguồn: VAIC-MAU-HO-SO-2026 (scan 33 mẫu, verify 17/07/2026).

⚠️ KỶ LUẬT: chỉ đưa vào đây mẫu mà văn bản căn cứ CÓ TRONG CORPUS.
Đã kiểm bằng scripts/check_vb_moi2.py — khớp chính xác số hiệu, không khớp chuỗi con.
Mẫu nào căn cứ nằm ngoài corpus thì BỎ, vì citation sẽ trỏ vào chỗ không tra được
→ đúng thứ sản phẩm này chống.

ĐÃ LOẠI (căn cứ không có trong corpus):
  • Ưu đãi đầu tư A.I.1–A.I.4  → cần Luật Đầu tư 143/2025/QH15 (không có)
  • DN CNC B1/B2-DNTLM         → cần TT 38/2026/TT-BKHCN (không có)
  • 8 mẫu Đề án 844            → ĐÃ CHẾT (hết giai đoạn 31/12/2025)
  • B1-DNCNC (GCN DN CNC)      → ĐÃ CHẾT (Luật CNC 133/2025 bỏ hẳn GCN từ 1/7/2026)

Mấy mẫu CHẾT ở trên không vứt đi — chúng là **ca demo "bắt lỗi hết hiệu lực"**
cho chức năng ② monitoring. Xem ho_so/het_hieu_luc.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Truong:
    """Một ô trong biểu mẫu. `nguon` quyết định AI có được gõ vào đây không."""

    khoa: str
    nhan: str
    nguon: str  # "ho_so" = điền từ profile DN | "corpus" = chép từ văn bản | "nguoi" = DN tự điền
    bat_buoc: bool = True
    goi_y: str = ""


@dataclass(frozen=True)
class MauHoSo:
    ma: str
    ten: str
    nhom: str
    can_cu: str  # số hiệu văn bản — PHẢI có trong corpus
    co_quan_nhan: str
    dn_tu_nop: bool
    truong: list[Truong] = field(default_factory=list)
    han_nop: str | None = None
    ghi_chu: str = ""


# ── A. NAFOSTED — căn cứ TT 44/2025/TT-BKHCN ✓ có trong corpus ────
# Bằng chứng còn hiệu lực: thông báo tài trợ NAFOSTED 2026, nhận hồ sơ 14/7–14/8/2026
NAFOSTED = [
    MauHoSo(
        ma="BM-03",
        ten="Đơn đăng ký chủ trì nhiệm vụ khoa học và công nghệ",
        nhom="NAFOSTED",
        can_cu="44/2025/TT-BKHCN",
        co_quan_nhan="Quỹ Phát triển khoa học và công nghệ Quốc gia (NAFOSTED)",
        dn_tu_nop=True,
        han_nop="14/08/2026",
        truong=[
            Truong("ten_to_chuc", "Tên tổ chức chủ trì", "ho_so"),
            Truong("mst", "Mã số thuế", "ho_so"),
            Truong("dia_chi", "Địa chỉ trụ sở", "ho_so"),
            Truong("nganh", "Lĩnh vực hoạt động", "ho_so"),
            Truong("ten_nhiem_vu", "Tên nhiệm vụ đăng ký", "nguoi", goi_y="do DN tự đặt"),
            Truong("chu_nhiem", "Họ tên chủ nhiệm nhiệm vụ", "nguoi"),
            Truong("thoi_gian", "Thời gian thực hiện (tháng)", "nguoi"),
            Truong("kinh_phi", "Tổng kinh phí đề nghị (đồng)", "nguoi"),
        ],
    ),
    MauHoSo(
        ma="BM-04",
        ten="Thuyết minh nhiệm vụ khoa học và công nghệ",
        nhom="NAFOSTED",
        can_cu="44/2025/TT-BKHCN",
        co_quan_nhan="NAFOSTED",
        dn_tu_nop=True,
        han_nop="14/08/2026",
        truong=[
            Truong("ten_to_chuc", "Tên tổ chức chủ trì", "ho_so"),
            Truong("ten_nhiem_vu", "Tên nhiệm vụ", "nguoi"),
            Truong("muc_tieu", "Mục tiêu nhiệm vụ", "nguoi"),
            Truong("noi_dung", "Nội dung nghiên cứu chính", "nguoi"),
            Truong("san_pham", "Sản phẩm dự kiến", "nguoi"),
        ],
    ),
    MauHoSo(
        ma="BM-07",
        ten="Năng lực và cơ sở vật chất của tổ chức chủ trì",
        nhom="NAFOSTED",
        can_cu="44/2025/TT-BKHCN",
        co_quan_nhan="NAFOSTED",
        dn_tu_nop=True,
        han_nop="14/08/2026",
        truong=[
            Truong("ten_to_chuc", "Tên tổ chức", "ho_so"),
            Truong("nhan_su", "Tổng số nhân sự", "ho_so"),
            Truong("chi_rnd", "Tỷ lệ chi cho R&D (% doanh thu)", "ho_so"),
            Truong("csvc", "Cơ sở vật chất phục vụ nghiên cứu", "nguoi"),
        ],
    ),
    MauHoSo(
        ma="BM-09",
        ten="Dự toán kinh phí chi tiết",
        nhom="NAFOSTED",
        can_cu="44/2025/TT-BKHCN",
        co_quan_nhan="NAFOSTED",
        dn_tu_nop=True,
        han_nop="14/08/2026",
        ghi_chu="Định mức chi theo TT 38/2025/TT-BKHCN (có trong corpus)",
        truong=[
            Truong("ten_to_chuc", "Tên tổ chức chủ trì", "ho_so"),
            Truong("ten_nhiem_vu", "Tên nhiệm vụ", "nguoi"),
            Truong("tong_kinh_phi", "Tổng dự toán (đồng)", "nguoi"),
        ],
    ),
]

# ── B. Hỗ trợ DNNVV — căn cứ NĐ 80/2021 + TT 06/2022 ✓ có trong corpus ──
DNNVV = [
    MauHoSo(
        ma="TK-DNNVV",
        ten="Tờ khai xác định doanh nghiệp nhỏ và vừa + đề xuất nhu cầu hỗ trợ",
        nhom="DNNVV",
        can_cu="80/2021/NĐ-CP",
        co_quan_nhan="Sở Tài chính / Cục Phát triển DN tư nhân và Kinh tế tập thể (Bộ Tài chính)",
        dn_tu_nop=True,
        ghi_chu="Cơ quan tiếp nhận đã đổi sang Bộ Tài chính sau khi sáp nhập Bộ KH&ĐT",
        truong=[
            Truong("ten_to_chuc", "Tên doanh nghiệp", "ho_so"),
            Truong("mst", "Mã số thuế", "ho_so"),
            Truong("dia_chi", "Địa chỉ", "ho_so"),
            Truong("nganh", "Ngành nghề kinh doanh chính", "ho_so"),
            Truong("nhan_su", "Số lao động bình quân năm", "ho_so"),
            Truong("von", "Tổng nguồn vốn (đồng)", "ho_so"),
            Truong("nhu_cau", "Nội dung hỗ trợ đề xuất", "nguoi"),
        ],
    ),
    MauHoSo(
        ma="PL3.3-M1",
        ten="Phiếu đăng ký tham gia khóa đào tạo",
        nhom="DNNVV",
        can_cu="06/2022/TT-BKHĐT",
        co_quan_nhan="Đơn vị tổ chức đào tạo",
        dn_tu_nop=True,
        truong=[
            Truong("ten_to_chuc", "Tên doanh nghiệp", "ho_so"),
            Truong("mst", "Mã số thuế", "ho_so"),
            Truong("hoc_vien", "Họ tên học viên", "nguoi"),
            Truong("khoa_hoc", "Tên khóa đào tạo", "nguoi"),
        ],
    ),
]

# ── C. Ưu đãi thuế TNDN — căn cứ TT 80/2021/TT-BTC ✓ có trong corpus ──
THUE = [
    MauHoSo(
        ma="03-3A/TNDN",
        ten="Phụ lục ưu đãi thuế TNDN (doanh nghiệp công nghệ cao / dự án ưu đãi)",
        nhom="Thuế TNDN",
        can_cu="80/2021/TT-BTC",
        co_quan_nhan="Cơ quan thuế quản lý trực tiếp",
        dn_tu_nop=True,
        ghi_chu=(
            "Cơ chế TỰ KHAI — không nộp hồ sơ xin ưu đãi trước. "
            "Biểu mẫu theo TT 80/2021/TT-BTC (không đổi), nhưng ĐIỀU KIỆN ưu đãi "
            "tính theo Luật TNDN 67/2025/QH15 — văn bản này ĐÃ có trong corpus "
            "(sau khi thêm doc_type='luat'), nên trích được điều khoản thật."
        ),
        truong=[
            Truong("ten_to_chuc", "Tên người nộp thuế", "ho_so"),
            Truong("mst", "Mã số thuế", "ho_so"),
            Truong("ky_tinh_thue", "Kỳ tính thuế", "nguoi"),
            Truong("dieu_kien_uu_dai", "Điều kiện ưu đãi áp dụng", "nguoi"),
        ],
    ),
]

TAT_CA: list[MauHoSo] = [*NAFOSTED, *DNNVV, *THUE]

# tra nhanh: chương trình nào → mẫu nào
THEO_CHUONG_TRINH: dict[str, list[str]] = {
    "cnc-thue": ["03-3A/TNDN"],
    "dnnvv-tuvan": ["TK-DNNVV", "PL3.3-M1"],
    "nafosted": ["BM-03", "BM-04", "BM-07", "BM-09"],
}
