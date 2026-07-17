"""Chốt con số corpus flagship qua API — thử nhiều cú pháp where cho tới khi chạy."""

import json
import time
import urllib.parse
import urllib.request

BASE = "https://datasets-server.huggingface.co"
DS, CONFIG, SPLIT = "tmquan/vbpl-vn", "documents", "train"

TYPES = ["nghi_dinh", "thong_tu", "quyet_dinh", "nghi_quyet"]
KWS = [
    "ưu đãi",
    "công nghệ cao",
    "doanh nghiệp nhỏ và vừa",
    "đổi mới sáng tạo",
    "khởi nghiệp",
    "chuyển đổi số",
    "khoa học và công nghệ",
    "hỗ trợ doanh nghiệp",
]

OR_TYPE = " OR ".join(f"\"doc_type\"='{t}'" for t in TYPES)
OR_KW = " OR ".join(f"\"markdown\" LIKE '%{k}%'" for k in KWS)


def dem(where: str, nhan: str, thu_lai: int = 4) -> int | None:
    for lan in range(thu_lai):
        url = f"{BASE}/filter?" + urllib.parse.urlencode(
            {
                "dataset": DS,
                "config": CONFIG,
                "split": SPLIT,
                "where": where,
                "limit": 1,
            }
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "policyradar/0.1"})
            with urllib.request.urlopen(req, timeout=120) as r:
                n = json.loads(r.read()).get("num_rows_total")
            print(f"  {nhan:46} {n:>8,}")
            return n
        except Exception as e:  # noqa: BLE001
            body = ""
            if hasattr(e, "read"):
                try:
                    body = e.read().decode()[:100]
                except Exception:  # noqa: BLE001
                    pass
            if "index is loading" in body and lan < thu_lai - 1:
                time.sleep(20)
                continue
            print(f"  {nhan:46} LỖI {body or type(e).__name__}")
            return None
    return None


print("=== PHỄU 3 TẦNG ===")
dem('"year">=2018', "year>=2018")
dem(f"({OR_TYPE})", "doc_type ∈ 4 loại")
dem(f'"year">=2018 AND ({OR_TYPE})', "year>=2018 AND doc_type")
n = dem(f'"year">=2018 AND ({OR_TYPE}) AND ({OR_KW})', "⭐ CẢ 3 TẦNG (corpus flagship)")

print("\n=== keyword còn thiếu ===")
dem("\"markdown\" LIKE '%đổi mới sáng tạo%'", "chạm 'đổi mới sáng tạo'")

if n:
    print(f"\n→ Corpus flagship kỳ vọng ≈ {n:,} văn bản (LIKE phân biệt hoa/thường,")
    print("   pipeline lower() nên số THẬT sẽ CAO HƠN con số này).")
