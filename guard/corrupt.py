"""ĐÒN #4 — sinh hard-negative "bịa điều luật". Thuần rule, KHÔNG dùng LLM.

Nhiệm vụ: từ một khoản luật THẬT, sinh ra các câu AI-có-thể-bịa, để guard học phân biệt.

⚠️ HARD-negative, không phải EASY-negative:
  "Nghị định 9999/1800" → vô dụng, nhìn là biết giả.
  "Nghị định 99/2026/NĐ-CP" → đúng format, năm hợp lý, số trong dải thật → MỚI KHÓ.

7 phép nhiễu gốc, **còn 6** sau khi kiểm data thật:
  #1 số văn bản giả        ✅ (khoá = số + cơ quan, vì 31 tỉnh trùng số 14/2025/QĐ-UBND)
  #2 sai điều/khoản        ✅
  #3 sai mức %             ✅
  #4 sai hạn/ngày          ✅
  #5 sai ngưỡng tiền       ✅
  #6 sai cơ quan ban hành  ✅
  #7 trích văn bản hết hiệu lực  ❌ BỎ — dump không có field hiệu lực, không bịa data được
  #8 bịa điều kiện thụ hưởng ✅ (trục ngữ nghĩa — chỉ NLI bắt được, phần đáng khoe)
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from guard.vn_number import bóc_số

# ── mẫu số hiệu văn bản VN ────────────────────────────────────────
RE_SO_VB = re.compile(r"\b(\d{1,3})/(\d{4})/(NĐ-CP|TT-[A-ZĐ]{2,6}|QĐ-[A-ZĐ]{2,6}|NQ-[A-ZĐ]{2,6})\b")

CO_QUAN_GIA = [
    "Bộ Tài chính",
    "Bộ Kế hoạch và Đầu tư",
    "Bộ Khoa học và Công nghệ",
    "Bộ Công Thương",
    "Chính phủ",
    "Thủ tướng Chính phủ",
    "Bộ Thông tin và Truyền thông",
]

# ── trục NGỮ NGHĨA (#8) ───────────────────────────────────────────
# ⚠️ BÀI HỌC ĐẮT: bản đầu chỉ có 3 template CỐ ĐỊNH → model học thuộc câu chữ,
#    bắt bịa ra 1.000 nhưng là số GIẢ (nó nhận diện template, không hiểu grounding).
#    Kho cảnh báo: "F1=1.00 = data synthetic quá dễ, đừng khoe".
# → Sinh đa dạng: 4 kiểu bịa × nhiều cách diễn đạt × nội dung LẤY TỪ CHÍNH KHOẢN.

_MO = [
    "Theo {cit}, {noi_dung}",
    "Căn cứ {cit}, {noi_dung}",
    "{cit} quy định {noi_dung}",
    "Đối chiếu {cit} thì {noi_dung}",
    "Như {cit} đã nêu, {noi_dung}",
]

# kiểu 1 — TỔNG QUÁT HOÁ QUÁ ĐÀ: bỏ hết điều kiện ràng buộc
_TONG_QUAT = [
    "mọi doanh nghiệp nhỏ và vừa đều mặc nhiên đủ điều kiện nhận hỗ trợ",
    "tất cả doanh nghiệp trong ngành đều được hưởng, không cần điều kiện gì thêm",
    "doanh nghiệp nào nộp hồ sơ cũng sẽ được duyệt",
    "quy định này áp dụng cho toàn bộ doanh nghiệp trên cả nước",
]

# kiểu 2 — TỰ KHẲNG ĐỊNH ĐỦ ĐIỀU KIỆN (anti-sycophancy)
_DU_DK = [
    "doanh nghiệp của bạn đã đủ điều kiện, có thể nộp hồ sơ ngay",
    "hồ sơ bạn mô tả hoàn toàn đáp ứng, không thiếu tiêu chí nào",
    "trường hợp này chắc chắn được chấp thuận",
    "bạn đủ điều kiện hưởng mức hỗ trợ cao nhất",
]

# kiểu 3 — BỎ RÀNG BUỘC / PHỦ ĐỊNH ĐIỀU KIỆN
_BO_RANG_BUOC = [
    "doanh nghiệp không cần đáp ứng thêm tiêu chí nào khác",
    "không có giới hạn về thời gian nộp hồ sơ",
    "không yêu cầu giấy chứng nhận nào kèm theo",
    "việc thẩm định là thủ tục hình thức, không ảnh hưởng kết quả",
]

# kiểu 4 — SUY DIỄN THẨM QUYỀN / HIỆU LỰC mà nguồn không hề nói
_SUY_DIEN = [
    "quy định này vẫn còn hiệu lực và được áp dụng thống nhất toàn quốc",
    "cơ quan thuế có trách nhiệm tự động áp dụng ưu đãi này",
    "doanh nghiệp được truy lĩnh phần hỗ trợ của các năm trước",
    "mức hỗ trợ này được cộng dồn với các chương trình khác",
]

_KIEU_NGU_NGHIA = [
    ("bia_tong_quat_hoa", _TONG_QUAT),
    ("bia_tu_du_dieu_kien", _DU_DK),
    ("bia_bo_rang_buoc", _BO_RANG_BUOC),
    ("bia_suy_dien", _SUY_DIEN),
]


@dataclass(frozen=True)
class TrichDan:
    doc_number: str
    co_quan: str
    dieu: int
    khoan: int

    def __str__(self) -> str:
        return f"Khoản {self.khoan} Điều {self.dieu} {self.doc_number} do {self.co_quan} ban hành"


@dataclass
class Cap:
    """Một cặp (premise, hypothesis) để train NLI."""

    premise: str
    hypothesis: str
    label: int  # 1 = grounded (premise entail hypothesis), 0 = bịa
    corruption_type: str | None
    doc_id: str
    gia_tri_goc: str | None = None
    gia_tri_bia: str | None = None


def _cau_co_so(text: str) -> list[str]:
    """Cắt khoản thành câu, chỉ giữ câu có %/tiền/ngày — thứ THẬT SỰ bịa được.

    ⚠️ KHÔNG nhận số thô (số điều, số thứ tự, "05 năm"): câu chỉ có số thô thì
    không sinh được nhiễu trục SỐ → cặp đó chỉ đẻ ra nhiễu trục ĐỊNH DANH →
    lệch trục → model chỉ học mẹo soi citation, mù với số bịa.
    Bản đầu dùng bóc_số() (nhận cả số thô) → ra 900 định danh vs 51 số. Đã sửa.
    """
    cau = re.split(r"(?<=[.;])\s+", text)
    ra = []
    for c in cau:
        c = c.strip()
        if not (40 < len(c) < 600):
            continue
        if any(s.loai in ("phan_tram", "tien", "ngay") for s in bóc_số(c)):
            ra.append(c)
    return ra


# ── các phép nhiễu ────────────────────────────────────────────────


def bia_so_van_ban(cit: TrichDan, rng: random.Random) -> tuple[TrichDan, str, str]:
    """#1 — đổi số nghị định sang số KHÔNG có thật nhưng đúng format, năm hợp lý."""
    m = RE_SO_VB.search(cit.doc_number)
    if m:
        so, nam, hau_to = int(m.group(1)), int(m.group(2)), m.group(3)
        so_moi = so + rng.choice([7, 13, 21, 34, 46])
        nam_moi = rng.choice([nam, nam, min(nam + 1, 2026)])
        moi = f"{so_moi}/{nam_moi}/{hau_to}"
    else:
        moi = f"{rng.randint(40, 190)}/2026/NĐ-CP"
    return (
        TrichDan(moi, cit.co_quan, cit.dieu, cit.khoan),
        cit.doc_number,
        moi,
    )


