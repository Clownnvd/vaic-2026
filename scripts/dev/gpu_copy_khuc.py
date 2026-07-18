"""Chạy TRÊN CONTAINER — copy các khúc checkpoint vào ĐÚNG Jupyter root."""

import os
import subprocess


def sh(c):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=120).stdout.strip()


root = sh("readlink /proc/$(pgrep -f jupyter | head -1)/cwd")
print("jupyter root:", root)

# khúc đã tạo ở /home/admin/vaic/out/pbk_*
print("khúc có sẵn:", sh("ls /home/admin/vaic/out/pbk_* | wc -l"))

# copy khúc + json vào root
sh(f"cp /home/admin/vaic/out/pbk_* '{root}/' && cp /home/admin/vaic/out/phobert_ket_qua.json '{root}/'")
print("đã copy vào root:")
print(sh(f"ls -la '{root}/pbk_'* '{root}/phobert_ket_qua.json' | awk '{{print $5, $9}}'"))
