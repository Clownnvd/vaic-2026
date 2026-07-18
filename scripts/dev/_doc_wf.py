import json
import sys

f = sys.argv[1]
d = json.load(open(f, encoding="utf-8"))
for k in d["result"]["ket_qua"]:
    if k["mang"] == "MATCHER":
        continue
    print("=" * 68)
    print("###", k["mang"])
    print("=" * 68)
    print((k.get("cau_tra_loi") or "")[:2400])
    if k.get("khong_tim_thay"):
        print("\n-- KHO KHONG CO --")
        for x in k["khong_tim_thay"][:4]:
            print("  *", x[:160])
    print()
