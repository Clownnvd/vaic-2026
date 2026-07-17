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
  const s = TRANG_THAI_STYLE[dk.trangThai];
  return (
    <li className="flex gap-2">
      <span
        aria-label={s.nhan}
        className={`mt-px shrink-0 font-mono text-xs font-bold ${s.mau}`}
      >
        {s.icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] leading-snug text-text">{dk.yeuCau}</span>
        <span className="mt-0.5 block text-[12px] leading-snug text-text-muted">
          Hồ sơ: {dk.hoSo}
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
              {LOAI_NHAN[ct.loai]}
            </span>
            <span className="text-[11px] text-text-muted">{ct.coQuan}</span>
          </div>
          <h3 className="mt-1 text-[15px] font-semibold leading-snug text-text">
            {ct.ten}
          </h3>
        </div>

        {(ct.giaTriHienThi || ct.giaTriKyVong !== null) && (
          <div className="shrink-0 text-right">
            <div
              className={`font-mono text-base font-bold leading-none ${
                ct.duDieuKien === false
                  ? "text-ink-400 line-through dark:text-ink-500"
                  : "text-eligible-600 dark:text-eligible-300"
              }`}
            >
              ~{ct.giaTriHienThi ?? dinhDangVND(ct.giaTriKyVong ?? 0)}
            </div>
            <div className="mt-1 text-[10px] uppercase tracking-wide text-text-muted">
              giá trị kỳ vọng
            </div>
          </div>
        )}
      </header>

      {/* Kết luận đủ / chưa đủ — TẤT ĐỊNH, không phải LLM đoán.
          Chưa đủ thì phải nêu ĐÍCH DANH điều kiện thiếu, không nói chung chung. */}
      {ct.duDieuKien !== undefined && (
        <div
          className={`mt-2.5 rounded-md border px-2.5 py-1.5 text-[12px] leading-snug ${
            ct.duDieuKien
              ? "border-eligible-300 bg-eligible-50 text-eligible-700 dark:border-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300"
              : "border-caution-300 bg-caution-50 text-caution-700 dark:border-caution-700 dark:bg-caution-500/10 dark:text-caution-300"
          }`}
        >
          {ct.duDieuKien ? (
            <>
              <span className="font-semibold">Đủ điều kiện</span> — hồ sơ hiện tại
              thoả toàn bộ tiêu chí bắt buộc
            </>
          ) : (
            <>
              <span className="font-semibold">Chưa đủ điều kiện</span>
              {ct.thieu?.length ? <> — thiếu: {ct.thieu.join(" · ")}</> : null}
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
          Hạn nộp: {ct.hanNop}
        </p>
      )}

      <div className="mt-3 border-t border-border-subtle pt-3">
        <h4 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">
          Vì sao đủ điều kiện
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
              className="block h-full rounded-full bg-brand-500"
              style={{ width: `${Math.round(ct.doTinCay * 100)}%` }}
            />
          </span>
          Độ tin cậy {Math.round(ct.doTinCay * 100)}%
        </span>

        {!ct.hieuLucDaDoiChieu && (
          <span className="text-[11px] text-caution-700 dark:text-caution-300">
            ⚠ Hiệu lực chưa đối chiếu vbpl.vn
          </span>
        )}
      </footer>
    </article>
  );
}
