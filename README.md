# PolicyRadar

> VAIC 2026 · Track **Đổi mới Sáng tạo** · Đề: **Policy & Grant Navigator** (National Innovation Center)

**Trợ lý chủ động hỏi hồ sơ doanh nghiệp rồi đưa ra danh sách chính sách ưu đãi / quỹ hỗ trợ mà doanh nghiệp đủ điều kiện — mọi điều luật đều có căn cứ, trích tới từng điều–khoản–điểm.**

## Vấn đề

Startup, doanh nghiệp FDI và công nghệ cao ở Việt Nam đang bỏ lỡ hàng nghìn chính sách ưu đãi và quỹ hỗ trợ mà họ đủ điều kiện — chỉ vì không biết những chương trình đó tồn tại để mà tìm. Kho pháp luật quốc gia có **158.822 văn bản**, sửa đổi và hết hiệu lực liên tục, rải rác nhiều bộ ngành. Hỏi trợ lý AI thông thường thì nó bịa ra nghị định không có thật → doanh nghiệp nộp sai, mất cơ hội, gánh rủi ro pháp lý.

## Giải pháp — matcher chạy ngược

Chatbot chỉ trả lời khi người ta **biết câu hỏi**. PolicyRadar chạy ngược lại: doanh nghiệp nhập hồ sơ (ngành, vốn, nhân sự, chi R&D, địa bàn, FDI) → hệ thống **quét ngược điều kiện thụ hưởng** trong kho chính sách → trả về danh sách chương trình **đủ điều kiện**, xếp hạng theo giá trị kỳ vọng, kèm trích dẫn điều–khoản–điểm và hạn nộp.

## Trạng thái

🚧 Đang build (48h, 17–19/07/2026). Repo bắt đầu từ giờ 0 sau khi đề công bố 11:00 ngày 17/07.

## Dữ liệu

`tmquan/vbpl-vn` — 158.822 văn bản pháp luật quốc gia (nguồn vbpl.vn, Bộ Tư pháp), cấu trúc document→điều→khoản→điểm, license **CC-BY-4.0**.