def bia_dieu_khoan(cit: TrichDan, rng: random.Random) -> tuple[TrichDan, str, str]:
    """#2 — văn bản đúng, nhưng trỏ sai vị trí điều/khoản."""
    d = cit.dieu + rng.choice([1, 2, 3, 5, -1]) if cit.dieu > 1 else cit.dieu + rng.randint(1, 4)
    k = max(1, cit.khoan + rng.choice([1, 2, -1]))
    return (
        TrichDan(cit.doc_number, cit.co_quan, max(1, d), k),
        f"Điều {cit.dieu} Khoản {cit.khoan}",
        f"Điều {max(1, d)} Khoản {k}",
    )


def bia_co_quan(cit: TrichDan, rng: random.Random) -> tuple[TrichDan, str, str]:
    """#6 — sai cơ quan ban hành."""
    khac = [c for c in CO_QUAN_GIA if c.lower() not in cit.co_quan.lower()]
    moi = rng.choice(khac) if khac else "Bộ Tài chính"
    return TrichDan(cit.doc_number, moi, cit.dieu, cit.khoan), cit.co_quan, moi


def bia_so_trong_cau(cau: str, rng: random.Random) -> tuple[str, str, str, str] | None:
    """#3/#4/#5 — đổi một con số trong câu. Trả (câu_bịa, loại, gốc, bịa)."""
    so = [s for s in bóc_số(cau) if s.loai in ("phan_tram", "tien", "ngay")]
    if not so:
        return None
    s = rng.choice(so)

    if s.loai == "phan_tram":
        goc = int(s.gia_tri)
        moi = rng.choice([v for v in (10, 20, 30, 50, 70, 80, 100) if v != goc])
        thay = f"{moi}%"
        loai = "sai_muc_phan_tram"
    elif s.loai == "tien":
        # bẫy đắt nhất: giữ nguyên chữ số, ĐỔI BẬC ĐƠN VỊ (lệch 1000×)
        if "tỷ" in s.raw or "tỉ" in s.raw:
            thay = s.raw.replace("tỷ", "triệu").replace("tỉ", "triệu")
        elif "triệu" in s.raw:
            thay = s.raw.replace("triệu", "tỷ")
        else:
            thay = s.raw
        if thay == s.raw:  # không đổi được bậc → đổi chữ số
            m = re.search(r"\d[\d.,]*", s.raw)
            if not m:
                return None
            thay = s.raw.replace(m.group(0), str(rng.choice([5, 10, 50, 100])), 1)
        loai = "sai_nguong_tien"
    else:
        # GIỮ NGUYÊN FORMAT gốc — "30/3/2016" phải bịa thành "28/9/2016",
        # KHÔNG được rụng năm thành "28/9" (nhìn là biết giả = easy-negative vô dụng).
        m = re.match(r"(\d{1,2})([/-])(\d{1,2})(?:([/-])(\d{4}))?", s.raw)
        if not m:
            return None
        ngay, sep, thang, sep2, nam = m.groups()
        ngay_moi = rng.choice([d for d in (5, 15, 25, 28) if d != int(ngay)])
        thang_moi = rng.choice([t for t in (3, 6, 9, 12) if t != int(thang)])
        thay = f"{ngay_moi}{sep}{thang_moi}"
        if nam:  # có năm thì GIỮ năm
            thay += f"{sep2}{nam}"
        loai = "sai_han_ngay"

    if thay == s.raw:
        return None
    return cau[: s.bat_dau] + thay + cau[s.ket_thuc :], loai, s.raw, thay


