"""Đọc trạng thái GPU Container + lấy URL truy cập (Jupyter) khi Running.

Chạy: uv run --python 3.11 --with websocket-client python scripts/trang_thai_container.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

URL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers"


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(URL)
        time.sleep(6)
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        # dòng có tên container + status
        m = re.search(r"vaic-guard-phobert\S*", txt)
        ten = m.group(0) if m else "(không thấy)"
        st = "?"
        for s in ("Running", "Creating", "Processing", "Stopped", "Failed", "Error"):
            if s in txt:
                st = s
                break
        print(f"container: {ten}")
        print(f"status   : {st}")

        # nếu Running → tìm link/nút Access để lấy URL Jupyter
        links = t.js(
            """
            (() => {
              const h = document.documentElement.outerHTML;
              const m = h.match(/https?:\\/\\/[^"'\\s<>\\\\]{6,160}/g) || [];
              return JSON.stringify([...new Set(m.filter(u =>
                /serverless|jupyter|lab|8888|container/i.test(u)))].slice(0,12));
            })()
            """
        )
        print(f"link liên quan: {links}")
        Path("./artifacts/anh").mkdir(parents=True, exist_ok=True)
        t.anh("./artifacts/anh/11_container_status.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
