"use client";

import { useEffect, useMemo, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { type KetQuaGiamSat, type VanBanGS, traGiamSat } from "@/lib/giamsat";

const CS = 25;
const KHOA_SAO = "policyradar.giamsat.sao"; // localStorage: văn bản đã ghim (dấu sao)

/** Khoá ổn định cho 1 văn bản (ghim dấu sao) — ưu tiên id, rồi số hiệu, rồi tiêu đề. */
function khoaVb(v: VanBanGS): string {
  return String(v.id ?? v.so_hieu ?? v.tieu_de);
}

/**
 * ② GIÁM SÁT — MỘT bảng: mọi văn bản kho + trạng thái hiệu lực THẬT (vbpl.vn).
 * Tìm kiếm + lọc (trạng thái, năm, miền, tỉnh) + ghim (dấu sao) + phân trang.
 * Còn hiệu lực lên đầu, hết hiệu lực xuống cuối; văn bản đã ghim luôn ở trên cùng.
 */
export function GiamSat() {
  const { t } = useI18n();
  const [data, setData] = useState<KetQuaGiamSat | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState("");
  const [tim, setTim] = useState("");
  const [trangThai, setTrangThai] = useState<"" | "het" | "con">("");
  const [nam, setNam] = useState("");
  const [mien, setMien] = useState("");
  const [tinh, setTinh] = useState("");
  const [trang, setTrang] = useState(1);
  const [sao, setSao] = useState<Set<string>>(new Set());

  useEffect(() => {
    traGiamSat()
      .then(setData)
      .catch((e) => setLoi(e instanceof Error ? e.message : "Lỗi tải"))
      .finally(() => setDangTai(false));
    // nạp danh sách ghim đã lưu
    try {
      const raw = localStorage.getItem(KHOA_SAO);
      if (raw) setSao(new Set(JSON.parse(raw) as string[]));
    } catch {
      /* localStorage lỗi → bỏ qua, danh sách ghim rỗng */
    }
  }, []);

  function ghim(v: VanBanGS) {
    const k = khoaVb(v);
    setSao((cu) => {
      const moi = new Set(cu);
      if (moi.has(k)) moi.delete(k);
      else moi.add(k);
      try {
        localStorage.setItem(KHOA_SAO, JSON.stringify([...moi]));
      } catch {
        /* bỏ qua nếu localStorage không ghi được */
      }
      return moi;
    });
  }

  const dsNam = useMemo(() => {
    const s = new Set<number>();
    data?.van_ban.forEach((v) => v.nam && s.add(v.nam));
    return [...s].sort((a, b) => b - a);
  }, [data]);

  // tỉnh/thành có văn bản — thu hẹp theo miền đang chọn
  const dsTinh = useMemo(() => {
    const s = new Set<string>();
    data?.van_ban.forEach((v) => {
      if (v.tinh && (!mien || v.mien === mien)) s.add(v.tinh);
    });
    return [...s].sort((a, b) => a.localeCompare(b, "vi"));
  }, [data, mien]);

  const loc = useMemo(() => {
    let ds = data?.van_ban ?? [];
    if (trangThai === "het") ds = ds.filter((v) => v.con_hieu_luc === false);
    if (trangThai === "con") ds = ds.filter((v) => v.con_hieu_luc === true);
    if (nam) ds = ds.filter((v) => String(v.nam) === nam);
    if (mien) ds = ds.filter((v) => v.mien === mien);
    if (tinh) ds = ds.filter((v) => v.tinh === tinh);
    const q = tim.trim().toLowerCase();
    if (q) ds = ds.filter((v) => `${v.so_hieu ?? ""} ${v.tieu_de} ${v.co_quan}`.toLowerCase().includes(q));
    // GHIM lên đầu (giữ nguyên thứ tự còn→hết của backend trong mỗi nhóm)
    const co = ds.filter((v) => sao.has(khoaVb(v)));
    const khong = ds.filter((v) => !sao.has(khoaVb(v)));
    return [...co, ...khong];
  }, [data, trangThai, nam, mien, tinh, tim, sao]);

  const soTrang = Math.max(1, Math.ceil(loc.length / CS));
  const trangHt = Math.min(trang, soTrang);
  const hienThi = loc.slice((trangHt - 1) * CS, trangHt * CS);
  const coLoc = trangThai || nam || mien || tinh || tim;

  // đổi lọc thì về trang 1
  useEffect(() => setTrang(1), [trangThai, nam, mien, tinh, tim]);
  // đổi miền thì bỏ tỉnh đã chọn nếu không còn thuộc miền đó
  useEffect(() => {
    if (tinh && mien && !dsTinh.includes(tinh)) setTinh("");
  }, [mien, tinh, dsTinh]);

  return (
    <div className="flex h-full flex-col">
      {/* thanh tìm + lọc */}
      <div className="border-b border-border-subtle bg-surface px-5 py-3.5">
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-[200px] flex-1">
              <svg className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-muted" viewBox="0 0 20 20" fill="none">
                <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.6" />
                <path d="m14 14 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
              <input
                value={tim}
                onChange={(e) => setTim(e.target.value)}
                placeholder={t("Tìm số hiệu, tiêu đề, cơ quan…")}
                className="w-full rounded-lg border border-border-strong bg-surface-2 py-2 pl-9 pr-3 text-[13px] text-text outline-none placeholder:text-text-muted focus:border-brand-500"
              />
            </div>
            <Chon gt={mien} onChon={setMien}
              opts={[["", t("Miền") + ": " + t("tất cả")], ["Bắc", t("Miền Bắc")], ["Trung", t("Miền Trung")], ["Nam", t("Miền Nam")], ["Trung ương", t("Trung ương")]]} />
            <Chon gt={tinh} onChon={setTinh}
              opts={[["", t("Tỉnh/TP") + ": " + t("tất cả")], ...dsTinh.map((x) => [x, x] as [string, string])]} />
            <Chon gt={trangThai} onChon={(v) => setTrangThai(v as "" | "het" | "con")}
              opts={[["", t("Trạng thái") + ": " + t("tất cả")], ["con", t("Còn hiệu lực")], ["het", t("Hết hiệu lực")]]} />
            <Chon gt={nam} onChon={setNam}
              opts={[["", t("Năm") + ": " + t("tất cả")], ...dsNam.map((n) => [String(n), String(n)] as [string, string])]} />
            {coLoc && (
              <button
                onClick={() => { setTim(""); setTrangThai(""); setNam(""); setMien(""); setTinh(""); }}
                className="shrink-0 rounded-lg border border-border-subtle px-3 py-2 text-[12px] text-text-muted hover:bg-surface-2"
              >
                {t("Xoá lọc")}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* bảng */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-5 py-4">
          <div className="mb-2.5 flex items-center justify-between text-[12px] text-text-muted">
            <span>
              {dangTai ? t("Đang đối chiếu vbpl.vn…") : `${loc.length.toLocaleString("vi-VN")} ${t("văn bản")}`}
              {!dangTai && data && (
                <span className="ml-2 text-blocked-600 dark:text-blocked-300">· {data.n_het} {t("đã hết hiệu lực")}</span>
              )}
              {sao.size > 0 && (
                <span className="ml-2 text-amber-600 dark:text-amber-400">· {sao.size} {t("đã ghim")}</span>
              )}
            </span>
            {soTrang > 1 && <span>{t("Trang")} {trangHt}/{soTrang}</span>}
          </div>

          {loi && (
            <p className="rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[13px] text-blocked-600 dark:bg-blocked-500/10">{loi}</p>
          )}

          {!loi && (
            <div className="overflow-x-auto rounded-xl border border-border-subtle">
              <table className="w-full border-collapse text-left">
                <thead className="bg-surface-2">
                  <tr className="text-[10.5px] uppercase tracking-wide text-text-muted">
                    <th className="w-9 border-b border-border-subtle px-2 py-2.5 text-center font-semibold" aria-label={t("Ghim")}></th>
                    <th className="border-b border-border-subtle px-4 py-2.5 font-semibold">{t("Số hiệu")}</th>
                    <th className="border-b border-border-subtle px-3 py-2.5 font-semibold">{t("Văn bản")}</th>
                    <th className="border-b border-border-subtle px-3 py-2.5 font-semibold">{t("Cơ quan")}</th>
                    <th className="border-b border-border-subtle px-3 py-2.5 text-center font-semibold">{t("Năm")}</th>
                    <th className="border-b border-border-subtle px-4 py-2.5 font-semibold">{t("Trạng thái")}</th>
                  </tr>
                </thead>
                <tbody>
                  {hienThi.map((v, i) => (
                    <Dong key={khoaVb(v) + i} v={v} daGhim={sao.has(khoaVb(v))} onGhim={() => ghim(v)} />
                  ))}
                  {!dangTai && hienThi.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-10 text-center text-[13px] text-text-muted">
                      {t("Không có văn bản nào khớp. Thử bỏ bớt bộ lọc.")}
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {soTrang > 1 && (
            <div className="mt-4 flex items-center justify-center gap-1.5">
              <NutTrang mo={trangHt > 1} onClick={() => setTrang(trangHt - 1)}>‹</NutTrang>
              <span className="px-2 text-[12px] text-text-muted">{trangHt} / {soTrang}</span>
              <NutTrang mo={trangHt < soTrang} onClick={() => setTrang(trangHt + 1)}>›</NutTrang>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Dong({ v, daGhim, onGhim }: { v: VanBanGS; daGhim: boolean; onGhim: () => void }) {
  const { t } = useI18n();
  const het = v.con_hieu_luc === false;
  return (
    <tr
      onClick={() => v.url && window.open(v.url, "_blank", "noreferrer")}
      className={"border-b border-border-subtle/70 transition-colors " + (v.url ? "cursor-pointer hover:bg-surface-2/60" : "")}
    >
      <td className="px-2 py-2.5 text-center align-top">
        <button
          onClick={(e) => { e.stopPropagation(); onGhim(); }}
          aria-label={daGhim ? t("Bỏ ghim") : t("Ghim lên đầu")}
          title={daGhim ? t("Bỏ ghim") : t("Ghim lên đầu")}
          className={"rounded p-0.5 transition-colors " + (daGhim ? "text-amber-500" : "text-ink-300 hover:text-amber-400 dark:text-ink-600")}
        >
          <svg viewBox="0 0 20 20" className="size-4" fill={daGhim ? "currentColor" : "none"}>
            <path d="M10 2.5l2.35 4.76 5.25.76-3.8 3.7.9 5.23L10 14.98l-4.7 2.47.9-5.23-3.8-3.7 5.25-.76z"
              stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
          </svg>
        </button>
      </td>
      <td className="whitespace-nowrap px-4 py-2.5 align-top">
        <span className={"font-mono text-[11.5px] font-semibold " + (het ? "text-blocked-700 dark:text-blocked-300" : "text-brand-700 dark:text-brand-300")}>
          {v.so_hieu || "—"}
        </span>
      </td>
      <td className="px-3 py-2.5 align-top text-[12.5px] leading-snug text-text"><span className="line-clamp-2">{v.tieu_de}</span></td>
      <td className="px-3 py-2.5 align-top text-[11.5px] leading-snug text-text-muted">{v.co_quan}</td>
      <td className="whitespace-nowrap px-3 py-2.5 text-center align-top text-[11.5px] text-text-muted">{v.nam ?? "—"}</td>
      <td className="whitespace-nowrap px-4 py-2.5 align-top">
        <span className={
          "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium " +
          (het
            ? "border-blocked-300 bg-blocked-50 text-blocked-700 dark:border-blocked-700 dark:bg-blocked-500/10 dark:text-blocked-300"
            : "border-eligible-300 bg-eligible-50 text-eligible-700 dark:border-eligible-700 dark:bg-eligible-500/10 dark:text-eligible-300")
        }>
          <span className={"size-1.5 rounded-full " + (het ? "bg-blocked-500" : "bg-eligible-500")} />
          {v.nhan}
        </span>
      </td>
    </tr>
  );
}

function Chon({ gt, onChon, opts }: { gt: string; onChon: (v: string) => void; opts: [string, string][] }) {
  const co = gt !== "";
  return (
    <div className="relative">
      <select
        value={gt}
        onChange={(e) => onChon(e.target.value)}
        className={
          "cursor-pointer appearance-none rounded-lg border py-2 pl-3 pr-8 text-[12px] outline-none focus:border-brand-500 " +
          (co ? "border-brand-300 bg-brand-50 text-brand-800 dark:border-brand-700 dark:bg-brand-900/40 dark:text-brand-100" : "border-border-strong bg-surface-2 text-text-muted")
        }
      >
        {opts.map(([v, nhan]) => <option key={v} value={v}>{nhan}</option>)}
      </select>
      <svg className="pointer-events-none absolute right-2.5 top-1/2 size-3.5 -translate-y-1/2 text-text-muted" viewBox="0 0 20 20" fill="none">
        <path d="m6 8 4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    </div>
  );
}

function NutTrang({ mo, onClick, children }: { mo: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      disabled={!mo}
      className="min-w-8 rounded-md border border-border-strong px-2 py-1 text-[13px] text-text-muted transition-colors hover:bg-surface-2 disabled:opacity-40"
    >
      {children}
    </button>
  );
}
