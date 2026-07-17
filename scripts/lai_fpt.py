"""Lái FPT AI Factory qua CDP — tìm chỗ chạy PhoBERT.

Tab "FPT AI Factory" (ai.fptcloud.com/AI-7P46PJK3L/) đang mở SẴN và ĐÃ ĐĂNG NHẬP.
→ lái thẳng, không cần login lại, không cần MCP.

Đọc trạng thái THẬT: có instance GPU nào? notebook? quota? — không đoán.

Chạy: uv run --python 3.11 --with websocket-client python scripts/lai_fpt.py
      ... --url <URL>     điều hướng tới trang khác rồi đọc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

ANH = Path("./artifacts/anh")


def tim_tab(khoa: str) -> dict | None:
    for t in tabs():
        if khoa.lower() in (t.get("url", "") + t.get("title", "")).lower():
            return t
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="điều hướng tới URL này trước khi đọc")
    ap.add_argument("--cho", type=int, default=4, help="giây chờ trang tải")
    args = ap.parse_args()

    t0 = tim_tab("fptcloud")
    if not t0:
        raise SystemExit("Không thấy tab FPT AI Factory — mở lại giúp mình")

    ANH.mkdir(parents=True, exist_ok=True)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        if args.url:
            print(f"→ đi tới {args.url}")
            t.di_toi(args.url)
            time.sleep(args.cho)

        print("=" * 72)
        print(f"  {t.js('document.title')}")
        print(f"  {t.js('location.href')}")
        print("=" * 72)

        # ── nội dung trang ─────────────────────────────────
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        print("\n--- NỘI DUNG TRANG ---")
        for d in [x.strip() for x in txt.splitlines() if x.strip()][:60]:
            print(f"  {d[:100]}")

        # ── link điều hướng: đâu là chỗ tạo GPU/notebook? ──
        print("\n--- LINK / NÚT (tìm chỗ chạy GPU) ---")
        links = t.js(
            """
            (() => {
              const out = [];
              document.querySelectorAll('a[href], button, [role=button], [role=menuitem]')
                .forEach(e => {
                  const s = (e.innerText || e.getAttribute('aria-label') || '').trim();
                  if (s && s.length < 60)
                    out.push({t: s, h: e.getAttribute('href') || ''});
                });
              return JSON.stringify(out.slice(0, 70));
            })()
            """
        )
        try:
            for x in json.loads(links or "[]"):
                h = f"  →  {x['h'][:56]}" if x["h"] else ""
                print(f"  • {x['t'][:52]:54}{h}")
        except Exception:  # noqa: BLE001
            print(f"  {links}")

        f = t.anh(str(ANH / "fpt_ai_factory.png"))
        print(f"\n  → ảnh: {f}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
