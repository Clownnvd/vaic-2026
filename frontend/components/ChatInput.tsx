"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/lib/i18n";

export function ChatInput({
  onGui,
  dangBan,
  goiY = [],
}: {
  onGui: (text: string) => void;
  dangBan?: boolean;
  goiY?: string[];
}) {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  // tự nở theo nội dung (auto-grow) — cao dần tới trần rồi mới cuộn, dễ nhìn
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 240) + "px";
  }, [text]);

  function gui(v: string) {
    const t = v.trim();
    if (!t || dangBan) return;
    onGui(t);
    setText("");
  }

  return (
    <div className="border-t border-border-subtle bg-surface-2/85 backdrop-blur">
      <div className="mx-auto max-w-3xl px-4 py-3">
        {goiY.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {goiY.map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => gui(g)}
                disabled={dangBan}
                className="rounded-full border border-border-strong bg-surface px-3 py-1 text-[12px] text-text-muted transition-colors hover:border-brand-300 hover:text-brand-700 disabled:opacity-50 dark:hover:text-brand-300"
              >
                {g}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            gui(text);
          }}
          className="flex items-end gap-2"
        >
          <textarea
            ref={taRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                gui(text);
              }
            }}
            rows={1}
            placeholder={t("Mô tả doanh nghiệp của bạn, hoặc hỏi về một chương trình… (Shift+Enter để xuống dòng)")}
            className="min-h-[44px] flex-1 resize-none overflow-y-auto rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[14px] leading-relaxed text-text placeholder:text-text-muted focus:border-brand-400"
          />
          <button
            type="submit"
            disabled={dangBan || !text.trim()}
            className="h-[44px] shrink-0 rounded-lg bg-brand-600 px-4 text-[14px] font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {t("Gửi")}
          </button>
        </form>

        <p className="mt-1.5 text-[11px] text-text-muted">
          {t("PolicyRadar chỉ khẳng định điều gì có căn cứ trong kho văn bản. Thiếu căn cứ thì nói thẳng là chưa đủ căn cứ.")}
        </p>
      </div>
    </div>
  );
}
