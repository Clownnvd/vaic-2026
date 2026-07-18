"""Chạy TRÊN LAB — train PhoBERT thật, offline hoàn toàn.

Nạp PhoBERT từ /mnt/data/phobert (đã đẩy sẵn — lab không ra được HF).
Data 50/50 từ /mnt/data/data/guard. Chạy full 3 epoch + eval theo trục + FPR.
"""

import os
import subprocess
import sys
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["MODEL_DIR"] = "/mnt/data/phobert"
os.environ["DATA_DIR"] = "/mnt/data/data/guard"
os.environ["OUT_DIR"] = "/mnt/data/out_guard"

# gói underthesea đã cài ở /opt/lab-venv lúc lab_cai.py; đảm bảo có
try:
    import underthesea  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "underthesea"], timeout=600)

sys.argv = ["train_phobert.py", "--day-du"]  # --day-du → 4 epoch, full data
print("Bắt đầu train PhoBERT trên lab FPT (128 core CPU)…")
print(f"  model : {os.environ['MODEL_DIR']}")
print(f"  data  : {os.environ['DATA_DIR']}")
t0 = time.time()

sys.path.insert(0, "/mnt/data")
exec(open("/mnt/data/guard/train_phobert.py").read())

print(f"\n⏱ tổng {time.time()-t0:.0f}s")
