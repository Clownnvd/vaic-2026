import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
for k in d["result"]["ket_qua"]:
    if k["huong"] == "ViHallu":
        continue
    print("=" * 72)
    print("###", k["huong"])
    print("=" * 72)
    print((k.get("tom_tat") or "")[:1500])
    for ds in k.get("dataset", []) or []:
        print(f"\n  ── {ds.get('ten')}")
        print(f"     nguồn   : {(ds.get('nguon') or '')[:110]}")
        print(f"     license : {(ds.get('license') or '')[:90]}")
        print(f"     dùng?   : {(ds.get('dung_duoc_cho_thi') or '')[:110]}")
        print(f"     hợp?    : {(ds.get('hop_voi_policyradar') or '')[:130]}")
        if ds.get("sota"):
            print(f"     SOTA    : {ds['sota'][:80]}")
    if k.get("canh_bao"):
        print("\n  -- CẢNH BÁO --")
        for x in k["canh_bao"][:4]:
            print(f"     ! {x[:150]}")
    print()
