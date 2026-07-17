"""4 ĐÒN với PhoBERT THẬT — đây là bài dự giải Meta PyTorch.

  #4 sinh hard-negative  → data (đã có: 28.742 cặp, cân trục 41/38/21)
  #2 mining              → vòng lặp train, đường cong bị-lừa giảm
  #3 calibration         → ngưỡng từ chối @97% precision
  #1 ablation            → bỏ từng món, chứng minh nó đáng tiền

CHỈ TRAIN TRỤC NGỮ NGHĨA. Lý do: lớp tất định đã bắt 6 trục kia với 0.977 và
giải trình được từng phán quyết. Bắt model học lại = lãng phí + loãng.
Đây cũng chính là câu trả lời CENTRALITY cho giám khảo Meta:
  "bọn em đo ranh giới rule/model, và chỉ dùng model ở chỗ rule KHÔNG THỂ."

Chạy:
  uv run --python 3.11 --with torch --with transformers --with underthesea \
      --with matplotlib --with numpy python guard/don4_phobert.py --nhanh
"""

from __future__ import annotations

import argparse
import csv
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
MODEL = "vinai/phobert-base"  # MIT. KHÔNG dùng v2 (AGPL)
MAX_LEN = 256  # đo thật: 25,9% khoản vượt 128 token
DATA = Path("./data/guard")
OUT = Path("./artifacts/guard")

TRUC_NGU_NGHIA = {
    "bia_tong_quat_hoa",
    "bia_tu_du_dieu_kien",
    "bia_bo_rang_buoc",
    "bia_suy_dien",
    "bia_ngu_nghia_tai_cho",  # trục phá-cue: negative trùng-từ-vựng premise
}


def boot_f1_cum(lg: np.ndarray, y: np.ndarray, rng: random.Random, n: int = 1000):
    """CI bootstrap F1 grounded — resample có hoàn lại. Trả (lo, hi) 95%.

    Vì sao có: sau leave-templates-out, negative gom về ít chuỗi gốc; báo F1
    trần trụi mà không CI thì giám khảo không biết dao động bao nhiêu.
    """
    pred = lg.argmax(1)
    m = len(y)
    fs = []
    for _ in range(n):
        idx = [rng.randrange(m) for _ in range(m)]
        p, t = pred[idx], y[idx]
        tp = int(((p == 1) & (t == 1)).sum())
        fp = int(((p == 1) & (t == 0)).sum())
        fn = int(((p == 0) & (t == 1)).sum())
        pr = tp / max(tp + fp, 1)
        rc = tp / max(tp + fn, 1)
        fs.append(2 * pr * rc / max(pr + rc, 1e-9))
    fs.sort()
    return float(fs[int(0.025 * n)]), float(fs[int(0.975 * n)])


def dat_seed(s: int = SEED) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def nap(ten: str) -> list[dict]:
    """Chỉ giữ positive + 4 trục ngữ nghĩa."""
    ra = []
    with (DATA / f"{ten}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["label"] == 0 and r["corruption_type"] not in TRUC_NGU_NGHIA:
                continue
            ra.append(r)
    return ra


def can_bang(rows: list[dict], rng: random.Random, tran: int | None = None) -> list[dict]:
    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]
    n = min(len(pos), len(neg))
    if tran:
        n = min(n, tran // 2)
    ra = rng.sample(pos, n) + rng.sample(neg, n)
    rng.shuffle(ra)
    return ra


def can_bang_giu_hard(goc: list[dict], hard: list[dict], rng: random.Random) -> list[dict]:
    """GIỮ hard-negative vừa đào, chỉ loại bớt negative THƯỜNG.

    🐛 Bug bản đầu: gọi thẳng can_bang(cur + them) → nó sample ngẫu nhiên neg
    xuống, vứt gần hết hard vừa đào. Đào xong ném đi → đường cong dao động.
    """
    pos = [r for r in goc if r["label"] == 1]
    thuong = [r for r in goc if r["label"] == 0]
    can = len(pos)
    giu = hard[:can]
    if len(giu) < can and thuong:
        giu += rng.sample(thuong, min(can - len(giu), len(thuong)))
    ra = pos + giu
    rng.shuffle(ra)
    return ra


def grounding_margin_loss(logits, y, margin: float = 2.0):
    """Ép KHOẢNG CÁCH logit đúng/sai ≥ margin.

    Cross-entropy chỉ cần đoán đúng lớp. Guard cần model TỰ TIN TÁCH BẠCH —
    vì ngưỡng từ chối cắt trên khoảng cách đó. Rule không có khái niệm này.
    Đây là món PyTorch thật, không phải if-else.
    """
    dung = logits.gather(1, y.view(-1, 1)).squeeze(1)
    sai = logits.gather(1, (1 - y).view(-1, 1)).squeeze(1)
    return torch.relu(margin - (dung - sai)).mean()


def softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def ece(prob: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = prob.max(1), prob.argmax(1)
    dung = (pred == y).astype(float)
    e = 0.0
    for i in range(bins):
        m = (conf > i / bins) & (conf <= (i + 1) / bins)
        if m.sum():
            e += m.mean() * abs(dung[m].mean() - conf[m].mean())
    return float(e)


def calibrate(lg: np.ndarray, y: np.ndarray) -> float:
    """Temperature scaling. FIX BUG T-ÂM ngay từ dòng đầu, không chờ nó nổ.

    LBFGS trên logit của model train bằng margin-loss có thể ra T<0 → xác suất
    lật ngược → ECE nổ 0.118→0.50. Tham số hoá qua log_T: T=exp(log_T) luôn >0.
    """
    z, t = torch.from_numpy(lg), torch.from_numpy(y)
    log_T = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_T], lr=0.1, max_iter=60)
    ce = nn.CrossEntropyLoss()

    def closure():
        opt.zero_grad()
        T = torch.exp(log_T).clamp(0.05, 20.0)
        loss = ce(z / T, t)
        loss.backward()
        return loss

    opt.step(closure)
    return float(torch.exp(log_T).clamp(0.05, 20.0).item())