# ── sinh cặp ──────────────────────────────────────────────────────


def sinh_cap(
    khoan_text: str, cit: TrichDan, doc_id: str, rng: random.Random
) -> list[Cap]:
    """1 khoản → 1 positive + nhiều hard-negative đủ các trục."""
    cau = _cau_co_so(khoan_text)
    if not cau:
        return []
    c = rng.choice(cau)
    ra: list[Cap] = []

    # POSITIVE — trích đúng, citation đúng
    ra.append(
        Cap(
            premise=khoan_text,
            hypothesis=f"Theo {cit}, {c}",
            label=1,
            corruption_type=None,
            doc_id=doc_id,
        )
    )

    # ── trục ĐỊNH DANH — lấy NGẪU NHIÊN 2/3, không lấy cả 3 ──
    # Lấy cả 3 thì tỉ lệ ra 60% định danh / 20% số → model chỉ học mẹo soi citation.
    # Mục tiêu kế hoạch: ~40% định danh / ~35% số / ~25% ngữ nghĩa.
    dinh_danh = [
        ("bia_so_van_ban", bia_so_van_ban),
        ("bia_dieu_khoan", bia_dieu_khoan),
        ("bia_co_quan", bia_co_quan),
    ]
    for ten, f in rng.sample(dinh_danh, 2):
        cit2, goc, bia = f(cit, rng)
        ra.append(
            Cap(
                premise=khoan_text,
                hypothesis=f"Theo {cit2}, {c}",
                label=0,
                corruption_type=ten,
                doc_id=doc_id,
                gia_tri_goc=goc,
                gia_tri_bia=bia,
            )
        )

    # ── trục SỐ — sinh tới 2 biến thể để cân với trục định danh ──
    da_co: set[str] = set()
    for _ in range(4):  # thử vài lần, giữ tối đa 2 bản khác nhau
        r = bia_so_trong_cau(c, rng)
        if not r:
            break
        cau_bia, loai, goc, bia = r
        if cau_bia in da_co:
            continue
        da_co.add(cau_bia)
        ra.append(
            Cap(
                premise=khoan_text,
                hypothesis=f"Theo {cit}, {cau_bia}",
                label=0,
                corruption_type=loai,
                doc_id=doc_id,
                gia_tri_goc=goc,
                gia_tri_bia=bia,
            )
        )
        if len(da_co) >= 2:
            break

    # ── trục NGỮ NGHĨA (#8) — không số nào sai, nhưng nguồn không hề nói vậy ──
    # Đa dạng hoá: 4 kiểu × 5 cách mở câu → model không học thuộc được template.
    ten_kieu, kho_cau = rng.choice(_KIEU_NGU_NGHIA)
    ra.append(
        Cap(
            premise=khoan_text,
            hypothesis=rng.choice(_MO).format(cit=cit, noi_dung=rng.choice(kho_cau)),
            label=0,
            corruption_type=ten_kieu,
            doc_id=doc_id,
        )
    )
    return ra
