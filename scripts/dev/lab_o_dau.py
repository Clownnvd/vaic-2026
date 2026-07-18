"""Chạy TRÊN LAB — thư mục gốc của Jupyter contents API là chỗ nào?

Đoán /home/jovyan là sai (ảnh conda khác nhau mỗi nhà cung cấp). Hỏi thẳng.
"""

import os
import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=30)
    return (r.stdout + r.stderr).strip()


print("cwd     :", os.getcwd())
print("HOME    :", os.environ.get("HOME"))
print("user    :", sh("whoami"))
print()
print("--- tìm vaic.tar.gz đã upload ---")
print(sh("find / -maxdepth 6 -name 'vaic.tar.gz' -not -path '*/proc/*' 2>/dev/null | head -5") or "(KHÔNG THẤY)")
print()
print("--- ls cwd ---")
print(sh("ls -la . | head -14"))
print()
print("--- ls $HOME ---")
print(sh("ls -la $HOME | head -14"))
