"""Soi corpus flagship → trả lời 3 câu quyết định trước khi viết corrupter.

1. Có field HIỆU LỰC (còn/hết) không? → quyết định phép nhiễu #7 sống hay chết.
2. Điều/khoản dài bao nhiêu? → chốt max_len 128 hay 256.
3. structure_json có cây điều→khoản→điểm dùng được không? → nền của lookup_doc().

Chạy: uv run --python 3.11 --with pyarrow python scripts/inspect_corpus.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

F = Path("./data/splits/train.parquet")


def phan_vi(xs: list[int], p: float) -> int:
    if not xs:
        return 0
    s = sorted(xs)
    return s[min(int(len(s) * p), len(s) - 1)]


def main() -> None:
    tbl = pq.read_table(F)
    print(f"train: {tbl.num_rows:,} văn bản\n")

    # ── 1. HIỆU LỰC ────────────────────────────────────────────────
    print("=" * 62)
    print("1. CÓ FIELD HIỆU LỰC KHÔNG?")
    print("=" * 62)
    cot = tbl.column_names
    print(f"  Cột hiện có: {', '.join(cot)}\n")

    nghi = [c for c in cot if re.search(r"hieu|luc|status|state|valid|expire|replac", c, re.I)]
    print(f"  Cột tên giống 'hiệu lực': {nghi or 'KHÔNG CÓ'}")

    # soi structure_json xem có nhét status bên trong không
    khoa = Counter()
    for s in tbl["structure_json"][:200].to_pylist():
        if not s:
            continue
        try:
            d = json.loads(s)
        except Exception:  # noqa: BLE001
            continue
        khoa.update(d.keys())
        if isinstance(d.get("meta"), dict):
            khoa.update(f"meta.{k}" for k in d["meta"])
    print(f"\n  Khoá trong structure_json (200 mẫu đầu):")
    for k, v in khoa.most_common(20):
        print(f"    {k:28} {v}")

    co_hl = any(re.search(r"hieu_luc|status|expire|replac", k, re.I) for k in khoa) or nghi
    print(f"\n  ⇒ KẾT LUẬN: {'CÓ dấu hiệu hiệu lực' if co_hl else 'KHÔNG CÓ field hiệu lực'}")
    if not co_hl:
        print("     → PHÉP NHIỄU #7 (trích văn bản hết hiệu lực) KHÔNG làm được từ dump.")
        print("     → Phải join API vbpl.vn, hoặc BỎ #7 và nói thẳng với giám khảo.")

    # ── 2. ĐỘ DÀI ──────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("2. ĐỘ DÀI — chốt max_len")
    print("=" * 62)
    md = [len(x) for x in tbl["markdown"].to_pylist() if x]
    print(f"  markdown (ký tự): p50={phan_vi(md, .5):,}  p90={phan_vi(md, .9):,}  max={max(md):,}")

    # bóc từng khoản từ structure_json → đây mới là đơn vị đưa vào NLI
    dai_khoan: list[int] = []
    mau_khoan: list[str] = []

    def di(node, depth=0):
        if isinstance(node, dict):
            t = node.get("text") or node.get("content") or ""
            if isinstance(t, str) and 20 < len(t) < 20000:
                dai_khoan.append(len(t))
                if len(mau_khoan) < 3:
                    mau_khoan.append(t)
            for v in node.values():
                di(v, depth + 1)
        elif isinstance(node, list):
            for v in node:
                di(v, depth + 1)

    for s in tbl["structure_json"][:400].to_pylist():
        if s:
            try:
                di(json.loads(s))
            except Exception:  # noqa: BLE001
                pass

    if dai_khoan:
        print(f"\n  Đơn vị text trong structure_json (n={len(dai_khoan):,}):")
        print(
            f"    ký tự : p50={phan_vi(dai_khoan, .5)}  p75={phan_vi(dai_khoan, .75)}"
            f"  p90={phan_vi(dai_khoan, .9)}  p99={phan_vi(dai_khoan, .99)}"
        )
        # ước lượng token: tiếng Việt ~1 token ≈ 3 ký tự với PhoBERT (word-piece)
        uoc = [d / 3 for d in dai_khoan]
        p90, p99 = phan_vi([int(x) for x in uoc], .9), phan_vi([int(x) for x in uoc], .99)
        qua128 = sum(1 for x in uoc if x > 128) / len(uoc) * 100
        qua256 = sum(1 for x in uoc if x > 256) / len(uoc) * 100
        print(f"    ~token: p90≈{p90}  p99≈{p99}   (ước lượng 1 token ≈ 3 ký tự)")
        print(f"\n    Vượt 128 token: {qua128:.1f}%   |   Vượt 256 token: {qua256:.1f}%")
        print(
            f"    ⇒ CHỐT max_len = {256 if qua128 > 20 else 128}"
            f" ({'>20% bị cắt ở 128' if qua128 > 20 else 'cắt ở 128 chấp nhận được'})"
        )
        print("\n  Mẫu:")
        for m in mau_khoan[:2]:
            print(f"    « {m[:150].replace(chr(10), ' ')}… »")
    else:
        print("  ⚠ Không bóc được text từ structure_json — xem cấu trúc thật bên dưới.")
        s = tbl["structure_json"][0].as_py()
        print(f"  Mẫu thô: {s[:600]}")

    # ── 3. SỐ HIỆU VĂN BẢN ─────────────────────────────────────────
    print("\n" + "=" * 62)
    print("3. SỐ HIỆU VĂN BẢN — nền của lookup_doc()")
    print("=" * 62)
    dn = [x for x in tbl["doc_number_str"][:20].to_pylist()]
    print("  Mẫu doc_number_str:")
    for x in dn[:8]:
        print(f"    {x}")
    rong = sum(1 for x in tbl["doc_number_str"].to_pylist() if not x)
    print(f"\n  Rỗng: {rong}/{tbl.num_rows}")
    print("\n  issuing_authority hay gặp:")
    for k, v in Counter(tbl["issuing_authority"].to_pylist()).most_common(8):
        print(f"    {str(k)[:44]:46} {v}")


if __name__ == "__main__":
    main()
