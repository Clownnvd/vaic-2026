"""Train Guard NLI (PhoBERT) — chạy được trên CPU / Kaggle T4 / FPT H100.

CHẠY --smoke TRƯỚC KHI ĐỐT GIỜ GPU. Kho ghi rõ: 2 phút smoke bắt hết lỗi API
để không phí giờ GPU. Đã có người trả giá cho bài học này.

  uv run --python 3.11 --with torch --with transformers --with underthesea python \
      guard/train_phobert.py --smoke          # 40 mẫu, 1 epoch, ~2 phút CPU
  ... --nhe                                   # 2k mẫu CPU (~20 phút)
  ... --day-du                                # full, dành cho GPU

⛔ `vinai/phobert-base` = MIT. TUYỆT ĐỐI KHÔNG dùng `phobert-base-v2` = AGPL.
⛔ Không đẩy checkpoint lên GitHub (luật E2) — đã .gitignore.

Tách từ bằng `underthesea.word_tokenize` để NÉ VnCoreNLP (cần Java) — nguồn lỗi #1.
max_len = 256: đo thật trên khoản luật, 25,9% vượt 128 token.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, ".")

SEED = 7
MODEL = "vinai/phobert-base"  # MIT — KHÔNG dùng v2 (AGPL)
MAX_LEN = 256  # đo thật: 25,9% khoản vượt 128 token
DATA = Path("./data/guard")
OUT = Path("./artifacts/guard")

# 4 trục NGỮ NGHĨA — thứ rule KHÔNG bắt được, đây là việc của model
TRUC_NGU_NGHIA = {
    "bia_tong_quat_hoa",
    "bia_tu_du_dieu_kien",
    "bia_bo_rang_buoc",
    "bia_suy_dien",
}


def dat_seed(s: int = SEED) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def nap(ten: str, chi_ngu_nghia: bool, gioi_han: int | None) -> list[dict]:
    """Nạp cặp. chi_ngu_nghia=True → chỉ giữ positive + 4 trục ngữ nghĩa.

    VÌ SAO lọc: lớp tất định đã bắt 6 trục kia với 0.977 và giải trình được.
    Bắt model học lại mấy trục đó = lãng phí + làm loãng. Giao đúng việc.
    """
    ra = []
    with (DATA / f"{ten}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if chi_ngu_nghia:
                if r["label"] == 0 and r["corruption_type"] not in TRUC_NGU_NGHIA:
                    continue
            ra.append(r)
            if gioi_han and len(ra) >= gioi_han:
                break
    return ra


def can_bang(rows: list[dict], rng: random.Random) -> list[dict]:
    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]
    n = min(len(pos), len(neg))
    ra = rng.sample(pos, n) + rng.sample(neg, n)
    rng.shuffle(ra)
    return ra


def tach_tu(s: str) -> str:
    """underthesea — né VnCoreNLP (cần Java). Lỗi thì trả nguyên, không chết."""
    try:
        from underthesea import word_tokenize

        return word_tokenize(s, format="text")
    except Exception:  # noqa: BLE001
        return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="40 mẫu 1 epoch — bắt lỗi trước khi đốt GPU")
    ap.add_argument("--nhe", action="store_true", help="2k mẫu, chạy CPU được")
    ap.add_argument("--day-du", action="store_true", help="full — dành cho GPU")
    ap.add_argument("--tat-ca-truc", action="store_true", help="train cả 6 trục rule đã bắt (mặc định KHÔNG)")
    args = ap.parse_args()

    if args.smoke:
        n_train, epochs, bs = 40, 1, 8
    elif args.nhe:
        n_train, epochs, bs = 2000, 3, 16
    else:
        n_train, epochs, bs = None, 4, 16

    dat_seed()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    chi_nn = not args.tat_ca_truc

    print(f"Model : {MODEL}  (MIT)")
    print(f"Chế độ: {'smoke' if args.smoke else ('nhẹ/CPU' if args.nhe else 'đầy đủ')}")
    print(f"Trục  : {'CHỈ ngữ nghĩa (rule không bắt được)' if chi_nn else 'tất cả'}")

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Thiết bị: {dev}" + ("  ⚠ CPU — chậm, cân nhắc GPU" if dev.type == "cpu" else ""))

    tr = can_bang(nap("train", chi_nn, None), rng)
    if n_train:
        tr = tr[:n_train]
    te = can_bang(nap("test", chi_nn, None), rng)
    print(f"\ntrain {len(tr):,} cặp (đã cân 1:1) · test {len(te):,}")
    if not tr:
        raise SystemExit("Không có dữ liệu — chạy guard/make_data.py trước.")

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    print("Nạp tokenizer + model…")
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2).to(dev)

    def batch(rows: list[dict]):
        p = [tach_tu(r["premise"][:1500]) for r in rows]
        h = [tach_tu(r["hypothesis"][:600]) for r in rows]
        enc = tok(p, h, truncation=True, max_length=MAX_LEN, padding=True, return_tensors="pt")
        y = torch.tensor([r["label"] for r in rows])
        return {k: v.to(dev) for k, v in enc.items()}, y.to(dev)

    opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
    ce = nn.CrossEntropyLoss()
    t0 = time.time()

    for ep in range(epochs):
        model.train()
        idx = list(range(len(tr)))
        rng.shuffle(idx)
        tong = 0.0
        for i in range(0, len(idx), bs):
            b = [tr[j] for j in idx[i : i + bs]]
            enc, y = batch(b)
            opt.zero_grad()
            out = model(**enc)
            loss = ce(out.logits, y)
            loss.backward()
            opt.step()
            tong += loss.item()
            if args.smoke:
                print(f"  step {i // bs}: loss {loss.item():.4f}")
        print(f"epoch {ep}: loss TB {tong / max(len(idx) // bs, 1):.4f}  ({time.time() - t0:.0f}s)")

    # ── đo trên test ──────────────────────────────────────────
    model.eval()
    dung = 0
    bat_bia = 0
    n_bia = 0
    with torch.no_grad():
        for i in range(0, len(te), 32):
            b = te[i : i + 32]
            enc, y = batch(b)
            pred = model(**enc).logits.argmax(1)
            dung += (pred == y).sum().item()
            for p_, y_ in zip(pred.tolist(), y.tolist()):
                if y_ == 0:
                    n_bia += 1
                    if p_ == 0:
                        bat_bia += 1

    acc = dung / max(len(te), 1)
    r_bia = bat_bia / max(n_bia, 1)
    print(f"\n{'=' * 52}")
    print(f"acc      = {acc:.3f}   ({dung}/{len(te)})")
    print(f"bắt bịa  = {r_bia:.3f}   ({bat_bia}/{n_bia})")
    print(f"thời gian= {time.time() - t0:.0f}s trên {dev}")

    if args.smoke:
        print("\n✓ SMOKE XANH — đường ống chạy được, giờ đẩy lên GPU chạy thật.")
        print("  (số trên vô nghĩa: 40 mẫu 1 epoch, chỉ để bắt lỗi)")
        return

    # so với lớp tất định — trục ngữ nghĩa nó ra 0.000
    print(f"\nSo sánh trên trục NGỮ NGHĨA:")
    print(f"  lớp tất định : 0.000  (rule KHÔNG THỂ bắt — không có số/mã nào sai)")
    print(f"  PhoBERT NLI  : {r_bia:.3f}")
    if r_bia > 0.5:
        print(f"  ⇒ model VÁ được chỗ rule mù → PyTorch load-bearing, ablation có cái để nói.")
    else:
        print(f"  ⇒ model CHƯA vá được. Chưa có gì để khoe — nói thật, đừng ép số.")

    d = OUT / "phobert_guard"
    model.save_pretrained(d)
    tok.save_pretrained(d)
    (OUT / "phobert_ket_qua.json").write_text(
        json.dumps(
            {"acc": acc, "bat_bia": r_bia, "n_train": len(tr), "n_test": len(te),
             "epochs": epochs, "device": str(dev), "chi_ngu_nghia": chi_nn},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n✓ checkpoint → {d}  (đã .gitignore — luật E2 cấm publish weights)")


if __name__ == "__main__":
    main()
