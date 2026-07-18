"""Đẩy code + data lên lab FPT — nén trước, giải nén trên lab.

Vì sao nén: train.jsonl 23MB → base64 thành ~31MB nhét trong 1 JSON PUT.
gzip xuống ~4MB. Nhanh hơn nhiều và ít gãy giữa chừng.

Chạy: uv run --python 3.11 --with websocket-client --with certifi --with truststore \
        python scripts/day_len_lab.py
"""

from __future__ import annotations

import gzip
import io
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, ".")
from scripts.jupyter_fpt import chay, goi  # noqa: E402

import base64
import json

FILE = [
    ("guard/train_phobert.py", "guard/train_phobert.py"),
    ("data/guard/train.jsonl", "data/guard/train.jsonl"),
    ("data/guard/test.jsonl", "data/guard/test.jsonl"),
    ("data/guard/calib.jsonl", "data/guard/calib.jsonl"),
]


def main() -> None:
    # ── gói tar.gz trong RAM ───────────────────────────────
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for nguon, dich in FILE:
            p = Path(nguon)
            if not p.exists():
                raise SystemExit(f"thiếu {p}")
            tar.add(p, arcname=dich)
    goi_tin = buf.getvalue()
    tho = sum(Path(n).stat().st_size for n, _ in FILE)
    print(f"Gói: {tho/1e6:.1f} MB → {len(goi_tin)/1e6:.1f} MB (nén {tho/len(goi_tin):.1f}×)")

    # ── đẩy lên ────────────────────────────────────────────
    t0 = time.time()
    r = goi(
        "/api/contents/vaic.tar.gz",
        "PUT",
        json.dumps(
            {"type": "file", "format": "base64", "content": base64.b64encode(goi_tin).decode()}
        ).encode(),
    )
    print(f"Đẩy xong: {r.get('path')} ({time.time()-t0:.0f}s)")

    # ── giải nén trên lab ──────────────────────────────────
    chay(
        "import tarfile, os\n"
        "os.makedirs('/home/jovyan/vaic', exist_ok=True)\n"
        "with tarfile.open('/home/jovyan/vaic.tar.gz') as t: t.extractall('/home/jovyan/vaic')\n"
        "for r,d,f in os.walk('/home/jovyan/vaic'):\n"
        "    for x in f: p=os.path.join(r,x); print(f'{os.path.getsize(p)/1e6:7.2f} MB  {p}')\n"
    )


if __name__ == "__main__":
    main()
