"""Tầng HỘI THOẠI bằng GPT — thay routing regex cứng nhắc.

Phân vai (chốt với user): GPT lo HỘI THOẠI (hiểu ý + trích hồ sơ + trả lời tự
nhiên). Lõi FACTS vẫn tất định: xét đủ điều kiện, trích dẫn điều–khoản, con số
do matcher + guard lo. GPT KHÔNG được tự quyết eligibility hay bịa số/căn cứ.

Trả None nếu GPT lỗi → caller rơi về đường rule cũ (fallback I2, không đơ chat).
"""
from __future__ import annotations

import json
import re

# 10 field hồ sơ + kiểu — để GPT trích đúng, không tự chế khoá lạ
_FIELD_SPEC = """\
- linh_vuc: "nong_lam_thuy_san" (nông-lâm-thuỷ sản, hoặc công nghiệp-xây dựng) HOẶC "thuong_mai_dich_vu" (thương mại-dịch vụ). null nếu không rõ.
- lao_dong_bhxh: số nguyên — số lao động tham gia BHXH bình quân năm (vd "45 người" -> 45).
- doanh_thu: số nguyên VND — tổng doanh thu năm (vd "50 tỷ" -> 50000000000, "8 tỉ" -> 8000000000, "120 triệu" -> 120000000).
- von: số nguyên VND — tổng nguồn vốn (quy đổi như doanh_thu).
- ty_le_dt_khcn: số thực — % doanh thu từ sản phẩm KH&CN (vd "45%" -> 45).
- co_gcn_khcn: true/false — có Giấy chứng nhận DN khoa học và công nghệ không.
- nu_lam_chu: true/false — doanh nghiệp do nữ làm chủ.
- nganh: chuỗi — ngành nghề cụ thể (vd "sản xuất phần mềm").
- dia_ban: chuỗi — tỉnh/thành (vd "Hà Nội").
- fdi: true/false — có vốn đầu tư nước ngoài (FDI).\
"""

_HE_THONG = f"""\
Bạn là PolicyRadar — trợ lý tra cứu chính sách ưu đãi & quỹ hỗ trợ cho DOANH NGHIỆP Việt Nam \
(mạnh nhất ở: doanh nghiệp nhỏ và vừa, doanh nghiệp khoa học–công nghệ, ưu đãi thuế TNDN, quỹ tài trợ nghiên cứu).

NHIỆM VỤ của bạn CHỈ là tầng hội thoại: hiểu ý người dùng, trích thông tin hồ sơ doanh nghiệp từ câu nói, \
và trả lời tự nhiên, thân thiện, ngắn gọn bằng tiếng Việt.

TUYỆT ĐỐI KHÔNG được: tự kết luận doanh nghiệp "đủ/không đủ điều kiện"; tự bịa số tiền/tỷ lệ/mức hỗ trợ; \
bịa số hiệu văn bản hay điều–khoản. Những thứ đó do một bộ máy TẤT ĐỊNH khác tính và trích dẫn — \
bạn chỉ dẫn dắt hội thoại. Nếu người dùng hỏi mình đủ điều kiện gì, hãy đặt y_dinh="ket_qua" để hệ thống quét.

Nếu người dùng hỏi về lĩnh vực kho CHƯA phủ (nông nghiệp thuần, y tế, dược, giáo dục, bất động sản, \
du lịch, xây dựng dân dụng…), hãy nói THẲNG là kho hiện chưa phủ lĩnh vực đó, đừng bịa.

Phân loại y_dinh:
- "ket_qua": người dùng MÔ TẢ doanh nghiệp (có thông tin quy mô/ngành/vốn…) HOẶC hỏi "mình đủ điều kiện gì / có ưu đãi nào cho tôi". → hệ thống sẽ quét chính sách.
- "tra_cuu": muốn DUYỆT/TÌM HIỂU luật, văn bản nói chung (không phải xét điều kiện của chính họ). → mời sang mục "Danh sách luật".
- "tro_chuyen": chào hỏi, cảm ơn, hỏi về bạn (bot), hoặc câu lạc đề. → trả lời tự nhiên rồi kéo về đúng việc.

Trích hồ sơ (chỉ điền field NÀO người dùng THỰC SỰ nêu, còn lại bỏ trống):
{_FIELD_SPEC}

Trả về DUY NHẤT một object JSON, không giải thích thêm, dạng:
{{"y_dinh": "...", "ho_so": {{...}}, "tra_loi": "..."}}
- ho_so: chỉ chứa field trích được từ câu MỚI (object rỗng nếu không có).
- tra_loi: câu trả lời tự nhiên. Với y_dinh="ket_qua" mà bạn thấy còn thiếu thông tin để quét, \
hãy hỏi thêm một cách tự nhiên (không phải mẫu cứng). Với "ket_qua" đã đủ thông tin thì tra_loi để chuỗi rỗng "".\
"""


