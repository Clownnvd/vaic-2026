"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "vi" | "en";

/**
 * i18n nhẹ — không thêm thư viện. Từ điển giao diện (UI chrome) VI↔EN.
 *
 * ⚠️ CHỈ dịch phần GIAO DIỆN (nút, nhãn, tiêu đề). KHÔNG dịch nội dung PHÁP LUẬT
 * (tên văn bản, trích dẫn, diễn giải) — đó là luật Việt Nam, dịch = sai/bịa.
 * Nội dung luật giữ nguyên tiếng Việt kể cả khi giao diện là tiếng Anh.
 *
 * Khoá = chính chuỗi tiếng Việt → đỡ phải đặt key riêng cho từng chuỗi.
 * t("Danh sách luật") → "Laws" khi lang=en, giữ nguyên khi vi.
 */
const EN: Record<string, string> = {
  // thương hiệu / nav
  "Trợ lý chính sách · NIC": "Policy Assistant · NIC",
  "Cuộc trò chuyện mới": "New chat",
  "Trợ lý tư vấn": "Advisor",
  "Soạn hồ sơ": "Prepare dossier",
  "Giám sát chính sách": "Policy monitor",
  "Danh sách luật": "Laws",
  "Lịch sử": "History",
  "Thu gọn thanh bên": "Collapse sidebar",
  "Mở thanh bên": "Open sidebar",
  "Doanh nghiệp": "Enterprise",
  "Gói tra cứu chính sách": "Policy lookup plan",
  "Xoá cuộc trò chuyện": "Delete chat",
  // nhóm thời gian
  "Hôm nay": "Today",
  "Hôm qua": "Yesterday",
  "7 ngày qua": "Last 7 days",
  "30 ngày qua": "Last 30 days",
  "Cũ hơn": "Older",
  "Chưa có cuộc trò chuyện nào. Bắt đầu bằng cách mô tả doanh nghiệp của bạn.":
    "No conversations yet. Start by describing your business.",
  // header
  "Trợ lý tư vấn chính sách": "Policy advisor",
  "Tìm đúng chính sách bạn đủ điều kiện — có căn cứ tới từng điều khoản":
    "Find policies you qualify for — grounded to each article",
  "Tra cứu văn bản trong corpus — tìm kiếm, lọc theo tiêu chí":
    "Search the corpus — filter by criteria",
  "Soạn hồ sơ xin tài trợ": "Prepare grant dossier",
  "Dựng khung hồ sơ, điền sẵn từ hồ sơ DN — bản nháp chờ duyệt":
    "Build form drafts, auto-filled from your profile — draft awaiting approval",
  "Theo dõi hiệu lực + văn bản liên quan, đối chiếu vbpl.vn":
    "Track validity + related documents against vbpl.vn",
  // chat
  "Đang quét kho văn bản…": "Scanning documents…",
  "Mô tả doanh nghiệp của bạn, hoặc hỏi về một chương trình… (Shift+Enter để xuống dòng)":
    "Describe your business, or ask about a program… (Shift+Enter for newline)",
  "Gửi": "Send",
  "PolicyRadar chỉ khẳng định điều gì có căn cứ trong kho văn bản. Thiếu căn cứ thì nói thẳng là chưa đủ căn cứ.":
    "PolicyRadar only asserts what is grounded in the corpus. When unsupported, it says so plainly.",
  // panel hồ sơ
  "Hồ sơ doanh nghiệp": "Business profile",
  "Ngữ cảnh giữ suốt cuộc trò chuyện. Dòng trống → trợ lý sẽ hỏi tiếp.":
    "Context kept across the chat. Empty rows → the assistant will ask.",
  "— chưa có": "— not set",
  // nhãn field hồ sơ
  "Lĩnh vực": "Sector",
  "Lao động BHXH": "SI employees",
  "Doanh thu năm": "Annual revenue",
  "Tổng nguồn vốn": "Total capital",
  "Doanh thu KH&CN": "S&T revenue",
  "GCN DN KH&CN": "S&T cert.",
  "Nữ làm chủ": "Woman-led",
  "Ngành": "Industry",
  "Địa bàn": "Location",
  "Vốn FDI": "FDI capital",
  // guard
  "Đã kiểm chứng — số liệu bám nguồn": "Verified — figures grounded",
  "Guard": "Guard",
  "Guard chặn": "Guard blocked",
  "số không có căn cứ": "ungrounded figure(s)",
  "Số này KHÔNG có trong căn cứ — guard tô đỏ":
    "This figure is NOT in the source — flagged by guard",
  "AI diễn giải · kiểm bằng lớp số tất định (đối chiếu nguyên văn corpus)":
    "AI interpretation · checked by the deterministic number layer (against corpus text)",
  // badge grounding
  "Đủ căn cứ": "Grounded",
  "Chưa đủ căn cứ": "Insufficient basis",
  // kết quả
  "Đã quét": "Scanned",
  "văn bản · xếp theo giá trị kỳ vọng": "documents · ranked by expected value",
  // danh sách luật
  "Loại văn bản": "Doc type",
  "Cơ quan": "Authority",
  "Năm": "Year",
  "Xoá lọc": "Clear filters",
  "Mở trên vbpl.vn ↗": "Open on vbpl.vn ↗",
  "Tìm theo số hiệu, tiêu đề, cơ quan… (gõ không dấu cũng được)":
    "Search by number, title, authority… (accents optional)",
  "tất cả": "all",
  "Đang tải…": "Loading…",
  "khớp": "matching",
  "Trang": "Page",
  "Không có văn bản nào khớp. Thử bỏ bớt bộ lọc.":
    "No documents match. Try removing some filters.",
  "Lỗi tải": "Load error",
  // soạn hồ sơ
  "Chọn chương trình để xem bộ văn bản cần nộp. Bấm từng văn bản để mở biểu mẫu điền — hệ thống điền sẵn phần biết chắc từ hồ sơ doanh nghiệp, bạn khai nốt phần còn lại.":
    "Pick a program to see its required documents. Click each to open a fillable form — the system pre-fills known fields from your profile; you fill the rest.",
  "Mọi bản đều là bản nháp chờ bạn duyệt.": "Every draft awaits your approval.",
  "AI không tự điền — code gợi ý, bạn duyệt": "AI never types — code suggests, you approve",
  "Lưu nháp": "Save draft",
  "Duyệt & tải": "Approve & download",
  "văn bản": "documents",
  "Đang dựng bộ hồ sơ…": "Building the dossier…",
  "Chương trình này chưa gắn biểu mẫu trong kho.":
    "This program has no forms attached in the corpus yet.",
  "Căn cứ": "Basis",
  "nơi nhận": "recipient",
  "hạn": "deadline",
  "ô": "fields",
  "Doanh nghiệp tự khai": "Self-declared by enterprise",
  "Hệ thống điền từ hồ sơ DN": "Filled by system from profile",
  "Điền từ văn bản (corpus)": "Filled from document (corpus)",
  "Bạn tự khai ô này…": "Fill this field yourself…",
  "Gốc hệ thống điền:": "System-filled original:",
  // giám sát
  "Giám sát hiệu lực chính sách": "Policy validity monitor",
  "Còn hiệu lực": "In effect",
  "Hết hiệu lực": "Expired",
  "Chưa đối chiếu": "Not checked",
  "Mỗi văn bản được đối chiếu trạng thái hiệu lực":
    "Each document's validity status is checked",
  "trực tiếp với vbpl.vn (Bộ Tư pháp)":
    "directly against vbpl.vn (Ministry of Justice)",
  "Khi một văn bản chuyển sang hết hiệu lực hoặc bị thay thế, hệ thống cảnh báo ngay — không để bạn nộp theo văn bản đã chết.":
    "When a document expires or is superseded, the system warns you immediately — so you never file against a dead document.",
  "Nguồn:": "Source:",
  "Đang đối chiếu vbpl.vn…": "Checking against vbpl.vn…",
  "Mở bài gốc trên vbpl.vn": "Open the original on vbpl.vn",
  "văn bản liên quan (căn cứ / thay thế / sửa đổi)":
    "related documents (basis / replacement / amendment)",
  "Chương trình bạn quan tâm — trạng thái hiện tại":
    "Programs you care about — current status",
  "Quét kho — đối chiếu vbpl.vn phát hiện văn bản đã đổi trạng thái":
    "Corpus scan — vbpl.vn check finds documents that changed status",
  "đã hết hiệu lực": "expired",
  "còn hiệu lực": "in effect",
  "đã quét": "scanned",
  "Nếu trợ lý trích các văn bản này mà không đối chiếu → doanh nghiệp nộp theo văn bản đã chết. Giám sát chặn đúng lỗi đó.":
    "If the assistant cited these without checking → the business would file against a dead document. Monitoring blocks exactly that.",
  "Danh sách văn bản đã hết hiệu lực": "List of expired documents",
  "Số hiệu": "Number",
  "Văn bản": "Document",
  "Trạng thái": "Status",
  "Tìm số hiệu, tiêu đề, cơ quan…": "Search number, title, authority…",
  // loại chương trình (LOAI_NHAN)
  "Ưu đãi thuế": "Tax incentive",
  "Quỹ hỗ trợ": "Support fund",
  "Tài trợ": "Grant",
  "Hỗ trợ lãi suất": "Interest subsidy",
  "Hỗ trợ chi phí": "Cost subsidy",
  // thẻ chương trình
  "Đạt": "Met",
  "Chưa đạt": "Not met",
  "Chưa đủ thông tin": "Insufficient info",
  "Hồ sơ:": "Dossier:",
  "giá trị kỳ vọng": "expected value",
  "Đủ điều kiện": "Eligible",
  "hồ sơ hiện tại thoả toàn bộ tiêu chí bắt buộc":
    "the current profile meets every required criterion",
  "Chưa đủ điều kiện": "Not yet eligible",
  "thiếu:": "missing:",
  "Hạn nộp:": "Deadline:",
  "Vì sao đủ điều kiện": "Why eligible",
  "Độ tin cậy": "Confidence",
  "— chưa xác nhận hết vì thiếu": "— not fully confirmed, missing",
  "Bổ sung để lên 100%.": "Add it to reach 100%.",
  "Hiệu lực chưa đối chiếu vbpl.vn": "Validity not checked against vbpl.vn",
  "đối chiếu vbpl.vn": "checked against vbpl.vn",
  // citation
  "Chưa đối chiếu corpus — dữ liệu seed dựng UI":
    "Not verified against corpus — seed data for UI",
  "Xem bài gốc trên vbpl.vn": "View the original on vbpl.vn",
  // lời chào onboarding + hệ thống
  "Để tìm đúng ưu đãi và quỹ mà bạn đủ điều kiện, cho mình biết vài thông tin về doanh nghiệp: lĩnh vực (nông-lâm-thuỷ sản/công nghiệp-xây dựng hay thương mại-dịch vụ), số lao động tham gia BHXH bình quân năm, tổng doanh thu, tổng nguồn vốn, có Giấy chứng nhận DN KH&CN không, và tỷ lệ doanh thu từ sản phẩm KH&CN.\n\nBạn cứ mô tả bằng một câu tự nhiên — gõ không dấu cũng được.":
    "To find the incentives and funds you qualify for, tell me a few details about your business: sector (agriculture-forestry-fishery/industry-construction, or trade-services), average annual number of employees covered by social insurance, total revenue, total capital, whether you hold a Science & Technology Enterprise Certificate, and the share of revenue from S&T products.\n\nJust describe it in one natural sentence.\n\n(Note: the example prompts below are in Vietnamese — the policy Q&A runs on the Vietnamese legal corpus, so answers are in Vietnamese.)",
  "Có lỗi khi gọi hệ thống. Vui lòng thử lại.":
    "Something went wrong calling the system. Please try again.",
  "Thời gian phản hồi. Đề bài yêu cầu ≤ 5.000ms cho câu đơn giản.":
    "Response time. The brief requires ≤ 5,000ms for simple queries.",
};


