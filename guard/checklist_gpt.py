"""CHECKLIST — bắn test suite của mình vào GPT-4o, xem NÓ thủng ở đâu.

Phương pháp: CheckList (Ribeiro et al., ACL 2020 Best Paper — "Beyond Accuracy:
Behavioral Testing of NLP Models"). https://aclanthology.org/2020.acl-main.442/

VÌ SAO LÀM CÁI NÀY:
  Đội sinh câu bịa bằng rule, rồi bắt bằng rule của chính đội → VÒNG TRÒN.
  CheckList tự bảo vệ bằng cách bắn test vào model BÊN THỨ BA (Microsoft/Google/
  Amazon). Google Cloud sai 54.2% ở câu phủ định — không ai cãi được là "test
  thiết kế để bắt model của chính họ".
  → Bắn test suite vào GPT-4o. Đội KHÔNG kiểm soát GPT-4o.
    Lúc đó test suite hết là "đề tự chấm", nó thành CÔNG CỤ ĐO.

⛔ TUYỆT ĐỐI KHÔNG train trên bộ test này.
  "Checking HateCheck" (Luz de Araujo & Roth, NLP Power! 2022): đem functional
  test đi train → model học thuộc khuôn template, tăng trên template nhưng TỤT
  ngoài đời. Test suite chỉ để ĐO, không để DẠY.

BA LOẠI TEST (thuật ngữ CheckList):
  MFT (Minimum Functionality Test) — câu BỊA, model phải phát hiện
  INV (Invariance Test)           — câu ĐÚNG viết khác đi, model KHÔNG được đổi ý
                                     ← đội đang THIẾU HẲN loại này
  DIR (Directional Expectation)   — sửa theo hướng biết trước, kỳ vọng đổi theo

Chạy: $env:OPENAI_API_KEY=...; uv run --python 3.11 --with openai python guard/checklist_gpt.py
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, ".")

SEED = 7
OUT = Path("./artifacts/guard")

PROMPT = """Bạn là trợ lý pháp luật. Dưới đây là NGUỒN (trích từ văn bản pháp luật Việt Nam) và một CÂU KHẲNG ĐỊNH.

Nhiệm vụ: câu khẳng định đó có được NGUỒN ủng hộ hoàn toàn không?

NGUỒN:
{nguon}

CÂU KHẲNG ĐỊNH:
{claim}

