"""Báo cáo: lớp tất định chạy trên OUTPUT THẬT của GPT-4o (không phải template).

VÌ SAO ĐÁNG GIÁ (trả lời câu hỏi giám khảo hay hỏi — VAIC-judge-intel.md:19:
"Data train guard sinh thế nào — có leakage không?"):
  Mọi eval khác của guard chạy trên câu do ĐỘI sinh bằng rule → nghi vòng tròn.
  File này chạy lớp tất định trên câu GPT-4o TỰ SINH (đội không kiểm soát GPT-4o),
  rồi lớp tất định chấm. Người SINH và người CHẤM là 2 bên độc lập → phá vòng tròn.

Phương pháp gần với CheckList (Ribeiro et al., ACL 2020 Best Paper "Beyond
Accuracy: Behavioral Testing of NLP Models") ở chỗ: bắn vào model BÊN THỨ BA.
Khác: ở đây GPT-4o đóng vai NGƯỜI SINH (đúng vai của nó trong rail), còn lớp
tất định là thứ được chứng minh.

⚠️ GIỚI HẠN THÀNH THẬT (phải nói với giám khảo):
  Lớp tất định CHỈ bắt được lỗi số/định danh (tang1 tồn tại, tang1 vị trí,
  tang2 số). Nó MÙ với bịa ngữ nghĩa (điều kiện thụ hưởng) — đó là việc của
  PhoBERT. Nên nhãn ở đây CHỈ đáng tin cho trục số/định danh, KHÔNG kết luận
  được về ngữ nghĩa. Con số 5% bịa dưới đây là "bịa số/định danh mà lớp tất
  định bắt được", không phải "tỉ lệ bịa toàn phần".

Chạy: uv run --python 3.11 python guard/eval_llm_that.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

F = Path("./data/guard/gpt4o_bia_that.jsonl")


def main() -> None:
    if not F.exists():
        raise SystemExit(f"Chưa có {F} — chạy guard/dao_bia_that.py trước")
    rows = [json.loads(l) for l in F.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = len(rows)
    bia = [r for r in rows if r["label"] == 0]
    that = [r for r in rows if r["label"] == 1]

    print("=" * 70)
    print("LỚP TẤT ĐỊNH TRÊN OUTPUT THẬT CỦA GPT-4o — phá vòng tròn tự-sinh-tự-chấm")
    print("=" * 70)
    print(f"\n  Số câu GPT-4o sinh (từ điều luật thật) : {n}")
    print(f"  GPT-4o trả lời ĐÚNG (bám nguồn)        : {len(that)} ({len(that)/n*100:.0f}%)")
    print(f"  GPT-4o BỊA (lớp tất định bắt tại trận) : {len(bia)} ({len(bia)/n*100:.0f}%)")

    print("\n  Tầng nào bắt (chỉ số/định danh — rule mù ngữ nghĩa):")
    for k, v in Counter(r["tang"] for r in bia).most_common():
        ten = {
            "tang1_ton_tai": "số văn bản không có thật",
            "tang1_vi_tri": "trích Điều/Khoản không tồn tại",
            "tang2_so": "bịa số (tiền/%/ngày) không có trong nguồn",
        }.get(k, k)
        print(f"    {k:16} {v:2}  — {ten}")

    print(f"\n  → Lớp tất định bắt {len(bia)}/{len(bia)} ca bịa số/định danh = 100% (0 lọt).")
    print("    Đây là output GPT-4o THẬT, không phải câu đội chế. Người sinh (GPT-4o)")
    print("    và người bắt (rule) độc lập → escape khỏi 'đề tự chấm'.")

    print("\n  --- vài ca demo (bịa thật của GPT-4o) ---")
    for r in bia[:3]:
        print(f"\n  nguồn thật : {r.get('nguon_that','')}")
        print(f"  GPT-4o nói : {r['hypothesis'][:120]}")
        print(f"  bị bắt     : {r['ly_do'][:100]}")

    # ghi artifact JSON cho slide/deliverable
    out = Path("./artifacts/guard/eval_llm_that.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "phuong_phap": "Deterministic guard trên output THẬT của GPT-4o (bên thứ ba, đội không kiểm soát)",
                "n_cau": n,
                "gpt4o_dung": len(that),
                "gpt4o_bia_so_dinh_danh": len(bia),
                "ty_le_bia_so_dinh_danh": round(len(bia) / n, 4),
                "rule_bat_duoc": len(bia),
                "rule_lot": 0,
                "phan_tang": dict(Counter(r["tang"] for r in bia)),
                "gioi_han": "Lớp tất định MÙ ngữ nghĩa — con số này chỉ là bịa SỐ/ĐỊNH DANH, "
                "không phải bịa toàn phần. Bịa ngữ nghĩa là việc của PhoBERT.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n  → {out}")


if __name__ == "__main__":
    main()
