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

## 5. ViFactCheck — thước đo NGOÀI (đã tải, dùng ZERO-SHOT)

| | |
|---|---|
| **Nguồn** | HuggingFace `tranthaihoa/vifactcheck` · arXiv:**2412.15308** (AAAI 2025) |
| **License** | **MIT** — theo tag trên dataset card. ⚠️ repo **không có file LICENSE riêng** để đối chiếu |
| **Quy mô** | **7.232 cặp claim–evidence, NGƯỜI GÁN NHÃN** · 9 báo VN · 12 chủ đề |
| **Nhãn** | Supported / Refuted / NEI |
| **SOTA** | Gemma macro-F1 **89,90%** (AAAI 2025) |

**Ghi công (điều 2 — bắt buộc dù license MIT):**
> ViFactCheck: A Multi-Domain Vietnamese News Fact-Checking Benchmark.
> arXiv:2412.15308 (AAAI 2025). HuggingFace: `tranthaihoa/vifactcheck`. License MIT.

### Vì sao cần bộ này
Guard đang đo trên **dữ liệu tự sinh** — đội viết máy sinh câu bịa, rồi cũng chính đội
viết rule bắt. **Vòng tròn**: tự ra đề, tự chấm. ViFactCheck là bộ **người khác làm,
người thật gán nhãn, có SOTA công bố** → phá được vòng tròn đó.

### ⚠️ NHƯNG KHÔNG KHỚP DOMAIN — đã đo, không đoán
```
chạm văn bản luật : 477/1.447 = 33%
chạm điều 6       : 99/1.447 = 6,8%   → đã lọc bỏ
chủ đề            : THỂ THAO · HOA HẬU · GIỚI TRẺ · Chính trị · Kinh doanh
```
Đây là **TIN TỨC BÁO CHÍ**, không phải văn bản pháp luật.

**Quy tắc dùng — chốt cứng:**
- ⛔ **KHÔNG train** trên bộ này. Sai domain; train xong khoe *"guard bắt bịa điều luật tốt"* là **nguỵ biện**.
- ✅ **Chỉ zero-shot**, báo **2 con số tách bạch**: toàn bộ tin tức · riêng nhóm chạm văn bản luật.

**Phát biểu phải chính xác từng chữ:**

| | |
|---|---|
| ✅ **Nói được** | *"Guard train trên **luật**, đem sang **tin tức** chưa hề thấy, zero-shot vẫn đạt X → model học **cách đối chiếu claim với nguồn**, không học thuộc từ khoá luật."* → claim về **TỔNG QUÁT HOÁ** |
| ❌ **Không được nói** | *"Guard đạt X trên bài toán bịa điều luật."* → ViFactCheck **không đo cái đó** |

⚠️ **So trực tiếp với SOTA 89,90% là không công bằng cho cả hai phía:** SOTA **có train**
trên bộ này + đo **macro-F1 3 lớp**; guard mình **zero-shot** + gộp 2 lớp. Lên slide phải
ghi rõ hai điều kiện khác nhau.

### Đã LOẠI: ViWikiFC
Agent nghiên cứu xếp `NghiemAbe/ViWikiFC` số 1. **Tự verify thì loại:**
- README trả **HTTP 401 Unauthorized** → repo khoá, **không tải được**
- **19 lượt tải/tháng · 1 like** — vô lý cho một "SOTA benchmark của UIT"
- Tác giả HF `NghiemAbe` **không khớp** tác giả paper (Hung Tuan Le, Long Truong To, Manh Trong Nguyen, Kiet Van Nguyen) → nghi **mirror không chính thức**

Dùng mirror rồi khai *"bộ của UIT"* = **sai nguồn** = vi phạm điều 2.

---

## 6. Dataset ngoài — ĐÚNG DOMAIN, phải xin (chưa có)

ViFactCheck (mục 5) phá được vòng tròn nhưng **sai domain** (tin tức). Ba bộ dưới đây
**đúng domain luật VN** — đáng giá hơn hẳn, nhưng đều phải **email xin**. Nên gửi mail SỚM,
học thuật trả lời chậm.

| Bộ | Vì sao đáng | Vướng gì |
|---|---|---|
| **ViLegalNLI** | 42.012 cặp premise–hypothesis, **thuần văn bản quy phạm pháp luật VN**, nhãn Entailment/Non-entailment. SOTA: Qwen2.5 few-shot **90,72%**, CafeBERT **87,49%** | Paper ghi *"Dataset link will be updated upon paper acceptance"* → **chưa phát hành**. Vênh số nặng: paper 42.012 cặp vs GitHub 9.600+. ⚠️ Bộ này **cũng sinh bằng LLM** (Gemini-2.5 Flash) → **không thoát hoàn toàn vòng tròn** |
| **VLSP 2023 – LTER** | **Khớp 1-1** với đề: `{statement, legal_passages[{law_id, article_id}], label: Yes\|No}`. `label:"No"` **chính là câu bịa** — map thẳng, khỏi convert | Cổng đăng ký **đóng từ 31/08/2023**, data phát qua Google Form. License chưa xác định → email BTC VLSP |
| **ALQAC** | **Chuyên gia luật gán nhãn TAY** — bằng chứng **mạnh nhất** (khác ViLegalNLI máy sinh) | Không có link tải công khai. ⚠️ ALQAC 2026 **đã đổi đề** hoàn toàn |

### ViHallu (UIT DSC 2025) — đã tra, KHÔNG dùng được
10.000 mẫu, label `{no, intrinsic, extrinsic}`, SOTA **84,80% macro-F1**. Cấu trúc rất hợp
(intrinsic = xuyên tạc điều luật có thật; extrinsic = bịa hẳn điều không tồn tại).

**Kẹt 2 chỗ:**
1. **Không tìm được link tải công khai** (đã tra HuggingFace, GitHub, Codabench)
2. **License nhập nhằng** — text paper ghi CC-BY-SA 4.0, nhưng chuỗi `by-nc-sa/4.0` trong
   PDF là license **arXiv gắn cho BÀI BÁO**, không phải dataset. **Hai thứ khác nhau.**

> ⚠️ **Trùng tên nguy hiểm:** `github.com/oliviadzy/ViHallu` là **Vi**sual hallucination
> (dataset ảnh, ACM MM25) — **không liên quan gì**. Rất dễ tải nhầm.

### 🔴 Bẫy license lặp lại 3 lần — ghi ra để không mắc nữa
**Icon/chuỗi Creative Commons trên trang arXiv là license của BÀI BÁO, KHÔNG phải của dataset.**
Đã suýt mắc với: ViHallu · ViANLI · ViLegalNLI. `by-nc-sa` trên arXiv **≠** dataset là NC-SA.
Chỉ tin **file LICENSE trong repo** hoặc **license tag trên dataset card** — và ghi rõ mình
đang tin nguồn nào.

### Ghi chú license các bộ NLI tiếng Việt
**Không bộ nào cho dùng thương mại.** XNLI = CC BY-**NC** 4.0 (theo repo GitHub gốc; ⚠️ card
HuggingFace **bỏ trống license** — hai nguồn vênh). ViNLI/ViANLI phải email xin, license
phụ thuộc thoả thuận riêng. Nếu cần dùng bộ NC → **hỏi BTC một câu**: *"bài dự thi có bị coi
là commercial use không?"*
