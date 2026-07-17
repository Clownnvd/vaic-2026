"""Lớp guard TẤT ĐỊNH — tra ngược corpus. Không đoán, chỉ tra.

⚠️ KHOÁ PHẢI LÀ (doc_number, issuing_authority) — KHÔNG được chỉ doc_number.
   31 tỉnh cùng ban hành "14/2025/QĐ-UBND". Tra bằng số không thì khớp 31 văn
   bản khác nhau → không kết luận được "có thật hay bịa".

Đây là thứ model KHÔNG làm được: model char n-gram bắt "50%→80%" chỉ đạt 0.04;
tra tất định đạt 1.00 và không cãi được.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, ".")
from corpus.parse_dieu import parse  # noqa: E402


def chuan(s: str | None) -> str:
    """Chuẩn hoá để so khớp: bỏ dấu, thường hoá, gộp khoảng trắng."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class KetQuaTra:
    ton_tai: bool
    ly_do: str
    doc_id: str | None = None
    title: str | None = None
    co_quan_that: str | None = None
    text_khoan: str | None = None
    so_dieu_co: list[int] | None = None


class IndexCorpus:
    """Index tra ngược: (số văn bản, cơ quan) → văn bản."""

    def __init__(self, parquet: Path):
        import pyarrow.parquet as pq

        t = pq.read_table(
            parquet,
            columns=["item_id", "doc_number_str", "issuing_authority", "title", "markdown"],
        )
        self._md: dict[str, str] = {}
        self._theo_so: dict[str, list[dict]] = {}

        for i in range(t.num_rows):
            so = t["doc_number_str"][i].as_py()
            if not so:
                continue
            r = {
                "item_id": t["item_id"][i].as_py(),
                "so": so,
                "co_quan": t["issuing_authority"][i].as_py() or "",
                "title": t["title"][i].as_py() or "",
            }
            self._md[r["item_id"]] = t["markdown"][i].as_py() or ""
            for s in re.split(r"[,;]\s*", so):
                s = chuan(s)
                if s:
                    self._theo_so.setdefault(s, []).append(r)

        self._cache_dieu: dict[str, list] = {}

    def __len__(self) -> int:
        return len(self._md)

    @property
    def so_khoa(self) -> int:
        return len(self._theo_so)

    def tra_doc(self, so_vb: str, co_quan: str | None = None) -> KetQuaTra:
        """Số văn bản này có thật không — và có đúng do cơ quan đó ban hành không?"""
        ds = self._theo_so.get(chuan(so_vb), [])
        if not ds:
            return KetQuaTra(False, f"Không có văn bản số '{so_vb}' trong kho")

        if co_quan is None:
            if len(ds) > 1:
                return KetQuaTra(
                    True,
                    f"Số '{so_vb}' khớp {len(ds)} văn bản của {len(ds)} cơ quan khác nhau "
                    "— thiếu cơ quan thì không xác định được văn bản nào",
                    doc_id=ds[0]["item_id"],
                )
            return KetQuaTra(True, "Khớp", doc_id=ds[0]["item_id"], title=ds[0]["title"])

        cq = chuan(co_quan)
        for r in ds:
            if chuan(r["co_quan"]) == cq:
                return KetQuaTra(True, "Khớp", doc_id=r["item_id"], title=r["title"],
                                 co_quan_that=r["co_quan"])

        that = ds[0]["co_quan"]
        return KetQuaTra(
            False,
            f"Văn bản '{so_vb}' có thật nhưng do '{that}' ban hành, không phải '{co_quan}'",
            doc_id=ds[0]["item_id"],
            co_quan_that=that,
        )

    def _dieu_cua(self, item_id: str) -> list:
        if item_id not in self._cache_dieu:
            self._cache_dieu[item_id] = parse(self._md.get(item_id, ""))
        return self._cache_dieu[item_id]

    def tra_dieu_khoan(
        self, so_vb: str, co_quan: str | None, so_dieu: int, so_khoan: int | None = None
    ) -> KetQuaTra:
        """Điều/khoản này có tồn tại trong văn bản đó không?"""
        r = self.tra_doc(so_vb, co_quan)
        if not r.ton_tai or not r.doc_id:
            return r

        ds = self._dieu_cua(r.doc_id)
        co = [d.so for d in ds]
        d = next((x for x in ds if x.so == so_dieu), None)
        if d is None:
            return KetQuaTra(
                False,
                f"Văn bản '{so_vb}' không có Điều {so_dieu} "
                f"(chỉ có Điều {min(co)}–{max(co)})" if co else
                f"Văn bản '{so_vb}' không parse được điều nào",
                doc_id=r.doc_id,
                so_dieu_co=co,
            )

        if so_khoan is None:
            return KetQuaTra(True, "Khớp", doc_id=r.doc_id, text_khoan=d.text)

        k = next((x for x in d.khoan if x.so == so_khoan), None)
        if k is None:
            co_k = [x.so for x in d.khoan]
            return KetQuaTra(
                False,
                f"Điều {so_dieu} của '{so_vb}' không có Khoản {so_khoan}"
                + (f" (chỉ có Khoản {min(co_k)}–{max(co_k)})" if co_k else " (điều này không chia khoản)"),
                doc_id=r.doc_id,
            )
        return KetQuaTra(True, "Khớp", doc_id=r.doc_id, text_khoan=k.text)


