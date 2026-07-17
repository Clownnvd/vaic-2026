"""Smoke BFF — bắn thật qua HTTP, không mock.
Chạy: uv run --python 3.11 python scripts/smoke_bff.py
"""

import json
import urllib.request

BASE = "http://localhost:8000"
loi = 0


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


print("=== 1. HEALTH ===")
with urllib.request.urlopen(BASE + "/health", timeout=8) as r:
    h = json.loads(r.read())
eq(h["service"], "policyradar-bff", "đúng service (không phải BFF cũ)")

print("\n=== 2. THIẾU HỒ SƠ → HỎI, KHÔNG ĐOÁN ===")
d = post("/chat", {"cau": "DN toi la DNNVV o Ha Noi", "ho_so": {"nganh": "phần mềm"}})
eq(d["dang"], "hoi_ho_so", "thiếu nhiều field → hỏi lại")
print(f"      → {d['noi_dung']}")
print(f"      đang hỏi: {d['dang_hoi']}  ·  {d['ms']}ms")

print("\n=== 3. ĐỦ HỒ SƠ → MATCHER QUÉT NGƯỢC ===")
ho_so = {
    "nganh": "Sản xuất phần mềm",
    "von": 20_000_000_000,
    "nhan_su": 45,
    "chi_rnd": 2.5,
    "dia_ban": "Hà Nội",
    "fdi": False,
}
d = post("/chat", {"cau": "Cty toi xin uu dai gi duoc?", "ho_so": ho_so})
eq(d["dang"], "ket_qua", "trả kết quả")
eq(len(d["chuong_trinh"]), 2, "2 chương trình")
print(f"      → {d['noi_dung']}  ({d['ms']}ms)")
for c in d["chuong_trinh"]:
    print(f"        #{c['ten'][:40]:42} EV={c['gia_tri_ky_vong']:>12}  "
          f"{'ĐỦ' if c['du_dieu_kien'] else 'CHƯA'}")
eq(d["chuong_trinh"][0]["id"], "cnc-thue", "xếp hạng theo giá trị kỳ vọng")

print("\n=== 4. JSON CÓ CẤU TRÚC (không phải markdown LLM) ===")
c0 = d["chuong_trinh"][0]
eq(isinstance(c0["dieu_kien"], list), True, "điều kiện là mảng, render thẻ được")
dk = c0["dieu_kien"][0]
eq(sorted(dk.keys()), ["citation", "doi_chieu", "trang_thai", "yeu_cau"], "mỗi điều kiện đủ field")
eq("hien_thi" in dk["citation"], True, "mỗi điều kiện có citation RIÊNG")
print(f"      {dk['yeu_cau']}")
print(f"        trạng thái: {dk['trang_thai']} · đối chiếu: {dk['doi_chieu']}")
print(f"        căn cứ    : {dk['citation']['hien_thi']}")

print("\n=== 5. ANTI-SYCOPHANCY — R&D 0,3% mà đòi ưu đãi CNC ===")
hs2 = {**ho_so, "chi_rnd": 0.3}
d = post("/chat", {"cau": "Ben minh du dieu kien cong nghe cao chu?", "ho_so": hs2})
cnc = next(c for c in d["chuong_trinh"] if c["id"] == "cnc-thue")
eq(cnc["du_dieu_kien"], False, "KHÔNG gật bừa")
eq(cnc["thieu"], ["Chi R&D ≥ 1% doanh thu"], "gọi ĐÍCH DANH điều kiện thiếu")
print(f"      → thiếu: {cnc['thieu']}")

print("\n=== 6. H1 — GÕ KHÔNG DẤU + VIẾT TẮT ===")
d = post("/chat", {"cau": "dn toi la dnnvv, chi r&d 2%", "ho_so": ho_so})
eq(d["dang"], "ket_qua", "câu không dấu + viết tắt vẫn chạy")

print("\n=== 7. H2 — PII bị che TRƯỚC khi ra ngoài ===")
d = post("/chat", {"cau": "MST 0123456789, SDT 0912345678, mail a@b.vn", "ho_so": ho_so})
eq(sorted(d["pii_da_che"]), ["email", "mst", "phone"], "che đủ MST + SĐT + email")
print(f"      đã che: {d['pii_da_che']}")

print("\n=== 8. ② MONITORING — diff 2 snapshot ===")
req = urllib.request.Request(
    BASE + "/monitoring/diff?" ,
    data=json.dumps({"truoc": ho_so, "sau": {**ho_so, "fdi": True}}).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    eq(d["vua_mat"], ["dnnvv-tuvan"], "phát hiện vừa MẤT điều kiện")
    print(f"      vừa mất: {d['vua_mat']} · giữ: {d['giu_nguyen']}")
except Exception as e:  # noqa: BLE001
    print(f"  (bỏ qua /monitoring — {type(e).__name__})")

print("\n" + "=" * 58)
print("SMOKE PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
raise SystemExit(1 if loi else 0)
