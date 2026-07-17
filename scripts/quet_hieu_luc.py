"""Quét hiệu lực THẬT trên nhiều văn bản corpus (không chỉ 2 flagship) để
GIÁM SÁT bắt được ca HẾT HIỆU LỰC / bị THAY THẾ / SỬA ĐỔI — chứng minh yêu cầu ②.

Ưu tiên văn bản CŨ (dễ hết hiệu lực). Query vbpl.vn (public), cache đĩa.
Chạy: uv run --python 3.11 --with pyarrow python scripts/quet_hieu_luc.py --n 80
"""
from __future__ import annotations
import argparse, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, ".")
from matcher.luat_index import LuatIndex  # noqa: E402
from vbpl.api import tra_hieu_luc  # noqa: E402

OUT = Path("./data/giam_sat_quet.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=80, help="số văn bản quét")
    ap.add_argument("--tu-nam", type=int, default=2010)
    ap.add_argument("--den-nam", type=int, default=2021, help="ưu tiên VB cũ ≤ năm này")
    args = ap.parse_args()

    idx = LuatIndex()
    print(f"corpus: {len(idx.ds)} văn bản")

    # lấy mẫu RẢI ĐỀU theo năm — để dashboard thực tế (VB mới phần lớn còn
    # hiệu lực, VB cũ hết). Không dồn hết vào 1 năm.
    ung = [v for v in idx.ds if v.item_id and v.item_id.isdigit()
           and v.nam and args.tu_nam <= v.nam <= args.den_nam]
    theo_nam: dict[int, list] = {}
    for v in ung:
        theo_nam.setdefault(v.nam, []).append(v)
    nams = sorted(theo_nam)
    quota = max(1, args.n // max(len(nams), 1))
    mau = []
    for nm in nams:
        ds = theo_nam[nm]
        mau += ds[: quota + 4]  # vài cái mỗi năm
    mau = mau[: args.n]
    print(f"quét {len(mau)} VB rải {nams[0]}–{nams[-1]} (~{quota}/năm)…\n")

    ket = []
    t0 = time.time()

    def lam(v):
        hl = tra_hieu_luc(v.item_id, dung_cache=True)  # cache miss → gọi API + lưu
        return v, hl

    het, thay_doi, con, loi = [], [], 0, 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(lam, v): v for v in mau}
        for i, fu in enumerate(as_completed(futs), 1):
            v, hl = fu.result()
            rec = {"item_id": v.item_id, "so_hieu": v.so_hieu, "tieu_de": v.tieu_de[:80],
                   "nam": v.nam, "co_quan": v.co_quan, "url": v.nguon_url,
                   "ma": hl.ma, "nhan": hl.nhan, "con_hieu_luc": hl.con_hieu_luc,
                   "so_quan_he": hl.so_quan_he, "loi": hl.loi}
            ket.append(rec)
            if hl.loi:
                loi += 1
            elif hl.con_hieu_luc is False:
                het.append(rec)
            elif hl.so_quan_he and hl.so_quan_he > 0:
                thay_doi.append(rec)
                if hl.con_hieu_luc:
                    con += 1
            elif hl.con_hieu_luc:
                con += 1
            if i % 10 == 0:
                print(f"  …{i}/{len(mau)}  ({time.time()-t0:.0f}s)  hết={len(het)} có-quan-hệ={len(thay_doi)}")

    print(f"\n=== KẾT QUẢ ({time.time()-t0:.0f}s) ===")
    print(f"  HẾT hiệu lực (HHL)      : {len(het)}")
    print(f"  Còn hiệu lực + có quan hệ: {len(thay_doi)}")
    print(f"  Còn hiệu lực (thuần)    : {con}")
    print(f"  Lỗi/chưa xác định       : {loi}")

    print("\n--- VĂN BẢN ĐÃ HẾT HIỆU LỰC (mẫu) ---")
    for r in het[:12]:
        print(f"  ⛔ {r['so_hieu']:22} {r['nam']}  {r['nhan']:28} {r['tieu_de'][:50]}")
    print("\n--- CÒN HIỆU LỰC NHƯNG CÓ VB SỬA ĐỔI/THAY THẾ (mẫu) ---")
    for r in sorted(thay_doi, key=lambda x: -x["so_quan_he"])[:8]:
        print(f"  ✎ {r['so_hieu']:22} {r['nam']}  {r['so_quan_he']} quan hệ  {r['tieu_de'][:44]}")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ lưu {OUT} ({len(ket)} VB)")


if __name__ == "__main__":
    main()
