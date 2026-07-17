"""Soi các bộ ĐÚNG DOMAIN doanh nghiệp — tải được ngay, không phải xin.

Chạy: uv run --python 3.11 --with datasets python scripts/soi_luat_dn.py
"""

from __future__ import annotations

from collections import Counter

BO = [
    ("AlexNgV/vietnamese-enterprise-law-qa", "LUẬT DOANH NGHIỆP — đúng domain P1"),
    ("Monmoonluna/vbpl-vn-legal-corpus", "vbpl.vn đã chunk sẵn cho RAG + graph"),
    ("NamSyntax/Vietnamese-Legal-QA-RAG", "QA pháp luật cho RAG"),
    ("duyet/vietnamese-legal-instruct", "instruct pháp luật"),
]

for ten, vi_sao in BO:
    print("=" * 74)
    print(f"### {ten}")
    print(f"    {vi_sao}")
    print("=" * 74)
    try:
        from datasets import load_dataset

        ds = load_dataset(ten)
        for k, v in ds.items():
            print(f"  {k:10} {len(v):7,} dòng")

        k0 = list(ds.keys())[0]
        cot = ds[k0].column_names
        print(f"\n  cột: {cot}")

        # có nhãn đúng/sai không — đây là thứ QUYẾT ĐỊNH dùng được hay không
        co_nhan = [c for c in cot if any(
            t in c.lower() for t in ("label", "nhan", "verdict", "answer_type", "is_", "correct")
        )]
        print(f"  cột nhãn: {co_nhan or '❌ KHÔNG CÓ — không đo được guard'}")
        for c in co_nhan:
            try:
                print(f"    {c}: {dict(Counter(ds[k0][c])) if len(set(ds[k0][c])) < 12 else '(nhiều giá trị)'}")
            except Exception:  # noqa: BLE001
                pass

        print(f"\n  --- MẪU ---")
        r = ds[k0][0]
        for c in cot[:7]:
            print(f"    {c:16}: {str(r[c])[:100]}")
    except Exception as e:  # noqa: BLE001
        print(f"  LỖI: {type(e).__name__}: {str(e)[:110]}")
    print("\n")
