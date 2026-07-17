/** API client cho ② — giám sát hiệu lực + văn bản liên quan (vbpl.vn). */

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

export type VanBanGS = {
  so_hieu: string | null;
  tieu_de: string;
  nam: number | null;
  co_quan: string;
  url?: string | null;
  nhan: string;
  con_hieu_luc: boolean | null;
};

export type KetQuaGiamSat = {
  van_ban: VanBanGS[];
  n_het: number;
  n_con: number;
  tong_kho: number;
  nguon: string;
  cap_nhat: string;
};

export async function traGiamSat(): Promise<KetQuaGiamSat> {
  const r = await fetch(`${BFF}/giam-sat`);
  if (!r.ok) throw new Error(`Không tải được giám sát (${r.status})`);
  return r.json();
}
