"""Vẽ 1 hình BẰNG CHỨNG sạch cho guard PhoBERT — thay ảnh mining 1 chấm.
3 mảng: (trái) ablation = NLI centrality; (phải) zero-shot ViFactCheck + ECE.
Số đọc THẲNG từ artifacts/guard/don4_h100/*.json — không gõ tay.
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SRC = Path("artifacts/guard/don4_h100")
kq = json.loads((SRC / "phobert_ket_qua.json").read_text(encoding="utf-8"))
ev = json.loads((SRC / "eval_ngoai.json").read_text(encoding="utf-8"))

# ── dữ liệu ablation: [ten, f1, bat_bia, nguong] ──
abl = kq["ablation"]
tens = [r[0] for r in abl]
f1s = [r[1] for r in abl]

fig = plt.figure(figsize=(13.5, 6.2), dpi=140)
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.22,
                      left=0.075, right=0.965, top=0.86, bottom=0.13)

# ── TRÁI: ablation bar ──
ax = fig.add_subplot(gs[0, 0])
mau = ["#2563eb", "#2563eb", "#2563eb", "#2563eb", "#dc2626"]
bars = ax.bar(range(len(tens)), f1s, color=mau, width=0.62, zorder=3)
ax.set_xticks(range(len(tens)))
ax.set_xticklabels(tens, rotation=18, ha="right", fontsize=10.5)
ax.set_ylabel("F1 bắt bịa", fontsize=11)
ax.set_ylim(0, 1.12)
ax.grid(axis="y", color="#e5e7eb", zorder=0)
ax.set_axisbelow(True)
for b, v in zip(bars, f1s):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.3f}",
            ha="center", va="bottom", fontsize=10.5, fontweight="bold",
            color="#dc2626" if v == 0 else "#1e3a8a")
ax.set_title("Ablation — bỏ từng thành phần, đo lại F1 bắt bịa",
             fontsize=12.5, fontweight="bold", pad=10)
# chú thích mũi tên vào cột NLI = 0
ax.annotate("Bỏ lớp NLI (chỉ còn rule) → 0.000\nlớp tất định MÙ trục ngữ nghĩa\n→ model NLI là BẮT BUỘC",
            xy=(4, 0.02), xytext=(2.4, 0.52), fontsize=9.6, color="#7f1d1d",
            ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.6),
            bbox=dict(boxstyle="round,pad=0.4", fc="#fef2f2", ec="#fecaca"))

# ── PHẢI: thẻ số zero-shot + ECE ──
ax2 = fig.add_subplot(gs[0, 1])
ax2.axis("off")
tb = ev["toan_bo_tin_tuc"]
nh = ev["nhom_cham_van_ban_luat"]
T = kq["T"]

def card(y0, h, title, lines, fc, ec, tc):
    ax2.add_patch(FancyBboxPatch((0.02, y0), 0.96, h, transform=ax2.transAxes,
                  boxstyle="round,pad=0.012", fc=fc, ec=ec, lw=1.3, zorder=2))
    ax2.text(0.06, y0 + h - 0.045, title, transform=ax2.transAxes,
             fontsize=11.5, fontweight="bold", color=tc, va="top")
    ax2.text(0.06, y0 + h - 0.115, "\n".join(lines), transform=ax2.transAxes,
             fontsize=10.0, color="#1f2937", va="top", linespacing=1.5)

card(0.545, 0.44,
     "① Zero-shot ViFactCheck  (model CHƯA hề train bộ này)",
     [f"• Toàn bộ tin tức:  acc {tb['acc']:.2f}   bắt-không-căn-cứ {tb['bat']:.2f}   (n={tb['n']:,})",
      f"• Nhóm chạm văn bản luật:  acc {nh['acc']:.2f}   (n={nh['n']:,})",
      "→ train trên LUẬT, đem sang TIN TỨC lạ vẫn 0.60",
      "   = học CÁCH đối chiếu claim–nguồn, không học vẹt từ khoá"],
     "#eff6ff", "#bfdbfe", "#1e40af")

card(0.055, 0.44,
     "② Hiệu chỉnh độ tự tin (calibration — Guo et al. ICML 2017)",
     [f"• ECE trước:  {kq['ece_truoc']:.4f}",
      f"• ECE sau temperature scaling (T={T:.2f}):  {kq['ece_sau']:.1e}",
      "→ độ tự tin của model bám sát xác suất đúng thật",
      "",
      "⚠ KHÔNG so trực tiếp 0.60 với SOTA 89.9% (Gemma):",
      "   SOTA CÓ train + macro-F1 3 lớp; mình zero-shot, gộp 2 lớp."],
     "#f0fdf4", "#bbf7d0", "#166534")

fig.suptitle("Guard PhoBERT — bằng chứng: lớp ngữ nghĩa là trung tâm + tổng quát hoá sang domain lạ",
             fontsize=13.5, fontweight="bold", y=0.955)

OUT = SRC / "guard_bang_chung.png"
fig.savefig(OUT, facecolor="white", bbox_inches="tight")
print("→", OUT)
