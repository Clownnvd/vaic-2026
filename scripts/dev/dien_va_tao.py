"""Điền tên container + bấm Create — qua CDP.

Đặt tên rõ để dễ tìm mà xóa sau (tránh để phí tiền). KHÔNG đụng GPU instance
(mặc định 1xH100 = rẻ nhất) và env (USERNAME/PASSWORD tự sinh).

Chạy: uv run --python 3.11 --with websocket-client python scripts/dien_va_tao.py <ten> [--tao]
  không có --tao: chỉ điền tên + chụp, KHÔNG bấm Create (xem trước)
  có --tao      : điền xong bấm Create THẬT (bắt đầu tính tiền)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

ANH = Path("./artifacts/anh")


def main() -> None:
    ten = sys.argv[1] if len(sys.argv) > 1 else "vaic-guard"
    tao_that = "--tao" in sys.argv
    ANH.mkdir(parents=True, exist_ok=True)

    t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), None)
    if not t0:
        raise SystemExit("Không thấy tab FPT")
    t = Tab(t0["webSocketDebuggerUrl"])
    try:
        # điền tên vào input name (React controlled → phải set value + bắn event)
        r = t.js(
            f"""
            (() => {{
              const inp = document.querySelector('input[name="name"]');
              if (!inp) return 'không thấy input name';
              const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
              setter.call(inp, {ten!r});
              inp.dispatchEvent(new Event('input', {{bubbles:true}}));
              inp.dispatchEvent(new Event('change', {{bubbles:true}}));
              return 'đã điền: ' + inp.value;
            }})()
            """
        )
        print(f"tên: {r}")
        time.sleep(1)
        t.anh(str(ANH / "07_da_dien_ten.png"))
        print("ảnh: artifacts/anh/07_da_dien_ten.png")

        if not tao_that:
            print("\n(chưa bấm Create — chạy lại với --tao để tạo thật)")
            return

        # bấm Create Container
        r2 = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button')]
                .find(x => (x.innerText||'').trim() === 'Create Container');
              if (!b) return 'không thấy nút Create Container';
              if (b.disabled) return 'nút Create đang DISABLED (thiếu field?)';
              b.click();
              return 'đã bấm Create Container';
            })()
            """
        )
        print(f"create: {r2}")
        time.sleep(6)
        print(f"url sau: {t.js('location.href')}")
        t.anh(str(ANH / "08_da_tao.png"))
        print("ảnh: artifacts/anh/08_da_tao.png")
        txt = (t.js("document.body ? document.body.innerText : ''") or "")
        for d in [x.strip() for x in txt.splitlines() if x.strip()][:40]:
            print(f"  {d[:90]}")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
