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

import re
import sys
import time
from typing import Any

sys.path.insert(0, ".")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from ho_so.mau import TAT_CA, THEO_CHUONG_TRINH  # noqa: E402
from ho_so.sinh import checklist, render_text  # noqa: E402
from matcher.kiem_ho_so import kiem, mo_ta_loi  # noqa: E402
from matcher.match import diff_ket_qua, quet_nguoc  # noqa: E402
from matcher.pham_vi import (  # noqa: E402
    cau_chuyen_huong,
    cau_meta_lac_de,
    cau_moi_tra_cuu,
    cau_tra_cuu_chung,
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
    # dev: localhost; deploy: mọi domain *.up.railway.app (frontend Railway).
    allow_origins=["http://localhost:3002", "http://localhost:3000"],
    allow_origin_regex=r"https://.*\.up\.railway\.app",
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


# nhãn NGẮN cho thẻ chương trình
_NHAN_NGAN = {
    "linh_vuc": "lĩnh vực", "lao_dong_bhxh": "số lao động BHXH",
    "doanh_thu": "doanh thu năm", "von": "tổng nguồn vốn",
    "ty_le_dt_khcn": "tỷ lệ DT KH&CN", "co_gcn_khcn": "GCN DN KH&CN",
    "nu_lam_chu": "nữ làm chủ", "nganh": "ngành", "dia_ban": "địa bàn", "fdi": "vốn FDI",
}
# quy mô DNNVV là DẪN XUẤT — không tự khai được, phải khai nguyên liệu của nó
_NGUYEN_LIEU = {"quy_mo_dnnvv": ("linh_vuc", "lao_dong_bhxh", "doanh_thu")}


def _can_bo_sung(can_hoi_them: list[str], p: "Profile") -> list[dict]:
    """Field NGƯỜI DÙNG cần khai để nâng độ tin cậy → 100%.

    Điều kiện 'thiếu tin' có thể là field dẫn xuất (quy_mo_dnnvv) → nở thành
    nguyên liệu (lĩnh vực/lao động/doanh thu) và CHỈ giữ cái còn TRỐNG.
    """
    fields: list[str] = []
    for f in can_hoi_them:
        for x in _NGUYEN_LIEU.get(f, (f,)):
            if getattr(p, x, None) is None and x not in fields:
                fields.append(x)
    return [{"field": x, "nhan": _NHAN_NGAN.get(x, x)} for x in fields]


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


def _url_van_ban(doc_id: str | None) -> str | None:
    """source_url của văn bản (vbpl.vn) để mọi citation bấm mở bài gốc."""
    if not doc_id:
        return None
    try:
        from matcher.luat_index import get_index

        return get_index().url_theo_id(doc_id)
    except Exception:  # noqa: BLE001
        return None


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


_MIEN_BAC = {
    "Hà Nội", "Hải Phòng", "Quảng Ninh", "Bắc Ninh", "Bắc Giang", "Bắc Kạn",
    "Cao Bằng", "Điện Biên", "Hà Giang", "Hà Nam", "Hải Dương", "Hòa Bình",
    "Hưng Yên", "Lai Châu", "Lạng Sơn", "Lào Cai", "Nam Định", "Ninh Bình",
    "Phú Thọ", "Sơn La", "Thái Bình", "Thái Nguyên", "Tuyên Quang", "Vĩnh Phúc",
    "Yên Bái",
}
_MIEN_TRUNG = {
    "Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế",
    "Đà Nẵng", "Quảng Nam", "Quảng Ngãi", "Bình Định", "Phú Yên", "Khánh Hòa",
    "Ninh Thuận", "Bình Thuận", "Kon Tum", "Gia Lai", "Đắk Lắk", "Đắk Nông",
    "Lâm Đồng",
}
_MIEN_NAM = {
    "Hồ Chí Minh", "Bà Rịa - Vũng Tàu", "Bình Dương", "Bình Phước", "Đồng Nai",
    "Tây Ninh", "An Giang", "Bạc Liêu", "Bến Tre", "Cà Mau", "Cần Thơ",
    "Đồng Tháp", "Hậu Giang", "Kiên Giang", "Long An", "Sóc Trăng", "Tiền Giang",
    "Trà Vinh", "Vĩnh Long",
}
_TINH_MIEN = {
    **{t: "Bắc" for t in _MIEN_BAC},
    **{t: "Trung" for t in _MIEN_TRUNG},
    **{t: "Nam" for t in _MIEN_NAM},
}
# cơ quan cấp TRUNG ƯƠNG — không thuộc miền nào
_TW_RE = re.compile(
    r"^\s*(Chính phủ|Quốc hội|Bộ |Ngân hàng Nhà nước|Thủ tướng|Văn phòng"
    r"|[UƯ]ỷ? ?ban Thường vụ|Tòa án|Viện |Kiểm toán|Bảo hiểm xã hội)",
    re.IGNORECASE,
)


def _dia_ly(co_quan: str | None) -> tuple[str, str]:
    """(tỉnh, miền) suy từ cơ quan ban hành. TW → ('', 'Trung ương').

    vbpl.vn ghi cơ quan dạng 'UBND Tỉnh X' / 'HĐND Thành phố Y' / 'Chính phủ'.
    Bóc tên tỉnh rồi tra bảng miền; quận/huyện gộp về TP.HCM; gộp biến thể hoa/thường.
    """
    cq = (co_quan or "").strip()
    if not cq or _TW_RE.match(cq):
        return "", "Trung ương"
    m = re.sub(r"^\s*(UBND|HĐND|Ủy ban nhân dân|Hội đồng nhân dân)\s*", "", cq, flags=re.I)
    m = re.sub(r"^\s*(Tỉnh|Thành phố|TP\.?)\s*", "", m, flags=re.I).strip()
    low = m.lower()
    if low.startswith("quận") or low.startswith("huyện"):
        m = "Hồ Chí Minh"  # quận/huyện đều thuộc TP.HCM trong corpus này
    elif low == "huế":
        m = "Thừa Thiên Huế"
    else:
        for t in _TINH_MIEN:  # gộp biến thể hoa/thường: "BÌNH ĐỊNH" → "Bình Định"
            if t.lower() == low:
                m = t
                break
    return m, _TINH_MIEN.get(m, "Khác")


@app.get("/giam-sat")
def giam_sat() -> dict:
    """② — theo dõi hiệu lực: MỘT bảng văn bản kho + trạng thái THẬT (vbpl.vn).

    Trả toàn bộ văn bản đã đối chiếu (scripts/cron_giam_sat.py quét vbpl.vn, cache
    đĩa) — mỗi dòng có trạng thái Còn/Hết. Frontend là 1 bảng + tìm kiếm + lọc.
    """
    from matcher.luat_index import get_index

    quet = _nap_quet()
    area = {v.item_id: v.linh_vuc for v in get_index().ds}  # item_id → lĩnh vực
    # CHỈ giữ văn bản LIÊN QUAN đề (chính sách DN) — bỏ nội bộ/hành chính.
    van_ban = []
    for r in quet:
        if r.get("con_hieu_luc") is None:  # có kết luận rõ Còn/Hết
            continue
        if not _lien_quan_dn(r.get("tieu_de"), area.get(r.get("item_id"))):
            continue
        tinh, mien = _dia_ly(r.get("co_quan"))
        van_ban.append({
            "id": r.get("item_id"),  # khoá ổn định cho dấu sao (ghim) ở frontend
            "so_hieu": r.get("so_hieu"),
            "tieu_de": r.get("tieu_de"),
            "nam": r.get("nam"),
            "co_quan": r.get("co_quan"),
            "tinh": tinh,  # '' nếu TW
            "mien": mien,  # Bắc | Trung | Nam | Trung ương
            "url": r.get("url"),
            "nhan": r.get("nhan"),
            "con_hieu_luc": r.get("con_hieu_luc"),
        })
    # CÒN hiệu lực lên đầu, HẾT hiệu lực xuống cuối; trong mỗi nhóm mới nhất trước
    van_ban.sort(key=lambda x: (x["con_hieu_luc"] is False, -(x.get("nam") or 0)))
    n_het = sum(1 for v in van_ban if v["con_hieu_luc"] is False)

    return {
        "van_ban": van_ban,
        "n_het": n_het,
        "n_con": len(van_ban) - n_het,
        "tong_kho": 2669,
        "nguon": "vbpl.vn (Bộ Tư pháp)",
        "cap_nhat": "đối chiếu trực tiếp vbpl.vn, cache đĩa",
    }


# Văn bản "liên quan doanh nghiệp" (miền sản phẩm phủ) vs nội bộ/hành chính.
# legal_area 75% "Chưa phân loại" → không đủ; kết hợp keyword tiêu đề.
_DN_KW = (
    "doanh nghiệp", "hỗ trợ", "ưu đãi", "đầu tư", "thuế", "khoa học", "công nghệ",
    "tín dụng", "cho vay", "nhỏ và vừa", "khởi nghiệp", "đổi mới sáng tạo",
    "xuất khẩu", "nhập khẩu", "chuyển giao", "khu công nghiệp", "cụm công nghiệp",
    "tài trợ", "sản xuất", "kinh doanh", "chuyển đổi số", "hợp tác xã",
    "lãi suất", "ngành nghề", "quỹ",
)
_DN_AREA = ("khoa học", "công nghệ", "đầu tư", "thuế", "doanh nghiệp",
            "xuất nhập khẩu", "công nghiệp")


def _lien_quan_dn(tieu_de: str | None, legal_area: str | None) -> bool:
    a = (legal_area or "").lower()
    if any(k in a for k in _DN_AREA):
        return True
    s = (tieu_de or "").lower()
    return any(k in s for k in _DN_KW)


def _nap_quet() -> list[dict]:
    """Đọc bản quét hiệu lực kho (scripts/quet_hieu_luc.py). Thiếu file → rỗng."""
    import json as _json
    from pathlib import Path as _Path

    f = _Path("./data/giam_sat_quet.json")
    if not f.exists():
        return []
    try:
        return _json.loads(f.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []


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
                # số biểu mẫu — đếm từ mapping, KHÔNG sinh form → hiện được ngay lúc vào
                "so_bieu_mau": len(THEO_CHUONG_TRINH.get(ct.id, [])),
            }
        )
    return {"tong": len(ra), "chuong_trinh": ra}


