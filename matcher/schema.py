"""Mô hình dữ liệu matcher — điều kiện thụ hưởng CẤU TRÚC HOÁ.

VÌ SAO PHẢI CẤU TRÚC (không để LLM tự đoán):
Khối demo 2 của đề đòi bot nói **"chưa, vì thiếu Y"** — gọi tên đích danh điều
kiện còn thiếu. LLM tự do không ra được câu đó ổn định. Muốn nêu đích danh Y thì
Y phải là một field so sánh được.

Kho chốt: "Suy luận đủ-điều-kiện (đối chiếu hồ sơ)" là LỚP RIÊNG, chạy TRƯỚC
ranker. RAG chỉ lo tra/diễn giải tài liệu, KHÔNG lo quyết định đủ-hay-không.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class Citation:
    """Trỏ về đúng điều–khoản trong corpus. Không có cái này = không được khẳng định."""

    so_vb: str
    co_quan: str
    dieu: int
    khoan: int | None = None
    trich: str = ""  # nguyên văn đoạn làm căn cứ — CHÉP, không diễn giải
    doc_id: str | None = None

    @property
    def khoa(self) -> str:
        return f"{self.so_vb}|Đ{self.dieu}|K{self.khoan or '-'}"

    def __str__(self) -> str:
        k = f" Khoản {self.khoan}" if self.khoan else ""
        return f"Điều {self.dieu}{k} {self.so_vb}"


class ToanTu(str, Enum):
    GTE = ">="
    LTE = "<="
    EQ = "=="
    IN = "in"
    NOT_IN = "not_in"


class TrangThai(str, Enum):
    DAT = "dat"
    KHONG_DAT = "khong_dat"
    THIEU_TIN = "thieu_tin"  # hồ sơ chưa khai field này → HỎI, đừng đoán


@dataclass(frozen=True)
class DieuKien:
    """Một điều kiện thụ hưởng, so sánh được bằng CODE."""

    field: str  # tên field trong Profile
    toan_tu: ToanTu
    nguong: Any
    mo_ta: str  # câu người đọc: "Chi R&D ≥ 1% doanh thu"
    citation: Citation
    bat_buoc: bool = True  # False = điều kiện cộng điểm, không loại


@dataclass(frozen=True)
class ChuongTrinh:
    id: str
    ten: str
    co_quan: str
    loai: str
    dieu_kien: list[DieuKien]
    gia_tri_mo_ta: str  # "Miễn 4 năm, giảm 50% trong 9 năm tiếp theo"
    gia_tri_uoc: int | None  # VND — dùng cho xếp hạng. None = chưa lượng hoá được
    han_nop: str | None
    giay_to: list[str] = field(default_factory=list)
    citation_chinh: Citation | None = None


@dataclass
class Profile:
    """6 field — chốt trong kho, lặp lại y nhau ở 3 file."""

    nganh: str | None = None
    von: int | None = None  # VND
    nhan_su: int | None = None
    chi_rnd: float | None = None  # % doanh thu
    dia_ban: str | None = None
    fdi: bool | None = None

    def thieu(self) -> list[str]:
        return [k for k, v in self.__dict__.items() if v is None]


@dataclass
class KetQuaDieuKien:
    dieu_kien: DieuKien
    trang_thai: TrangThai
    gia_tri_ho_so: Any
    giai_thich: str


@dataclass
class KetQuaKhop:
    chuong_trinh: ChuongTrinh
    chi_tiet: list[KetQuaDieuKien]
    diem_phu_hop: float  # P(phù hợp) 0..1
    gia_tri_ky_vong: float  # P × tác động
    du_dieu_kien: bool
    thieu: list[str]  # tên đích danh điều kiện chưa đạt — cho câu "thiếu Y"
    can_hoi_them: list[str]  # field hồ sơ còn trống

    @property
    def citations(self) -> list[Citation]:
        return [c.dieu_kien.citation for c in self.chi_tiet]
