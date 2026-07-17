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
    cau_chuyen_huong,
    cau_meta_lac_de,
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


@app.on_event("startup")
def _ham_index() -> None:
    """Đọc parquet + tính facets LÚC KHỞI ĐỘNG, không đợi user bấm 'Danh sách luật'.
    Nhờ vậy lần bấm đầu đã có sẵn trong RAM → trả tức thì thay vì đợi đọc 2.669 dòng."""
    try:
        from matcher.luat_index import get_index

        idx = get_index()
        print(f"[startup] đã hâm index luật: {len(idx.ds)} văn bản + facets")
    except Exception as e:  # noqa: BLE001
        print(f"[startup] hâm index lỗi (sẽ nạp lười ở request đầu): {type(e).__name__}")

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


# ⚠️ ĐỔI theo Profile mới — Profile cũ dựng quanh ĐIỀU KIỆN BỊA.
# `nhan_su`/`chi_rnd` không phải thứ luật hỏi:
#   80/2021 Đ5 đếm "lao động CÓ THAM GIA BHXH bình quân năm" (≠ đầu người),
#     và dùng TỔNG DOANH THU — field mà bản cũ không hề có;
#   13/2019 Đ12 K3 đòi doanh thu sản phẩm KH&CN ≥ 30% tổng doanh thu,
#     KHÔNG phải "chi R&D ≥ 1%" (điều kiện đó không tồn tại trong văn bản).
PROFILE_FIELDS = (
    "linh_vuc",
    "lao_dong_bhxh",
    "doanh_thu",
    "von",
    "ty_le_dt_khcn",
    "co_gcn_khcn",
    "nu_lam_chu",
    "nganh",
    "dia_ban",
    "fdi",
)


def _field_can_hoi() -> tuple[str, ...]:
    """CHỈ hỏi field mà kho THẬT SỰ dùng — đừng bắt DN khai cho đủ bộ.

    PROFILE_FIELDS là thứ Profile CHỨA (10 field). Nếu hỏi hết 10 thì bot thành
    cái tờ khai, hỏi mãi mới chịu trả lời. Nên hỏi đúng:
      • field xuất hiện trong dieu_kien của chương trình nào đó, CỘNG
      • field mà bậc thang Điều 5 cần để ra quy mô (quy_mo_dnnvv là DẪN XUẤT,
        DN không tự khai được — phải hỏi nguyên liệu của nó)
    Kho đổi thì danh sách này tự đổi theo, không phải sửa tay.
    """
    can = {f for ct in KHO for dk in ct.dieu_kien for f in (dk.field,)}
    if "quy_mo_dnnvv" in can:
        can.discard("quy_mo_dnnvv")
        can |= {"linh_vuc", "lao_dong_bhxh", "doanh_thu"}  # nguyên liệu của Điều 5
    return tuple(f for f in PROFILE_FIELDS if f in can)


FIELD_CAN_HOI = _field_can_hoi()


def _nhan(f: str) -> str:
    return {
        "linh_vuc": "lĩnh vực (nông-lâm-thuỷ sản/công nghiệp-xây dựng hay thương mại-dịch vụ)",
        "lao_dong_bhxh": "số lao động tham gia BHXH bình quân năm",
        "doanh_thu": "tổng doanh thu của năm",
        "von": "tổng nguồn vốn của năm",
        "ty_le_dt_khcn": "tỷ lệ doanh thu từ sản phẩm KH&CN (% tổng doanh thu)",
        "co_gcn_khcn": "có Giấy chứng nhận doanh nghiệp KH&CN hay không",
        "nu_lam_chu": "doanh nghiệp có do phụ nữ làm chủ / sử dụng nhiều lao động nữ / là DN xã hội không",
        "nganh": "ngành",
        "dia_ban": "địa bàn",
        "fdi": "có vốn FDI hay không",
    }[f]


