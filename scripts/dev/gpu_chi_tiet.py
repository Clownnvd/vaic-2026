"""Chạy TRÊN CONTAINER GPU — chi tiết để cài torch KHỚP driver (né 3 bug CUDA).

Kho dính: torch build cu130 nhưng driver cu126 → phải cài cu124.
Nên phải BIẾT driver CUDA version TRƯỚC khi pip install torch.
"""

import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=40)
    return (r.stdout + r.stderr).strip()


print("── nvidia-smi (driver + CUDA version) ──")
print(sh("nvidia-smi | head -12"))

print("\n── CUDA runtime version từ driver ──")
print("  driver CUDA :", sh("nvidia-smi | grep -o 'CUDA Version: [0-9.]*' | head -1"))

print("\n── GIỚI HẠN RAM thật của container (cgroup) ──")
print("  memory.max :", sh(
    "for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory/memory.limit_in_bytes; do "
    "[ -f $f ] && v=$(cat $f) && [ \"$v\" != max ] && echo \"$(($v/1024/1024/1024)) GB\" && break; done"
) or "(không giới hạn / max)")

print("\n── python + pip ──")
print("  python:", sh("which python python3 | head -2"))
print("  pip   :", sh("python -m pip --version 2>&1 | head -1"))
