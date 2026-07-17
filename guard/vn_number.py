"""Chuẩn hoá + bóc số tiếng Việt — lõi của lớp guard TẤT ĐỊNH.

Dùng ở HAI chỗ, và phải là CÙNG một hàm:
  1. Lúc sinh hard-negative (đòn #4) — bịa số.
  2. Lúc chặn thật (runtime)        — đối chiếu số AI nói vs số trong nguồn.
Nếu hai chỗ dùng hai cách hiểu số khác nhau thì guard sẽ bắt hụt.

Quy ước số Việt Nam (KHÁC Anh/Mỹ — đây là chỗ dễ sai nhất):
    "1.234.567"  → dấu chấm  = ngăn nghìn   → 1234567
    "2,5"        → dấu phẩy  = thập phân    → 2.5
    "1.234,56"   → cả hai                   → 1234.56
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# bậc đơn vị — thứ tự quan trọng: khớp cụm dài trước ("nghìn tỷ" trước "tỷ")
DON_VI: list[tuple[str, float]] = [
    ("nghìn tỷ", 1e12),
    ("ngàn tỷ", 1e12),
    ("tỷ", 1e9),
    ("tỉ", 1e9),
    ("triệu", 1e6),
    ("nghìn", 1e3),
    ("ngàn", 1e3),
    ("k", 1e3),
]

_SO = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?|\d+(?:\.\d+)?"


def normalize_vn_number(s: str) -> float | None:
    """'1.234,56' → 1234.56 · '2,5' → 2.5 · '20' → 20.0. Không parse được → None.

    Chỉ xử lý phần SỐ, không xử lý đơn vị (xem parse_gia_tri).
    """
    if not s:
        return None
    s = s.strip().replace(" ", "")
    if not re.fullmatch(r"[\d.,]+", s):
        return None

    co_cham = "." in s
    co_phay = "," in s

    if co_cham and co_phay:
        # kiểu VN đầy đủ: chấm ngăn nghìn, phẩy thập phân
        s = s.replace(".", "").replace(",", ".")
    elif co_phay:
        # chỉ có phẩy → thập phân VN
        s = s.replace(",", ".")
    elif co_cham:
        # Chỉ có chấm — nhập nhằng thật sự: "1.234" là 1234 (VN) hay 1.234 (Anh)?
        # Luật: nhóm đúng 3 chữ số sau MỌI dấu chấm ⇒ ngăn nghìn.
        # "1.234" → 1234 · "1.234.567" → 1234567 · "2.5" → 2.5 · "1.23" → 1.23
        phan = s.split(".")
        if len(phan) > 1 and all(len(p) == 3 for p in phan[1:]) and phan[0].isdigit():
            s = s.replace(".", "")
        # còn lại giữ nguyên → float hiểu như thập phân
    try:
        return float(s)
    except ValueError:
        return None


def parse_gia_tri(text: str) -> float | None:
    """'20 tỷ' → 2e10 · '1,5 triệu' → 1_500_000 · '50%' → 50.0 (giá trị %, không chia).

    Trả None nếu không thấy số.
    """
    t = text.strip().lower()
    m = re.search(rf"({_SO})", t)
    if not m:
        return None
    so = normalize_vn_number(m.group(1))
    if so is None:
        return None

    duoi = t[m.end() :].strip()
    for ten, he in DON_VI:
        if duoi.startswith(ten):
            return so * he
    return so


@dataclass(frozen=True)
class SoTimThay:
    """Một con số bóc được từ văn bản, kèm vị trí để tô đỏ trên UI."""

    raw: str
    gia_tri: float
    loai: str  # "phan_tram" | "tien" | "ngay" | "tho"
    bat_dau: int
    ket_thuc: int


_RE_PHAN_TRAM = re.compile(rf"({_SO})\s*%")
_RE_TIEN = re.compile(
    rf"({_SO})\s*(nghìn tỷ|ngàn tỷ|tỷ|tỉ|triệu|nghìn|ngàn)\s*(?:đồng|đ|vnđ|vnd)?",
    re.IGNORECASE,
)
_RE_NGAY = re.compile(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b")
_RE_THO = re.compile(rf"\b({_SO})\b")


def bóc_số(text: str) -> list[SoTimThay]:
    """Bóc mọi con số đáng kiểm trong 1 câu, kèm span.

    Ưu tiên loại cụ thể trước (phần trăm > tiền > ngày > thô) và KHÔNG cho
    chồng lấn — tránh '50%' vừa bị tính là phần trăm vừa là số thô.
    """
    ra: list[SoTimThay] = []
    da_chiem: list[tuple[int, int]] = []

    def cham(a: int, b: int) -> bool:
        return any(a < y and x < b for x, y in da_chiem)

    for re_, loai in (
        (_RE_PHAN_TRAM, "phan_tram"),
        (_RE_TIEN, "tien"),
        (_RE_NGAY, "ngay"),
    ):
        for m in re_.finditer(text):
            if cham(m.start(), m.end()):
                continue
            if loai == "ngay":
                gt = float(f"{m.group(2)}{m.group(1).zfill(2)}")
            else:
                gt = parse_gia_tri(m.group(0))
                if gt is None:
                    continue
            ra.append(SoTimThay(m.group(0), gt, loai, m.start(), m.end()))
            da_chiem.append((m.start(), m.end()))

    for m in _RE_THO.finditer(text):
        if cham(m.start(), m.end()):
            continue
        gt = normalize_vn_number(m.group(1))
        if gt is None:
            continue
        ra.append(SoTimThay(m.group(1), gt, "tho", m.start(), m.end()))
        da_chiem.append((m.start(), m.end()))

    return sorted(ra, key=lambda x: x.bat_dau)


def lech_so(claim: str, nguon: str, dung_sai: float = 1e-6) -> list[SoTimThay]:
    """Số nào trong `claim` KHÔNG tìm thấy trong `nguon` → nghi bịa, trả về để tô đỏ.

    Đây là guard tất định: LLM không thể cãi, vì so số với số.
    Bỏ qua loại 'tho' (số thứ tự điều/khoản… do lớp existence-lookup lo).
    """
    so_nguon = {round(s.gia_tri, 6) for s in bóc_số(nguon)}
    ra = []
    for s in bóc_số(claim):
        if s.loai == "tho":
            continue
        if not any(abs(s.gia_tri - g) <= dung_sai for g in so_nguon):
            ra.append(s)
    return ra
