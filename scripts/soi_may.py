"""Chạy TRÊN LAB FPT — máy này là cái gì? Có GPU không?

Đọc trạng thái THẬT, không đoán: nvidia-smi vắng mặt chưa chắc là không có GPU
(có thể thiếu binary mà vẫn có /dev/nvidia*). Soi nhiều đường.
"""

import os
import platform
import subprocess


def sh(c: str) -> str:
    try:
        r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=30)
        return (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return f"({type(e).__name__})"


print("=" * 60)
print("MÁY   :", platform.node(), "|", platform.machine())
print("CPU   :", os.cpu_count(), "core")
print("RAM   :", sh("free -g | head -2 | tail -1"))
print("DISK  :", sh("df -h /home 2>/dev/null | tail -1"))
print("=" * 60)

print("\n--- GPU: soi nhiều đường ---")
print("nvidia-smi   :", sh("which nvidia-smi || echo KHONG CO"))
print("/dev/nvidia* :", sh("ls /dev/nvidia* 2>&1 | head -4"))
print("lspci        :", sh("lspci 2>/dev/null | grep -i nvidia | head -3 || echo '(khong co lspci)'"))
print("libcuda      :", sh("ldconfig -p 2>/dev/null | grep -i libcuda | head -2 || echo KHONG CO"))

print("\n--- torch ---")
try:
    import torch

    print("torch     :", torch.__version__)
    print("cuda build:", torch.version.cuda)
    print("available :", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU       :", torch.cuda.get_device_name(0))
        print("VRAM      :", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1), "GB")
except ImportError:
    print("torch     : CHƯA CÀI")

print("\n--- có sẵn gói gì ---")
for g in ("transformers", "underthesea", "datasets", "numpy", "pyarrow"):
    try:
        m = __import__(g)
        print(f"  {g:14} {getattr(m, '__version__', '?')}")
    except ImportError:
        print(f"  {g:14} —")

print("\n--- ra internet được không (tải PhoBERT từ HF) ---")
print(sh("curl -sS -o /dev/null -w '%{http_code}' -m 12 https://huggingface.co/vinai/phobert-base/resolve/main/config.json"))
