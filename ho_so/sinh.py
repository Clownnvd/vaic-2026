"""③ Sinh khung hồ sơ — structure-then-fill. AI KHÔNG được gõ số.

Kho chốt: "structure-then-fill | email → **khung hồ sơ grant** | Checklist còn thiếu gì"
Tức tái dùng đúng rail soạn-email, đổi phích sang hồ sơ.

Ba nguồn điền, phân vai rạch ròi:
  • `ho_so`  → CODE điền từ profile DN            (AI không chạm)
  • `corpus` → CODE chép verbatim từ văn bản      (AI không chạm)
  • `nguoi`  → DN tự điền                          (AI chỉ gợi ý, đánh dấu rõ)

Vì sao không cho AI điền: mọi số trong hồ sơ nộp cơ quan nhà nước mà sai =
DN nộp sai, mất cơ hội, gánh rủi ro pháp lý. Đây là chỗ đắt nhất để bịa.

Write-gate: hồ sơ là HÀNH ĐỘNG GHI → `requires_approval=True`, bản nháp chờ
người duyệt. Kho: "Người bấm Duyệt, không phải AI tự gửi."
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

sys.path.insert(0, ".")
from ho_so.mau import MauHoSo, TAT_CA, THEO_CHUONG_TRINH  # noqa: E402
from vn.context import format_vnd  # noqa: E402


@dataclass
class O:
    """Một ô đã điền (hoặc chưa)."""

    khoa: str
    nhan: str
    gia_tri: str | None
    nguon: str
    da_dien: bool
    ai_duoc_go: bool  # luôn False cho ô số/dữ kiện — bằng chứng AI không chạm


@dataclass
class KhungHoSo:
    mau: MauHoSo
    o: list[O] = field(default_factory=list)
    thieu: list[str] = field(default_factory=list)  # ô bắt buộc chưa có
    requires_approval: bool = True  # write-gate — LUÔN True
    citations: list[str] = field(default_factory=list)

    @property
    def phan_tram_day(self) -> float:
        bb = [x for x in self.o if x.khoa]
        return round(sum(1 for x in bb if x.da_dien) / max(len(bb), 1), 3)


def _tu_ho_so(khoa: str, hs: dict) -> str | None:
    """Điền từ profile DN. CODE lấy, không phải AI gõ."""
    v = hs.get(khoa)
    if v is None:
        return None
    if khoa == "von":
        return format_vnd(int(v), rut_gon=False)
    if khoa == "nhan_su":
        return f"{v} người"
    if khoa == "chi_rnd":
        return f"{str(v).replace('.', ',')}% doanh thu"
    if khoa == "fdi":
        return "Có" if v else "Không"
    return str(v)


def sinh_khung(mau: MauHoSo, ho_so: dict) -> KhungHoSo:
    """1 biểu mẫu + hồ sơ DN → khung điền sẵn phần CODE biết, chừa phần DN tự khai."""
    k = KhungHoSo(mau=mau)

    for t in mau.truong:
        gt: str | None = None
        if t.nguon == "ho_so":
            gt = _tu_ho_so(t.khoa, ho_so)
        # nguồn "corpus": chép verbatim từ văn bản — nối khi curate xong điều khoản
        # nguồn "nguoi": để trống, DN tự điền

        k.o.append(
            O(
                khoa=t.khoa,
                nhan=t.nhan,
                gia_tri=gt,
                nguon=t.nguon,
                da_dien=gt is not None,
                ai_duoc_go=False,  # KHÔNG ô nào cho AI gõ
            )
        )
        if t.bat_buoc and gt is None:
            k.thieu.append(t.nhan)

    k.citations = [mau.can_cu]
    return k


def checklist(ma_chuong_trinh: str, ho_so: dict) -> list[KhungHoSo]:
    """Chương trình → bộ hồ sơ cần nộp + trạng thái điền của từng mẫu."""
    ma_list = THEO_CHUONG_TRINH.get(ma_chuong_trinh, [])
    ra = []
    for m in TAT_CA:
        if m.ma in ma_list:
            ra.append(sinh_khung(m, ho_so))
    return ra


def render_text(k: KhungHoSo) -> str:
    """Xuất khung dạng đọc được. Mọi giá trị là CODE điền, AI không gõ chữ số nào."""
    d = [
        f"{k.mau.ma} — {k.mau.ten}",
        f"Căn cứ: {k.mau.can_cu}",
        f"Nơi nhận: {k.mau.co_quan_nhan}",
    ]
    if k.mau.han_nop:
        d.append(f"Hạn nộp: {k.mau.han_nop}")
    d.append("")
    for o in k.o:
        if o.da_dien:
            d.append(f"  {o.nhan}: {o.gia_tri}")
        elif o.nguon == "nguoi":
            d.append(f"  {o.nhan}: ____________  (doanh nghiệp tự điền)")
        else:
            d.append(f"  {o.nhan}: ____________  (thiếu trong hồ sơ)")
    if k.mau.ghi_chu:
        d += ["", f"Lưu ý: {k.mau.ghi_chu}"]
    d += ["", "— BẢN NHÁP, chờ bạn duyệt trước khi nộp —"]
    return "\n".join(d)
