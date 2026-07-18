"""Lái Chrome (CDP) test khung chat trên UI THẬT + chụp từng ca.
Chứng minh: i18n VI↔EN, happy path bung thẻ + guard + citation, meta/browse/edge.
Ảnh lưu ./artifacts/anh/ui_*.png
"""
from __future__ import annotations
import json, time, urllib.request, urllib.parse
from pathlib import Path
import sys
sys.path.insert(0, ".")
from scripts.chrome_cdp import Tab, tabs  # noqa: E402

APP = "http://127.0.0.1:3002/"
OUT = Path("./artifacts/anh")
OUT.mkdir(parents=True, exist_ok=True)
CDP = "http://127.0.0.1:9222"


def tab_moi(url: str) -> Tab:
    """Ưu tiên TÁI DÙNG tab localhost đã hydrate (click mới có handler React).
    Không có thì điều hướng một tab sẵn sang app + chờ hydrate lâu."""
    t0 = next((t for t in tabs() if "localhost:3002" in t.get("url", "")), None)
    if t0:
        return Tab(t0["webSocketDebuggerUrl"])
    # tạo mới rồi chờ lâu cho Turbopack compile+hydrate
    try:
        req = urllib.request.Request(
            f"{CDP}/json/new?{urllib.parse.quote(url, safe=':/?=&')}", method="PUT")
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
        t = Tab(d["webSocketDebuggerUrl"])
    except Exception:
        t0 = next((t for t in tabs() if "fptcloud" in t.get("url", "")), tabs()[0])
        t = Tab(t0["webSocketDebuggerUrl"])
        t.di_toi(url)
    time.sleep(14)  # hydrate lần đầu
    return t


def len_truoc(t: Tab) -> None:
    """Đưa tab lên foreground — tránh captureScreenshot treo trên tab nền."""
    try:
        t.goi("Page.bringToFront")
    except Exception:
        pass


def go_chu(t: Tab, sel_placeholder_chua: str, text: str) -> str:
    """Gõ vào textarea (React-safe) + submit form."""
    js = """
    (() => {
      const ta = document.querySelector('textarea');
      if (!ta) return 'no-textarea';
      const set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
      set.call(ta, %s);
      ta.dispatchEvent(new Event('input',{bubbles:true}));
      // submit: tìm form gần nhất rồi requestSubmit, hoặc bấm nút Send/Gửi
      const form = ta.closest('form');
      if (form) { form.requestSubmit(); return 'submitted'; }
      const btn = [...document.querySelectorAll('button')].find(b=>/gửi|send/i.test(b.innerText||''));
      if (btn) { btn.click(); return 'clicked'; }
      return 'no-submit';
    })()
    """ % json.dumps(text)
    return t.js(js)


def cho_xong(t: Tab, giay: int = 30) -> None:
    """Chờ tới khi hết trạng thái 'đang quét/scanning' (bot trả lời xong)."""
    t0 = time.time()
    while time.time() - t0 < giay:
        txt = t.js("document.body ? document.body.innerText : ''") or ""
        if "Đang quét" not in txt and "Scanning" not in txt:
            # có phản hồi trợ lý chưa? chờ thêm chút cho render
            time.sleep(1.2)
            return
        time.sleep(1)


def shot(t: Tab, ten: str) -> None:
    p = str(OUT / f"ui_{ten}.png")
    t.anh(p)
    print(f"  📸 {ten}")


def lang_hien(t: Tab) -> str:
    """Ngôn ngữ ĐANG hiển thị = text nút toggle ('VI'/'EN') → 'vi'/'en'."""
    tx = t.js("""(() => {
      const b=[...document.querySelectorAll('button')].find(
        x=>(x.getAttribute('aria-label')||'')==='Đổi ngôn ngữ');
      return b ? (b.innerText||'').trim().toLowerCase() : '?';
    })()""") or "?"
    return "en" if "en" in tx else ("vi" if "vi" in tx else "?")


def bam_toggle(t: Tab) -> str:
    return t.js("""(() => {
      const b=[...document.querySelectorAll('button')].find(
        x=>(x.getAttribute('aria-label')||'')==='Đổi ngôn ngữ');
      if(!b) return 'KHONG-THAY-TOGGLE';
      b.click(); return 'clicked';
    })()""")


def dat_lang(t: Tab, lang: str, thu: int = 4) -> str:
    """Bấm toggle tới khi text nút = lang mong muốn (chống chưa hydrate)."""
    for _ in range(thu):
        if lang_hien(t) == lang:
            return lang
        bam_toggle(t)
        time.sleep(1.3)
    return lang_hien(t)


def main() -> None:
    t = tab_moi(APP)
    try:
        len_truoc(t)
        time.sleep(7)  # chờ Turbopack hydrate xong (click mới có handler)
        print("== title:", t.js("document.title"))

        # ép về VI cho xác định (dựa text nút toggle, không reload)
        print("  đặt VI:", dat_lang(t, "vi"))

        # 1) trạng thái đầu — tiếng Việt
        shot(t, "01_vi_khoi_dong")

        # 2) sang English
        print("  đặt EN:", dat_lang(t, "en"))
        time.sleep(1)
        shot(t, "02_en_khoi_dong")

        # 3) mở các trang khác ở EN để chứng minh i18n
        for khung, ten in [("Laws", "03_en_laws"), ("Prepare dossier", "04_en_dossier"), ("Policy monitor", "05_en_monitor")]:
            t.js(f"""(() => {{
              const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==={json.dumps(khung)});
              if(b) b.click(); return b?'ok':'no';
            }})()""")
            time.sleep(2.5)
            shot(t, ten)

        # về English Advisor để test chat
        t.js("""(() => { const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Advisor'); if(b) b.click(); })()""")
        time.sleep(1.5)

        # 4) đổi lại về tiếng Việt cho phần chat (câu trả lời là tiếng Việt)
        dat_lang(t, "vi")

        # 5) CÁC CA CHAT
        cases = [
            ("06_happy", "Bên mình làm phần mềm (công nghiệp) ở Hà Nội, 45 lao động, doanh thu 50 tỷ, vốn 20 tỷ, có giấy chứng nhận DN KH&CN, doanh thu từ sản phẩm KH&CN khoảng 45%"),
            ("07_meta_aila", "bạn là ai"),
            ("08_browse", "cho tôi xem danh sách các văn bản luật"),
            ("09_thieu", "công ty tôi ở Hà Nội"),
            ("10_ngoai", "thời tiết hôm nay thế nào"),
            ("11_edge_rac", "asdfghjkl qwerty ?????"),
        ]
        for ten, cau in cases:
            # tạo cuộc mới cho sạch (nút "Cuộc trò chuyện mới")
            t.js("""(() => { const b=[...document.querySelectorAll('button')].find(x=>/cuộc trò chuyện mới|new chat/i.test(x.innerText||'')); if(b) b.click(); })()""")
            time.sleep(1)
            r = go_chu(t, "", cau)
            print(f"  gửi [{ten}]: {r}")
            cho_xong(t, 30)
            time.sleep(1.5)
            shot(t, ten)

        print("\n→ ảnh ở", OUT)
    finally:
        t.dong()


if __name__ == "__main__":
    main()
