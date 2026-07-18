"""Chạy TRÊN CONTAINER GPU — cài torch cu124 (KHỚP driver CUDA 12.4).

NÉ 3 BUG CUDA CỦA KHO (STATE.md:53):
  1. "torch cu130 vs driver cu126→cài cu124": driver ở đây là CUDA 12.4 →
     cài torch build cu124 cho khớp. KHÔNG để pip kéo bản mặc định (có thể cu13x).
  2. "bỏ --no-deps thiếu libcusparseLt": KHÔNG dùng --no-deps → pip kéo đủ dep.
  3. "pkill self-kill": không dùng pkill ở đây.

Cài đủ: torch(cu124) + transformers + underthesea + numpy + pyarrow.
"""

import subprocess
import sys
import time


def sh(c: str, cho: int = 1200) -> int:
    print(f"\n$ {c[:90]}")
    t0 = time.time()
    p = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho)
    for d in (p.stdout + p.stderr).strip().splitlines()[-5:]:
        print("  " + d[:110])
    print(f"  ({time.time()-t0:.0f}s, mã {p.returncode})")
    return p.returncode


# torch cu124 — khớp driver CUDA 12.4. KHÔNG --no-deps.
sh("python -m pip install -q torch --index-url https://download.pytorch.org/whl/cu124")
sh("python -m pip install -q transformers underthesea numpy pyarrow scikit-learn")

print("\n" + "=" * 56)
print("KIỂM TRA GPU + TORCH")
print("=" * 56)
import torch  # noqa: E402

print("torch        :", torch.__version__)
print("cuda build   :", torch.version.cuda)
print("cuda khả dụng:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU          :", torch.cuda.get_device_name(0))
    print("VRAM         :", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1), "GB")
    # thử một phép tính trên GPU cho chắc
    x = torch.randn(1000, 1000, device="cuda")
    y = (x @ x).sum().item()
    print("phép thử GPU : OK (", round(y, 1), ")")
else:
    print("⚠ CUDA KHÔNG khả dụng — kiểm lại")
