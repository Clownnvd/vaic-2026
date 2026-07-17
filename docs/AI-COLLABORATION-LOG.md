# Nhật ký hợp tác với AI — PolicyRadar

> VAIC 2026 · đội build 17–19/07/2026. Ghi trực tiếp trong lúc thi, timestamp khớp `git log`.
>
> Công cụ: **Claude Code (Opus 4.8)**. Vai trò: người quyết định hướng + duyệt/bác đề xuất; AI viết code và tra cứu.
> Log này ghi cả lúc AI **sai** và ai bắt được — đó mới là thứ chứng minh có người thật trong vòng lặp.

---

## Mốc 0 — Chuẩn bị trước ngày thi (hợp lệ, không có code)

Trước 17/07 đội chuẩn bị **tài liệu markdown**: nghiên cứu đề, chiến lược, kiến trúc bằng chữ, bài học từ các bản tập dượt. Theo luật BTC, được mang boilerplate rỗng + markdown + mockup + seed data; **toàn bộ code logic viết trong 48h**.

Repo này bắt đầu từ **commit đầu tiên lúc 14:00 ngày 17/07**, sau khi đề công bố lúc 11:00. Không có dòng code nào chuyển từ nơi khác sang.

---

## 17/07

### 14:00 — `5cfa4d8` khởi tạo repo
**Người:** chốt đề **P1 — Policy & Grant Navigator (NIC)** ngay khi menu đề mở, sau khi đã chấm bảng tiêu chí từ trước.
**AI:** dựng README + `.gitignore` (chặn sẵn weights/data/`.env` theo ràng buộc không publish model & dữ liệu).

### ~14:0x — Kiểm tra môi trường, AI phát hiện 2 rủi ro
**AI báo:**
1. Máy đang dùng **pnpm 10.33**. pnpm ≥10 chặn build script của dependency → `sharp` fail → build đỏ khi deploy. → hạ **pnpm 9.15.9**.
2. **Python 3.14.4** quá mới, nhiều khả năng chưa có wheel cho torch/transformers → sẽ chặn phần guard PhoBERT.
**Người:** duyệt hạ pnpm. Rủi ro Python ghi nợ, xử lý khi tới phần guard.
> Rủi ro #2 vẫn **đang mở** — chưa verify.

### ~14:1x — Scaffold frontend
Next.js **16.2.2** + React **19.2.4** + Tailwind **v4** + TypeScript, App Router.

**AI tự bắt lỗi của chính mình (1):** viết `globals.css` gộp `:root[data-theme="dark"]` với `@media` trong cùng một danh sách selector — **CSS không hợp lệ**, dark mode sẽ chết câm. Tự phát hiện ngay khi đọc lại và tách thành 2 khối. Không ai phải chỉ ra.

**AI bác lựa chọn mặc định của scaffold (2):** `create-next-app` gắn font **Geist** với `subsets: ["latin"]` — **không có subset tiếng Việt**. Cả sản phẩm là tiếng Việt, các chữ có dấu (ă, ơ, ư, đ) sẽ rớt sang font hệ thống → chữ lệch nhau trong cùng một dòng. Đổi sang **Be Vietnam Pro** (`subsets: ["latin", "vietnamese"]`). Đây là lỗi chức năng, không phải thẩm mỹ.

### ~14:2x — Quyết định về seed data (quan trọng nhất tới giờ)
Khi dựng `lib/seed.ts`, AI cần dữ liệu chương trình ưu đãi để render giao diện.

**AI từ chối bịa trích dẫn.** Sản phẩm này tồn tại để chặn việc AI bịa số nghị định; nếu chính seed của mình bịa số điều–khoản thì:
- sai ngay về mặt sự thật, và
- sẽ vỡ trước giám khảo có chuyên môn LLM luật.

