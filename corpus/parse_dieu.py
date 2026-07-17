"""Parse markdown phẳng → cây Điều → Khoản → Điểm.

VÌ SAO PHẢI TỰ VIẾT: `structure_json` của dump chỉ có sections/paragraphs/sentences
(parse tổng quát, 1 doc = 1 section "header"). KHÔNG có cấu trúc pháp lý.
Nhưng markdown CÓ đầy đủ "Điều N" (499/500 văn bản, 13.668 lần) — chỉ là bị làm
phẳng, không xuống dòng.

CHỖ KHÓ NHẤT — phân biệt 2 loại "Điều N":
  • TIÊU ĐỀ  : "… QUYẾT ĐỊNH: Điều 1. Bãi bỏ Quyết định số 16/2013…"
  • TRÍCH DẪN: "… quy định tại Điều 5 của Luật Hải quan…"
Bắt nhầm trích dẫn thành tiêu đề → cắt vụn văn bản → citation trỏ sai chỗ.

Cách trị: tiêu đề Điều trong một văn bản luôn ĐÁNH SỐ TĂNG DẦN TỪ 1.
→ Lấy tất cả "Điều N", rồi tìm dãy con tăng dần 1,2,3… — đó mới là tiêu đề.
Cách này chắc hơn đoán bằng từ đứng trước ("tại/theo/của").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# "Điều 1." / "Điều 1 ." / "Điều 12" — số điều luôn ngay sau chữ Điều
RE_DIEU = re.compile(r"Điều\s+(\d{1,3})\s*\.?")
# khoản = "1." "2." đứng sau khoảng trắng, KHÔNG phải số trong "38/2015" hay "ngày 20"
RE_KHOAN = re.compile(r'(?:^|\s)(\d{1,2})\s*\.\s+(?=[A-ZĐÀ-Ỹ«"“]|[a-zà-ỹ])')
# điểm = "a)" "b)"
RE_DIEM = re.compile(r"(?:^|\s)([a-zđ])\s*\)\s+")

TU_TRICH_DAN = re.compile(
    r"(tại|theo|của|quy định ở|nêu tại|khoản \d+|điểm [a-z]\)?\s*)\s*$", re.I
)


@dataclass
class Diem:
    ky_hieu: str  # "a"
    text: str


@dataclass
class Khoan:
    so: int
    text: str
    diem: list[Diem] = field(default_factory=list)


@dataclass
class Dieu:
    so: int
    tieu_de: str
    text: str
    khoan: list[Khoan] = field(default_factory=list)
    char_start: int = 0


def _la_tieu_de(md: str, m: re.Match) -> bool:
    """'Điều N' này là tiêu đề hay chỉ là trích dẫn trong câu?"""
    truoc = md[max(0, m.start() - 26) : m.start()]
    return not TU_TRICH_DAN.search(truoc)


def tim_tieu_de_dieu(md: str) -> list[re.Match]:
    """Lấy các match 'Điều N' là TIÊU ĐỀ: lọc trích dẫn + giữ dãy tăng dần từ 1."""
    ung_vien = [m for m in RE_DIEU.finditer(md) if _la_tieu_de(md, m)]
    if not ung_vien:
        return []

    # dãy con tăng dần bắt đầu từ 1 (tham lam theo thứ tự xuất hiện)
    ra: list[re.Match] = []
    mong_doi = 1
    for m in ung_vien:
        if int(m.group(1)) == mong_doi:
            ra.append(m)
            mong_doi += 1
    return ra


def tach_khoan(than: str) -> list[Khoan]:
    """Cắt thân Điều thành các khoản '1.' '2.' — cũng phải tăng dần."""
    ung = list(RE_KHOAN.finditer(than))
    hop_le: list[re.Match] = []
    mong = 1
    for m in ung:
        if int(m.group(1)) == mong:
            hop_le.append(m)
            mong += 1
    if not hop_le:
        return []

    ra: list[Khoan] = []
    for i, m in enumerate(hop_le):
        a = m.end()
        b = hop_le[i + 1].start() if i + 1 < len(hop_le) else len(than)
        t = than[a:b].strip()
        if not t:
            continue
        k = Khoan(so=int(m.group(1)), text=t)
        # điểm a) b) trong khoản
        diem = list(RE_DIEM.finditer(t))
        hop_diem: list[re.Match] = []
        cho = "a"
        for dm in diem:
            if dm.group(1) == cho:
                hop_diem.append(dm)
                cho = chr(ord(cho) + 1)
        for j, dm in enumerate(hop_diem):
            x = dm.end()
            y = hop_diem[j + 1].start() if j + 1 < len(hop_diem) else len(t)
            k.diem.append(Diem(ky_hieu=dm.group(1), text=t[x:y].strip()))
        ra.append(k)
    return ra


def parse(md: str) -> list[Dieu]:
    """markdown phẳng → list[Dieu]."""
    if not md:
        return []
    heads = tim_tieu_de_dieu(md)
    ra: list[Dieu] = []
    for i, m in enumerate(heads):
        a = m.end()
        b = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        than = md[a:b].strip()
        if not than:
            continue
        # tiêu đề = cụm tới dấu chấm đầu tiên (thường "Phạm vi điều chỉnh")
        cham = than.find(".")
        tieu_de = than[:cham].strip() if 0 < cham < 160 else ""
        ra.append(
            Dieu(
                so=int(m.group(1)),
                tieu_de=tieu_de,
                text=than,
                khoan=tach_khoan(than),
                char_start=m.start(),
            )
        )
    return ra


def don_vi_trich_dan(md: str) -> list[tuple[str, str]]:
    """Trả list (nhãn_citation, text) — đơn vị nhỏ nhất để làm premise cho NLI.

    Ưu tiên KHOẢN (đơn vị tự nhiên của luật VN). Điều không có khoản → lấy cả Điều.
    """
    ra: list[tuple[str, str]] = []
    for d in parse(md):
        if d.khoan:
            for k in d.khoan:
                ra.append((f"Điều {d.so} Khoản {k.so}", k.text))
        elif len(d.text) > 40:
            ra.append((f"Điều {d.so}", d.text))
    return ra
