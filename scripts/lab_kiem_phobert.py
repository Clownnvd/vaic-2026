"""Chạy TRÊN LAB — PhoBERT nạp được offline không?

HF_HUB_OFFLINE=1 để CẤM ra mạng. Nếu nạp được thì chứng minh: lab không cần
với tới HuggingFace nữa (mà nó cũng không với tới được — CDN bị chặn).
"""

import os
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

D = "/mnt/data/phobert"
print("file trong", D)
for f in sorted(os.listdir(D)):
    print(f"  {os.path.getsize(os.path.join(D, f))/1e6:8.2f} MB  {f}")

t0 = time.time()
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tok = AutoTokenizer.from_pretrained(D)
m = AutoModelForSequenceClassification.from_pretrained(D, num_labels=2)
n = sum(p.numel() for p in m.parameters())
print(f"\n✓ NẠP OFFLINE OK — {n/1e6:.0f}M tham số ({time.time()-t0:.0f}s)")
print("  tokenize thử:", tok.tokenize("Doanh nghiệp nhỏ và vừa được hỗ trợ 50 triệu đồng")[:9])
