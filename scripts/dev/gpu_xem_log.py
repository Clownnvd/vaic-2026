"""Chạy TRÊN CONTAINER — đọc log train + trạng thái tiến trình."""

import subprocess


def sh(c):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=30).stdout.strip()


pid = sh("cat /home/admin/vaic/train.pid 2>/dev/null")
alive = sh(f"kill -0 {pid} 2>&1 && echo SỐNG || echo XONG") if pid else "?"
print(f"PID {pid}: {alive}")
print(f"GPU: {sh('nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null')}")
print("\n--- train.log (40 dòng cuối) ---")
print(sh("tail -40 /home/admin/vaic/train.log 2>/dev/null"))
print("\n--- model đã lưu chưa ---")
print(sh("ls -la /home/admin/vaic/out 2>/dev/null || echo '(chưa có out)'"))
