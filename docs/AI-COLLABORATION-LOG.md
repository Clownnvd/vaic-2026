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

### ~15:4x — Chạy 4 đòn bản CPU nhẹ: KẾT QUẢ XẤU, và đó là thông tin quý

Chạy đúng thứ tự kế hoạch (bản nhẹ trước, verify pipeline rồi mới lên GPU). Số ra:

```
Mining:  55.8% → 24.8% → 35.9% → 73.2%   ← dao động rồi TỆ HƠN
F1 = 0.353 · bắt bịa = 0.268 · ngưỡng refuse @97%: KHÔNG ĐẠT
Ablation: bỏ mining lại TỐT HƠN (0.442 vs 0.268)
```

Bắt bịa theo trục: bịa-điều-kiện **1.000** 🚩 · còn lại **0.03–0.20**.

**Con số 1.000 kia là GIẢ.** Nhiễu ngữ nghĩa chỉ có **3 template cố định** → model học thuộc câu chữ, không học grounding. Đúng thứ kho cảnh báo: *"F1=1.00 = data synthetic quá dễ, đừng khoe"*. **Không đưa số này lên slide.**

**Chẩn đoán (giá trị nhất phiên này):** model char n-gram **về nguyên lý không thể** bắt `50%→80%` — feature là túi n-gram, đổi một con số thì độ trùng gần như không đổi. Không phải model kém, mà **giao sai việc**.

→ **6/7 trục thuộc lớp TẤT ĐỊNH, chỉ 1 trục cần model.** Mình đã bắt model gánh cả 7.

### 🐛 Bug mining tự tìm ra khi đọc lại code
```python
cur = can_bang(cur + them, rng)   # them = 400 hard-negative vừa đào
```
`can_bang()` thấy neg>pos → **sample ngẫu nhiên neg xuống** → **vứt gần hết hard-negative vừa đào**. Đào xong ném đi → đường cong dao động. Chưa sửa (ghi nợ).

### ~15:5x — Wire lớp tất định → KIẾN TRÚC ĐƯỢC XÁC NHẬN

Viết `guard/lookup.py` (index corpus, **khoá = doc_number + issuing_authority**) + `guard/check.py` (3 tầng).

| Trục | model n-gram | **tất định** |
|---|---|---|
| bịa cơ quan | 0.180 | **1.000** |
| bịa số văn bản | 0.043 | **1.000** |
| sai hạn ngày | 0.043 | **1.000** |
| sai ngưỡng tiền | 0.199 | **0.993** |
| bịa điều/khoản | 0.031 | **0.967** |
| sai mức % | 0.040 | **0.937** |

**6 trục tất định: 1.968/2.013 = 0,978 · báo động giả 0/528 = 0,000**

**Sửa thiết kế giữa chừng (đưa 0.627 → 0.967):** ban đầu đối chiếu số của claim với **premise mình sẵn có** → trích đúng nội dung nhưng gắn nhầm Điều/Khoản thì lọt. Sửa: đối chiếu với **text TẠI ĐÚNG VỊ TRÍ AI TRÍCH**. Câu hỏi đúng là *"cái nguồn ANH TRÍCH có nói vậy không?"*, không phải *"câu này có khớp đoạn tôi đang cầm không?"*.

Phán quyết giải trình được từng câu: *"Số '80%' không có trong 13/2018/NQ-HĐND Điều 3 Khoản 2"* — không phải model đoán.

### 15:42 — `81a8208` Tầng PHÒNG NGỪA: structure-then-fill
**Người chỉ đạo:** đọc kho thấy còn thiếu tầng mạnh nhất → *"structure-then-fill trước — rẻ nhất, chống tận gốc, và là câu đấm demo"*.

Đảo ngược cách nghĩ: thay vì *cho LLM viết số rồi đi kiểm*, **không cho nó chạm vào số**. LLM viết `hỗ trợ {{s2}}`, CODE chép verbatim `50%` từ nguồn. Cưỡng chế 2 chiều: LLM tự gõ `80%` → CHẶN; gọi `{{s99}}` (slot ma) → CHẶN.

Khác biệt với guard: guard là **bắt sau khi bịa**; cái này **không có gì để bắt**.

Cùng lượt: `enforce_grounding` + citation binding — nối từ rail cũ, khớp đúng PROMPT-PACK §4 (3 tầng bảo vệ).

**Test hỏng làm lộ quyết định thiết kế:** LLM nói "có căn cứ" nhưng không trích gì, mà vết tra cứu CÓ 2 nguồn — bắt viết lại hay tự gắn nguồn vào? Chốt theo tinh thần kho: **citation là thứ hệ thống ghi lại, không phải thứ LLM khai** → tự gắn nguồn thật; lời khai của LLM chỉ dùng để **phát hiện ý đồ bịa nguồn**. `enforce_grounding` chỉ nổ khi **vết rỗng**.
Và **ràng TRƯỚC, enforce SAU** — ngược lại thì câu "grounded + citation toàn đồ bịa" sẽ lọt (có citation, nhưng là citation ma). Có test riêng cho bẫy này.

