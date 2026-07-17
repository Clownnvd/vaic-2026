"""Tải checkpoint PhoBERT + kết quả từ container về local, rồi để XÓA container.

Checkpoint ~517MB → tar + chia khúc 30MB, GET từng khúc qua contents API,
ghép lại local. Ngược với lúc đẩy lên.

Chạy với FPT_LAB_CONFIG=.fpt_container.json
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, ".")
from scripts.jupyter_fpt import CTX, chay, nap_cau_hinh  # noqa: E402

OUT = Path("./artifacts/guard/phobert_fpt")
OUT.mkdir(parents=True, exist_ok=True)


def get_file(duong: str) -> bytes | None:
    """GET một file trên contents API → bytes (giải base64)."""
    goc, token = nap_cau_hinh()
    req = urllib.request.Request(
        f"{goc}/api/contents/{duong}",
        headers={"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        d = json.loads(r.read())
    if d.get("format") == "base64":
        return base64.b64decode(d["content"])
    return (d.get("content") or "").encode()


def main() -> None:
    # 1. kết quả nhỏ trước
    print("Tải phobert_ket_qua.json…")
    kq = get_file("vaic/out/phobert_ket_qua.json") if False else None
    # file nằm ngoài Jupyter root (root=/mnt hay /home?) → copy vào root trước
    chay(
        """
import shutil, os, subprocess, glob
root = subprocess.run(['bash','-lc',"ls -l /proc/$(pgrep -f jupyter|head -1)/cwd|sed 's/.*-> //'"],
                      capture_output=True,text=True).stdout.strip()
print('jupyter root:', root)
# tar checkpoint + copy vao root de tai
os.system('cd /home/admin/vaic/out && tar czf /home/admin/vaic/out/phobert_guard.tar.gz phobert_guard phobert_ket_qua.json')
sz = os.path.getsize('/home/admin/vaic/out/phobert_guard.tar.gz')
print('tar size MB:', round(sz/1e6,1))
# chia khuc 30MB
os.system('cd /home/admin/vaic/out && split -b 30m phobert_guard.tar.gz pbk_ && ls pbk_* | wc -l')
# copy khuc vao jupyter root
os.system(f'cp /home/admin/vaic/out/pbk_* {root}/ 2>/dev/null; cp /home/admin/vaic/out/phobert_ket_qua.json {root}/ 2>/dev/null')
print('khuc:', subprocess.run(['bash','-lc',f'ls {root}/pbk_* | wc -l'],capture_output=True,text=True).stdout.strip())
print('ten khuc:', subprocess.run(['bash','-lc',f'ls {root}/pbk_*'],capture_output=True,text=True).stdout.strip())
"""
    )

    # 2. kết quả json
    try:
        b = get_file("phobert_ket_qua.json")
        (OUT / "phobert_ket_qua.json").write_bytes(b)
        print("✓ phobert_ket_qua.json:")
        print("  ", json.loads(b))
    except Exception as e:  # noqa: BLE001
        print("✗ json:", e)

    # 3. các khúc checkpoint
    print("\nTải các khúc checkpoint…")
    import string

    parts = []
    for a in string.ascii_lowercase:
        for b_ in string.ascii_lowercase:
            ten = f"pbk_{a}{b_}"
            try:
                data = get_file(ten)
            except Exception:  # noqa: BLE001
                data = None
            if not data:
                if parts:  # hết khúc
                    break
                continue
            parts.append((ten, data))
            print(f"  {ten}: {len(data)/1e6:.1f} MB")
        else:
            continue
        break

    if parts:
        gz = OUT / "phobert_guard.tar.gz"
        with gz.open("wb") as f:
            for _, d in parts:
                f.write(d)
        print(f"\n✓ ghép {len(parts)} khúc → {gz} ({gz.stat().st_size/1e6:.1f} MB)")
        print("  giải nén: tar xzf artifacts/guard/phobert_fpt/phobert_guard.tar.gz")
    else:
        print("✗ không tải được khúc nào")


if __name__ == "__main__":
    main()
