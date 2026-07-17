import type { Message, TrangThaiGrounding } from "@/lib/types";
import { CitationChip } from "./CitationChip";
import { ProgramCard } from "./ProgramCard";

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

      <div className="mt-2.5 space-y-2.5">
        {m.chuongTrinh.map((ct, i) => (
          <ProgramCard key={ct.id} ct={ct} hang={i} />
        ))}
      </div>
    </div>
  );
}