### 15:47 — `40ea78b` Trả 2 món nợ
🐛 **Bug mining tự tìm ra khi đọc lại code:** `can_bang(cur + them)` → hàm cân thấy neg>pos nên **sample ngẫu nhiên neg xuống, vứt gần hết hard-negative vừa đào**. Đào xong ném đi.
→ Nên ablation báo *"bỏ mining lại tốt hơn"* — **đó là hệ quả của bug, không phải mining vô dụng.** Suýt kết luận sai về cả một đòn.

🚩 **Template ngữ nghĩa:** 3 câu cố định → model học thuộc chữ → ra bắt-bịa **1.000 GIẢ**. Sửa thành 4 kiểu × 5 cách mở = 20 biến thể.

### 15:51 — `669405b` Matcher chạy ngược
Cover ① và ② của đề. **Điều kiện CẤU TRÚC HOÁ, đối chiếu bằng CODE không phải LLM** — vì Khối demo 2 đòi nói *"chưa, vì thiếu **Y**"*, gọi tên đích danh; LLM tự do không ra được câu đó ổn định.

**② Monitoring không cần API:** kho nhắc *"join API vbpl.vn"* 5 lần nhưng **0 dòng endpoint** — chỗ mù thật, và kho chỉ *giả định* có API công khai, chưa ai mở thử. Nhưng chuỗi diff là `khoản đổi → DN nào vừa đủ/mất → cảnh báo`: **mắt 2–3 code được ngay** bằng cách chạy matcher 2 lần trên 2 snapshot rồi lấy hiệu.

**Thiếu tin ≠ không đạt:** chưa khai field → HỎI, không kết luận loại. Kết luận "không đủ điều kiện" khi chưa hỏi xong **cũng là một dạng bịa**.

### 15:58 → 16:01 — `61cb8c4` `d7a5eaa` Ràng buộc J + I2
**Người hỏi:** *"cái J đã làm chưa"* → chưa. Dựng cổng LLM.

**Dựng cổng TRƯỚC call LLM đầu tiên** — hệ thống lúc này chưa có call nào (corpus/guard/matcher tất định hết) nên `goi_llm()` là cửa **duy nhất**, không có đường lách. Dựng sau là chắc chắn sót chỗ gọi thẳng.

**Người chỉnh:** *"dùng gpt-4o, fallback mấy con khác kém lắm"* → đúng, và mình **đã cấu hình sai so với kho**: để `gpt-4o-mini` cho task-fast trong khi BATTLE-NOTES đo thật `FAST_MODEL=openai:gpt-4o` và ghi *"mini ĐỒNG BÓNG — lúc thrash 6 tool/27s, lúc bịa ngày"*. Sửa cả 2 đường về gpt-4o.
**Nhưng cãi lại 1 điểm:** fallback không phải để thay chất lượng mà để **không chết khi primary sập** — I2 là ràng buộc đề, bỏ là vi phạm. Và fallback **phải khác provider**: bản đầu mình để `task-deep → task-fast`, cả hai đều OpenAI → OpenAI sập là chết cả hai → không thoả I2.

### 16:03 — `6e00566` H1 + H2
Áp công thức `VN-CONTEXT.md` sang domain chính sách. **PII bài này khác bài ngân hàng:** hồ sơ là **doanh nghiệp** → khoá định danh là **mã số thuế**, không phải số tài khoản; nhưng **người đại diện** vẫn là cá nhân → CCCD/SĐT/email phải mask.
**Thứ tự mask:** cccd(12) → mst(10) → cmnd(9) — regex ngắn chạy trước sẽ ăn nhầm số dài hơn.

### 16:12 — `41d0405` Nối BFF
**2 lỗi tự bắt:**
1. **Cổng 8000 bị BFF CŨ của `vaic-rehearsal` chiếm** (chạy từ 16/07 02:32 — 37h trước). `/health` trả `{"model":"openai:gpt-4o"}` thay vì service của mình. **Nếu không đọc kỹ response mà báo "BFF lên rồi ✓" thì đã verify NHẦM service** — mọi test sau đó vô nghĩa. Không tự giết (process không phải của mình tạo) → hỏi người dùng, được phép mới dọn.
2. **Import file test để lấy data**: `from matcher.test_match import KHO` → import = chạy test + `sys.exit()` → **server chết ngay lúc boot**. Tách sang `matcher/kho_mau.py`.

smoke 13/13 qua HTTP thật. Latency **0ms** — toàn tất định, chưa có LLM.

