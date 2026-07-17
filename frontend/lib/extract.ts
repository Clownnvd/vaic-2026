/**
 * ⚠️ TẠM THỜI — bóc hồ sơ bằng regex để chạy UI khi agent chưa wire.
 * Bản thật: slot-filling do agent lo (hiểu được câu nói tự nhiên, hỏi lại khi mơ hồ).
 * Giữ file này nhỏ và dễ xoá.
 */

import type { Profile } from "./types";

const NGANH_KEYWORDS: [RegExp, string][] = [
  [/phần mềm|software|lập trình|công nghệ thông tin|cntt/i, "Sản xuất phần mềm"],
  [/bán dẫn|chip|vi mạch/i, "Bán dẫn / vi mạch"],
  [/sinh học|biotech|dược/i, "Công nghệ sinh học"],
  [/cơ khí|chế tạo|sản xuất/i, "Sản xuất, chế tạo"],
  [/nông nghiệp|thuỷ sản|thủy sản/i, "Nông nghiệp công nghệ cao"],
  [/thương mại điện tử|e-?commerce|bán lẻ/i, "Thương mại điện tử"],
];

const DIA_BAN_KEYWORDS: [RegExp, string][] = [
  [/hà nội|ha noi|hn\b/i, "Hà Nội"],
  [/hồ chí minh|hcm|sài gòn|tphcm/i, "TP. Hồ Chí Minh"],
  [/đà nẵng|da nang/i, "Đà Nẵng"],
  [/hải phòng/i, "Hải Phòng"],
  [/bình dương/i, "Bình Dương"],
  [/bắc ninh/i, "Bắc Ninh"],
];

/** "20 tỷ" → 20e9 · "500 triệu" → 5e8 */
function bocTien(text: string): number | undefined {
  const m = text.match(/(\d+(?:[.,]\d+)?)\s*(tỷ|ty|tỉ|triệu|trieu)/i);
  if (!m) return undefined;
  const so = parseFloat(m[1].replace(",", "."));
  const donVi = m[2].toLowerCase();
  return /t[yỷỉ]/.test(donVi) ? so * 1_000_000_000 : so * 1_000_000;
}

export function bocHoSo(text: string, hienTai: Profile): Profile {
  const p: Profile = { ...hienTai };

  if (p.nganh === undefined) {
    for (const [re, nhan] of NGANH_KEYWORDS) {
      if (re.test(text)) {
        p.nganh = nhan;
        break;
      }
    }
  }

  if (p.diaBan === undefined) {
    for (const [re, nhan] of DIA_BAN_KEYWORDS) {
      if (re.test(text)) {
        p.diaBan = nhan;
        break;
      }
    }
  }

  // vốn: chỉ nhận khi có chữ "vốn" gần con số, tránh nuốt nhầm doanh thu
  if (p.von === undefined) {
    const m = text.match(/vốn[^.]{0,24}?(\d+(?:[.,]\d+)?\s*(?:tỷ|ty|tỉ|triệu|trieu))/i);
    if (m) p.von = bocTien(m[1]);
  }

  if (p.nhanSu === undefined) {
    const m = text.match(/(\d{1,5})\s*(?:người|nhân sự|nhân viên|lao động|nv)\b/i);
    if (m) p.nhanSu = parseInt(m[1], 10);
  }

  if (p.chiRDPhanTram === undefined) {
    const m =
      text.match(/(?:r&?d|nghiên cứu[^.]{0,16})[^.]{0,20}?(\d+(?:[.,]\d+)?)\s*%/i) ??
      text.match(/(\d+(?:[.,]\d+)?)\s*%[^.]{0,20}?(?:r&?d|nghiên cứu)/i);
    if (m) p.chiRDPhanTram = parseFloat(m[1].replace(",", "."));
  }

  if (p.fdi === undefined) {
    if (/không.{0,12}(fdi|vốn ngoại|nước ngoài)|thuần việt|100%\s*việt/i.test(text))
      p.fdi = false;
    else if (/\bfdi\b|vốn ngoại|vốn nước ngoài|có vốn đầu tư nước ngoài/i.test(text))
      p.fdi = true;
  }

  return p;
}

export function thieuTruong(p: Profile): (keyof Profile)[] {
  return (["nganh", "von", "nhanSu", "chiRDPhanTram", "diaBan", "fdi"] as const).filter(
    (k) => p[k] === undefined,
  );
}
