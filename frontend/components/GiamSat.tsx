"use client";

import { useEffect, useMemo, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { type CtGiamSat, type KetQuaGiamSat, type QuetHieuLuc, traGiamSat } from "@/lib/giamsat";

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

        {/* QUÉT KHO — bằng chứng giám sát BẮT ĐƯỢC văn bản đã hết hiệu lực */}
        {data?.quet && data.quet.n > 0 && <QuetKho q={data.quet} />}

        {data && data.chuong_trinh.length > 0 && (
          <h3 className="mb-2 mt-6 text-[13px] font-semibold text-text">
            {t("Chương trình bạn quan tâm — trạng thái hiện tại")}
          </h3>
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

/** Quét kho: đối chiếu vbpl.vn nhiều VB → BẢNG văn bản đã hết hiệu lực. */
function QuetKho({ q }: { q: QuetHieuLuc }) {
  const { t } = useI18n();
  const [tim, setTim] = useState("");
  const loc = useMemo(() => {
    const s = tim.trim().toLowerCase();
    if (!s) return q.het;
    return q.het.filter((v) =>
      `${v.so_hieu ?? ""} ${v.tieu_de} ${v.co_quan}`.toLowerCase().includes(s),
    );
  }, [tim, q.het]);
  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-border-subtle bg-surface">
      <div className="border-b border-border-subtle bg-surface-2/40 px-4 py-3">
        <h3 className="text-[13px] font-semibold text-text">
          {t("Quét kho — đối chiếu vbpl.vn phát hiện văn bản đã đổi trạng thái")}
        </h3>
        <div className="mt-2.5 flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-blocked-300 bg-blocked-50 px-2.5 py-1 text-[12.5px] font-semibold text-blocked-700 dark:border-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300">
            <span className="text-[15px] font-bold">{q.n_het}</span> {t("đã hết hiệu lực")}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-eligible-300 bg-eligible-50 px-2.5 py-1 text-[12.5px] font-semibold text-eligible-700 dark:border-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300">
            <span className="text-[15px] font-bold">{q.n_con}</span> {t("còn hiệu lực")}
          </span>
          <span className="inline-flex items-center gap-1 rounded-lg border border-border-strong bg-surface px-2.5 py-1 text-[12.5px] text-text-muted">
            {t("đã quét")} {q.n}/{q.tong_kho.toLocaleString("vi-VN")} {t("văn bản")}
          </span>
        </div>
        <p className="mt-2 text-[11.5px] leading-snug text-text-muted">
          {t("Nếu trợ lý trích các văn bản này mà không đối chiếu → doanh nghiệp nộp theo văn bản đã chết. Giám sát chặn đúng lỗi đó.")}
        </p>
      </div>

      {/* ô tìm + tiêu đề bảng */}
      <div className="flex flex-wrap items-center gap-2 border-t border-border-subtle px-4 py-2.5">
        <span className="text-[12.5px] font-medium text-text">
          {t("Danh sách văn bản đã hết hiệu lực")} ({loc.length})
        </span>
        <div className="relative ml-auto">
          <svg className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-text-muted" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.6" />
            <path d="m14 14 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          <input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder={t("Tìm số hiệu, tiêu đề, cơ quan…")}
            className="w-56 rounded-lg border border-border-strong bg-surface-2 py-1.5 pl-8 pr-3 text-[12px] text-text outline-none placeholder:text-text-muted focus:border-brand-500"
          />
        </div>
      </div>

      {/* BẢNG — căn cột như bảng thật */}
      <div className="max-h-[32rem] overflow-auto border-t border-border-subtle">
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-surface-2">
            <tr className="text-[10.5px] uppercase tracking-wide text-text-muted">
              <th className="border-b border-border-subtle px-4 py-2 font-semibold">{t("Số hiệu")}</th>
              <th className="border-b border-border-subtle px-3 py-2 font-semibold">{t("Văn bản")}</th>
              <th className="border-b border-border-subtle px-3 py-2 font-semibold">{t("Cơ quan")}</th>
              <th className="border-b border-border-subtle px-3 py-2 text-center font-semibold">{t("Năm")}</th>
              <th className="border-b border-border-subtle px-4 py-2 font-semibold">{t("Trạng thái")}</th>
            </tr>
          </thead>
          <tbody>
            {loc.map((v, i) => (
              <tr
                key={i}
                onClick={() => v.url && window.open(v.url, "_blank", "noreferrer")}
                className={
                  "border-b border-border-subtle/70 transition-colors " +
                  (v.url ? "cursor-pointer hover:bg-blocked-50/50 dark:hover:bg-blocked-500/5" : "")
                }
              >
                <td className="whitespace-nowrap px-4 py-2 align-top">
                  <span className="font-mono text-[11.5px] font-semibold text-blocked-700 dark:text-blocked-300">
                    {v.so_hieu || "—"}
                  </span>
                </td>
                <td className="px-3 py-2 align-top text-[12.5px] leading-snug text-text">
                  <span className="line-clamp-2">{v.tieu_de}</span>
                </td>
                <td className="px-3 py-2 align-top text-[11.5px] leading-snug text-text-muted">{v.co_quan}</td>
                <td className="whitespace-nowrap px-3 py-2 text-center align-top text-[11.5px] text-text-muted">{v.nam ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2 align-top">
                  <span className="inline-flex items-center gap-1 rounded-md border border-blocked-300 bg-blocked-50 px-1.5 py-0.5 text-[10px] font-medium text-blocked-700 dark:border-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300">
                    <span className="size-1.5 rounded-full bg-blocked-500" />
                    {v.nhan}
                  </span>
                </td>
              </tr>
            ))}
            {loc.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-[12.5px] text-text-muted">
                  {t("Không có văn bản nào khớp. Thử bỏ bớt bộ lọc.")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
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
