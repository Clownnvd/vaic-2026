"""XÓA container vaic-4don-h100 (ID 6a5a76a9a74bb74d27f0f058) để DỪNG TIỀN.

Kết quả 4 đòn đã tải về ./artifacts/guard/don4_h100 → xoá an toàn.
Luồng: Delete → gõ 'delete' vào ô xác nhận → Confirm → xác minh + chụp.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

CID = "6a5a76a9a74bb74d27f0f058"
TEN = "vaic-4don-h100"
DETAIL = f"https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/{CID}"
LIST = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers"


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    if not t0:
        raise SystemExit("Không thấy tab FPT — mở console FPT trong Chrome đã.")
    t = Tab(t0["webSocketDebuggerUrl"])
    Path("./artifacts/anh").mkdir(parents=True, exist_ok=True)
    try:
        t.di_toi(DETAIL)
        time.sleep(7)
        st = t.js("document.body ? document.body.innerText : ''") or ""
        print("trạng thái trước xoá:",
              next((s for s in ("Running", "Creating", "Stopped", "Failed") if s in st), "?"))

        # 1) bấm Delete
        r = t.js(
            """
            (() => {
              const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Delete');
              if(!b) return 'không thấy nút Delete';
              b.click(); return 'đã bấm Delete';
            })()
            """
        )
        print("1)", r)
        time.sleep(3)
        t.anh("./artifacts/anh/4don_01_dialog.png")

        # 2) gõ 'delete' vào ô xác nhận (nếu có)
        r2 = t.js(
            """
            (() => {
              const inp=[...document.querySelectorAll('input')].find(
                x=>/delete/i.test((x.placeholder||'')+(x.name||'')));
              if(!inp) return 'không có ô gõ (dialog xác nhận đơn giản)';
              const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
              set.call(inp,'delete');
              inp.dispatchEvent(new Event('input',{bubbles:true}));
              inp.dispatchEvent(new Event('change',{bubbles:true}));
              return 'đã gõ delete';
            })()
            """
        )
        print("2)", r2)
        time.sleep(1)

        # 3) bấm nút xác nhận (Confirm/Delete/OK, tránh Cancel)
        r3 = t.js(
            """
            (() => {
              const btns=[...document.querySelectorAll('button')].reverse();
              const b=btns.find(x=>{
                const s=(x.innerText||'').trim().toLowerCase();
                return /confirm|delete|xóa|xoá|ok|yes|đồng ý/.test(s) && !/cancel|hủy|huỷ/.test(s);
              });
              if(!b) return 'không thấy nút xác nhận';
              if(b.disabled) return 'nút xác nhận vẫn disabled';
              b.click(); return 'đã xác nhận: '+(b.innerText||'').trim().slice(0,16);
            })()
            """
        )
        print("3)", r3)
        time.sleep(8)

        # 4) kiểm danh sách còn container không
        t.di_toi(LIST)
        time.sleep(7)
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        con = TEN in txt
        stt = next((s for s in ("Deleting", "Running", "Stopped") if s in txt), "?")
        print(f"\ncòn '{TEN}' trong danh sách? {con}  (trạng thái: {stt})")
        import re
        m = re.search(r"Total Balance:[^\n]{0,24}", txt)
        print("số dư:", m.group(0) if m else "?")
        t.anh("./artifacts/anh/4don_02_sau_xoa.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
