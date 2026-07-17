"""Kho này phủ tới đâu — và nói thẳng khi bị hỏi ngoài phạm vi.

VÌ SAO CẦN: bộ ca đối kháng bắt được 2 ca gãy:
    hỏi "ưu đãi NÔNG NGHIỆP"     → trả về ưu đãi công nghệ cao (đồ khác!)
    hỏi "Luật 67/2025 mức bao nhiêu" → trả kết quả bừa
Nguyên nhân: BFF bỏ qua hoàn toàn câu hỏi, hỏi gì cũng ra một đáp án.

Hệ thống PHẢI BIẾT MÌNH KHÔNG BIẾT GÌ. "Sâu 10 chương trình, kiến trúc nhân
ra được" chỉ trung thực khi nói được ranh giới của 10 chương trình đó ở đâu.
Im lặng trả đồ khác = một dạng bịa.
"""

from __future__ import annotations

import re
import sys

sys.path.insert(0, ".")
from vn.context import bo_dau  # noqa: E402

# Lĩnh vực kho ĐANG phủ — cập nhật khi thêm chương trình
DANG_PHU = {
    "công nghệ cao / khoa học công nghệ",
    "doanh nghiệp nhỏ và vừa",
    "ưu đãi thuế thu nhập doanh nghiệp",
    "tài trợ nghiên cứu (NAFOSTED)",
}

# Lĩnh vực người dùng hay hỏi mà kho CHƯA phủ → phải nói thẳng
CHUA_PHU: dict[str, str] = {
    "nong nghiep": "nông nghiệp",
    "thuy san": "thuỷ sản",
    "lam nghiep": "lâm nghiệp",
    "chan nuoi": "chăn nuôi",
    "y te": "y tế",
    # ⚠️ KHÔNG để "duoc" trần: bỏ dấu thì "được" (hư từ cực phổ biến) = "dược".
    #    Câu "bạn giúp được gì" → "duoc" → bị hiểu nhầm là lĩnh vực dược.
    #    Bắt "dược" phải kèm ngữ cảnh ngành → hết va chạm.
    "duoc pham": "dược",
    "nganh duoc": "dược",
    "cong ty duoc": "dược",
    "san xuat duoc": "dược",
    "linh vuc duoc": "dược",
    "giao duc": "giáo dục",
    "dao tao nghe": "đào tạo nghề",
    "bat dong san": "bất động sản",
    "xay dung": "xây dựng",
    "du lich": "du lịch",
    "van tai": "vận tải",
    "logistics": "logistics",
    "dien anh": "điện ảnh",
    "the thao": "thể thao",
    "moi truong": "môi trường",
    "nang luong tai tao": "năng lượng tái tạo",
}

# Văn bản người dùng hay nhắc mà KHÔNG có trong corpus.
# Đã kiểm bằng check_vb_moi2.py — khớp CHÍNH XÁC số hiệu, không khớp chuỗi con.
#
# ⚠️ CẬP NHẬT sau khi thêm doc_type='luat' vào bộ lọc corpus (9.299 → 9.436, +137 Luật):
#   • Luật TNDN 67/2025/QH15      → ĐÃ VÀO corpus, BỎ khỏi danh sách này
#   • Luật KH,CN&ĐMST 93/2025/QH15 → ĐÃ VÀO corpus, BỎ
#   • Luật CNC 133/2025 và Luật Đầu tư 143/2025 vẫn KHÔNG có — không phải do bộ lọc
#     (Luật CNC chắc chắn chạm keyword "công nghệ cao"), mà do DUMP không có chúng
#     (dump parse 21/05/2026). Giữ lại đây.
NGOAI_CORPUS: dict[str, str] = {
    "133/2025/QH15": "Luật Công nghệ cao 133/2025/QH15",
    "143/2025/QH15": "Luật Đầu tư 143/2025/QH15",
    "239/2025": "Nghị định 239/2025/NĐ-CP",
    "38/2026": "Thông tư 38/2026/TT-BKHCN",
    "20/2026": "Thông tư 20/2026/TT-BTC",
    "190/2025/QH15": "Nghị quyết 190/2025/QH15",
    "202/2025/QH15": "Nghị quyết 202/2025/QH15",
}