**Cách xử lý đã chốt:** seed chỉ dùng **tên chương trình và số hiệu văn bản có thật** (NĐ 13/2019, NĐ 80/2021, Luật Hỗ trợ DNNVV 04/2017/QH14, QĐ 844/QĐ-TTg, NĐ 76/2018); mọi đoạn `trichDan` để nguyên chuỗi `[PLACEHOLDER]` và bị UI **tự gắn cảnh báo vàng "chưa đối chiếu corpus"** khi mở ra. Số điều/khoản chỉ được coi là thật sau khi sinh từ corpus `tmquan/vbpl-vn`.

> Kỷ luật này chính là sản phẩm: **không tin số chưa verify, kể cả số của mình.**

### Giao diện — quyết định thiết kế
**Người chốt:** giao diện **chat-first**, nhưng là *matcher mặc áo chat* — AI **chủ động hỏi hồ sơ trước**, không ngồi đợi người dùng biết mà hỏi.
**Hệ quả bắt buộc (AI nhấn):** kết quả matcher phải render thành **thẻ xếp hạng có cấu trúc trong bong bóng chat**, tuyệt đối không trả đoạn văn xuôi — ra văn xuôi thì trông y hệt một chatbot phổ thông và mất luôn điểm khác biệt.

Đã dựng: `ProfileRibbon` (ngữ cảnh hồ sơ luôn hiện hình), `ProgramCard` (thẻ xếp hạng: giá trị kỳ vọng, hạn nộp, từng điều kiện kèm trạng thái đạt/chưa đạt **và citation riêng cho từng dòng**), `CitationChip` (bấm mở đoạn căn cứ), `ChatMessage` (badge *đủ căn cứ / chưa đủ căn cứ / guard chặn*).

### ~15:xx — Corpus: rủi ro Python đã thành hiện thực
Rủi ro ghi nợ lúc 14:0x nổ đúng như dự báo: **Python 3.14 không import được `pyarrow`**. Không mất giờ debug — chuyển sang `uv run --python 3.11` là chạy (pyarrow 25.0.0). Ghi lại để không ai thử lại đường 3.14.

### ~15:xx — Thăm dò schema TRƯỚC khi viết pipeline
Không đoán dtype. Tải 1 shard, in schema thật → bắt được **2 chỗ mà spec ban đầu đoán sai**:
- `doc_number` là `list<string>`, không phải string → thêm cột `doc_number_str` đã join.
- Có sẵn `item_id` + `source_url` → map thẳng vào `docId`/`url` của `Citation`. Thiếu 2 field này thì citation không truy ngược được — suýt bỏ sót.

### ~15:xx — Không tải 1.8GB: đọc footer parquet
Parquet lưu min/max từng cột trong footer. Đọc footer 32 shard qua HTTP range (**vài KB thay vì 1.8GB**) → **14 shard có `year_max < 2018` ⇒ chắc chắn 0 dòng lọt lọc ⇒ khỏi tải**. Tiết kiệm ~770MB.

Đây là suy luận từ **thống kê chính xác**, không phải ngoại suy mẫu. Và đã **chéo kiểm**: shard 24 đọc thật ra dải 1946–2015, footer cũng nói 1946–2015 → stats tin được.

Tổng rows từ footer = 31×5000 + 3822 = **158.822**, khớp *chính xác* con số đã biết của kho.

### ~15:xx — "0 khớp" trông như bug. Điều tra thay vì đoán.
Shard 03 báo có văn bản tới **2025** nhưng lọc ra **0 khớp**. Hai giả thuyết trái ngược, cả hai đều nguy hiểm nếu đoán bừa:
- "bộ lọc hỏng" → sửa nhầm cái đang đúng.
- "kho không có dữ liệu" → bỏ cả hướng.

**Đã làm:** dừng job tải (không để nó nuốt 18 shard rồi mới biết) → hỏi **HF datasets-server API** lấy số cứng → tải đúng shard 03, in phễu từng tầng.

**Kết quả:** shard 03 có đúng **1/5000** văn bản từ 2018. `year_max=2025` là **một văn bản lẻ duy nhất**. Mọi tầng lọc đều sống (doc_type 4.616 · keyword 816). **Bộ lọc đúng, dữ liệu chỉ lệch khủng khiếp.**

