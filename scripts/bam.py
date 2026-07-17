"""Bấm nút trên trang FPT qua CDP — theo TEXT của nút, không theo toạ độ.

Bấm theo toạ độ là bẫy: layout đổi một tí là bấm nhầm. Bấm theo text thì
sai text sẽ BÁO LỖI thay vì lặng lẽ bấm nhầm nút bên cạnh.

Chạy: uv run --python 3.11 --with websocket-client python scripts/bam.py "Open AI Notebook"
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
    if len(sys.argv) < 2:
        raise SystemExit('Dùng: python scripts/bam.py "<text nút>" [khoá-tab]')
    nhan = sys.argv[1]
    khoa = sys.argv[2] if len(sys.argv) > 2 else "fptcloud"

    t0 = tim_tab(khoa)
    if not t0:
        raise SystemExit(f"Không thấy tab khớp '{khoa}'")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        truoc = t.js("location.href")
        n_tab = len(tabs())

        r = t.js(
            f"""
            (() => {{
              const muc = {json.dumps(nhan)}.toLowerCase();
              const ds = [...document.querySelectorAll('a,button,[role=button],div,span')];
              // khớp CHÍNH XÁC trước, rồi mới khớp chứa — tránh bấm nhầm phần tử cha
              let e = ds.find(x => (x.innerText||'').trim().toLowerCase() === muc);
              if (!e) e = ds.find(x => {{
                const s = (x.innerText||'').trim().toLowerCase();
                return s.includes(muc) && s.length < muc.length + 24;
              }});
              if (!e) return JSON.stringify({{ok:false, ly_do:'không thấy nút'}});
              e.scrollIntoView({{block:'center'}});
              e.click();
              return JSON.stringify({{ok:true, the:e.tagName, href:e.getAttribute('href')||''}});
            }})()
            """
        )
        print(f"bấm «{nhan}» → {r}")
        time.sleep(5)

        sau = t.js("location.href")
        print(f"  url: {truoc}")
        print(f"   →   {sau}")
        if sau == truoc:
            print("  (url không đổi — có thể mở TAB MỚI)")

        ds = tabs()
        if len(ds) != n_tab:
            print(f"\n  ⭐ TAB MỚI ({n_tab} → {len(ds)}):")
        for x in ds:
            print(f"    • {x.get('title','')[:46]:48} {x.get('url','')[:64]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
