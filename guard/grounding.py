"""enforce_grounding + citation binding — nối từ rail cũ, không nghĩ mới.

Hai luật của rail, đã chạy thật ở bản tập dượt:

1. **enforce_grounding** — câu gắn nhãn `grounded=true` thì BUỘC phải có ≥1 citation.
   Không có → ném ModelRetry → bắt model viết lại (tối đa 2 lần). Model không được
   phép vừa nói "có căn cứ" vừa không chỉ ra căn cứ ở đâu.

2. **citation binding** — citation phải RÀNG theo VẾT TRA CỨU THẬT:
   • LLM khai nguồn nó CHƯA HỀ tra   → LOẠI (đây là kiểu bịa tinh vi nhất:
     nội dung đúng, nguồn bịa — nhìn qua rất thuyết phục)
   • LLM quên khai nguồn đã tra thật → TỰ THÊM vào
   Nói cách khác: citation KHÔNG phải thứ LLM tự khai, mà là thứ hệ thống ghi lại.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ModelRetry(Exception):
    """Bắt model viết lại. Trùng tên với cơ chế của Pydantic AI trong rail cũ."""


@dataclass(frozen=True)
class NguonDaLay:
    """Một khoản THẬT SỰ được lấy khỏi corpus — do CODE ghi, không do LLM khai."""

    doc_id: str
    so_vb: str
    co_quan: str
    dieu: int
    khoan: int | None
    text: str

    @property
    def khoa(self) -> str:
        return f"{self.so_vb}|Đ{self.dieu}|K{self.khoan or '-'}"


@dataclass
class VetTraCuu:
    """Vết tra cứu của một lượt trả lời. CODE ghi mỗi lần chạm corpus."""

    da_lay: list[NguonDaLay] = field(default_factory=list)

    def ghi(self, n: NguonDaLay) -> None:
        if n.khoa not in {x.khoa for x in self.da_lay}:
            self.da_lay.append(n)

    @property
    def khoa_that(self) -> set[str]:
        return {n.khoa for n in self.da_lay}


@dataclass
class TraLoi:
    noi_dung: str
    grounded: bool
    citations: list[str] = field(default_factory=list)  # khoá dạng "80/2021/NĐ-CP|Đ5|K3"


@dataclass
class KetQuaRang:
    tra_loi: TraLoi
    da_loai: list[str] = field(default_factory=list)  # nguồn LLM bịa
    da_them: list[str] = field(default_factory=list)  # nguồn LLM quên


def enforce_grounding(tl: TraLoi) -> None:
    """grounded ⇒ phải có ≥1 citation. Không có → ModelRetry."""
    if tl.grounded and not tl.citations:
        raise ModelRetry(
            "Câu trả lời gắn nhãn có căn cứ nhưng không kèm trích dẫn nào. "
            "Hãy trích rõ điều–khoản làm căn cứ, hoặc đổi sang 'chưa đủ căn cứ'."
        )


def rang_citation(tl: TraLoi, vet: VetTraCuu) -> KetQuaRang:
    """Ràng citation theo vết tra cứu thật: loại nguồn bịa, thêm nguồn quên."""
    that = vet.khoa_that
    khai = list(dict.fromkeys(tl.citations))

    giu = [c for c in khai if c in that]
    loai = [c for c in khai if c not in that]
    them = [k for k in that if k not in khai]

    tl2 = TraLoi(noi_dung=tl.noi_dung, grounded=tl.grounded, citations=giu + them)
    return KetQuaRang(tl2, da_loai=loai, da_them=them)


def kiem_tra_tra_loi(tl: TraLoi, vet: VetTraCuu) -> KetQuaRang:
    """Chạy đủ 2 luật. Ném ModelRetry nếu sau khi ràng vẫn không còn căn cứ nào.

    ── THỨ TỰ: ràng TRƯỚC, enforce SAU. Đây là quyết định thiết kế, không tuỳ tiện:

    Nếu enforce TRƯỚC thì câu 'grounded + citation toàn đồ bịa' sẽ LỌT — nó có
    citation nên qua được enforce, dù citation đó là ma. Ràng trước thì citation
    ma bị loại sạch → còn 0 → enforce mới nổ đúng.

    ── HỆ QUẢ (cố ý): citation cuối cùng = VẾT TRA CỨU, không phải lời LLM khai.
    LLM nói có-căn-cứ mà quên trích, nhưng hệ thống CÓ tra thật → tự gắn nguồn
    thật vào, không bắt viết lại. Vì nguồn là thứ CODE ghi lại được, không phải
    thứ phải tin LLM.
    Lời khai của LLM chỉ dùng để PHÁT HIỆN ý đồ bịa nguồn (xem `da_loai`).
    → enforce_grounding chỉ nổ khi nói có-căn-cứ mà VẾT RỖNG.
    """
    kq = rang_citation(tl, vet)
    enforce_grounding(kq.tra_loi)
    return kq
