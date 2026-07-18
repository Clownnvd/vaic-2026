"""Chạy TRÊN CONTAINER — verify GPU + cài đủ gói cho 4 đòn (torch cu124 + matplotlib)."""
import subprocess, sys, time


def sh(c, cho=1200):
    print(f"\n$ {c[:80]}")
    t0 = time.time()
    p = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho)
    for d in (p.stdout + p.stderr).strip().splitlines()[-4:]:
        print("  " + d[:110])
    print(f"  ({time.time()-t0:.0f}s, mã {p.returncode})")


print("=== GPU ===")
print(sh("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"))

# torch cu124 khớp driver (né 3 bug CUDA) + đủ gói cho don4 + eval_ngoai
sh("python -m pip install -q --index-url https://download.pytorch.org/whl/cu124 torch 2>&1 | tail -2")
sh("python -m pip install -q transformers underthesea numpy scikit-learn matplotlib 2>&1 | tail -2")

print("\n=== KIỂM ===")
import importlib
for g in ("torch", "transformers", "underthesea", "sklearn", "matplotlib", "numpy"):
    try:
        m = importlib.import_module(g)
        print(f"  {g:14} {getattr(m,'__version__','ok')}")
    except Exception as e:
        print(f"  {g:14} ✗ {e}")
import torch
print("  cuda:", torch.cuda.is_available(), "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
