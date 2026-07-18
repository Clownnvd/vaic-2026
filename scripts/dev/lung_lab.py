"""Lùng URL THẬT của AI Notebook (JupyterLab) — không bấm mò.

Nút "Open AI Notebook" là DIV, bấm thì popup bị Chrome chặn. Thay vì bấm mò,
đi tìm URL đích: nó phải nằm đâu đó trong DOM / state / localStorage / API.

Chạy: uv run --python 3.11 --with websocket-client python scripts/lung_lab.py
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def tim_tab(khoa: str) -> dict | None:
    for t in tabs():
        if khoa.lower() in (t.get("url", "") + t.get("title", "")).lower():
            return t
    return None


def main() -> None:
    t0 = tim_tab("ai-notebook")
    if not t0:
        t0 = tim_tab("fptcloud")
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # ── 1. mọi URL trong HTML nhắc tới lab/jupyter/notebook ──
        print("── URL trong HTML ──")
        r = t.js(
            """
            (() => {
              const h = document.documentElement.outerHTML;
              const m = h.match(/https?:\\/\\/[^"'\\s<>\\\\]{6,150}/g) || [];
              const loc = m.filter(u => /lab|jupyter|notebook|kernel|studio|8888/i.test(u));
              return JSON.stringify([...new Set(loc)].slice(0, 25));
            })()
            """
        )
        for u in json.loads(r or "[]"):
            print(f"  • {u}")

        # ── 2. localStorage / sessionStorage ────────────────
        print("\n── storage ──")
        r = t.js(
            """
            (() => {
              const out = {};
              for (const s of [localStorage, sessionStorage]) {
                for (let i = 0; i < s.length; i++) {
                  const k = s.key(i); const v = s.getItem(k) || '';
                  if (/lab|jupyter|notebook|url|endpoint/i.test(k + v))
                    out[k] = v.slice(0, 180);
                }
              }
              return JSON.stringify(out);
            })()
            """
        )
        try:
            for k, v in json.loads(r or "{}").items():
                print(f"  • {k[:40]:42} {v[:110]}")
        except Exception:  # noqa: BLE001
            print(f"  {str(r)[:300]}")

        # ── 3. nút Open AI Notebook: nó gắn handler gì? ─────
        print("\n── phần tử «Open AI Notebook» ──")
        r = t.js(
            """
            (() => {
              const ds = [...document.querySelectorAll('*')];
              const e = ds.find(x => (x.innerText||'').trim() === 'Open AI Notebook');
              if (!e) return 'không thấy';
              return JSON.stringify({
                the: e.tagName, cls: (e.className||'').toString().slice(0,90),
                cha: e.parentElement ? e.parentElement.tagName : '',
                cha_href: e.parentElement ? (e.parentElement.getAttribute('href')||'') : '',
                onclick: (e.onclick||'').toString().slice(0,150),
                html: e.outerHTML.slice(0, 260),
              });
            })()
            """
        )
        print(f"  {r}")

        # ── 4. MENU — trang bảo "open from the menu" ────────
        print("\n── menu ──")
        r = t.js(
            """
            (() => {
              const out = [];
              document.querySelectorAll('nav a, aside a, [class*=menu] a, [class*=sidebar] a, header a')
                .forEach(a => out.push({t:(a.innerText||'').trim().slice(0,40), h:a.getAttribute('href')||''}));
              return JSON.stringify(out.filter(x => x.t).slice(0, 30));
            })()
            """
        )
        try:
            for x in json.loads(r or "[]"):
                print(f"  • {x['t']:34} → {x['h'][:60]}")
        except Exception:  # noqa: BLE001
            print(f"  {str(r)[:250]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
