"""Client API vbpl.vn — LẤY TRẠNG THÁI HIỆU LỰC THẬT.

🎯 ĐÂY LÀ THỨ MỞ KHOÁ YÊU CẦU ② CỦA ĐỀ (theo dõi cập nhật chính sách).

Kho nhắc "join API vbpl.vn" 5 LẦN suốt nhiều ngày nhưng KHÔNG có endpoint nào,
và chỉ GIẢ ĐỊNH là có API. Chưa ai mở thử.
Manh mối nằm ngay trong dump: cột `api_url`. Gọi phát đầu → HTTP 200, PUBLIC,
không cần auth, và CÓ field effStatus.

    GET https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/{item_id}

    data.effStatus = {"name": "Hết hiệu lực toàn bộ", "code": "HHL"}
    data.isOld     = true
    data.references = [...]   ← quan hệ thay thế / bãi bỏ / sửa đổi

VÌ SAO QUAN TRỌNG: corpus KHÔNG có field hiệu lực. Không có API này thì matcher
đang trích văn bản CHẾT mà không biết → khuyên DN theo văn bản hết hiệu lực →
DN nộp sai. Đây là lỗi NẶNG NHẤT có thể mắc với sản phẩm chính sách.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API = "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc"
CACHE = Path("./data/cache_vbpl")

# mã hiệu lực vbpl.vn (đọc từ effStatus.code)
CON_HIEU_LUC = {"CHL"}  # Còn hiệu lực
HET_HIEU_LUC = {"HHL"}  # Hết hiệu lực toàn bộ


@dataclass(frozen=True)
class HieuLuc:
    item_id: str
    ma: str | None  # "HHL" | "CHL" | ...
    ten: str | None  # "Hết hiệu lực toàn bộ"
    is_old: bool
    co_quan: str | None
    so_quan_he: int
    loi: str | None = None

    @property
    def con_hieu_luc(self) -> bool | None:
        """True/False, hoặc None = KHÔNG BIẾT (đừng đoán)."""
        if self.loi or not self.ma:
            return None
        if self.ma in HET_HIEU_LUC:
            return False
        if self.ma in CON_HIEU_LUC:
            return True
        return None  # mã lạ → không kết luận

    @property
    def nhan(self) -> str:
        c = self.con_hieu_luc
        if c is True:
            return "Còn hiệu lực"
        if c is False:
            return self.ten or "Hết hiệu lực"
        return self.ten or "Chưa xác định được hiệu lực"


def _tai(item_id: str, timeout: int = 20) -> dict | None:
    req = urllib.request.Request(
        f"{API}/{item_id}",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def tra_hieu_luc(item_id: str, dung_cache: bool = True, chi_cache: bool = False) -> HieuLuc:
    """Tra trạng thái hiệu lực THẬT. Cache đĩa — API chậm, demo không chờ được.

    chi_cache=True: CHỈ đọc cache, KHÔNG gọi API. Dùng ở BFF/lúc /chat để không
    bao giờ bị API chậm làm đơ request. Cache miss → trả 'chưa xác định' (loi set),
    demo hâm cache trước bằng scripts/ham_cache_vbpl.py.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{item_id}.json"

    if dung_cache and f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            d = None
    else:
        d = None

    if d is None and chi_cache:
        return HieuLuc(item_id, None, None, False, None, 0, "chưa hâm cache")

    if d is None:
        try:
            d = _tai(item_id)
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        except urllib.error.HTTPError as e:
            return HieuLuc(item_id, None, None, False, None, 0, f"HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            return HieuLuc(item_id, None, None, False, None, 0, type(e).__name__)

    da = (d or {}).get("data") or {}
    es = da.get("effStatus") or {}
    return HieuLuc(
        item_id=item_id,
        ma=es.get("code"),
        ten=es.get("name"),
        is_old=bool(da.get("isOld")),
        co_quan=da.get("agencyName"),
        so_quan_he=len(da.get("references") or []),
    )


def quan_he(item_id: str) -> list[dict]:
    """Quan hệ văn bản: thay thế / bãi bỏ / sửa đổi.

    ⚠️ `referenceType` là INT, không phải dict — đã crash một lần vì đoán sai.
    Phải soi kiểu thật trước khi bóc.
    """
    f = CACHE / f"{item_id}.json"
    if not f.exists():
        tra_hieu_luc(item_id)
    if not f.exists():
        return []
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []

    ra = []
    for r in ((d.get("data") or {}).get("references") or []):
        td = r.get("targetDocument") or {}
        ra.append(
            {
                "loai": r.get("referenceType"),  # int — chưa biết bảng mã, KHÔNG đoán
                "so_vb": td.get("docNumber") or td.get("docName"),
                "title": td.get("title"),
                "item_id": td.get("id"),
                "is_root": r.get("isRootDocument"),
            }
        )
    return ra
