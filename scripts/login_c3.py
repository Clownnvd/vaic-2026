"""Login JupyterHub container mới + lấy token → ghi .fpt_container.json."""
import sys, time
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs
from pathlib import Path

BASE = "https://vaic-4don-h100-l9zbe38g-8000.serverless.fptcloud.com"
PW = "vaic2026guard"


def main():
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(f"{BASE}/hub/login?next=%2Fhub%2F"); time.sleep(5)
        r = t.js(f"""(()=>{{const u=document.querySelector('input[name=username]');const p=document.querySelector('input[name=password]');if(!u||!p)return 'no form: '+document.title;
          const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          s.call(u,'admin');u.dispatchEvent(new Event('input',{{bubbles:true}}));
          s.call(p,{PW!r});p.dispatchEvent(new Event('input',{{bubbles:true}}));
          const b=document.querySelector('input[type=submit],button[type=submit]')||[...document.querySelectorAll('button')].find(x=>/sign in/i.test(x.innerText));
          if(!b)return 'no submit';b.click();return 'submitted'}})()""")
        print("login:", r)
        time.sleep(6)
        u = t.js("location.href")
        print("url:", u[:80])
        if "/login" in u:
            print("✗ vẫn ở login"); return
        # xin token
        t.di_toi(f"{BASE}/hub/token"); time.sleep(4)
        t.js("(()=>{const b=document.querySelector('#request-token-form button,#request-token-form input[type=submit]')||[...document.querySelectorAll('button,input')].find(x=>/request new api token/i.test(x.innerText||x.value||''));if(b)b.click();return 1})()")
        time.sleep(4)
        tok = t.js("""(()=>{const e=document.querySelector('#token-result,.result-message');const m=((e&&e.innerText)||document.body.innerText||'').match(/[0-9a-f]{32,}/i);return m?m[0]:''})()""")
        if tok and len(tok) >= 32:
            print("TOKEN:", tok)
            Path("./.fpt_container.json").write_text('{\n  "goc": "%s/user/admin",\n  "token": "%s"\n}\n' % (BASE, tok), encoding="utf-8")
            print("→ .fpt_container.json")
        else:
            print("✗ không lấy được token")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
