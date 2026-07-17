/** API client cho "Danh sách luật" — tra cứu corpus (tìm kiếm + lọc + phân trang). */

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

export type VanBan = {
  item_id: string;
  so_hieu: string;
  tieu_de: string;
  doc_type: string;
  linh_vuc: string;
  co_quan: string;
  ngay_ban_hanh: string;
  nam: number | null;
  tom_tat: string;
  nguon_url: string;
};

export type TrangLuat = {
  tong: number;
  trang: number;
  so_trang: number;
  cs: number;
  van_ban: VanBan[];
};

export type Facet = { gia_tri: string; so_luong: number };
export type Facets = {
  doc_type: Facet[];
  linh_vuc: Facet[];
  co_quan: Facet[];
  nam: Facet[];
};

export type BoLoc = {
  q?: string;
  doc_type?: string;
  linh_vuc?: string;
  co_quan?: string;
  nam?: string;
  trang?: number;
  cs?: number;
};

export async function traLuat(loc: BoLoc): Promise<TrangLuat> {
  const p = new URLSearchParams();
  if (loc.q) p.set("q", loc.q);
  if (loc.doc_type) p.set("doc_type", loc.doc_type);
  if (loc.linh_vuc) p.set("linh_vuc", loc.linh_vuc);
  if (loc.co_quan) p.set("co_quan", loc.co_quan);
  if (loc.nam) p.set("nam", loc.nam);
  p.set("trang", String(loc.trang ?? 1));
  p.set("cs", String(loc.cs ?? 20));
  const r = await fetch(`${BFF}/luat?${p.toString()}`);
  if (!r.ok) throw new Error(`Không tải được danh sách luật (${r.status})`);
  return r.json();
}

export async function traFacets(): Promise<Facets> {
  const r = await fetch(`${BFF}/luat/facets`);
  if (!r.ok) throw new Error(`Không tải được bộ lọc (${r.status})`);
  return r.json();
}

/** Nhãn tiếng Việt cho doc_type (backend trả mã gạch dưới). */
export const NHAN_DOC_TYPE: Record<string, string> = {
  luat: "Luật",
  nghi_dinh: "Nghị định",
  thong_tu: "Thông tư",
  quyet_dinh: "Quyết định",
  nghi_quyet: "Nghị quyết",
};

export function nhanLoai(dt: string): string {
  return NHAN_DOC_TYPE[dt] ?? dt;
}
