"""Chạy TRÊN LAB — giới hạn RAM THẬT của pod là bao nhiêu (cgroup)?

free -g cho thấy RAM của HOST (2TB), nhưng pod serverless thường bị cgroup
giới hạn thấp hơn nhiều. Train bị Killed ngay sau nạp model ⇒ nghi đụng trần.
"""

import subprocess


def sh(c: str) -> str:
    r = subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=20)
    return (r.stdout + r.stderr).strip()


print("── cgroup v2 (đường thường gặp) ──")
print("  memory.max :", sh("cat /sys/fs/cgroup/memory.max 2>/dev/null || echo '(không có)'"))
print("  memory.current:", sh("cat /sys/fs/cgroup/memory.current 2>/dev/null || echo '(không có)'"))

print("\n── cgroup v1 ──")
print("  limit_in_bytes:", sh("cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo '(không có)'"))

print("\n── quy ra GB ──")
print(sh(
    "for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory/memory.limit_in_bytes; do "
    "[ -f $f ] && v=$(cat $f) && [ $v != max ] && echo \"$f = $(($v/1024/1024/1024)) GB\"; done"
) or "(không đọc được)")

print("\n── log train (đoạn cuối, xem có OOM message) ──")
print(sh("tail -8 /mnt/data/train.log 2>/dev/null"))

print("\n── ulimit ──")
print("  ", sh("ulimit -a | grep -i 'memory\\|virtual' || echo '(không giới hạn ulimit)'"))
