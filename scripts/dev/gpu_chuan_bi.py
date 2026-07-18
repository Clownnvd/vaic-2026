"""Chạy TRÊN CONTAINER — gốc Jupyter ở đâu + tải PhoBERT từ HF được không.

Nếu HF tải được (container có internet thật) → khỏi đẩy 518MB từ local.
"""

import os
import subprocess
import sys
import time


def sh(c: str, cho=300) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho)
    return (r.stdout + r.stderr).strip()


print("gốc Jupyter (root_dir):",
      sh("ls -l /proc/$(pgrep -f jupyter | head -1)/cwd 2>/dev/null | sed 's/.*-> //' || echo '?'"))
print("cwd kernel :", os.getcwd())
print("HOME       :", os.environ.get("HOME"))

# thư mục ghi được để chứa data + model
for d in ("/home/admin", "/mnt/data", "/workspace", "/tmp"):
    print(f"  {d:14} {'ghi được' if os.access(d, os.W_OK) else 'KHÔNG'}" if os.path.exists(d) else f"  {d:14} (không tồn tại)")

print("\n── thử tải PhoBERT config từ HF (container có internet thật?) ──")
sys.path.insert(0, "/home/admin/.local/lib/python3.10/site-packages")
t0 = time.time()
try:
    from huggingface_hub import hf_hub_download
    p = hf_hub_download("vinai/phobert-base", "config.json")
    print(f"  ✓ config tải được: {p} ({time.time()-t0:.0f}s)")
    HF_OK = True
except Exception as e:  # noqa: BLE001
    print(f"  ✗ {type(e).__name__}: {str(e)[:120]}")
    HF_OK = False

if HF_OK:
    print("\n── tải TRỌNG SỐ PhoBERT (540MB — phép thử thật) ──")
    t0 = time.time()
    try:
        from transformers import AutoModelForSequenceClassification
        m = AutoModelForSequenceClassification.from_pretrained("vinai/phobert-base", num_labels=2)
        print(f"  ✓ nạp {sum(p.numel() for p in m.parameters())/1e6:.0f}M tham số ({time.time()-t0:.0f}s)")
        print("  → container tải được PhoBERT từ HF, KHỎI đẩy 518MB từ local")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ {type(e).__name__}: {str(e)[:150]}")
        print("  → phải đẩy PhoBERT từ local")
