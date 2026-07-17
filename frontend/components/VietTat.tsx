import { Fragment, type ReactNode } from "react";

/** Từ viết tắt chính sách → dạng đầy đủ. Mirror vn/context.py:VIET_TAT.
 *  Khoá viết HOA cho khớp cách người ta thường gõ. */
const VIET_TAT: Record<string, string> = {
  DNNVV: "doanh nghiệp nhỏ và vừa",
  "KH&CN": "khoa học và công nghệ",
  KHCN: "khoa học và công nghệ",
  BHXH: "bảo hiểm xã hội",
  FDI: "vốn đầu tư trực tiếp nước ngoài",
  "R&D": "nghiên cứu và phát triển",
  GCN: "giấy chứng nhận",
  TNDN: "thu nhập doanh nghiệp",
  GTGT: "giá trị gia tăng",
  ĐMST: "đổi mới sáng tạo",
  CNC: "công nghệ cao",
  CĐS: "chuyển đổi số",
  MST: "mã số thuế",
  SXKD: "sản xuất kinh doanh",
  UBND: "ủy ban nhân dân",
  HĐND: "hội đồng nhân dân",
  NIC: "Trung tâm Đổi mới sáng tạo Quốc gia",
  "NĐ-CP": "nghị định — Chính phủ",
  "QĐ-TTg": "quyết định — Thủ tướng Chính phủ",
  "QĐ-UBND": "quyết định — Ủy ban nhân dân",
  "NQ-HĐND": "nghị quyết — Hội đồng nhân dân",
  "TT-BKHCN": "thông tư — Bộ Khoa học và Công nghệ",
  "TT-BTC": "thông tư — Bộ Tài chính",
  "QH14": "Quốc hội khoá 14",
  "QH15": "Quốc hội khoá 15",
};

// sắp khoá dài trước để "KH&CN" thắng "KHCN", "NĐ-CP" thắng "NĐ"
const KHOA = Object.keys(VIET_TAT).sort((a, b) => b.length - a.length);
// escape ký tự regex trong khoá (& . -)
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\&]/g, "\\$&");
const RE = new RegExp(`(${KHOA.map(esc).join("|")})`, "g");

/**
 * Bọc mọi từ viết tắt trong `text` bằng <abbr> có tooltip full form.
 * Hover (hoặc chạm) hiện nghĩa đầy đủ — người đọc không cần biết trước từ tắt.
 */
export function VietTat({ children }: { children: string }): ReactNode {
  const text = children;
  const phan = text.split(RE);
  return (
    <>
      {phan.map((p, i) => {
        const day = VIET_TAT[p];
        if (day) {
          return (
            <abbr
              key={i}
              title={day}
              className="cursor-help underline decoration-dotted decoration-text-muted/60 underline-offset-2"
            >
              {p}
            </abbr>
          );
        }
        return <Fragment key={i}>{p}</Fragment>;
      })}
    </>
  );
}
