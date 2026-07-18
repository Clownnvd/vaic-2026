"""Lái FPT AI Factory — tìm đường tới Notebook/GPU và ĐỌC GIÁ trước khi tiêu tiền.

Số dư thật: 1.280.848 ₫. Tiêu là mất. ĐỌC GIÁ TRƯỚC, không bấm bừa.

Chạy: uv run --python 3.11 --with websocket-client python scripts/lai_fpt_do.py
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

GOC = "https://ai.fptcloud.com/AI-7P46PJK3L"


def tim_tab(khoa: str) -> dict | None:
    for t in tabs():
        if khoa.lower() in (t.get("url", "") + t.get("title", "")).lower():
            return t
    return None


def doc(t: Tab, nhan: str) -> str:
    txt = t.js("document.body ? document.body.innerText : ''") or ""
    print(f"\n{'=' * 72}\n  {nhan}  —  {t.js('location.href')}\n{'=' * 72}")
    return txt


def main() -> None:
    t0 = tim_tab("fptcloud")
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # ── 1. mọi route trong SPA ─────────────────────────
        print("Dò mọi link nội bộ trên trang chủ…")
        r = t.js(
            """
            (() => {
              const s = new Set();
              document.querySelectorAll('a[href^="/AI-"]').forEach(a =>
                s.add(a.getAttribute('href')));
              return JSON.stringify([...s]);
            })()
            """
        )
        print(f"  link <a>: {r}")

        # Card "Quick access" gắn onclick → dò text để bấm đúng cái
        r2 = t.js(
            """
            (() => {
              const out = [];
              document.querySelectorAll('div,section,li').forEach(e => {
                const s = (e.innerText || '').trim();
                if (/Run a GPU Container|GPU Virtual Machine|Start AI Notebook|Model Inference/i.test(s)
                    && s.length < 130 && e.children.length < 6)
                  out.push(s.split('\\n')[0]);
              });
              return JSON.stringify([...new Set(out)]);
            })()
            """
        )
        print(f"  card quick-access: {r2}")

        # ── 2. thử các route hay gặp ───────────────────────
        for duong in ("/notebook", "/notebooks", "/ai-notebook", "/gpu-container", "/instances"):
            t.di_toi(GOC + duong)
            time.sleep(3)
            u = t.js("location.href") or ""
            tit = (t.js("document.body ? document.body.innerText.slice(0,90) : ''") or "").replace("\n", " ")
            ok = "404" not in tit and "not found" not in tit.lower()
            print(f"  {duong:16} {'✓' if ok else '✗'}  {u[-42:]:44} {tit[:44]}")

        # ── 3. TRANG GIÁ — đọc trước khi tiêu ──────────────
        t.di_toi(GOC + "/pricing")
        time.sleep(5)
        txt = doc(t, "BẢNG GIÁ")
        for d in [x.strip() for x in txt.splitlines() if x.strip()][:70]:
            print(f"  {d[:96]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
