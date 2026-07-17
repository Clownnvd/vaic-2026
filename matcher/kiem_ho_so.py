"""Kiểm hồ sơ DN trước khi đối chiếu — bắt số vô lý.

VÌ SAO CẦN: bộ ca đối kháng bắt được 3 ca nhục:
    vốn = -5 tỷ    → "ĐỦ điều kiện" (vì -5 tỷ ≤ 100 tỷ = True)
    nhân sự = 0    → vẫn match
    chi R&D = 250% → "đủ điều kiện công nghệ cao" (vì 250 ≥ 1.0 = True)
Toán đúng, nghiệp vụ sai. DN vốn âm / 0 người / chi R&D gấp 2,5 lần doanh thu
thì KHÔNG TỒN TẠI.

Mỉa mai đáng ghi: cả sản phẩm chống AI bịa số, mà chính nó không kiểm số đầu vào.

Nguyên tắc: giá trị vô lý → KHÔNG đối chiếu, báo thẳng. Đối chiếu rác ra kết
luận rác, mà kết luận rác lại trông rất tự tin — đó mới nguy.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

sys.path.insert(0, ".")
from matcher.schema import Profile  # noqa: E402

# ngưỡng nghiệp vụ — không phải giới hạn kỹ thuật
VON_MAX = 500_000_000_000_000  # 500 nghìn tỷ — lớn hơn mọi DN VN
NHAN_SU_MAX = 1_000_000  # lớn hơn mọi DN VN


@dataclass(frozen=True)
class LoiHoSo:
    field: str
    gia_tri: object
    ly_do: str


def kiem(p: Profile) -> list[LoiHoSo]:
    """Trả danh sách field vô lý. Rỗng = hồ sơ dùng được."""
    loi: list[LoiHoSo] = []

    if p.von is not None:
        if p.von < 0:
            loi.append(LoiHoSo("von", p.von, "vốn điều lệ không thể âm"))
        elif p.von == 0:
            loi.append(LoiHoSo("von", p.von, "vốn điều lệ bằng 0 — doanh nghiệp chưa góp vốn?"))
        elif p.von > VON_MAX:
            loi.append(LoiHoSo("von", p.von, "vốn vượt mọi doanh nghiệp Việt Nam — kiểm lại đơn vị"))

    if p.nhan_su is not None:
        if p.nhan_su < 0:
            loi.append(LoiHoSo("nhan_su", p.nhan_su, "số nhân sự không thể âm"))
        elif p.nhan_su == 0:
            loi.append(LoiHoSo("nhan_su", p.nhan_su, "doanh nghiệp 0 nhân sự — kiểm lại"))
        elif p.nhan_su > NHAN_SU_MAX:
            loi.append(LoiHoSo("nhan_su", p.nhan_su, "số nhân sự vượt mọi doanh nghiệp Việt Nam"))

    if p.chi_rnd is not None:
        if p.chi_rnd < 0:
            loi.append(LoiHoSo("chi_rnd", p.chi_rnd, "chi R&D không thể âm"))
        elif p.chi_rnd > 100:
            loi.append(
                LoiHoSo(
                    "chi_rnd",
                    p.chi_rnd,
                    f"chi R&D {p.chi_rnd}% doanh thu — không thể vượt 100% doanh thu",
                )
            )

    return loi


def mo_ta_loi(loi: list[LoiHoSo]) -> str:
    """Câu nói với người dùng — nêu ĐÍCH DANH field sai, không nói chung chung."""
    if not loi:
        return ""
    NHAN = {"von": "vốn điều lệ", "nhan_su": "số nhân sự", "chi_rnd": "chi R&D"}
    ds = "; ".join(f"{NHAN.get(x.field, x.field)} = {x.gia_tri} ({x.ly_do})" for x in loi)
    return (
        f"Hồ sơ có số liệu chưa hợp lệ nên mình chưa đối chiếu được: {ds}. "
        "Bạn kiểm lại giúp mình nhé."
    )
