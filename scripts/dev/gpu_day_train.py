"""Đẩy data + train script lên CONTAINER GPU rồi khởi động train DETACHED.

Chạy với FPT_LAB_CONFIG=.fpt_container.json.
PhoBERT tải thẳng từ HF trên container (đã test được) → khỏi đẩy 518MB.
Data chỉ 3.5MB. Train chạy nohup, ghi /home/admin/vaic/train.log, poll sau.
"""

from __future__ import annotations

import base64
import io
import json
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.jupyter_fpt import chay, goi  # noqa: E402

FILE = [
    ("guard/train_phobert.py", "guard/train_phobert.py"),
    ("data/guard/train.jsonl", "data/guard/train.jsonl"),
    ("data/guard/test.jsonl", "data/guard/test.jsonl"),
    ("data/guard/calib.jsonl", "data/guard/calib.jsonl"),
    ("data/guard/gpt4o_bia_that.jsonl", "data/guard/gpt4o_bia_that.jsonl"),
]


def main() -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for nguon, dich in FILE:
            tar.add(Path(nguon), arcname=dich)
    goi_tin = buf.getvalue()
    print(f"Gói: {len(goi_tin)/1e6:.1f} MB")

    goi(
        "/api/contents/vaic.tar.gz",
        "PUT",
        json.dumps({"type": "file", "format": "base64",
                    "content": base64.b64encode(goi_tin).decode()}).encode(),
    )
    print("Đẩy xong. Giải nén + khởi động train…\n")

    # giải nén vào /home/admin/vaic, tìm file tar ở gốc Jupyter (root_dir)
    chay(
        """
import tarfile, os, glob, subprocess
# tar rơi vào root_dir của Jupyter — tìm nó
cands = glob.glob('/home/admin/**/vaic.tar.gz', recursive=True) + \
        glob.glob('/mnt/**/vaic.tar.gz', recursive=True) + \
        glob.glob('/root/**/vaic.tar.gz', recursive=True) + \
        glob.glob('/**/vaic.tar.gz', recursive=False)
src = subprocess.run(['bash','-lc',"find / -maxdepth 5 -name vaic.tar.gz -not -path '/proc/*' 2>/dev/null | head -1"],
                     capture_output=True,text=True).stdout.strip()
print('tar ở:', src)
os.makedirs('/home/admin/vaic', exist_ok=True)
with tarfile.open(src) as t: t.extractall('/home/admin/vaic')
print('đã giải nén vào /home/admin/vaic')
for r,d,f in os.walk('/home/admin/vaic'):
    for x in f: print(' ', os.path.join(r,x))
"""
    )

    # khởi động train DETACHED. MODEL để mặc định (tải HF). cuda tự nhận.
    env = (
        "DATA_DIR=/home/admin/vaic/data/guard "
        "OUT_DIR=/home/admin/vaic/out "
        "HF_HOME=/home/admin/.cache/huggingface "
    )
    chay(
        f"""
import subprocess, time
cmd = ("cd /home/admin/vaic && {env} nohup python -u guard/train_phobert.py --day-du "
       "> /home/admin/vaic/train.log 2>&1 & echo $! > /home/admin/vaic/train.pid")
subprocess.run(['bash','-lc',cmd], timeout=30)
time.sleep(6)
pid = open('/home/admin/vaic/train.pid').read().strip()
print('PID train:', pid)
print('--- log đầu ---')
print(subprocess.run(['bash','-lc','head -20 /home/admin/vaic/train.log'],capture_output=True,text=True).stdout)
alive = subprocess.run(['bash','-lc',f'kill -0 {{pid}} 2>&1 && echo SỐNG || echo CHẾT'],capture_output=True,text=True).stdout.strip()
print('tiến trình:', alive)
"""
    )


if __name__ == "__main__":
    main()
