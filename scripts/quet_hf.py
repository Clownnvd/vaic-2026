"""Quét HuggingFace API tìm dataset DÙNG NGAY ĐƯỢC — không phải xin.

Vì sao hỏi API thay vì google: API trả license tag, số lượt tải, ngày cập nhật,
danh sách file — số THẬT, không phải đọc paper rồi đoán. Và lọc được theo license.

Tiêu chí "dùng ngay được":
  1. license tag CÓ và là loại mở (mit/apache/cc-by/odc-by/cc0)  — không NC, không trống
  2. tải được (không gated/private) — kiểm bằng cách đọc thử README
  3. có file data thật

Chạy: uv run --python 3.11 python scripts/quet_hf.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

TU_KHOA = [
    "vietnamese legal", "vietnamese law", "legal vietnamese", "luat viet nam",
    "vietnamese nli", "vietnamese entailment", "vietnamese fact", "vietnamese claim",
    "vihallu", "vilegal", "alqac", "vlsp legal", "zalo legal",
    "vietnamese hallucination", "vietnamese verification", "vbpl",
]

# license MỞ — dùng được không cần xin
MO = {"mit", "apache-2.0", "cc-by-4.0", "cc-by-sa-4.0", "cc0-1.0", "odc-by", "bsd-3-clause"}
# license HẠN CHẾ — dùng được nhưng vướng
HAN_CHE = {"cc-by-nc-4.0", "cc-by-nc-sa-4.0", "cc-by-nc-nd-4.0", "gpl-3.0", "agpl-3.0"}


def api(path: str, params: dict | None = None):
    url = f"https://huggingface.co/api/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "policyradar/0.1"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def doc_duoc(ten: str) -> bool:
    """Đọc thử README — 401/403 = gated, không tải được (ca ViWikiFC)."""
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/datasets/{ten}/raw/main/README.md",
            headers={"User-Agent": "policyradar/0.1"},
        )
        urllib.request.urlopen(req, timeout=12).read(64)
        return True
    except urllib.error.HTTPError:
        return False
    except Exception:  # noqa: BLE001
        return True  # lỗi mạng → không kết luận


thay: dict[str, dict] = {}
for tk in TU_KHOA:
    try:
        for d in api("datasets", {"search": tk, "limit": 40, "full": "true"}):
            thay[d["id"]] = d
    except Exception as e:  # noqa: BLE001
        print(f"  (lỗi '{tk}': {type(e).__name__})")

print(f"Quét {len(TU_KHOA)} từ khoá → {len(thay)} dataset\n")

ket = []
for ten, d in thay.items():
    cd = d.get("cardData") or {}
    lic = str(cd.get("license") or "").lower()
    if isinstance(cd.get("license"), list):
        lic = str(cd["license"][0]).lower()
    dl = d.get("downloads", 0) or 0
    ket.append(
        {
            "ten": ten,
            "license": lic or "(trống)",
            "mo": lic in MO,
            "han_che": lic in HAN_CHE,
            "dl": dl,
            "likes": d.get("likes", 0) or 0,
            "sua": (d.get("lastModified") or "")[:10],
        }
    )

# ── nhóm 1: license MỞ, có người dùng ──────────────────────
mo = sorted([k for k in ket if k["mo"]], key=lambda x: -x["dl"])
print("=" * 78)
print("① LICENSE MỞ — dùng ngay, KHÔNG phải xin")
print("=" * 78)
print(f"{'dataset':46} {'license':14} {'tải/th':>7} {'♥':>4}")
for k in mo[:22]:
    print(f"{k['ten'][:46]:46} {k['license']:14} {k['dl']:7,} {k['likes']:4}")

print(f"\n{'=' * 78}")
print("② KIỂM TẢI ĐƯỢC KHÔNG (401/403 = gated — ca ViWikiFC)")
print("=" * 78)
for k in mo[:12]:
    ok = doc_duoc(k["ten"])
    print(f"  {'✓ tải được' if ok else '✗ GATED   '} {k['ten'][:52]:54} {k['license']}")

han = sorted([k for k in ket if k["han_che"]], key=lambda x: -x["dl"])
print(f"\n{'=' * 78}")
print("③ LICENSE HẠN CHẾ (NC/GPL — dùng được nhưng phải hỏi BTC)")
print("=" * 78)
for k in han[:10]:
    print(f"  {k['ten'][:50]:52} {k['license']:16} {k['dl']:6,}")

trong = [k for k in ket if not k["mo"] and not k["han_che"] and k["dl"] > 400]
print(f"\n{'=' * 78}")
print("④ LICENSE TRỐNG nhưng nhiều người tải (≥400/tháng) — RỦI RO, phải làm rõ")
print("=" * 78)
for k in sorted(trong, key=lambda x: -x["dl"])[:10]:
    print(f"  {k['ten'][:50]:52} {k['license']:16} {k['dl']:6,}")

print(f"\n{'=' * 78}")
print(f"TỔNG: {len(mo)} mở · {len(han)} hạn chế · {len(trong)} trống-nhưng-phổ-biến")
