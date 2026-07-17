"""Đẩy trọng số PhoBERT từ máy local lên lab FPT — CHIA KHÚC.

VÌ SAO PHẢI ĐẨY: lab FPT KHÔNG ra được CDN của HuggingFace.
  curl tới huggingface.co trả 307 (redirect) → nhìn tưởng OK,
  nhưng file thật nằm ở cdn-lfs.huggingface.co và chỗ đó BỊ CHẶN
  → cache HF trống, from_pretrained() treo vô hạn (chết 2 lần).
  Máy local đã có sẵn cache 518MB → đẩy thẳng lên, khỏi phụ thuộc mạng lab.

VÌ SAO CHIA KHÚC: contents API nhét cả file vào 1 JSON base64.
  518MB → ~700MB JSON trong một PUT = gãy chắc.
  Chia 32MB/khúc, ghép lại trên lab bằng `cat`.

Chạy: uv run --python 3.11 --with websocket-client --with certifi --with truststore \
        python scripts/day_phobert.py
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

KHUC = 32 * 1024 * 1024  # 32MB/khúc
CACHE = Path.home() / ".cache/huggingface/hub/models--vinai--phobert-base"

# Dùng snapshot c1e37c… : nó có ĐỦ BỘ (pytorch_model.bin + config + tokenizer).
# Snapshot 92f45c… chỉ có model.safetensors mà THIẾU tokenizer → trộn 2 revision
# khác nhau là tự rước lỗi lệch version. Lấy trọn một revision.
SNAP = "c1e37c5c86f918761049cef6fa216b4779d0d01d"
CAN = ["pytorch_model.bin", "config.json", "tokenizer.json", "bpe.codes", "vocab.txt"]


def main() -> None:
    d = CACHE / "snapshots" / SNAP
    if not d.exists():
        raise SystemExit(f"Không thấy cache: {d}")

    # ── gói: cây thư mục PHẲNG, lab trỏ from_pretrained thẳng vào ──
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:  # bin nén không ăn thua, khỏi gzip cho nhanh
        for ten in CAN:
            f = d / ten
            if not f.exists():
                print(f"  ⚠ thiếu {ten}, bỏ qua")
                continue
            tar.add(str(f.resolve()), arcname=f"phobert/{ten}")
    goi_tin = buf.getvalue()
    print(f"Gói PhoBERT: {len(goi_tin)/1e6:.1f} MB → {(len(goi_tin)+KHUC-1)//KHUC} khúc\n")

    # ── đẩy từng khúc ──────────────────────────────────────
    t0 = time.time()
    n = 0
    for i in range(0, len(goi_tin), KHUC):
        m = goi_tin[i : i + KHUC]
        goi(
            f"/api/contents/pb_{n:03d}.part",
            "PUT",
            json.dumps(
                {"type": "file", "format": "base64", "content": base64.b64encode(m).decode()}
            ).encode(),
        )
        n += 1
        print(f"  khúc {n:2}  {(i+len(m))/1e6:6.1f}/{len(goi_tin)/1e6:.1f} MB  ({time.time()-t0:.0f}s)")

    # ── ghép + giải nén trên lab ───────────────────────────
    print("\nGhép và giải nén trên lab…")
    chay(
        f"""
import os, subprocess, tarfile, glob
os.chdir('/mnt/data')
parts = sorted(glob.glob('/mnt/data/pb_*.part'))
print('khúc thấy:', len(parts))
with open('/mnt/data/phobert.tar','wb') as out:
    for p in parts:
        with open(p,'rb') as f: out.write(f.read())
print('ghép xong:', os.path.getsize('/mnt/data/phobert.tar')/1e6, 'MB')
with tarfile.open('/mnt/data/phobert.tar') as t: t.extractall('/mnt/data')
for f in sorted(os.listdir('/mnt/data/phobert')):
    print(f'  {{os.path.getsize("/mnt/data/phobert/"+f)/1e6:8.2f}} MB  {{f}}')
for p in parts: os.remove(p)
os.remove('/mnt/data/phobert.tar')
print('đã dọn khúc tạm')
""",
        cho=600,
    )

    # ── kiểm: nạp được model từ đĩa không (KHÔNG đụng mạng) ──
    print("\nKiểm nạp model từ đĩa lab (offline hoàn toàn)…")
    chay(
        """
import os, time
os.environ['HF_HUB_OFFLINE'] = '1'      # cấm ra mạng — chứng minh không cần HF
os.environ['TRANSFORMERS_OFFLINE'] = '1'
t0 = time.time()
from transformers import AutoTokenizer, AutoModelForSequenceClassification
tok = AutoTokenizer.from_pretrained('/mnt/data/phobert')
m = AutoModelForSequenceClassification.from_pretrained('/mnt/data/phobert', num_labels=2)
print(f'✓ nạp OK {sum(p.numel() for p in m.parameters())/1e6:.0f}M tham số ({time.time()-t0:.0f}s)')
print('  tokenizer thử:', tok.tokenize('Doanh nghiệp nhỏ và vừa được hỗ trợ 50 triệu đồng')[:8])
""",
        cho=600,
    )


if __name__ == "__main__":
    main()
