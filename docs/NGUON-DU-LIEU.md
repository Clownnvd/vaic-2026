# Nguồn dữ liệu & ghi công

> Lập theo **Điều 2** luật thi: *"Không sao chép, sử dụng trái phép hoặc đạo nhái sản phẩm,
> mã nguồn, dữ liệu hoặc ý tưởng của đội khác hoặc bên thứ ba khi chưa được phép **hoặc
> không trích dẫn phù hợp**"*.
>
> Đọc ngược: dùng được, **miễn là license cho phép VÀ ghi công đàng hoàng**. File này là phần ghi công.

---

## 1. Kho văn bản pháp luật — `tmquan/vbpl-vn`

| | |
|---|---|
| **Nguồn** | HuggingFace `tmquan/vbpl-vn` |
| **Dữ liệu gốc** | **vbpl.vn — Cơ sở dữ liệu quốc gia về văn bản pháp luật, Bộ Tư pháp** |
| **License** | **CC-BY-4.0** |
| **Quy mô** | 158.822 văn bản (147.317 có toàn văn markdown) |
| **Dùng vào** | corpus tra cứu + đối chiếu điều kiện + sinh dữ liệu huấn luyện guard |

**CC-BY-4.0 nghĩa là gì:** dùng được cho mọi mục đích kể cả thương mại, **nhưng BẮT BUỘC ghi công**.
Chữ **BY** chính là *"by attribution"*. Không ghi công = vi phạm license = vi phạm Điều 2 luật thi.

Ghi công phải xuất hiện ở: **README repo · slide · mô tả sản phẩm · trang web sản phẩm**.

**Câu ghi công chuẩn:**
> Dữ liệu văn bản pháp luật lấy từ bộ `tmquan/vbpl-vn` (HuggingFace), nguồn gốc từ
> **vbpl.vn — Cơ sở dữ liệu quốc gia về văn bản pháp luật (Bộ Tư pháp)**. License CC-BY-4.0.

### Phần đã xử lý lại (khai minh bạch)
Đội **không** dùng nguyên dump. Đã xử lý:
- Lọc còn **9.436 văn bản** (chạm 8 từ khoá chính sách ∧ 5 loại văn bản ∧ năm ≥ 2018)
- **Tự viết parser Điều → Khoản → Điểm** — vì `structure_json` của dump **không có** cấu trúc pháp lý (chỉ có sections/paragraphs; đã kiểm: 1 doc = 1 section "header")
- Lọc theo chủ đề doanh nghiệp → **2.669 văn bản**
- Lọc theo **Điều 6** (xem mục 3)

---

## 2. Biểu mẫu hồ sơ

| | |
|---|---|
| **Nguồn** | Rà soát nội bộ 33 biểu mẫu + verify hiệu lực 2026 (17/07/2026) |
| **Căn cứ** | TT 44/2025/TT-BKHCN · NĐ 80/2021/NĐ-CP · TT 06/2022/TT-BKHĐT · TT 80/2021/TT-BTC |
| **Trạng thái** | Chỉ giữ mẫu có văn bản căn cứ **NẰM TRONG corpus** (kiểm bằng `scripts/check_vb_moi2.py`) |

**Đã loại chủ động** vì căn cứ ngoài corpus → không trích được → không hứa:
- Ưu đãi đầu tư A.I.1–A.I.4 (cần Luật Đầu tư 143/2025/QH15 — dump không có)
- DN CNC B1/B2-DNTLM (cần TT 38/2026/TT-BKHCN — dump không có)

---

## 3. Điều 6 — rà nội dung nhạy cảm

> *"Đội thi có trách nhiệm kiểm tra kỹ nội dung, dữ liệu... bảo đảm không chứa nội dung sai lệch
> hoặc không phù hợp liên quan đến **chính trị, biên giới, lãnh thổ, chủ quyền quốc gia và biển đảo**"*

**Đã rà toàn bộ 9.436 văn bản** (`scripts/kiem_dieu6.py`), bám **đúng 5 phạm vi điều 6 nêu**, không tự nới:

