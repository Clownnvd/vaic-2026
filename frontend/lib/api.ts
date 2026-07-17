/**
 * Gọi BFF — cửa DUY NHẤT ra backend.
 *
 * Frontend KHÔNG được gọi thẳng LLM/corpus:
 *  • key nằm trong browser thì ai mở DevTools cũng thấy
 *  • che PII phải làm server-side, kẻo PII bay ra trước khi kịp che
 *  • guard phải không lách được — gọi thẳng LLM = bỏ qua guard
 *  • ràng buộc J: mọi LLM call qua proxy có log
 */

import type { Profile } from "./types";

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

/** Citation trả về từ BFF — đã ràng theo vết tra cứu thật, không phải LLM tự khai. */
export type ApiCitation = {
  hien_thi: string;
  khoa: string;
  trich: string;
  doc_id: string | null;
  url?: string | null; // source_url vbpl.vn — bấm mở bài gốc
};

export type ApiDieuKien = {
  yeu_cau: string;
  trang_thai: "dat" | "khong_dat" | "thieu_tin";
  doi_chieu: string;
  citation: ApiCitation;
};

export type ApiHieuLuc = {
  da_doi_chieu: boolean;
  con_hieu_luc: boolean | null; // null = chưa xác định (KHÔNG đoán)
  nhan: string;
  ma?: string;
  so_quan_he?: number;
  nguon?: string;
};

export type ApiChuongTrinh = {
  id: string;
  ten: string;
  co_quan: string;
  loai: string; // "ho_tro_chi_phi" | "uu_dai_thue" ... (gạch dưới, đổi sang gạch ngang ở UI)
  gia_tri: string;
  gia_tri_ky_vong: string;
  han_nop: string | null;
  du_dieu_kien: boolean;
  do_tin_cay: number;
  thieu: string[];
  can_hoi_them: string[];
  dieu_kien: ApiDieuKien[];
  hieu_luc?: ApiHieuLuc;
};

/** Hồ sơ backend trích được (GPT) — snake_case, gửi kèm mọi phản hồi để UI đồng bộ. */
export type ApiHoSoMoi = Record<string, unknown>;

export type ApiTraLoi =
  | {
      dang: "van_ban";
      noi_dung: string;
      text?: string;
      grounded?: boolean;
      ho_so_moi?: ApiHoSoMoi;
      pii_da_che: string[];
      ms: number;
    }
  | {
      dang: "hoi_ho_so";
      noi_dung: string;
      dang_hoi: string[];
      ho_so_moi?: ApiHoSoMoi;
      pii_da_che: string[];
      ms: number;
    }
  | {
      dang: "ket_qua";
      noi_dung: string;
      chuong_trinh: ApiChuongTrinh[];
      dien_giai?: ApiDienGiai | null;
      ho_so_moi?: ApiHoSoMoi;
      pii_da_che: string[];
      ms: number;
    };

/** Map hồ sơ backend (snake) → Profile UI (camel) — GPT trích ở server, UI hiện lại. */
export function sangUI(hs: ApiHoSoMoi): Partial<Profile> {
  const p: Record<string, unknown> = {};
  const m: Record<string, string> = {
    nganh: "nganh", linh_vuc: "linhVuc", von: "von", doanh_thu: "doanhThu",
    lao_dong_bhxh: "laoDongBhxh", ty_le_dt_khcn: "tyLeDtKhcn",
    co_gcn_khcn: "coGcnKhcn", nu_lam_chu: "nuLamChu", dia_ban: "diaBan", fdi: "fdi",
  };
  for (const [k, v] of Object.entries(hs)) {
    if (k in m && v !== null && v !== undefined) p[m[k]] = v;
  }
  return p as Partial<Profile>;
}

/** Diễn giải LLM (① interpreting) + phán quyết guard lớp số. */
export type ApiDienGiai = {
  text: string;
  grounded: boolean;
  so_bia: { raw: string; loai: string; bat_dau: number; ket_thuc: number }[];
  guard: string;
  canh_bao: string | null;
};

/** Map Profile của UI → khoá backend (UI dùng camelCase, backend snake_case). */
function sangBackend(p: Profile): Record<string, unknown> {
  const ra: Record<string, unknown> = {};
  if (p.nganh !== undefined) ra.nganh = p.nganh;
  if (p.linhVuc !== undefined) ra.linh_vuc = p.linhVuc;
  if (p.von !== undefined) ra.von = p.von;
  if (p.doanhThu !== undefined) ra.doanh_thu = p.doanhThu;
  if (p.laoDongBhxh !== undefined) ra.lao_dong_bhxh = p.laoDongBhxh;
  if (p.tyLeDtKhcn !== undefined) ra.ty_le_dt_khcn = p.tyLeDtKhcn;
  if (p.coGcnKhcn !== undefined) ra.co_gcn_khcn = p.coGcnKhcn;
  if (p.nuLamChu !== undefined) ra.nu_lam_chu = p.nuLamChu;
  if (p.diaBan !== undefined) ra.dia_ban = p.diaBan;
  if (p.fdi !== undefined) ra.fdi = p.fdi;
  return ra;
}

export class BffLoi extends Error {}

export async function hoiBff(cau: string, profile: Profile): Promise<ApiTraLoi> {
  let r: Response;
  try {
    r = await fetch(`${BFF}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cau, ho_so: sangBackend(profile) }),
    });
  } catch {
    throw new BffLoi(
      `Không kết nối được backend (${BFF}). Kiểm tra BFF đã chạy chưa.`,
    );
  }
  if (!r.ok) throw new BffLoi(`Backend trả lỗi ${r.status}`);
  return (await r.json()) as ApiTraLoi;
}
