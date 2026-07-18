# Mô hình kinh doanh — PolicyRadar

> Cùng nguyên tắc với [Lộ trình Pilot](LO-TRINH-PILOT.md): số có thật → dẫn nguồn; số ước lượng → **(giả định)**. **Cảnh báo thẳng: hiện CHƯA có tín hiệu cầu đo được** (khảo sát/LOI/willingness-to-pay) — mọi đơn giá dưới đây là giả định để minh hoạ cấu trúc, **phải validate qua pilot** (mục KPI cuối).

## Bối cảnh thị trường (số 2025)

- **Gần 98% doanh nghiệp Việt Nam là DNNVV.** Cuối 2025 cả nước có **859.048 doanh nghiệp đang hoạt động có kết quả sản xuất kinh doanh** (Tổng cục Thống kê, +2,4% so 2024); tổng số DN đăng ký còn hoạt động ~1,1 triệu. Khu vực DNNVV đóng góp **gần 40% GDP**, tạo **5,5 triệu việc làm** (GSO 2025).
- **Bệ đỡ chính sách mạnh (2025): Nghị quyết 68-NQ/TW ngày 4/5/2025** của Bộ Chính trị về phát triển kinh tế tư nhân — coi kinh tế tư nhân là "động lực quan trọng nhất", mục tiêu **≥3 triệu doanh nghiệp vào 2045** và **giảm ≥30% chi phí tuân thủ / thủ tục hành chính ngay trong 2025**. PolicyRadar phục vụ trực tiếp mục tiêu này: *cắt chi phí + thời gian để DN tiếp cận đúng chính sách*.
- Nhà nước **có ngân sách hỗ trợ DNNVV** (Luật Hỗ trợ DNNVV 2017; NĐ 80/2021, 13/2019) — đã tồn tại "túi tiền công" cho việc kết nối DN với chính sách.
- Nỗi đau: chính sách rải rác, sửa đổi/hết hiệu lực liên tục; DN **không biết mình đủ điều kiện gói nào để mà tìm**.

