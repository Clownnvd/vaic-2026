"""Lái Chrome bằng CDP trực tiếp — KHÔNG cần chrome-devtools-mcp.

Vì sao viết cái này: MCP chỉ nạp lúc MỞ PHIÊN. `.mcp.json` không có trong
VAIC-DDAY nên phiên này không có chrome-devtools. Nhưng chrome-devtools-mcp
bản chất chỉ là lớp bọc quanh **Chrome DevTools Protocol** — mà Chrome đang mở
sẵn cổng 9222, nên nói thẳng với CDP là xong. Không cần restart phiên.

Dùng để: xem tab đang mở, điều hướng, đọc nội dung trang, chụp màn hình
(vd: vào console FPT thuê GPU, hoặc lấy brief đầy đủ của đề P1 trên hub).

Chạy: uv run --python 3.11 --with websocket-client python scripts/chrome_cdp.py
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.request

CDP = "http://127.0.0.1:9222"


def tabs() -> list[dict]:
    with urllib.request.urlopen(f"{CDP}/json/list", timeout=8) as r:
        return [t for t in json.load(r) if t.get("type") == "page"]


class Tab:
    """Một tab Chrome — gửi lệnh CDP qua WebSocket."""

    def __init__(self, ws_url: str):
        from websocket import create_connection

        # ⚠️ suppress_origin=True là BẮT BUỘC.
        # Chrome chặn WebSocket CDP nếu request có header `Origin` (chống DNS-rebinding):
        #   403 "Rejected an incoming WebSocket connection from the http://127.0.0.1:9222 origin"
        # websocket-client mặc định tự gắn Origin → bị chặn.
        # Cách khác là mở Chrome kèm --remote-allow-origins=* nhưng phải khởi động lại
        # Chrome (mất session đã đăng nhập). Bỏ Origin đi thì không phải đụng gì.
        self.ws = create_connection(ws_url, timeout=25, suppress_origin=True)
        self._id = 0

    def goi(self, method: str, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self._id:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m.get("result", {})

    def js(self, bieu_thuc: str):
        """Chạy JS trong trang, trả giá trị."""
        r = self.goi(
            "Runtime.evaluate",
            expression=bieu_thuc,
            returnByValue=True,
            awaitPromise=True,
        )
        return r.get("result", {}).get("value")

    def di_toi(self, url: str) -> None:
        self.goi("Page.enable")
        self.goi("Page.navigate", url=url)

    def anh(self, duong_dan: str) -> str:
        r = self.goi("Page.captureScreenshot", format="png")
        with open(duong_dan, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        return duong_dan

    def dong(self) -> None:
        self.ws.close()


def main() -> None:
    ds = tabs()
    print(f"Chrome CDP :9222 — {len(ds)} tab đang mở\n")
    for i, t in enumerate(ds):
        print(f"  [{i}] {t.get('title', '')[:56]}")
        print(f"      {t.get('url', '')[:92]}")

    if not ds:
        return

    # thử lái tab đầu — đọc trạng thái thật, không đoán
    print("\n=== THỬ ĐIỀU KHIỂN (tab 0) ===")
    t = Tab(ds[0]["webSocketDebuggerUrl"])
    try:
        print(f"  title    : {t.js('document.title')}")
        print(f"  url      : {str(t.js('location.href'))[:88]}")
        print(f"  đăng nhập: {t.js('!!document.cookie.length')} (có cookie)")
        txt = t.js("document.body ? document.body.innerText.slice(0,180) : ''")
        print(f"  nội dung : {str(txt)[:160]!r}")
        print("\n  ✓ LÁI ĐƯỢC — đọc/chạy JS/điều hướng/chụp ảnh đều làm được, không cần MCP.")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