### 16:2x — Sửa BFF về đúng schema `AgentReply`
BFF đang trả shape tự chế → sửa theo PROMPT-PACK §5: `text · citations · next_actions · grounded · requires_approval`.

### ⚠️ Tự khai: log này bị bỏ bê một đoạn
Từ ~15:5x đến 16:2x mình **làm 6 việc mà không ghi log**, người dùng hỏi mới nhớ. Kho ghi rõ *"ghi log TRỰC TIẾP trong lúc thi, timestamp khớp git log"* — ghi bù sau là đúng thứ giám khảo ngửi ra. Các mốc trên khớp `git log` thật (đối chiếu được), nhưng phần diễn giải là viết bù. **Ghi ra để trung thực, không giấu.**

---

## 17/07 (chiều–tối) — Data thật, GPU H100, UI hoàn chỉnh

### Soi data trước khi đốt GPU — bắt 2 lỗi tự bắn vào chân
Viết `guard/soi_data.py` (7 phép soi) chạy TRƯỚC khi train. Bắt được:
- **Rò rỉ premise**: 9 đoạn nguồn nằm ở cả train lẫn test dù `doc_id` đã tách (điều khoản mẫu "Thông tư này có hiệu lực…" lặp nguyên văn ở nhiều văn bản → tách theo doc_id không bắt được). Gỡ 166 cặp khỏi train, KHÔNG đụng test.
- **Cân nhãn 17/83** — NGƯỢC với đời (LLM phần lớn nói đúng). Gốc: `sinh_cap` lấy đúng 1 câu làm positive rồi vứt phần còn lại, vẫn đẻ ~5 negative. Sửa: lấy nốt các câu thật còn lại → **50/50**. Hệ quả đo được: smoke báo động giả **0,579 → 0,000** sau khi cân.

### `kho_mau.py` đang BỊA LUẬT — moi nguyên văn corpus mới lộ
Đối chiếu 80/2021/NĐ-CP và 13/2019/NĐ-CP thật:
- "Tối thiểu 30 nhân sự", "Chi R&D ≥ 1%" — **bịa trắng**, không có trong văn bản.
- `480 triệu` — Điều 13 K2 trần cao nhất chỉ **200 triệu**.
- "Nhân sự ≤ 200" — thực ra **200 với CN-XD nhưng 100 với thương mại-dịch vụ**; và doanh thu **HOẶC** vốn (kho_mau biến thành VÀ).
Viết lại toàn chuỗi `quy_mo.py`→`schema`→`match`→`bff`→`frontend`→`ho_so`, mọi citation chép nguyên văn 273–895 ký tự trỏ `doc_id` corpus. 12/12 test quy mô + toàn bộ test khác pass.

### Đào bịa THẬT của GPT-4o — phá vòng tròn tự-sinh-tự-chấm
`dao_bia_that.py`: GPT-4o SINH câu từ điều luật thật, lớp tất định (độc lập) chấm. Kết quả sau khi sửa parser: **95% GPT-4o trung thực, 5% bịa thật** (bịa số "03-05 ngày", trích "Điều 25" khi văn bản chỉ có Điều 1–19). Lớp tất định bắt **7/7** ca bịa số/định danh. Nói thẳng giới hạn: rule MÙ ngữ nghĩa nên 5% chỉ là bịa số/định danh, không phải toàn phần.

### GPU H100 trên FPT — điều khiển bằng CDP, né 3 bug CUDA
Lái Chrome bằng Chrome DevTools Protocol → FPT AI Factory → JupyterHub. Phát hiện: **lab notebook miễn phí bị cap `memory.max = 1GB`** (128 core/2TB là của host) → PhoBERT bị Killed ngay. Tạo **GPU Container H100 (250GB RAM)** với template Jupyter — **né cả 3 bug CUDA kho dính lần trước** (VM+SSH tự cài torch): driver CUDA 12.4 → cài `torch cu124` khớp, không `--no-deps`. Train **130s trên cuda**: báo động giả **0,000**, 4 trục ngữ nghĩa **1,000** (rule mù = 0,000 → PhoBERT load-bearing). Tải checkpoint 450MB về, verify nạp được (P(grounded)=0,999), **XÓA container** — tổng tốn **14.962 ₫** (kho lần trước ~12k, cùng cỡ).

### vbpl.vn cắm thật vào UI
Hâm cache hiệu lực 2 văn bản flagship → cả hai **CHL (Còn hiệu lực)**. Badge "⚠ Hiệu lực chưa đối chiếu" → **"✓ Còn hiệu lực — đối chiếu vbpl.vn"**. Đọc cache-only ở BFF nên không bao giờ làm đơ /chat.