# ── bóc citation ngược từ câu AI nói ─────────────────────────────
#
# ⚠️ BẢN CŨ CHỈ BẮT MỘT DẠNG và bỏ lọt 3 dạng thật (đo được ở dao_bia_that.py:
#    79/120 câu GPT-4o RÕ RÀNG có trích dẫn mà parser báo "không có citation"):
#      cũ: r"Khoản (\d+) Điều (\d+) (\S+?) do (.+?) ban hành"
#    Bỏ lọt:
#      1. "Nghị định 57/2018/NĐ-CP"  → `\S+?` không nuốt được tiền tố có dấu cách
#      2. "Điều 5 Khoản 3 80/2021/NĐ-CP" → ĐIỀU TRƯỚC KHOẢN. Chí mạng: chính
#         Citation.__str__ của mình xuất dạng này → guard không đọc nổi citation
#         của chính mình → chặn oan câu đúng trên production.
#      3. thiếu "do ... ban hành" → regex cũ BẮT BUỘC cụm này.
#
# Lối mới: TÌM SỐ VĂN BẢN TRƯỚC (mỏ neo chắc chắn: \d+/\d{4}/CHỮ), rồi soi
# Điều/Khoản quanh nó (cả 2 thứ tự), rồi soi "do ... ban hành" nếu có.

# số hiệu VB: 57/2018/NĐ-CP · 77/2018/NQ-HĐND · 01/2018/QĐ-UBND · 15/2023/QH15
RE_SO_VB = re.compile(r"\b(\d{1,4}/\d{4}/[A-ZĐ][A-ZĐ0-9-]*)", re.I)
RE_DIEU = re.compile(r"Điều\s+(\d+)", re.I)
RE_KHOAN = re.compile(r"Khoản\s+(\d+)", re.I)
RE_BAN_HANH = re.compile(r"\bdo\s+(.+?)\s+ban hành", re.I)


@dataclass
class CitationBoc:
    khoan: int | None
    dieu: int
    so_vb: str
    co_quan: str | None


def boc_citation(text: str) -> CitationBoc | None:
    """Bóc (điều, khoản, số VB, cơ quan) từ câu AI nói. None nếu không có số VB.

    Số VB là mỏ neo bắt buộc — không có nó thì không tra ngược corpus được.
    Điều bắt buộc; Khoản/cơ quan có thì lấy, không thì None (nhiều câu chỉ trích
    tới cấp Điều — vẫn tra được).
    """
    m_vb = RE_SO_VB.search(text)
    if not m_vb:
        return None
    so_vb = m_vb.group(1).upper()

    # Điều/Khoản: lấy match GẦN số VB nhất về phía TRƯỚC (câu VN đặt Điều/Khoản
    # trước số hiệu). Nếu trước không có thì mới nhìn cả câu.
    dau = text[: m_vb.start()]
    m_dieu = _cuoi_cung(RE_DIEU, dau) or _cuoi_cung(RE_DIEU, text)
    if not m_dieu:
        return None  # không có Điều → không định vị được
    m_khoan = _cuoi_cung(RE_KHOAN, dau) or _cuoi_cung(RE_KHOAN, text)

    m_bh = RE_BAN_HANH.search(text)
    co_quan = m_bh.group(1).strip() if m_bh else None

    return CitationBoc(
        khoan=int(m_khoan.group(1)) if m_khoan else None,
        dieu=int(m_dieu.group(1)),
        so_vb=so_vb,
        co_quan=co_quan,
    )


def _cuoi_cung(rx: re.Pattern, s: str) -> re.Match | None:
    """Match CUỐI CÙNG trong s — Điều/Khoản sát số VB nhất, tránh nuốt số lạ ở đầu câu."""
    m = None
    for m in rx.finditer(s):
        pass
    return m
