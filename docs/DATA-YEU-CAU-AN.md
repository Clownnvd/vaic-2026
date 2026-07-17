# Yêu cầu ẩn của data — `tmquan/vbpl-vn`

> Mọi thứ dưới đây **đo trên dump thật ngày 17/07**, không phải đọc doc.
> Nhiều mục **mâu thuẫn với tài liệu chuẩn bị** — tin tài liệu là hỏng.
> Ai đụng vào data này đọc file này trước.

---

## 0. Bốn cú lật gãy giả định ban đầu

| # | Tài liệu chuẩn bị nói | Dump thật |
|---|---|---|
| 1 | "đã parse sẵn document→điều→khoản→điểm" | ❌ `structure_json` **không có** điều/khoản/điểm |
| 2 | (không nhắc) | ❌ markdown **bị làm phẳng, 0 xuống dòng** |
| 3 | "trạng thái hiệu lực nằm trên vbpl.vn API" | ✅ đúng — dump **không có** field hiệu lực |
| 4 | (không nhắc) | ❌ `doc_number` **không duy nhất** |

---

## 1. `structure_json` KHÔNG dùng được cho cấu trúc pháp lý

```
khoá gốc : schema_version, doc_id, meta, stats, sections, paragraphs, sentences
stats    : num_sections=1, num_paragraphs=1, num_sentences=71
sections : 1 phần tử, kind="header"   ← CẢ VĂN BẢN là 1 section
```

`meta` còn có `court_level`, `precedent_number`, `case_type` → parser này vốn viết cho **án lệ**, chạy tổng quát trên văn bản luật. Nó chỉ cắt câu, **không hiểu điều/khoản**.

→ **Phải tự parse.** Xem `corpus/parse_dieu.py`.

## 2. markdown bị LÀM PHẲNG — 0 ký tự xuống dòng

**500/500 văn bản có `\n` = 0.** Toàn bộ văn bản là một dòng dài.

**Hậu quả:** mọi regex neo `^` với `re.M` đều **chết câm**.

> Lần đo đầu ra: *"1/500 văn bản có 'Điều N' (0%)"* → suýt kết luận corpus không có cấu trúc và bỏ cả hướng citation.
> Bỏ neo `^` → **499/500 văn bản · 13.668 lần**. Cấu trúc CÓ, chỉ chưa ai parse.

## 3. "Khoản N" KHÔNG BAO GIỜ được viết ra

| Cụm | Số lần trong 500 văn bản |
|---|---|
| `Điều N` | **13.668** |
| `Khoản N` | **0** |
| `Chương ...` | 1.327 |

Luật VN **không viết "Khoản 1"** — khoản được đánh số `1.` `2.` `3.` bên trong Điều, điểm là `a)` `b)`.
→ Parser phải cắt theo số thứ tự, không tìm chữ "Khoản".

## 4. Điều-tiêu-đề vs Điều-trích-dẫn

Hai thứ trông giống hệt nhau:
- **tiêu đề**: `… QUYẾT ĐỊNH: Điều 1. Bãi bỏ Quyết định số 16/2013…`
- **trích dẫn**: `… quy định tại Điều 5 của Luật Hải quan…`

Bắt nhầm trích dẫn thành tiêu đề → cắt vụn văn bản → **citation trỏ sai chỗ**.

**Cách trị đang dùng:** tiêu đề Điều trong một văn bản luôn **đánh số tăng dần từ 1** → lấy dãy con tăng dần. Chắc hơn đoán bằng từ đứng trước (`tại/theo/của`).

## 5. `doc_number` KHÔNG phải khoá duy nhất 🔴

```
14/2025/QĐ-UBND  ×31      20/2025/QĐ-UBND  ×30      08/2025/QĐ-UBND  ×29
```

**31 tỉnh cùng ban hành số `14/2025/QĐ-UBND`.** Không phải trùng lặp — 31 văn bản khác nhau. (`item_id` vẫn duy nhất 9.299/9.299.)

→ **Khoá tra cứu phải là `doc_number` + `issuing_authority`.**
→ `lookup_doc("14/2025/QĐ-UBND")` một mình **vô nghĩa** — nó khớp 31 văn bản, không kết luận được "có thật hay bịa".

