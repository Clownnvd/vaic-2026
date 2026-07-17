"""Matcher CHẠY NGƯỢC — profile DN → quét ngược điều kiện → xếp hạng.

Khác chatbot ở chỗ: chatbot đợi người ta biết mà hỏi. Matcher chủ động quét
NGƯỢC toàn bộ điều kiện thụ hưởng rồi nói "bạn đủ điều kiện những cái này".

Đối chiếu bằng CODE, không phải LLM. Ba lý do:
  1. Phải gọi tên đích danh điều kiện thiếu ("chưa, vì thiếu Y") — Khối demo 2.
  2. Kết quả phải TẤT ĐỊNH: cùng hồ sơ → cùng kết quả, mọi lần.
  3. Giải trình được: mỗi dòng có citation riêng, giám khảo bấm là ra nguồn.

Kho chốt: lớp này chạy TRƯỚC ranker, tách khỏi RAG.
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from matcher.schema import (  # noqa: E402
    ChuongTrinh,
    DieuKien,
    KetQuaDieuKien,
    KetQuaKhop,
    Profile,
    ToanTu,
    TrangThai,
)

# thiếu thông tin thì coi như "có thể đạt" ở mức nào — KHÔNG cho 1.0 (lạc quan
# hoá là bịa), KHÔNG cho 0.0 (bi quan hoá thì hỏi thêm cũng vô nghĩa).
P_THIEU_TIN = 0.5


def _so_sanh(dk: DieuKien, gt) -> tuple[TrangThai, str]:
    if gt is None:
        return TrangThai.THIEU_TIN, "hồ sơ chưa khai"

    t = dk.toan_tu
    try:
        if t is ToanTu.GTE:
            ok = gt >= dk.nguong
        elif t is ToanTu.LTE:
            ok = gt <= dk.nguong
        elif t is ToanTu.EQ:
            ok = gt == dk.nguong
        elif t is ToanTu.IN:
            ok = gt in dk.nguong
        elif t is ToanTu.NOT_IN:
            ok = gt not in dk.nguong
        else:
            return TrangThai.THIEU_TIN, "toán tử không hỗ trợ"
    except TypeError:
        return TrangThai.THIEU_TIN, "kiểu dữ liệu không so được"

    return (
        (TrangThai.DAT, f"{gt} {t.value} {dk.nguong}")
        if ok
        else (TrangThai.KHONG_DAT, f"{gt} không thoả {t.value} {dk.nguong}")
    )


def doi_chieu(profile: Profile, ct: ChuongTrinh) -> KetQuaKhop:
    """Đối chiếu 1 hồ sơ với 1 chương trình. Tất định, giải trình được."""
    chi_tiet: list[KetQuaDieuKien] = []
    thieu: list[str] = []
    can_hoi: list[str] = []
    dat = 0.0
    tong_trong_so = 0.0

    for dk in ct.dieu_kien:
        gt = getattr(profile, dk.field, None)
        tt, gt_thich = _so_sanh(dk, gt)
        chi_tiet.append(KetQuaDieuKien(dk, tt, gt, gt_thich))

        w = 1.0 if dk.bat_buoc else 0.5
        tong_trong_so += w
        if tt is TrangThai.DAT:
            dat += w
        elif tt is TrangThai.THIEU_TIN:
            dat += w * P_THIEU_TIN
            can_hoi.append(dk.field)
        else:
            thieu.append(dk.mo_ta)  # tên ĐÍCH DANH cho câu "chưa, vì thiếu Y"

    p = dat / tong_trong_so if tong_trong_so else 0.0

    # đủ điều kiện = KHÔNG điều kiện bắt buộc nào KHÔNG ĐẠT
    # (thiếu tin ≠ không đạt — phải hỏi, không được kết luận)
    du = not any(
        c.trang_thai is TrangThai.KHONG_DAT and c.dieu_kien.bat_buoc for c in chi_tiet
    )

    # giá trị kỳ vọng = P(phù hợp) × tác động   (template kho: P × tác động)
    ev = p * (ct.gia_tri_uoc or 0)

    return KetQuaKhop(
        chuong_trinh=ct,
        chi_tiet=chi_tiet,
        diem_phu_hop=round(p, 4),
        gia_tri_ky_vong=ev,
        du_dieu_kien=du,
        thieu=thieu,
        can_hoi_them=sorted(set(can_hoi)),
    )


def quet_nguoc(
    profile: Profile, kho: list[ChuongTrinh], chi_du_dieu_kien: bool = False
) -> list[KetQuaKhop]:
    """Quét NGƯỢC toàn bộ kho chương trình → xếp theo giá trị kỳ vọng giảm dần."""
    ra = [doi_chieu(profile, ct) for ct in kho]
    if chi_du_dieu_kien:
        ra = [r for r in ra if r.du_dieu_kien]
    return sorted(ra, key=lambda r: (-r.gia_tri_ky_vong, -r.diem_phu_hop))


def diff_ket_qua(
    truoc: list[KetQuaKhop], sau: list[KetQuaKhop]
) -> dict[str, list[str]]:
    """MONITORING (② của đề) — chạy matcher 2 lần trên 2 snapshot rồi lấy hiệu.

    Không cần API hiệu lực để dựng mắt xích này: 'DN nào vừa đủ / vừa mất điều
    kiện' tính được ngay từ 2 lần chạy matcher. Chỉ mắt xích 'khoản nào đổi'
    mới cần nguồn hiệu lực bên ngoài.
    """
    d1 = {r.chuong_trinh.id for r in truoc if r.du_dieu_kien}
    d2 = {r.chuong_trinh.id for r in sau if r.du_dieu_kien}
    return {
        "vua_du": sorted(d2 - d1),
        "vua_mat": sorted(d1 - d2),
        "giu_nguyen": sorted(d1 & d2),
    }
