"""ARTIFACT PROBE — biến chỉ trích "F1=1.000 là học thuộc" thành CON SỐ.

Ý tưởng (Poliak et al. 2018 "Hypothesis Only Baselines in NLI", *SEM/NAACL;
Gururangan et al. 2018 "Annotation Artifacts in NLI Data", NAACL):
  Train một model CHỈ nhìn hypothesis (giấu premise/nguồn). Nếu nó vẫn đạt
  cao → NHÃN đoán được KHÔNG cần nguồn → điểm cao là ARTIFACT bề mặt, không
  phải grounding. Đây là bằng-chứng-số cho chính lời chỉ trích.

3 chế độ, cùng vectorizer + classifier, chỉ khác PHẦN TEXT nhìn thấy:
  • hypothesis-only : chỉ hypothesis (bịt nguồn)
  • premise-only    : chỉ premise
  • full            : premise [SEP] hypothesis

Đọc BẰNG MẮT: nếu hyp-only ≈ full ≈ 1.0 còn premise-only ≈ 0.5 →
tác vụ giải được KHÔNG cần đối chiếu nguồn = artifact. Khi bịt lối tắt
(test copy-cue-broken), hyp-only PHẢI sập về ~chance thì trục mới mới "sạch".

Cũng là CỔNG KIỂM CHẤT LƯỢNG cho trục bia_ngu_nghia_tai_cho: nếu hyp-only
còn giải được negative mới → negative còn artifact, quay lại sửa corrupt.py.

Chạy: uv run --python 3.11 --with scikit-learn python guard/probe_artifact.py
      [--train data/guard/train.jsonl] [--test data/guard/test.jsonl]
CPU, ~vài giây.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

# 4 trục ngữ nghĩa + trục phá-cue mới (nếu có) — khớp don4_phobert.nap()
TRUC_NGU_NGHIA = {
    "bia_tong_quat_hoa",
    "bia_tu_du_dieu_kien",
    "bia_bo_rang_buoc",
    "bia_suy_dien",
    "bia_ngu_nghia_tai_cho",  # trục phá-cue (nếu đã regen)
}
SEED = 7


def nap(path: Path, neg_only: set[str] | None = None) -> list[dict]:
    """Chỉ giữ positive + trục ngữ nghĩa. neg_only: chỉ giữ negative thuộc trục này
    (để đo RIÊNG trục phá-cue = 'test copy-cue-broken')."""
    keep = neg_only if neg_only else TRUC_NGU_NGHIA
    ra = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["label"] == 0 and r.get("corruption_type") not in keep:
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


def text_theo_che_do(r: dict, che_do: str) -> str:
    p = (r["premise"] or "")[:1200]
    h = (r["hypothesis"] or "")[:500]
    if che_do == "hypothesis-only":
        return h
    if che_do == "premise-only":
        return p
    return p + " [SEP] " + h


def macro_f1(y, pred) -> float:
    from sklearn.metrics import f1_score

    return float(f1_score(y, pred, average="macro"))


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score

    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/guard/train.jsonl")
    ap.add_argument("--test", default="data/guard/test.jsonl")
    ap.add_argument("--neg-only", default="", help="chỉ giữ negative trục này ở TEST (vd bia_ngu_nghia_tai_cho)")
    args = ap.parse_args()

    neg = {args.neg_only} if args.neg_only else None
    rng = random.Random(SEED)
    tr = can_bang(nap(Path(args.train)), rng, tran=8000)
    te = can_bang(nap(Path(args.test), neg_only=neg), rng, tran=2000)
    ytr = [r["label"] for r in tr]
    yte = [r["label"] for r in te]

    print(f"train {len(tr)} · test {len(te)}  (pos/neg cân 1:1)")
    print(f"test file: {args.test}\n")
    print(f"{'chế độ':18} {'macro-F1':>9} {'F1_grounded':>12} {'F1_bia':>8}")
    print("-" * 50)

    ket = {}
    for che_do in ("hypothesis-only", "premise-only", "full"):
        vec = TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True
        )
        vec_char = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=60000
        )
        Xtr_w = vec.fit_transform([text_theo_che_do(r, che_do) for r in tr])
        Xtr_c = vec_char.fit_transform([text_theo_che_do(r, che_do) for r in tr])
        Xte_w = vec.transform([text_theo_che_do(r, che_do) for r in te])
        Xte_c = vec_char.transform([text_theo_che_do(r, che_do) for r in te])
        from scipy.sparse import hstack

        Xtr = hstack([Xtr_w, Xtr_c]).tocsr()
        Xte = hstack([Xte_w, Xte_c]).tocsr()

        clf = LogisticRegression(max_iter=2000, C=4.0)
        clf.fit(Xtr, ytr)
        pred = clf.predict(Xte)
        mf1 = float(f1_score(yte, pred, average="macro"))
        f1g = float(f1_score(yte, pred, pos_label=1))
        f1b = float(f1_score(yte, pred, pos_label=0))
        ket[che_do] = {"macro_f1": mf1, "f1_grounded": f1g, "f1_bia": f1b}
        print(f"{che_do:18} {mf1:9.3f} {f1g:12.3f} {f1b:8.3f}")

    # đọc số
    hyp = ket["hypothesis-only"]["macro_f1"]
    full = ket["full"]["macro_f1"]
    prem = ket["premise-only"]["macro_f1"]
    print("\n=== ĐỌC SỐ ===")
    if hyp >= 0.85:
        print(f"  ⚠ hypothesis-only = {hyp:.3f} ≈ full {full:.3f}: NHÃN ĐOÁN ĐƯỢC")
        print("    KHÔNG cần nhìn nguồn → điểm cao là ARTIFACT bề mặt, không phải grounding.")
    else:
        print(f"  ✓ hypothesis-only = {hyp:.3f} (thấp) → bịt nguồn thì SẬP.")
        print(f"    Khoảng cách full − hyp-only = {full - hyp:+.3f} = grounding thật")
        print("    (không giả được bằng trí nhớ hypothesis).")
    print(f"  premise-only = {prem:.3f}  (tham chiếu)")

    out = Path("artifacts/guard/probe_artifact.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"test": args.test, "n_train": len(tr), "n_test": len(te), "che_do": ket,
             "gap_full_hyp": full - hyp},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
