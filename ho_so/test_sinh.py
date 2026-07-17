"""Test ③ soạn hồ sơ.
Chạy: uv run --python 3.11 python ho_so/test_sinh.py
"""

import sys

sys.path.insert(0, ".")
from ho_so.mau import TAT_CA  # noqa: E402
from ho_so.sinh import checklist, render_text, sinh_khung  # noqa: E402

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


HO_SO = {
    "ten_to_chuc": "Công ty CP Công nghệ ABC",
    "mst": "0123456789",
    "dia_chi": "12 Nguyễn Huệ, Hà Nội",
    "nganh": "Sản xuất phần mềm",
    "von": 20_000_000_000,
    "nhan_su": 45,
    "chi_rnd": 2.5,
    "fdi": False,
}

print("=== KỶ LUẬT: mọi mẫu phải có căn cứ TRONG CORPUS ===")
CO_TRONG_CORPUS = {
    "44/2025/TT-BKHCN", "80/2021/NĐ-CP", "06/2022/TT-BKHĐT",
    "80/2021/TT-BTC", "267/2025/NĐ-CP", "320/2025/NĐ-CP",
    "36/2025/TT-BKHCN", "38/2025/TT-BKHCN", "13/2019/NĐ-CP",
}
ngoai = [m.ma for m in TAT_CA if m.can_cu not in CO_TRONG_CORPUS]
eq(ngoai, [], "KHÔNG mẫu nào trích văn bản ngoài corpus")
print(f"      {len(TAT_CA)} mẫu, căn cứ: {sorted({m.can_cu for m in TAT_CA})}")

print("\n=== STRUCTURE-THEN-FILL: AI không được gõ ô nào ===")
k = sinh_khung(TAT_CA[0], HO_SO)
eq(any(o.ai_duoc_go for o in k.o), False, "KHÔNG ô nào cho AI gõ")
eq(all(o.nguon in ("ho_so", "corpus", "nguoi") for o in k.o), True, "mọi ô có nguồn rõ ràng")

print("\n=== CODE điền từ hồ sơ, số CHÍNH XÁC ===")
k = sinh_khung(next(m for m in TAT_CA if m.ma == "TK-DNNVV"), HO_SO)
o_von = next(o for o in k.o if o.khoa == "von")
eq(o_von.gia_tri, "20.000.000.000 đ", "vốn: CODE format, dấu chấm ngăn nghìn")
eq(o_von.nguon, "ho_so", "nguồn = hồ sơ DN, không phải AI")
o_ns = next(o for o in k.o if o.khoa == "nhan_su")
eq(o_ns.gia_tri, "45 người", "nhân sự")

print("\n=== WRITE-GATE: hồ sơ là hành động GHI ===")
eq(k.requires_approval, True, "requires_approval=True — bản nháp chờ duyệt")

print("\n=== CHECKLIST 'còn thiếu gì' ===")
ks = checklist("dnnvv-tuvan", HO_SO)
eq(len(ks), 2, "chương trình DNNVV → 2 mẫu")
for x in ks:
    print(f"      {x.mau.ma:12} đầy {x.phan_tram_day:.0%}  thiếu: {x.thieu or '—'}")
eq(ks[0].thieu, ["Nội dung hỗ trợ đề xuất"], "nêu ĐÍCH DANH ô còn thiếu")

print("\n=== HỒ SƠ THIẾU FIELD → không bịa, để trống ===")
k2 = sinh_khung(next(m for m in TAT_CA if m.ma == "BM-07"), {"ten_to_chuc": "Cty ABC"})
o_rnd = next(o for o in k2.o if o.khoa == "chi_rnd")
eq(o_rnd.gia_tri, None, "thiếu chi_rnd → để TRỐNG, không đoán")
eq("Tỷ lệ chi cho R&D (% doanh thu)" in k2.thieu, True, "báo thiếu đích danh")

print("\n=== KHUNG HỒ SƠ XUẤT RA ===")
k3 = sinh_khung(next(m for m in TAT_CA if m.ma == "BM-03"), HO_SO)
print("      " + render_text(k3).replace("\n", "\n      "))

print("\n" + "=" * 58)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
