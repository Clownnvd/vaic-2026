"""Chạy TRÊN LAB (kernel riêng) — train PhoBERT có đang chạy thật không?

Kiểm CPU load + tiến trình python + có file output chưa. Để phân biệt
'đang train' với 'treo/chết'.
"""

import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=30)
    return (r.stdout + r.stderr).strip()


print("── tải CPU (train nặng thì load cao) ──")
print(" ", sh("uptime"))
print(" ", sh("nproc"), "core")

print("\n── tiến trình python đang chạy ──")
print(sh("ps aux | grep -i python | grep -v grep | awk '{print $3\"% CPU  \"$11\" \"$12\" \"$13}' | head -6") or "(không có)")

print("\n── file output train đã sinh chưa ──")
print(sh("ls -la /mnt/data/out_guard 2>/dev/null || echo '(chưa có out_guard)'"))

print("\n── RAM đang dùng ──")
print(" ", sh("free -g | head -2 | tail -1"))
