# PolicyRadar

> VAIC 2026 · Track **Đổi mới Sáng tạo** · Đề: **Policy & Grant Navigator** (National Innovation Center)

**Trợ lý chủ động hỏi hồ sơ doanh nghiệp rồi đưa ra danh sách chính sách ưu đãi / quỹ hỗ trợ mà doanh nghiệp đủ điều kiện — mọi điều luật đều có căn cứ, trích tới từng điều–khoản–điểm.**

## 🔗 Bản chạy LIVE

| | URL | Kiểm |
|---|---|---|
| **Ứng dụng** | https://vaic-2026-production.up.railway.app | mở là dùng ngay |
| **BFF (API)** | https://web-production-db4aa.up.railway.app/health | `{"ok":true,"service":"policyradar-bff","so_chuong_trinh":7}` |

Hai service chạy trên Railway (repo public). Chi tiết deploy: [DEPLOY.md](DEPLOY.md).

## Vấn đề

Startup, doanh nghiệp FDI và công nghệ cao ở Việt Nam đang bỏ lỡ hàng nghìn chính sách ưu đãi và quỹ hỗ trợ mà họ đủ điều kiện — chỉ vì không biết những chương trình đó tồn tại để mà tìm. Kho pháp luật quốc gia có **158.822 văn bản**, sửa đổi và hết hiệu lực liên tục, rải rác nhiều bộ ngành. Hỏi trợ lý AI thông thường thì nó bịa ra nghị định không có thật → doanh nghiệp nộp sai, mất cơ hội, gánh rủi ro pháp lý.

## Giải pháp — matcher chạy ngược

Chatbot chỉ trả lời khi người ta **biết câu hỏi**. PolicyRadar chạy ngược lại: doanh nghiệp nhập hồ sơ (lĩnh vực, doanh thu, lao động BHXH, tổng nguồn vốn, tỷ lệ doanh thu KH&CN, Giấy chứng nhận DN KH&CN, địa bàn, FDI) → hệ thống **quét ngược điều kiện thụ hưởng** trong kho chính sách → trả về danh sách chương trình **đủ điều kiện**, xếp hạng theo giá trị kỳ vọng, kèm trích dẫn điều–khoản–điểm và hạn nộp.

## Trạng thái

🚧 Đang build (48h, 17–19/07/2026). Repo bắt đầu từ giờ 0 sau khi đề công bố 11:00 ngày 17/07.

## Dữ liệu & ghi công

Dữ liệu văn bản pháp luật lấy từ bộ **`tmquan/vbpl-vn`** (HuggingFace), nguồn gốc từ
**vbpl.vn — Cơ sở dữ liệu quốc gia về văn bản pháp luật (Bộ Tư pháp)**. License **CC-BY-4.0**.

> CC-**BY** = bắt buộc ghi công. Đây là phần ghi công theo Điều 2 luật thi.

Đội **không dùng nguyên dump**: đã lọc còn **9.436 văn bản** (chạm từ khoá chính sách ∧
5 loại văn bản ∧ năm ≥ 2018), **tự viết parser Điều→Khoản→Điểm** (vì `structure_json` của
dump không có cấu trúc pháp lý), lọc chủ đề doanh nghiệp còn **2.669 văn bản**.

**Điều 6 — đã rà nội dung nhạy cảm:** rà toàn bộ 9.436 văn bản theo đúng 5 phạm vi điều 6
nêu (chính trị · biên giới · lãnh thổ · chủ quyền · biển đảo) → **chủ động loại 1 văn bản**
(`16/2021/NQ-HĐND` — Chương trình phát triển bền vững kinh tế biển) khỏi phạm vi tra cứu.

Chi tiết đầy đủ + license thư viện: **[docs/NGUON-DU-LIEU.md](docs/NGUON-DU-LIEU.md)**
