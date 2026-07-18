"""Bắt URL mà nút định mở — không cần popup.

BẪY: nút "Open AI Notebook" là <button> React gọi window.open(). Chrome chặn
popup vì click do CDP kích, không phải cử chỉ người dùng thật.

MẸO: tráo window.open bằng hàm GHI LẠI url rồi trả về giả. Bấm xong đọc biến.
Không cần popup, không cần bật lại popup blocker.

Chạy: uv run --python 3.11 --with websocket-client python scripts/bat_popup.py
"""

from __future__ import annotations

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
    t0 = tim_tab("ai-notebook") or tim_tab("fptcloud")
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # tráo window.open + chặn mọi cách điều hướng khác để ghi lại đích
        t.js(
            """
            (() => {
              window.__bat = [];
              const goc = window.open;
              window.open = function(u, ...r) {
                window.__bat.push({cach:'window.open', url: String(u)});
                return {focus(){}, close(){}, closed:false, document:{}};
              };
              window.__open_goc = goc;
              // vài SPA dùng <a> ẩn + click, hoặc gán location
              document.addEventListener('click', e => {
                const a = e.target.closest && e.target.closest('a[href]');
                if (a) window.__bat.push({cach:'thẻ a', url: a.href});
              }, true);
              return 'đã tráo';
            })()
            """
        )

        # bấm ĐÚNG <button>, không phải DIV bọc ngoài
        r = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button')]
                .find(x => (x.innerText||'').trim() === 'Open AI Notebook');
              if (!b) return 'không thấy BUTTON';
              b.click();
              return 'đã bấm button';
            })()
            """
        )
        print(f"  {r}")
        time.sleep(4)

        bat = t.js("JSON.stringify(window.__bat || [])")
        print(f"\n  ⭐ ĐÍCH BẮT ĐƯỢC: {bat}")
        print(f"  url hiện tại   : {t.js('location.href')}")

        # nếu bắt được → đi thẳng tới đó bằng chính tab này (không cần popup)
        import json

        ds = json.loads(bat or "[]")
        if ds:
            u = ds[0]["url"]
            print(f"\n  → điều hướng thẳng tới: {u}")
            t.di_toi(u)
            time.sleep(8)
            print(f"  url sau  : {t.js('location.href')}")
            print(f"  title    : {t.js('document.title')}")
            txt = (t.js("document.body ? document.body.innerText.slice(0,400) : ''") or "").replace("\n", " | ")
            print(f"  nội dung : {txt[:340]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
