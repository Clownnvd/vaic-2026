"""Lấy URL Jupyter của container mới (6a5a756c) + đọc env password nếu lộ."""
import sys, time, re
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs

DETAIL = "https://ai.fptcloud.com/AI-7P46PJK3L/gpu-containers/6a5a756ca74bb74d27f0f041"


def main():
    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        t.di_toi(DETAIL)
        time.sleep(7)
        # URL serverless trong trang
        txt = t.js("document.documentElement.outerHTML") or ""
        m = re.search(r"https://[a-z0-9-]+\.serverless\.fptcloud\.com", txt)
        print("serverless URL:", m.group(0) if m else "(chưa thấy — có thể đang khởi động)")
        # thử đọc password env (input value)
        pw = t.js(
            """(()=>{const i=[...document.querySelectorAll('input')].find(x=>/password/i.test(x.name||''));return i?i.value:''})()"""
        )
        print("password env:", pw or "(bị che)")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
