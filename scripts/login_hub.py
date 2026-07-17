"""Đăng nhập JupyterHub container bằng admin + mật khẩu.

Chạy: uv run --python 3.11 --with websocket-client python scripts/login_hub.py <password>
"""

import sys
import time

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

HUB = "https://vaic-guard-phobert-sgcpz687-8000.serverless.fptcloud.com/hub/login"


def main() -> None:
    pw = sys.argv[1] if len(sys.argv) > 1 else ""
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(HUB)
        time.sleep(5)
        r = t.js(
            f"""
            (() => {{
              const u = document.querySelector('input[name=username]');
              const p = document.querySelector('input[name=password]');
              if (!u || !p) return 'không thấy form login: ' + document.title;
              const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
              set.call(u,'admin'); u.dispatchEvent(new Event('input',{{bubbles:true}}));
              set.call(p,{pw!r}); p.dispatchEvent(new Event('input',{{bubbles:true}}));
              const btn = document.querySelector('input[type=submit],button[type=submit]') ||
                          [...document.querySelectorAll('button')].find(b=>/sign in|log in|đăng nhập/i.test(b.innerText));
              if (!btn) return 'không thấy nút submit';
              btn.click();
              return 'đã submit admin/' + '*'.repeat({len(pw)});
            }})()
            """
        )
        print(r)
        time.sleep(6)
        u = t.js("location.href")
        tit = t.js("document.title")
        print(f"url  : {u}")
        print(f"title: {tit}")
        # login thành công → rời khỏi /login
        if "/login" not in u:
            print("✓ ĐĂNG NHẬP THÀNH CÔNG")
        else:
            err = t.js("(()=>{const e=document.querySelector('.error,[class*=error]');return e?e.innerText:''})()")
            print(f"✗ vẫn ở login. lỗi: {err[:80]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
