"""Chạy TRÊN LAB — còn sống không, tải xong PhoBERT chưa, data đã giải nén chưa."""

import os
import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip()


print("cache HF (PhoBERT tải xong chưa):")
print(" ", sh("du -sh ~/.cache/huggingface 2>/dev/null || echo '(chưa có cache)'"))
print(" ", sh("ls ~/.cache/huggingface/hub 2>/dev/null | head -4 || echo '(trống)'"))

print("\ndata đã giải nén ở /mnt/data:")
print(" ", sh("ls -la /mnt/data 2>/dev/null | head -8"))
print(" ", sh("du -sh /mnt/data/data /mnt/data/guard 2>/dev/null || echo '(chưa giải nén)'"))

print("\ntorch:")
try:
    import torch

    print("  ", torch.__version__, "| luồng:", torch.get_num_threads(), "| core:", os.cpu_count())
except ImportError:
    print("   CHƯA CÀI")
