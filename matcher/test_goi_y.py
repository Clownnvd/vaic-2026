"""Test TỪ CHỐI CÓ TRÁCH NHIỆM.
Chạy: uv run --python 3.11 python matcher/test_goi_y.py
"""

import sys

sys.path.insert(0, ".")
from matcher.goi_y_vb import cau_tra_loi, soi_cau  # noqa: E402

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


# giả lập kho — thực tế lấy từ IndexCorpus
KHO = {
    "80/2021/NĐ-CP": "Quy định chi tiết Luật Hỗ trợ doanh nghiệp nhỏ và vừa",
    "13/2019/NĐ-CP": "Về doanh nghiệp khoa học và công nghệ",
    "44/2025/TT-BKHCN": "Quy định quản lý nhiệm vụ khoa học và công nghệ",
    "06/2022/TT-BKHĐT": "Hướng dẫn Nghị định 80/2021",
    "67/2025/NĐ-CP": "Nghị định về một số nội dung khác",
    "320/2025/NĐ-CP": "Quy định chi tiết một số điều",
}

print("=== SỐ ĐÚNG → im lặng, không làm phiền ===")
g = soi_cau("Theo 80/2021/NĐ-CP thì DNNVV được hỗ trợ gì?", KHO)
eq(g, [], "số có thật → không báo gì")

print("\n=== SỐ SAI + CÓ CÁI GẦN ĐÚNG (ca của anh) ===")
g = soi_cau("Luật Thuế TNDN 67/2025 quy định mức ưu đãi bao nhiêu?", KHO)
eq(len(g), 1, "tìm ra 1 chỗ sai")
eq(g[0].raw, "67/2025", "bóc đúng đoạn sai để TÔ ĐỎ")
eq(g[0].bat_dau, 15, "biết vị trí bắt đầu (UI tô đỏ đúng chỗ)")  # 'Luật Thuế TNDN ' = 15 ký tự
eq(g[0].co_goi_y, True, "CÓ gợi ý gần đúng")
eq(g[0].goi_y[0][0], "67/2025/NĐ-CP", "gợi ý đúng: cùng số/năm, khác loại văn bản")
print("\n  Câu trả lời cho người dùng:")
print("      " + cau_tra_loi(g[0]).replace("\n", "\n      "))
print(f"\n  UI tô đỏ đoạn [{g[0].bat_dau}:{g[0].ket_thuc}] = {g[0].raw!r}")
cau = "Luật Thuế TNDN 67/2025 quy định mức ưu đãi bao nhiêu?"
print(f"      {cau[:g[0].bat_dau]}[{g[0].raw}]{cau[g[0].ket_thuc:]}")

print("\n=== SỐ SAI, KHÔNG có gì gần → nói thẳng, KHÔNG bịa ===")
g = soi_cau("Theo 999/2099/NĐ-CP thì sao?", KHO)
eq(len(g), 1, "tìm ra chỗ sai")
eq(g[0].co_goi_y, False, "không có gợi ý → không bịa ra cái gần đúng")
print("      " + cau_tra_loi(g[0]))

print("\n=== GÕ NHẦM 1 KÝ TỰ ===")
g = soi_cau("Theo 80/2022/NĐ-CP", KHO)  # thật là 80/2021
eq(len(g), 1, "bắt được")
if g[0].co_goi_y:
    print(f"      gợi ý: {[s for s, _ in g[0].goi_y]}")
    eq("80/2021/NĐ-CP" in [s for s, _ in g[0].goi_y], True, "gợi ý đúng 80/2021")

print("\n=== NHIỀU SỐ SAI TRONG 1 CÂU ===")
g = soi_cau("So sánh 67/2025 với 143/2025/QH15 xem cái nào lợi hơn", KHO)
eq(len(g), 2, "bắt được CẢ HAI chỗ sai")
print(f"      chỗ sai: {[x.raw for x in g]}")

print("\n" + "=" * 56)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
