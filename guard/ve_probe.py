"""Vẽ BIỂU ĐỒ HONEST từ artifact probe — trả lời "F1=1.000 chẳng phải học thuộc à".

2 panel:
  A) Artifact probe: hyp-only (giấu nguồn) trên từng tập/trục → phơi bày ĐÂU là
     artifact (đoán được không cần nguồn) và ĐÂU thật sự cần đối chiếu premise.
  B) Bậc thang giảm dần: full-model càng khử lối tắt càng tụt = học thật, không chạm trần.

Chạy: uv run --python 3.11 --with scikit-learn --with scipy --with matplotlib --with numpy python guard/ve_probe.py
"""
from __future__ import annotations

import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

import sys
sys.path.insert(0, ".")
from guard.probe_artifact import can_bang, nap, text_theo_che_do  # noqa: E402

SEED = 7
DATA = Path("data/guard")


def fit_eval(tr, te, che_do: str) -> float:
    vw = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True)
    vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=60000)
    Xtr = hstack([vw.fit_transform([text_theo_che_do(r, che_do) for r in tr]),
                  vc.fit_transform([text_theo_che_do(r, che_do) for r in tr])]).tocsr()
    Xte = hstack([vw.transform([text_theo_che_do(r, che_do) for r in te]),
                  vc.transform([text_theo_che_do(r, che_do) for r in te])]).tocsr()
    clf = LogisticRegression(max_iter=2000, C=4.0)
    clf.fit(Xtr, [r["label"] for r in tr])
    return float(f1_score([r["label"] for r in te], clf.predict(Xte), average="macro"))


def main() -> None:
    rng = random.Random(SEED)
    tr_easy = can_bang(nap(DATA / "train_easy.jsonl"), rng, 8000)
    tr_lto = can_bang(nap(DATA / "train.jsonl"), rng, 8000)

    # các tập test
    te_easy = can_bang(nap(DATA / "test_easy.jsonl"), rng, 2000)
    te_lto = can_bang(nap(DATA / "test.jsonl"), rng, 2000)
    te_so = can_bang(nap(DATA / "test.jsonl", neg_only={"sai_muc_phan_tram"}), rng, 2000)
    te_cue = can_bang(nap(DATA / "test.jsonl", neg_only={"bia_ngu_nghia_tai_cho"}), rng, 2000)

    # ── Panel A: hyp-only phơi bày artifact ──
    A = [
        ("Test CŨ\n(semantic, cân)", fit_eval(tr_easy, te_easy, "hypothesis-only"), "#dc2626"),
        ("Test KHÓ (LTO\n+ phá-cue)", fit_eval(tr_lto, te_lto, "hypothesis-only"), "#f59e0b"),
        ("Trục NGỮ NGHĨA\n(generic)", fit_eval(tr_lto, te_cue, "hypothesis-only"), "#f59e0b"),
        ("Trục SỐ\n(sai %)", fit_eval(tr_lto, te_so, "hypothesis-only"), "#16a34a"),
    ]
    # ── Panel B: full-model bậc thang ──
    B = [
        ("Test CŨ", fit_eval(tr_easy, te_easy, "full")),
        ("LTO (kiểu\nchưa thấy)", fit_eval(tr_lto, te_lto, "full")),
        ("LTO + phá-cue\n(chỉ tại-chỗ)", fit_eval(tr_lto, te_cue, "full")),
    ]

    fig = plt.figure(figsize=(13, 5.6), dpi=140)
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.24,
                          left=0.08, right=0.97, top=0.82, bottom=0.16)

    # Panel A
    ax = fig.add_subplot(gs[0, 0])
    xs = range(len(A))
    bars = ax.bar(xs, [v for _, v, _ in A], color=[c for *_, c in A], width=0.6, zorder=3)
    ax.axhline(0.5, ls="--", color="#6b7280", lw=1.3, zorder=2)
    ax.text(len(A) - 0.5, 0.52, "chance 0.5", fontsize=9, color="#6b7280", ha="right")
    for b, (_, v, _) in zip(bars, A):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_xticks(list(xs)); ax.set_xticklabels([n for n, *_ in A], fontsize=9.5)
    ax.set_ylim(0, 1.12); ax.set_ylabel("macro-F1 (chỉ nhìn CLAIM, giấu nguồn)", fontsize=10.5)
    ax.set_title("A. Artifact probe — model YẾU giấu nguồn còn giải được không?",
                 fontsize=12, fontweight="bold", pad=8)
    ax.grid(axis="y", color="#eee", zorder=0); ax.set_axisbelow(True)
    ax.annotate("1.00 = đoán được KHÔNG cần nguồn\n→ số cũ là ARTIFACT",
                xy=(0, 1.0), xytext=(0.35, 0.66), fontsize=9, color="#7f1d1d",
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.4),
                bbox=dict(boxstyle="round,pad=0.35", fc="#fef2f2", ec="#fecaca"))
    ax.annotate("0.37 < chance: text-only KHÔNG\nbiết số đúng/sai nếu không đọc\nnguồn → việc của lớp số tất định",
                xy=(3, A[3][1]), xytext=(1.5, 0.14), fontsize=8.8, color="#14532d",
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.4),
                bbox=dict(boxstyle="round,pad=0.35", fc="#f0fdf4", ec="#bbf7d0"))

    # Panel B
    ax2 = fig.add_subplot(gs[0, 1])
    ys = [v for _, v in B]
    ax2.plot(range(len(B)), ys, "o-", color="#2563eb", lw=2.2, ms=9, zorder=3)
    ax2.axhline(1.0, ls="--", color="#dc2626", lw=1.2)
    ax2.text(len(B) - 1, 1.005, "chạm trần 1.0 = đáng nghi", fontsize=8.6, color="#dc2626", ha="right", va="bottom")
    ax2.axhline(0.5, ls="--", color="#6b7280", lw=1.2)
    ax2.text(0, 0.51, "chance 0.5", fontsize=8.6, color="#6b7280")
    for i, (n, v) in enumerate(B):
        ax2.text(i, v - 0.045, f"{v:.2f}", ha="center", fontsize=11, fontweight="bold", color="#1e3a8a")
    ax2.set_xticks(range(len(B))); ax2.set_xticklabels([n for n, _ in B], fontsize=9.5)
    ax2.set_ylim(0.4, 1.08); ax2.set_ylabel("macro-F1 (full model)", fontsize=10.5)
    ax2.set_title("B. Càng khử lối tắt, số càng TỤT = học thật",
                  fontsize=12, fontweight="bold", pad=8)
    ax2.grid(axis="y", color="#eee", zorder=0); ax2.set_axisbelow(True)
    ax2.annotate("mỗi lần bịt 1 lối tắt số tụt\nđúng hướng dự đoán — KHÔNG\nchạm trần, cao hơn chance",
                 xy=(2, B[2][1]), xytext=(0.15, 0.62), fontsize=8.8, color="#1e3a8a",
                 arrowprops=dict(arrowstyle="->", color="#2563eb", lw=1.4))

    fig.suptitle("Guard PhoBERT — bằng chứng KHÔNG học thuộc: 1.000 cũ là artifact, "
                 "grounding thật ở lớp số (hyp-only 0.37)",
                 fontsize=13, fontweight="bold", y=0.95)

    out = Path("artifacts/guard/bang_chung_artifact.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    print("→", out)
    print("Panel A:", [(n, round(v, 3)) for n, v, _ in A])
    print("Panel B:", [(n.replace(chr(10), " "), round(v, 3)) for n, v in B])


if __name__ == "__main__":
    main()
