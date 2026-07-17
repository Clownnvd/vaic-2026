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

from ho_so.mau import TAT_CA  # noqa: E402
from ho_so.sinh import checklist, render_text  # noqa: E402
from matcher.kiem_ho_so import kiem, mo_ta_loi  # noqa: E402
from matcher.match import diff_ket_qua, quet_nguoc  # noqa: E402
from matcher.pham_vi import (  # noqa: E402
    cau_tu_choi_linh_vuc,
    cau_tu_choi_van_ban,
    hoi_van_ban_ngoai_kho,
    ngoai_pham_vi,
)
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

    # ── HỎI NGOÀI PHẠM VI → nói thẳng, không trả đồ khác ──────
    # (bộ ca đối kháng bắt: hỏi "ưu đãi nông nghiệp" → trả ưu đãi công nghệ cao)
    vb = hoi_van_ban_ngoai_kho(cau)
    if vb:
        return {
            "dang": "van_ban",
            "text": cau_tu_choi_van_ban(vb),
            "noi_dung": cau_tu_choi_van_ban(vb),
            "grounded": False,  # KHÔNG có căn cứ → nói thẳng
            "citations": [],
            "requires_approval": False,
            "pii_da_che": list(da_che.keys()),
            "ms": int((time.perf_counter() - t0) * 1000),
        }

    lv = ngoai_pham_vi(cau)
    if lv:
        return {
            "dang": "van_ban",
            "text": cau_tu_choi_linh_vuc(lv),
            "noi_dung": cau_tu_choi_linh_vuc(lv),
            "grounded": False,
            "citations": [],
            "requires_approval": False,
            "pii_da_che": list(da_che.keys()),
            "ms": int((time.perf_counter() - t0) * 1000),
        }

    p = Profile(**{k: v for k, v in r.ho_so.items() if k in PROFILE_FIELDS})

    # ── SỐ VÔ LÝ → KHÔNG đối chiếu ────────────────────────────
    # (bộ ca đối kháng bắt: vốn -5 tỷ → "ĐỦ điều kiện" vì -5 tỷ ≤ 100 tỷ = True)
    # Đối chiếu rác ra kết luận rác — mà kết luận rác lại trông rất tự tin.
    loi_hs = kiem(p)
    if loi_hs:
        return {
            "dang": "van_ban",
            "text": mo_ta_loi(loi_hs),
            "noi_dung": mo_ta_loi(loi_hs),
            "grounded": False,
            "citations": [],
            "requires_approval": False,
            "loi_ho_so": [{"field": x.field, "gia_tri": x.gia_tri, "ly_do": x.ly_do} for x in loi_hs],
            "pii_da_che": list(da_che.keys()),
            "ms": int((time.perf_counter() - t0) * 1000),
        }

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


class YeuCauHoSo(BaseModel):
    chuong_trinh: str
    ho_so: dict[str, Any] = {}


@app.get("/ho-so/mau")
def danh_sach_mau() -> dict:
    """③ — biểu mẫu nào đang dùng được, căn cứ nào."""
    return {
        "so_mau": len(TAT_CA),
        "mau": [
            {
                "ma": m.ma,
                "ten": m.ten,
                "nhom": m.nhom,
                "can_cu": m.can_cu,
                "co_quan_nhan": m.co_quan_nhan,
                "han_nop": m.han_nop,
                "dn_tu_nop": m.dn_tu_nop,
            }
            for m in TAT_CA
        ],
    }


@app.post("/ho-so/sinh")
def sinh_ho_so(r: YeuCauHoSo) -> dict:
    """③ — sinh khung hồ sơ. AI KHÔNG gõ ô nào; CODE điền, DN tự khai phần còn lại.

    Write-gate: hồ sơ là hành động GHI → requires_approval=True, bản nháp chờ duyệt.
    """
    t0 = time.perf_counter()
    ks = checklist(r.chuong_trinh, r.ho_so)
    if not ks:
        return {
            "text": f"Chưa có biểu mẫu nào gắn với chương trình '{r.chuong_trinh}'.",
            "grounded": False,
            "citations": [],
            "requires_approval": False,
            "ms": int((time.perf_counter() - t0) * 1000),
        }

    return {
        "text": f"Đã dựng {len(ks)} khung hồ sơ. Phần số liệu do hệ thống điền từ hồ sơ "
        f"doanh nghiệp — bản nháp, bạn duyệt trước khi nộp.",
        "grounded": True,
        "requires_approval": True,  # write-gate — LUÔN True
        "citations": [{"hien_thi": k.mau.can_cu, "khoa": k.mau.can_cu} for k in ks],
        "khung": [
            {
                "ma": k.mau.ma,
                "ten": k.mau.ten,
                "can_cu": k.mau.can_cu,
                "co_quan_nhan": k.mau.co_quan_nhan,
                "han_nop": k.mau.han_nop,
                "ghi_chu": k.mau.ghi_chu,
                "phan_tram_day": k.phan_tram_day,
                "thieu": k.thieu,
                "o": [
                    {
                        "nhan": o.nhan,
                        "gia_tri": o.gia_tri,
                        "nguon": o.nguon,
                        "da_dien": o.da_dien,
                        "ai_duoc_go": o.ai_duoc_go,  # luôn False — bằng chứng AI không chạm
                    }
                    for o in k.o
                ],
                "van_ban": render_text(k),
            }
            for k in ks
        ],
        "ms": int((time.perf_counter() - t0) * 1000),
    }
