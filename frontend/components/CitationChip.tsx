"use client";

import { useState } from "react";
import type { Citation } from "@/lib/types";

/** Gộp điều–khoản–điểm thành nhãn ngắn: "NĐ 80/2021 · Điều 5 · Khoản 2" */
export function nhanNgan(c: Citation): string {
  const phan = [c.vanBan.replace(/^Nghị định /, "NĐ ").replace(/^Quyết định /, "QĐ ")];
  if (c.dieu) phan.push(c.dieu);
  if (c.khoan) phan.push(c.khoan);
  if (c.diem) phan.push(c.diem);
  return phan.join(" · ");
}

/**
 * Chip trích dẫn — bấm mở đoạn căn cứ.
 * Đây là thứ phân biệt matcher với chatbot: mọi khẳng định trỏ về được nguồn.
 */
export function CitationChip({ citation }: { citation: Citation }) {
  const [mo, setMo] = useState(false);
  const laPlaceholder = citation.trichDan.startsWith("[PLACEHOLDER");

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setMo((v) => !v)}
        aria-expanded={mo}
        className="inline-flex items-center gap-1 rounded-md border border-brand-200 bg-brand-50 px-1.5 py-0.5 font-mono text-[11px] leading-tight text-brand-700 transition-colors hover:bg-brand-100 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-200 dark:hover:bg-brand-900/70"
      >
        <svg viewBox="0 0 12 12" className="size-2.5 shrink-0" aria-hidden="true">
          <path
            fill="currentColor"
            d="M3 1h4.5L10 3.5V11H3zm4 .8V4h2.2zM4 5h4v1H4zm0 2h4v1H4z"
          />
        </svg>
        {nhanNgan(citation)}
      </button>

      {mo && (
        <span className="animate-card-in absolute bottom-full left-0 z-20 mb-1.5 block w-80 max-w-[85vw] rounded-lg border border-border-strong bg-surface p-3 text-left shadow-xl">
          <span className="block font-mono text-[11px] text-text-muted">
            {citation.vanBan}
            {citation.coQuan && ` — ${citation.coQuan}`}
          </span>
          <span className="mt-1.5 block border-l-2 border-brand-300 pl-2 text-[13px] leading-relaxed text-text">
            {citation.trichDan}
          </span>
          {laPlaceholder && (
            <span className="mt-2 block rounded bg-caution-50 px-2 py-1 text-[11px] text-caution-700 dark:bg-caution-500/10 dark:text-caution-300">
              ⚠ Chưa đối chiếu corpus — dữ liệu seed dựng UI
            </span>
          )}
          {citation.docId && (
            <span className="mt-2 block font-mono text-[10px] text-text-muted">
              {citation.docId}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
