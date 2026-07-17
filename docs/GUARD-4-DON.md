# Guard chống bịa điều luật — kế hoạch 4 đòn

> Domain: văn bản pháp luật VN (corpus `tmquan/vbpl-vn`). Guard phải bắt AI bịa:
> số nghị định không có thật · sai điều/khoản · sai mức % · sai hạn · sai ngưỡng vốn ·
> sai cơ quan ban hành · trích văn bản hết hiệu lực · **bịa điều kiện thụ hưởng**.
>
> Ngân sách: 6–8h trong 48h. PyTorch là **giải phụ** — không được để nó giết bài chính.

## Thứ tự chạy: #4 → #2 → #3 → #1

| Thứ tự | Đòn | Gọi với giám khảo | Compute |
|---|---|---|---|
| 1 | #4 sinh hard-negative | *"adversarial corruption engine, thuần rule"* | giây |
| 2 | #2 đào hard-negative | **"iterative hard-negative mining"** (KHÔNG nói "self-play") | 15–25′ |
| 3 | #3 calibration | *"temperature scaling (Guo 2017)"* | 2–5′ |
| 4 | #1 ablation | *"ablation study"* | ~20′ |

**Vì sao thứ tự này:** #4 là *nguyên liệu* (không có nó thì #2 không có gì để đào), và `lookup_doc()` + `normalize_vn_number` sinh ra từ #4 **dùng luôn làm lớp guard tất định lúc chạy thật**. #3 là hậu-xử-lý nên cần model cuối. #1 cần đủ món để tắt.

---

## Đòn #4 — sinh hard-negative

Domain luật có **2 trục mà domain số tiền không có**:
- **ĐỊNH DANH** — số nghị định/điều/khoản/cơ quan: chuỗi *tra ngược được trong corpus*. Đây là chỗ LLM gãy nặng nhất.
- **THỜI HIỆU** — còn/hết hiệu lực.

Câu gốc ví dụ: *"Theo Khoản 3 Điều 5 Nghị định 80/2021/NĐ-CP do Chính phủ ban hành, DNNVV được hỗ trợ 50% chi phí tư vấn, nộp trước 30/9, áp dụng với DN vốn dưới 20 tỷ."*

| # | Phép nhiễu | Bịa thành | Bắt bằng |
|---|---|---|---|
| 1 | Số văn bản giả | NĐ **99/2026/NĐ-CP** | tất định — `lookup_doc()` miss |
| 2 | Sai điều/khoản | **Khoản 1 Điều 8** | tất định — vị trí không tồn tại |
| 3 | Sai mức % | hỗ trợ **30%** | `normalize_vn_number` |
| 4 | Sai hạn | trước **31/12** | parse ngày |
| 5 | Sai ngưỡng | vốn dưới **100 tỷ** | `normalize_vn_number` |
| 6 | Sai cơ quan | do **Bộ Tài chính** ban hành | tra field issuer |
| 7 | Văn bản hết hiệu lực | dùng NĐ 39/2018 (đã bị thay) | tra status/replaced_by |
| 8 | **Bịa điều kiện thụ hưởng** | "DN bạn **đủ điều kiện**" trong khi điều-khoản không nói vậy | **chỉ NLI bắt được** ← phần đáng khoe |

**Quy tắc:**
- Trộn đa trục: ~40% định danh · ~35% số · ~25% ngữ nghĩa. Một trục áp đảo → model chỉ học 1 mẹo.
- Số nghị định giả phải **nghe hợp lý** (đúng format, năm hợp lệ, số trong dải thật). Sinh "NĐ 9999/1800" là easy-negative, vô dụng.
- Mỗi bản ghi bắt buộc có `corruption_type` (→ confusion matrix per-slice) + `doc_id` (→ split chống rò rỉ) + `gia_tri_goc`/`gia_tri_bia`.
- **Mắt người đọc 20 mẫu ngẫu nhiên** — nhìn là biết giả ngay thì corrupter hỏng.

## Đòn #2 — iterative hard-negative mining

1. Vòng 0: train trên positive + negative ngẫu nhiên.
2. Sinh pool bằng #4 → vài nghìn câu bịa.
3. **Đào**: guard chấm cả pool → giữ câu ungrounded mà guard tưởng grounded (P>0.5), **sai-mà-tự-tin-cao lên đầu**, lấy top-k ≈500.
4. Nhồi vào train → train lại. Đo trên test **đóng băng**. Lặp 3–5 vòng → `mining_curve.png`.

**Bẫy rò rỉ — quan trọng nhất:**
- Test hard-negative **đóng băng từ vòng 0**, không bao giờ lẫn vào train.
- ⚠️ **Rò rỉ theo DOCUMENT, không phải theo câu** (bẫy riêng của domain luật): nếu NĐ 80/2021 xuất hiện cả train lẫn test (dù khác điều), model học thuộc văn bản đó → điểm ảo. → **split theo `doc_id`**, viết `assert` thật chứ đừng tin mắt.
- **3-way split từ đầu**: train / calib / test. Calib dành riêng cho #3.
- Trung bình 3 seed mỗi vòng → đường mượt.

## Đòn #3 — calibration

Temperature scaling trên tập **calib** (không phải test) → reliability diagram → ECE trước/sau → chọn ngưỡng refuse.

⚠️ **BUG T-ÂM — đã gặp thật, sẽ gặp lại.** LBFGS trên logit của model train bằng margin-loss có thể ra **T < 0** → xác suất lật ngược → ECE nổ 0.118 → 0.50. **Áp fix ngay từ dòng code đầu:**
```python
T = torch.exp(log_T)          # tham số hoá qua log → luôn > 0
T = torch.clamp(T, 0.05, 20)
```
**Assert `ECE_sau < ECE_truoc`** — fail thì dừng, đừng ghi số lên slide.

