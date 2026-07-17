"""Đào câu bịa THẬT của GPT-4o — phá vòng tròn tự-sinh-tự-chấm.

VẤN ĐỀ GỐC:
  hard-negative của đội do RULE sinh (đổi 50%→80%), rồi cũng RULE bắt (so số).
  Vòng tròn. Giám khảo hỏi một câu là đứng hình.

ĐƯỜNG THOÁT (kiến trúc kho đã chốt: "LLM sinh → Guard NLI gác → chặn & sinh lại"):
  GPT-4o SINH câu trả lời thật từ điều luật thật
        ↓
  lớp TẤT ĐỊNH chấm (lookup_doc + lech_so — đã đo 0.974, báo động giả 0/541)
        ↓
  câu nào bịa → HARD-NEGATIVE THẬT của LLM
        ↓
  train PhoBERT trên đó

Vòng tròn ĐỨT vì người SINH (GPT-4o) và người BẮT (rule) là HAI BÊN ĐỘC LẬP —
đội không kiểm soát GPT-4o.

⚠️ Đây KHÁC hẳn phép đo checklist_gpt.py: ở đó hỏi GPT-4o làm GIÁM KHẢO
   (và nó dở: bỏ lọt 41.7% số nghị định giả, từ chối oan 62.5% câu đúng).
   Ở đây GPT-4o làm NGƯỜI SINH — đúng vai của nó trong rail.

Chạy: uv run --python 3.11 --with openai --with pyarrow python guard/dao_bia_that.py --n 40
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")

SEED = 7
OUT = Path("./data/guard")

# ⚠️ BẢN 1 CỦA PROMPT NÀY ĐÃ HỎNG — ghi lại để không ai làm lại:
#   Bản cũ bốc KHOẢN ngẫu nhiên ghép CÂU HỎI ngẫu nhiên trong danh sách cứng
#   ("mức hỗ trợ bao nhiêu %?"). Phần lớn khoản KHÔNG nói về thứ được hỏi
#   → GPT-4o trả lời rất đúng đắn: "Xin lỗi, đoạn văn bản bạn cung cấp không có
#   thông tin này" → 120/120 ca đều là LỜI TỪ CHỐI, KHÔNG PHẢI CÂU BỊA.
#   Đo được một điều tốt (GPT-4o thà từ chối còn hơn bịa) nhưng KHÔNG đo được
#   thứ định đo, và không đào ra hard-negative nào.
#
# BẢN 2: bắt GPT-4o DIỄN GIẢI CHÍNH KHOẢN ĐÓ. Đáp án chắc chắn nằm trong nguồn
# → nó không còn cửa từ chối → sai là BỊA THẬT, không phải "nguồn không có".
PROMPT = """Bạn là trợ lý tư vấn chính sách cho doanh nghiệp Việt Nam.

Đây là {vi_tri} của văn bản {so_vb} do {co_quan} ban hành:
---
{nguon}
---

Doanh nghiệp hỏi: "{hoi}"

Trả lời trong 1-2 câu, bám sát đoạn trên, TRÍCH DẪN căn cứ theo đúng mẫu:
"Theo Khoản <số> Điều <số> <số hiệu văn bản> do <cơ quan> ban hành, <nội dung>"

