/**
 * Bóc hồ sơ từ câu nói tự nhiên — CHỊU ĐƯỢC GÕ KHÔNG DẤU (H1 của đề).
 *
 * ⚠️ SỬA LỖI THẬT: bản cũ khớp regex trực tiếp trên text có dấu, nên câu gõ
 * không dấu ("cong nghiep", "von 20 ty", "lao dong", "giay chung nhan") TRƯỢT
 * hết → bot hỏi lại đúng thứ vừa khai → cảm giác "không đồng nhất".
 * Nay: BỎ DẤU cả câu trước khi khớp, và mọi pattern viết ở dạng KHÔNG DẤU.
 * Giá trị lấy ra là SỐ (không phụ thuộc dấu) hoặc nhãn cố định → bỏ dấu an toàn.
 */

import type { Profile } from "./types";

/** Bỏ dấu tiếng Việt + hạ chữ thường — để khớp kiểu gõ-không-dấu. */
function boDau(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

// pattern viết KHÔNG DẤU (vì khớp trên chuỗi đã boDau)
const NGANH_KEYWORDS: [RegExp, string][] = [
  [/phan mem|software|lap trinh|cong nghe thong tin|cntt/, "Sản xuất phần mềm"],
  [/ban dan|chip|vi mach/, "Bán dẫn / vi mạch"],
  [/sinh hoc|biotech|duoc/, "Công nghệ sinh học"],
  [/co khi|che tao|san xuat/, "Sản xuất, chế tạo"],
  [/nong nghiep|thuy san/, "Nông nghiệp công nghệ cao"],
  [/thuong mai dien tu|e-?commerce|ban le/, "Thương mại điện tử"],
];

const DIA_BAN_KEYWORDS: [RegExp, string][] = [
  [/ha noi|\bhn\b/, "Hà Nội"],
  [/ho chi minh|hcm|sai gon|tphcm/, "TP. Hồ Chí Minh"],
  [/da nang/, "Đà Nẵng"],
  [/hai phong/, "Hải Phòng"],
  [/binh duong/, "Bình Dương"],
  [/bac ninh/, "Bắc Ninh"],
];

/** "20 ty" → 20e9 · "500 trieu" → 5e8 (khớp trên chuỗi đã bỏ dấu). */
function bocTien(t: string): number | undefined {
  const m = t.match(/(\d+(?:[.,]\d+)?)\s*(ty|tr|trieu)/);
  if (!m) return undefined;
  const so = parseFloat(m[1].replace(",", "."));
  return /ty/.test(m[2]) ? so * 1_000_000_000 : so * 1_000_000;
}

export function bocHoSo(text: string, hienTai: Profile): Profile {
  const p: Profile = { ...hienTai };
  const t = boDau(text); // tất cả khớp trên chuỗi KHÔNG DẤU

  if (p.nganh === undefined) {
    for (const [re, nhan] of NGANH_KEYWORDS)
      if (re.test(t)) {
        p.nganh = nhan;
        break;
      }
  }

  if (p.diaBan === undefined) {
    for (const [re, nhan] of DIA_BAN_KEYWORDS)
      if (re.test(t)) {
        p.diaBan = nhan;
        break;
      }
  }

  // vốn — có chữ "von" gần số, tránh nuốt nhầm doanh thu
  if (p.von === undefined) {
    const m = t.match(/von[^.]{0,24}?(\d+(?:[.,]\d+)?\s*(?:ty|tr|trieu))/);
    if (m) p.von = bocTien(m[1]);
  }

  // doanh thu — Điều 5 dùng doanh thu ở mọi ngưỡng
  if (p.doanhThu === undefined) {
    const m = t.match(/(?:doanh thu|doanh so)[^.]{0,24}?(\d+(?:[.,]\d+)?\s*(?:ty|tr|trieu))/);
    if (m) p.doanhThu = bocTien(m[1]);
  }

  // lao động BHXH — "lao dong", "nguoi", "nhan su"…
  if (p.laoDongBhxh === undefined) {
    const m = t.match(/(\d{1,5})\s*(?:nguoi|nhan su|nhan vien|lao dong|nv)\b/);
    if (m) p.laoDongBhxh = parseInt(m[1], 10);
  }

  // tỷ lệ doanh thu từ sản phẩm KH&CN (13/2019 Đ12 K3, ngưỡng 30%).
  // KHÔNG trộn với "chi R&D": R&D là tiền BỎ RA, đây là doanh thu THU VỀ.
  if (p.tyLeDtKhcn === undefined) {
    const m =
      t.match(/(?:doanh thu[^.]{0,20}?(?:kh&?cn|khcn|khoa hoc|san pham khcn))[^.]{0,20}?(\d+(?:[.,]\d+)?)\s*%/) ??
      t.match(/(\d+(?:[.,]\d+)?)\s*%[^.]{0,24}?doanh thu[^.]{0,16}?(?:kh&?cn|khcn|khoa hoc)/);
    if (m) p.tyLeDtKhcn = parseFloat(m[1].replace(",", "."));
  }

  // có/không Giấy chứng nhận DN KH&CN
  if (p.coGcnKhcn === undefined) {
    if (/(chua|khong)[^.]{0,20}(giay chung nhan|gcn)[^.]{0,16}(kh&?cn|khcn|khoa hoc)/.test(t))
      p.coGcnKhcn = false;
    else if (/(co|duoc cap)?[^.]{0,10}(giay chung nhan|gcn)[^.]{0,16}(kh&?cn|khcn|khoa hoc)/.test(t))
      p.coGcnKhcn = true;
  }

  // lĩnh vực — 2 nhóm Điều 5. Thương mại-dịch vụ ưu tiên xét trước.
  if (p.linhVuc === undefined) {
    if (/thuong mai|dich vu|ban le|ban buon|logistics|du lich/.test(t))
      p.linhVuc = "thuong_mai_dich_vu";
    else if (/nong nghiep|lam nghiep|thuy san|cong nghiep|xay dung|san xuat|che bien/.test(t))
      p.linhVuc = "nong_lam_thuy_san__cong_nghiep_xay_dung";
  }

  // nữ làm chủ / nhiều lao động nữ / DN xã hội (Điều 13 K2 nâng trần)
  if (p.nuLamChu === undefined) {
    if (/phu nu lam chu|nu lam chu|nhieu lao dong nu|doanh nghiep xa hoi/.test(t)) p.nuLamChu = true;
  }

  // FDI
  if (p.fdi === undefined) {
    if (/khong[^.]{0,12}(fdi|von ngoai|nuoc ngoai)|thuan viet|100%\s*viet/.test(t)) p.fdi = false;
    else if (/\bfdi\b|von ngoai|von nuoc ngoai|co von dau tu nuoc ngoai/.test(t)) p.fdi = true;
  }

  return p;
}

/** Field còn thiếu — CHỈ những thứ kho THẬT SỰ cần, không bắt khai cho đủ bộ. */
export function thieuTruong(p: Profile): (keyof Profile)[] {
  return (["linhVuc", "laoDongBhxh", "doanhThu", "tyLeDtKhcn", "coGcnKhcn"] as const).filter(
    (k) => p[k] === undefined,
  );
}
