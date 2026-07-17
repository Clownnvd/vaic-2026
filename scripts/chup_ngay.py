"""Chụp tab FPT HIỆN TẠI (không điều hướng) + đọc mọi input/select/option.

Chạy: uv run --python 3.11 --with websocket-client python scripts/chup_ngay.py <ten_anh>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

ANH = Path("./artifacts/anh")


def main() -> None:
    ten = sys.argv[1] if len(sys.argv) > 1 else "fpt_now"
    ANH.mkdir(parents=True, exist_ok=True)
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        print(f"url: {t.js('location.href')}")
        f = t.anh(str(ANH / f"{ten}.png"))
        print(f"ảnh: {f}")

        # đọc mọi trường nhập liệu
        r = t.js(
            """
            (() => {
              const out = {inputs:[], selects:[], radios:[], buttons:[]};
              document.querySelectorAll('input').forEach(e => out.inputs.push(
                {name:e.name||e.placeholder||'', type:e.type, value:(e.value||'').slice(0,40),
                 checked:e.checked}));
              document.querySelectorAll('select').forEach(e => out.selects.push(
                {name:e.name||'', opts:[...e.options].map(o=>o.text).slice(0,12)}));
              document.querySelectorAll('button,[role=button]').forEach(e => {
                const s=(e.innerText||'').trim(); if(s && s.length<40) out.buttons.push(s);});
              return JSON.stringify(out);
            })()
            """
        )
        d = json.loads(r or "{}")
        print("\n-- INPUT --")
        for x in d.get("inputs", [])[:20]:
            print(f"  [{x['type']:8}] {x['name'][:38]:40} = {x['value']!r}{' ✓' if x['checked'] else ''}")
        print("\n-- SELECT --")
        for x in d.get("selects", []):
            print(f"  {x['name']}: {x['opts']}")
        print("\n-- BUTTON --")
        print(" ", list(dict.fromkeys(d.get("buttons", [])))[:16])
    finally:
        t.dong()


if __name__ == "__main__":
    main()
