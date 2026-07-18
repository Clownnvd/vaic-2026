"""Tải 15 khúc pbk_* + json từ container → ghép thành checkpoint local."""

from __future__ import annotations

import base64
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, ".")
from scripts.jupyter_fpt import CTX, nap_cau_hinh  # noqa: E402

OUT = Path("./artifacts/guard/phobert_fpt")
OUT.mkdir(parents=True, exist_ok=True)


def get_file(duong: str) -> bytes:
    goc, token = nap_cau_hinh()
    req = urllib.request.Request(
        f"{goc}/api/contents/{duong}",
        headers={"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        d = json.loads(r.read())
    return base64.b64decode(d["content"]) if d.get("format") == "base64" else (d.get("content") or "").encode()


def main() -> None:
    # json kết quả
    b = get_file("phobert_ket_qua.json")
    (OUT / "phobert_ket_qua.json").write_bytes(b)
    print("✓ phobert_ket_qua.json:", json.loads(b))

    # 15 khúc aa..ao
    import string

    names = [f"pbk_a{c}" for c in string.ascii_lowercase[:15]]  # aa..ao
    gz = OUT / "phobert_guard.tar.gz"
    tong = 0
    with gz.open("wb") as f:
        for ten in names:
            try:
                data = get_file(ten)
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {ten}: {e}")
                break
            f.write(data)
            tong += len(data)
            print(f"  {ten}: {len(data)/1e6:.1f} MB  (tổng {tong/1e6:.0f})")
    print(f"\n✓ → {gz} ({gz.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