| Kết quả | |
|---|---|
| Văn bản chạm phạm vi điều 6 trong tiêu đề | 28 / 9.436 |
| Lọt vào subset matcher dùng | **1** |
| **Đã chủ động loại** | `16/2021/NQ-HĐND` — *Chương trình phát triển bền vững kinh tế biển* |

Văn bản này lọt vào vì đúng chủ đề kinh tế, nhưng **không liên quan ưu đãi doanh nghiệp**
→ loại đi **mất 0 giá trị nghiệp vụ**.

> ⚠️ **Ghi nhận một lỗi đã sửa:** bản lọc đầu tiên tự thêm `quốc phòng` + `an ninh quốc gia` —
> hai từ **điều 6 không hề nhắc**. Hậu quả: loại nhầm **27** văn bản, phần lớn là báo cáo
> kinh tế - xã hội thường kỳ của HĐND tỉnh (cụm *"kinh tế - xã hội, quốc phòng - an ninh"*
> là công thức tiêu đề chuẩn). Đã siết đúng chữ điều 6 → **27 → 1**.
> Bài học: *"kiểm tra kỹ" ≠ "chặn tất"* — chặn bừa mất giá trị thật mà không được gì.

### Vì sao rủi ro điều 6 ở mức thấp — do kiến trúc, không do may
Hệ thống **không diễn giải lại** văn bản nhà nước, nó **trích dẫn**:
- **structure-then-fill** — AI không được gõ số; code chép **nguyên văn** từ nguồn
- **citation ràng theo nguồn** — mọi khẳng định trỏ về điều–khoản gốc, bấm ra xem được
- **refuse-when-ungrounded** — thiếu căn cứ thì nói *"chưa đủ căn cứ"*, không đoán

Muốn làm sai lệch nội dung thì phải diễn giải. Hệ thống không có đường để diễn giải.

---

## 4. Thư viện & mô hình

| Thứ | License | Ghi chú |
|---|---|---|
| `vinai/phobert-base` | **MIT** | ⛔ **KHÔNG dùng `phobert-base-v2` — AGPL** |
| `underthesea` | GNU GPL-3.0 | tách từ; dùng để né VnCoreNLP (cần Java) |
| PyTorch · transformers · pyarrow · FastAPI · Next.js | BSD / Apache-2.0 / MIT | |

⛔ **Không publish weights/checkpoint** lên GitHub (đã `.gitignore`).

---

## 5. Dataset ngoài — đang cân nhắc, CHƯA dùng

**ViHallu (UIT DSC 2025)** — bộ phát hiện hallucination tiếng Việt, 10.000 mẫu,
label `{no, intrinsic, extrinsic}`, **SOTA 84,80% macro-F1**.

Vì sao đáng quan tâm: guard hiện đo trên **dữ liệu tự sinh** — tự viết máy sinh câu bịa
rồi tự viết rule bắt → **vòng tròn**. ViHallu là thước đo **bên ngoài**, có SOTA công bố
→ số mới có sức nặng với giám khảo.

**⚠️ CHƯA DÙNG, vì hai chỗ chưa thông:**
1. **Không tìm được link tải công khai** (đã tra HuggingFace, GitHub, Codabench)
2. **License chưa xác minh** — text paper ghi CC-BY-SA 4.0, nhưng chuỗi `by-nc-sa/4.0`
   trong PDF là license **arXiv gắn cho BÀI BÁO**, không phải cho dataset. Hai thứ khác nhau.

→ Phải **email nhóm tác giả UIT xin link + xác nhận license bằng văn bản** trước khi đụng.
Chưa có xác nhận thì **không dùng, không nhắc trên slide**.

> ⚠️ **Cảnh báo trùng tên:** `github.com/oliviadzy/ViHallu` là **Vi**sual hallucination
> (dataset ảnh, ACM MM25) — **không liên quan**. Đừng tải nhầm.