def _hieu_luc_the(ct) -> dict:
    """Trạng thái hiệu lực THẬT (② của đề) — đọc CACHE vbpl.vn, không gọi API.

    Lấy doc_id từ citation chính. chi_cache=True → không bao giờ block /chat.
    Cache hâm trước bằng scripts/ham_cache_vbpl.py. Cache miss → 'chưa xác định'
    (KHÔNG đoán — đúng nguyên tắc: thà nói chưa biết còn hơn khẳng định sai).
    """
    doc_id = None
    if ct.citation_chinh and ct.citation_chinh.doc_id:
        doc_id = ct.citation_chinh.doc_id
    elif ct.dieu_kien and ct.dieu_kien[0].citation.doc_id:
        doc_id = ct.dieu_kien[0].citation.doc_id
    if not doc_id:
        return {"da_doi_chieu": False, "con_hieu_luc": None, "nhan": "Chưa có mã văn bản"}

    try:
        from vbpl.api import tra_hieu_luc

        hl = tra_hieu_luc(doc_id, chi_cache=True)
    except Exception:  # noqa: BLE001
        return {"da_doi_chieu": False, "con_hieu_luc": None, "nhan": "Chưa đối chiếu"}

    if hl.loi:  # cache miss / lỗi → chưa đối chiếu được (đừng khẳng định)
        return {"da_doi_chieu": False, "con_hieu_luc": None, "nhan": hl.nhan}
    return {
        "da_doi_chieu": True,
        "con_hieu_luc": hl.con_hieu_luc,
        "nhan": hl.nhan,
        "ma": hl.ma,
        "so_quan_he": hl.so_quan_he,
        "nguon": "vbpl.vn (Bộ Tư pháp)",
    }


def _cho_dien_giai() -> bool:
    """Có bật bước LLM diễn giải không — cần key + không tắt bằng USE_LLM=0."""
    import os

    if os.getenv("USE_LLM", "1") == "0":
        return False
    if os.getenv("OPENAI_API_KEY"):
        return True
    from pathlib import Path

    return Path(".env").exists() and "OPENAI_API_KEY=" in Path(".env").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    """Landing tĩnh + curl-grep được — V1 là MÁY chấm, phải trả nhanh."""
    return {"ok": True, "service": "policyradar-bff", "so_chuong_trinh": len(KHO)}


@app.get("/luat/facets")
def luat_facets() -> dict:
    """Giá trị lọc (loại VB / lĩnh vực / cơ quan / năm) + số lượng — cho dropdown."""
    from matcher.luat_index import get_index

    return get_index().facets()


@app.get("/luat")
def danh_sach_luat(
    q: str = "",
    doc_type: str = "",
    linh_vuc: str = "",
    co_quan: str = "",
    nam: str = "",
    trang: int = 1,
    cs: int = 20,
) -> dict:
    """Danh sách LUẬT có tìm kiếm + lọc + phân trang — 2.669 văn bản trong corpus.

    Tra cứu thuần: KHÔNG cần hồ sơ, KHÔNG đối chiếu điều kiện. Chỉ metadata.
    """
    from matcher.luat_index import get_index

    return get_index().truy_van(q, doc_type, linh_vuc, co_quan, nam, trang, cs)


@app.get("/giam-sat")
def giam_sat() -> dict:
    """② — theo dõi hiệu lực + văn bản liên quan (thay thế/sửa đổi) từ vbpl.vn.

    Đây là phần "theo dõi cập nhật chính sách": mỗi văn bản flagship được đối
    chiếu trạng thái hiệu lực THẬT (Còn/Hết) và liệt kê văn bản liên quan mà
    vbpl.vn ghi nhận. Nếu một văn bản chuyển sang HẾT hiệu lực → badge đổi, DN
    được cảnh báo ngay (thay vì trích văn bản chết).
    """
    from vbpl.api import quan_he, tra_hieu_luc

    # nhãn loai tham chiếu vbpl (int) — chưa có bảng mã chính thức, để mô tả mềm
    LOAI = {3: "Căn cứ pháp lý", 4: "Văn bản liên quan / tiền nhiệm"}
    ra = []
    for ct in KHO:
        c = ct.citation_chinh or (ct.dieu_kien[0].citation if ct.dieu_kien else None)
        if not c or not c.doc_id:
            continue
        hl = tra_hieu_luc(c.doc_id, chi_cache=True)
        qh = quan_he(c.doc_id)
        # KHỬ TRÙNG: vbpl liệt kê cùng một văn bản nhiều lần (loai khác nhau).
        # Gộp theo tiêu đề, giữ lần đầu.
        seen_lq: set[str] = set()
        lq = []
        for r in qh:
            khoa = (r.get("title") or r.get("so_vb") or "").strip().lower()
            if not khoa or khoa in seen_lq:
                continue
            seen_lq.add(khoa)
            lq.append(
                {
                    "so_vb": r.get("so_vb"),
                    "title": (r.get("title") or "")[:120],
                    "loai": LOAI.get(r.get("loai"), "Liên quan"),
                }
            )
        ra.append(
            {
                "id": ct.id,
                "ten": ct.ten,
                "so_hieu": c.so_vb,
                "co_quan": ct.co_quan,
                "hieu_luc": {
                    "da_doi_chieu": hl.loi is None,
                    "con_hieu_luc": hl.con_hieu_luc,
                    "nhan": hl.nhan,
                    "ma": hl.ma,
                },
                "so_lien_quan": len(lq),
                "lien_quan": lq[:10],
            }
        )
    return {
        "chuong_trinh": ra,
        "nguon": "vbpl.vn (Bộ Tư pháp)",
        "cap_nhat": "đối chiếu khi tải trang; cache đĩa để không đơ",
    }


