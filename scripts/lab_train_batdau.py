"""Chạy TRÊN LAB — khởi động train PhoBERT DETACHED (nohup), ghi log ra file.

Vì sao không exec() trong kernel: giữ WebSocket 20 phút mong manh, và exec()
nuốt mất __main__. Cách chắc: chạy train_phobert.py như TIẾN TRÌNH CON thật
bằng nohup, ghi /mnt/data/train.log, rồi poll log bằng kernel khác.

python -u để KHÔNG đệm stdout → log chảy ngay, thấy tiến độ.
"""

import os
import subprocess
import time

LOG = "/mnt/data/train.log"
PID = "/mnt/data/train.pid"

env = (
    "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
    "MODEL_DIR=/mnt/data/phobert "
    "DATA_DIR=/mnt/data/data/guard "
    "OUT_DIR=/mnt/data/out_guard "
)

# nohup + & : chạy tách hẳn, kernel trả về ngay. python -u: không đệm.
cmd = (
    f"cd /mnt/data && {env} nohup python -u guard/train_phobert.py --day-du "
    f"> {LOG} 2>&1 & echo $! > {PID}"
)
subprocess.run(["bash", "-lc", cmd], timeout=30)
time.sleep(3)

pid = subprocess.run(["bash", "-lc", f"cat {PID}"], capture_output=True, text=True).stdout.strip()
print(f"đã khởi động train, PID={pid}")
print("--- log 15 dòng đầu ---")
print(subprocess.run(["bash", "-lc", f"sleep 4; head -15 {LOG} 2>/dev/null"],
                     capture_output=True, text=True).stdout)
alive = subprocess.run(["bash", "-lc", f"kill -0 {pid} 2>&1 && echo SỐNG || echo CHẾT"],
                       capture_output=True, text=True).stdout.strip()
print(f"tiến trình: {alive}")
