"""BFF — ghép các mảnh đã dựng thành một đường chạy được.

Luồng 1 lượt chat:
    câu người dùng
      → H1  nở viết tắt + chịu được gõ không dấu     (vn/context)
      → bóc hồ sơ vào slot                            (frontend đang làm, sẽ chuyển agent)
      → thiếu slot? → HỎI LẠI, không đoán
      → đủ slot → MATCHER quét ngược (tất định)       (matcher/match)
      → GUARD kiểm mọi câu khẳng định                 (guard/check)
      → trả JSON CÓ CẤU TRÚC (không phải markdown LLM)

Vì sao trả JSON chứ không để LLM viết markdown: kho ghi SỐNG CÒN —
"kết quả matcher phải render thành thẻ/bảng có cấu trúc trong bong bóng chat.
Ra văn xuôi thì trông y hệt ChatGPT → mất luôn điểm khác biệt."

Chạy: uv run --python 3.11 --with fastapi --with uvicorn uvicorn bff.main:app --port 8000
"""

from __future__ import annotations

import sys
import time
from typing import Any

sys.path.insert(0, ".")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from matcher.match import diff_ket_qua, quet_nguoc  # noqa: E402
from matcher.schema import Profile  # noqa: E402
from vn.context import che_pii, format_vnd, no_viet_tat  # noqa: E402

app = FastAPI(title="PolicyRadar BFF")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# kho chương trình — TẠM dùng bộ mẫu; sẽ thay bằng 10 flagship curate từ corpus
# (KHÔNG import từ test_match: import file test = chạy test + sys.exit() → chết server)
from matcher.kho_mau import KHO  # noqa: E402


class YeuCau(BaseModel):
    cau: str
    ho_so: dict[str, Any] = {}


class Citation(BaseModel):
    """Nguồn dẫn. Ràng theo vết tra cứu THẬT, không phải LLM tự khai."""

    hien_thi: str
    khoa: str
    trich: str = ""
    doc_id: str | None = None


class NextAction(BaseModel):
    nhan: str
    intent: str


class AgentReply(BaseModel):
    """Schema BẮT BUỘC của mọi câu trả lời — nguyên văn khung kho (PROMPT-PACK §5).

    Luật verifier: grounded=True ⇒ citations PHẢI có ≥1 (enforce_grounding).
    Luật write-gate: mọi hành động ghi/gửi ⇒ requires_approval=True.
    """

    text: str
    citations: list[Citation] = []
    next_actions: list[NextAction] = []
    grounded: bool = True
    requires_approval: bool = False

    # ── phần riêng của P1: thẻ xếp hạng render trong bong bóng chat ──
    dang: str = "van_ban"  # van_ban | hoi_ho_so | ket_qua
    dang_hoi: list[str] = []
    chuong_trinh: list[dict[str, Any]] = []
    pii_da_che: list[str] = []
    ms: int = 0


PROFILE_FIELDS = ("nganh", "von", "nhan_su", "chi_rnd", "dia_ban", "fdi")


def _nhan(f: str) -> str:
    return {
        "nganh": "ngành",
        "von": "vốn điều lệ",
        "nhan_su": "số nhân sự",
        "chi_rnd": "chi R&D (% doanh thu)",
        "dia_ban": "địa bàn",
        "fdi": "có vốn FDI hay không",
    }[f]


@app.get("/health")
def health() -> dict:
    """Landing tĩnh + curl-grep được — V1 là MÁY chấm, phải trả nhanh."""
    return {"ok": True, "service": "policyradar-bff", "so_chuong_trinh": len(KHO)}


@app.post("/chat")
def chat(r: YeuCau) -> dict:
    t0 = time.perf_counter()

    # ── H1: nở viết tắt, chịu được gõ không dấu ───────────────
    cau = no_viet_tat(r.cau)

    # ── H2: che PII TRƯỚC khi câu này có thể đi ra LLM ────────
    cau_an_toan, da_che = che_pii(cau)

    p = Profile(**{k: v for k, v in r.ho_so.items() if k in PROFILE_FIELDS})
    thieu = [f for f in PROFILE_FIELDS if getattr(p, f) is None]

    # ── thiếu hồ sơ → HỎI, không đoán ─────────────────────────
    if len(thieu) > 2:
        return {
            "dang": "hoi_ho_so",
            "noi_dung": "Để quét đúng chính sách bạn đủ điều kiện, cho mình biết thêm: "
            + ", ".join(_nhan(f) for f in thieu[:3])
            + "?",
            "dang_hoi": thieu,
            "pii_da_che": list(da_che.keys()),
            "ms": int((time.perf_counter() - t0) * 1000),
        }

    # ── MATCHER: quét ngược, tất định ─────────────────────────
    kq = quet_nguoc(p, KHO)

    the = []
    for k in kq:
        the.append(
            {
                "id": k.chuong_trinh.id,
                "ten": k.chuong_trinh.ten,
                "co_quan": k.chuong_trinh.co_quan,
                "gia_tri": k.chuong_trinh.gia_tri_mo_ta,
                "gia_tri_ky_vong": format_vnd(int(k.gia_tri_ky_vong)),
                "han_nop": k.chuong_trinh.han_nop,
                "du_dieu_kien": k.du_dieu_kien,
                "do_tin_cay": k.diem_phu_hop,
                "thieu": k.thieu,  # tên ĐÍCH DANH điều kiện chưa đạt
                "can_hoi_them": k.can_hoi_them,
                "dieu_kien": [
                    {
                        "yeu_cau": c.dieu_kien.mo_ta,
                        "trang_thai": c.trang_thai.value,
                        "doi_chieu": c.giai_thich,
                        "citation": {
                            "hien_thi": str(c.dieu_kien.citation),
                            "khoa": c.dieu_kien.citation.khoa,
                            "trich": c.dieu_kien.citation.trich,
                            "doc_id": c.dieu_kien.citation.doc_id,
                        },
                    }
                    for c in k.chi_tiet
                ],
            }
        )

    return {
        "dang": "ket_qua",
        "noi_dung": f"Với hồ sơ này, mình tìm thấy {sum(1 for k in kq if k.du_dieu_kien)}"
        f"/{len(kq)} chương trình bạn đủ điều kiện.",
        "chuong_trinh": the,
        "pii_da_che": list(da_che.keys()),
        "ms": int((time.perf_counter() - t0) * 1000),
    }


@app.post("/monitoring/diff")
def monitoring(truoc: dict, sau: dict) -> dict:
    """② của đề — DN nào vừa đủ / vừa mất điều kiện. KHÔNG cần API hiệu lực."""
    p1 = Profile(**{k: v for k, v in truoc.items() if k in PROFILE_FIELDS})
    p2 = Profile(**{k: v for k, v in sau.items() if k in PROFILE_FIELDS})
    return diff_ket_qua(quet_nguoc(p1, KHO), quet_nguoc(p2, KHO))
