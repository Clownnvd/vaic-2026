"use client";

import { useI18n } from "@/lib/i18n";
import type { DienGiai, Message, TrangThaiGrounding } from "@/lib/types";
import { CitationChip } from "./CitationChip";
import { ProgramCard } from "./ProgramCard";
import { VietTat } from "./VietTat";

/** ① Diễn giải luật do LLM sinh, đã qua GUARD lớp số — tô đỏ số bịa nếu có. */
function DienGiaiGuard({ dg }: { dg: DienGiai }) {
  const { t } = useI18n();
  // cắt text theo vị trí số bịa để tô đỏ đúng chỗ (bat_dau/ket_thuc từ guard)
  const bia = [...dg.soBia].sort((a, b) => a.batDau - b.batDau);
  const doan: { t: string; do: boolean }[] = [];
  let i = 0;
  for (const b of bia) {
    if (b.batDau > i) doan.push({ t: dg.text.slice(i, b.batDau), do: false });
    doan.push({ t: dg.text.slice(b.batDau, b.ketThuc), do: true });
    i = b.ketThuc;
  }
  doan.push({ t: dg.text.slice(i), do: false });

  const ok = dg.grounded;
  return (
    <div
      className={
        "mt-2.5 overflow-hidden rounded-xl border bg-surface shadow-sm " +
        (ok
          ? "border-eligible-200 dark:border-eligible-900"
          : "border-blocked-300 dark:border-blocked-800")
      }
    >
      {/* thanh tiêu đề guard */}
      <div
        className={
          "flex items-center gap-2 px-3.5 py-2 " +
          (ok
            ? "bg-eligible-50/70 dark:bg-eligible-500/10"
            : "bg-blocked-50 dark:bg-blocked-500/10")
        }
      >
        <span
          className={
            "flex size-5 items-center justify-center rounded-full " +
            (ok
              ? "bg-eligible-500 text-white"
              : "bg-blocked-500 text-white")
          }
        >
          {ok ? (
            <svg viewBox="0 0 16 16" className="size-3" fill="none">
              <path d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : (
            <svg viewBox="0 0 16 16" className="size-3" fill="none">
              <path d="M8 5v4M8 11.5v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          )}
        </span>
        <span className={"text-[12px] font-semibold " + (ok ? "text-eligible-800 dark:text-eligible-200" : "text-blocked-800 dark:text-blocked-200")}>
          {ok
            ? t("Đã kiểm chứng")
            : `${t("Guard chặn")} — ${dg.soBia.length} ${t("số không có căn cứ")}`}
        </span>
        <span className="ml-auto flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-text-muted">
          <svg viewBox="0 0 16 16" className="size-3.5" fill="none">
            <path d="M8 1.5l5 2v4c0 3-2.2 5.3-5 6.5-2.8-1.2-5-3.5-5-6.5v-4l5-2Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
          </svg>
          {t("Guard")}
        </span>
      </div>

      {/* nội dung diễn giải */}
      <div className="px-3.5 py-3">
        <p className="text-[13.5px] leading-relaxed text-text">
          {doan.map((d, k) =>
            d.do ? (
              <mark
                key={k}
                className="rounded bg-blocked-200 px-1 font-semibold text-blocked-800 line-through decoration-blocked-500 dark:bg-blocked-500/30 dark:text-blocked-100"
                title={t("Số này KHÔNG có trong căn cứ — guard tô đỏ")}
              >
                {d.t}
              </mark>
            ) : (
              <VietTat key={k}>{d.t}</VietTat>
            ),
          )}
        </p>
        {dg.canhBao && (
          <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-blocked-50 px-2.5 py-1.5 text-[11.5px] font-medium leading-snug text-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300">
            <span>⚠</span>
            <span>{dg.canhBao}</span>
          </p>
        )}
      </div>
    </div>
  );
}

const GROUNDING: Record<TrangThaiGrounding, { nhan: string; cls: string }> = {
  "du-can-cu": {
    nhan: "Đủ căn cứ",
    cls: "border-eligible-300 bg-eligible-50 text-eligible-700 dark:border-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300",
  },
  "chua-du-can-cu": {
    nhan: "Chưa đủ căn cứ",
    cls: "border-caution-300 bg-caution-50 text-caution-700 dark:border-caution-700 dark:bg-caution-500/10 dark:text-caution-300",
  },
  "guard-chan": {
    nhan: "Guard chặn",
    cls: "border-blocked-300 bg-blocked-50 text-blocked-700 dark:border-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300",
  },
};

function BadgeGrounding({ tt }: { tt: TrangThaiGrounding }) {
  const { t } = useI18n();
  const g = GROUNDING[tt];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${g.cls}`}
    >
      {t(g.nhan)}
    </span>
  );
}

function BongBong({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-card border border-border-subtle bg-surface px-4 py-3 shadow-sm">
      {children}
    </div>
  );
}

export function ChatMessage({ m }: { m: Message }) {
  if (m.vaiTro === "nguoi-dung") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-card bg-brand-600 px-4 py-2.5 text-[14px] leading-relaxed text-white shadow-sm">
          {m.noiDung}
        </div>
      </div>
    );
  }

  if (m.dang === "van-ban") {
    return (
      <div className="max-w-[92%]">
        <BongBong>
          {m.grounding && (
            <div className="mb-2">
              <BadgeGrounding tt={m.grounding} />
            </div>
          )}
          <p className="whitespace-pre-wrap text-[14px] leading-relaxed text-text">
            {m.noiDung}
          </p>

          {m.canhBao && (
            <p className="mt-2.5 rounded border border-blocked-300 bg-blocked-50 px-2.5 py-1.5 text-[12px] leading-snug text-blocked-700 dark:border-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300">
              {m.canhBao}
            </p>
          )}

          {m.citations && m.citations.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5 border-t border-border-subtle pt-2.5">
              {m.citations.map((c) => (
                <CitationChip key={c.id} citation={c} />
              ))}
            </div>
          )}
        </BongBong>
      </div>
    );
  }

  if (m.dang === "hoi-ho-so") {
    return <HoiHoSo m={m} />;
  }

  // dang === "ket-qua" — khoảnh khắc bung thẻ xếp hạng
  return <KetQua m={m} />;
}

function HoiHoSo({ m }: { m: Extract<Message, { dang: "hoi-ho-so" }> }) {
  const { t } = useI18n();
  return (
    <div className="max-w-[92%]">
      <BongBong>
        {/* t() dịch lời chào onboarding nếu có key; câu hỏi thật từ backend giữ nguyên tiếng Việt */}
        <p className="whitespace-pre-wrap text-[14px] leading-relaxed text-text">{t(m.noiDung)}</p>
      </BongBong>
    </div>
  );
}

function KetQua({ m }: { m: Extract<Message, { dang: "ket-qua" }> }) {
  const { t } = useI18n();
  return (
    <div className="max-w-[92%]">
      <BongBong>
        <p className="text-[14px] leading-relaxed text-text">{m.noiDung}</p>
        <p className="mt-1 text-[12px] text-text-muted">
          {t("Đã quét")} {m.daQuet.toLocaleString("vi-VN")} {t("văn bản · xếp theo giá trị kỳ vọng")}
        </p>
      </BongBong>

      {m.dienGiai && <DienGiaiGuard dg={m.dienGiai} />}

      <div className="mt-2.5 space-y-2.5">
        {m.chuongTrinh.map((ct, i) => (
          <ProgramCard key={ct.id} ct={ct} hang={i} />
        ))}
      </div>
    </div>
  );
}
