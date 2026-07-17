"""TẦNG PHÒNG NGỪA — structure-then-fill. LLM không được gõ số.

Đảo ngược cách nghĩ:
  ❌ cũ : LLM viết "hỗ trợ 50%" → guard đi kiểm xem 50% có đúng không
  ✅ mới: LLM viết "hỗ trợ {{s3}}" → CODE chép verbatim "50%" từ nguồn vào

Khác biệt: cách cũ là BẮT SAU KHI BỊA. Cách mới thì KHÔNG CÓ GÌ ĐỂ BẮT —
số trong đầu ra **về mặt cơ học** là bản sao từ nguồn.

Câu chốt demo: "số không phải kiểm tra sau — mà là KHÔNG THỂ sai từ lúc sinh."

Cưỡng chế 2 chiều:
  1. LLM tự gõ số vào khung  → BẮT (nó phải dùng slot, không được gõ tay)
  2. LLM gọi slot không tồn tại → BẮT (không bịa được nguồn)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, ".")
from guard.vn_number import bóc_số  # noqa: E402

RE_SLOT = re.compile(r"\{\{\s*(s\d+)\s*\}\}")
RE_CIT_SLOT = re.compile(r"\{\{\s*(cit)\s*\}\}")


@dataclass
class Slot:
    id: str
    raw: str  # chuỗi NGUYÊN VĂN trong nguồn — đây là thứ được chép ra
    loai: str
    gia_tri: float
    ngu_canh: str  # ~40 ký tự quanh số, để LLM biết slot này nói về cái gì


@dataclass
class KetQuaDung:
    ok: bool
    text: str | None = None
    vi_pham: list[str] = field(default_factory=list)


def trich_slot(nguon: str, gioi_han: int = 24) -> dict[str, Slot]:
    """Nguồn → bảng slot. Đây là TOÀN BỘ số mà LLM được phép dùng."""
    ra: dict[str, Slot] = {}
    for i, s in enumerate(bóc_số(nguon)[:gioi_han], 1):
        a = max(0, s.bat_dau - 42)
        b = min(len(nguon), s.ket_thuc + 42)
        ra[f"s{i}"] = Slot(
            id=f"s{i}",
            raw=s.raw,
            loai=s.loai,
            gia_tri=s.gia_tri,
            ngu_canh=nguon[a:b].replace("\n", " ").strip(),
        )
    return ra


def mo_ta_slot(slots: dict[str, Slot]) -> str:
    """Bảng slot đưa vào prompt cho LLM chọn."""
    if not slots:
        return "(nguồn không có số nào — không được nêu bất kỳ con số nào)"
    return "\n".join(
        f"  {{{{{s.id}}}}} = {s.raw!r} ({s.loai}) — …{s.ngu_canh}…" for s in slots.values()
    )


def dung_khung(khung: str, slots: dict[str, Slot], cit: str | None = None) -> KetQuaDung:
    """Điền khung của LLM bằng slot. Từ chối nếu LLM tự gõ số hoặc gọi slot ma.

    Trả (ok, text, vi_pham). ok=False ⇒ KHÔNG hiển thị, bắt LLM viết lại.
    """
    vi_pham: list[str] = []

    # ── 1. gọi slot không tồn tại = bịa nguồn ──────────────
    dung = RE_SLOT.findall(khung)
    ma = [d for d in dung if d not in slots]
    if ma:
        vi_pham.append(f"gọi slot không có trong nguồn: {', '.join(sorted(set(ma)))}")

    # ── 2. LLM tự gõ số vào khung = phạm luật ──────────────
    # Xoá slot đi rồi mới soi — kẻo bắt nhầm "s3" hay số bên trong slot.
    con_lai = RE_SLOT.sub(" ", khung)
    con_lai = RE_CIT_SLOT.sub(" ", con_lai)
    tu_go = [s for s in bóc_số(con_lai) if s.loai in ("phan_tram", "tien", "ngay")]
    if tu_go:
        ds = ", ".join(f"{s.raw!r}" for s in tu_go)
        vi_pham.append(f"tự gõ số thay vì dùng slot: {ds}")

    if vi_pham:
        return KetQuaDung(False, None, vi_pham)

    # ── 3. điền: chép VERBATIM từ nguồn ────────────────────
    out = RE_SLOT.sub(lambda m: slots[m.group(1)].raw, khung)
    if cit:
        out = RE_CIT_SLOT.sub(cit, out)

    return KetQuaDung(True, out, [])


# ── prompt block để nhét vào system prompt ────────────────────────
HUONG_DAN = """\
QUY TẮC SỐ — BẮT BUỘC:
Bạn KHÔNG được tự gõ bất kỳ con số nào (mức %, số tiền, ngày tháng) vào câu trả lời.
Mọi con số phải dùng slot lấy từ nguồn, dạng {{sN}}.

Slot có sẵn từ nguồn:
{bang_slot}

Ví dụ ĐÚNG : "Doanh nghiệp được hỗ trợ {{s2}} chi phí tư vấn, nộp trước {{s5}}."
Ví dụ SAI  : "Doanh nghiệp được hỗ trợ 50% chi phí tư vấn."   ← tự gõ số, sẽ bị chặn

Nếu nguồn không có con số bạn cần, ĐỪNG bịa — hãy nói thẳng là chưa đủ căn cứ.\
"""


def prompt_cho(nguon: str) -> tuple[str, dict[str, Slot]]:
    slots = trich_slot(nguon)
    return HUONG_DAN.format(bang_slot=mo_ta_slot(slots)), slots
