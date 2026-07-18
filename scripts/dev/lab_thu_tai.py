"""Chạy TRÊN LAB — tải PhoBERT được THẬT không?

curl trả 307 chỉ nghĩa là "có redirect", KHÔNG chứng minh tải được file.
Cache HF trống sau lần chạy trước ⇒ nghi lab không ra được CDN của HuggingFace.
Thử tải THẬT, đo thời gian, và bắt lỗi cho rõ.
"""

import subprocess
import time


def sh(c: str, cho: int = 240) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho)
    return (r.stdout + r.stderr).strip()


print("1. HEAD tới file thật (theo redirect):")
print("  ", sh("curl -sSL -o /dev/null -w 'http=%{http_code} bytes=%{size_download} time=%{time_total}s' "
              "-m 60 https://huggingface.co/vinai/phobert-base/resolve/main/config.json"))

print("\n2. Tải config.json ra file:")
print("  ", sh("curl -sSL -m 60 -o /tmp/cfg.json "
              "https://huggingface.co/vinai/phobert-base/resolve/main/config.json; "
              "ls -l /tmp/cfg.json 2>&1; head -c 120 /tmp/cfg.json 2>&1"))

print("\n3. Tải bằng chính thư viện HF (đường mà transformers dùng):")
t0 = time.time()
try:
    from huggingface_hub import hf_hub_download

    p = hf_hub_download("vinai/phobert-base", "config.json")
    print(f"   ✓ {p}  ({time.time()-t0:.1f}s)")
except Exception as e:  # noqa: BLE001
    print(f"   ✗ {type(e).__name__}: {str(e)[:200]}")

print("\n4. Tải TRỌNG SỐ (file to ~540MB — đây mới là phép thử thật):")
t0 = time.time()
try:
    from transformers import AutoModelForSequenceClassification

    m = AutoModelForSequenceClassification.from_pretrained("vinai/phobert-base", num_labels=2)
    n = sum(p.numel() for p in m.parameters())
    print(f"   ✓ nạp xong {n/1e6:.0f}M tham số  ({time.time()-t0:.0f}s)")
except Exception as e:  # noqa: BLE001
    print(f"   ✗ {type(e).__name__}: {str(e)[:300]}")

print("\n5. Proxy / chặn mạng?")
print("  ", sh("env | grep -i proxy || echo '(không có biến proxy)'"))