**Ngưỡng refuse domain luật đặt CAO hơn:** target precision **97–98%** (không phải 95%). Refuse sai = khách khó chịu; khuyên sai = **DN nộp sai hồ sơ, mất cơ hội, gánh rủi ro pháp lý**. Thà nói *"chưa đủ căn cứ"*.

## Đòn #1 — ablation

Train **5 bản**, mỗi bản tắt đúng 1 món: Full · −margin loss · −hard-neg mining · −calibration · **−existence lookup** (riêng domain luật).

⚠️ **Tách ngưỡng khi đo** (bài học đã trả giá): F1 + bắt-bịa đo ở **argmax 0.5**; refuse-precision đo ở **ngưỡng calibrated**. Trộn chung → các dòng ablation ra giống hệt nhau, mất trắng đòn #1.

Cùng seed / cùng test / cùng epoch, chỉ đổi 1 thành phần. Dòng `−existence lookup` phải cho thấy cột "bắt NĐ-giả" **sập** → đó là bằng chứng lớp tất định đáng tiền.

---

## Model + data

| Thứ | Chốt |
|---|---|
| Backbone | **`vinai/phobert-base` (MIT)** — ⛔ TUYỆT ĐỐI TRÁNH `phobert-base-v2` (**AGPL**) |
| Tách từ | **`underthesea.word_tokenize`** — né hẳn VnCoreNLP + Java |
| Fallback | char n-gram → MLP trên CPU (~30s) — **verify pipeline trước khi đốt GPU** |
| Data | JSONL `{premise, hypothesis, label, doc_id, corruption_type, gia_tri_goc, gia_tri_bia}` |
| Hyperparams | lr 2e-5 · batch 16 · seed 7 · epochs 8 (CPU) / 3–4 (T4) · λ grid {0, 0.3, 0.7, 1.0} |

⚠️ **`max_len=128` là rủi ro thật cho domain luật** — một khoản có thể dài hơn. Đo phân bố độ dài token ngay giờ đầu; >20% bị cắt → lên 256.

⚠️ **PhobertTokenizer là slow tokenizer, KHÔNG có offsets** → không highlight token-level được. Dùng **diff tất định** (regex số bịa vs số nguồn) để tô đỏ → được ~80% cú wow với 0h train thêm.

## Số cũ từ rehearsal — CHỈ để đối chiếu, KHÔNG đọc lên slide

> Số của **domain khác** (ngân hàng/ĐMX), model nhẹ, data tổng hợp. Dùng để biết pipeline chạy đúng trông thế nào.

- #2: bị lừa 65% → ~4% qua 6 vòng. Hình dạng phải **dốc mượt**; ra vách đứng = data quá dễ.
- #3: ECE 0.118 → 0.002, T≈0.18. ECE sau > trước = **đỏ đèn bug T-âm**.
- #1: Full F1 1.00 — **F1=1.00 là dấu hiệu data synthetic bão hoà, đừng khoe.** Bản policy trên data thật phải ra **thấp hơn**, đó mới là số đáng tin. Đáng đối chiếu là **hình dạng ablation**, không phải trị tuyệt đối.

## Cách gọi tên — sai tên = mất điểm

| ❌ Đừng nói | ✅ Nói |
|---|---|
| "self-play" | **"iterative hard-negative mining"** |
| "model hiểu luật" | "guard **đối chiếu** claim với điều-khoản được trích" |
| "guard bắt 99%" | "trên test held-out N mẫu bắt X% — **giới hạn: chỉ phủ 7 kiểu bịa bọn em sinh được**" |
| khoe F1 trên data synthetic | khoe **pipeline + ablation** |

## Điều cấm

1. ⛔ `phobert-base-v2` = AGPL.
2. ⛔ Không publish weights/checkpoint lên GitHub → `.gitignore`.
3. ⛔ Không rò rỉ test set — nhớ rò rỉ theo **doc_id**.
4. ⛔ Không dùng LLM sinh corruption → **thuần code**.
5. ⛔ Tổng >3 model train on-site = tự bắn vào chân.
6. ⛔ **Anti-fabrication áp cho CHÍNH MÌNH** — số slide phải verify, không ngoại suy.

## Checklist ngay

1. ✅ Corpus: full-count qua API — **158.822 tổng · 48.007 từ 2018 · ~7.598 khớp 3 tầng lọc**.
2. ⬜ **Kiểm field hiệu lực có tồn tại trong corpus không.** Nếu KHÔNG → **phép nhiễu #7 phải bỏ**, đừng hứa với giám khảo cái không có data.
3. ⬜ Đo phân bố độ dài điều/khoản → chốt `max_len` 128 hay 256.
4. ⬜ `lookup_doc(doc_number, dieu, khoan)` → `{exists, text, issuer, status}` — **lớp guard tất định runtime**.
5. ⬜ `normalize_vn_number` (dấu chấm = ngăn nghìn → bỏ; dấu phẩy = thập phân).
6. ⬜ 7 corrupter + template bịa-điều-kiện → `hard_negs_policy.jsonl` (~5–10k).
7. ⬜ 3-way split theo `doc_id` + assert không trùng phía.
8. ⬜ Chạy bản CPU nhẹ trước → xanh mới lên PhoBERT.
9. ⬜ #2 mining 3–5 vòng × 3 seed → `mining_curve.png`.
10. ⬜ #3 calibration (áp fix T ngay) + assert ECE giảm → ngưỡng refuse @97%.
11. ⬜ #1 ablation 5 bản, tách ngưỡng khi đo → `ablation_table.csv` + per-slice.
12. ⬜ 20 ca golden eval (10 số/văn-bản + 10 điều-kiện + ca ⭐ anti-sycophancy).
