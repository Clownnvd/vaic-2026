"""CRON giám sát ② — chạy định kỳ (vd hằng ngày) để cập nhật hiệu lực.

Khác quet_hieu_luc.py (quét 1 lần): script này
  1. Đọc snapshot cũ (giam_sat_quet.json).
  2. Quét MỚI (fresh, không cache) một lô: (a) mọi VB đang theo dõi (bắt đổi
     trạng thái) + (b) một lô XOAY VÒNG (rolling) VB chưa quét → sau vài lần
     phủ hết kho, không quét mù 2.669 VB mỗi ngày.
  3. DIFF: VB nào 'còn → hết hiệu lực' kể từ lần trước = VỪA CHẾT → cảnh báo.
  4. Ghi lại snapshot + nhật ký thay đổi (giam_sat_thay_doi.json).

Lịch chạy: cron trên Railway/host, vd 02:00 mỗi ngày:
  0 2 * * *  cd /app && python scripts/cron_giam_sat.py --lo 300
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, ".")
from matcher.luat_index import LuatIndex  # noqa: E402
from vbpl.api import tra_hieu_luc  # noqa: E402

SNAP = Path("./data/giam_sat_quet.json")
THAYDOI = Path("./data/giam_sat_thay_doi.json")
CURSOR = Path("./data/giam_sat_cursor.txt")


def _nap_snapshot() -> dict:
    if not SNAP.exists():
        return {}
    try:
        return {r["item_id"]: r for r in json.loads(SNAP.read_text(encoding="utf-8"))}
    except Exception:  # noqa: BLE001
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=int, default=300, help="số VB mới quét thêm mỗi lần (rolling)")
    args = ap.parse_args()

    cu = _nap_snapshot()
    print(f"snapshot cũ: {len(cu)} văn bản đang theo dõi")

    idx = LuatIndex()
    ung = [v for v in idx.ds if v.item_id and v.item_id.isdigit()]
    ids_all = [v.item_id for v in ung]
    meta = {v.item_id: v for v in ung}

    # rolling cursor
    cur = int(CURSOR.read_text().strip()) if CURSOR.exists() else 0
    moi = ids_all[cur: cur + args.lo]
    cur_moi = (cur + args.lo) % max(len(ids_all), 1)

    # lô quét = VB đang theo dõi (bắt đổi) ∪ lô mới (rolling)
    can_quet = list(dict.fromkeys(list(cu.keys()) + moi))
    print(f"quét fresh {len(can_quet)} VB (theo dõi {len(cu)} + mới {len(moi)}, cursor→{cur_moi})…")

    def lam(iid):
        hl = tra_hieu_luc(iid, dung_cache=False)  # FRESH — để bắt đổi trạng thái
        return iid, hl

    moi_snap = dict(cu)
    thay_doi = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(lam, i): i for i in can_quet}
        for fu in as_completed(futs):
            iid, hl = fu.result()
            if hl.loi:
                continue
            v = meta.get(iid)
            rec = {
                "item_id": iid, "so_hieu": v.so_hieu if v else cu.get(iid, {}).get("so_hieu"),
                "tieu_de": (v.tieu_de[:80] if v else cu.get(iid, {}).get("tieu_de")),
                "nam": v.nam if v else cu.get(iid, {}).get("nam"),
                "co_quan": v.co_quan if v else cu.get(iid, {}).get("co_quan"),
                "url": v.nguon_url if v else cu.get(iid, {}).get("url"),
                "ma": hl.ma, "nhan": hl.nhan, "con_hieu_luc": hl.con_hieu_luc,
                "so_quan_he": hl.so_quan_he, "loi": None,
            }
            # DIFF: còn → hết = vừa chết
            truoc = cu.get(iid, {}).get("con_hieu_luc")
            if truoc is True and hl.con_hieu_luc is False:
                thay_doi.append({**rec, "tu": "còn hiệu lực", "sang": hl.nhan})
            moi_snap[iid] = rec

    Path("./data").mkdir(exist_ok=True)
    SNAP.write_text(json.dumps(list(moi_snap.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    CURSOR.write_text(str(cur_moi), encoding="utf-8")

    n_het = sum(1 for r in moi_snap.values() if r.get("con_hieu_luc") is False)
    n_con = sum(1 for r in moi_snap.values() if r.get("con_hieu_luc") is True)
    print(f"\n=== CẬP NHẬT XONG {datetime.now(timezone.utc).isoformat(timespec='seconds')} ===")
    print(f"  snapshot: {len(moi_snap)} VB  ({n_het} hết / {n_con} còn)")
    print(f"  VỪA ĐỔI (còn→hết) lần này: {len(thay_doi)}")
    for r in thay_doi[:10]:
        print(f"    ⛔ {r['so_hieu']:22} {r['tieu_de'][:50]}")

    # ghi nhật ký thay đổi (giữ 200 gần nhất)
    lich_su = []
    if THAYDOI.exists():
        try:
            lich_su = json.loads(THAYDOI.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            lich_su = []
    if thay_doi:
        lich_su.insert(0, {
            "luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "so_thay_doi": len(thay_doi), "vb": thay_doi,
        })
    THAYDOI.write_text(json.dumps(lich_su[:200], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  → {SNAP}  +  {THAYDOI}")


if __name__ == "__main__":
    main()
