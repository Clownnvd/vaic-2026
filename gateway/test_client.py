"""Test cổng LLM — ràng buộc J + I2.
Chạy: uv run --python 3.11 python gateway/test_client.py
"""

import os
import sys

sys.path.insert(0, ".")
from gateway.client import (  # noqa: E402
    HOST_CHO_PHEP,
    ViPhamEgress,
    che_do,
    goi_llm,
    kiem_egress,
    resolve_model,
)

loi = 0


def eq(thuc, mong, nhan):
    global loi
    ok = thuc == mong
    if not ok:
        loi += 1
    print(f"  {'✓' if ok else '✗'} {nhan}")
    if not ok:
        print(f"      được : {thuc!r}\n      mong : {mong!r}")


print("=== J: EGRESS ALLOWLIST ===")
for u in ("https://api.openai.com/v1", "https://mkp-api.fptcloud.com/v1", "http://localhost:4000"):
    try:
        kiem_egress(u)
        eq(True, True, f"cho qua host hợp lệ: {u}")
    except ViPhamEgress:
        eq(False, True, f"cho qua host hợp lệ: {u}")

for u in ("https://evil.example.com/v1", "https://api.deepseek.com/v1"):
    try:
        kiem_egress(u)
        eq(False, True, f"CHẶN host lạ: {u}")
    except ViPhamEgress as e:
        eq(True, True, f"CHẶN host lạ: {u}")
        print(f"      → {str(e)[:78]}…")

print("\n=== J: MẶC ĐỊNH PHẢI QUA CỔNG ===")
os.environ.pop("USE_GATEWAY", None)
os.environ.pop("USE_TEST_MODEL", None)
eq(che_do(), "gateway", "không set gì → mặc định 'gateway' (J là ràng buộc cứng)")

m, base, mode = resolve_model("task-deep")
eq(mode, "gateway", "resolve_model → qua proxy")
eq(base, "http://localhost:4000/v1", "trỏ vào LiteLLM proxy :4000")

print("\n=== I2: COMPLEXITY ROUTING → chuỗi fallback ===")
for t in ("task-deep", "task-fast", "task-vn"):
    m, base, _ = resolve_model(t)
    eq(m, t, f"{t} → model_name '{t}' (fallback cấu hình trong litellm.config)")

print("\n=== TEST MODE: không gọi mạng, 0 đồng ===")
os.environ["USE_TEST_MODEL"] = "1"
eq(che_do(), "test", "USE_TEST_MODEL=1 → test")
kq = goi_llm("khách hỏi gì đó", muc_dich="smoke.test")
eq("[TestModel]" in kq, True, "TestModel trả lời, không chạm mạng")

print("\n=== J: MỌI CALL ĐỀU ĐỂ LẠI VẾT ===")
from pathlib import Path  # noqa: E402

so = Path("./artifacts/audit/llm_calls.jsonl")
eq(so.exists(), True, "sổ audit được tạo")
n = len(so.read_text(encoding="utf-8").strip().splitlines())
print(f"      {n} bản ghi trong {so}")
eq(n >= 1, True, "call vừa rồi đã có vết")

print("\n" + "=" * 58)
print("TẤT CẢ PASS ✓" if loi == 0 else f"{loi} TEST HỎNG ✗")
sys.exit(1 if loi else 0)
