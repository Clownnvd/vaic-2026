"""Lái tab FPT + CHỤP MÀN HÌNH mỗi bước — để xem tận mắt.

Chạy: uv run --python 3.11 --with websocket-client python scripts/lai_chup.py [url] [ten_anh]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

ANH = Path("./artifacts/anh")


def tim_tab(khoa: str) -> dict | None:
    for t in tabs():
        if khoa.lower() in (t.get("url", "") + t.get("title", "")).lower():
            return t
    return None


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else None
    ten = sys.argv[2] if len(sys.argv) > 2 else "fpt"
    ANH.mkdir(parents=True, exist_ok=True)

    t0 = tim_tab("fptcloud")
    if not t0:
        raise SystemExit("Không thấy tab FPT — mở lại giúp mình")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        if url:
            t.di_toi(url)
            time.sleep(8)
        print(f"title    : {t.js('document.title')}")
        print(f"url      : {t.js('location.href')}")
        # đăng nhập chưa? tìm số dư / nút sign-in
        so_du = t.js(
            "(()=>{const m=document.body.innerText.match(/Total Balance:[^\\n]{0,24}/);return m?m[0]:''})()"
        )
        can_dn = t.js("!!document.body.innerText.match(/Sign in\\/Sign up|Welcome back/i)")
        print(f"số dư    : {so_du or '(không thấy)'}")
        print(f"cần ĐN?  : {can_dn}")
        f = t.anh(str(ANH / f"{ten}.png"))
        print(f"ảnh      : {f}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
