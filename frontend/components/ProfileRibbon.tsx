import type { Profile } from "@/lib/types";
import { PROFILE_FIELDS } from "@/lib/types";
import { dinhDangVND } from "./ProgramCard";

function hienThi(key: keyof Profile, v: Profile[keyof Profile]): string {
  if (v === undefined || v === "") return "";
  if (key === "von" || key === "doanhThu") return dinhDangVND(v as number);
  if (key === "laoDongBhxh") return `${v} người`;
  if (key === "tyLeDtKhcn") return `${String(v).replace(".", ",")}% doanh thu`;
  if (key === "linhVuc")
    return v === "thuong_mai_dich_vu"
      ? "Thương mại - dịch vụ"
      : "Nông-lâm-thuỷ sản / CN-XD";
  if (key === "fdi" || key === "coGcnKhcn" || key === "nuLamChu") return v ? "Có" : "Không";
  return String(v);
}

/**
 * Ribbon hồ sơ — giữ ngữ cảnh hiện hình.
 * Đây là cách biến "agent không mất context" thành thứ giám khảo NHÌN THẤY,
 * thay vì phải tin lời. Chip xám = slot còn thiếu, AI sẽ hỏi tiếp.
 */
export function ProfileRibbon({ profile }: { profile: Profile }) {
  const daDien = PROFILE_FIELDS.filter((f) => profile[f.key] !== undefined).length;
  const tong = PROFILE_FIELDS.length;

  return (
    <div className="sticky top-0 z-10 border-b border-border-subtle bg-surface-2/85 backdrop-blur">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-1.5 px-4 py-2.5">
        <span className="mr-1 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
          Hồ sơ {daDien}/{tong}
        </span>

        {PROFILE_FIELDS.map((f) => {
          const giaTri = hienThi(f.key, profile[f.key]);
          const co = giaTri !== "";
          return (
            <span
              key={f.key}
              className={
                co
                  ? "inline-flex items-center gap-1 rounded-md border border-brand-200 bg-brand-50 px-2 py-0.5 text-[12px] text-brand-800 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-100"
                  : "inline-flex items-center gap-1 rounded-md border border-dashed border-border-strong px-2 py-0.5 text-[12px] text-text-muted"
              }
            >
              <span className="opacity-70">{f.nhan}:</span>
              <span className="font-medium">{co ? giaTri : "—"}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