## 6. KHÔNG có field hiệu lực

Cột thật: `item_id · doc_number · title · doc_type · legal_type · legal_area · issuing_authority · issue_date · year · summary · markdown · structure_json · source_url`

Không có gì về còn/hết hiệu lực, kể cả trong `structure_json.meta`.

→ **Phép nhiễu #7 (bịa "trích văn bản hết hiệu lực") BỊ LOẠI.** Không hứa với giám khảo cái không có data.
→ Muốn có → join API vbpl.vn = phần monitoring riêng.

## 7. Shard xếp KHÔNG đều — cực kỳ lệch

- Shard **không** sắp theo năm. Mỗi shard trải 1945–20xx.
- Shard 03 báo `year_max=2025` nhưng **chỉ có 1/5000 văn bản ≥2018** — cái max đó là *một* văn bản lẻ.
- Shard 0,1,2,17,18,22–28,30,31 (14 shard): `year_max < 2018` → **0 văn bản lọt lọc**.

**Bài học:** `year_max` từ footer chỉ chứng minh được chiều **"bỏ đi an toàn"**, KHÔNG chứng minh **"có hàng"**.

**Mẹo dùng được:** đọc footer parquet qua HTTP range (**vài KB**) → loại 14 shard chắc chắn rỗng → **khỏi tải 770MB**. Đây là suy luận từ thống kê chính xác, không phải ngoại suy.

## 8. Đếm keyword: HOA/THƯỜNG đổi kết quả ~2×

| | HF API (`LIKE`, phân biệt hoa/thường) | có `utf8_lower` |
|---|---|---|
| ưu đãi | 6.366 | **11.950** |
| công nghệ cao | 2.701 | 4.424 |

→ **Luôn `utf8_lower` trước khi `match_substring`.** Quên là mất nửa số văn bản.

## 9. Corpus bị PHA LOÃNG — chỉ 28,5% đúng chủ đề

Khớp keyword **toàn văn** ≠ đúng chủ đề. Đọc `title` của 9.299 văn bản:

| Chủ đề | % |
|---|---|
| (khác / không rõ) | **45,3** |
| **DN / đầu tư / công nghệ** ⭐ | **28,5** |
| y tế / giáo dục | 12,4 |
| đất đai / xây dựng | 9,2 |
| nông nghiệp | 8,2 |
| người có công / liệt sĩ | 4,0 |

**Bẫy ngữ nghĩa:** `"ưu đãi"` trong luật VN dính cả:
- *"trợ cấp, phụ cấp **ưu đãi** đối với người có công với cách mạng"*
- *"cơ chế **ưu đãi** trong hoạt động vận tải khách công cộng bằng xe buýt"*
- *"vốn vay **ưu đãi** nước ngoài của Chính phủ (ODA)"*

→ **Phải lọc thêm theo `title`**, không tin keyword toàn văn.
→ `data/splits_dn/` = 2.646 văn bản đã lọc (train 2.132 / calib 270 / test 244).

## 10. max_len = **256** (đo thật, không ước lượng)

Tokenizer PhoBERT thật, trên **khoản** thật (không phải cả văn bản):

| p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| 72 | 132 | **261** | 390 | 946 | 10.616 |

**vượt 128: 25,9%** · vượt 256: 10,3%

→ Chốt **256**. 128 cắt mất 1/4 số khoản.
→ 256 là **trần PhoBERT** — 10,3% còn lại phải **cửa sổ trượt**, không lên 512 được.

> ⚠️ Ước lượng "1 token ≈ 3 ký tự" ra 20,2% — **suýt chốt nhầm 128**. Phải đo bằng tokenizer thật.

## 11. Số tiếng Việt ngược với Anh/Mỹ

```
"1.234.567"  chấm = ngăn nghìn   → 1234567
"2,5"        phẩy = thập phân    → 2.5
"1.234,56"   cả hai              → 1234.56
"2.5"        KHÔNG nhóm 3 chữ số → 2.5  (thập phân)
```

