"""Đẩy data + code 4 đòn lên container GPU (nén gzip, giải nén /home/admin/vaic).

Gồm: data/guard/*.jsonl, data/ngoai/vifactcheck_*.jsonl, guard/don4_phobert.py,
guard/eval_ngoai.py. PhoBERT tải từ HF trên container (đã test container ra được HF).
"""
from __future__ import annotations
import base64, io, json, sys, tarfile, time
from pathlib import Path
sys.path.insert(0, ".")
from scripts.jupyter_fpt import chay, goi  # noqa: E402

FILE = [
    ("guard/don4_phobert.py", "guard/don4_phobert.py"),
    ("guard/eval_ngoai.py", "guard/eval_ngoai.py"),
    ("data/guard/train.jsonl", "data/guard/train.jsonl"),
    ("data/guard/test.jsonl", "data/guard/test.jsonl"),
    ("data/guard/calib.jsonl", "data/guard/calib.jsonl"),
    ("data/ngoai/vifactcheck_test.jsonl", "data/ngoai/vifactcheck_test.jsonl"),
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
    print(f"Gói: {len(goi_tin)/1e6:.1f} MB")
    goi("/api/contents/don4.tar.gz", "PUT",
        json.dumps({"type": "file", "format": "base64", "content": base64.b64encode(goi_tin).decode()}).encode())
    print("Đẩy xong. Giải nén…")
    chay("""
import tarfile, os, subprocess
src = subprocess.run(['bash','-lc',"find / -maxdepth 5 -name don4.tar.gz -not -path '/proc/*' 2>/dev/null | head -1"],capture_output=True,text=True).stdout.strip()
os.makedirs('/home/admin/vaic', exist_ok=True)
with tarfile.open(src) as t: t.extractall('/home/admin/vaic')
print('giải nén xong:')
for r,d,f in os.walk('/home/admin/vaic'):
    for x in f: print(' ', os.path.join(r,x)[:70])
""")


if __name__ == "__main__":
    main()
