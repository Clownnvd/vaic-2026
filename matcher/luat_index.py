"""Index tra cứu luật — nạp metadata corpus (KHÔNG nạp markdown nặng).

Cho sidebar "Danh sách luật": tìm kiếm + lọc tiêu chí + phân trang trên 2.669
văn bản. Nạp 1 lần lúc BFF khởi động, giữ trong RAM, lọc/phân trang tức thì.

Vì sao KHÔNG nạp `markdown`: mỗi văn bản markdown vài chục KB × 2669 = hàng
trăm MB. Danh sách chỉ cần metadata. Nội dung điều–khoản tra riêng khi bấm vào.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# cột nhẹ — KHÔNG lấy markdown/structure_json
COT = [
    "item_id", "doc_number_str", "title", "doc_type", "legal_area",
    "issuing_authority", "issue_date", "year", "summary", "source_url",
]
SPLITS = Path("./data/splits_dn")


def _bo_dau(s: str) -> str:
    """Bỏ dấu để tìm kiếm gõ-không-dấu khớp (H1 của đề: chịu gõ không dấu)."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d").replace("Đ", "D").lower()


@dataclass
class VanBan:
    item_id: str
    so_hieu: str
    tieu_de: str
    doc_type: str
    linh_vuc: str
    co_quan: str
    ngay_ban_hanh: str
    nam: int | None
    tom_tat: str
    nguon_url: str
    _tim: str = field(default="", repr=False)  # chuỗi tìm kiếm đã bỏ dấu


class LuatIndex:
    def __init__(self, thu_muc: Path = SPLITS):
        self.ds: list[VanBan] = []
        self._facets: dict | None = None
        self._nap(thu_muc)
        self._facets = self._tinh_facets()  # tính SẴN lúc nạp, khỏi tính lại mỗi request

    def _nap(self, thu_muc: Path) -> None:
        import pyarrow.parquet as pq

        for ten in ("train", "calib", "test"):
            f = thu_muc / f"{ten}.parquet"
            if not f.exists():
                continue
            tbl = pq.read_table(f, columns=COT)
            cols = {c: tbl[c].to_pylist() for c in COT}
            for i in range(tbl.num_rows):
                so = cols["doc_number_str"][i] or ""
                td = cols["title"][i] or ""
                vb = VanBan(
                    item_id=str(cols["item_id"][i]),
                    so_hieu=so,
                    tieu_de=td,
                    doc_type=cols["doc_type"][i] or "",
                    linh_vuc=cols["legal_area"][i] or "",
                    co_quan=cols["issuing_authority"][i] or "",
                    ngay_ban_hanh=str(cols["issue_date"][i] or "")[:10],
                    nam=cols["year"][i],
                    tom_tat=cols["summary"][i] or "",
                    nguon_url=cols["source_url"][i] or "",
                )
                vb._tim = _bo_dau(f"{so} {td} {vb.co_quan}")
                self.ds.append(vb)
        # sắp mới nhất lên đầu (năm giảm dần) — dễ theo dõi
        self.ds.sort(key=lambda v: (v.nam or 0), reverse=True)

    def url_theo_id(self, item_id: str | None) -> str | None:
        """source_url của văn bản theo item_id — để mọi citation bấm mở bài gốc."""
        if not item_id:
            return None
        if not hasattr(self, "_url_map"):
            self._url_map = {v.item_id: v.nguon_url for v in self.ds if v.nguon_url}
        return self._url_map.get(str(item_id))

    def facets(self) -> dict:
        """Giá trị lọc + số lượng — trả bản đã tính sẵn (không tính lại mỗi request)."""
        return self._facets if self._facets is not None else self._tinh_facets()

    def _tinh_facets(self) -> dict:
        def dem(lay):
            d: dict[str, int] = {}
            for v in self.ds:
                k = lay(v)
                if k:
                    d[k] = d.get(k, 0) + 1
            return sorted(({"gia_tri": k, "so_luong": n} for k, n in d.items()),
                          key=lambda x: -x["so_luong"])

        return {
            "doc_type": dem(lambda v: v.doc_type),
            "linh_vuc": dem(lambda v: v.linh_vuc),
            "co_quan": dem(lambda v: v.co_quan),
            "nam": sorted(
                ({"gia_tri": str(v), "so_luong": n} for v, n in _dem_nam(self.ds).items()),
                key=lambda x: -int(x["gia_tri"]),
            ),
        }

    def truy_van(
        self,
        q: str = "",
        doc_type: str = "",
        linh_vuc: str = "",
        co_quan: str = "",
        nam: str = "",
        trang: int = 1,
        cs: int = 20,
    ) -> dict:
        """Lọc + tìm + phân trang. Trả {tong, trang, so_trang, van_ban[]}."""
        kq = self.ds
        if q:
            qn = _bo_dau(q.strip())
            kq = [v for v in kq if qn in v._tim]
        if doc_type:
            kq = [v for v in kq if v.doc_type == doc_type]
        if linh_vuc:
            kq = [v for v in kq if v.linh_vuc == linh_vuc]
        if co_quan:
            kq = [v for v in kq if v.co_quan == co_quan]
        if nam:
            kq = [v for v in kq if str(v.nam) == str(nam)]

        tong = len(kq)
        cs = max(1, min(cs, 100))
        so_trang = max(1, (tong + cs - 1) // cs)
        trang = max(1, min(trang, so_trang))
        lat = kq[(trang - 1) * cs : trang * cs]
        return {
            "tong": tong,
            "trang": trang,
            "so_trang": so_trang,
            "cs": cs,
            "van_ban": [
                {
                    "item_id": v.item_id,
                    "so_hieu": v.so_hieu,
                    "tieu_de": v.tieu_de,
                    "doc_type": v.doc_type,
                    "linh_vuc": v.linh_vuc,
                    "co_quan": v.co_quan,
                    "ngay_ban_hanh": v.ngay_ban_hanh,
                    "nam": v.nam,
                    "tom_tat": v.tom_tat[:280],
                    "nguon_url": v.nguon_url,
                }
                for v in lat
            ],
        }


def _dem_nam(ds: list[VanBan]) -> dict[int, int]:
    d: dict[int, int] = {}
    for v in ds:
        if v.nam:
            d[v.nam] = d.get(v.nam, 0) + 1
    return d


@lru_cache(maxsize=1)
def get_index() -> LuatIndex:
    """Nạp 1 lần, tái dùng — lru_cache đảm bảo singleton."""
    return LuatIndex()
