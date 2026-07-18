# Lộ trình Pilot — PolicyRadar

> Nguyên tắc: **số có thật → dẫn nguồn kiểm được; số ước lượng → ghi rõ "(giả định)"**. Không tô hồng, không bịa cam kết. Doc này chứng minh *sản phẩm chạy thật + có đường thành pilot*, không hứa kết quả.

Đối tượng: **NIC** (Trung tâm Đổi mới sáng tạo Quốc gia, Bộ KH&ĐT) và **doanh nghiệp nhỏ và vừa (DNNVV)** Việt Nam.

**Thời điểm thuận (2025):** gần 98% doanh nghiệp Việt Nam là DNNVV (~840 nghìn DN đang hoạt động có kết quả SXKD cuối 2025, GSO), và **Nghị quyết 68-NQ/TW (4/5/2025)** đặt kinh tế tư nhân làm động lực chính, yêu cầu **giảm ≥30% chi phí tuân thủ / thủ tục** — đúng thứ PolicyRadar giúp cắt (chi phí + thời gian để DN tiếp cận đúng chính sách). Quy mô thị trường + nguồn số: xem [Mô hình kinh doanh](MO-HINH-KINH-DOANH.md).

---

## Pha 0 — Hiện trạng (ĐÃ CÓ, kiểm được trong repo)

| Hạng mục | Con số thật | Nguồn kiểm |
|---|---|---|
| Kho gói chuẩn hoá | **7 gói** (điều kiện + số chép nguyên văn) | `matcher/kho_mau.py`, đã kiểm chứng đối kháng 0 gói bịa |
| Gói có bộ biểu mẫu soạn sẵn | **3** (khcn-thue, dnnvv-tuvan, nafosted) | `ho_so/mau.py` |
| Corpus tra cứu | **2.669 văn bản** vbpl.vn | `data/corpus_slim/` |
| Giám sát hiệu lực (đối chiếu thật) | **949 văn bản**: 598 còn / 290 hết hẳn / **60 hết một phần** / 1 chưa có hiệu lực | `data/giam_sat_quet.json` (nhãn `ma`: CHL/HHL/HHL1P/CCHL) |
| Thẻ địa lý trên corpus | **63 địa phương** (suy từ cơ quan ban hành) | `_dia_ly` (bff) |
| Bản chạy | **LIVE** Railway 2 service | `/health` → 7 gói |

**⚠️ Đọc đúng để không tự tô hồng:**
- **7 gói hiện 100% cấp trung ương** (đều "Chính phủ" — 2 nghị định 13/2019 + 80/2021 + NAFOSTED). "63 địa phương" chỉ là **thẻ địa lý trên corpus TRA CỨU** (theo tên cơ quan ban hành trong văn bản lịch sử), **KHÔNG phải 63 tỉnh đã có gói ưu đãi khớp được**. Con số tỉnh cũng theo cơ cấu hành chính cũ trong metadata — từ 2025 cả nước còn 34 tỉnh/thành, nên "63" là dấu vết lịch sử, không phải hiện trạng.
- Lớp khớp **ngữ nghĩa (PhoBERT NLI) CHƯA chạy live** — mới chặn số + kiểm tồn tại citation. "Guard giữ 7/7 số bịa" đo offline trên cỡ mẫu bằng đúng số gói (7) → **chưa đủ để tuyên bố robust**, phải đo lại khi kho lên 25–100 gói.
- Deploy LIVE đang ở **hosting hobby-tier** (~$10–30/tháng) — đủ để trải nghiệm, **chưa phải hạ tầng production** (SLA/backup/uptime).

**Kết luận Pha 0 trung thực:** lõi tất định (matcher quét ngược + guard số + giám sát) **chạy thật**; đủ để **thí điểm có kiểm soát**, chưa phải "vận hành production toàn quốc".

---

## Ai chịu chi phí Pha 1?

Pilot đi theo **Đường 1 (B2G)** của [Mô hình kinh doanh](MO-HINH-KINH-DOANH.md): **PolicyRadar miễn phí cho DN, chi phí pilot do NIC / ngân sách hỗ trợ DNNVV chi** (Luật Hỗ trợ DNNVV 2017 có mục ngân sách này). Nếu không có NIC, phương án dự phòng: chạy pilot tự chi ở quy mô nhỏ hơn (10–15 DN) để lấy dữ liệu cầu trước khi tiếp cận đối tác.

