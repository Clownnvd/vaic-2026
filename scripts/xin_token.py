"""Xin API token từ JupyterHub container (đã đăng nhập bằng cookie).

Vào /hub/token → Request new API token → bắt token hiện ra.
Token này để jupyter_fpt.py gọi REST/WebSocket như với lab cũ.

Chạy: uv run --python 3.11 --with websocket-client python scripts/xin_token.py
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

BASE = "https://vaic-guard-phobert-sgcpz687-8000.serverless.fptcloud.com"


def main() -> None:
    t0 = next((t for t in tabs() if "serverless.fptcloud" in t.get("url", "")), None)
    if not t0:
        t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(f"{BASE}/hub/token")
        time.sleep(5)
        # bấm "Request new API token"
        r = t.js(
            """
            (() => {
              const b = document.querySelector('#request-token-form button, #request-token-form input[type=submit]')
                || [...document.querySelectorAll('button,input')].find(x=>/request new api token/i.test(x.innerText||x.value||''));
              if (!b) return 'không thấy nút request';
              b.click();
              return 'đã bấm request';
            })()
            """
        )
        print(r)
        time.sleep(5)
        # token hiện trong .result-message hoặc #token-result
        tok = t.js(
            """
            (() => {
              const e = document.querySelector('#token-result, .result-message, [id*=token]');
              if (e) {
                const m = (e.innerText||'').match(/[0-9a-f]{32,}/i);
                if (m) return m[0];
              }
              const m2 = (document.body.innerText||'').match(/[0-9a-f]{32,}/i);
              return m2 ? m2[0] : '';
            })()
            """
        )
        if tok and len(tok) >= 32:
            print(f"⭐ TOKEN: {tok}")
            Path("./.fpt_container.json").write_text(
                '{\n  "goc": "%s/user/admin",\n  "token": "%s"\n}\n' % (BASE, tok),
                encoding="utf-8",
            )
            print("  → lưu .fpt_container.json")
        else:
            print(f"✗ không bắt được token. body: {(t.js('document.body.innerText') or '')[:200]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
