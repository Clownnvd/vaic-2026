"""Chạy CẢ 4 ĐÒN trên model nhẹ (CPU) → verify pipeline trước khi lên PhoBERT.

  #4 sinh hard-negative      → đã xong ở guard/make_data.py
  #2 hard-negative mining    → mining_curve.png
  #3 calibration             → reliability.png + ece.txt
  #1 ablation                → ablation_table.csv + ablation.png

Chạy: uv run --python 3.11 --with torch --with numpy --with matplotlib python guard/run_4don.py
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, ".")
from guard.model_light import GuardNhe, featurize, grounding_margin_loss  # noqa: E402

SEED = 7
DATA = Path("./data/guard")
OUT = Path("./artifacts/guard")
DEV = torch.device("cpu")


def dat_seed(s: int = SEED) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def nap(ten: str, gioi_han: int | None = None) -> list[dict]:
    ra = []
    with (DATA / f"{ten}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            ra.append(json.loads(line))
            if gioi_han and len(ra) >= gioi_han:
                break
    return ra


def can_bang(rows: list[dict], rng: random.Random) -> list[dict]:
    """Undersample negative về 1:1. Không cân → model học 'cứ đoán bịa là đúng 83%'."""
    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]
    if len(neg) > len(pos):
        neg = rng.sample(neg, len(pos))
    ra = pos + neg
    rng.shuffle(ra)
    return ra


def can_bang_giu_hard(
    rows: list[dict], hard: list[dict], rng: random.Random
) -> list[dict]:
    """Cân 1:1 nhưng GIỮ BẰNG ĐƯỢC đám hard-negative vừa đào.

    🐛 BUG ĐÃ SỬA: bản đầu gọi thẳng can_bang(cur + them) → can_bang thấy neg>pos
    nên sample NGẪU NHIÊN neg xuống → vứt gần hết hard-negative vừa đào.
    Đào xong ném đi → đường mining dao động 55→24→36→73%, và ablation cho thấy
    BỎ mining lại tốt hơn. Đó là hệ quả của bug, không phải mining vô dụng.

    Sửa: hard-negative được ưu tiên giữ; chỉ loại bớt negative THƯỜNG để lấp chỗ.
    """
    pos = [r for r in rows if r["label"] == 1]
    thuong = [r for r in rows if r["label"] == 0]
    can = len(pos)

    giu = hard[:can]  # hard vào trước
    thieu = can - len(giu)
    if thieu > 0 and thuong:
        giu += rng.sample(thuong, min(thieu, len(thuong)))

    ra = pos + giu
    rng.shuffle(ra)
    return ra


def vec_hoa(rows: list[dict]) -> tuple[torch.Tensor, torch.Tensor]:
    X = np.stack([featurize(r["premise"], r["hypothesis"]) for r in rows])
    y = np.array([r["label"] for r in rows], dtype=np.int64)
    return torch.from_numpy(X), torch.from_numpy(y)


def train(
    rows: list[dict],
    dung_margin: bool = True,
    epochs: int = 6,
    lam: float = 0.7,
) -> GuardNhe:
    dat_seed()
    X, y = vec_hoa(rows)
    m = GuardNhe().to(DEV)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    n, bs = len(rows), 128

    m.train()
    for _ in range(epochs):
        idx = torch.randperm(n)
        for i in range(0, n, bs):
            b = idx[i : i + bs]
            opt.zero_grad()
            lg = m(X[b])
            loss = ce(lg, y[b])
            if dung_margin:
                loss = loss + lam * grounding_margin_loss(lg, y[b])
            loss.backward()
            opt.step()
    return m


@torch.no_grad()
def logit_cua(m: GuardNhe, rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    m.eval()
    X, y = vec_hoa(rows)
    return m(X).numpy(), y.numpy()


def do_f1(lg: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """F1 (lớp grounded) + bắt-bịa (recall lớp ungrounded) — đo ở argmax 0.5."""
    pred = lg.argmax(1)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    f1 = 2 * p * r / max(p + r, 1e-9)
    bat_bia = int(((pred == 0) & (y == 0)).sum()) / max(int((y == 0).sum()), 1)
    return f1, bat_bia


def softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def ece(prob: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf = prob.max(1)
    pred = prob.argmax(1)
    dung = (pred == y).astype(float)
    e = 0.0
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        m = (conf > lo) & (conf <= hi)
        if m.sum() == 0:
            continue
        e += m.mean() * abs(dung[m].mean() - conf[m].mean())
    return float(e)


def calibrate(lg_calib: np.ndarray, y_calib: np.ndarray) -> float:
    """Temperature scaling (Guo 2017) — học ĐÚNG 1 tham số, không đụng weights.

    ⚠️ BUG T-ÂM đã gặp thật: LBFGS trên logit của model train bằng margin-loss có
    thể tìm ra T < 0 → xác suất LẬT NGƯỢC → ECE nổ 0.118 → 0.50.
    → Tham số hoá qua log_T: T = exp(log_T) luôn > 0, + clamp 2 đầu. Áp NGAY,
      không chờ nó nổ.
    """
    z = torch.from_numpy(lg_calib)
    t = torch.from_numpy(y_calib)
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


def nguong_refuse(prob: np.ndarray, y: np.ndarray, muc_tieu: float = 0.97) -> float | None:
    """Ngưỡng NHỎ NHẤT mà precision của nhãn 'grounded' ≥ mục tiêu.

    Domain luật đặt 97% (không phải 95% như bán lẻ): khuyên DN nộp sai hồ sơ
    đắt hơn nhiều so với nói 'chưa đủ căn cứ'.
    """
    p1 = prob[:, 1]
    for th in np.arange(0.50, 0.999, 0.005):
        m = p1 >= th
        if m.sum() < 20:
            continue
        prec = (y[m] == 1).mean()
        if prec >= muc_tieu:
            return float(th)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gioi-han", type=int, default=12000, help="giới hạn cặp train")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    print("Nạp data…")
    tr = can_bang(nap("train", args.gioi_han), rng)
    ca = nap("calib", 3000)
    te = nap("test", 3000)
    print(f"  train {len(tr):,} (đã cân 1:1) · calib {len(ca):,} · test {len(te):,}\n")

    # ═══ ĐÒN #2 — hard-negative mining ═══════════════════════════
    print("=" * 58)
    print("ĐÒN #2 — iterative hard-negative mining")
    print("=" * 58)
    pool = [r for r in nap("train") if r["label"] == 0]
    cur = list(tr)
    hard_tich: list[dict] = []  # hard-negative TÍCH LUỸ qua các vòng, không được rơi
    duong: list[float] = []

    for vong in range(4):
        m = train(cur)
        lg, y = logit_cua(m, te)
        _, bat = do_f1(lg, y)
        bi_lua = 1 - bat
        duong.append(bi_lua)
        print(
            f"  vòng {vong}: bị lừa {bi_lua * 100:5.1f}%  "
            f"(train {len(cur):,} cặp, hard giữ {len(hard_tich):,})"
        )

        if vong == 3:
            break
        # đào: câu bịa mà model TƯỞNG là thật, sai-mà-tự-tin-cao lên đầu
        mau = rng.sample(pool, min(4000, len(pool)))
        lg_p, _ = logit_cua(m, mau)
        p1 = softmax(lg_p)[:, 1]
        thu_tu = np.argsort(-p1)[:400]
        them = [mau[i] for i in thu_tu if p1[i] > 0.5]
        if not them:
            print("  (không đào được thêm — dừng)")
            break
        hard_tich.extend(them)
        cur = can_bang_giu_hard(tr, hard_tich, rng)  # GIỮ hard, chỉ loại neg thường

    # ═══ ĐÒN #3 — calibration ════════════════════════════════════
    print("\n" + "=" * 58)
    print("ĐÒN #3 — temperature scaling")
    print("=" * 58)
    m_full = train(cur)
    lg_c, y_c = logit_cua(m_full, ca)
    lg_t, y_t = logit_cua(m_full, te)

    ece_truoc = ece(softmax(lg_t), y_t)
    T = calibrate(lg_c, y_c)
    ece_sau = ece(softmax(lg_t / T), y_t)

    print(f"  T = {T:.4f}   ({'✓ dương' if T > 0 else '✗ ÂM — bug!'})")
    print(f"  ECE trước = {ece_truoc:.4f}")
    print(f"  ECE sau   = {ece_sau:.4f}")
    assert T > 0, "T ÂM — bug đã biết, kiểm lại exp(log_T)"
    if ece_sau >= ece_truoc:
        print("  ⚠ ECE KHÔNG giảm → KHÔNG ghi số này lên slide, phải soi lại.")
    else:
        print(f"  ✓ ECE giảm {(1 - ece_sau / max(ece_truoc, 1e-9)) * 100:.0f}%")

    prob_t = softmax(lg_t / T)
    th = nguong_refuse(prob_t, y_t, 0.97)
    print(f"  Ngưỡng refuse @precision 97%: {th if th else 'KHÔNG ĐẠT — cần model mạnh hơn'}")

    (OUT / "ece.txt").write_text(
        f"T={T:.4f}\nECE_truoc={ece_truoc:.4f}\nECE_sau={ece_sau:.4f}\nnguong_refuse={th}\n",
        encoding="utf-8",
    )

    # ═══ ĐÒN #1 — ablation ═══════════════════════════════════════
    print("\n" + "=" * 58)
    print("ĐÒN #1 — ablation (cùng seed / cùng test / cùng epoch)")
    print("=" * 58)
    bang = []

    # Full
    f1, bat = do_f1(lg_t, y_t)
    bang.append(("Full", f1, bat, th))

    # − margin loss
    m2 = train(cur, dung_margin=False)
    lg2, _ = logit_cua(m2, te)
    f1_2, bat_2 = do_f1(lg2, y_t)
    lgc2, _ = logit_cua(m2, ca)
    T2 = calibrate(lgc2, y_c)
    th2 = nguong_refuse(softmax(lg2 / T2), y_t, 0.97)
    bang.append(("− margin loss", f1_2, bat_2, th2))

    # − hard-negative mining (chỉ dùng tập gốc)
    m3 = train(tr)
    lg3, _ = logit_cua(m3, te)
    f1_3, bat_3 = do_f1(lg3, y_t)
    lgc3, _ = logit_cua(m3, ca)
    T3 = calibrate(lgc3, y_c)
    th3 = nguong_refuse(softmax(lg3 / T3), y_t, 0.97)
    bang.append(("− hard-neg mining", f1_3, bat_3, th3))

    # − calibration (dùng xác suất thô)
    th4 = nguong_refuse(softmax(lg_t), y_t, 0.97)
    bang.append(("− calibration", f1, bat, th4))

    print(f"\n  {'bản':22} {'F1':>7} {'bắt bịa':>9} {'ngưỡng refuse':>14}")
    for ten, f1_, bat_, th_ in bang:
        print(f"  {ten:22} {f1_:7.3f} {bat_:9.3f} {str(th_ if th_ else 'không đạt'):>14}")

    with (OUT / "ablation_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ban", "f1", "bat_bia", "nguong_refuse"])
        w.writerows(bang)

    # bắt-bịa theo từng trục — bảng ăn tiền của domain luật
    print("\n  Bắt bịa theo TRỤC (bản Full):")
    pred = lg_t.argmax(1)
    for lo in sorted({r["corruption_type"] for r in te if r["corruption_type"]}):
        idx = [i for i, r in enumerate(te) if r["corruption_type"] == lo]
        if not idx:
            continue
        acc = float((pred[idx] == 0).mean())
        print(f"    {lo:28} {acc:5.3f}  (n={len(idx)})")

    # ═══ biểu đồ ═════════════════════════════════════════════════
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(5, 3.2))
        plt.plot([d * 100 for d in duong], "o-")
        plt.xlabel("vòng mining")
        plt.ylabel("tỉ lệ bị lừa (%)")
        plt.title("Đòn #2 — hard-negative mining")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(OUT / "mining_curve.png", dpi=130)
        print(f"\n✓ biểu đồ → {OUT}/mining_curve.png")
    except Exception as e:  # noqa: BLE001
        print(f"\n(bỏ qua biểu đồ: {e})")

    print(f"\nArtifacts → {OUT}/")


if __name__ == "__main__":
    main()
