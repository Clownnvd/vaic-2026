"""Test giao diện E2E — lái frontend localhost:3002 qua nhiều ca, chụp lại.

Chạy: uv run --python 3.11 --with websocket-client python scripts/test_ui.py <ca> <text>
  ca: ten anh (vd 'du_dk', 'khong_dk', 'thieu_tin', 'ngoai_pham_vi')
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

ANH = Path("./artifacts/anh")
FE = "http://localhost:3002/"


def tab_fe() -> Tab:
    t0 = next((t for t in tabs() if "localhost:3002" in t.get("url", "")), None)
    if not t0:
        t0 = next((t for t in tabs() if "localhost" in t.get("url", "")), None)
    if not t0:
        raise SystemExit("Không thấy tab localhost:3002 — mở giúp mình")
    return Tab(t0["webSocketDebuggerUrl"])


def go_chat(t: Tab, text: str) -> str:
    """Gõ vào ô chat (React-compatible) + submit form."""
    r = t.js(
        f"""
        (() => {{
          const ta = document.querySelector('textarea');
          if (!ta) return 'no textarea';
          const set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
          set.call(ta, {text!r});
          ta.dispatchEvent(new Event('input',{{bubbles:true}}));
          return 'typed len=' + ta.value.length;
        }})()
        """
    )
    time.sleep(0.5)
    # submit qua form (requestSubmit) — chắc hơn click nút
    r2 = t.js(
        """
        (() => {
          const ta = document.querySelector('textarea');
          const form = ta && ta.closest('form');
          if (form) { form.requestSubmit(); return 'submitted'; }
          const b = [...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Gửi');
          if (b && !b.disabled) { b.click(); return 'clicked Gửi'; }
          return 'no submit';
        })()
        """
    )
    return f"{r} → {r2}"


def main() -> None:
    ca = sys.argv[1] if len(sys.argv) > 1 else "test"
    text = sys.argv[2] if len(sys.argv) > 2 else ""
    ANH.mkdir(parents=True, exist_ok=True)

    t = tab_fe()
    try:
        if text:
            go_chat(t, text)
            time.sleep(5)  # chờ BFF trả
        # đọc nội dung phản hồi cuối
        txt = t.js("document.body ? document.body.innerText.slice(-1400) : ''") or ""
        print(f"=== {ca} ===")
        print(txt[-900:])
        t.anh(str(ANH / f"ui_{ca}.png"))
        print(f"\nảnh: artifacts/anh/ui_{ca}.png")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
