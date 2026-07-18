"""Đẩy DATA ĐÃ VÁ (50/50) + script train lên lab — ghi đè bản cũ (17/83).

Data trên lab hiện là bản 17/83 lỗi cân nhãn. Sau khi vá make_data.py phải
đẩy lại. Nhỏ (~34MB → gzip ~4MB) nên 1 PUT là xong.
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
            p = Path(nguon)
            if not p.exists():
                print(f"  ⚠ thiếu {p}")
                continue
            tar.add(p, arcname=dich)
    goi_tin = buf.getvalue()
    print(f"Gói data mới: {len(goi_tin)/1e6:.1f} MB")

    t0 = time.time()
    goi(
        "/api/contents/vaic_data.tar.gz",
        "PUT",
        json.dumps(
            {"type": "file", "format": "base64", "content": base64.b64encode(goi_tin).decode()}
        ).encode(),
    )
    print(f"Đẩy xong ({time.time()-t0:.0f}s)\n")

    chay(
        """
import tarfile, os, json
os.chdir('/mnt/data')
with tarfile.open('/mnt/data/vaic_data.tar.gz') as t: t.extractall('/mnt/data')
# kiểm cân nhãn bản mới
for ten in ['train','test','calib']:
    n1=n0=0
    for line in open(f'/mnt/data/data/guard/{ten}.jsonl',encoding='utf-8'):
        r=json.loads(line)
        if r['label']==1: n1+=1
        else: n0+=1
    print(f'{ten:6} thật {n1:6} / bịa {n0:6} = {n1/(n1+n0)*100:.0f}%/{n0/(n1+n0)*100:.0f}%')
print('✓ data mới đã lên lab')
"""
    )


if __name__ == "__main__":
    main()
