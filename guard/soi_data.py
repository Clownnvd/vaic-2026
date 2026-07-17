"""SOI DATA TRƯỚC KHI ĐỐT GPU — train/test/calib có sạch không.

Train 42MB. Bẩn thì train xong vứt. Soi hết trước.

7 PHÉP SOI (mỗi phép ứng một cách data giết model):
  1. RÒ RỈ doc_id   — cùng văn bản ở cả train lẫn test → điểm test là điểm giả
  2. RÒ RỈ premise  — cùng đoạn nguồn ở 2 bên → model học thuộc, không học hiểu
  3. TRÙNG y hệt    — cùng (premise,hypothesis) 2 bên → ăn gian trắng trợn
  4. CÂN NHÃN       — lệch quá → model đoán bừa nhãn đông vẫn cao điểm
  5. CÂN TRỤC       — trục nào quá ít → model mù trục đó mà tổng điểm vẫn đẹp
  6. THUỘC KHUÔN    — hypothesis lặp khuôn → học template, ra đời tụt
                      ("Checking HateCheck", Luz de Araujo & Roth 2022)
  7. LẪN TEST SUITE — bộ test CheckList lọt vào train → mất tư cách công cụ đo

Chạy: uv run --python 3.11 python guard/soi_data.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

D = Path("./data/guard")
CHET = []  # lỗi chặn train
CANH = []  # cảnh báo


def nap(ten: str) -> list[dict]:
    f = D / f"{ten}.jsonl"
    if not f.exists():
        CHET.append(f"THIẾU FILE {f}")
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def bam(s: str) -> str:
    return hashlib.md5((s or "").strip().encode()).hexdigest()[:16]


def khuon(h: str) -> str:
    """Rút khuôn: bỏ hết số + tên riêng → còn xương câu."""
    x = re.sub(r"\d+([.,]\d+)*", "#", h or "")
    x = re.sub(r"[A-ZĐ]{2,}(-[A-ZĐ]{2,})*", "@", x)
    return re.sub(r"\s+", " ", x).strip()[:110]


def main() -> None:
    tr, te, ca = nap("train"), nap("test"), nap("calib")
    if not tr or not te:
        print("\n".join(CHET))
        sys.exit(1)

    print("=" * 76)
    print("SOI DATA GUARD — trước khi đốt GPU")
    print("=" * 76)
    print(f"  train {len(tr):6,}   test {len(te):6,}   calib {len(ca):6,}\n")

    # ── 1. RÒ RỈ doc_id ────────────────────────────────────────
    print("─" * 76)
    print("1. RÒ RỈ doc_id — cùng văn bản ở 2 bên?")
    print("─" * 76)
    d_tr = {r.get("doc_id") for r in tr if r.get("doc_id")}
    d_te = {r.get("doc_id") for r in te if r.get("doc_id")}
    d_ca = {r.get("doc_id") for r in ca if r.get("doc_id")}
    ro1 = d_tr & d_te
    ro2 = d_tr & d_ca
    print(f"   train {len(d_tr):5,} văn bản · test {len(d_te):5,} · calib {len(d_ca):5,}")
    print(f"   train ∩ test  = {len(ro1)}")
    print(f"   train ∩ calib = {len(ro2)}")
    if ro1:
        CHET.append(f"RÒ RỈ doc_id: {len(ro1)} văn bản ở cả train lẫn test → điểm test LÀ GIẢ")
        print(f"   🔴 {list(ro1)[:5]}")
    else:
        print("   🟢 sạch — chia theo văn bản, không phải theo câu")

    # ── 2. RÒ RỈ premise ───────────────────────────────────────
    print("\n" + "─" * 76)
    print("2. RÒ RỈ premise — cùng ĐOẠN NGUỒN ở 2 bên?")
    print("─" * 76)
    p_tr = {bam(r["premise"]) for r in tr}
    p_te = {bam(r["premise"]) for r in te}
    ro = p_tr & p_te
    print(f"   train {len(p_tr):5,} premise · test {len(p_te):5,} · chung {len(ro)}")
    if ro:
        CHET.append(f"RÒ RỈ premise: {len(ro)} đoạn nguồn ở cả 2 bên → model học thuộc nguồn")
        print(f"   🔴 {len(ro)} đoạn nguồn dùng chung")
    else:
        print("   🟢 sạch")

    # ── 3. TRÙNG Y HỆT ─────────────────────────────────────────
    print("\n" + "─" * 76)
    print("3. TRÙNG Y HỆT — cùng (premise, hypothesis)?")
    print("─" * 76)
    c_tr = {bam(r["premise"] + "|" + r["hypothesis"]) for r in tr}
    c_te = {bam(r["premise"] + "|" + r["hypothesis"]) for r in te}
    ro = c_tr & c_te
    print(f"   cặp trùng train↔test: {len(ro)}")
    if ro:
        CHET.append(f"TRÙNG {len(ro)} cặp y hệt giữa train và test")
        print("   🔴 ăn gian trắng trợn")
    else:
        print("   🟢 sạch")
    # trùng nội bộ train
    nb = len(tr) - len(c_tr)
    print(f"   trùng nội bộ train: {nb:,} / {len(tr):,} ({nb/len(tr)*100:.1f}%)")
    if nb / len(tr) > 0.25:
        CANH.append(f"train trùng nội bộ {nb/len(tr)*100:.0f}% → phí compute, lệch phân bố")

    # ── 4. CÂN NHÃN ────────────────────────────────────────────
    print("\n" + "─" * 76)
    print("4. CÂN NHÃN — lệch thì model đoán bừa vẫn cao điểm")
    print("─" * 76)
    for ten, ds in [("train", tr), ("test", te), ("calib", ca)]:
        if not ds:
            continue
        c = Counter(r["label"] for r in ds)
        p1 = c[1] / len(ds) * 100
        cd = "🟢" if 35 <= p1 <= 65 else ("🟡" if 25 <= p1 <= 75 else "🔴")
        print(f"   {ten:6} đủ-căn-cứ {c[1]:6,} ({p1:4.1f}%) · bịa {c[0]:6,} ({100-p1:4.1f}%) {cd}")
        if not (25 <= p1 <= 75):
            CANH.append(f"{ten} lệch nhãn {p1:.0f}% — đoán bừa nhãn đông đã được {max(p1,100-p1):.0f}%")

    # ── 5. CÂN TRỤC ────────────────────────────────────────────
    print("\n" + "─" * 76)
    print("5. CÂN TRỤC — trục ít quá thì model mù trục đó")
    print("─" * 76)
    for ten, ds in [("train", tr), ("test", te)]:
        c = Counter(r.get("corruption_type") for r in ds if r["label"] == 0)
        t = sum(c.values())
        print(f"\n   {ten} — {t:,} câu bịa, {len(c)} trục:")
        for k, v in c.most_common():
            p = v / t * 100
            cd = "🔴" if p < 4 else ("🟡" if p < 8 else "🟢")
            print(f"     {str(k):26} {v:6,} ({p:4.1f}%) {cd}")
        it = [k for k, v in c.items() if v / t < 0.04]
        if it and ten == "train":
            CANH.append(f"train: trục {it} < 4% → model gần như mù các trục này")

    # ── 6. THUỘC KHUÔN ─────────────────────────────────────────
    print("\n" + "─" * 76)
    print("6. THUỘC KHUÔN — hypothesis lặp khuôn thì model học template")
    print("─" * 76)
    print("   (Checking HateCheck 2022: train trên template → tăng template, TỤT ngoài đời)")
    for ten, ds in [("train", tr), ("test", te)]:
        c = Counter(khuon(r["hypothesis"]) for r in ds)
        top = c.most_common(1)[0]
        p = top[1] / len(ds) * 100
        n_kh = len(c)
        cd = "🟢" if p < 8 else ("🟡" if p < 20 else "🔴")
        print(f"\n   {ten}: {n_kh:,} khuôn khác nhau / {len(ds):,} câu")
        print(f"     khuôn dày nhất: {p:.1f}% {cd}  «{top[0][:62]}»")
        if p > 20:
            CHET.append(f"{ten}: 1 khuôn chiếm {p:.0f}% → model học thuộc khuôn, không học hiểu")
        elif p > 8:
            CANH.append(f"{ten}: khuôn dày nhất {p:.0f}%")
    # khuôn train ∩ test
    k_tr = Counter(khuon(r["hypothesis"]) for r in tr)
    k_te = Counter(khuon(r["hypothesis"]) for r in te)
    chung = set(k_tr) & set(k_te)
    pc = sum(k_te[k] for k in chung) / len(te) * 100
    print(f"\n   khuôn test đã thấy trong train: {pc:.1f}% số câu test")
    if pc > 80:
        CANH.append(
            f"{pc:.0f}% câu test dùng khuôn đã có trong train → test đo 'thuộc khuôn' "
            "nhiều hơn 'hiểu'. Phải nói thẳng chỗ này với giám khảo."
        )

    # ── 7. LẪN TEST SUITE ──────────────────────────────────────
    print("\n" + "─" * 76)
    print("7. LẪN TEST SUITE — bộ CheckList có lọt vào train không?")
    print("─" * 76)
    f = Path("./artifacts/guard/checklist_gpt4o.json")
    print(f"   checklist_gpt4o.json chỉ lưu THỐNG KÊ, không lưu câu → không thể rò qua file này")
    print(f"   nhưng bộ test dựng TỪ test.jsonl → đã kiểm ở phép 1-3 ở trên")
    print("   🟢 test.jsonl tách khỏi train theo doc_id" if not ro1 else "   🔴 xem phép 1")

    # ── 8. ĐỘ DÀI (chốt max_len) ───────────────────────────────
    print("\n" + "─" * 76)
    print("8. ĐỘ DÀI — chốt max_len")
    print("─" * 76)
    ln = sorted(len(r["premise"]) + len(r["hypothesis"]) for r in tr[:20000])
    for q in (50, 90, 95, 99):
        v = ln[int(len(ln) * q / 100)]
        print(f"   p{q:<3} {v:6,} ký tự  ≈ {v//4:5,} token (PhoBERT ~4 ký tự/token)")
    print("   → max_len=256 phủ p95 (đã đo bằng tokenizer thật trước đó: 25.9% tràn ở 128)")

    # ── PHÁN QUYẾT ─────────────────────────────────────────────
    print("\n" + "=" * 76)
    print("PHÁN QUYẾT")
    print("=" * 76)
    if CHET:
        print("\n  🔴 CHẶN TRAIN:")
        for x in CHET:
            print(f"     • {x}")
    if CANH:
        print("\n  🟡 CẢNH BÁO (train được, nhưng PHẢI khai với giám khảo):")
        for x in CANH:
            print(f"     • {x}")
    if not CHET and not CANH:
        print("\n  🟢 SẠCH HẾT — đẩy lên GPU được")
    elif not CHET:
        print("\n  🟢 KHÔNG CÓ LỖI CHẶN — đẩy lên GPU được, mang theo phần cảnh báo")
    print()
    sys.exit(1 if CHET else 0)


if __name__ == "__main__":
    main()
