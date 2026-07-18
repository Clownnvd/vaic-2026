"use client";

import { useI18n } from "@/lib/i18n";
import type { ChuongTrinh, DieuKien } from "@/lib/types";
import { LOAI_NHAN } from "@/lib/types";
import { CitationChip } from "./CitationChip";

/** 3_400_000_000 → "~3,4 tỷ đ" — đọc được bằng mắt, không đếm số 0. */
export function dinhDangVND(n: number): string {
  if (n >= 1_000_000_000) {
    const ty = n / 1_000_000_000;
    return `${ty.toFixed(ty < 10 ? 1 : 0).replace(".", ",")} tỷ đ`;
  }
  if (n >= 1_000_000) return `${Math.round(n / 1_000_000)} triệu đ`;
  return `${n.toLocaleString("vi-VN")} đ`;
}

const TRANG_THAI_STYLE: Record<
  DieuKien["trangThai"],
  { icon: string; mau: string; nhan: string }
> = {
  dat: {
    icon: "✓",
    mau: "text-eligible-600 dark:text-eligible-300",
    nhan: "Đạt",
  },
  "khong-dat": {
    icon: "✕",
    mau: "text-blocked-600 dark:text-blocked-300",
    nhan: "Chưa đạt",
  },
  "chua-du-thong-tin": {
    icon: "?",
    mau: "text-caution-600 dark:text-caution-300",
    nhan: "Chưa đủ thông tin",
  },
};

function DongDieuKien({ dk }: { dk: DieuKien }) {
  const { t } = useI18n();
  const s = TRANG_THAI_STYLE[dk.trangThai];
  return (
    <li className="flex gap-2">
      <span
        aria-label={t(s.nhan)}
        className={`mt-px shrink-0 font-mono text-xs font-bold ${s.mau}`}
      >
        {s.icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] leading-snug text-text">{dk.yeuCau}</span>
        <span className="mt-0.5 block text-[12px] leading-snug text-text-muted">
          {t("Hồ sơ:")} {dk.hoSo}
        </span>
        <span className="mt-1 block">
          <CitationChip citation={dk.citation} />
        </span>
      </span>
    </li>
  );
}

