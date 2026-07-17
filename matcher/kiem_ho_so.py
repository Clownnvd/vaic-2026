"""Kiểm hồ sơ DN trước khi đối chiếu — bắt số vô lý.

VÌ SAO CẦN: bộ ca đối kháng bắt được 3 ca nhục:
    vốn = -5 tỷ    → "ĐỦ điều kiện" (vì -5 tỷ ≤ 100 tỷ = True)
    nhân sự = 0    → vẫn match
    chi R&D = 250% → "đủ điều kiện" (vì 250 ≥ 1.0 = True)
Toán đúng, nghiệp vụ sai. DN vốn âm / 0 người / tỷ lệ gấp 2,5 lần doanh thu
thì KHÔNG TỒN TẠI.

Mỉa mai đáng ghi: cả sản phẩm chống AI bịa số, mà chính nó không kiểm số đầu vào.

Nguyên tắc: giá trị vô lý → KHÔNG đối chiếu, báo thẳng. Đối chiếu rác ra kết
luận rác, mà kết luận rác lại trông rất tự tin — đó mới nguy.

⚠️ ĐÃ CẬP NHẬT theo Profile mới (đối chiếu nguyên văn 80/2021 và 13/2019):
   `nhan_su` → `lao_dong_bhxh` (luật đếm lao động CÓ THAM GIA BHXH bình quân năm)
   `chi_rnd` → `ty_le_dt_khcn` (Điều 12 K3: doanh thu sản phẩm KH&CN / tổng doanh thu)
   thêm `doanh_thu` — Điều 5 dùng doanh thu ở mọi ngưỡng, Profile cũ KHÔNG có.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

sys.path.insert(0, ".")
from matcher.schema import Profile  # noqa: E402

# ngưỡng nghiệp vụ — không phải giới hạn kỹ thuật
VON_MAX = 500_000_000_000_000  # 500 nghìn tỷ — lớn hơn mọi DN VN
DOANH_THU_MAX = 500_000_000_000_000
LAO_DONG_MAX = 1_000_000  # lớn hơn mọi DN VN


@dataclass(frozen=True)
class LoiHoSo:
    field: str
    gia_tri: object
    ly_do: str


NHAN = {
    "von": "tổng nguồn vốn",
    "doanh_thu": "tổng doanh thu",
    "lao_dong_bhxh": "lao động tham gia BHXH bình quân năm",
    "ty_le_dt_khcn": "tỷ lệ doanh thu từ sản phẩm KH&CN",
}


def _tien(loi: list, ten: str, v: int | None, tran: int) -> None:
    if v is None:
        return
    if v < 0:
        loi.append(LoiHoSo(ten, v, f"{NHAN[ten]} không thể âm"))
    elif v == 0 and ten == "von":
        loi.append(LoiHoSo(ten, v, "tổng nguồn vốn bằng 0 — doanh nghiệp chưa góp vốn?"))
    elif v > tran:
        loi.append(LoiHoSo(ten, v, f"{NHAN[ten]} vượt mọi doanh nghiệp Việt Nam — kiểm lại đơn vị"))


def kiem(p: Profile) -> list[LoiHoSo]:
    """Trả danh sách field vô lý. Rỗng = hồ sơ dùng được."""
    loi: list[LoiHoSo] = []

    _tien(loi, "von", p.von, VON_MAX)
    _tien(loi, "doanh_thu", p.doanh_thu, DOANH_THU_MAX)

    if p.lao_dong_bhxh is not None:
        if p.lao_dong_bhxh < 0:
            loi.append(LoiHoSo("lao_dong_bhxh", p.lao_dong_bhxh, "số lao động không thể âm"))
        elif p.lao_dong_bhxh == 0:
            loi.append(
                LoiHoSo("lao_dong_bhxh", p.lao_dong_bhxh, "doanh nghiệp 0 lao động — kiểm lại")
            )
        elif p.lao_dong_bhxh > LAO_DONG_MAX:
            loi.append(
                LoiHoSo("lao_dong_bhxh", p.lao_dong_bhxh, "số lao động vượt mọi doanh nghiệp Việt Nam")
            )

    if p.ty_le_dt_khcn is not None:
        if p.ty_le_dt_khcn < 0:
            loi.append(LoiHoSo("ty_le_dt_khcn", p.ty_le_dt_khcn, "tỷ lệ không thể âm"))
        elif p.ty_le_dt_khcn > 100:
            loi.append(
                LoiHoSo(
                    "ty_le_dt_khcn",
                    p.ty_le_dt_khcn,
                    f"{p.ty_le_dt_khcn}% — doanh thu một phần không thể vượt 100% tổng doanh thu",
                )
            )

    return loi


def mo_ta_loi(loi: list[LoiHoSo]) -> str:
    """Câu nói với người dùng — nêu ĐÍCH DANH field sai, không nói chung chung."""
    if not loi:
        return ""
    ds = "; ".join(f"{NHAN.get(x.field, x.field)} = {x.gia_tri} ({x.ly_do})" for x in loi)
    return (
        f"Hồ sơ có số liệu chưa hợp lệ nên mình chưa đối chiếu được: {ds}. "
        "Bạn kiểm lại giúp mình nhé."
    )
