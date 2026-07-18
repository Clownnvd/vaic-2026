"""Gõ 'delete' vào ô xác nhận + bấm Confirm để XÓA container thật."""

import sys
import time

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # gõ "delete" vào ô input của dialog
        r = t.js(
            """
            (() => {
              const inp = [...document.querySelectorAll('input')].find(
                x => /input delete|delete/i.test(x.placeholder||''));
              if (!inp) return 'không thấy ô delete';
              const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
              set.call(inp,'delete');
              inp.dispatchEvent(new Event('input',{bubbles:true}));
              inp.dispatchEvent(new Event('change',{bubbles:true}));
              return 'đã gõ delete';
            })()
            """
        )
        print(r)
        time.sleep(1)
        r2 = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button')].find(
                x => (x.innerText||'').trim() === 'Confirm');
              if (!b) return 'không thấy Confirm';
              if (b.disabled) return 'Confirm vẫn disabled';
              b.click();
              return 'đã bấm Confirm';
            })()
            """
        )
        print(r2)
        time.sleep(7)
        # kiểm danh sách
        t.di_toi("https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers")
        time.sleep(6)
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        con = "vaic-guard-phobert" in txt
        import re
        st = "?"
        for s in ("Deleting", "Deleted", "Running", "No containers", "Total items: 0"):
            if s in txt:
                st = s
                break
        m = re.search(r"Total Balance:[^\n]{0,24}", txt)
        print(f"\ncontainer còn? {con}  ·  trạng thái: {st}")
        print("số dư:", m.group(0) if m else "?")
        t.anh("./artifacts/anh/15_sau_xoa.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