export function ProgramCard({
  ct,
  hang,
}: {
  ct: ChuongTrinh;
  hang: number;
}) {
  const { t } = useI18n();
  // 3 trạng thái tất định — thiếu-tin KHÔNG được gộp vào "đủ". Ưu tiên xacQuyet
  // của backend; fallback cho dữ liệu cũ chưa có field này.
  const tt: "du" | "khong" | "gan_dat" =
    ct.xacQuyet ??
    (ct.duDieuKien === false
      ? "khong"
      : ct.doTinCay < 1 && ct.canBoSung && ct.canBoSung.length > 0
        ? "gan_dat"
        : "du");
  return (
    <article
      className="animate-card-in rounded-card border border-border-subtle bg-surface p-4 shadow-sm transition-shadow hover:shadow-md"
      style={{ animationDelay: `${hang * 60}ms` }}
    >
      <header className="flex items-start gap-3">
        <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-600 font-mono text-xs font-bold text-white">
          {hang + 1}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded border border-brand-200 bg-brand-50 px-1.5 py-0.5 text-[11px] font-medium text-brand-700 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-200">
              {t(LOAI_NHAN[ct.loai])}
            </span>
            <span className="text-[11px] text-text-muted">{ct.coQuan}</span>
          </div>
          <h3 className="mt-1 text-[15px] font-semibold leading-snug text-text">
            {ct.ten}
          </h3>
        </div>

        {(() => {
          // Ô góc phải: ưu tiên SỐ ĐỒNG (lượng hoá được) → "giá trị kỳ vọng".
          // Không có số thì hiện NHÃN MỨC HỖ TRỢ lấy từ nguyên văn (100%/miễn phí/
          // ≤50% lãi suất…) — KHÔNG bịa số, cũng KHÔNG để trống.
          const coSo = ct.giaTriHienThi || ct.giaTriKyVong !== null;
          if (!coSo && !ct.giaTriNhan) return null;
          const bituoc = ct.duDieuKien === false;
          return (
            <div className="shrink-0 text-right">
              <div
                className={`font-mono font-bold leading-none ${coSo ? "text-base" : "text-[15px]"} ${
                  bituoc
                    ? "text-ink-400 line-through dark:text-ink-500"
                    : "text-eligible-600 dark:text-eligible-300"
                }`}
              >
                {coSo ? `~${ct.giaTriHienThi ?? dinhDangVND(ct.giaTriKyVong ?? 0)}` : ct.giaTriNhan}
              </div>
              <div className="mt-1 text-[10px] uppercase tracking-wide text-text-muted">
                {coSo ? t("giá trị kỳ vọng") : t("mức hỗ trợ")}
              </div>
            </div>
          );
        })()}
      </header>

      {/* Phán quyết TẤT ĐỊNH — 3 trạng thái, KHÔNG gộp "thiếu tin" vào "đủ".
          • đủ    → thoả toàn bộ tiêu chí bắt buộc
          • chưa  → có điều kiện bắt buộc KHÔNG ĐẠT (nêu ĐÍCH DANH)
          • gần   → còn THIẾU TIN → liệt kê thứ cần bổ sung thành gạch đầu dòng */}
      {tt === "du" && (
        <div className="mt-2.5 rounded-md border border-eligible-300 bg-eligible-50 px-2.5 py-1.5 text-[12px] leading-snug text-eligible-700 dark:border-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300">
          <span className="font-semibold">{t("Đủ điều kiện")}</span> —{" "}
          {t("hồ sơ hiện tại thoả toàn bộ tiêu chí bắt buộc")}
        </div>
      )}

      {tt === "khong" && (
        <div className="mt-2.5 rounded-md border border-rose-300 bg-rose-50 px-2.5 py-1.5 text-[12px] leading-snug text-rose-700 dark:border-rose-800 dark:bg-rose-500/10 dark:text-rose-300">
          <span className="font-semibold">{t("Chưa đủ điều kiện")}</span>
          {ct.thieu?.length ? <> — {t("thiếu:")} {ct.thieu.join(" · ")}</> : null}
        </div>
      )}

      {tt === "gan_dat" && (
        <div className="mt-2.5 rounded-md border border-caution-300 bg-caution-50 px-2.5 py-2 text-[12px] leading-snug text-caution-700 dark:border-caution-700 dark:bg-caution-500/10 dark:text-caution-300">
          <div className="flex items-start gap-1.5">
            <svg viewBox="0 0 16 16" className="mt-0.5 size-3.5 shrink-0" fill="none">
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3" />
              <path d="M8 7.2v3.4M8 5.2v.2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <span>
              <span className="font-semibold">{t("Gần đạt tiêu chí")}</span> —{" "}
              {t("chưa xác nhận được vì hồ sơ còn thiếu thông tin")}
            </span>
          </div>
          {ct.canBoSung && ct.canBoSung.length > 0 && (
            <>
              <div className="mt-2 text-[10px] font-semibold uppercase tracking-wide opacity-80">
                {t("Cần bổ sung để xác nhận")}
              </div>
              <ul className="mt-1 space-y-1">
                {ct.canBoSung.map((x) => (
                  <li key={x.field} className="flex items-center gap-1.5">
                    <span className="size-1 shrink-0 rounded-full bg-current opacity-70" />
                    <span className="capitalize">{t(x.nhan)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <p className="mt-2.5 text-[13px] leading-relaxed text-text-muted">{ct.giaTri}</p>

      {ct.hanNop && (
        <p className="mt-1.5 flex items-center gap-1.5 text-[12px] text-text-muted">
          <svg viewBox="0 0 14 14" className="size-3 shrink-0" aria-hidden="true">
            <path
              fill="currentColor"
              d="M7 0a7 7 0 100 14A7 7 0 007 0zm.5 3v4.2l3 1.8-.5.9L6.5 7.8V3z"
            />
          </svg>
          {t("Hạn nộp:")} {ct.hanNop}
        </p>
      )}

      <div className="mt-3 border-t border-border-subtle pt-3">
        <h4 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">
          {t("Đối chiếu điều kiện")}
        </h4>
        <ul className="mt-2 space-y-2.5">
          {ct.dieuKien.map((dk, i) => (
            <DongDieuKien key={i} dk={dk} />
          ))}
        </ul>
      </div>

      <footer className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-border-subtle pt-2.5">
        <span className="flex items-center gap-1.5 text-[11px] text-text-muted">
          <span className="inline-block h-1 w-12 overflow-hidden rounded-full bg-ink-200 dark:bg-ink-700">
            <span
              className={`block h-full rounded-full ${
                tt === "du"
                  ? "bg-eligible-500"
                  : tt === "gan_dat"
                    ? "bg-caution-500"
                    : "bg-rose-500"
              }`}
              style={{ width: `${Math.round(ct.doTinCay * 100)}%` }}
            />
          </span>
          {tt === "du"
            ? t("Đủ tiêu chí")
            : tt === "gan_dat"
              ? t("Gần đạt tiêu chí")
              : t("Chưa đạt")}
        </span>

        {(() => {
          // Trạng thái hiệu lực THẬT từ vbpl.vn (② của đề). 3 trạng thái, KHÔNG
          // đoán: còn (xanh) / hết (đỏ) / chưa xác định (vàng). Nguồn: Bộ Tư pháp.
          const hl = ct.hieuLuc;
          if (!hl || !hl.daDoiChieu) {
            return (
              <span className="text-[11px] text-caution-700 dark:text-caution-300">
                ⚠ {t("Hiệu lực chưa đối chiếu vbpl.vn")}
              </span>
            );
          }
          if (hl.conHieuLuc === true) {
            return (
              <span
                className="text-[11px] text-emerald-700 dark:text-emerald-300"
                title={`${t("đối chiếu vbpl.vn")} (${hl.nguon ?? "Bộ Tư pháp"})${hl.soQuanHe ? ` · ${hl.soQuanHe} văn bản liên quan` : ""}`}
              >
                ✓ {t(hl.nhan)} — {t("đối chiếu vbpl.vn")}
              </span>
            );
          }
          if (hl.conHieuLuc === false) {
            return (
              <span className="text-[11px] font-medium text-rose-700 dark:text-rose-300">
                ⛔ {t(hl.nhan)} — vbpl.vn
              </span>
            );
          }
          return (
            <span className="text-[11px] text-caution-700 dark:text-caution-300">
              ⚠ {t(hl.nhan)}
            </span>
          );
        })()}
      </footer>
    </article>
  );
}
