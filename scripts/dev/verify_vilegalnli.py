"""Verify ViLegalNLI — bộ ĐÚNG DOMAIN, Apache 2.0, không phải xin.

Agent bao "chua phat hanh". Quet HF API thi thay: ntphuc149/ViLegalNLI, apache-2.0.
Paper viet "link se cap nhat sau khi bai duoc nhan" — thuc te DA phat hanh roi.
=> Hoi thang API hon han doc paper.

Da hoc tu vu ViWikiFC (agent xep #1, thuc te README tra 401) -> phai tu verify.

Chay: uv run --python 3.11 --with datasets python scripts/verify_vilegalnli.py
"""

from __future__ import annotations

import json
import urllib.request
from collections import Counter


def api(path: str):
    req = urllib.request.Request(
        f"https://huggingface.co/api/{path}", headers={"User-Agent": "policyradar/0.1"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


for ten in ("ntphuc149/ViLegalNLI", "ntphuc149/ViLegalMCQ", "Monmoonluna/vbpl-vn-legal-corpus"):
    print("=" * 70)
    print(f"### {ten}")
    print("=" * 70)
    try:
        d = api(f"datasets/{ten}")
        cd = d.get("cardData") or {}
        print(f"  license   : {cd.get('license') or 'KHONG GHI'}")
        print(f"  tac gia   : {d.get('author')}")
        print(f"  tai/thang : {d.get('downloads', 0):,}   likes: {d.get('likes', 0)}")
        print(f"  cap nhat  : {(d.get('lastModified') or '')[:10]}")
        files = [f["rfilename"] for f in d.get("siblings", [])]
        print(f"  file      : {files[:6]}")

        # doc README that -> 401 = gated
        try:
            req = urllib.request.Request(
                f"https://huggingface.co/datasets/{ten}/raw/main/README.md",
                headers={"User-Agent": "policyradar/0.1"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                txt = r.read().decode("utf-8", "ignore")
            print(f"  README    : DOC DUOC ({len(txt)} ky tu)")
            print("\n  --- 900 ky tu dau ---")
            print("  " + txt[:900].replace("\n", "\n  "))
        except Exception as e:  # noqa: BLE001
            print(f"  README    : LOI {type(e).__name__} — co the bi GATED")
    except Exception as e:  # noqa: BLE001
        print(f"  LOI: {type(e).__name__}: {str(e)[:80]}")
    print("\n")

# tai thu ViLegalNLI
print("=" * 70)
print("TAI THU ntphuc149/ViLegalNLI")
print("=" * 70)
try:
    from datasets import load_dataset

    ds = load_dataset("ntphuc149/ViLegalNLI")
    for k, v in ds.items():
        print(f"  {k:8} {len(v):6,} dong")
    cot = ds[list(ds.keys())[0]].column_names
    print(f"\n  cot: {cot}")

    k0 = list(ds.keys())[0]
    for c in cot:
        if "label" in c.lower():
            print(f"  nhan {c}: {dict(Counter(ds[k0][c]))}")

    print("\n  --- MAU 1 DONG ---")
    r = ds[k0][0]
    for c in cot:
        print(f"    {c:14}: {str(r[c])[:110]}")
except Exception as e:  # noqa: BLE001
    print(f"  LOI TAI: {type(e).__name__}: {str(e)[:140]}")
