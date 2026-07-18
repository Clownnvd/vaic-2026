"""Bấm Access container (container mới) + bắt URL có token (tráo window.open)."""
import sys, time, json
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs

DETAIL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/6a5a756ca74bb74d27f0f041"


def main():
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(DETAIL); time.sleep(6)
        t.js("(()=>{window.__u=[];const g=window.open;window.open=function(u){window.__u.push(String(u));return{focus(){},close(){}}};return 1})()")
        r = t.js("(()=>{const b=[...document.querySelectorAll('button,a')].find(x=>/access container/i.test(x.innerText||''));if(!b)return 'no btn';b.click();return 'clicked'})()")
        print("access:", r)
        time.sleep(4)
        print("window.open bắt:", t.js("JSON.stringify(window.__u||[])"))
        # tab mới?
        for x in tabs():
            u = x.get("url", "")
            if "serverless" in u:
                print("  tab serverless:", u[:110])
    finally:
        t.dong()


if __name__ == "__main__":
    main()
