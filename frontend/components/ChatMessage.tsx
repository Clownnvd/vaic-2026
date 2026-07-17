import type { DienGiai, Message, TrangThaiGrounding } from "@/lib/types";
import { CitationChip } from "./CitationChip";
import { ProgramCard } from "./ProgramCard";
import { VietTat } from "./VietTat";

/** ① Diễn giải luật do LLM sinh, đã qua GUARD lớp số — tô đỏ số bịa nếu có. */
function DienGiaiGuard({ dg }: { dg: DienGiai }) {
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

  return (
    <div
      className={
        "mt-2.5 rounded-xl border px-3.5 py-3 " +
        (dg.grounded
          ? "border-eligible-300 bg-eligible-50/60 dark:border-eligible-800 dark:bg-eligible-500/5"
          : "border-blocked-300 bg-blocked-50 dark:border-blocked-700 dark:bg-blocked-500/10")
      }
    >
      <div className="mb-1.5 flex items-center gap-1.5">
        <span
          className={
            "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold " +
            (dg.grounded
              ? "bg-eligible-100 text-eligible-700 dark:bg-eligible-500/15 dark:text-eligible-300"
              : "bg-blocked-100 text-blocked-700 dark:bg-blocked-500/15 dark:text-blocked-300")
          }
        >
          {dg.grounded ? "✓ Guard: số bám nguồn" : `⛔ Guard chặn: ${dg.soBia.length} số bịa`}
        </span>
        <span className="text-[10.5px] text-text-muted">LLM diễn giải · kiểm bằng lớp số tất định</span>
      </div>
      <p className="text-[13.5px] leading-relaxed text-text">
        {doan.map((d, k) =>
          d.do ? (
            <mark
              key={k}
              className="rounded bg-blocked-200 px-0.5 font-semibold text-blocked-800 line-through dark:bg-blocked-500/30 dark:text-blocked-200"
              title="Số này KHÔNG có trong căn cứ — guard tô đỏ"
            >
              {d.t}
            </mark>
          ) : (
            <VietTat key={k}>{d.t}</VietTat>
          ),
        )}
      </p>
      {dg.canhBao && (
        <p className="mt-1.5 text-[11.5px] font-medium text-blocked-700 dark:text-blocked-300">
          {dg.canhBao}
        </p>
      )}
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
  const g = GROUNDING[tt];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${g.cls}`}
    >
      {g.nhan}
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
          <div className="mb-2">
            <BadgeGrounding tt={m.grounding} />
          </div>
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
    return (
      <div className="max-w-[92%]">
        <BongBong>
          <p className="text-[14px] leading-relaxed text-text">{m.noiDung}</p>
        </BongBong>
      </div>
    );
  }

  // dang === "ket-qua" — khoảnh khắc bung thẻ xếp hạng
  return (
    <div className="max-w-[92%]">
      <BongBong>
        <p className="text-[14px] leading-relaxed text-text">{m.noiDung}</p>
        <p className="mt-1 text-[12px] text-text-muted">
          Đã quét {m.daQuet.toLocaleString("vi-VN")} văn bản · xếp theo giá trị kỳ vọng
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
