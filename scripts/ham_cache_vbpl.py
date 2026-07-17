"""Hâm cache hiệu lực vbpl.vn cho các văn bản flagship — chạy TRƯỚC demo.

API vbpl chậm (vài giây/văn bản). Gọi lúc /chat thì demo đơ. Nên hâm cache
sẵn ở đây; BFF chỉ đọc cache (mili-giây). Cache nằm ở data/cache_vbpl/.

Lấy doc_id từ chính KHO (không hardcode) — kho đổi thì đây theo.

Chạy: uv run --python 3.11 python scripts/ham_cache_vbpl.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")
from matcher.kho_mau import KHO  # noqa: E402
from vbpl.api import quan_he, tra_hieu_luc  # noqa: E402


def main() -> None:
    ids: dict[str, str] = {}
    for ct in KHO:
        for c in [ct.citation_chinh] + [dk.citation for dk in ct.dieu_kien]:
            if c and c.doc_id:
                ids[c.doc_id] = c.so_vb

    print(f"Hâm cache {len(ids)} văn bản flagship…\n")
    for doc_id, so_vb in ids.items():
        hl = tra_hieu_luc(doc_id, dung_cache=False)  # gọi tươi, ghi cache
        qh = quan_he(doc_id)
        print(f"  {so_vb:18} (item {doc_id})")
        print(f"     mã        : {hl.ma}  ·  {hl.ten}")
        print(f"     còn HL?   : {hl.con_hieu_luc}  →  nhãn '{hl.nhan}'")
        print(f"     quan hệ   : {len(qh)} văn bản (thay thế/sửa đổi/bãi bỏ)")
        if hl.loi:
            print(f"     ⚠ lỗi    : {hl.loi}")
        print()

    print("✓ cache đã hâm — BFF đọc mili-giây, demo không chờ API")


if __name__ == "__main__":
    main()
