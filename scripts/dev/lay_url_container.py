"""Bấm 'Access container' + bắt URL Jupyter mà nó mở (tráo window.open).

Giống bat_popup.py cho notebook: nút mở tab mới → Chrome chặn popup →
tráo window.open để ghi lại URL đích thay vì để nó mở.

Chạy: uv run --python 3.11 --with websocket-client python scripts/lay_url_container.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def main() -> None:
    t0 = next((t for t in tabs() if "gpu-containers" in t.get("url", "")), None)
    if not t0:
        t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # tráo window.open + ghi mọi href được click
        t.js(
            """
            (() => {
              window.__bat = [];
              const goc = window.open;
              window.open = function(u, ...r){ window.__bat.push(String(u)); return {focus(){},close(){},closed:false}; };
              document.addEventListener('click', e => {
                const a = e.target.closest && e.target.closest('a[href]');
                if (a && a.href) window.__bat.push(a.href);
              }, true);
              return 'đã tráo';
            })()
            """
        )
        r = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button,a')]
                .find(x => (x.innerText||'').trim() === 'Access container');
              if (!b) return 'không thấy nút Access container';
              b.click();
              return 'đã bấm Access container';
            })()
            """
        )
        print(r)
        time.sleep(4)
        bat = t.js("JSON.stringify(window.__bat || [])")
        print(f"URL bắt được: {bat}")

        ds = json.loads(bat or "[]")
        jup = next((u for u in ds if "serverless" in u or "8888" in u or "jupyter" in u.lower()), None)
        if jup:
            print(f"\n⭐ URL Jupyter container: {jup}")
            Path("./artifacts").mkdir(exist_ok=True)
            Path("./artifacts/container_jupyter_url.txt").write_text(jup, encoding="utf-8")
            print("  → lưu artifacts/container_jupyter_url.txt")
        else:
            # có thể URL nằm trong trang detail (field endpoint)
            txt = t.js("document.body ? document.body.innerText : ''") or ""
            import re
            for m in re.findall(r"https?://[^\s]{10,140}", txt):
                if "serverless" in m or "8888" in m:
                    print(f"  URL trong trang: {m}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
