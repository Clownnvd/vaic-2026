"use client";

import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { type CtGiamSat, type KetQuaGiamSat, traGiamSat } from "@/lib/giamsat";

/**
 * ② GIÁM SÁT chính sách — đối chiếu hiệu lực THẬT (vbpl.vn) + văn bản liên quan.
 * Nếu một văn bản chuyển sang HẾT hiệu lực → badge đỏ, DN được cảnh báo ngay
 * thay vì trích văn bản chết.
 */
export function GiamSat() {
  const { t } = useI18n();
  const [data, setData] = useState<KetQuaGiamSat | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState("");

  useEffect(() => {
    traGiamSat()
      .then(setData)
      .catch((e) => setLoi(e instanceof Error ? e.message : "Lỗi tải"))
      .finally(() => setDangTai(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-5 py-5">
        <div className="mb-4">
          <h2 className="text-[16px] font-semibold text-text">{t("Giám sát hiệu lực chính sách")}</h2>
          <p className="mt-1 text-[13px] leading-relaxed text-text-muted">
            {t("Mỗi văn bản được đối chiếu trạng thái hiệu lực")}{" "}
            <b>{t("trực tiếp với vbpl.vn (Bộ Tư pháp)")}</b>.{" "}
            {t("Khi một văn bản chuyển sang hết hiệu lực hoặc bị thay thế, hệ thống cảnh báo ngay — không để bạn nộp theo văn bản đã chết.")}
          </p>
          {data && (
            <p className="mt-1 text-[11px] text-text-muted">
              {t("Nguồn:")} {data.nguon} · {data.cap_nhat}
            </p>
          )}
        </div>

        {dangTai && <p className="text-[13px] text-text-muted">{t("Đang đối chiếu vbpl.vn…")}</p>}
        {loi && (
          <p className="rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[13px] text-blocked-600 dark:bg-blocked-500/10">
            {loi}
          </p>
        )}

        <div className="space-y-3">
          {data?.chuong_trinh.map((c) => (
            <CtCard key={c.id} c={c} />
          ))}
        </div>
      </div>
    </div>
  );
}

function BadgeHL({ c }: { c: CtGiamSat }) {
  const { t } = useI18n();
  const hl = c.hieu_luc;
  if (!hl.da_doi_chieu)
    return <Badge cls="border-caution-300 bg-caution-50 text-caution-700 dark:bg-caution-500/10 dark:text-caution-300" icon="?" nhan={t("Chưa đối chiếu")} />;
  if (hl.con_hieu_luc === true)
    return <Badge cls="border-eligible-300 bg-eligible-50 text-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300" icon="✓" nhan={t(hl.nhan)} />;
  if (hl.con_hieu_luc === false)
    return <Badge cls="border-blocked-300 bg-blocked-50 text-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300" icon="⛔" nhan={t(hl.nhan)} />;
  return <Badge cls="border-caution-300 bg-caution-50 text-caution-700 dark:bg-caution-500/10 dark:text-caution-300" icon="?" nhan={t(hl.nhan)} />;
}

function Badge({ cls, icon, nhan }: { cls: string; icon: string; nhan: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11.5px] font-semibold ${cls}`}>
      {icon} {nhan}
    </span>
  );
}

function CtCard({ c }: { c: CtGiamSat }) {
  const { t } = useI18n();
  const [mo, setMo] = useState(false);
  return (
    <article className="overflow-hidden rounded-xl border border-border-subtle bg-surface">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3">
        {c.url ? (
          <a
            href={c.url}
            target="_blank"
            rel="noreferrer"
            title={t("Mở bài gốc trên vbpl.vn")}
            className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-900/40 dark:text-brand-200"
          >
            {c.so_hieu}
            <svg viewBox="0 0 16 16" className="size-2.5" fill="none">
              <path d="M6 3h7v7M13 3l-8 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        ) : (
          <span className="rounded-md bg-brand-50 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
            {c.so_hieu}
          </span>
        )}
        <h3 className="text-[14px] font-medium text-text">{c.ten}</h3>
        <div className="ml-auto">
          <BadgeHL c={c} />
        </div>
      </div>

      <div className="border-t border-border-subtle px-4 py-2.5">
        <button
          onClick={() => setMo((v) => !v)}
          className="flex w-full items-center gap-1.5 text-[12.5px] font-medium text-text-muted hover:text-text"
        >
          <svg viewBox="0 0 16 16" className={"size-3.5 transition-transform " + (mo ? "rotate-90" : "")} fill="none">
            <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {c.so_lien_quan} {t("văn bản liên quan (căn cứ / thay thế / sửa đổi)")}
        </button>
        {mo && (
          <div className="mt-2 divide-y divide-border-subtle border-t border-border-subtle">
            {c.lien_quan.map((r, i) => (
              <div key={i} className="grid grid-cols-[132px_1fr] items-start gap-3 py-1.5 text-[12px]">
                <span
                  className={
                    "inline-flex w-full items-center justify-center rounded px-1.5 py-0.5 text-center text-[10px] font-medium " +
                    (r.loai.startsWith("Căn cứ")
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-200"
                      : "bg-caution-50 text-caution-700 dark:bg-caution-500/10 dark:text-caution-300")
                  }
                >
                  {r.loai}
                </span>
                <span className="leading-snug text-text">{r.title || r.so_vb || "—"}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
