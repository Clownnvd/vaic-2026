"""Tạo container mới + ĐẶT PASSWORD BIẾT TRƯỚC (để login JupyterHub được).

Navigate /new → Change template → Jupyter → đóng dialog → set password + name → Create.
"""
import sys, time
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs

PW = "vaic2026guard"
TEN = "vaic-4don-h100"


def setv(t, sel, val):
    return t.js(f"""(()=>{{const i=document.querySelector({sel!r});if(!i)return 'no';
      const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
      s.call(i,{val!r});i.dispatchEvent(new Event('input',{{bubbles:true}}));i.dispatchEvent(new Event('change',{{bubbles:true}}));return i.value}})()""")


def clickText(t, txt):
    return t.js(f"""(()=>{{const b=[...document.querySelectorAll('button,a,span,div')].find(x=>(x.innerText||'').trim()==={txt!r});if(!b)return 'no';b.click();return 'ok'}})()""")


def main():
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi("https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/new"); time.sleep(7)
        print("change template:", clickText(t, "Change template")); time.sleep(2)
        print("jupyter:", clickText(t, "Jupyter Notebook")); time.sleep(1.5)
        # đóng dialog (nút X hoặc ESC)
        t.js("(()=>{const b=document.querySelector('[aria-label=Close],[aria-label=close]');if(b)b.click();else document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));return 1})()")
        time.sleep(1.5)
        print("name:", setv(t, 'input[name="name"]', TEN))
        # password env — input password thứ 2 (container_envs.1.value)
        pw = t.js(f"""(()=>{{const i=[...document.querySelectorAll('input')].find(x=>x.type==='password'||/password/i.test(x.name||''));if(!i)return 'no';
          const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          s.call(i,{PW!r});i.dispatchEvent(new Event('input',{{bubbles:true}}));i.dispatchEvent(new Event('change',{{bubbles:true}}));return i.value}})()""")
        print("password:", pw)
        time.sleep(1)
        print("create:", t.js("(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Create Container');if(!b)return 'no';if(b.disabled)return 'disabled';b.click();return 'ok'})()"))
        time.sleep(6)
        print("url sau:", t.js("location.href")[:70])
    finally:
        t.dong()


if __name__ == "__main__":
    main()
