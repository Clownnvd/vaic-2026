"""Test khung chat NHIỀU CA qua /chat — happy, meta, browse, fail, edge.
In gọn từng ca: cau → dạng phản hồi + trích 1 phần noi_dung + có citation/chương trình không.
"""
from __future__ import annotations
import json, urllib.request

BFF = "http://127.0.0.1:8000/chat"

# hồ sơ đầy đủ để test ca happy có kết quả
HS_DU = {
    "nganh": "sản xuất phần mềm", "linh_vuc": "nong_lam_thuy_san",
    "von": 20_000_000_000, "doanh_thu": 50_000_000_000,
    "lao_dong_bhxh": 45, "ty_le_dt_khcn": 45, "co_gcn_khcn": True,
}

CA = [
    # nhóm HAPPY
    ("HAPPY", "Bên mình làm phần mềm (công nghiệp) ở Hà Nội, 45 lao động, doanh thu 50 tỷ, vốn 20 tỷ, có giấy chứng nhận DN KH&CN, doanh thu từ sản phẩm KH&CN khoảng 45%", {}),
    ("HAPPY", "Cty thương mại - dịch vụ tại Bắc Ninh, 150 lao động, doanh thu 120 tỷ, vốn 60 tỷ, có vốn FDI", {}),
    ("HAPPY", "doanh nghiệp nhỏ, 15 lao động, doanh thu 8 tỷ, vốn 5 tỷ, nữ làm chủ", {}),
    # nhóm KHÔNG DẤU (parser phải chịu được)
    ("KHONG_DAU", "cong ty phan mem ha noi 45 lao dong doanh thu 50 ty von 20 ty co gcn khcn", {}),
    # nhóm META (bot phải hiểu context, KHÔNG gắn "chưa đủ căn cứ")
    ("META", "xin chào", {}),
    ("META", "bạn là ai", {}),
    ("META", "bạn giúp được gì cho tôi", {}),
    ("META", "cảm ơn nhé", {}),
    # nhóm BROWSE (ý định tra cứu → mời sang Danh sách luật)
    ("BROWSE", "cho tôi xem danh sách các văn bản luật", {}),
    ("BROWSE", "có nghị định nào về thuế không", {}),
    ("BROWSE", "tra cứu luật hỗ trợ doanh nghiệp nhỏ và vừa", {}),
    # nhóm HỎI THIẾU THÔNG TIN (phải hỏi tiếp, không bịa)
    ("THIEU", "công ty tôi ở Hà Nội", {}),
    ("THIEU", "tôi muốn xin hỗ trợ", {}),
    # nhóm NGOÀI PHẠM VI (từ chối lịch sự)
    ("NGOAI", "thời tiết hôm nay thế nào", {}),
    ("NGOAI", "1 + 1 bằng mấy", {}),
    # nhóm EDGE (rác / rỗng / ký tự lạ)
    ("EDGE", "asdfghjkl qwerty", {}),
    ("EDGE", "", {}),
    ("EDGE", "?????", {}),
    ("EDGE", "😀😀😀 chính sách 😀", {}),
    # nhóm CÓ HỒ SƠ SẴN + hỏi cụ thể
    ("CO_HS", "tôi đủ điều kiện gì", HS_DU),
    ("CO_HS", "điều kiện hỗ trợ tư vấn cho doanh nghiệp nhỏ và vừa là gì", HS_DU),
]


def goi(cau: str, ho_so: dict) -> dict:
    body = json.dumps({"cau": cau, "ho_so": ho_so}).encode()
    req = urllib.request.Request(BFF, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> None:
    ket = []
    for i, (nhom, cau, hs) in enumerate(CA, 1):
        try:
            d = goi(cau, hs)
        except Exception as e:  # noqa: BLE001
            print(f"[{i:02d}] {nhom:9} ❌ LỖI: {e}  | cau={cau!r:.50}")
            ket.append({"i": i, "nhom": nhom, "cau": cau, "loi": str(e)})
            continue
        dang = d.get("dang") or d.get("loai") or "?"
        noi = (d.get("noi_dung") or "")[:90].replace("\n", " ")
        n_ct = len(d.get("chuong_trinh") or [])
        n_cit = len(d.get("citations") or [])
        grd = d.get("grounding") or d.get("trang_thai_grounding") or ""
        print(f"[{i:02d}] {nhom:9} dang={dang:12} ct={n_ct} cit={n_cit} grd={grd:14} | {noi}")
        ket.append({"i": i, "nhom": nhom, "cau": cau, "dang": dang, "n_ct": n_ct,
                    "n_cit": n_cit, "grounding": grd, "noi_dung": d.get("noi_dung", "")})
    from pathlib import Path
    Path("./artifacts").mkdir(exist_ok=True)
    Path("./artifacts/test_chat_ket.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {len(ket)} ca, lưu artifacts/test_chat_ket.json")


if __name__ == "__main__":
    main()
