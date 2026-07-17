"""Đào sâu API vbpl.vn — nó cho những gì?

VỪA PHÁT HIỆN: API CÓ THẬT, PUBLIC, không cần auth, và CÓ field effStatus.
Kho nhắc "join API vbpl.vn" 5 lần mà chưa ai mở thử. Manh mối nằm ngay trong
dump: cột `api_url`.

Đây là thứ mở khoá YÊU CẦU ② của đề (theo dõi cập nhật chính sách) và gỡ được
badge "⚠ Hiệu lực chưa đối chiếu".

Chạy: uv run --python 3.11 --with pyarrow python scripts/dao_api_vbpl.py
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

API = "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc"


def goi(item_id: str) -> dict | None:
    try:
        req = urllib.request.Request(
            f"{API}/{item_id}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        print(f"  lỗi {item_id}: {type(e).__name__}")
        return None


def main() -> None:
    tbl = pq.read_table(
        Path("./data/splits_dn/test.parquet"),
        columns=["item_id", "doc_number_str", "title", "year"],
    )
    ids = tbl["item_id"].to_pylist()
    dns = tbl["doc_number_str"].to_pylist()
    titles = tbl["title"].to_pylist()
    years = tbl["year"].to_pylist()

    d = goi(ids[0])
    if not d:
        raise SystemExit("không gọi được")

    data = d.get("data", {})
    print("=" * 72)
    print("CẤU TRÚC data")
    print("=" * 72)
    for k, v in data.items():
        t = type(v).__name__
        s = json.dumps(v, ensure_ascii=False)[:78] if not isinstance(v, str) else v[:78]
        print(f"  {k:26} {t:6} {s}")

    print("\n" + "=" * 72)
    print("⭐ effStatus — TRẠNG THÁI HIỆU LỰC")
    print("=" * 72)
    print(f"  {json.dumps(data.get('effStatus'), ensure_ascii=False, indent=2)}")

    print("\n" + "=" * 72)
    print("⭐ references — QUAN HỆ VĂN BẢN (thay thế / bãi bỏ / sửa đổi)")
    print("=" * 72)
    refs = data.get("references") or []
    print(f"  {len(refs)} quan hệ")
    for r in refs[:5]:
        td = r.get("targetDocument") or {}
        print(f"    • [{(r.get('referenceType') or {}).get('name', '?')}] "
              f"{td.get('docNumber') or td.get('docName', '?')} — {(td.get('title') or '')[:44]}")

    # ── quét nhiều văn bản xem phân bố hiệu lực ──────────────
    print("\n" + "=" * 72)
    print("QUÉT 12 VĂN BẢN TRONG CORPUS — bao nhiêu cái ĐÃ CHẾT?")
    print("=" * 72)
    dem: dict[str, int] = {}
    ket = []
    for i in range(12):
        dd = goi(ids[i])
        if not dd:
            continue
        da = dd.get("data") or {}
        es = (da.get("effStatus") or {}).get("name") or "(không rõ)"
        dem[es] = dem.get(es, 0) + 1
        ket.append((dns[i], years[i], es, (titles[i] or "")[:40]))
        print(f"  {str(dns[i])[:20]:22} {years[i]}  {es[:30]:32} {(titles[i] or '')[:34]}")

    print(f"\n  --- phân bố ---")
    for k, v in sorted(dem.items(), key=lambda x: -x[1]):
        print(f"    {k[:44]:46} {v}")

    chet = [x for x in ket if "hết hiệu lực" in x[2].lower()]
    print(f"\n  ⚠ {len(chet)}/{len(ket)} văn bản trong corpus ĐÃ HẾT HIỆU LỰC")
    if chet:
        print("  → matcher đang trích văn bản CHẾT mà không biết. Đây là lỗi NẶNG:")
        print("    khuyên DN theo văn bản hết hiệu lực = DN nộp sai.")
        for x in chet[:4]:
            print(f"      • {x[0]} ({x[1]}) — {x[3]}")

    Path("./artifacts").mkdir(exist_ok=True)
    Path("./artifacts/api_vbpl_mau.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2)[:60000], encoding="utf-8"
    )
    print("\n  → artifacts/api_vbpl_mau.json (response mẫu đầy đủ)")


if __name__ == "__main__":
    main()
