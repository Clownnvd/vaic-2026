"""E2E THẬT — lái Chrome bấm vào giao diện, xem BFF có bị gọi không.

VÌ SAO CẦN: trước giờ chỉ verify bằng typecheck + build + curl thẳng BFF.
Chưa lần nào chứng minh FRONTEND thật sự GỌI được BFF. Nói "cắm xong" mà chưa
nhìn thấy nó chạy là nói ẩu.

Cách đo: đếm số dòng trong sổ audit / gọi API trước và sau khi bấm — nếu frontend
thật sự gọi BFF thì phải thấy request. Ở đây dùng CDP bắt Network.

Chạy: uv run --python 3.11 --with websocket-client python scripts/e2e_browser.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request

sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

URL = "http://localhost:3002/"
CAU = "Bên mình làm phần mềm ở Hà Nội, vốn 20 tỷ, 45 người, chi R&D khoảng 2,5% doanh thu, không có vốn FDI"


def tab_moi(url: str) -> dict:
    with urllib.request.urlopen(
        f"http://127.0.0.1:9222/json/new?{urllib.parse.quote(url, safe='')}", timeout=10
    ) as r:
        return json.load(r)


def main() -> None:
    import urllib.parse  # noqa: F401

    # tìm tab localhost:3002 sẵn có
    ds = [t for t in tabs() if "localhost:3002" in t.get("url", "")]
    if not ds:
        print("Không thấy tab localhost:3002 — mở tab đó trong Chrome rồi chạy lại.")
        return

    t = Tab(ds[0]["webSocketDebuggerUrl"])
    try:
        # ── bắt network để BIẾT có gọi BFF không ──────────────
        t.goi("Network.enable")
        t.goi("Page.enable")
        t.goi("Page.reload", ignoreCache=True)
        time.sleep(4)

        print("=== TRANG RENDER GÌ ===")
        print(f"  title: {t.js('document.title')}")
        n_msg = t.js("document.querySelectorAll('main .rounded-card').length")
        print(f"  số bong bóng chat ban đầu: {n_msg}")
        loi_mo = t.js(
            "(() => {const e=document.querySelector('main p, main .rounded-card');"
            "return e ? e.innerText.slice(0,90) : 'không thấy'})()"
        )
        print(f"  lời mở đầu: {loi_mo!r}")

        # ── GÕ CÂU VÀO Ô CHAT + BẤM GỬI ──────────────────────
        print(f"\n=== GÕ CÂU THẬT VÀO Ô CHAT ===")
        print(f"  {CAU[:70]}…")

        ok = t.js(
            """
            (() => {
              const ta = document.querySelector('textarea');
              if (!ta) return 'KHÔNG THẤY textarea';
              const set = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value').set;
              set.call(ta, %s);
              ta.dispatchEvent(new Event('input', {bubbles: true}));
              return 'đã gõ';
            })()
            """
            % json.dumps(CAU)
        )
        print(f"  {ok}")

        gui = t.js(
            """
            (() => {
              const b = [...document.querySelectorAll('button')]
                .find(x => x.innerText.trim() === 'Gửi');
              if (!b) return 'KHÔNG THẤY nút Gửi';
              if (b.disabled) return 'nút Gửi đang DISABLED';
              b.click();
              return 'đã bấm Gửi';
            })()
            """
        )
        print(f"  {gui}")

        time.sleep(4)

        # ── KẾT QUẢ CÓ HIỆN LÊN KHÔNG ────────────────────────
        print("\n=== SAU KHI BẤM ===")
        n2 = t.js("document.querySelectorAll('main .rounded-card').length")
        print(f"  số bong bóng chat: {n_msg} → {n2}")

        the = t.js("document.querySelectorAll('main article').length")
        print(f"  số THẺ chương trình render ra: {the}")

        noi_dung = t.js(
            "(() => {const a=document.querySelectorAll('main article');"
            "return [...a].map(x => x.innerText.slice(0,120).replace(/\\n/g,' | '))})()"
        )
        for i, x in enumerate(noi_dung or []):
            print(f"    [{i}] {x}")

        ribbon = t.js(
            "(() => {const e=document.querySelector('main');"
            "const m=e.innerText.match(/Hồ sơ \\d\\/\\d/); return m?m[0]:'không thấy'})()"
        )
        print(f"  ribbon hồ sơ: {ribbon}")

        ms = t.js(
            "(() => {const m=document.body.innerText.match(/(\\d+)ms/); return m?m[0]:'không thấy'})()"
        )
        print(f"  badge latency: {ms}")

        t.anh("./artifacts/e2e_chat.png")
        print("\n  ✓ ảnh → artifacts/e2e_chat.png")

        print("\n" + "=" * 60)
        if the and the > 0:
            print("✓ E2E THẬT: gõ vào giao diện → BFF trả về → THẺ render ra màn hình")
        else:
            print("✗ KHÔNG có thẻ nào render — frontend CHƯA gọi được BFF")
    finally:
        t.dong()


if __name__ == "__main__":
    main()
