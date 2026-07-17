"""Guard hoàn chỉnh = TẤT ĐỊNH (tra corpus + đối chiếu số) → NLI (ngữ nghĩa).

Phân công theo đúng năng lực:
  • Tất định gánh 6/7 trục — tra được, không cãi được, ~1.0 chính xác.
  • NLI chỉ gánh trục ngữ nghĩa ("DN đủ điều kiện") — thứ không tra được bằng rule.

Bài học đắt: bắt model char n-gram bắt "50%→80%" chỉ đạt 0.04. Không phải model
kém — mà việc đó VỀ NGUYÊN LÝ không hợp với model. Giao đúng người đúng việc.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, ".")
from guard.lookup import IndexCorpus, boc_citation  # noqa: E402
from guard.vn_number import SoTimThay, lech_so  # noqa: E402


class KetLuan(str, Enum):
    DU_CAN_CU = "du_can_cu"
    CHAN = "chan"
    CHUA_DU_CAN_CU = "chua_du_can_cu"


@dataclass
class PhanQuyet:
    ket_luan: KetLuan
    tang: str  # tầng nào ra quyết định — để giải trình
    ly_do: str
    so_bia: list[SoTimThay] | None = None


def kiem_tra(
    claim: str,
    premise: str,
    idx: IndexCorpus,
) -> PhanQuyet:
    """Một câu AI nói → phán quyết. Chạy tất định TRƯỚC (rẻ + chắc)."""

    # ── TẦNG 1: citation có tồn tại không ────────────────────
    cit = boc_citation(claim)
    if cit is None:
        return PhanQuyet(
            KetLuan.CHUA_DU_CAN_CU, "tang1_citation", "Câu không kèm trích dẫn điều–khoản"
        )

    r = idx.tra_doc(cit.so_vb, cit.co_quan)
    if not r.ton_tai:
        return PhanQuyet(KetLuan.CHAN, "tang1_ton_tai", r.ly_do)

    r2 = idx.tra_dieu_khoan(cit.so_vb, cit.co_quan, cit.dieu, cit.khoan)
    if not r2.ton_tai:
        return PhanQuyet(KetLuan.CHAN, "tang1_vi_tri", r2.ly_do)

    # ── TẦNG 2: số trong câu có khớp ĐÚNG CHỖ ĐƯỢC TRÍCH không ──
    # Đối chiếu với text TẠI VỊ TRÍ AI TRÍCH (r2.text_khoan), KHÔNG phải với
    # premise mình sẵn có. Vì câu hỏi đúng là: "cái nguồn ANH TRÍCH có nói vậy không?"
    # Trích đúng nội dung nhưng gắn nhầm Điều/Khoản → chỉ cách này mới bắt được.
    nguon = r2.text_khoan or premise
    lech = lech_so(claim, nguon)
    if lech:
        ds = ", ".join(f"'{s.raw}'" for s in lech)
        return PhanQuyet(
            KetLuan.CHAN,
            "tang2_so",
            f"Số {ds} không có trong {cit.so_vb} Điều {cit.dieu} Khoản {cit.khoan}",
            so_bia=lech,
        )

    # ── TẦNG 3: ngữ nghĩa — phần này để NLI lo ───────────────
    return PhanQuyet(
        KetLuan.DU_CAN_CU, "tang3_nli", "Citation khớp, số khớp — còn lại chuyển NLI"
    )
