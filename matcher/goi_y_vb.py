"""TỪ CHỐI CÓ TRÁCH NHIỆM — không tìm thấy văn bản thì chỉ đúng chỗ sai + gợi ý gần đúng.

Pattern lấy từ kho (BATTLE-NOTES 16/07, đã chạy thật ở bản tập dượt):
    "Không tìm thấy 'ngô hữu phong' (tô đỏ) — có phải ý bạn là 'Ngô Hữu Long' (KH303)?"
    difflib, ngưỡng ≥0.6, badge TỪ CHỐI CÓ TRÁCH NHIỆM.

Vì sao không từ chối suông: "văn bản này không có trong kho" thì ĐÚNG nhưng VÔ DỤNG —
người dùng không biết mình gõ sai chỗ nào, cũng không biết đi đâu tiếp.
Trợ lý thật thì chỉ đúng chỗ sai và đưa đường.

Trả về `span` để UI tô đỏ ĐÚNG đoạn sai, không tô đỏ cả câu.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

# số hiệu văn bản VN: 80/2021/NĐ-CP · 44/2025/TT-BKHCN · 67/2025/QH15 · hoặc rút gọn 67/2025
RE_SO_VB = re.compile(
    r"\b(\d{1,3}/20\d{2}(?:/(?:QH\d+|N[ĐD]-CP|TT-[A-ZĐ]{2,8}|Q[ĐD]-[A-ZĐ]{2,8}|NQ-[A-ZĐ]{2,8}))?)\b",
    re.IGNORECASE,
)


@dataclass
class GoiY:
    """Một chỗ sai tìm được trong câu."""

    raw: str  # nguyên văn đoạn sai — để tô đỏ
    bat_dau: int
    ket_thuc: int
    goi_y: list[tuple[str, str]]  # [(số hiệu gần đúng, tiêu đề)]

    @property
    def co_goi_y(self) -> bool:
        return bool(self.goi_y)


def _chuan_so(s: str) -> str:
    return s.upper().replace("ND-CP", "NĐ-CP").replace("QD-", "QĐ-")


def tim_gan_dung(
    so_hoi: str, kho_so: dict[str, str], n: int = 3, nguong: float = 0.75
) -> list[tuple[str, str]]:
    """Số hiệu gần đúng nhất trong kho. kho_so: {số hiệu → tiêu đề}.

    ⚠️ SO TRÊN PHẦN SỐ/NĂM, KHÔNG so cả chuỗi.
    Bug đã dính: '999/2099/NĐ-CP' được gợi ý thành '13/2019/NĐ-CP' vì difflib
    thấy chung hậu tố '/NĐ-CP' nên tưởng giống. Số hoàn toàn khác nhau!
    **Gợi ý bừa còn tệ hơn không gợi ý** — người dùng tin theo là hỏng.
    """
    khoa = list(kho_so.keys())
    s = _chuan_so(so_hoi)
    m = re.match(r"(\d{1,3}/20\d{2})", s)
    if not m:
        return []
    so_nam = m.group(1)

    # ── ưu tiên 1: TRÙNG KHÍT phần số/năm, chỉ khác hậu tố loại văn bản ──
    # ("Luật 67/2025" không có → nhưng kho có "67/2025/NĐ-CP" → gợi ý ngay)
    cung = [k for k in khoa if k.upper().startswith(so_nam)]
    if cung:
        return [(k, kho_so[k]) for k in cung[:n]]

    # ── ưu tiên 2: gõ nhầm vài ký tự trong phần SỐ/NĂM ──
    # So sánh CHỈ phần số/năm của từng khoá, bỏ hậu tố ra ngoài.
    ung_vien: list[tuple[float, str]] = []
    for k in khoa:
        mk = re.match(r"(\d{1,3}/20\d{2})", k.upper())
        if not mk:
            continue
        ti_le = difflib.SequenceMatcher(None, so_nam, mk.group(1)).ratio()
        if ti_le >= nguong:
            ung_vien.append((ti_le, k))

    ung_vien.sort(key=lambda x: -x[0])
    return [(k, kho_so[k]) for _, k in ung_vien[:n]]


def soi_cau(cau: str, kho_so: dict[str, str]) -> list[GoiY]:
    """Quét câu hỏi, tìm số hiệu văn bản KHÔNG có trong kho + gợi ý gần đúng.

    Chỉ trả những số KHÔNG tra được — số đúng thì im lặng cho qua.
    """
    ra: list[GoiY] = []
    co = {_chuan_so(k) for k in kho_so}

    for m in RE_SO_VB.finditer(cau):
        so = _chuan_so(m.group(1))
        if so in co:
            continue  # có thật → không nói gì
        ra.append(
            GoiY(
                raw=m.group(1),
                bat_dau=m.start(1),
                ket_thuc=m.end(1),
                goi_y=tim_gan_dung(m.group(1), kho_so),
            )
        )
    return ra


def cau_tra_loi(g: GoiY) -> str:
    """Câu nói với người dùng — chỉ đích danh, có gợi ý thì đưa."""
    if not g.co_goi_y:
        return (
            f"Không tìm thấy văn bản số **{g.raw}** trong kho mình đang tra, "
            f"và cũng không có số hiệu nào gần giống. Mình không đoán."
        )
    ds = "\n".join(f"  • **{so}** — {ten[:70]}" for so, ten in g.goi_y)
    return (
        f"Không tìm thấy **{g.raw}** trong kho. Có phải ý bạn là:\n{ds}\n\n"
        f"Nếu đúng thật là {g.raw} thì văn bản đó chưa được nạp vào kho — "
        f"mình không trích được, không đoán."
    )
