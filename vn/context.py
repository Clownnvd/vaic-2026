"""H1 + H2 — ngôn ngữ & ngữ cảnh Việt Nam. Áp công thức kho sang domain CHÍNH SÁCH.

H1 (ngôn ngữ):
  • Giao diện hoàn toàn tiếng Việt
  • Hiểu VIẾT TẮT nghiệp vụ — nhưng của domain chính sách, không phải ngân hàng
    (kho có glossary ngân hàng: KH/RM/CBNV → ở đây là DNNVV/NĐ/TT/ĐMST/CNC…)
  • Hỗ trợ gõ KHÔNG DẤU — người dùng gõ "doanh nghiep nho va vua"

H2 (ngữ cảnh địa phương):
  • VND: dấu chấm ngăn nghìn, không có xu, "triệu"/"tỷ" khẩu ngữ
  • Ngày dd/MM/yyyy · timezone Asia/Ho_Chi_Minh UTC+7 KHÔNG DST
  • PII mask theo Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP

⚠️ PII Ở BÀI NÀY KHÁC BÀI NGÂN HÀNG:
  Hồ sơ ở đây là DOANH NGHIỆP → khoá định danh là MÃ SỐ THUẾ (10 hoặc 13 số),
  không phải số tài khoản. Nhưng NGƯỜI ĐẠI DIỆN vẫn là cá nhân → CCCD/SĐT/email
  của họ là dữ liệu cá nhân, phải mask trước khi rời hệ thống ra LLM ngoài.
"""

from __future__ import annotations

import re
import unicodedata

# ── H1: viết tắt domain CHÍNH SÁCH ────────────────────────────────
VIET_TAT: dict[str, str] = {
    "dnnvv": "doanh nghiệp nhỏ và vừa",
    "dn": "doanh nghiệp",
    "nđ": "nghị định",
    "nd": "nghị định",
    "tt": "thông tư",
    "qđ": "quyết định",
    "qd": "quyết định",
    "nq": "nghị quyết",
    "cnc": "công nghệ cao",
    "khcn": "khoa học và công nghệ",
    "kh&cn": "khoa học và công nghệ",
    "đmst": "đổi mới sáng tạo",
    "dmst": "đổi mới sáng tạo",
    "cđs": "chuyển đổi số",
    "cds": "chuyển đổi số",
    "fdi": "vốn đầu tư trực tiếp nước ngoài",
    "r&d": "nghiên cứu và phát triển",
    "rd": "nghiên cứu và phát triển",
    "sxkd": "sản xuất kinh doanh",
    "gcn": "giấy chứng nhận",
    "mst": "mã số thuế",
    "tndn": "thu nhập doanh nghiệp",
    "gtgt": "giá trị gia tăng",
    "ubnd": "ủy ban nhân dân",
    "hđnd": "hội đồng nhân dân",
    "hdnd": "hội đồng nhân dân",
    "nic": "Trung tâm Đổi mới sáng tạo Quốc gia",
}


def bo_dau(s: str) -> str:
    """'Đổi mới sáng tạo' → 'doi moi sang tao'. Dùng để so khớp, KHÔNG để hiển thị."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def chuan_nfc(s: str) -> str:
    """Ép NFC — tên/văn bản có dấu phải nhất quán, kẻo thành tofu hoặc so khớp trượt."""
    return unicodedata.normalize("NFC", s)


def no_viet_tat(text: str) -> str:
    """'DN toi la DNNVV, chi R&D 2%' → nở viết tắt để agent hiểu.

    So khớp KHÔNG DẤU + không phân biệt hoa thường → bắt được cả 'DNNVV', 'dnnvv',
    'Dnnvv'. Chỉ thay khi đứng riêng thành từ (\\b) — tránh nuốt nhầm giữa từ.
    """
    ra = text
    for tat, day in sorted(VIET_TAT.items(), key=lambda x: -len(x[0])):
        pat = re.compile(rf"\b{re.escape(tat)}\b", re.IGNORECASE)
        ra = pat.sub(day, ra)
    return ra


# ── H2: PII doanh nghiệp — mask theo Luật 91/2025 + NĐ 356/2025 ───
RE_PII: dict[str, re.Pattern] = {
    # MST: 10 số, hoặc 13 số dạng 0123456789-001 (đơn vị trực thuộc)
    "mst": re.compile(r"\b\d{10}(?:-\d{3})?\b"),
    "cccd": re.compile(r"\b\d{12}\b"),
    "cmnd": re.compile(r"\b\d{9}\b"),
    "phone": re.compile(r"(?:\+?84|0)(?:3|5|7|8|9)(?:\d[ .-]?){7}\d"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}


def mask_duoi(s: str, giu: int = 3) -> str:
    """'0912345678' → '****678'. Giữ đuôi để người còn đối chiếu được."""
    return "****" + s[-giu:] if len(s) > giu else "****"


def che_pii(text: str) -> tuple[str, dict[str, list[str]]]:
    """Che PII TRƯỚC KHI gửi ra LLM ngoài. Trả (text đã che, bảng đã che).

    Vì sao phải che: gửi dữ liệu cá nhân ra model nước ngoài chạm CẢ HAI —
    chuyển dữ liệu xuyên biên giới (Luật 91/2025) và nội địa hoá (Điều 26 An ninh mạng).

    ⚠️ THỨ TỰ QUAN TRỌNG: mask cccd (12 số) TRƯỚC mst (10 số) trước cmnd (9 số) —
    regex ngắn hơn sẽ ăn nhầm vào số dài hơn nếu chạy trước.
    """
    ra = text
    da_che: dict[str, list[str]] = {}
    for loai in ("email", "phone", "cccd", "mst", "cmnd"):
        found: list[str] = []

        def _thay(m: re.Match) -> str:
            found.append(m.group(0))
            return mask_duoi(re.sub(r"\D", "", m.group(0)) or m.group(0))

        if loai == "email":

            def _thay_email(m: re.Match) -> str:
                found.append(m.group(0))
                a, _, d = m.group(0).partition("@")
                return f"{a[0]}***@{d}"

            ra = RE_PII[loai].sub(_thay_email, ra)
        else:
            ra = RE_PII[loai].sub(_thay, ra)

        if found:
            da_che[loai] = found
    return ra, da_che


# ── H2: định dạng ─────────────────────────────────────────────────
def format_vnd(n: int, rut_gon: bool = True) -> str:
    """20000000000 → '20 tỷ đ' (rút gọn) hoặc '20.000.000.000 đ' (đầy đủ).

    Dấu CHẤM ngăn nghìn — kiểu VN, không phải phẩy. VND không có xu.
    """
    if rut_gon:
        if n >= 1_000_000_000:
            t = n / 1_000_000_000
            return f"{t:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " tỷ đ"
        if n >= 1_000_000:
            t = n / 1_000_000
            return f"{t:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " triệu đ"
    return f"{n:,}".replace(",", ".") + " đ"


def format_ngay(d: int, m: int, y: int | None = None) -> str:
    """dd/MM/yyyy — chuẩn VN."""
    return f"{d:02d}/{m:02d}/{y}" if y else f"{d:02d}/{m:02d}"


TIMEZONE = "Asia/Ho_Chi_Minh"  # UTC+7, KHÔNG có DST — đừng cộng trừ theo mùa
