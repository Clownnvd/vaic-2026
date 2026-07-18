"""Xem console FPT AI Factory — CHỈ ĐỌC, không thuê gì, không tiêu tiền.

Mục đích: biết đang có gì (balance, GPU nào, giá) TRƯỚC khi quyết thuê.
Chạy: uv run --python 3.11 --with websocket-client python scripts/fpt_xem.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def main() -> None:
    ds = tabs()
    fpt = [t for t in ds if "fptcloud.com" in t.get("url", "")]
    if not fpt:
        print("Không thấy tab FPT nào đang mở.")
        return

    t = Tab(fpt[0]["webSocketDebuggerUrl"])
    try:
        print(f"URL: {t.js('location.href')}\n")

        print("=== TÀI KHOẢN ===")
        bal = t.js(
            """
            (() => {
              const m = document.body.innerText.match(/Total Balance:\\s*([\\d.,]+\\s*₫)/);
              return m ? m[1] : 'không thấy';
            })()
            """
        )
        print(f"  số dư: {bal}")
        vung = t.js(
            """
            (() => {
              const m = document.body.innerText.match(/(Hanoi|Saigon|HCM)[^\\n]{0,24}/i);
              return m ? m[0] : 'không thấy';
            })()
            """
        )
        print(f"  vùng : {vung}   ← data ở VN = pitch chủ quyền dữ liệu")

        print("\n=== MENU / DỊCH VỤ trên trang ===")
        menu = t.js(
            """
            [...document.querySelectorAll('a,button')]
              .map(e => (e.innerText||'').trim())
              .filter(s => s.length > 2 && s.length < 44)
              .filter((s,i,a) => a.indexOf(s) === i)
              .slice(0, 30)
            """
        )
        for m in menu or []:
            print(f"  • {m}")

        print("\n=== TÌM MỤC GPU / INSTANCE ===")
        gpu = t.js(
            """
            (() => {
              const t = document.body.innerText;
              const ra = [];
              for (const k of ['GPU','H100','A100','H200','Instance','VM','Notebook','Serverless','Model Hub']) {
                if (t.includes(k)) ra.push(k);
              }
              return ra;
            })()
            """
        )
        print(f"  từ khoá thấy trên trang: {gpu or 'không có'}")

        t.anh("./artifacts/fpt_console.png")
        print("\n  ✓ đã chụp → artifacts/fpt_console.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
