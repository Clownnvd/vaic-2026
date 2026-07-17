"""Liệt kê tab Chrome đang mở qua CDP (cổng 9222) — không cần MCP.

Dùng để xem Chrome debug đã đăng nhập vào đâu trước khi lái nó.
Chạy: uv run --python 3.11 python scripts/chrome_tabs.py
"""

import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=8) as r:
    tabs = json.load(r)

pages = [t for t in tabs if t.get("type") == "page"]
print(f"{len(pages)} tab đang mở:\n")
for t in pages:
    print(f"  • {t.get('title', '')[:70]}")
    print(f"    {t.get('url', '')[:110]}\n")