> **Điểm chết đơn lẻ (nói thẳng):** cả Pha 1 giả định NIC/vườn ươm cấp được 30–50 DN. **Chưa có LOI/biên bản/đầu mối cam kết** — đây là rủi ro số 1, cần chốt bằng 1 thư ngỏ trước khi khởi động.

---

## Pha 1 — Pilot có kiểm soát với NIC (0–3 tháng)

**Phạm vi (giả định):** ~30–50 DNNVV do NIC/vườn ươm kết nối. Để tránh **thiên lệch chọn mẫu** (chọn đúng DN hợp 7 gói rồi báo tỉ lệ khớp cao), chia 2 nhóm:
- **Nhóm A — có định hướng** (~20 DN KH&CN / khởi nghiệp sáng tạo): đo được luồng soạn hồ sơ end-to-end.
- **Nhóm B — ngẫu nhiên/không tuyển chọn** (~15–20 DN bất kỳ): đo **tỉ lệ khớp THẬT** của kho hiện tại — chấp nhận con số thấp và dùng nó làm căn cứ mở rộng kho.

**Việc làm:** mở kho 7 → ~20–25 gói ưu tiên (cùng khung pháp lý, vẫn verbatim + kiểm chứng); DN thật dùng; đối chiếu phán quyết matcher với **thẩm định của chuyên viên NIC** trên cùng hồ sơ.

**KPI — tách 2 nhóm rõ ràng:**

*KPI SẢN PHẨM (giá trị người dùng):*
| Chỉ số | Ngưỡng (giả định) | Cách đo |
|---|---|---|
| Độ chính xác match vs chuyên viên | ≥ 90% trùng phán quyết | **N ≥ 30 hồ sơ**, chọn ngẫu nhiên, chuyên viên NIC là chuẩn vàng, báo cả khoảng tin cậy |
| Trích dẫn đúng điều–khoản | **100%** (không được sai căn cứ) | rà từng citation, N như trên |
| DN Nhóm A soạn được ≥1 hồ sơ hoàn chỉnh | ≥ 60% | log soạn hồ sơ |
| Tỉ lệ khớp trên Nhóm B (ngẫu nhiên) | *đo để biết, không đặt ngưỡng* | % DN ra ≥1 gói đủ ĐK |

*KPI VẬN HÀNH / AN TOÀN (nội bộ, không trộn với trên):*
| Chỉ số | Ngưỡng |
|---|---|
| Guard chặn số bịa (nếu bật GPT) | không để lọt số vô căn cứ; đo lại trên kho ≥25 gói |
| Uptime pilot | ≥ 99% giờ hành chính |

**Go** nếu KPI sản phẩm đạt (đặc biệt trích dẫn 100% + match ≥90%); **no-go/điều chỉnh** nếu có citation sai hoặc match < 90%.

---

## Pha 2 — Mở rộng kho + bán tự động hoá curation (3–6 tháng)

Nút thắt lớn nhất là **curate mỗi gói bằng tay = LAO ĐỘNG PHÁP LÝ** (không phải hosting). Pha 2 giải nút này:
- Pipeline **bán tự động**: LLM đề xuất cấu trúc điều kiện từ nguyên văn (`scripts/moi_nguyen_van.py` đã moi nguyên văn) → **chuyên viên pháp lý duyệt** → guard đối chiếu verbatim với corpus. Người chốt, máy dựng nháp.
- Mục tiêu: **~20–25 → 80–100 gói**. *Lưu ý (giả định):* chưa có mẫu số chính thức "tổng số gói ưu đãi DNNVV trung ương" nên **không tuyên bố "phủ phần lớn"** — chỉ nói "phủ các gói phổ biến nhất, đo độ phủ theo danh mục NIC cung cấp".
- Đo **chi phí curate/gói** (giả định 1–2 giờ chuyên viên/gói giai đoạn này) → căn cứ tính đơn giá nhân rộng và ngân sách kho.

