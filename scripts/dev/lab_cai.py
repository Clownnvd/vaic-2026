"""Chạy TRÊN LAB — cài gói cần cho PhoBERT.

Lab trống trơn: không torch, không transformers. Cài bản CPU trước (nhẹ hơn
nhiều so với bản CUDA ~2.5GB) để ĐO xem 128 core có đủ nhanh không.
Đủ thì khỏi tiêu 67.925 ₫/giờ cho H100.
"""

import subprocess
import sys
import time


def sh(c: str, cho: int = 900) -> None:
    print(f"\n$ {c}")
    t0 = time.time()
    p = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho)
    ra = (p.stdout + p.stderr).strip().splitlines()
    for d in ra[-6:]:
        print("  " + d[:110])
    print(f"  ({time.time() - t0:.0f}s, mã {p.returncode})")


# torch CPU: index riêng của pytorch → ~200MB thay vì ~2.5GB bản CUDA
sh("pip install -q --index-url https://download.pytorch.org/whl/cpu torch 2>&1 | tail -3")
sh("pip install -q transformers underthesea 2>&1 | tail -3")

print("\n" + "=" * 56)
try:
    import torch

    print("torch        :", torch.__version__)
    print("số luồng     :", torch.get_num_threads())
    import transformers

    print("transformers :", transformers.__version__)
    import underthesea

    print("underthesea  : ok")
except Exception as e:  # noqa: BLE001
    print("LỖI:", type(e).__name__, e)
