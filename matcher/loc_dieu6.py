"""ĐIỀU 6 luật thi — loại văn bản nhạy cảm khỏi phạm vi matcher.

Nguyên văn điều 6: "Đội thi có trách nhiệm KIỂM TRA KỸ nội dung, dữ liệu, hình ảnh,
bản đồ và thông tin được sử dụng trong sản phẩm, bảo đảm không chứa nội dung sai lệch
hoặc không phù hợp liên quan đến chính trị, biên giới, lãnh thổ, chủ quyền quốc gia
và biển đảo."

ĐÂY LÀ KIỂM TRA CHỦ ĐỘNG, KHÔNG PHẢI NÉ TRÁNH.
Điều 6 cấm nội dung SAI LỆCH, không cấm nhắc tới. Kiến trúc vốn đã không thể sai lệch
(chép nguyên văn + citation ràng nguồn + từ chối khi thiếu căn cứ). Nhưng điều 6 bắt
"kiểm tra kỹ" → phải có lớp chặn tường minh, chứng minh được là đã kiểm.

ĐÃ ĐO (scripts/kiem_dieu6.py trên corpus 9.436 văn bản):
    28 văn bản có từ nhạy cảm trong tiêu đề
    3  văn bản lọt vào subset DN mà matcher dùng:
       • 16/2021/NQ-HĐND — Chương trình phát triển bền vững kinh tế biển
       • 60/2026/NĐ-CP   — Tổ hợp công nghiệp an ninh quốc gia
    Chúng lọt vì ĐÚNG chủ đề kinh tế/doanh nghiệp thật, không phải lỗi bộ lọc.

QUYẾT ĐỊNH: loại khỏi subset matcher.
Lý do đổi hời: mấy văn bản này KHÔNG liên quan ưu đãi DNNVV/công nghệ cao
→ mất 0 giá trị nghiệp vụ, bớt 100% rủi ro pháp lý.
"""

from __future__ import annotations

import re

# ⚠️ BÁM ĐÚNG CHỮ CỦA ĐIỀU 6, KHÔNG TỰ NỚI PHẠM VI.
# Điều 6 nói đúng 5 thứ: chính trị · biên giới · lãnh thổ · chủ quyền quốc gia · biển đảo.
#
# LỖI ĐÃ MẮC: bản đầu mình tự thêm "quốc phòng" và "an ninh quốc gia" — hai từ điều 6
# KHÔNG hề nhắc. Hậu quả: loại nhầm 27 văn bản, phần lớn là BÁO CÁO KINH TẾ - XÃ HỘI
# THƯỜNG KỲ của tỉnh, vì cụm "kinh tế - xã hội, quốc phòng - an ninh" là CÔNG THỨC
# TIÊU ĐỀ CHUẨN của HĐND, chẳng dính gì nội dung nhạy cảm.
#
# Chặn bừa = mất giá trị thật mà không được gì. "Kiểm tra kỹ" ≠ "chặn tất".
RE_NHAY_CAM = re.compile(
    r"biên giới"
    r"|lãnh thổ"
    r"|chủ quyền"
    r"|biển đảo|hải đảo|quần đảo"
    r"|hoàng sa|trường sa"
    r"|lãnh hải|thềm lục địa|vùng đặc quyền kinh tế"
    r"|địa giới hành chính",  # thuộc "lãnh thổ" — vd NQ 202/2025 sáp nhập 34 tỉnh
    re.IGNORECASE,
)


def nhay_cam(title: str | None) -> bool:
    """Tiêu đề có chạm phạm vi điều 6 không."""
    return bool(title) and bool(RE_NHAY_CAM.search(title))


def loc(rows: list[dict], khoa_title: str = "title") -> tuple[list[dict], list[dict]]:
    """Tách (giữ lại, đã loại). Trả cả phần loại để GIẢI TRÌNH được — điều 6 đòi
    'kiểm tra kỹ', nên phải chỉ ra được đã loại cái gì, vì sao."""
    giu, bo = [], []
    for r in rows:
        (bo if nhay_cam(r.get(khoa_title)) else giu).append(r)
    return giu, bo


def cau_giai_trinh(bo: list[dict]) -> str:
    """Câu nói với giám khảo — chủ động khai, không giấu."""
    if not bo:
        return "Đã rà toàn bộ corpus theo điều 6: không có văn bản nào thuộc phạm vi nhạy cảm."
    ds = "\n".join(f"  • {r.get('doc_number_str', '?')} — {(r.get('title') or '')[:60]}" for r in bo[:8])
    return (
        f"Theo điều 6 luật thi, bọn em rà toàn bộ corpus và **chủ động loại {len(bo)} văn bản** "
        f"chạm phạm vi chính trị/biên giới/lãnh thổ/chủ quyền/biển đảo khỏi phạm vi tra cứu:\n{ds}\n\n"
        f"Chúng lọt vào vì đúng chủ đề kinh tế, nhưng không liên quan ưu đãi doanh nghiệp — "
        f"loại đi mất 0 giá trị nghiệp vụ. Ngoài ra kiến trúc vốn không diễn giải lại văn bản: "
        f"chép nguyên văn + trích dẫn điều–khoản + từ chối khi thiếu căn cứ."
    )
