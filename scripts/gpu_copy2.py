"""Copy khúc checkpoint vào /home/admin (Jupyter root của container)."""

import subprocess


def sh(c):
    return subprocess.run(["bash", "-lc", c], capture_output=True, text=True, timeout=120).stdout.strip()


# xác nhận root: file upload trước rơi vào /home/admin
print("test file cũ:", sh("ls /home/admin/vaic.tar.gz 2>&1"))
sh("cp /home/admin/vaic/out/pbk_* /home/admin/ && cp /home/admin/vaic/out/phobert_ket_qua.json /home/admin/")
print("khúc trong /home/admin:")
print(sh("ls -la /home/admin/pbk_* /home/admin/phobert_ket_qua.json | awk '{print $5, $9}'"))
