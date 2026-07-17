/** API client cho ② — giám sát hiệu lực + văn bản liên quan (vbpl.vn). */

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

export type HieuLucGS = {
  da_doi_chieu: boolean;
  con_hieu_luc: boolean | null;
  nhan: string;
  ma?: string | null;
};

export type LienQuan = { so_vb: string | null; title: string; loai: string };

export type CtGiamSat = {
  id: string;
  ten: string;
  so_hieu: string;
  co_quan: string;
  url?: string | null;
  hieu_luc: HieuLucGS;
  so_lien_quan: number;
  lien_quan: LienQuan[];
};

export type VanBanHet = {
  so_hieu: string | null;
  tieu_de: string;
  nam: number | null;
  co_quan: string;
  url?: string | null;
  nhan: string;
};

export type QuetHieuLuc = {
  n: number;
  n_het: number;
  n_con: number;
  tong_kho: number;
  het: VanBanHet[];
};

export type KetQuaGiamSat = {
  chuong_trinh: CtGiamSat[];
  quet?: QuetHieuLuc;
  nguon: string;
  cap_nhat: string;
};

export async function traGiamSat(): Promise<KetQuaGiamSat> {
  const r = await fetch(`${BFF}/giam-sat`);
  if (!r.ok) throw new Error(`Không tải được giám sát (${r.status})`);
  return r.json();
}