**Bài học ghi lại:** `year_max` chỉ chứng minh được chiều *"bỏ đi an toàn"*, không chứng minh *"có hàng"*. Đúng tinh thần: đừng suy từ mẫu.

### ~15:xx — Số cứng của corpus (verify qua API, không ngoại suy)
| Tầng | Số văn bản |
|---|---|
| Tổng kho | **158.822** |
| year ≥ 2018 | **48.007** |
| doc_type ∈ 4 loại | 77.907 |
| year≥2018 ∧ doc_type | 46.465 |
| ⭐ cả 3 tầng (corpus flagship) | **~7.598** |

⚠️ Số keyword từ API **thấp hơn** số kho (ưu đãi 6.366 vs 11.950) vì `LIKE` phân biệt hoa/thường. Pipeline dùng `utf8_lower` nên số thật cao hơn. **Ghi rõ chỗ vênh này thay vì chọn số đẹp hơn.**

### ~15:02 — Corpus flagship XONG
827 giây. **Tải 18/32 shard** (14 shard bị loại bằng footer, tiết kiệm ~770MB). Quét 90.000 văn bản → **9.299 khớp cả 3 tầng lọc** (10,3%). Parquet 153MB.

**Phép thử chéo:** đếm `ưu đãi` = 6.798 trong 90k đã quét. Nhân theo tỷ lệ lên 158.822 ≈ 12.000, gần khít con số 11.950 đã đếm độc lập từ trước → hai lần đếm khác nhau, khớp nhau.
⚠️ **Nhưng KHÔNG dùng phép nhân đó làm số báo cáo** — 14 shard bỏ qua toàn văn bản cũ nên phân bố không đều, ngoại suy không hợp lệ. Chỉ được nói: *"6.798 trong 90.000 văn bản đã quét"*.

### ~15:0x — Chia train/calib/test
| | văn bản | % |
|---|---|---|
| train | 7.484 | 80,5 |
| calib | 938 | 10,1 |
| test | 877 | 9,4 |

