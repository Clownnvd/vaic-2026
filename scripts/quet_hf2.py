"""Quét lần 2 — license mở VÀ THẬT SỰ TẢI ĐƯỢC (không gated).

BÀI HỌC ĐÃ TRẢ GIÁ 2 LẦN:
  ViWikiFC   — license MIT trên card, README trả 401 → repo khoá
  ViLegalNLI — license apache-2.0 trên card, load_dataset báo "gated dataset,
               you must be authenticated" → vẫn phải xin (qua nút bấm thay vì email)

⇒ LICENSE MỞ ≠ TẢI ĐƯỢC. Phải kiểm CẢ HAI.
Cách kiểm chắc nhất: gọi API /parquet — endpoint này CHỈ trả dữ liệu khi repo
thật sự công khai. Đọc README có thể lỗi vì rate-limit, dễ báo nhầm.

Chạy: uv run --python 3.11 python scripts/quet_hf2.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

TU_KHOA = [
    "vietnamese legal", "vietnamese law", "luat viet nam", "vbpl",
    "vietnamese nli", "vietnamese entailment", "vietnamese fact check",
    "vietnamese claim verification", "vietnamese legal qa", "legal retrieval vietnamese",
]

MO = {"mit", "apache-2.0", "cc-by-4.0", "cc-by-sa-4.0", "cc0-1.0", "odc-by", "bsd-3-clause"}


def api(path: str, params: dict | None = None, timeout: int = 25):
    url = f"https://huggingface.co/api/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "policyradar/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def that_su_tai_duoc(ten: str) -> tuple[bool, str]:
    """/parquet chỉ trả dữ liệu khi repo CÔNG KHAI. Gated → 401/403."""
    try:
        d = api(f"datasets/{ten}/parquet", timeout=15)
        return True, f"config: {list(d.keys())[:3] if isinstance(d, dict) else '?'}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}" + (" — GATED/khoá" if e.code in (401, 403) else "")
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


thay: dict[str, dict] = {}
for tk in TU_KHOA:
    try:
        for d in api("datasets", {"search": tk, "limit": 50, "full": "true"}):
            thay[d["id"]] = d
    except Exception:  # noqa: BLE001
        pass

ung_vien = []
for ten, d in thay.items():
    cd = d.get("cardData") or {}
    lic = cd.get("license")
    if isinstance(lic, list):
        lic = lic[0] if lic else None
    lic = str(lic or "").lower()
    if lic in MO:
        ung_vien.append((d.get("downloads", 0) or 0, ten, lic, d.get("likes", 0) or 0))

ung_vien.sort(reverse=True)
print(f"Quét {len(thay)} dataset → {len(ung_vien)} có license mở\n")
print("=" * 80)
print("KIỂM TỪNG BỘ: license mở + THẬT SỰ tải được?")
print("=" * 80)
print(f"{'dataset':44} {'license':13} {'tải':>6} {'tải được?'}")
print("-" * 80)

ok_list = []
for dl, ten, lic, likes in ung_vien[:24]:
    ok, ghi = that_su_tai_duoc(ten)
    if ok:
        ok_list.append((ten, lic, dl))
    print(f"{ten[:44]:44} {lic:13} {dl:6,} {'✓' if ok else '✗ ' + ghi}")

print("\n" + "=" * 80)
print(f"⇒ {len(ok_list)} BỘ DÙNG NGAY ĐƯỢC (license mở + không gated)")
print("=" * 80)
for ten, lic, dl in ok_list:
    print(f"  ✓ {ten:48} {lic:14} {dl:,} tải/tháng")
