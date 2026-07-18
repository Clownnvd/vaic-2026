"""Chạy TRÊN CONTAINER — chờ 4 đòn + zero-shot xong, in kết quả."""
import subprocess, time


def sh(c, cho=40):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=cho).stdout.strip()


pid = sh("cat /home/admin/vaic/don4.pid")
print("chờ PID", pid, "…")
t0 = time.time()
while time.time() - t0 < 1500:
    alive = sh(f"kill -0 {pid} 2>&1 && echo SONG || echo XONG")
    if alive == "XONG":
        break
    time.sleep(15)

print(f"\n=== XONG sau {time.time()-t0:.0f}s ===")
print("--- 45 dòng cuối log (ablation + zero-shot) ---")
print(sh("tail -45 /home/admin/vaic/don4.log", cho=40))
print("\n--- file kết quả ---")
print(sh("ls -la /home/admin/vaic/artifacts/guard/ 2>/dev/null | awk '{print $5,$9}'"))