def _van_ban(text: str, da_che: dict, t0: float, ho_so: dict) -> dict:
    """Phản hồi văn bản thuần (chào/tra cứu/lạc đề) — không phán quyết điều luật."""
    return {
        "dang": "van_ban",
        "text": text,
        "noi_dung": text,
        "grounded": False,
        "citations": [],
        "requires_approval": False,
        "ho_so_moi": ho_so,  # đồng bộ hồ sơ GPT trích được về frontend
        "pii_da_che": list(da_che.keys()),
        "ms": int((time.perf_counter() - t0) * 1000),
    }


@app.post("/chat")
def chat(r: YeuCau) -> dict:
    t0 = time.perf_counter()

    # ── H1: nở viết tắt, chịu được gõ không dấu ───────────────
    cau = no_viet_tat(r.cau)

    # ── H2: che PII TRƯỚC khi câu này có thể đi ra LLM ────────
    cau_an_toan, da_che = che_pii(cau)

    ho_so = dict(r.ho_so)  # sẽ gộp thêm field GPT trích được

    # ── SAFETY NET (luôn chạy, KHÔNG phải intent routing): scope honesty ──
    # Giữ tất định 2 net này vì chúng bảo đảm TRUNG THỰC về phạm vi kho,
    # thứ GPT có thể lỡ bịa. (bộ ca đối kháng: "ưu đãi nông nghiệp" → không bịa)
    vb = hoi_van_ban_ngoai_kho(cau)
    if vb:
        return _van_ban(cau_tu_choi_van_ban(vb), da_che, t0, ho_so)
    lv = ngoai_pham_vi(cau)
    if lv:
        return _van_ban(cau_tu_choi_linh_vuc(lv), da_che, t0, ho_so)

    # ── TẦNG HỘI THOẠI GPT: hiểu ý + trích hồ sơ + trả lời tự nhiên ──
    # Thay routing regex cứng. GPT KHÔNG quyết eligibility/số — chỉ dẫn hội thoại.
    tra_loi_gpt: str | None = None
    gpt_yd: str | None = None
    if _cho_dien_giai():  # có key + USE_LLM
        try:
            from bff.hoi_thoai import hieu

            hk = hieu(cau_an_toan, ho_so)
        except Exception:  # noqa: BLE001
            hk = None
        if hk:
            ho_so = {**ho_so, **hk["ho_so"]}  # gộp field GPT trích
            gpt_yd = hk["y_dinh"]
            tra_loi_gpt = hk["tra_loi"]
            if gpt_yd == "tro_chuyen":
                return _van_ban(tra_loi_gpt or cau_chuyen_huong(), da_che, t0, ho_so)
            if gpt_yd == "tra_cuu":
                return _van_ban(tra_loi_gpt or cau_moi_tra_cuu(), da_che, t0, ho_so)
            # gpt_yd == "ket_qua" → xuống lõi tất định với ho_so đã gộp

    # ── FALLBACK RULE (GPT tắt/lỗi): intent routing cũ trên câu gốc ──
    if gpt_yd is None:
        if cau_meta_lac_de(cau):
            return _van_ban(cau_chuyen_huong(), da_che, t0, ho_so)
        if cau_tra_cuu_chung(cau):
            return _van_ban(cau_moi_tra_cuu(), da_che, t0, ho_so)

    p = Profile(**{k: v for k, v in ho_so.items() if k in PROFILE_FIELDS})

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
            "ho_so_moi": ho_so,
            "pii_da_che": list(da_che.keys()),
            "ms": int((time.perf_counter() - t0) * 1000),
        }

    thieu = [f for f in FIELD_CAN_HOI if getattr(p, f) is None]

    # ── CHƯA KHAI GÌ → hỏi (onboarding). Nhưng CHỈ CẦN 1 field là ĐÃ quét được:
    # vd "có GCN DN KH&CN" ra ngay 2 gói KH&CN chỉ cần GCN (đủ) + các gói khác
    # (gần đạt, kèm "cần bổ sung"). 1 tiêu chí PHẢI ra gói trong tầm với, đừng
    # bắt khai đủ bộ mới cho xem. Dùng câu hỏi TỰ NHIÊN của GPT nếu có.
    if len(thieu) == len(FIELD_CAN_HOI):
        hoi = tra_loi_gpt or (
            "Để quét đúng chính sách bạn đủ điều kiện, cho mình biết thêm: "
            + ", ".join(_nhan(f) for f in thieu[:3])
            + "?"
        )
        return {
            "dang": "hoi_ho_so",
            "noi_dung": hoi,
            "dang_hoi": thieu,
            "ho_so_moi": ho_so,
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
                # None khi chương trình CHƯA LƯỢNG HOÁ được giá trị (gia_tri_uoc=None):
                # gửi "0 đ" sẽ hiểu nhầm là giá trị bằng 0. Ẩn hẳn ô số, để mô tả chữ nói.
                "gia_tri_ky_vong": (
                    format_vnd(int(k.gia_tri_ky_vong))
                    if k.chuong_trinh.gia_tri_uoc is not None
                    else None
                ),
                # nhãn mức hỗ trợ khi không có số đồng (100%/miễn phí/≤50% lãi suất…)
                "gia_tri_nhan": k.chuong_trinh.gia_tri_nhan,
                "han_nop": k.chuong_trinh.han_nop,
                "du_dieu_kien": k.du_dieu_kien,
                "xac_quyet": k.xac_quyet,  # 'du' | 'khong' | 'gan_dat' — 3 trạng thái, KHÔNG gộp thiếu-tin vào đủ
                "do_tin_cay": k.diem_phu_hop,
                "thieu": k.thieu,  # tên ĐÍCH DANH điều kiện chưa đạt
                "can_hoi_them": k.can_hoi_them,
                "can_bo_sung": _can_bo_sung(k.can_hoi_them, p),  # field khai để lên 100%
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
                            "url": _url_van_ban(c.dieu_kien.citation.doc_id),  # bấm mở bài gốc
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

    n_du = sum(1 for k in kq if k.xac_quyet == "du")
    n_gan = sum(1 for k in kq if k.xac_quyet == "gan_dat")
    tom_tat = f"Với hồ sơ này, mình tìm thấy {n_du} chương trình bạn đủ điều kiện"
    if n_gan:
        tom_tat += f", {n_gan} chương trình gần đạt (cần bổ sung thông tin)"
    tom_tat += "."

    from matcher.luat_index import get_index

    return {
        "dang": "ket_qua",
        "noi_dung": tom_tat,
        "chuong_trinh": the,
        "da_quet": len(get_index().ds),  # số văn bản corpus THẬT (không hardcode)
        "dien_giai": dg,  # {text, grounded, so_bia, canh_bao} hoặc None
        "ho_so_moi": ho_so,  # đồng bộ hồ sơ GPT trích được về frontend
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


@app.get("/ho-so/chuong-trinh")
def ho_so_chuong_trinh() -> dict:
    """Chương trình CÓ bộ hồ sơ (cho picker Soạn hồ sơ) + số biểu mẫu — hiện ngay.

    Gồm cả NAFOSTED (tài trợ nghiên cứu) — chương trình này KHÔNG nằm trong KHO
    matcher (tài trợ xét theo nhiệm vụ, không theo điều kiện DN đơn thuần) nhưng
    có bộ biểu mẫu thật từ 44/2025/TT-BKHCN.
    """
    ten_kho = {ct.id: (ct.ten, ct.co_quan) for ct in KHO}
    ten_ngoai = {
        "nafosted": (
            "Tài trợ nghiên cứu khoa học và công nghệ (NAFOSTED)",
            "Quỹ Phát triển KH&CN Quốc gia",
        ),
    }
    ra = []
    for cid, ma_list in THEO_CHUONG_TRINH.items():
        ten, co_quan = ten_kho.get(cid) or ten_ngoai.get(cid, (cid, ""))
        ra.append({"id": cid, "ten": ten, "co_quan": co_quan, "so_bieu_mau": len(ma_list)})
    return {"chuong_trinh": ra}


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
