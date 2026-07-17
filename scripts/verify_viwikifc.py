"""Tự verify ViWikiFC — KHÔNG tin lời agent, nhìn tận mắt.

Agent báo "license MIT". Nhưng workflow cũng bắt được 3 bẫy license:
  • icon CC trên arXiv là license của BÀI BÁO, không phải dataset
  • mirror ISE-DSC01 không khớp bản gốc (37.967 vs 24.7k, schema đổi)
  • repo ViWikiFC là user 'NghiemAbe', KHÔNG khớp tên tác giả trong paper
Nên phải tự đọc metadata thật từ HuggingFace API.

Chạy: uv run --python 3.11 python scripts/verify_viwikifc.py
"""

from __future__ import annotations

import json
import urllib.request

BO = [
    ("NghiemAbe/ViWikiFC", "ứng viên số 1 — claim tạo bằng cách BIẾN ĐỔI evidence"),
    ("tranthaihoa/vifactcheck", "bổ sung — có sẵn split, có Context + Evidence"),
    ("facebook/xnli", "đo năng lực nền entail/contradict"),
]


def api(path: str):
    req = urllib.request.Request(
        f"https://huggingface.co/api/{path}", headers={"User-Agent": "policyradar/0.1"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


for ten, vi_sao in BO:
    print("=" * 68)
    print(f"### {ten}")
    print(f"    {vi_sao}")
    print("=" * 68)
    try:
        d = api(f"datasets/{ten}")
        cd = d.get("cardData") or {}
        lic = cd.get("license") or d.get("license") or "KHÔNG GHI"
        print(f"  license (cardData) : {lic}")
        print(f"  tags               : {[t for t in d.get('tags', []) if 'license' in t] or 'không có tag license'}")
        print(f"  downloads/tháng    : {d.get('downloads', '?'):,}" if isinstance(d.get("downloads"), int) else f"  downloads: {d.get('downloads')}")
        print(f"  likes              : {d.get('likes', '?')}")
        print(f"  cập nhật           : {(d.get('lastModified') or '')[:10]}")
        print(f"  tác giả            : {d.get('author', '?')}")

        files = [f["rfilename"] for f in d.get("siblings", [])]
        print(f"  file ({len(files)}): {files[:8]}")
        co_lic = [f for f in files if "licen" in f.lower()]
        print(f"  file LICENSE riêng : {co_lic or 'KHÔNG CÓ — chỉ có tag trên card'}")

        # kích thước thật
        try:
            sz = api(f"datasets/{ten}/parquet")
            print(f"  config             : {list(sz.keys()) if isinstance(sz, dict) else sz}")
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:  # noqa: BLE001
        print(f"  LỖI: {type(e).__name__}: {str(e)[:90]}")
    print()

print("=" * 68)
print("ĐÁNH GIÁ")
print("=" * 68)
print("  • license tag trên card = tác giả TỰ KHAI, không phải file LICENSE pháp lý")
print("  • Điều 2 luật thi đòi 'trích dẫn phù hợp' → dù MIT vẫn PHẢI ghi công")
print("  • Nếu không có file LICENSE riêng → ghi rõ trong NGUON-DU-LIEU.md là")
print("    'license theo tag HuggingFace, chưa có file LICENSE để đối chiếu'")
print("    — nói thật mức độ chắc chắn, đừng khẳng định quá.")
