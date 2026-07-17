"""Đẩy train_phobert.py đã sửa + retrain trên container. Chạy 2 phần:

phần 1 (local): PUT file lên contents API
phần 2 (trên container, script này exec qua chay_file): copy vào chỗ đúng + retrain
"""

import glob
import os
import subprocess
import time


def sh(c, cho=30):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho).stdout.strip()


# tìm train_phobert.py vừa upload (rơi vào Jupyter root_dir)
src = sh("find / -maxdepth 5 -name train_phobert.py -newermt '-5 minutes' -not -path '*/vaic/*' 2>/dev/null | head -1")
print("file mới upload:", src or "(không thấy — dùng bản trong vaic)")
if src:
    sh(f"cp '{src}' /home/admin/vaic/guard/train_phobert.py")
    print("đã copy đè vào /home/admin/vaic/guard/")

# retrain detached
env = ("DATA_DIR=/home/admin/vaic/data/guard OUT_DIR=/home/admin/vaic/out "
       "HF_HOME=/home/admin/.cache/huggingface ")
cmd = (f"cd /home/admin/vaic && {env} nohup python -u guard/train_phobert.py --day-du "
       "> /home/admin/vaic/train.log 2>&1 & echo $! > /home/admin/vaic/train.pid")
subprocess.run(["bash", "-lc", cmd], timeout=30)
time.sleep(6)
pid = sh("cat /home/admin/vaic/train.pid")
print("PID retrain:", pid)
print("--- log đầu ---")
print(sh("head -12 /home/admin/vaic/train.log"))
print("tiến trình:", sh(f"kill -0 {pid} 2>&1 && echo SỐNG || echo CHẾT"))
