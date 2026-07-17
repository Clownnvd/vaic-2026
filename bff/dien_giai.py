"""Bước LLM DIỄN GIẢI luật (yêu cầu ① "interpreting") + GUARD gác live.

VÌ SAO CÓ FILE NÀY:
  /chat trước đây thuần tất định (matcher → thẻ). Không có LLM sinh text →
  guard (thứ bắt LLM bịa) KHÔNG có gì để gác → model train xong nằm không.
  Nay: LLM viết một đoạn DIỄN GIẢI ngắn "vì sao DN đủ điều kiện, được hưởng gì",
  grounded theo nguyên văn điều luật đã trích. Guard kiểm ngay đoạn đó:
    • lớp SỐ (tất định, guard/vn_number.lech_so): số nào trong diễn giải KHÔNG
      có trong nguồn trích → BỊA → tô đỏ + hạ cờ grounded.
  Đây là chỗ guard load-bearing THẬT: LLM có thể bịa "60%", "300 triệu" — lớp số
  bắt tại trận, đối chiếu nguyên văn corpus.

  (PhoBERT NLI gác trục NGỮ NGHĨA — nạp nặng 515MB, để lazy/riêng; lớp số chạy
   live vì nhanh + chính xác tuyệt đối với con số.)

Mọi call LLM đi qua gateway.goi_llm → có audit (J) + fallback (I2).
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from gateway.client import goi_llm  # noqa: E402
from guard.vn_number import lech_so  # noqa: E402

HE_THONG = (
    "Bạn là trợ lý chính sách cho doanh nghiệp Việt Nam. Bạn CHỈ được nêu con số "
    "(phần trăm, số tiền, thời hạn, năm) CÓ trong đoạn văn bản pháp luật được cung cấp. "
    "TUYỆT ĐỐI không tự thêm hay làm tròn số. Nếu đoạn luật không nêu con số nào thì "
    "diễn giải bằng lời, không bịa số."
)


def _nguon_trich(chuong_trinh: list) -> str:
    """Gom nguyên văn các điều–khoản đã trích của những chương trình đủ điều kiện.

    Gồm cả `citation_chinh` (mức hỗ trợ — vd Điều 13 K2 có "50%, 50 triệu") lẫn
    citation từng điều kiện. Có đủ nguyên văn thì diễn giải mới nêu được con số
    hỗ trợ cụ thể, và guard mới có nguồn để đối chiếu.
    """
    doan = []
    seen = set()
    for ct in chuong_trinh:
        cits = ([ct.citation_chinh] if ct.citation_chinh else []) + [
            dk.citation for dk in ct.dieu_kien
        ]
        for c in cits:
            if c and c.trich and c.khoa not in seen:
                seen.add(c.khoa)
                doan.append(f"[{c}] {c.trich}")
    return "\n\n".join(doan)


def dien_giai_va_gac(chuong_trinh_du: list, ten_ct: list[str]) -> dict | None:
    """Sinh diễn giải cho các chương trình ĐỦ điều kiện + guard kiểm số.

    Trả None nếu không có gì để diễn giải (không đủ chương trình / không có nguồn).
    Không bao giờ ném lỗi ra /chat — LLM lỗi thì trả None, thẻ vẫn hiện.
    """
    if not chuong_trinh_du:
        return None
    nguon = _nguon_trich(chuong_trinh_du)
    if not nguon:
        return None

    prompt = (
        f"Doanh nghiệp đủ điều kiện các chương trình: {', '.join(ten_ct)}.\n\n"
        f"Dựa CHỈ vào các đoạn luật dưới đây, viết 2-3 câu tiếng Việt giải thích cho "
        f"doanh nghiệp: họ được hưởng mức hỗ trợ CỤ THỂ gì (nêu đúng con số trong luật), "
        f"và căn cứ ở đâu. Ngắn gọn, không lặp lại nguyên văn.\n\n"
        f"Các đoạn luật:\n{nguon}\n\nDiễn giải:"
    )

    try:
        text = goi_llm(
            prompt, "dien-giai-chinh-sach", "task-deep",
            he_thong=HE_THONG, max_tokens=260, temperature=0.2,
        )
    except Exception:  # noqa: BLE001
        return None  # LLM/gateway lỗi → bỏ diễn giải, thẻ vẫn đủ dùng

    if not text:
        return None

    # ── GUARD lớp SỐ: số nào trong diễn giải KHÔNG có trong nguồn → bịa ──
    bia = lech_so(text, nguon)
    grounded = len(bia) == 0

    return {
        "text": text,
        "grounded": grounded,
        "so_bia": [
            {"raw": s.raw, "loai": s.loai, "bat_dau": s.bat_dau, "ket_thuc": s.ket_thuc}
            for s in bia
        ],
        "guard": "so_tat_dinh",  # lớp đã gác
        "canh_bao": (
            None
            if grounded
            else "Guard phát hiện số không có trong căn cứ — đã tô đỏ, không dùng để ra quyết định."
        ),
    }