**KPI:** ≥80 gói với 0 gói lệch verbatim; chi phí curate/gói giảm ≥30% *(giả định mục tiêu)* so với làm tay thuần.

---

## Pha 3 — Nhân rộng / tích hợp (6–12 tháng)

- Đối chiếu/tích hợp **Cổng thông tin quốc gia hỗ trợ DNNVV** (Điều 12 NĐ 80/2021).
- Mở API cho vườn ươm / hiệp hội ngành / đơn vị tư vấn.
- Chuyển giám sát từ cron hằng ngày sang **theo dõi ưu tiên** văn bản gốc của gói (bắt "vừa hết hiệu lực" sớm hơn).

---

## Chi phí pilot (giả định — chốt lại khi khởi động)

Chi phí biến đổi/lượt rất thấp: LLM ~250–500đ/lượt *(giả định ~2k token)*, API vbpl.vn **0đ** (công khai CC-BY-4.0), hosting ~$10–30/tháng (thật). **Nhưng chi phí thật của pilot là LAO ĐỘNG:**

| Khoản (giả định) | Ước lượng |
|---|---|
| 1 chuyên viên pháp lý (curate kho + duyệt hồ sơ), bán thời gian | ~20–35 triệu đ/tháng |
| Vận hành + hạ tầng | ~5–10 triệu đ/tháng |
| **Tổng pilot 3 tháng** | **~75–135 triệu đ (giả định)** — đây là con số NIC/ngân sách cần duyệt |

> Ai làm chuyên viên (thuê ngoài / NIC cử / founder) là biến cần chốt với đối tác. Bảng chi phí "vài chục USD hosting" KHÔNG phải chi phí thật — chi phí thật là lao động pháp lý.

---

## Đối thủ & rủi ro pháp lý (giám khảo sẽ hỏi)

**Hôm nay DN tra ưu đãi bằng gì:** LuatVietnam / Thư viện Pháp luật (kho văn bản, tìm kiếm — **không** khớp điều kiện theo hồ sơ), tư vấn thuê ngoài (đắt, chậm), hoặc tự đọc. PolicyRadar khác ở **matcher chạy ngược** (DN không cần biết để mà hỏi) + **citation verbatim + giám sát hiệu lực**. Chi tiết cạnh tranh: [Mô hình kinh doanh](MO-HINH-KINH-DOANH.md).

**Trách nhiệm pháp lý:** matcher suy eligibility từ **tờ khai DN tự khai** → kết quả là **gợi ý CÓ CĂN CỨ, không phải phán quyết**. Mọi hồ sơ là **bản nháp chờ DN duyệt** (write-gate), kèm citation để DN/chuyên viên tự kiểm. Pilot cần **điều khoản miễn trừ** rõ: PolicyRadar hỗ trợ tra cứu, không thay thế thẩm định của cơ quan.

| Rủi ro | Giảm thiểu |
|---|---|
| NIC không tham gia | Có phương án tự chi quy mô nhỏ lấy dữ liệu cầu trước |
| Luật đổi/hết hiệu lực → dẫn sai | Giám sát ② đối chiếu vbpl.vn; văn bản hết hiệu lực bị đánh dấu, không dùng làm căn cứ |
| LLM bịa số/điều luật | Guard số tất định chặn; matcher (không LLM) quyết eligibility |
| Thiên lệch chọn mẫu | Nhóm B ngẫu nhiên đo tỉ lệ khớp thật |
| DN nộp trượt vì tin công cụ | Write-gate + citation + điều khoản miễn trừ |

---

## Tóm tắt cho giám khảo

Pilot **không bắt đầu từ 0** (7 gói verbatim, giám sát 949 VB, deploy LIVE). Pha 1 **kiểm chứng độ chính xác với chuyên viên NIC trên DN thật, có nhóm ngẫu nhiên chống thiên lệch, KPI go/no-go + cỡ mẫu rõ**; Pha 2 giải nút curate (lao động pháp lý); Pha 3 nhân rộng. Số thật dẫn nguồn; số kế hoạch ghi rõ giả định; điểm yếu (NLI chưa live, chưa có LOI NIC, kho toàn trung ương) **nói thẳng, không giấu**.
