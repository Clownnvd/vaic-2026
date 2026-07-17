"""Đọc README thật của dataset — xem có ghi công tác giả gốc không (điều 2)."""

import urllib.request

for ten in ("NghiemAbe/ViWikiFC", "tranthaihoa/vifactcheck"):
    print("=" * 68)
    print(f"### README: {ten}")
    print("=" * 68)
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/datasets/{ten}/raw/main/README.md",
            headers={"User-Agent": "policyradar/0.1"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = r.read().decode("utf-8", "ignore")
        print(txt[:1600])
    except Exception as e:  # noqa: BLE001
        print(f"LỖI: {type(e).__name__}: {str(e)[:80]}")
    print("\n")
