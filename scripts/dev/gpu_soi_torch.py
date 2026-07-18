"""Chạy TRÊN CONTAINER — torch cài ở đâu, kernel có thấy không."""

import subprocess
import sys

print("sys.executable :", sys.executable)
print("PYTHONNOUSERSITE:", __import__("os").environ.get("PYTHONNOUSERSITE"))
print("\nsys.path:")
for p in sys.path:
    print("  ", p)

print("\ntorch cài ở đâu:")
r = subprocess.run(["bash", "-lc", "find /home/admin/.local /usr/local/lib /usr/lib -maxdepth 4 -name 'torch' -type d 2>/dev/null | head -5"],
                   capture_output=True, text=True)
print(r.stdout.strip() or "(không thấy)")

print("\nthử thêm user site rồi import:")
import site
us = site.getusersitepackages()
print("  user site:", us)
if us not in sys.path:
    sys.path.insert(0, us)
try:
    import torch
    print("  ✓ import OK sau khi thêm user site:", torch.__version__, "cuda", torch.cuda.is_available())
except Exception as e:  # noqa: BLE001
    print("  ✗", type(e).__name__, e)
