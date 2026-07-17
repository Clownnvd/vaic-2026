"""XÓA GPU container để DỪNG TIỀN — bấm Delete + xác nhận.

Chạy: uv run --python 3.11 --with websocket-client python scripts/xoa_container.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

DETAIL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/6a5a4ae9cadaf9af84b4885f"


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(DETAIL)
        time.sleep(6)
        # bấm Delete
        r = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Delete');
              if (!b) return 'không thấy nút Delete';
              b.click();
              return 'đã bấm Delete';
            })()
            """
        )
        print(r)
        time.sleep(3)
        Path("./artifacts/anh").mkdir(parents=True, exist_ok=True)
        t.anh("./artifacts/anh/14_xoa_confirm.png")

        # dialog xác nhận: bấm nút xác nhận (Delete/Confirm/Xóa/OK)
        r2 = t.js(
            """
            (() => {
              const btns = [...document.querySelectorAll('button')];
              // nút xác nhận trong dialog — ưu tiên đỏ/Delete/Confirm, tránh Cancel
              const b = btns.reverse().find(x=>{
                const s=(x.innerText||'').trim().toLowerCase();
                return /delete|confirm|xóa|xoá|ok|đồng ý|yes/.test(s) && !/cancel|hủy|huỷ/.test(s);
              });
              if (!b) return 'không thấy nút xác nhận';
              b.click();
              return 'đã xác nhận: ' + (b.innerText||'').trim().slice(0,20);
            })()
            """
        )
        print(r2)
        time.sleep(6)
        # kiểm còn container không
        t.di_toi("https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers")
        time.sleep(6)
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        con = "vaic-guard-phobert" in txt
        st = "Deleting" if "Deleting" in txt else ("Running" if "Running" in txt else "?")
        print(f"\ncontainer còn trong danh sách? {con}  (trạng thái: {st})")
        # số dư
        import re
        m = re.search(r"Total Balance:[^\n]{0,24}", txt)
        print("số dư:", m.group(0) if m else "?")
        t.anh("./artifacts/anh/15_sau_xoa.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
