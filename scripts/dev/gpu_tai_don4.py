"""Tải kết quả 4 đòn về local: mining_phobert.png, ablation_phobert.csv,
phobert_ket_qua.json, eval_ngoai (zero-shot). Copy vào Jupyter root rồi GET."""
from __future__ import annotations
import base64, json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, ".")
from scripts.jupyter_fpt import CTX, chay, nap_cau_hinh  # noqa: E402

OUT = Path("./artifacts/guard/don4_h100")
OUT.mkdir(parents=True, exist_ok=True)
FILES = [
    "mining_phobert.png",
    "ablation_phobert.csv",
    "phobert_ket_qua.json",
    "eval_ngoai.json",
    "zero_shot.json",
]


def get_file(duong: str) -> bytes | None:
    goc, token = nap_cau_hinh()
    req = urllib.request.Request(f"{goc}/api/contents/{duong}",
                                 headers={"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
            d = json.loads(r.read())
    except Exception:
        return None
    if d.get("format") == "base64":
        return base64.b64decode(d["content"])
    return (d.get("content") or "").encode()


def main() -> None:
    # copy mọi file artifacts vào Jupyter root
    chay("""
import shutil, os, glob
root='/mnt/data' if os.path.isdir('/mnt/data') else '/home/admin'
src='/home/admin/vaic/artifacts/guard'
for f in glob.glob(src+'/*'):
    if os.path.isfile(f):
        try: shutil.copy(f, root); print('copy', os.path.basename(f))
        except Exception as e: print('skip', f, e)
print('root =', root)
print('list:', os.listdir(src) if os.path.isdir(src) else 'no dir')
""")
    for f in FILES:
        b = get_file(f)
        if b:
            (OUT / f).write_bytes(b)
            print(f"  ✓ {f}: {len(b)/1024:.0f} KB")
        else:
            print(f"  — {f}: không có")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
