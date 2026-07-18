"""Bấm 'Access container' + bắt URL/tab mở ra (có thể đã tự đăng nhập SSO).

Chạy: uv run --python 3.11 --with websocket-client python scripts/access_container.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def main() -> None:
    t0 = next((t for t in tabs() if "gpu-containers/6a5a" in t.get("url", "")), None)
    if not t0:
        t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    n_tab_truoc = len(tabs())
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.js(
            """
            (() => {
              window.__u = [];
              const g = window.open;
              window.open = function(u,...r){ window.__u.push(String(u)); return {focus(){},close(){},closed:false}; };
              return 'traó';
            })()
            """
        )
        r = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button,a,[role=button]')]
                .find(x => /access container/i.test((x.innerText||'')));
              if (!b) return 'không thấy';
              b.click();
              return 'đã bấm: ' + (b.innerText||'').trim().slice(0,30);
            })()
            """
        )
        print(r)
        time.sleep(5)
        print("window.open bắt:", t.js("JSON.stringify(window.__u||[])"))

        # tab mới?
        ds = tabs()
        if len(ds) != n_tab_truoc:
            print(f"\nTAB MỚI ({n_tab_truoc}→{len(ds)}):")
        for x in ds:
            u = x.get("url", "")
            if "serverless" in u or "jupyter" in u.lower() or "hub" in u:
                print(f"  ⭐ {x.get('title','')[:30]:32} {u[:100]}")
                Path("./artifacts").mkdir(exist_ok=True)
                Path("./artifacts/container_access_url.txt").write_text(u, encoding="utf-8")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
