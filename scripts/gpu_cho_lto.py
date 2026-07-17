"""Chờ pipeline LTO trên container xong → in log + tải JSON kết quả về local."""
from __future__ import annotations
import base64, json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, ".")
from scripts.jupyter_fpt import CTX, chay, nap_cau_hinh  # noqa: E402

OUT = Path("./artifacts/guard/lto")
OUT.mkdir(parents=True, exist_ok=True)
FILES = ["phobert_ket_qua.json", "ablation_phobert.csv", "eval_ngoai.json",
         "eval_ladder.json", "behavioral_phobert.json", "mining_phobert.png"]


def get(duong: str) -> bytes | None:
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
    # chờ process xong (poll qua pgrep — run.pid rỗng nên dùng pattern)
    for i in range(70):  # tối đa ~35 phút
        out = chay(r'''
import subprocess
def sh(c): return subprocess.run(["bash","-lc",c],capture_output=True,text=True,timeout=30).stdout.strip()
n=sh("pgrep -cf 'guard/(don4|eval_ngoai|eval_ladder|behavioral)'")
print("PROC", n)
print(sh("grep -vE 'overflowing tokens|transformers.' /home/admin/vaic/run.log | tail -2"))
''', cho=60)
        # PROC 0 = không còn tiến trình guard nào → xong
        proc0 = any(l.strip() == "PROC 0" or l.strip() == "PROC" for l in out.splitlines())
        if proc0:
            print(f"\n=== PIPELINE XONG (sau ~{i*30}s poll) ===")
            break
        time.sleep(30)

    # in 40 dòng cuối
    print(chay('import subprocess;print(subprocess.run(["bash","-lc","tail -45 /home/admin/vaic/run.log"],capture_output=True,text=True,timeout=30).stdout)', cho=40))

    # copy artifacts về Jupyter root rồi tải
    chay(r'''
import shutil, os, glob
src="/home/admin/vaic/artifacts/guard"
for f in glob.glob(src+"/*"):
    if os.path.isfile(f):
        try: shutil.copy(f, "/home/admin");
        except Exception: pass
print("copied", os.listdir(src) if os.path.isdir(src) else "no dir")
''', cho=40)
    for f in FILES:
        b = get(f)
        if b:
            (OUT / f).write_bytes(b)
            print(f"  ✓ {f}: {len(b)/1024:.0f} KB")
        else:
            print(f"  — {f}: không có")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