def nguong_refuse(prob: np.ndarray, y: np.ndarray, muc: float = 0.97) -> float | None:
    """Ngưỡng NHỎ NHẤT mà precision nhãn 'grounded' ≥ mục tiêu.

    Domain luật đặt 97% (không phải 95% như bán lẻ): khuyên DN nộp sai hồ sơ
    đắt hơn nhiều so với nói "chưa đủ căn cứ".
    """
    p1 = prob[:, 1]
    for th in np.arange(0.50, 0.999, 0.005):
        m = p1 >= th
        if m.sum() >= 20 and (y[m] == 1).mean() >= muc:
            return float(th)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhanh", action="store_true", help="1.2k cặp, 2 epoch — CPU chạy được")
    ap.add_argument("--vong-mining", type=int, default=3)
    args = ap.parse_args()

    tran = 1200 if args.nhanh else None
    epochs = 2 if args.nhanh else 3
    bs = 16

    dat_seed()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODEL)

    try:
        from underthesea import word_tokenize

        def tach(s: str) -> str:
            return word_tokenize(s, format="text")
    except Exception:  # noqa: BLE001
        def tach(s: str) -> str:
            return s

    def batch(rows):
        p = [tach(r["premise"][:1200]) for r in rows]
        h = [tach(r["hypothesis"][:500]) for r in rows]
        enc = tok(p, h, truncation=True, max_length=MAX_LEN, padding=True, return_tensors="pt")
        return {k: v.to(dev) for k, v in enc.items()}, torch.tensor(
            [r["label"] for r in rows]
        ).to(dev)

    def train(rows, margin=True, ep=epochs):
        dat_seed()
        m = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2).to(dev)
        opt = torch.optim.AdamW(m.parameters(), lr=2e-5)
        ce = nn.CrossEntropyLoss()
        m.train()
        for _ in range(ep):
            idx = list(range(len(rows)))
            rng.shuffle(idx)
            for i in range(0, len(idx), bs):
                b = [rows[j] for j in idx[i : i + bs]]
                enc, y = batch(b)
                opt.zero_grad()
                lg = m(**enc).logits
                loss = ce(lg, y)
                if margin:
                    loss = loss + 0.7 * grounding_margin_loss(lg, y)
                loss.backward()
                opt.step()
        return m

    @torch.no_grad()
    def logit(m, rows):
        m.eval()
        out = []
        for i in range(0, len(rows), 32):
            enc, _ = batch(rows[i : i + 32])
            out.append(m(**enc).logits.cpu().numpy())
        return np.vstack(out), np.array([r["label"] for r in rows])

    def do(lg, y):
        pred = lg.argmax(1)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        p = tp / max(tp + fp, 1)
        r = tp / max(tp + fn, 1)
        f1 = 2 * p * r / max(p + r, 1e-9)
        bat = int(((pred == 0) & (y == 0)).sum()) / max(int((y == 0).sum()), 1)
        return f1, bat

    tr = can_bang(nap("train"), rng, tran)
    ca = can_bang(nap("calib"), rng, 600)
    te = can_bang(nap("test"), rng, 600)
    pool = [r for r in nap("train") if r["label"] == 0]

    print(f"{MODEL} (MIT) · {dev} · max_len={MAX_LEN}")
    print(f"train {len(tr)} · calib {len(ca)} · test {len(te)}")
    print("CHỈ trục ngữ nghĩa — 6 trục kia lớp tất định đã bắt 0.977\n")
    t0 = time.time()

    # ═══ ĐÒN #2 — mining ═══════════════════════════════════════
    print("=" * 56)
    print("ĐÒN #2 — iterative hard-negative mining")
    print("=" * 56)
    cur, hard, duong = list(tr), [], []
    for v in range(args.vong_mining):
        m = train(cur)
        lg, y = logit(m, te)
        _, bat = do(lg, y)
        duong.append(1 - bat)
        print(f"  vòng {v}: bị lừa {(1-bat)*100:5.1f}%  (train {len(cur)}, hard giữ {len(hard)})  {time.time()-t0:.0f}s")
        if v == args.vong_mining - 1:
            break
        mau = rng.sample(pool, min(600, len(pool)))
        p1 = softmax(logit(m, mau)[0])[:, 1]
        them = [mau[i] for i in np.argsort(-p1)[:150] if p1[i] > 0.5]
        if not them:
            print("  (không đào được thêm)")
            break
        hard.extend(them)
        cur = can_bang_giu_hard(tr, hard, rng)

    m_full = m

    # ═══ ĐÒN #3 — calibration ══════════════════════════════════
    print("\n" + "=" * 56)
    print("ĐÒN #3 — temperature scaling")
    print("=" * 56)
    lg_c, y_c = logit(m_full, ca)
    lg_t, y_t = logit(m_full, te)
    e_truoc = ece(softmax(lg_t), y_t)
    T = calibrate(lg_c, y_c)
    e_sau = ece(softmax(lg_t / T), y_t)
    print(f"  T = {T:.4f}  ({'✓ dương' if T > 0 else '✗ ÂM — bug!'})")
    print(f"  ECE {e_truoc:.4f} → {e_sau:.4f}" + ("  ✓ giảm" if e_sau < e_truoc else "  ⚠ KHÔNG giảm"))
    assert T > 0, "T ÂM — kiểm lại exp(log_T)"
    th = nguong_refuse(softmax(lg_t / T), y_t, 0.97)
    print(f"  ngưỡng từ chối @precision 97%: {th if th else 'KHÔNG ĐẠT'}")

    # ═══ ĐÒN #1 — ablation ═════════════════════════════════════
    print("\n" + "=" * 56)
    print("ĐÒN #1 — ablation (cùng seed / cùng test / cùng epoch)")
    print("=" * 56)
    bang = []
    f1, bat = do(lg_t, y_t)
    f1_lo, f1_hi = boot_f1_cum(lg_t, y_t, rng)  # CI 95% cho F1 headline
    print(f"  Full F1 = {f1:.3f}  (CI95 [{f1_lo:.3f}, {f1_hi:.3f}])")
    bang.append(("Full", f1, bat, th))

    m2 = train(cur, margin=False)
    lg2, _ = logit(m2, te)
    f2, b2 = do(lg2, y_t)
    T2 = calibrate(logit(m2, ca)[0], y_c)
    bang.append(("− margin loss", f2, b2, nguong_refuse(softmax(lg2 / T2), y_t, 0.97)))

    m3 = train(tr)  # không mining
    lg3, _ = logit(m3, te)
    f3, b3 = do(lg3, y_t)
    T3 = calibrate(logit(m3, ca)[0], y_c)
    bang.append(("− hard-neg mining", f3, b3, nguong_refuse(softmax(lg3 / T3), y_t, 0.97)))

    bang.append(("− calibration", f1, bat, nguong_refuse(softmax(lg_t), y_t, 0.97)))
    bang.append(("− NLI (chỉ rule)", 0.0, 0.0, None))  # rule mù hoàn toàn trục ngữ nghĩa

    print(f"\n  {'bản':22} {'F1':>7} {'bắt bịa':>9} {'ngưỡng từ chối':>15}")
    for t_, f_, b_, th_ in bang:
        print(f"  {t_:22} {f_:7.3f} {b_:9.3f} {str(th_ or 'không đạt'):>15}")

    with (OUT / "ablation_phobert.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ban", "f1", "bat_bia", "nguong_refuse"])
        w.writerows(bang)

    print("\n  ⭐ Dòng '− NLI (chỉ rule)' = 0.000 — lớp tất định MÙ HOÀN TOÀN trục")
    print("     ngữ nghĩa. Đây là CENTRALITY: không có model thì 4 kiểu bịa này lọt hết.")

    (OUT / "phobert_ket_qua.json").write_text(
        json.dumps(
            {"T": T, "ece_truoc": e_truoc, "ece_sau": e_sau, "nguong_refuse": th,
             "f1_full": f1, "f1_lo": f1_lo, "f1_hi": f1_hi,
             "mining_curve": duong, "ablation": [list(x) for x in bang],
             "n_train": len(tr), "n_test": len(te), "device": str(dev),
             "giay": round(time.time() - t0)},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(5, 3.2))
        plt.plot([d * 100 for d in duong], "o-")
        plt.xlabel("vòng mining"); plt.ylabel("tỉ lệ bị lừa (%)")
        plt.title("Đòn #2 — hard-negative mining (PhoBERT)")
        plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(OUT / "mining_phobert.png", dpi=130)
    except Exception as e:  # noqa: BLE001
        print(f"(bỏ biểu đồ: {e})")

    m_full.save_pretrained(OUT / "phobert_guard")
    tok.save_pretrained(OUT / "phobert_guard")
    print(f"\n✓ xong {time.time()-t0:.0f}s → {OUT}/  (checkpoint đã .gitignore — luật E2)")


if __name__ == "__main__":
    main()
