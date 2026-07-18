"""XÓA container trong MỘT MẠCH: mở detail → Delete → gõ 'delete' → Confirm."""

import sys
import time

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

DETAIL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/6a5a4ae9cadaf9af84b4885f"


def main() -> None:
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(DETAIL)
        time.sleep(6)
        print("mở Delete:", t.js(
            "(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Delete');"
            "if(!b)return 'no btn';b.click();return 'ok';})()"
        ))
        time.sleep(2.5)
        print("gõ delete:", t.js(
            """(()=>{
              const inp=[...document.querySelectorAll('input')].find(x=>/delete/i.test(x.placeholder||''));
              if(!inp)return 'no input';
              const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
              set.call(inp,'delete');
              inp.dispatchEvent(new Event('input',{bubbles:true}));
              inp.dispatchEvent(new Event('change',{bubbles:true}));
              return 'ok val='+inp.value;
            })()"""
        ))
        time.sleep(1.5)
        print("Confirm:", t.js(
            """(()=>{
              const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Confirm');
              if(!b)return 'no confirm';
              if(b.disabled)return 'disabled';
              b.click();return 'clicked';
            })()"""
        ))
        time.sleep(8)
        t.di_toi("https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers")
        time.sleep(6)
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        import re
        st = next((s for s in ("Deleting", "No containers", "Total items: 0", "Running") if s in txt), "?")
        m = re.search(r"Total Balance:[^\n]{0,24}", txt)
        print(f"\ncòn container? {'vaic-guard-phobert' in txt}  ·  {st}")
        print("số dư:", m.group(0) if m else "?")
        t.anh("./artifacts/anh/16_ket_qua_xoa.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
