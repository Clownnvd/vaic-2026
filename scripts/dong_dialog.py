"""Đóng dialog Templates bằng nút X (không bấm vào card bên trong).

Chạy: uv run --python 3.11 --with websocket-client python scripts/dong_dialog.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # nút X: thường là button chứa svg, gần chữ "Templates", góc phải trên
        r = t.js(
            """
            (() => {
              // tìm nút đóng: aria-label close, hoặc svg trong header dialog
              let b = document.querySelector('[aria-label="Close"],[aria-label="close"]');
              if (!b) {
                // nút góc phải trên của modal (gần tiêu đề Templates)
                const modal = [...document.querySelectorAll('*')].find(e =>
                  (e.innerText||'').trim().startsWith('Templates'));
                if (modal) b = modal.querySelector('button');
              }
              if (!b) {
                // ESC fallback
                document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',keyCode:27,bubbles:true}));
                return 'thử ESC';
              }
              b.click();
              return 'đã bấm X';
            })()
            """
        )
        print(r)
        time.sleep(2)
        # kiểm dialog đóng chưa
        con_mo = t.js("!!document.body.innerText.match(/Search[\\s\\S]{0,40}Jupyter Notebook VOAI/)")
        print(f"dialog còn mở? {con_mo}")
        Path("./artifacts/anh").mkdir(parents=True, exist_ok=True)
        t.anh("./artifacts/anh/10_dong_dialog.png")
        # đọc summary bên phải: GPU/RAM/tổng
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        import re
        for kw in ["vaic-guard", "1xH100", "GPU:", "GPU VRAM", "RAM:", "Total:", "per hour"]:
            m = re.search(rf"{re.escape(kw)}[^\n]{{0,30}}", txt)
            if m:
                print(f"  {m.group(0)[:50]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