Trả lời:"""


def sinh_cau_hoi(text: str, rng: random.Random) -> str:
    """Câu hỏi RÚT TỪ CHÍNH KHOẢN — đáp án chắc chắn có trong nguồn.

    Ghép câu hỏi rời với khoản ngẫu nhiên (bản cũ) thì GPT-4o chỉ việc từ chối.
    Muốn thấy nó BỊA thì phải hỏi thứ nó TRẢ LỜI ĐƯỢC.
    """
    t = text.lower()
    ch = []
    if "%" in text or "phần trăm" in t:
        ch.append("Mức hỗ trợ theo tỷ lệ phần trăm ở đây là bao nhiêu?")
    if "đồng" in t or "triệu" in t or "tỷ" in t:
        ch.append("Quy định này nêu mức tiền cụ thể là bao nhiêu?")
    if "ngày" in t or "tháng" in t or "năm" in t:
        ch.append("Quy định này nêu mốc thời gian/thời hạn nào?")
    if "điều kiện" in t or "phải" in t or "đáp ứng" in t:
        ch.append("Doanh nghiệp phải đáp ứng điều kiện gì theo quy định này?")
    ch.append("Tóm tắt nội dung chính của quy định này cho doanh nghiệp.")
    return rng.choice(ch)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="số câu cho GPT-4o sinh")
    args = ap.parse_args()

    key = os.getenv("OPENAI_API_KEY")
    if not key and Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    if not key:
        raise SystemExit("Không có OPENAI_API_KEY")

    from openai import OpenAI
    import pyarrow.parquet as pq

    from guard.check import KetLuan, kiem_tra
    from guard.lookup import IndexCorpus

    cli = OpenAI(api_key=key)
    rng = random.Random(SEED)

    print("Nạp index corpus (trọng tài tất định)…")
    idx = IndexCorpus(Path("./data/splits_dn/test.parquet"))

    # lấy khoản THẬT làm nguồn
    from corpus.parse_dieu import parse

    tbl = pq.read_table(
        Path("./data/splits_dn/test.parquet"),
        columns=["item_id", "doc_number_str", "issuing_authority", "markdown"],
    )
    nguon = []
    for i in range(min(120, tbl.num_rows)):
        md = tbl["markdown"][i].as_py()
        if not md:
            continue
        for d in parse(md):
            for k in d.khoan:
                if 150 < len(k.text) < 900:
                    nguon.append(
                        {
                            "text": k.text,
                            "so_vb": tbl["doc_number_str"][i].as_py(),
                            "co_quan": tbl["issuing_authority"][i].as_py(),
                            "dieu": d.so,
                            "khoan": k.so,
                        }
                    )
        if len(nguon) > 400:
            break
    print(f"  {len(nguon)} khoản thật làm nguồn\n")

    print(f"GPT-4o SINH {args.n} câu trả lời (prompt KHÔNG nhắc 'đừng bịa')…")
    ket = []
    t0 = time.time()
    n_tu_choi = 0
    for i in range(args.n):
        n = rng.choice(nguon)
        hoi = sinh_cau_hoi(n["text"], rng)
        try:
            r = cli.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT.format(
                            hoi=hoi,
                            nguon=n["text"][:900],
                            vi_tri=f"Điều {n['dieu']} Khoản {n['khoan']}",
                            so_vb=n["so_vb"],
                            co_quan=n["co_quan"],
                        ),
                    }
                ],
                temperature=0.7,  # để nó tự nhiên, không quá thận trọng
                max_tokens=160,
            )
            tl = (r.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            print(f"  lỗi {i}: {type(e).__name__}")
            continue

        # tách LỜI TỪ CHỐI khỏi CÂU BỊA — bản cũ gộp chung nên 120/120 "sai" mà
        # thực ra toàn là GPT-4o từ chối đúng đắn. Từ chối ≠ bịa.
        if any(x in tl.lower()[:60] for x in ("xin lỗi", "rất tiếc", "không có thông tin", "không đủ")):
            n_tu_choi += 1
            continue

        # ── TRỌNG TÀI TẤT ĐỊNH chấm ────────────────────────
        pq_ = kiem_tra(tl, n["text"], idx)
        ket.append(
            {
                "premise": n["text"],
                "hypothesis": tl,
                "label": 1 if pq_.ket_luan == KetLuan.DU_CAN_CU else 0,
                "corruption_type": None if pq_.ket_luan == KetLuan.DU_CAN_CU else f"gpt4o_{pq_.tang}",
                "doc_id": n["so_vb"],
                "phan_quyet": pq_.ket_luan.value,
                "tang": pq_.tang,
                "ly_do": pq_.ly_do,
                "nguon_that": f"Điều {n['dieu']} Khoản {n['khoan']} {n['so_vb']}",
            }
        )
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{args.n}  ({time.time()-t0:.0f}s)")

    # ── BÁO CÁO ────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("GPT-4o BỊA THẬT SỰ NHƯ THẾ NÀO — trọng tài: lớp tất định")
    print("=" * 72)
    print(f"  GPT-4o TỪ CHỐI trả lời : {n_tu_choi}/{args.n}  ({n_tu_choi/args.n*100:.0f}%)")
    print(f"  GPT-4o CÓ trả lời      : {len(ket)}/{args.n}\n")
    if not ket:
        print("  ⚠ Không câu nào để chấm — câu hỏi vẫn lệch khỏi nguồn.")
        return
    c = Counter(x["phan_quyet"] for x in ket)
    for k, v in c.most_common():
        print(f"  {k:20} {v:3}/{len(ket)}  ({v/len(ket)*100:.0f}%)")

    print("\n  Tầng nào bắt:")
    for k, v in Counter(x["tang"] for x in ket if x["label"] == 0).most_common():
        print(f"    {k:22} {v}")

    bia = [x for x in ket if x["label"] == 0]
    print(f"\n  --- 3 CA GPT-4o BỊA THẬT ---")
    for x in bia[:3]:
        print(f"\n  nguồn thật : {x['nguon_that']}")
        print(f"  GPT-4o nói : {x['hypothesis'][:150]}")
        print(f"  bị bắt bởi : {x['tang']} — {x['ly_do'][:90]}")

    f = OUT / "gpt4o_bia_that.jsonl"
    with f.open("w", encoding="utf-8") as fh:
        for x in ket:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"\n  → {f}  ({len(bia)} hard-negative THẬT của LLM)")
    print("\n  ⭐ Đây KHÔNG phải câu bịa do đội chế. Đây là GPT-4o bịa thật,")
    print("     bị lớp tất định bắt tại trận. Người sinh và người bắt là 2 bên độc lập.")


if __name__ == "__main__":
    main()