**Bẫy đắt nhất — lệch bậc 1000×:** `20 triệu` vs `20 tỷ` cùng chữ số. Phải so **giá trị đã chuẩn hoá**, không so chuỗi.

→ `guard/vn_number.py`, test 14/14 pass. **Dùng CHUNG một hàm** cho cả lúc sinh data lẫn lúc chặn runtime — hai cách hiểu số khác nhau thì guard bắt hụt.

## 12. Cân trục hard-negative — không thì model học mẹo tủ

Bản đầu: **900 định danh vs 51 số** (76% / 4%) → model chỉ học soi citation, **mù với số bịa**.

Nguyên nhân: lọc câu bằng `bóc_số()` — hàm này nhận cả **số thô** (số điều, "05 năm"), nên câu được chọn thường **không có % / tiền để bịa**.

**Sửa:** chỉ giữ câu có `phan_tram|tien|ngay`; lấy ngẫu nhiên 2/3 nhiễu định danh; sinh tới 2 biến thể nhiễu số.

**Sau khi sửa:** định danh 41,4% · số 37,9% · ngữ nghĩa 20,7% (nhắm 40/35/25).

## 13. Hard ≠ Easy negative

| ❌ Easy (vô dụng) | ✅ Hard |
|---|---|
| `Nghị định 9999/1800` | `103/2018/NĐ-CP` (đúng format, năm hợp lý) |
| `30/3/2016` → `28/9` (rụng năm) | `03/6/2016` → `5/12/2016` (giữ format) |

> Bug thật đã dính: bịa ngày làm **rụng mất năm** → nhìn là biết giả. Đã sửa: giữ nguyên format gốc.

**Bắt buộc: đọc 20 mẫu bằng mắt sau mỗi lần sửa corrupter.** Cả 2 bug trên đều do đọc mà ra, không phải do test.

## 14. Cân positive:negative lúc train

Data sinh ra **1 : 4,8**. Kế hoạch yêu cầu **~1:1** → phải **undersample negative** (~4.571 mỗi bên ≈ 9,1k cặp train).
Không cân → model học *"cứ đoán bịa là đúng 83%"*.

---

## Số chốt

| | |
|---|---|
| Tổng kho | **158.822** văn bản |
| year ≥ 2018 | **48.007** |
| Khớp 3 tầng lọc (đã `lower`) | **9.299** |
| Đúng chủ đề DN/đầu tư/công nghệ | **2.646** (28,5%) |
| Khoản ước lượng (subset DN) | ~88.000 |
| Cặp train / calib / test | 26.674 / 3.313 / 3.069 |
| max_len | **256** |
| License | **CC-BY-4.0** (phải ghi nguồn vbpl.vn — Bộ Tư pháp) |

## Môi trường

- ❌ Python 3.14: **không có pyarrow** → dùng `uv run --python 3.11`
- ✅ Python 3.14 **có** torch 2.11+cpu; uv 3.11 có torch 2.13 + transformers 5.14
- ❌ **Máy không có GPU** (`cuda: False`) → CPU ~1h, hoặc Kaggle T4
- ⚠️ Ép `PYTHONUTF8=1` trên Windows kẻo cp1252 vỡ tiếng Việt
- ⚠️ `fsspec` đọc cột parquet qua CDN HuggingFace **không range được** → chậm ngang tải cả file. Chỉ dùng fsspec để đọc **footer**.
- ⛔ **`phobert-base` = MIT** · **`phobert-base-v2` = AGPL, TUYỆT ĐỐI TRÁNH**

## Nợ chưa trả

| # | Việc |
|---|---|
| 1 | Parser: tiêu đề Điều đôi lúc nuốt số khoản (`"Phạm vi điều chỉnh 1"`), có điều tiêu đề rỗng |
| 2 | 10,3% khoản > 256 token → chưa có cửa sổ trượt |
| 3 | `lookup_doc` chưa viết — và phải dùng khoá `doc_number + issuing_authority` |
| 4 | Chưa kiểm: số văn bản "bịa" sinh ra có vô tình trùng văn bản THẬT không |
| 5 | Seed frontend vẫn `[PLACEHOLDER]` — phải thay bằng citation sinh từ corpus |