def _so_goc(khoa: str) -> str:
    """'67/2025/QH15' → '67/2025' — người dùng thường chỉ nói phần số."""
    m = re.match(r"(\d{1,3}/20\d{2})", khoa)
    return m.group(1) if m else khoa


def ngoai_pham_vi(cau: str) -> str | None:
    """Câu hỏi có chạm lĩnh vực kho CHƯA phủ không → trả tên lĩnh vực."""
    c = bo_dau(cau).lower()
    for khoa, ten in CHUA_PHU.items():
        if re.search(rf"\b{re.escape(khoa)}\b", c):
            return ten
    return None


# ── câu META/LẠC ĐỀ (bot phải HIỂU CONTEXT, không chạy matcher) ──────
# Bug thật: hồ sơ đã đầy từ lượt trước → câu "bạn năm nay bao tuổi" cũng
# re-run matcher → trả kết quả đủ điều kiện cho một câu KHÔNG hỏi chính sách.
# Bot phải nhận ra đây là câu meta/tán gẫu và chuyển hướng, không đoán.
_META = [
    r"\bbao (nhieu )?tuoi\b", r"\bmay tuoi\b", r"\bnam nay bao\b",
    r"\bban la ai\b", r"\bten (la )?gi\b", r"\bten ban\b",
    r"\bban co phai (la )?(nguoi|ai|robot|con nguoi|may)\b",
    r"\bai (tao|lam|xay dung|phat trien) ra ban\b", r"\bban duoc tao\b",
    r"\bban co (nguoi yeu|gia dinh|cam xuc)\b",
    r"\bthoi tiet\b", r"\bhom nay (la )?(thu|ngay) may\b", r"\bmay gio\b",
    r"\bke chuyen\b", r"\bhat (cho|mot)\b", r"\bban thich\b",
    r"\b(cam on|cang on|thanks?|thank you|tks|thank)\b",
]
# lời chào ĐƠN THUẦN (cả câu chỉ là chào, không kèm nội dung chính sách)
_CHAO = r"^(xin chao|chao( ban| buoi)?|hello|hi|hey|alo)[\s!.?]*$"


def cau_meta_lac_de(cau: str) -> bool:
    """True nếu câu là meta (hỏi về bot) / chào hỏi đơn thuần / tán gẫu lạc đề."""
    c = bo_dau(cau).strip().lower()
    if re.match(_CHAO, c):
        return True
    return any(re.search(p, c) for p in _META)


def cau_chuyen_huong() -> str:
    """Trả lời câu meta/lạc đề — kéo về đúng việc, không đoán chính sách."""
    return (
        "Mình là **PolicyRadar** — trợ lý tra cứu chính sách, ưu đãi và quỹ hỗ trợ "
        "cho doanh nghiệp, có căn cứ tới từng điều–khoản.\n\n"
        "Mình chỉ trả lời trong phạm vi đó, nên câu này mình xin phép không suy đoán. "
        "Bạn mô tả doanh nghiệp (lĩnh vực, lao động, doanh thu, vốn…) hoặc hỏi về một "
        "chương trình cụ thể để mình tra giúp nhé."
    )


