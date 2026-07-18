"""Chạy TRÊN CONTAINER — khởi động 4 đòn + zero-shot DETACHED, ghi log."""
import subprocess, time


def sh(c, cho=30):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho).stdout.strip()


# chạy don4 (full) → nếu xong (có checkpoint) thì chạy eval_ngoai zero-shot
cmd = (
    "cd /home/admin/vaic && "
    "HF_HOME=/home/admin/.cache/huggingface nohup bash -c "
    "'python -u guard/don4_phobert.py && python -u guard/eval_ngoai.py' "
    "> /home/admin/vaic/don4.log 2>&1 & echo $! > /home/admin/vaic/don4.pid"
)
subprocess.run(["bash", "-lc", cmd], timeout=30)
time.sleep(6)
pid = sh("cat /home/admin/vaic/don4.pid")
print("PID:", pid)
print("--- log đầu ---")
print(sh("head -15 /home/admin/vaic/don4.log"))
print("tiến trình:", sh(f"kill -0 {pid} 2>&1 && echo SỐNG || echo CHẾT"))
