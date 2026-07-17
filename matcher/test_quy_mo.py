"""Test quy mô DNNVV — nhắm đúng chỗ bản cũ BỊA.

Mỗi ca dưới đây bản cũ ("nhan_su ≤ 200 VÀ von ≤ 100 tỷ") trả lời SAI.

Chạy: uv run --python 3.11 python matcher/test_quy_mo.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from matcher.quy_mo import QuyMo, muc_ho_tro_tu_van, xac_dinh_quy_mo  # noqa: E402
from matcher.schema import Profile  # noqa: E402

TY = 1_000_000_000
TR = 1_000_000
loi = 0


def kt(ten: str, thuc, mong) -> None:
    global loi
    ok = thuc == mong
    loi += 0 if ok else 1
    print(f"  {'✓' if ok else '✗'} {ten}")
    if not ok:
        print(f"      mong {mong!r}  ·  thực {thuc!r}")


print("── Điều 5: ngưỡng lao động ĐỔI THEO LĨNH VỰC ──")
print("   (bản cũ phẳng hoá thành '≤200' → sai với thương mại-dịch vụ)")

# 150 lao động, TM-DV: ngưỡng DN vừa của TM-DV là 100 → VƯỢT → không phải DNNVV
kt(
    "150 LĐ, thương mại-dịch vụ → NGOÀI (ngưỡng TM-DV là 100)",
    xac_dinh_quy_mo(
        Profile(linh_vuc="thuong_mai_dich_vu", lao_dong_bhxh=150, doanh_thu=50 * TY)
    ).quy_mo,
    QuyMo.NGOAI,
)
# 150 lao động, CN-XD: ngưỡng DN vừa là 200 → vẫn là DN vừa
kt(
    "150 LĐ, công nghiệp-xây dựng → VỪA (ngưỡng CN-XD là 200)",
    xac_dinh_quy_mo(
        Profile(linh_vuc="nong_lam_thuy_san__cong_nghiep_xay_dung", lao_dong_bhxh=150, doanh_thu=50 * TY)
    ).quy_mo,
    QuyMo.VUA,
)

print("\n── Điều 5: doanh thu HOẶC vốn (bản cũ biến thành VÀ) ──")
# vốn 300 tỷ (vượt), nhưng doanh thu 10 tỷ (đạt) → HOẶC ⇒ vẫn là DN nhỏ
kt(
    "vốn 300 tỷ VƯỢT nhưng doanh thu 10 tỷ ĐẠT → vẫn NHỎ (vì luật ghi HOẶC)",
    xac_dinh_quy_mo(
        Profile(
            linh_vuc="nong_lam_thuy_san__cong_nghiep_xay_dung",
            lao_dong_bhxh=60,
            doanh_thu=10 * TY,
            von=300 * TY,
        )
    ).quy_mo,
    QuyMo.NHO,
)

print("\n── Bậc thang: siêu nhỏ trước, không nhảy thẳng vào 'vừa' ──")
kt(
    "5 LĐ, doanh thu 1 tỷ → SIÊU NHỎ (không phải 'nhỏ' hay 'vừa')",
    xac_dinh_quy_mo(
        Profile(linh_vuc="nong_lam_thuy_san__cong_nghiep_xay_dung", lao_dong_bhxh=5, doanh_thu=1 * TY)
    ).quy_mo,
    QuyMo.SIEU_NHO,
)

print("\n── Thiếu tin → KHÔNG kết luận ──")
kq = xac_dinh_quy_mo(Profile(linh_vuc="thuong_mai_dich_vu"))
kt("thiếu lao động + doanh thu → quy_mo None", kq.quy_mo, None)
kt("  và nêu đích danh field thiếu", "lao_dong_bhxh" in kq.thieu_field, True)

print("\n── Điều 13 K2: mức hỗ trợ thật (bản cũ ghi 480 triệu) ──")
kt("siêu nhỏ → 100%, trần 50tr", muc_ho_tro_tu_van(QuyMo.SIEU_NHO, False)[:2], (100, 50 * TR))
kt("nhỏ → 50%, trần 100tr", muc_ho_tro_tu_van(QuyMo.NHO, False)[:2], (50, 100 * TR))
kt("vừa → 30%, trần 150tr", muc_ho_tro_tu_van(QuyMo.VUA, False)[:2], (30, 150 * TR))
kt("vừa + nữ làm chủ → trần 200tr", muc_ho_tro_tu_van(QuyMo.VUA, True)[1], 200 * TR)
kt(
    "KHÔNG có mức nào tới 480 triệu",
    max(muc_ho_tro_tu_van(q, True)[1] for q in (QuyMo.SIEU_NHO, QuyMo.NHO, QuyMo.VUA)),
    200 * TR,
)

print(f"\n{'✓ TẤT CẢ QUA' if not loi else f'✗ {loi} LỖI'}")
sys.exit(1 if loi else 0)