**Hai quyết định thiết kế:**
1. **Chia theo VĂN BẢN, không theo dòng.** Guard train trên cặp (điều-khoản, claim); một văn bản đẻ nhiều cặp. Chia theo cặp → cùng một nghị định nằm cả train lẫn test → model học thuộc văn bản → điểm ảo. Đây là bẫy riêng của domain luật. Đã viết `assert` kiểm thật: train∩calib = train∩test = calib∩test = ∅ ✓
2. **Có tập `calib` riêng.** Temperature scaling (đòn #3) phải fit trên dữ liệu không-train-không-test. Fit trên test rồi lấy test báo ECE = số gian.

**Băm bằng `md5(item_id)` chứ không dùng `hash()`** — `hash()` của Python bị salt ngẫu nhiên mỗi lần chạy → split đổi mỗi lần → không tái lập được.

Kiểm phân bố: doc_type và năm trung vị đồng đều cả 3 phía (nghị định 6,9/6,6/6,3% · median 2023) → test không lệch chủ đề.

### ~15:2x — 🔴 BA CÚ VỀ DATA (quan trọng nhất phiên này)

Kho chuẩn bị ghi: *"dataset đã parse sẵn document→điều→khoản→điểm + NER"*. **Kiểm trên dump thật thì KHÔNG ĐÚNG.**

**Cú 1 — `structure_json` vô dụng cho việc này.** Nó chỉ có `sections / paragraphs / sentences`, và `stats` ghi `num_sections=1, num_paragraphs=1` — tức **cả văn bản là MỘT section kind="header"**. Đây là parse tổng quát (meta còn có `court_level`, `precedent_number` — parser vốn cho án lệ), **không phải parse pháp lý**. Không có điều/khoản/điểm.

**Cú 2 — markdown bị LÀM PHẲNG.** 500/500 văn bản có **0 ký tự xuống dòng**. Mọi regex neo `^` đều chết câm.
→ Lần đo đầu ra "1/500 văn bản có Điều (0%)" — **suýt kết luận corpus không có cấu trúc**. Kiểm lại bỏ neo `^`: **499/500 văn bản, 13.668 lần "Điều N"**. Cấu trúc CÓ, chỉ là chưa ai parse. Nếu tin con số 0% đầu tiên thì đã bỏ cả hướng citation.

**Cú 3 — không có field hiệu lực** (đã xác nhận, xem nợ #5).

**Xử lý:** tự viết `corpus/parse_dieu.py`. Chỗ khó nhất là phân biệt `Điều 1.` (tiêu đề) với `tại Điều 5` (trích dẫn) — bắt nhầm thì cắt vụn văn bản, citation trỏ sai. Trị bằng: tiêu đề Điều luôn **đánh số tăng dần từ 1** → lấy dãy con tăng dần, chắc hơn đoán bằng từ đứng trước.

### ~15:3x — Đo max_len bằng tokenizer THẬT (sửa phép đo ẩu của chính mình)
Lần đo đầu mình **ước lượng "1 token ≈ 3 ký tự"** và đo trên **cả văn bản** (sai đơn vị) → ra 20,2% vượt 128. Người dùng ép "vừa đầy đủ vừa chuẩn xác" → đo lại bằng **tokenizer PhoBERT thật** trên **khoản thật**:

| p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| 72 | 132 | **261** | 390 | 946 | 10.616 |

**Vượt 128: 25,9%** · vượt 256: 10,3% → **CHỐT max_len = 256**.
Kho cảnh báo "'>20% truncate thì lên 256" — đo ra 25,9%, cảnh báo đúng. Tin số ước lượng (20,2%) thì đã suýt chốt nhầm 128.

**Sản lượng:** 24.564 đơn vị trích dẫn / 600 văn bản ≈ 41 khoản/văn bản → ~300k khoản từ 7.484 văn bản train. Đủ xa để train.

**Chất lượng parser — nói thẳng:** text khoản (dùng làm premise) đúng; nhưng **tiêu đề Điều đôi lúc nuốt nhầm số khoản** ("Phạm vi điều chỉnh 1") và có điều ra tiêu đề rỗng. Chưa chặn train → ghi nợ, không giấu.

---

## Nợ kỹ thuật đang mở

| # | Việc | Trạng thái |
|---|---|---|
| 1 | ~~Python 3.14 chạy được pyarrow?~~ | ✅ đóng — KHÔNG. Dùng `uv run --python 3.11` |
| 1b | Python 3.14 chạy được torch/transformers? | ❓ chưa verify — sẽ chặn guard |
| 2 | Thay seed bằng dữ liệu sinh từ corpus vbpl-vn | 🔴 bắt buộc trước demo |
| 3 | Join API vbpl.vn lấy trạng thái hiệu lực | 🔴 chưa làm |
| 4 | Wire frontend → BFF (hiện bóc hồ sơ bằng regex ở client) | 🔴 tạm |
| 5 | ~~Corpus có field hiệu lực không?~~ | ✅ đóng — **KHÔNG CÓ** → **phép nhiễu #7 BỊ LOẠI** |
| 6 | ~~Chốt `max_len`~~ | ✅ đóng — **256** (đo thật: 25,9% khoản vượt 128) |
| 7 | Parser: tiêu đề Điều nuốt nhầm số khoản, có điều tiêu đề rỗng | 🟡 chưa chặn train |
| 8 | 10,3% khoản vượt 256 token (trần PhoBERT) → cần cửa sổ trượt | 🟡 chưa làm |

---

## Đếm chiều ngược (người/AI bác đề xuất)

| Lần | Ai bác | Bác cái gì | Vì sao |
|---|---|---|---|
| 1 | AI ↔ AI | `globals.css` dark mode | CSS không hợp lệ, tự bắt khi đọc lại |
| 2 | AI ↔ scaffold | font Geist mặc định | thiếu subset tiếng Việt |
| 3 | AI ↔ AI | bịa trích dẫn cho seed | tự mâu thuẫn với chính sản phẩm |