# ── câu TRA CỨU CHUNG (muốn xem/tìm hiểu luật, KHÔNG phải xét điều kiện) ──
# Bug thật: "tôi muốn tìm hiểu thêm về luật" → bot đòi hồ sơ DN như thể xét
# điều kiện. Nhưng ý người dùng là DUYỆT/TRA luật. Phải phân biệt:
#   • tra cứu chung  → chỉ sang "Danh sách luật" (2.669 văn bản) / hỏi chủ đề
#   • xét điều kiện  → mới cần hồ sơ DN
# ⚠️ VIẾT KHÔNG DẤU — vì khớp trên chuỗi đã bo_dau (lỗi cũ: viết có dấu → trượt
#    đúng câu "tìm hiểu thêm về luật" mà người dùng báo).
_TRA_CUU = [
    r"\b(tim hieu|hieu them|muon hieu|xem them|doc them)\b.*\b(luat|van ban|chinh sach|nghi dinh|thong tu|quy dinh)\b",
    r"\btra cuu\b",
    r"\b(xem|coi|doc)\b.*\b(luat|van ban|nghi dinh|chinh sach)\b",
    r"\bco\b.*\b(luat|chinh sach|van ban|uu dai|nghi dinh|thong tu|quyet dinh)\b.*\b(gi|nao)\b",
    r"\bdanh sach\b.*\b(luat|van ban)\b",
    r"\btim\b.*\b(van ban|luat|nghi dinh)\b",
]


def cau_tra_cuu_chung(cau: str) -> bool:
    """True nếu là câu muốn DUYỆT/TRA luật chung (không kèm thông tin DN cụ thể)."""
    c = bo_dau(cau).strip().lower()
    # có số/thông tin DN (tỷ, triệu, lao động, %) → là mô tả DN, KHÔNG phải tra cứu chung
    if re.search(r"\d+\s*(t[yỷ]|tri[eệ]u|%|lao [dđ][oộ]ng|nh[aâ]n s[uự]|ng[uư][oờ]i)", c):
        return False
    return any(re.search(p, c) for p in _TRA_CUU)


def cau_moi_tra_cuu() -> str:
    """Hướng người dùng sang tra cứu luật — không đòi hồ sơ."""
    return (
        "Bạn muốn tra cứu văn bản đúng không? Mình có **kho 2.669 văn bản** (luật, "
        "nghị định, thông tư) — mở mục **“Danh sách luật”** ở thanh bên để tìm kiếm và "
        "lọc theo loại / lĩnh vực / cơ quan / năm.\n\n"
        "Hoặc nói rõ bạn quan tâm **chủ đề gì** (vd: ưu đãi thuế cho doanh nghiệp KH&CN, "
        "hỗ trợ doanh nghiệp nhỏ và vừa…) để mình tra thẳng vào điều–khoản giúp bạn."
    )


def hoi_van_ban_ngoai_kho(cau: str) -> str | None:
    """Hỏi đích danh văn bản KHÔNG có trong corpus → trả tên văn bản.

    Khớp cả dạng đầy đủ ('67/2025/QH15') lẫn dạng người ta hay nói ('Luật ... 67/2025').
    Bộ ca đối kháng bắt được: câu hỏi ghi '67/2025' mà key là '67/2025/QH15' → trượt.
    """
    c = cau.lower()
    for so, ten in NGOAI_CORPUS.items():
        if so.lower() in c:
            return ten
        # dạng rút gọn: '67/2025' — phải có BIÊN, kẻo '7/2025' khớp trúng '67/2025'
        goc = _so_goc(so)
        if re.search(rf"(?:^|[^\d/]){re.escape(goc)}(?:$|[^\d/])", c):
            return ten
    return None


def cau_tu_choi_linh_vuc(linh_vuc: str) -> str:
    return (
        f"Kho chính sách hiện tại của mình **chưa phủ lĩnh vực {linh_vuc}**, nên mình "
        f"không có căn cứ để trả lời — nói thẳng còn hơn đưa chương trình không liên quan.\n\n"
        f"Hiện mình đi sâu vào: {', '.join(sorted(DANG_PHU))}. "
        f"Kiến trúc nhân ra được cho lĩnh vực khác khi nạp thêm văn bản."
    )


def cau_tu_choi_van_ban(ten_vb: str) -> str:
    return (
        f"**{ten_vb} không có trong kho văn bản mình đang tra**, nên mình không trích "
        f"được điều khoản nào từ đó — không đoán.\n\n"
        f"Kho hiện dựng từ dump vbpl.vn (parse 21/05/2026). Muốn trả lời chính xác về "
        f"văn bản này thì phải nạp bản gốc vào kho trước."
    )
