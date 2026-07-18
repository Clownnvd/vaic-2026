"""Xóa container 6a5a756c (liền mạch: Delete → gõ 'delete' → Confirm)."""
import sys, time, re
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs

DETAIL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/6a5a756ca74bb74d27f0f041"


def main():
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(DETAIL); time.sleep(6)
        print("Delete:", t.js("(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Delete');if(!b)return 'no';b.click();return 'ok'})()"))
        time.sleep(2.5)
        print("gõ delete:", t.js("""(()=>{const i=[...document.querySelectorAll('input')].find(x=>/delete/i.test(x.placeholder||''));if(!i)return 'no';const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(i,'delete');i.dispatchEvent(new Event('input',{bubbles:true}));return 'ok'})()"""))
        time.sleep(1.5)
        print("Confirm:", t.js("(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Confirm');if(!b||b.disabled)return 'no/disabled';b.click();return 'ok'})()"))
        time.sleep(7)
        t.di_toi('https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers'); time.sleep(6)
        txt=t.js('document.body?document.body.innerText:""') or ''
        print("còn vaic-4don?", 'vaic-4don-validate' in txt, '| Deleting?' , 'Deleting' in txt)
    finally:
        t.dong()


if __name__ == "__main__":
    main()
