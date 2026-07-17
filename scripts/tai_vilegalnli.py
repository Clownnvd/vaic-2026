"""Tải ViLegalNLI — thử 3 đường, không cần token nếu file public.

Trang HF hiện PUBLIC (có preview, license apache-2.0), nhưng load_dataset báo
"gated". Có thể chỉ resolver của datasets bị chặn, còn file thô vẫn tải thẳng được.
Thử theo thứ tự rẻ → đắt.

Chạy: uv run --python 3.11 python scripts/tai_vilegalnli.py
"""

from __future__ import annotations

import csv
import io
import os
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO = "ntphuc149/ViLegalNLI"
OUT = Path("./data/ngoai")
TOKEN = os.getenv("HF_TOKEN")


def tai(f: str) -> bytes | None:
    url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{f}"
    h = {"User-Agent": "policyradar/0.1"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        print(f"  ✗ {f}: HTTP {e.code}" + (" (cần token)" if e.code in (401, 403) else ""))
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ {f}: {type(e).__name__}")
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Tải {REPO}" + (" (có HF_TOKEN)" if TOKEN else " (KHÔNG có token — thử public)"))

    ok = {}
    for f in ("train.csv", "val.csv"):
        b = tai(f)
        if b:
            p = OUT / f"vilegalnli_{f}"
            p.write_bytes(b)
            print(f"  ✓ {f}: {len(b)/1e6:.1f} MB → {p}")
            ok[f] = b

    if not ok:
        print("\n" + "=" * 66)
        print("KHÔNG TẢI ĐƯỢC — cần token. Cách lấy:")
        print("=" * 66)
        print("  1. Vào huggingface.co/datasets/ntphuc149/ViLegalNLI")
        print("     → bấm nút đồng ý điều khoản (nếu có)")
        print("  2. Vào huggingface.co/settings/tokens → New token (quyền: read)")
        print("  3. Chạy lại kèm token:")
        print('     $env:HF_TOKEN="hf_..."; uv run ... python scripts/tai_vilegalnli.py')
        return

    # ── soi cấu trúc ──────────────────────────────────────────
    b = ok.get("train.csv")
    rows = list(csv.DictReader(io.StringIO(b.decode("utf-8", "ignore"))))
    print(f"\n=== train.csv: {len(rows):,} dòng ===")
    print(f"  cột: {list(rows[0].keys())}")

    lab = [r.get("label") for r in rows]
    print(f"  nhãn: {dict(Counter(lab))}")

    print("\n=== MẪU 2 DÒNG ===")
    for r in rows[:2]:
        for k, v in r.items():
            print(f"  {k:10}: {str(v)[:110]}")
        print()

    print("=" * 66)
    print("KHỚP DOMAIN?")
    print("=" * 66)
    import re

    RE_LUAT = re.compile(r"điều \d+|khoản \d+|nghị định|thông tư|bộ luật|luật ", re.I)
    n = sum(1 for r in rows if RE_LUAT.search(str(r.get("context", ""))))
    print(f"  context chạm văn bản luật: {n:,}/{len(rows):,} = {n/len(rows)*100:.0f}%")
    print(f"  ⇒ {'KHỚP — đây là VĂN BẢN LUẬT VN' if n/len(rows) > 0.5 else 'không khớp'}")
    print("\n  Ghi công (điều 2): ViLegalNLI — ntphuc149/ViLegalNLI, Apache-2.0")


if __name__ == "__main__":
    main()
