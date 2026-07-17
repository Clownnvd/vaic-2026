"use client";

import { useState } from "react";

export function ChatInput({
  onGui,
  dangBan,
  goiY = [],
}: {
  onGui: (text: string) => void;
  dangBan?: boolean;
  goiY?: string[];
}) {
  const [text, setText] = useState("");

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
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                gui(text);
              }
            }}
            rows={1}
            placeholder="Mô tả doanh nghiệp của bạn, hoặc hỏi về một chương trình…"
            className="max-h-40 min-h-[44px] flex-1 resize-y rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[14px] leading-relaxed text-text placeholder:text-text-muted focus:border-brand-400"
          />
          <button
            type="submit"
            disabled={dangBan || !text.trim()}
            className="h-[44px] shrink-0 rounded-lg bg-brand-600 px-4 text-[14px] font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Gửi
          </button>
        </form>

        <p className="mt-1.5 text-[11px] text-text-muted">
          PolicyRadar chỉ khẳng định điều gì có căn cứ trong kho văn bản. Thiếu căn cứ thì
          nói thẳng là chưa đủ căn cứ.
        </p>
      </div>
    </div>
  );
}
