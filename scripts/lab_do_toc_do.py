"""Chạy TRÊN LAB — giải nén rồi ĐO tốc độ train thật trên 128 core.

MỤC ĐÍCH: quyết định CPU hay GPU bằng SỐ ĐO, không bằng cảm giác.
  CPU lab  : miễn phí, 128 core
  H100     : 67.925 ₫/giờ

4 đòn cần train NHIỀU LƯỢT (đòn #2 self-play: train → đào → train lại → lặp).
Nên phép tính đúng là: giây/bước × số bước × số lượt, chứ không phải 1 lượt.
"""

import json
import os
import tarfile
import time

GOC = "/mnt/data"  # root_dir của Jupyter (KHÔNG phải /home/jovyan — kernel cwd khác)
os.chdir(GOC)

if not os.path.exists(f"{GOC}/guard/train_phobert.py"):
    with tarfile.open(f"{GOC}/vaic.tar.gz") as t:
        t.extractall(GOC)
print("Đã giải nén:")
for r, _, f in os.walk(f"{GOC}/data"):
    for x in f:
        p = os.path.join(r, x)
        print(f"  {os.path.getsize(p)/1e6:7.2f} MB  {p}")
print(f"  {os.path.getsize(f'{GOC}/guard/train_phobert.py')/1e3:7.2f} KB  guard/train_phobert.py")

# ── đếm thật xem còn bao nhiêu cặp sau khi lọc 4 trục ngữ nghĩa ──
TRUC = {"bia_tong_quat_hoa", "bia_tu_du_dieu_kien", "bia_bo_rang_buoc", "bia_suy_dien"}
n_pos = n_neg = 0
with open(f"{GOC}/data/guard/train.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["label"] == 1:
            n_pos += 1
        elif r["corruption_type"] in TRUC:
            n_neg += 1
print(f"\nSau lọc 4 trục ngữ nghĩa: {n_pos:,} thật · {n_neg:,} bịa")
print(f"Cân 1:1 → {min(n_pos, n_neg)*2:,} cặp train")

# ── ĐO: giây/bước thật ──────────────────────────────────
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

torch.set_num_threads(os.cpu_count())
print(f"\nluồng torch: {torch.get_num_threads()} / {os.cpu_count()} core")

print("Tải PhoBERT (MIT)…")
t0 = time.time()
tok = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModelForSequenceClassification.from_pretrained("vinai/phobert-base", num_labels=2)
print(f"  tải xong {time.time()-t0:.0f}s")

rows = []
with open(f"{GOC}/data/guard/train.jsonl", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 64:
            break
        rows.append(json.loads(line))

opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
ce = torch.nn.CrossEntropyLoss()
BS = 32
print(f"\nĐo 4 bước, batch {BS}, max_len 256…")
giay = []
for i in range(4):
    b = rows[(i * BS) % 32 : (i * BS) % 32 + BS]
    t1 = time.time()
    enc = tok(
        [r["premise"][:1500] for r in b],
        [r["hypothesis"][:600] for r in b],
        truncation=True, max_length=256, padding=True, return_tensors="pt",
    )
    y = torch.tensor([r["label"] for r in b])
    opt.zero_grad()
    loss = ce(model(**enc).logits, y)
    loss.backward()
    opt.step()
    d = time.time() - t1
    giay.append(d)
    print(f"  bước {i}: {d:5.2f}s  loss {loss.item():.4f}")

gpb = sum(giay[1:]) / max(len(giay) - 1, 1)  # bỏ bước đầu (warm-up)
n_cap = min(n_pos, n_neg) * 2
buoc_1ep = n_cap // BS
print("\n" + "=" * 58)
print(f"  {gpb:.2f} giây/bước  ·  {buoc_1ep} bước/epoch")
print(f"  1 epoch  ≈ {gpb*buoc_1ep/60:5.1f} phút")
print(f"  3 epoch  ≈ {gpb*buoc_1ep*3/60:5.1f} phút   ← 1 lượt train")
print(f"  4 đòn (≈6 lượt) ≈ {gpb*buoc_1ep*3*6/60:5.1f} phút = {gpb*buoc_1ep*3*6/3600:.1f} giờ")
print("=" * 58)
print(f"\n  H100 nhanh ~20-30× → 4 đòn ≈ {gpb*buoc_1ep*3*6/60/25:.1f} phút, tốn ~68.000 ₫ (1 giờ tối thiểu)")
print("  → CPU miễn phí. Chỉ thuê H100 nếu CPU quá {:.0f} phút.".format(gpb*buoc_1ep*3*6/60))
