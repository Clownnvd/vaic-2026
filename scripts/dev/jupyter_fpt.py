"""Nói chuyện với JupyterLab FPT bằng REST API + WebSocket — KHÔNG bấm UI.

Vì sao không lái UI Jupyter: bấm nút trong Lab là mò mẫm, đổi layout là gãy,
không biết cell chạy xong chưa. Jupyter có API CHÍNH THỨC:
    GET  /api/status              — server sống chưa
    PUT  /api/contents/<path>     — upload file
    POST /api/kernels             — tạo kernel
    ws   /api/kernels/<id>/channels — chạy code, đọc output THẬT

→ tất định, biết chắc chạy xong hay chưa, đọc được stderr. Đúng WAT:
  việc thực thi giao cho code, không giao cho mắt.

Dùng:
  python scripts/jupyter_fpt.py gpu                    # kiểm GPU
  python scripts/jupyter_fpt.py chay "print(1+1)"      # chạy code
  python scripts/jupyter_fpt.py day <file> <đích>      # upload
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# FPT_LAB_CONFIG chọn cấu hình: lab notebook cũ (.fpt_lab.json) hay
# GPU container (.fpt_container.json). Mặc định lab cũ.
CAU_HINH = Path(os.environ.get("FPT_LAB_CONFIG", "./.fpt_lab.json"))

# Python trên Windows KHÔNG dùng kho chứng chỉ của Windows → CERTIFICATE_VERIFY_FAILED
# dù Chrome mở trang bình thường.
# certifi KHÔNG cứu được ca này: CA cấp cert cho *.serverless.fptcloud.com không nằm
# trong bundle của certifi, nhưng CÓ trong kho Windows (nên Chrome tin).
# → `truststore` bảo Python mượn thẳng kho của Windows. Đúng cách.
# TUYỆT ĐỐI KHÔNG tắt xác thực (ssl._create_unverified_context): đường này đang
# tải TOKEN của lab — tắt xác thực = mời người khác nghe trộm token.
def _ssl_ctx() -> ssl.SSLContext:
    try:
        import truststore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        pass
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _ca() -> str | None:
    try:
        import certifi

        return certifi.where()
    except ImportError:
        return None


CTX = _ssl_ctx()


def nap_cau_hinh() -> tuple[str, str]:
    if not CAU_HINH.exists():
        raise SystemExit(
            "Chưa có .fpt_lab.json — chạy scripts/bat_popup.py để lấy URL+token trước"
        )
    d = json.loads(CAU_HINH.read_text(encoding="utf-8"))
    return d["goc"].rstrip("/"), d["token"]


def goi(duong: str, method: str = "GET", body: bytes | None = None, kieu: str = "application/json"):
    goc, token = nap_cau_hinh()
    req = urllib.request.Request(
        f"{goc}{duong}",
        data=body,
        method=method,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": kieu,
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        b = r.read()
        try:
            return json.loads(b)
        except Exception:  # noqa: BLE001
            return {"raw": b[:400].decode("utf-8", "replace")}


def day_file(nguon: Path, dich: str) -> dict:
    """Upload file lên Lab. File nhị phân/lớn → base64."""
    noi_dung = nguon.read_bytes()
    return goi(
        f"/api/contents/{dich}",
        "PUT",
        json.dumps(
            {
                "type": "file",
                "format": "base64",
                "content": base64.b64encode(noi_dung).decode(),
            }
        ).encode(),
    )


def chay(code: str, cho: int = 600) -> str:
    """Chạy code trong kernel, TRẢ OUTPUT THẬT (cả stderr). Chờ tới khi xong."""
    from websocket import create_connection

    goc, token = nap_cau_hinh()
    ks = goi("/api/kernels", "POST", json.dumps({"name": "python3"}).encode())
    kid = ks["id"]
    ws_goc = goc.replace("https://", "wss://").replace("http://", "ws://")

    ws = create_connection(
        f"{ws_goc}/api/kernels/{kid}/channels?token={token}",
        timeout=cho,
        suppress_origin=True,  # ⚠️ như CDP — server chặn Origin lạ
        header={"Authorization": f"token {token}"},
        # ⚠️ phải truyền THẲNG context, không phải ca_certs: websocket-client tự
        # dựng context riêng từ ca_certs (=certifi) → vẫn CERTIFICATE_VERIFY_FAILED.
        # Nó chỉ dùng kho Windows khi mình đưa hẳn context truststore vào.
        sslopt={"context": CTX},
    )
    msg_id = "vaic-1"
    ws.send(
        json.dumps(
            {
                "header": {
                    "msg_id": msg_id,
                    "username": "vaic",
                    "session": "s1",
                    "msg_type": "execute_request",
                    "version": "5.3",
                },
                "parent_header": {},
                "metadata": {},
                "content": {
                    "code": code,
                    "silent": False,
                    "store_history": True,
                    "allow_stdin": False,
                    "stop_on_error": False,
                },
                "channel": "shell",
            }
        )
    )

    ra: list[str] = []
    t0 = time.time()
    while time.time() - t0 < cho:
        try:
            m = json.loads(ws.recv())
        except Exception:  # noqa: BLE001
            break
        if (m.get("parent_header") or {}).get("msg_id") != msg_id:
            continue
        mt = m.get("msg_type")
        c = m.get("content") or {}
        if mt == "stream":
            ra.append(c.get("text", ""))
            print(c.get("text", ""), end="")
        elif mt in ("execute_result", "display_data"):
            x = (c.get("data") or {}).get("text/plain", "")
            ra.append(x)
            print(x)
        elif mt == "error":
            x = "\n".join(c.get("traceback") or [])
            ra.append(x)
            print(x)
        elif mt == "status" and c.get("execution_state") == "idle":
            break
    ws.close()
    return "".join(ra)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    lenh = sys.argv[1]

    if lenh == "status":
        print(json.dumps(goi("/api/status"), indent=2))
    elif lenh == "gpu":
        chay(
            "import subprocess;print(subprocess.run(['nvidia-smi'],capture_output=True,text=True).stdout)\n"
            "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available(),"
            "torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"
        )
    elif lenh == "chay":
        chay(sys.argv[2])
    elif lenh == "chay_file":
        # ĐỌC file .py local rồi chạy trên lab.
        # Vì sao có lệnh này: truyền code nhiều dòng qua argv thì PowerShell băm
        # nát dấu nháy/dấu hai chấm ("print(MAY" → SyntaxError). Qua file thì
        # code đi nguyên vẹn, byte nào ra byte đó.
        chay(Path(sys.argv[2]).read_text(encoding="utf-8"), cho=int(sys.argv[3]) if len(sys.argv) > 3 else 600)
    elif lenh == "day":
        print(json.dumps(day_file(Path(sys.argv[2]), sys.argv[3]), indent=2)[:300])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