→ PolicyRadar bán **gợi ý CÓ CĂN CỨ** "bạn có thể đủ điều kiện gói này, căn cứ điều–khoản này, còn hiệu lực" — *không phải phán quyết pháp lý* (eligibility suy từ tờ khai DN tự khai; xem [disclaimer](#trách-nhiệm-pháp-lý)).

## Đối thủ (có tên, không nói chung chung)

| Bên | Làm được | Giá (thật) | Thiếu (chỗ PolicyRadar chen vào) |
|---|---|---|---|
| **LuatVietnam** | kho văn bản 1945–nay, tra cứu, tóm tắt, 12 triệu lượt/tháng | Tiêu chuẩn **752.400đ/năm**, Nâng cao **2.120.400đ/năm** | KHÔNG khớp điều kiện theo hồ sơ DN; DN phải tự biết tìm gì |
| **Thư viện Pháp luật** | kho văn bản + bản dịch, gói thành viên | thu phí theo gói năm (tương đương) | như trên — tra cứu, không "quét ngược" ra gói đủ ĐK |
| **Cổng quốc gia hỗ trợ DNNVV** (business.gov.vn, NĐ 80/2021 Đ12) | danh mục hỗ trợ chính thống, miễn phí | 0đ | thụ động: đăng thông tin, không khớp hồ sơ, không soạn hồ sơ |
| **Tư vấn thuê ngoài** | chính xác, có người chịu trách nhiệm | vài triệu đ/vụ | đắt, chậm, không phủ số đông |
| **Chatbot AI phổ thông** | trả lời nhanh | — | **bịa nghị định/số** → rủi ro pháp lý; không citation verbatim |

*Định vị giá:* tra cứu văn bản thuần ~**63k–177k đ/tháng** (LuatVietnam quy đổi), tư vấn thuê ngoài vài triệu/vụ. PolicyRadar Pro nằm giữa — làm nhiều hơn tra cứu (khớp điều kiện + soạn hồ sơ + giám sát), rẻ hơn thuê tư vấn.

Khác biệt cốt lõi: **matcher chạy ngược** (DN không cần biết để mà hỏi) + **guard chống bịa + citation verbatim tới điều–khoản** + **giám sát hiệu lực**. *Lưu ý trung thực: các kỹ thuật này đội tự dựng được — không phải rào bất khả xâm phạm; lợi thế nằm ở việc dựng ĐÚNG + dữ liệu giám sát tích luỹ, không phải "đối thủ không bao giờ vượt".*

---

## Hai đường doanh thu — và cách chúng KHÔNG ăn thịt nhau

Vấn đề rõ: nếu Đường 1 (NIC) phát bản free có đủ matcher + citation, thì **ai trả Pro?** Giải bằng **ranh giới tính năng**:

| Tính năng | Free (Đường 1, NIC phát) | Pro (Đường 2, SaaS) |
|---|---|---|
| Tra cứu + matcher ra gói đủ ĐK | ✅ | ✅ |
| Citation verbatim | ✅ | ✅ |
| **Soạn hồ sơ tự động** (điền sẵn + xuất file) | ❌ | ✅ |
| **Giám sát cảnh báo riêng** (văn bản của gói DN quan tâm sắp/đã hết hiệu lực → email/thông báo) | ❌ | ✅ |
| **Quản nhiều hồ sơ DN + API** (cho đơn vị tư vấn) | ❌ | ✅ |

→ Free (do NIC tài trợ) lo **độ phủ + phúc lợi chính sách**; Pro thu tiền ở **tự động hoá + giám sát chủ động + đa DN** — thứ NIC không phát free. Hai đường **bổ sung**, không trùng.

### Đường 1 — B2G: NIC kết nối doanh nghiệp
| | Nội dung |
|---|---|
| **Ai trả** | NIC / ngân sách hỗ trợ DNNVV |
| **Ai ký** | NIC hoặc Sở KH&ĐT, qua **hợp đồng dịch vụ / đặt hàng nhiệm vụ** (cơ chế mua sắm công), chu kỳ ngân sách năm |
| **Giá trị hợp đồng (giả định)** | ~**300–800 triệu đ/năm** cho vận hành + curate kho + hỗ trợ — cần chốt qua đấu thầu/đặt hàng |
| **NIC được gì** | tăng tỉ lệ DN tiếp cận chính sách (KPI cơ quan), giảm tải tư vấn, **dữ liệu insight** (gói nào được quan tâm, DN thiếu điều kiện gì → phản hồi thiết kế chính sách) |
| **Nhược** | phụ thuộc chu kỳ ngân sách/đấu thầu, ra quyết định chậm |

### Đường 2 — SaaS freemium
| Gói | Ai dùng | Giá (neo theo thị trường; chưa validate willingness-to-pay) |
|---|---|---|
| **Free** | mọi DN | 0đ (tra cứu + matcher + citation) |
| **Pro** | DN muốn nộp hồ sơ | **~150–300k đ/tháng/DN** — cao hơn tra cứu thuần (~63–177k) vì có soạn hồ sơ + giám sát, thấp hơn thuê tư vấn |
| **Đơn vị tư vấn / hiệp hội** | quản nhiều DN + API | báo giá theo số DN |

---

## Unit economics & hoà vốn (giả định — độ nhạy)

**Chi phí cố định (giả định):** 1 chuyên viên pháp lý (curate + duyệt) + hạ tầng + vận hành ≈ **~50 triệu đ/tháng** (curation lao động là khoản chính, không phải hosting). **Chi phí biến đổi/lượt thấp:** LLM ~250–500đ + phục vụ free-tier (phân bổ) — gộp vẫn nhỏ so với giá Pro.

**Số DN Pro cần để hoà vốn** (50 triệu/tháng ÷ giá):
| Giá Pro | DN Pro hoà vốn |
|---|---|
| 150k | ~333 DN |
| 200k | ~250 DN |
| 300k | ~167 DN |

**Phễu freemium để đạt số đó.** Benchmark ngành: freemium **3–5% là "tốt"**, app nhắm đúng đối tượng high-intent **5–15%**, còn freemium rộng thường **1–5%** (nguồn tổng hợp OpenView/Userpilot 2024–2025). Vì PolicyRadar nhắm hẹp (DN cần nộp hồ sơ ưu đãi = high-intent), lấy dải **3–5%**:
| Chuyển đổi | Free users cần cho ~250 Pro (giá 200k) |
|---|---|
| 5% | ~5.000 |
| 4% | ~6.250 |
| 3% | ~8.300 |

- **Kênh tiếp cận (giả định):** qua NIC/vườn ươm/hiệp hội ngành (CAC thấp — lý do đi Đường 1 trước) + SEO nội dung "ưu đãi cho DN ngành X".
- **LTV / churn:** chưa đo — giả định churn ~3–5%/tháng thì LTV ~20–33 tháng × giá. **Cần pilot đo thật.**

> Cần ~167–333 DN Pro để hoà vốn — trên nền **~840 nghìn DNNVV đang hoạt động**, đây là con số nhỏ về *quy mô thị trường*. **Nhưng thị trường lớn KHÔNG tự chứng minh giành được khách**: rào thật là **tỉ lệ chuyển đổi + kênh phân phối**, phải validate ở pilot. Đây là rủi ro số 1, nói thẳng.

---

## Đề xuất: đi cả 2 đường theo thứ tự
1. **Ngắn hạn — Đường 1 (B2G/NIC):** pilot cùng NIC (phủ rộng, uy tín, nguồn văn bản chính thống, ngân sách chi). Cũng là Pha 1 của lộ trình.
2. **Trung hạn — bật Đường 2 (SaaS):** khi kho đủ lớn (Pha 2), mở Pro cho DN/đơn vị tư vấn cần soạn hồ sơ + giám sát — nguồn thu **độc lập ngân sách**, bền hơn.

Hai đường dùng chung một lõi; B2G nuôi độ phủ + dữ liệu, SaaS nuôi doanh thu bền.

## KPI go/no-go cho mô hình kinh doanh (validate ở pilot)
| Tín hiệu | Ngưỡng đi tiếp (giả định) |
|---|---|
| Cầu B2G | ≥1 LOI/đặt hàng từ NIC hoặc Sở KH&ĐT |
| Willingness-to-pay SaaS | ≥20% DN pilot Nhóm A nói sẵn sàng trả cho soạn hồ sơ + giám sát (phỏng vấn) |
| Tỉ lệ chuyển đổi thử | free→Pro ≥2% trên nhóm thử có phí |
| Giữ chân | churn tháng < 5% |

## Trách nhiệm pháp lý
Eligibility là **gợi ý có căn cứ**, suy từ tờ khai DN tự khai — **không thay thế thẩm định của cơ quan có thẩm quyền**. Mọi hồ sơ là **bản nháp chờ DN duyệt** (write-gate) kèm citation. Điều khoản dịch vụ cần **giới hạn trách nhiệm** rõ.

## Tóm tắt cho giám khảo
Hai đường: **(1) B2G qua NIC** (nhà nước tài trợ, DN dùng free, đổi lại độ phủ + insight, giá trị hợp đồng giả định ~300–800tr/năm) và **(2) SaaS freemium** (thu ở soạn hồ sơ + giám sát cảnh báo — Pro-only, KHÔNG trùng bản free → hết cannibalization). Thị trường + benchmark là **số thật có nguồn**; đơn giá neo theo giá đối thủ thật; **nói thẳng điểm chí mạng**: chưa có tín hiệu cầu, phải validate ở pilot. Lợi thế cạnh tranh là grounding chống bịa + matcher chạy ngược — dựng đúng, không phải bất khả xâm phạm. Bệ đỡ chính sách 2025 (**Nghị quyết 68**) đang thuận.

---

## Nguồn (số thật đã dẫn)
- Số DN & DNNVV 2025, đóng góp GDP: Tổng cục Thống kê — *Bức tranh phát triển doanh nghiệp Việt Nam năm 2025* (nso.gov.vn, 01/2026).
- Nghị quyết 68-NQ/TW ngày 4/5/2025 về phát triển kinh tế tư nhân: Báo Chính phủ (baochinhphu.vn).
- Giá dịch vụ đối thủ: LuatVietnam (luatvietnam.vn/dich-vu.html) — Tiêu chuẩn 752.400đ/năm, Nâng cao 2.120.400đ/năm.
- Cổng quốc gia hỗ trợ DNNVV: business.gov.vn (NĐ 80/2021 Điều 12).
- Benchmark chuyển đổi freemium: tổng hợp OpenView / Userpilot (2024–2025).

*Các con số đánh dấu (giả định) là ước lượng nội bộ, chưa validate — phân biệt rõ với số có nguồn ở trên.*
