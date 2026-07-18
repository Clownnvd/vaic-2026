"""API vbpl.vn CÓ THẬT KHÔNG — chưa ai mở thử.

Kho nhắc "join API vbpl.vn" 5 LẦN nhưng KHÔNG có endpoint nào, và chỉ GIẢ ĐỊNH
là có API công khai. Chưa ai verify.

Manh mối: lúc probe schema thấy corpus có sẵn cột `api_url`:
    https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/10
→ THỬ GỌI THẬT xem trả gì, có field hiệu lực không.

Đây là thứ quyết định yêu cầu ② của đề (theo dõi cập nhật chính sách).

Chạy: uv run --python 3.11 --with pyarrow python scripts/thu_api_vbpl.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq


def goi(url: str, nhan: str) -> dict | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read()
            print(f"  ✓ {nhan}: HTTP {r.status}, {len(b)} bytes")
            try:
                return json.loads(b)
            except Exception:  # noqa: BLE001
                print(f"    (không phải JSON: {b[:110]!r})")
                return None
    except urllib.error.HTTPError as e:
        print(f"  ✗ {nhan}: HTTP {e.code}")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ {nhan}: {type(e).__name__}: {str(e)[:70]}")
    return None


def tim_hieu_luc(d, duong="") -> list[str]:
    """Lùng field nào nói về hiệu lực trong response."""
    ra = []
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{duong}.{k}" if duong else k
            if any(
                t in k.lower()
                for t in ("hieu", "luc", "status", "state", "effect", "valid", "expire", "replac", "tinhtrang")
            ):
                ra.append(f"{p} = {str(v)[:70]}")
            ra += tim_hieu_luc(v, p)
    elif isinstance(d, list) and d:
        ra += tim_hieu_luc(d[0], f"{duong}[0]")
    return ra


def main() -> None:
    # lấy api_url thật từ corpus
    tbl = pq.read_table(
        Path("./data/splits_dn/test.parquet"), columns=["item_id", "doc_number_str", "source_url"]
    )
    ids = tbl["item_id"].to_pylist()[:3]
    dns = tbl["doc_number_str"].to_pylist()[:3]
    print(f"Thử với văn bản thật trong corpus: {list(zip(ids, dns))}\n")

    print("=" * 70)
    print("1. API GATEWAY (lấy từ cột api_url của dump)")
    print("=" * 70)
    d = None
    for i in ids[:2]:
        d = goi(f"https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/{i}", f"doc/{i}")
        if d:
            break

    if d:
        print("\n  --- khoá trong response ---")
        print(f"  {list(d.keys())[:18] if isinstance(d, dict) else type(d)}")
        hl = tim_hieu_luc(d)
        print(f"\n  --- FIELD HIỆU LỰC ---")
        if hl:
            for x in hl[:12]:
                print(f"    ✓ {x}")
        else:
            print("    ✗ KHÔNG thấy field nào về hiệu lực")

    print("\n" + "=" * 70)
    print("2. CÁC ĐƯỜNG KHÁC")
    print("=" * 70)
    for url, nhan in [
        ("https://vbpl.vn/TW/Pages/vbpq-timkiem.aspx", "vbpl.vn trang tìm kiếm"),
        ("https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/10", "gateway doc/10 (mẫu trong dump)"),
        ("https://vbpl.vn/api/", "vbpl.vn /api/"),
    ]:
        goi(url, nhan)

    print("\n" + "=" * 70)
    print("KẾT LUẬN")
    print("=" * 70)
    print("  Nếu gateway trả JSON có field hiệu lực → yêu cầu ② của đề LÀM ĐƯỢC THẬT,")
    print("  badge 'chưa đối chiếu' gỡ được, và monitoring có nguồn thật.")
    print("  Nếu không → phải nói thẳng với giám khảo, và tìm đường khác")
    print("  (vd: đào chính corpus tìm quan hệ 'thay thế/bãi bỏ' giữa các văn bản).")


if __name__ == "__main__":
    main()
