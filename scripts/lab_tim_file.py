"""Chạy TRÊN LAB — vaic.tar.gz rơi vào đâu?

Contents API báo file nằm ở gốc `''`, nhưng kernel chạy ở /home/jovyan lại không
thấy. Nghĩa là gốc contents ≠ cwd kernel. Tìm thật, đừng đoán tiếp.
"""

import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=90)
    return (r.stdout + r.stderr).strip()


print("--- tìm vaic.tar.gz khắp máy ---")
ra = sh("find / -name 'vaic.tar.gz' -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null | head -5")
print(ra or "(KHÔNG THẤY)")

print("\n--- gốc contents của jupyter (từ config) ---")
print(sh("cat ~/.jupyter/jupyter_server_config.py 2>/dev/null | grep -i 'root_dir\\|notebook_dir' | head -4") or "(không có trong config)")
print(sh("ps aux | grep -o '\\-\\-ServerApp.root_dir=[^ ]*' | head -2") or "(không có trong dòng lệnh)")
print("ServerApp cwd:", sh("ls -l /proc/$(pgrep -f jupyter | head -1)/cwd 2>/dev/null | sed 's/.*-> //'") or "?")