@app.get("/chuong-trinh")
def danh_sach_chuong_trinh() -> dict:
    """Danh sách LUẬT/chương trình hệ thống biết — cho sidebar 'Danh sách luật'.

    Mỗi mục kèm căn cứ (điều–khoản + nguyên văn corpus) và hiệu lực THẬT (vbpl.vn).
    KHÔNG cần hồ sơ — đây là tra cứu thuần, không đối chiếu điều kiện.
    """
    ra = []
    for ct in KHO:
        cits = []
        seen = set()
        for dk in ct.dieu_kien:
            c = dk.citation
            if c.khoa in seen:
                continue
            seen.add(c.khoa)
            cits.append(
                {
                    "hien_thi": str(c),
                    "so_vb": c.so_vb,
                    "co_quan": c.co_quan,
                    "trich": c.trich,
                    "doc_id": c.doc_id,
                    "yeu_cau": dk.mo_ta,
                }
            )
        ra.append(
            {
                "id": ct.id,
                "ten": ct.ten,
                "co_quan": ct.co_quan,
                "loai": ct.loai,
                "gia_tri": ct.gia_tri_mo_ta,
                "han_nop": ct.han_nop,
                "so_hieu_chinh": ct.citation_chinh.so_vb if ct.citation_chinh else None,
                "hieu_luc": _hieu_luc_the(ct),
                "can_cu": cits,
            }
        )
    return {"tong": len(ra), "chuong_trinh": ra}


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

    # ── CÂU META / LẠC ĐỀ → hiểu context, KHÔNG chạy matcher ──────
    # Bug thật: hồ sơ đầy từ lượt trước → "bạn bao tuổi" cũng ra kết quả đủ
    # điều kiện. Bot phải nhận ra câu KHÔNG hỏi chính sách và chuyển hướng.
    if cau_meta_lac_de(cau):
        return {
            "dang": "van_ban",
            "text": cau_chuyen_huong(),
            "noi_dung": cau_chuyen_huong(),
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

    thieu = [f for f in FIELD_CAN_HOI if getattr(p, f) is None]

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
                "loai": k.chuong_trinh.loai,  # E2E bắt: thiếu field này → frontend hardcode "uu-dai-thue" → thẻ gắn nhãn SAI
                "gia_tri": k.chuong_trinh.gia_tri_mo_ta,
                "gia_tri_ky_vong": format_vnd(int(k.gia_tri_ky_vong)),
                "han_nop": k.chuong_trinh.han_nop,
                "du_dieu_kien": k.du_dieu_kien,
                "do_tin_cay": k.diem_phu_hop,
                "thieu": k.thieu,  # tên ĐÍCH DANH điều kiện chưa đạt
                "can_hoi_them": k.can_hoi_them,
                "hieu_luc": _hieu_luc_the(k.chuong_trinh),  # ② — trạng thái thật từ vbpl.vn
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

    # ── ① INTERPRETING: LLM diễn giải + GUARD gác số live ─────
    # Đây là chỗ guard load-bearing thật: LLM sinh text → lớp số tất định kiểm
    # ngay, số bịa → tô đỏ. Bật/tắt bằng USE_LLM (mặc định bật nếu có key).
    du = [k.chuong_trinh for k in kq if k.du_dieu_kien]
    dg = None
    if du and _cho_dien_giai():
        try:
            from bff.dien_giai import dien_giai_va_gac

            dg = dien_giai_va_gac(du, [c.ten for c in du])
        except Exception:  # noqa: BLE001
            dg = None  # không bao giờ làm hỏng /chat vì diễn giải

    return {
        "dang": "ket_qua",
        "noi_dung": f"Với hồ sơ này, mình tìm thấy {sum(1 for k in kq if k.du_dieu_kien)}"
        f"/{len(kq)} chương trình bạn đủ điều kiện.",
        "chuong_trinh": the,
        "dien_giai": dg,  # {text, grounded, so_bia, canh_bao} hoặc None
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