def _bo_rao_json(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    i, j = s.find("{"), s.rfind("}")
    return s[i : j + 1] if i >= 0 and j > i else s


def hieu(cau: str, ho_so: dict) -> dict | None:
    """Gọi GPT hiểu ý + trích hồ sơ + trả lời. None nếu lỗi (caller fallback rule)."""
    from gateway.client import goi_llm

    prompt = (
        f"Hồ sơ doanh nghiệp đã biết (giữ nguyên, chỉ bổ sung thêm nếu câu mới có):\n"
        f"{json.dumps(ho_so, ensure_ascii=False)}\n\n"
        f"Câu người dùng vừa nói:\n\"{cau}\"\n\n"
        f"Trả JSON theo đúng định dạng đã hướng dẫn."
    )
    try:
        raw = goi_llm(
            prompt, muc_dich="hoi-thoai-intent", tac_vu="task-deep",
            he_thong=_HE_THONG, temperature=0.3, max_tokens=400,
        )
        d = json.loads(_bo_rao_json(raw))
    except Exception:  # noqa: BLE001
        return None

    yd = d.get("y_dinh")
    if yd not in ("ket_qua", "tra_cuu", "tro_chuyen"):
        yd = "ket_qua"  # mặc định an toàn: cho lõi tất định quyết
    hs = d.get("ho_so") if isinstance(d.get("ho_so"), dict) else {}
    # chỉ giữ khoá hợp lệ, ép kiểu nhẹ
    tl = str(d.get("tra_loi") or "").strip()
    return {"y_dinh": yd, "ho_so": _loc_ho_so(hs), "tra_loi": tl}


_KIEU = {
    "linh_vuc": str, "lao_dong_bhxh": int, "doanh_thu": int, "von": int,
    "ty_le_dt_khcn": float, "co_gcn_khcn": bool, "nu_lam_chu": bool,
    "nganh": str, "dia_ban": str, "fdi": bool,
}


def _loc_ho_so(hs: dict) -> dict:
    """Giữ đúng 10 field, ép kiểu; bỏ giá trị None/rác. GPT có thể trả 'null'."""
    ra: dict = {}
    for k, kieu in _KIEU.items():
        if k not in hs:
            continue
        v = hs[k]
        if v is None or v == "" or (isinstance(v, str) and v.lower() in ("null", "none", "không rõ")):
            continue
        try:
            if kieu is bool:
                ra[k] = v if isinstance(v, bool) else str(v).lower() in ("true", "có", "co", "1", "yes")
            elif kieu is int:
                ra[k] = int(float(v)) if not isinstance(v, str) else int(float(re.sub(r"[^\d.]", "", v) or 0))
            elif kieu is float:
                ra[k] = float(v) if not isinstance(v, str) else float(re.sub(r"[^\d.]", "", v) or 0)
            else:
                ra[k] = str(v).strip()
        except Exception:  # noqa: BLE001
            continue
    return ra