const I18nCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (s: string) => string }>({
  lang: "vi",
  setLang: () => {},
  t: (s) => s,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangRaw] = useState<Lang>("vi");
  useEffect(() => {
    const l = localStorage.getItem("policyradar.lang");
    if (l === "en" || l === "vi") setLangRaw(l);
  }, []);
  const setLang = (l: Lang) => {
    setLangRaw(l);
    localStorage.setItem("policyradar.lang", l);
  };
  const t = (s: string) => (lang === "en" ? EN[s] ?? s : s);
  return <I18nCtx.Provider value={{ lang, setLang, t }}>{children}</I18nCtx.Provider>;
}

export function useI18n() {
  return useContext(I18nCtx);
}

/** Nút đổi ngôn ngữ — MỘT nút, bấm là đổi VI↔EN (globe + mã ngôn ngữ hiện tại). */
export function LangToggle() {
  const { lang, setLang } = useI18n();
  const khac: Lang = lang === "vi" ? "en" : "vi";
  return (
    <button
      onClick={() => setLang(khac)}
      title={lang === "vi" ? "Switch to English" : "Chuyển sang Tiếng Việt"}
      aria-label="Đổi ngôn ngữ"
      className="inline-flex items-center gap-1.5 rounded-md border border-border-strong px-2 py-1 text-[12px] font-semibold text-text hover:border-brand-400 hover:bg-surface-2"
    >
      <svg viewBox="0 0 20 20" className="size-4 text-text-muted" fill="none">
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" strokeWidth="1.4" />
        <path d="M2.5 10h15M10 2.5c2.5 2.2 2.5 12.8 0 15M10 2.5c-2.5 2.2-2.5 12.8 0 15" stroke="currentColor" strokeWidth="1.2" />
      </svg>
      <span className="uppercase">{lang}</span>
    </button>
  );
}
