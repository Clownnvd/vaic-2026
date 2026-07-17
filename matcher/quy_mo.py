"""Xác định quy mô DNNVV theo Điều 5 Nghị định 80/2021/NĐ-CP — TẤT ĐỊNH.

VÌ SAO CÓ FILE NÀY (và vì sao kho_mau cũ SAI):
  Luật KHÔNG nói "nhân sự ≤ 200 người" một cách phẳng. Nó nói:
    • ngưỡng lao động ĐỔI THEO LĨNH VỰC: 200 (nông-lâm-thuỷ sản / CN-XD)
      nhưng chỉ 100 (thương mại - dịch vụ)
    • đếm "lao động CÓ THAM GIA BHXH BÌNH QUÂN NĂM", không phải đầu người
    • doanh thu HOẶC nguồn vốn — là HOẶC, không phải hai điều kiện rời
    • xét theo BẬC THANG: siêu nhỏ → nhỏ → vừa, mỗi bậc "nhưng KHÔNG PHẢI
      là bậc dưới"
  kho_mau cũ dẹp hết thành 2 điều kiện phẳng "nhan_su ≤ 200" + "von ≤ 100 tỷ"
  → sai với thương mại-dịch vụ, và biến HOẶC thành VÀ.

Điều 5 nguyên văn (đã moi từ corpus, xem scripts/moi_nguyen_van.py):
  K1 siêu nhỏ  A: LĐ ≤ 10  và (DT ≤ 3 tỷ   hoặc vốn ≤ 3 tỷ)
               B: LĐ ≤ 10  và (DT ≤ 10 tỷ  hoặc vốn ≤ 3 tỷ)
  K2 nhỏ       A: LĐ ≤ 100 và (DT ≤ 50 tỷ  hoặc vốn ≤ 20 tỷ)   & không phải siêu nhỏ
               B: LĐ ≤ 50  và (DT ≤ 100 tỷ hoặc vốn ≤ 50 tỷ)   & không phải siêu nhỏ
  K3 vừa       A: LĐ ≤ 200 và (DT ≤ 200 tỷ hoặc vốn ≤ 100 tỷ)  & không phải siêu nhỏ/nhỏ
               B: LĐ ≤ 100 và (DT ≤ 300 tỷ hoặc vốn ≤ 100 tỷ)  & không phải siêu nhỏ/nhỏ
  A = nông nghiệp, lâm nghiệp, thuỷ sản; công nghiệp và xây dựng
  B = thương mại và dịch vụ
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, ".")
from matcher.schema import Citation, Profile  # noqa: E402

TY = 1_000_000_000


class LinhVuc(str, Enum):
    """2 nhóm lĩnh vực Điều 5 gộp — KHÔNG phải ngành nghề tự do."""

    NONG_CN_XD = "nong_lam_thuy_san__cong_nghiep_xay_dung"
    THUONG_MAI_DV = "thuong_mai_dich_vu"


class QuyMo(str, Enum):
    SIEU_NHO = "sieu_nho"
    NHO = "nho"
    VUA = "vua"
    NGOAI = "ngoai"  # lớn hơn DN vừa → không thuộc phạm vi hỗ trợ DNNVV


# (lao động tối đa, doanh thu tối đa, vốn tối đa) theo (quy mô, lĩnh vực)
NGUONG: dict[tuple[QuyMo, LinhVuc], tuple[int, int, int]] = {
    (QuyMo.SIEU_NHO, LinhVuc.NONG_CN_XD): (10, 3 * TY, 3 * TY),
    (QuyMo.SIEU_NHO, LinhVuc.THUONG_MAI_DV): (10, 10 * TY, 3 * TY),
    (QuyMo.NHO, LinhVuc.NONG_CN_XD): (100, 50 * TY, 20 * TY),
    (QuyMo.NHO, LinhVuc.THUONG_MAI_DV): (50, 100 * TY, 50 * TY),
    (QuyMo.VUA, LinhVuc.NONG_CN_XD): (200, 200 * TY, 100 * TY),
    (QuyMo.VUA, LinhVuc.THUONG_MAI_DV): (100, 300 * TY, 100 * TY),
}

KHOAN_CUA = {QuyMo.SIEU_NHO: 1, QuyMo.NHO: 2, QuyMo.VUA: 3}


def citation_quy_mo(qm: QuyMo, trich: str) -> Citation:
    return Citation(
        so_vb="80/2021/NĐ-CP",
        co_quan="Chính phủ",
        dieu=5,
        khoan=KHOAN_CUA.get(qm),
        trich=trich,
        doc_id="158783",
    )


@dataclass(frozen=True)
class KetQuaQuyMo:
    quy_mo: QuyMo | None  # None = THIẾU TIN, không kết luận
    citation: Citation | None
    giai_thich: str
    thieu_field: list[str]


def xac_dinh_quy_mo(p: Profile) -> KetQuaQuyMo:
    """Điều 5 → bậc quy mô. THIẾU TIN thì trả None, TUYỆT ĐỐI không đoán.

    Đoán bừa ở đây = kết luận DN đủ/không đủ điều kiện dựa trên thứ không biết
    → DN nộp sai hồ sơ. Thà hỏi thêm.
    """
    thieu = [
        t
        for t, v in (
            ("linh_vuc", p.linh_vuc),
            ("lao_dong_bhxh", p.lao_dong_bhxh),
        )
        if v is None
    ]
    # doanh thu HOẶC vốn — chỉ cần MỘT trong hai là xét được (luật ghi "hoặc")
    if p.doanh_thu is None and p.von is None:
        thieu.append("doanh_thu hoặc von")
    if thieu:
        return KetQuaQuyMo(None, None, f"Chưa đủ thông tin: {', '.join(thieu)}", thieu)

    try:
        lv = LinhVuc(p.linh_vuc)
    except ValueError:
        return KetQuaQuyMo(
            None, None, f"Lĩnh vực '{p.linh_vuc}' không thuộc 2 nhóm của Điều 5", ["linh_vuc"]
        )

    # BẬC THANG: xét siêu nhỏ trước, rồi nhỏ, rồi vừa — đúng thứ tự luật
    # ("nhưng không phải là doanh nghiệp siêu nhỏ theo quy định tại khoản 1").
    for qm in (QuyMo.SIEU_NHO, QuyMo.NHO, QuyMo.VUA):
        max_ld, max_dt, max_von = NGUONG[(qm, lv)]
        if p.lao_dong_bhxh > max_ld:
            continue
        # ── HOẶC, không phải VÀ ──
        hop_dt = p.doanh_thu is not None and p.doanh_thu <= max_dt
        hop_von = p.von is not None and p.von <= max_von
        if not (hop_dt or hop_von):
            continue
        ly = (
            f"lao động BHXH bình quân {p.lao_dong_bhxh} ≤ {max_ld}"
            f" và ({'doanh thu ≤ ' + f'{max_dt/TY:.0f} tỷ' if hop_dt else ''}"
            f"{' hoặc ' if hop_dt and hop_von else ''}"
            f"{'nguồn vốn ≤ ' + f'{max_von/TY:.0f} tỷ' if hop_von else ''})"
        )
        return KetQuaQuyMo(qm, citation_quy_mo(qm, ""), ly, [])

    return KetQuaQuyMo(
        QuyMo.NGOAI,
        citation_quy_mo(QuyMo.VUA, ""),
        "Vượt ngưỡng doanh nghiệp vừa tại Điều 5 → không thuộc diện hỗ trợ DNNVV",
        [],
    )


# ── Điều 13 Khoản 2: mức hỗ trợ tư vấn theo quy mô ──────────────
# (% giá trị hợp đồng, trần thường, trần khi nữ làm chủ/nhiều LĐ nữ/DN xã hội)
TR = 1_000_000
HO_TRO_TU_VAN: dict[QuyMo, tuple[int, int, int]] = {
    QuyMo.SIEU_NHO: (100, 50 * TR, 70 * TR),
    QuyMo.NHO: (50, 100 * TR, 150 * TR),
    QuyMo.VUA: (30, 150 * TR, 200 * TR),
}


def muc_ho_tro_tu_van(qm: QuyMo, nu_lam_chu: bool | None) -> tuple[int, int, str]:
    """Điều 13 K2 → (phần trăm, trần VND, câu giải thích).

    ⚠️ 480 triệu ở kho_mau cũ là BỊA: trần CAO NHẤT của điều này là 200 triệu
    (DN vừa do phụ nữ làm chủ). Không có mức nào tới 480 triệu.
    """
    pt, tran, tran_uu = HO_TRO_TU_VAN[qm]
    dung_tran = tran_uu if nu_lam_chu else tran
    them = " (mức ưu tiên: do phụ nữ làm chủ / nhiều lao động nữ / DN xã hội)" if nu_lam_chu else ""
    return pt, dung_tran, f"Hỗ trợ tối đa {pt}% giá trị hợp đồng tư vấn, không quá {dung_tran/TR:.0f} triệu đồng/năm{them}"