### Sidebar + trình duyệt luật + 2 bug UX người dùng bắt
Sidebar 3 mục kiểu Claude (Chat · Danh sách luật · Lịch sử), trình duyệt **2.669 văn bản** có tìm kiếm + lọc facets + phân trang. Người dùng bắt 2 bug thật:
- **Bóc hồ sơ không dấu bị trượt**: "von 20 ty", "cong nghiep", "lao dong" không khớp (regex có dấu) → bot hỏi lại thứ vừa khai → cảm giác "không đồng nhất". Sửa: `bocHoSo` bỏ dấu trước khi khớp (H1). Ribbon 3/10 → **8/10**.
- **Không hiểu context**: hồ sơ đầy từ lượt trước → "bạn năm nay bao tuổi" cũng re-run matcher → trả kết quả đủ điều kiện. Thêm `cau_meta_lac_de` phát hiện câu meta/chào/tán gẫu → chuyển hướng, không đoán.

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

## Đếm chiều ngược (ai bác ai)

> Metric đáng kể không phải "AI viết bao nhiêu %", mà là **bác nhau mấy lần và vì sao**.

| # | Ai bác | Bác cái gì | Vì sao |
|---|---|---|---|
| 1 | AI ↔ AI | `globals.css` dark mode | CSS không hợp lệ, tự bắt khi đọc lại |
| 2 | AI ↔ scaffold | font Geist mặc định | thiếu subset tiếng Việt → chữ có dấu rớt font |
| 3 | AI ↔ AI | bịa trích dẫn cho seed | tự mâu thuẫn với chính sản phẩm |
| 4 | AI ↔ **kho** | *"đã parse sẵn điều→khoản→điểm"* | đo dump thật: **KHÔNG có** |
| 5 | AI ↔ **AI** | kết luận *"corpus không có Điều (0%)"* | regex neo `^` sai — markdown làm phẳng. Kiểm lại: **499/500** |
| 6 | AI ↔ AI | phép đo max_len bằng ước lượng | *"3 ký tự/token"* + đo sai đơn vị → đo lại bằng tokenizer thật: **25,9%** chứ không phải 20,2% |
| 7 | **Người** ↔ AI | *"vừa đầy đủ vừa chuẩn xác"* | ép bỏ ước lượng, đo thật → suýt chốt nhầm `max_len=128` |
| 8 | AI ↔ AI | kiến trúc guard | bắt model gánh 7 trục → nó **về nguyên lý** chỉ làm được 1 |
| 9 | AI ↔ AI | ablation *"bỏ mining tốt hơn"* | là **hệ quả của bug** vứt hard-negative, không phải mining vô dụng |
| 10 | AI ↔ AI | con `1.000` ở trục ngữ nghĩa | **số GIẢ** — model học thuộc 3 template |
| 11 | **Người** ↔ AI | *"fallback mấy con kia kém lắm"* | đúng phần model chính (gpt-4o), **nhưng AI cãi lại**: fallback là để không chết khi primary sập — I2 là ràng buộc đề |
| 12 | AI ↔ **AI** | fallback `task-deep → task-fast` | cả hai đều OpenAI → sập là chết cả hai → **không thoả I2** |
| 13 | AI ↔ AI | *"BFF lên rồi"* | đọc kỹ response: **đó là BFF CŨ**, suýt verify nhầm service |
| 14 | **Người** ↔ AI | *"nãy giờ có ghi log AI không"* | log bị bỏ bê 6 việc — bắt đúng |
| 15 | AI ↔ **AI** | `dao_bia_that` bản 1: *"GPT-4o bịa 66%"* | đọc câu thật: nó **TỪ CHỐI** 120/120, không bịa. Câu hỏi lệch khỏi nguồn. Sửa prompt → 95% trung thực |
| 16 | AI ↔ **AI** | *"66% chưa đủ căn cứ"* (bản 2) | là **bug parser** `boc_citation` (bỏ lọt "Nghị định", Điều-trước-Khoản) — không phải GPT bịa. Guard không đọc nổi citation của chính mình → chặn oan trên production |
| 17 | AI ↔ **kho** | định dùng GPU VM+SSH như lần trước | kho ghi VM dính **3 bug CUDA**. Chọn Container+Jupyter → né cả 3 |
| 18 | AI ↔ **máy** | *"128 core 2TB RAM"* của lab free | cgroup thật **1GB** → PhoBERT Killed. Host ≠ pod |
| 19 | **Người** ↔ AI | *"vốn chưa bắt được kìa"* | bóc hồ sơ không xử gõ-không-dấu → vi phạm H1 chính mình đặt ra |
| 20 | **Người** ↔ AI | *"bạn năm nay bao tuổi"* → ra kết quả | bot không hiểu context — hồ sơ đầy thì câu nào cũng chạy matcher |
| 21 | **Người** ↔ AI | *"nho in ('sieu_nho','nho','vua')"* | in biểu thức Python thô lên UI cho người dùng đọc |
