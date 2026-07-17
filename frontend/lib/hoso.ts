/** API client cho ③ — soạn hồ sơ xin tài trợ (structure-then-fill). */

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

export type OHoSo = {
  nhan: string;
  gia_tri: string | null;
  nguon: "ho_so" | "corpus" | "nguoi";
  da_dien: boolean;
  ai_duoc_go: boolean; // luôn false — bằng chứng AI không chạm ô nào
};

export type KhungHoSo = {
  ma: string;
  ten: string;
  can_cu: string;
  co_quan_nhan: string;
  han_nop: string | null;
  ghi_chu: string | null;
  phan_tram_day: number;
  thieu: string[];
  o: OHoSo[];
  van_ban: string;
};

export type KetQuaHoSo = {
  text: string;
  grounded: boolean;
  requires_approval: boolean;
  citations: { hien_thi: string; khoa: string }[];
  // BFF BỎ field này khi chương trình chưa gắn biểu mẫu nào → phải optional.
  khung?: KhungHoSo[];
  ms?: number;
};

export async function sinhHoSo(
  chuongTrinh: string,
  hoSo: Record<string, unknown>,
): Promise<KetQuaHoSo> {
  const r = await fetch(`${BFF}/ho-so/sinh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chuong_trinh: chuongTrinh, ho_so: hoSo }),
  });
  if (!r.ok) throw new Error(`Không sinh được hồ sơ (${r.status})`);
  return r.json();
}

export const NGUON_NHAN: Record<OHoSo["nguon"], { nhan: string; cls: string }> = {
  ho_so: {
    nhan: "Hệ thống điền từ hồ sơ DN",
    cls: "text-eligible-700 dark:text-eligible-300",
  },
  corpus: {
    nhan: "Điền từ văn bản (corpus)",
    cls: "text-brand-700 dark:text-brand-300",
  },
  nguoi: {
    nhan: "Doanh nghiệp tự khai",
    cls: "text-text-muted",
  },
};