Chỉ trả lời đúng một từ:
- CO   : nếu nguồn ủng hộ hoàn toàn câu khẳng định
- KHONG: nếu câu khẳng định sai, bịa, hoặc nguồn không đủ căn cứ"""


def sinh_inv(claim: str) -> tuple[str, str] | None:
    """INV test — viết LẠI câu ĐÚNG mà KHÔNG đổi nghĩa. Model không được đổi ý.

    Đội chưa bao giờ test loại này → không biết rule có BÁO ĐỘNG GIẢ không.
    """
    bien = [
        (r"\b50%", "một nửa", "phần trăm → chữ"),
        (r"\b100%", "toàn bộ", "phần trăm → chữ"),
        (r"\bNghị định\b", "NĐ", "viết tắt tên loại văn bản"),
        (r"\bThông tư\b", "TT", "viết tắt"),
        (r"\bdoanh nghiệp nhỏ và vừa\b", "DNNVV", "viết tắt nghiệp vụ"),
        (r"\bKhoản (\d+) Điều (\d+)\b", r"Điều \2 Khoản \1", "đảo thứ tự điều/khoản"),
    ]
    rng = random.Random(hash(claim) % 10000)
    rng.shuffle(bien)
    for pat, thay, mo_ta in bien:
        moi = re.sub(pat, thay, claim, count=1, flags=re.IGNORECASE)
        if moi != claim:
            return moi, mo_ta
    return None


def main() -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        # đọc từ .env
        env = Path(".env")
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise SystemExit("Không có OPENAI_API_KEY (đặt env hoặc .env)")

    from openai import OpenAI

    cli = OpenAI(api_key=key)
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(l) for l in Path("./data/guard/test.jsonl").read_text(encoding="utf-8").splitlines()]

    # ── dựng bộ test theo CAPABILITY (không gộp thành 1 số) ──
    theo_truc: dict[str, list] = defaultdict(list)
    for r in rows:
        if r["label"] == 0 and r["corruption_type"]:
            theo_truc[r["corruption_type"]].append(r)
    pos = [r for r in rows if r["label"] == 1]

    N = 12  # mỗi trục — đủ để thấy xu hướng, không đốt tiền
    bo_test = []
    for truc, ds in sorted(theo_truc.items()):
        for r in rng.sample(ds, min(N, len(ds))):
            bo_test.append({"loai": "MFT", "truc": truc, "mong": "KHONG", **r})

    # MFT âm tính: câu ĐÚNG, model phải nói CO
    for r in rng.sample(pos, min(N * 2, len(pos))):
        bo_test.append({"loai": "MFT", "truc": "(câu đúng)", "mong": "CO", **r})

    # ── INV: câu ĐÚNG viết khác đi — ĐỘI ĐANG THIẾU HẲN ──────
    n_inv = 0
    for r in rng.sample(pos, min(30, len(pos))):
        v = sinh_inv(r["hypothesis"])
        if v:
            moi, mo_ta = v
            bo_test.append(
                {"loai": "INV", "truc": f"INV: {mo_ta}", "mong": "CO",
                 "premise": r["premise"], "hypothesis": moi, "corruption_type": None}
            )
            n_inv += 1
        if n_inv >= N * 2:
            break

    print(f"Bộ test CheckList: {len(bo_test)} ca")
    print(f"  MFT (câu bịa)     : {sum(1 for x in bo_test if x['loai']=='MFT' and x['mong']=='KHONG')}")
    print(f"  MFT (câu đúng)    : {sum(1 for x in bo_test if x['loai']=='MFT' and x['mong']=='CO')}")
    print(f"  INV (đúng viết lại): {sum(1 for x in bo_test if x['loai']=='INV')}")
    print(f"\nBắn vào gpt-4o — model bên thứ ba, đội KHÔNG kiểm soát\n")

    ket = defaultdict(lambda: {"dung": 0, "tong": 0})
    t0 = time.time()
    for i, c in enumerate(bo_test):
        try:
            r = cli.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": PROMPT.format(
                    nguon=c["premise"][:1400], claim=c["hypothesis"][:400])}],
                temperature=0,
                max_tokens=5,
            )
            tl = (r.choices[0].message.content or "").strip().upper()
            tl = "CO" if tl.startswith("CO") else ("KHONG" if "KHONG" in tl else "?")
        except Exception as e:  # noqa: BLE001
            print(f"  lỗi {i}: {type(e).__name__}")
            continue

        k = f"{c['loai']}|{c['truc']}"
        ket[k]["tong"] += 1
        if tl == c["mong"]:
            ket[k]["dung"] += 1
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(bo_test)}  ({time.time()-t0:.0f}s)")

    # ── BÁO CÁO THEO CAPABILITY, KHÔNG GỘP 1 SỐ ─────────────
    print("\n" + "=" * 74)
    print("BẢNG CAPABILITY × TEST TYPE — gpt-4o thủng ở đâu")
    print("=" * 74)
    print(f"  {'loại':5} {'capability':30} {'GPT-4o sai':>11} {'n':>5}")
    print("  " + "-" * 60)
    for k in sorted(ket):
        loai, truc = k.split("|", 1)
        v = ket[k]
        sai = 1 - v["dung"] / max(v["tong"], 1)
        cd = "🔴" if sai > 0.3 else ("🟡" if sai > 0.1 else "🟢")
        print(f"  {loai:5} {truc:30} {sai*100:9.1f}% {v['tong']:5} {cd}")

    Path(OUT / "checklist_gpt4o.json").write_text(
        json.dumps(
            {
                "phuong_phap": "CheckList (Ribeiro et al., ACL 2020 Best Paper)",
                "model_do": "gpt-4o (bên thứ ba — đội KHÔNG kiểm soát)",
                "ket_qua": {k: dict(v) for k, v in ket.items()},
                "luu_y": "Đây là FAILURE RATE theo capability, KHÔNG phải accuracy tổng quát. "
                         "Test suite = công cụ ĐO, tuyệt đối không dùng để TRAIN "
                         "(Checking HateCheck: train trên template → học thuộc khuôn → tụt ngoài đời).",
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n  → {OUT}/checklist_gpt4o.json")
    print("\n  ⭐ Test suite này KHÔNG còn là 'đề tự chấm' — nó phát hiện lỗi ở")
    print("     model đội KHÔNG kiểm soát. Đúng chiêu CheckList dùng với MS/Google/Amazon.")


if __name__ == "__main__":
    main()
