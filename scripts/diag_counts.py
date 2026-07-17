"""Đếm chính xác qua HF datasets-server API — không tải shard nào.

Trả lời dứt điểm: kho có bao nhiêu văn bản ≥2018, bao nhiêu đúng doc_type,
bao nhiêu chạm keyword. Nếu API trả số → khỏi phải mò bằng cách tải 1.8GB.

Chạy: uv run --python 3.11 python scripts/diag_counts.py
"""

import json
import urllib.parse
import urllib.request

BASE = "https://datasets-server.huggingface.co"
DS = "tmquan/vbpl-vn"
CONFIG = "documents"
SPLIT = "train"


def goi(path: str, params: dict) -> dict:
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "policyradar/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def dem(where: str, nhan: str) -> int | None:
    try:
        d = goi(
            "filter",
            {
                "dataset": DS,
                "config": CONFIG,
                "split": SPLIT,
                "where": where,
                "limit": 1,
            },
        )
        n = d.get("num_rows_total")
        print(f"  {nhan:52} {n:>8,}" if n is not None else f"  {nhan:52} ?")
        return n
    except Exception as e:  # noqa: BLE001
        body = ""
        if hasattr(e, "read"):
            try:
                body = e.read().decode()[:120]
            except Exception:  # noqa: BLE001
                pass
        print(f"  {nhan:52} LỖI {type(e).__name__} {body}")
        return None


def main() -> None:
    print("=== TỔNG QUAN ===")
    try:
        d = goi("size", {"dataset": DS, "config": CONFIG})
        rows = d["size"]["config"]["num_rows"]
        print(f"  Tổng số văn bản trong kho: {rows:,}")
    except Exception as e:  # noqa: BLE001
        print(f"  size lỗi: {e}")

    print("\n=== PHỄU LỌC ===")
    dem('"year">=2018', "year >= 2018")
    dem(
        "\"doc_type\" IN ('nghi_dinh','thong_tu','quyet_dinh','nghi_quyet')",
        "doc_type hợp lệ (4 loại)",
    )
    dem(
        "\"year\">=2018 AND \"doc_type\" IN ('nghi_dinh','thong_tu','quyet_dinh','nghi_quyet')",
        "year>=2018 AND doc_type hợp lệ",
    )

    print("\n=== KEYWORD (toàn kho, chưa lọc năm/loại) ===")
    for kw in [
        "ưu đãi",
        "công nghệ cao",
        "doanh nghiệp nhỏ và vừa",
        "đổi mới sáng tạo",
        "khởi nghiệp",
        "chuyển đổi số",
        "khoa học và công nghệ",
        "hỗ trợ doanh nghiệp",
    ]:
        dem(f"\"markdown\" LIKE '%{kw}%'", f"markdown chạm '{kw}'")

    print("\n=== GIAO CẢ 3 TẦNG (đây là số corpus flagship) ===")
    dem(
        "\"year\">=2018 AND \"doc_type\" IN ('nghi_dinh','thong_tu','quyet_dinh','nghi_quyet')"
        " AND (\"markdown\" LIKE '%ưu đãi%' OR \"markdown\" LIKE '%công nghệ cao%'"
        " OR \"markdown\" LIKE '%doanh nghiệp nhỏ và vừa%' OR \"markdown\" LIKE '%đổi mới sáng tạo%'"
        " OR \"markdown\" LIKE '%khởi nghiệp%' OR \"markdown\" LIKE '%chuyển đổi số%'"
        " OR \"markdown\" LIKE '%khoa học và công nghệ%' OR \"markdown\" LIKE '%hỗ trợ doanh nghiệp%')",
        "3 tầng lọc",
    )

    print("\n=== PHÂN BỐ NĂM ===")
    for y in [2018, 2020, 2022, 2023, 2024, 2025, 2026]:
        dem(f'"year"={y}', f"year = {y}")


if __name__ == "__main__":
    main()
