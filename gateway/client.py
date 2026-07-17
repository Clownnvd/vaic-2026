"""L4 Gateway — resolve_model (test/gateway/direct) + egress allowlist + audit.

Theo đúng khung kho: `gateway/client.py` = model resolver, `litellm.config.yaml` = proxy.

3 chế độ (kho chốt):
  • test    — TestModel, không gọi mạng. Dùng cho smoke/CI, 0 đồng.
  • gateway — qua LiteLLM proxy :4000 → thoả ràng buộc J (mọi call có log)
              + I2 (fallback đa provider). ĐÂY LÀ MẶC ĐỊNH D-DAY.
  • direct  — gọi thẳng provider. CHỈ để debug, KHÔNG dùng khi nộp (lách mất log).

Bật bằng `USE_GATEWAY=1`.

Egress allowlist cưỡng chế ở đây vì LiteLLM không có sẵn (ràng buộc J:
"không được gọi external API ngoài danh sách cho phép").
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

# ── ràng buộc J: chỉ được gọi ra những host này ───────────────────
HOST_CHO_PHEP = {
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "mkp-api.fptcloud.com",  # FPT — đường data-ở-VN
    "localhost",
    "127.0.0.1",
}

GATEWAY_URL = os.getenv("LITELLM_URL", "http://localhost:4000")


class ViPhamEgress(Exception):
    """Gọi ra host ngoài allowlist — ràng buộc J."""


class LachCong(Exception):
    """Gọi LLM không qua cổng khi USE_GATEWAY=1."""


def kiem_egress(url: str) -> None:
    host = urlparse(url).hostname or ""
    if host not in HOST_CHO_PHEP:
        raise ViPhamEgress(
            f"Chặn gọi ra '{host}' — ngoài allowlist. Ràng buộc J: "
            f"agent không được gọi external API ngoài danh sách cho phép."
        )


# ── audit: mọi call để lại vết (ràng buộc J) ──────────────────────
@dataclass
class BanGhi:
    trace_id: str
    luc: str
    che_do: str
    model: str
    muc_dich: str
    do_tre_ms: int
    thanh_cong: bool
    loi: str | None = None


SO_AUDIT = Path("./artifacts/audit/llm_calls.jsonl")


def ghi_audit(b: BanGhi) -> None:
    """Append-only. Bản thật: bảng Postgres REVOKE UPDATE/DELETE."""
    SO_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with SO_AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(b), ensure_ascii=False) + "\n")


# ── resolve_model ─────────────────────────────────────────────────
def che_do() -> str:
    if os.getenv("USE_TEST_MODEL") == "1":
        return "test"
    if os.getenv("USE_GATEWAY", "1") == "1":  # MẶC ĐỊNH bật — J là ràng buộc cứng
        return "gateway"
    return "direct"


def resolve_model(tac_vu: str = "task-deep"):
    """Trả (model_name, base_url, che_do) theo complexity routing.

    tac_vu: 'task-deep' (suy luận/soạn) · 'task-fast' (slot-filling/intent)
            · 'task-vn' (chủ quyền dữ liệu — chạy trên FPT, data không rời VN)
    """
    m = che_do()
    if m == "test":
        return ("test", None, m)

    if m == "gateway":
        kiem_egress(GATEWAY_URL)
        return (tac_vu, f"{GATEWAY_URL}/v1", m)

    # direct — CẢNH BÁO: lách cổng = mất log = vi phạm J
    print("⚠ USE_GATEWAY=0: gọi thẳng provider, KHÔNG qua proxy có log.")
    print("  Vi phạm ràng buộc J. Chỉ dùng để debug, TUYỆT ĐỐI không dùng khi nộp.")
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    kiem_egress(base)
    return (os.getenv("REAL_MODEL", "gpt-4o"), base, m)


def _doc_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key and Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return key


# Chuỗi fallback I2 — primary sập thì thử cái kế. Đề cấm PHỤ THUỘC MỘT LLM.
# ⚠️ Lý tưởng khác provider (OpenAI→Anthropic→Gemini) nhưng chỉ có key OpenAI,
# nên hiện fallback trong OpenAI (gpt-4o → gpt-4o-mini). Khai thẳng giới hạn này.
FALLBACK = {
    "task-deep": ["gpt-4o", "gpt-4o-mini"],
    "task-fast": ["gpt-4o-mini", "gpt-4o"],
    "task-vn": ["gpt-4o", "gpt-4o-mini"],
}


def goi_llm(prompt: str, muc_dich: str, tac_vu: str = "task-deep", he_thong: str = "", **opts):
    """Điểm vào DUY NHẤT gọi LLM. Mọi call đi qua đây → mọi call có vết (audit + egress).

    Có fallback I2: primary lỗi → thử model kế trong chuỗi. Mỗi lần thử ghi audit.
    """
    model, base, m = resolve_model(tac_vu)
    trace_id = str(uuid.uuid4())[:8]

    if m == "test":
        t0 = time.perf_counter()
        kq = f"[TestModel] {muc_dich}: {prompt[:60]}…"
        ghi_audit(BanGhi(trace_id, time.strftime("%Y-%m-%dT%H:%M:%S"), m, "test",
                         muc_dich, int((time.perf_counter() - t0) * 1000), True, None))
        return kq

    from openai import OpenAI

    key = _doc_key()
    if not key:
        raise RuntimeError("Không có OPENAI_API_KEY")
    base_url = base if m == "gateway" else os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    kiem_egress(base_url)
    cli = OpenAI(api_key=key, base_url=base_url)

    msgs = ([{"role": "system", "content": he_thong}] if he_thong else []) + [
        {"role": "user", "content": prompt}
    ]
    loi_cuoi = None
    for mdl in FALLBACK.get(tac_vu, ["gpt-4o"]):
        t0 = time.perf_counter()
        ok, loi = False, None
        try:
            r = cli.chat.completions.create(
                model=mdl,
                messages=msgs,
                temperature=opts.get("temperature", 0.2),
                max_tokens=opts.get("max_tokens", 320),
            )
            ok = True
            return (r.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            loi = f"{type(e).__name__}: {e}"[:160]
            loi_cuoi = loi
        finally:
            ghi_audit(BanGhi(trace_id, time.strftime("%Y-%m-%dT%H:%M:%S"), m, mdl,
                             muc_dich, int((time.perf_counter() - t0) * 1000), ok, loi))
    raise RuntimeError(f"Mọi model trong chuỗi fallback đều lỗi: {loi_cuoi}")
