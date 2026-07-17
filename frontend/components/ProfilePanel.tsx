"use client";

import type { Profile } from "@/lib/types";
import { PROFILE_FIELDS } from "@/lib/types";
import { dinhDangVND } from "./ProgramCard";

function hienThi(key: keyof Profile, v: Profile[keyof Profile]): string {
  if (v === undefined || v === "") return "";
  if (key === "von" || key === "doanhThu") return dinhDangVND(v as number);
  if (key === "laoDongBhxh") return `${v} người`;
  if (key === "tyLeDtKhcn") return `${String(v).replace(".", ",")}% doanh thu`;
  if (key === "linhVuc")
    return v === "thuong_mai_dich_vu" ? "Thương mại - dịch vụ" : "Nông-lâm-thuỷ sản / CN-XD";
  if (key === "fdi" || key === "coGcnKhcn" || key === "nuLamChu") return v ? "Có" : "Không";
  return String(v);
}

/**
 * Panel HỒ SƠ dọc bên phải — giữ ngữ cảnh hiện hình suốt cuộc trò chuyện.
 * Biến "agent không mất context" thành thứ giám khảo NHÌN THẤY, thay vì tin lời.
 * Dòng đã điền = xanh; dòng còn trống = AI sẽ hỏi tiếp.
 */
export function ProfilePanel({ profile }: { profile: Profile }) {
  const daDien = PROFILE_FIELDS.filter((f) => profile[f.key] !== undefined).length;
  const tong = PROFILE_FIELDS.length;
  const pct = Math.round((daDien / tong) * 100);

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-l border-border-subtle bg-surface-2 lg:flex">
      <div className="border-b border-border-subtle px-4 py-3.5">
        <div className="flex items-center justify-between">
          <h2 className="text-[13px] font-semibold text-text">Hồ sơ doanh nghiệp</h2>
          <span className="text-[12px] font-medium text-text-muted">
            {daDien}/{tong}
          </span>
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border-subtle">
          <span
            className="block h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-1.5 text-[10.5px] leading-snug text-text-muted">
          Ngữ cảnh giữ suốt cuộc trò chuyện. Dòng trống → trợ lý sẽ hỏi tiếp.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {PROFILE_FIELDS.map((f) => {
          const giaTri = hienThi(f.key, profile[f.key]);
          const co = giaTri !== "";
          return (
            <div
              key={f.key}
              className={
                "flex items-start gap-2 rounded-lg px-2.5 py-2 " +
                (co ? "" : "opacity-70")
              }
            >
              <span
                className={
                  "mt-1 size-1.5 shrink-0 rounded-full " +
                  (co ? "bg-eligible-500" : "bg-border-strong")
                }
              />
              <div className="min-w-0 flex-1">
                <div className="text-[11px] leading-tight text-text-muted">{f.nhan}</div>
                <div
                  className={
                    "mt-0.5 text-[13px] leading-snug " +
                    (co ? "font-medium text-text" : "text-text-muted")
                  }
                >
                  {co ? giaTri : "— chưa có"}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
