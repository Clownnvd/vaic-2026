import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import "./globals.css";

// Be Vietnam Pro: có subset "vietnamese" — dấu ă/ơ/ư/đ render đúng một font,
// không rớt sang font hệ thống như Geist (chỉ có latin).
const beVietnam = Be_Vietnam_Pro({
  variable: "--font-be-vietnam",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PolicyRadar — tìm đúng chính sách ưu đãi doanh nghiệp đủ điều kiện",
  description:
    "Trợ lý chủ động hỏi hồ sơ doanh nghiệp rồi đưa ra danh sách chính sách ưu đãi và quỹ hỗ trợ đủ điều kiện, trích dẫn tới từng điều–khoản–điểm.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={`${beVietnam.variable} h-full`}>
      <body className="min-h-full">{children}</body>
    </html>
  );
}
