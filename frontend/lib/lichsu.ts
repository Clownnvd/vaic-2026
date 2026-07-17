/** Lịch sử chat — lưu localStorage, nhóm theo thời gian như Claude web. */

import type { Message, Profile } from "./types";

export type CuocTroChuyen = {
  id: string;
  tieuDe: string;
  messages: Message[];
  profile: Profile;
  taoLuc: number; // epoch ms
  suaLuc: number;
};

const KHOA = "policyradar.lichsu.v1";

export function taiLichSu(): CuocTroChuyen[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KHOA);
    if (!raw) return [];
    const ds = JSON.parse(raw) as CuocTroChuyen[];
    return Array.isArray(ds) ? ds.sort((a, b) => b.suaLuc - a.suaLuc) : [];
  } catch {
    return [];
  }
}

export function luuLichSu(ds: CuocTroChuyen[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(KHOA, JSON.stringify(ds));
  } catch {
    /* quota — bỏ qua */
  }
}

/** Tiêu đề từ câu người dùng đầu tiên (cắt gọn). */
export function datTieuDe(messages: Message[]): string {
  const u = messages.find((m) => m.vaiTro === "nguoi-dung");
  const t = (u?.noiDung ?? "").trim().replace(/\s+/g, " ");
  if (!t) return "Cuộc trò chuyện mới";
  return t.length > 48 ? t.slice(0, 48) + "…" : t;
}

/** Nhóm hội thoại theo mốc thời gian — Hôm nay / Hôm qua / 7 ngày / 30 ngày / Cũ hơn. */
export function nhomTheoThoiGian(
  ds: CuocTroChuyen[],
  mocNgay: number, // truyền Date.now() từ component (tránh gọi Date trong lib thuần)
): { nhan: string; items: CuocTroChuyen[] }[] {
  const NGAY = 86_400_000;
  const homNay = new Date(mocNgay).setHours(0, 0, 0, 0);
  const nhom: Record<string, CuocTroChuyen[]> = {
    "Hôm nay": [],
    "Hôm qua": [],
    "7 ngày qua": [],
    "30 ngày qua": [],
    "Cũ hơn": [],
  };
  for (const c of ds) {
    const d = c.suaLuc;
    if (d >= homNay) nhom["Hôm nay"].push(c);
    else if (d >= homNay - NGAY) nhom["Hôm qua"].push(c);
    else if (d >= homNay - 7 * NGAY) nhom["7 ngày qua"].push(c);
    else if (d >= homNay - 30 * NGAY) nhom["30 ngày qua"].push(c);
    else nhom["Cũ hơn"].push(c);
  }
  return Object.entries(nhom)
    .filter(([, v]) => v.length > 0)
    .map(([nhan, items]) => ({ nhan, items }));
}
