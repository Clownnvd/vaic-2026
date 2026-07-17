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
RE_CIT = re.compile(
    r"Khoản\s+(\d+)\s+Điều\s+(\d+)\s+(\S+?)\s+do\s+(.+?)\s+ban hành",
    re.I,
)


@dataclass
class CitationBoc:
    khoan: int
    dieu: int
    so_vb: str
    co_quan: str


def boc_citation(text: str) -> CitationBoc | None:
    m = RE_CIT.search(text)
    if not m:
        return None
    return CitationBoc(int(m.group(1)), int(m.group(2)), m.group(3), m.group(4).strip())
