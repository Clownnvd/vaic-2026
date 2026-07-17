"""4-PANEL bằng chứng guard PhoBERT — SỐ THẬT, honest, không overclaim.

A) Artifact probe (hyp-only): 1.000 cũ là artifact; trục SỐ 0.37 = phụ thuộc premise.
B) Behavioral (phân vai): DIR-num PhoBERT-alone fail 99.5% → +rule 5%; INV 0.7%.
C) Không memorize: PhoBERT giữ F1 0.975 trên KIỂU bịa CHƯA THẤY (LTO) + CI.
D) Giới hạn thật (OOD news): model một mình ~chance — KHÔNG claim domain transfer.

Chạy: uv run --python 3.11 --with matplotlib --with numpy python guard/ve_4panel.py
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LTO = Path("artifacts/guard/lto")
kq = json.loads((LTO / "phobert_ket_qua.json").read_text(encoding="utf-8"))
beh = json.loads((LTO / "behavioral_phobert.json").read_text(encoding="utf-8"))["probe"]
lad = json.loads((LTO / "eval_ladder.json").read_text(encoding="utf-8"))["thang"]

# CPU artifact probe (ve_probe.py) — hyp-only theo trục
HYP = [("Test CŨ\n(semantic)", 1.00, "#dc2626"),
       ("Trục ngữ nghĩa\n(LTO)", 0.83, "#f59e0b"),
       ("Trục SỐ\n(sai %)", 0.38, "#16a34a")]

fig = plt.figure(figsize=(14.5, 9), dpi=140)
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.24, left=0.07, right=0.97, top=0.9, bottom=0.08)

# ── A ── artifact probe
ax = fig.add_subplot(gs[0, 0])
bars = ax.bar(range(len(HYP)), [v for _, v, _ in HYP], color=[c for *_, c in HYP], width=0.6, zorder=3)
ax.axhline(0.5, ls="--", color="#6b7280", lw=1.2); ax.text(2.4, 0.52, "chance", fontsize=8.5, color="#6b7280", ha="right")
for b, (_, v, _) in zip(bars, HYP):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", fontsize=11, fontweight="bold")
ax.set_xticks(range(len(HYP))); ax.set_xticklabels([n for n, *_ in HYP], fontsize=9.5)
ax.set_ylim(0, 1.12); ax.set_ylabel("macro-F1 khi GIẤU nguồn", fontsize=10)
ax.set_title("A. Artifact probe — hyp-only (Poliak 2018)", fontsize=12, fontweight="bold", pad=8)
ax.grid(axis="y", color="#eee", zorder=0); ax.set_axisbelow(True)
ax.annotate("1.00 = đoán được KHÔNG cần nguồn\n→ F1=1.000 cũ là ARTIFACT", xy=(0, 1.0), xytext=(0.3, 0.62),
            fontsize=8.6, color="#7f1d1d", arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.3),
            bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#fecaca"))
ax.annotate("0.38 < chance: SỐ phụ thuộc\npremise → việc lớp rule", xy=(2, 0.38), xytext=(0.9, 0.12),
            fontsize=8.4, color="#14532d", arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.3),
            bbox=dict(boxstyle="round,pad=0.3", fc="#f0fdf4", ec="#bbf7d0"))

# ── B ── behavioral / phân vai
ax2 = fig.add_subplot(gs[0, 1])
labs = ["INV\nparaphrase", "DIR-num\nPhoBERT\nMỘT MÌNH", "DIR-num\nFULL-STACK\n(+rule)", "DIR-sem\nPhoBERT"]
vals = [beh["INV_paraphrase"]["fail"], beh["DIR_num_PhoBERT_alone"]["fail"],
        beh["DIR_num_full_stack"]["fail"], beh["DIR_sem"]["fail"]]
cols = ["#16a34a", "#dc2626", "#16a34a", "#f59e0b"]
bars = ax2.bar(range(4), [v * 100 for v in vals], color=cols, width=0.62, zorder=3)
for b, v in zip(bars, vals):
    ax2.text(b.get_x() + b.get_width() / 2, v * 100 + 1.5, f"{v*100:.0f}%", ha="center", fontsize=10.5, fontweight="bold")
ax2.set_xticks(range(4)); ax2.set_xticklabels(labs, fontsize=8.6)
ax2.set_ylim(0, 112); ax2.set_ylabel("tỉ lệ SÓT (%) — thấp = tốt", fontsize=10)
ax2.set_title("B. Behavioral (CheckList) — phân vai rule/model", fontsize=12, fontweight="bold", pad=8)
ax2.grid(axis="y", color="#eee", zorder=0); ax2.set_axisbelow(True)
ax2.annotate("PhoBERT MÙ số (99%)\n→ +lớp số tất định\nsót còn 5%", xy=(2, 5), xytext=(2.15, 55),
             fontsize=8.5, color="#14532d", arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.4),
             bbox=dict(boxstyle="round,pad=0.3", fc="#f0fdf4", ec="#bbf7d0"))

# ── C ── không memorize
ax3 = fig.add_subplot(gs[1, 0])
C = [("Test CŨ\n(easy)", 1.000, "#9ca3af"), ("LTO — kiểu bịa\nCHƯA THẤY", kq["f1_full"], "#2563eb"),
     ("hyp-only\ntrên LTO", 0.83, "#dc2626")]
bars = ax3.bar(range(3), [v for _, v, _ in C], color=[c for *_, c in C], width=0.6, zorder=3)
# CI cho cột LTO
ax3.errorbar(1, kq["f1_full"], yerr=[[kq["f1_full"] - kq["f1_lo"]], [kq["f1_hi"] - kq["f1_full"]]],
             fmt="none", ecolor="#1e3a8a", capsize=5, lw=1.6, zorder=4)
ax3.axhline(0.5, ls="--", color="#6b7280", lw=1.2); ax3.text(2.4, 0.52, "chance", fontsize=8.5, color="#6b7280", ha="right")
for i, (_, v, _) in enumerate(C):
    ax3.text(i, v + 0.025, f"{v:.3f}", ha="center", fontsize=10.5, fontweight="bold")
ax3.set_xticks(range(3)); ax3.set_xticklabels([n for n, *_ in C], fontsize=9)
ax3.set_ylim(0, 1.15); ax3.set_ylabel("F1 (PhoBERT)", fontsize=10)
ax3.set_title("C. KHÔNG memorize — giữ 0.975 trên kiểu chưa thấy", fontsize=12, fontweight="bold", pad=8)
ax3.grid(axis="y", color="#eee", zorder=0); ax3.set_axisbelow(True)
ax3.annotate("model học thuộc thì LTO phải TỤT;\ngiữ 0.975 (CI hẹp) = tổng quát hoá.\ncao hơn hyp-only 0.83 = DÙNG premise",
             xy=(1, kq["f1_lo"]), xytext=(0.05, 0.30), fontsize=8.3, color="#1e3a8a",
             arrowprops=dict(arrowstyle="->", color="#2563eb", lw=1.3))

# ── D ── giới hạn thật OOD
ax4 = fig.add_subplot(gs[1, 1])
order = ["Guard-PhoBERT (zero-shot)", "Rule-only (lệch số)", "Majority", "SOTA in-domain (Gemma, CÓ train)"]
names = ["Guard-PhoBERT", "Rule-only", "Majority", "SOTA (CÓ train,\n3-lớp — tham chiếu)"]
vv = [lad[k]["macro_f1"] for k in order]
cc = ["#dc2626", "#9ca3af", "#6b7280", "#cbd5e1"]
bars = ax4.barh(range(4), vv, color=cc, zorder=3)
bars[-1].set_hatch("///")
for i, v in enumerate(vv):
    ax4.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=10, fontweight="bold")
ax4.axvline(0.5, ls="--", color="#6b7280", lw=1.1)
ax4.set_yticks(range(4)); ax4.set_yticklabels(names, fontsize=8.8)
ax4.set_xlim(0, 1.0); ax4.set_xlabel("macro-F1 (ViFactCheck NEWS, zero-shot)", fontsize=9.5)
ax4.set_title("D. Giới hạn THẬT — OOD news: model một mình ~chance", fontsize=12, fontweight="bold", pad=8)
ax4.grid(axis="x", color="#eee", zorder=0); ax4.set_axisbelow(True)
ax4.annotate("khai thẳng: train trên bịa-luật synthetic hẹp\n→ KHÔNG chuyển sang TIN TỨC. Guard dùng ở\nMIỀN LUẬT, hợp thành với lớp rule.",
             xy=(vv[0], 0), xytext=(0.30, 1.5), fontsize=8.0, color="#7f1d1d",
             bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#fecaca"))

fig.suptitle("Guard PhoBERT — 4 bằng chứng HONEST (số thật, không overclaim): "
             "artifact bị phơi · phân vai rule/model · không memorize · khai giới hạn OOD",
             fontsize=12.5, fontweight="bold", y=0.965)

out = Path("artifacts/guard/lto/guard_4panel.png")
fig.savefig(out, facecolor="white", bbox_inches="tight")
print("→", out)
