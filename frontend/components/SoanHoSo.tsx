"use client";

import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import {
  type KetQuaHoSo,
  type KhungHoSo,
  type OHoSo,
  NGUON_NHAN,
  sinhHoSo,
} from "@/lib/hoso";
import type { Profile } from "@/lib/types";

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

type CtItem = { id: string; ten: string; co_quan: string; so_bieu_mau?: number };

/** UI Profile (camelCase) → khoá backend (snake) khi sinh hồ sơ. */
function sangBackend(p: Profile): Record<string, unknown> {
  const r: Record<string, unknown> = {};
  if (p.nganh) r.nganh = p.nganh;
  if (p.linhVuc) r.linh_vuc = p.linhVuc;
  if (p.von !== undefined) r.von = p.von;
  if (p.doanhThu !== undefined) r.doanh_thu = p.doanhThu;
  if (p.laoDongBhxh !== undefined) r.lao_dong_bhxh = p.laoDongBhxh;
  if (p.tyLeDtKhcn !== undefined) r.ty_le_dt_khcn = p.tyLeDtKhcn;
  return r;
}

/**
 * ③ SOẠN HỒ SƠ — accordion 2 tầng:
 *   Chương trình (dropdown dọc) → các văn bản/biểu mẫu → bấm mở FORM ĐIỀN ĐƯỢC.
 * CODE điền sẵn phần biết chắc (từ hồ sơ DN), người dùng sửa/khai nốt.
 * Luôn là bản nháp chờ duyệt (write-gate).
 */
export function SoanHoSo({ profile, moId }: { profile: Profile; moId?: string }) {
  const { t } = useI18n();
  const [ct, setCt] = useState<CtItem[]>([]);
  const [moCt, setMoCt] = useState<string>(""); // chương trình đang mở
  const [khungTheoCt, setKhungTheoCt] = useState<Record<string, KetQuaHoSo>>({});
  const [dangTai, setDangTai] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // dùng /ho-so/chuong-trinh (gồm NAFOSTED + số biểu mẫu hiện ngay), không phải
    // /chuong-trinh (chỉ 2 chương trình matcher).
    fetch(`${BFF}/ho-so/chuong-trinh`)
      .then((r) => r.json())
      .then((d) => setCt(d.chuong_trinh ?? []))
      .catch(() => {});
  }, []);

  async function moChuongTrinh(id: string) {
    const dangMo = moCt === id;
    setMoCt(dangMo ? "" : id);
    if (!dangMo && !khungTheoCt[id]) {
      setDangTai((s) => ({ ...s, [id]: true }));
      try {
        const kq = await sinhHoSo(id, sangBackend(profile));
        setKhungTheoCt((s) => ({ ...s, [id]: kq }));
      } catch {
        /* bỏ qua — hiện thông báo bên dưới */
      } finally {
        setDangTai((s) => ({ ...s, [id]: false }));
      }
    }
  }

  // Mở SẴN gói được chỉ định (bấm "Điền hồ sơ" từ thẻ chương trình) khi danh
  // sách đã tải. Chỉ mở, không đóng — nên gate bằng moCt !== moId.
  useEffect(() => {
    if (moId && ct.some((c) => c.id === moId) && moCt !== moId) {
      moChuongTrinh(moId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moId, ct]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-5 py-5">
        <div className="mb-4">
          <h2 className="text-[16px] font-semibold text-text">{t("Soạn hồ sơ xin tài trợ")}</h2>
          <p className="mt-1 text-[13px] leading-relaxed text-text-muted">
            {t("Chọn chương trình để xem bộ văn bản cần nộp. Bấm từng văn bản để mở biểu mẫu điền — hệ thống điền sẵn phần biết chắc từ hồ sơ doanh nghiệp, bạn khai nốt phần còn lại.")}
            <b> {t("Mọi bản đều là bản nháp chờ bạn duyệt.")}</b>
          </p>
        </div>

        <div className="space-y-2.5">
          {ct.map((c) => {
            const mo = moCt === c.id;
            const kq = khungTheoCt[c.id];
            return (
              <div key={c.id} className="overflow-hidden rounded-xl border border-border-subtle bg-surface">
                {/* HEADER chương trình = dropdown */}
                <button
                  onClick={() => moChuongTrinh(c.id)}
                  className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-surface-2"
                >
                  <svg viewBox="0 0 16 16" className={"size-4 shrink-0 text-text-muted transition-transform " + (mo ? "rotate-90" : "")} fill="none">
                    <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="min-w-0 flex-1">
                    <div className="text-[14px] font-semibold text-text">{c.ten}</div>
                    <div className="text-[11.5px] text-text-muted">{c.co_quan}</div>
                  </div>
                  {/* số biểu mẫu HIỆN NGAY (từ so_bieu_mau, không đợi mở) */}
                  {(c.so_bieu_mau ?? kq?.khung?.length) !== undefined && (
                    <span className="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
                      {kq?.khung?.length ?? c.so_bieu_mau} {t("văn bản")}
                    </span>
                  )}
                </button>

                {/* THÂN — danh sách văn bản */}
                {mo && (
                  <div className="border-t border-border-subtle bg-surface-2/40 px-2 py-2">
                    {dangTai[c.id] && (
                      <p className="px-3 py-2 text-[12.5px] text-text-muted">{t("Đang dựng bộ hồ sơ…")}</p>
                    )}
                    {kq && !kq.khung?.length && (
                      <p className="px-3 py-2 text-[12.5px] text-text-muted">
                        {kq.text || t("Chương trình này chưa gắn biểu mẫu trong kho.")}
                      </p>
                    )}
                    {kq?.khung?.map((k) => (
                      <VanBanForm key={k.ma} k={k} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/** Một văn bản = hàng bấm mở → form điền được. */
function VanBanForm({ k }: { k: KhungHoSo }) {
  const { t } = useI18n();
  const [mo, setMo] = useState(false);
  // giá trị điền được, khởi từ phần code đã điền
  const [gt, setGt] = useState<Record<number, string>>(() =>
    Object.fromEntries(k.o.map((o, i) => [i, o.gia_tri ?? ""])),
  );
  const [daLuu, setDaLuu] = useState(false);
  const KEY_NHAP = `policyradar.hoso.${k.ma}`;

  // nạp bản nháp đã lưu (sau mount → tránh lỗi SSR), đè lên phần code điền sẵn
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY_NHAP);
      if (raw) setGt((cu) => ({ ...cu, ...(JSON.parse(raw) as Record<number, string>) }));
    } catch {
      /* localStorage lỗi → dùng bản code điền sẵn */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // sửa ô nào thì xoá dấu "đã lưu"
  useEffect(() => setDaLuu(false), [gt]);

  function luuNhap() {
    try {
      localStorage.setItem(KEY_NHAP, JSON.stringify(gt));
      setDaLuu(true);
    } catch {
      /* bỏ qua nếu không ghi được */
    }
  }

  /** Duyệt & tải: xuất bản nháp ra .txt để DN in/nộp — bản nháp chờ duyệt. */
  function taiVe() {
    const dong = k.o.map((o, i) => `${o.nhan}: ${gt[i]?.trim() || "…"}`).join("\n");
    const noiDung =
      `${k.ma} — ${k.ten}\n` +
      `Căn cứ: ${k.can_cu}\nNơi nhận: ${k.co_quan_nhan}` +
      (k.han_nop ? `\nHạn nộp: ${k.han_nop}` : "") +
      `\n\n${dong}\n\n(Bản nháp do PolicyRadar dựng — chờ doanh nghiệp duyệt trước khi nộp)\n`;
    const url = URL.createObjectURL(new Blob([noiDung], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${k.ma}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const day = Object.values(gt).filter((v) => v.trim() !== "").length;
  const tong = k.o.length;

  return (
    <div className="mb-1.5 overflow-hidden rounded-lg border border-border-subtle bg-surface">
      <button onClick={() => setMo((v) => !v)} className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left hover:bg-surface-2">
        <svg viewBox="0 0 20 20" className="size-4 shrink-0 text-brand-600 dark:text-brand-300" fill="none">
          <path d="M6 3h5l3 3v11H6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M11 3v3h3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
        </svg>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand-50 px-1.5 py-0.5 font-mono text-[10.5px] font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
              {k.ma}
            </span>
            <span className="truncate text-[13px] font-medium text-text">{k.ten}</span>
          </div>
          <div className="mt-0.5 text-[11px] text-text-muted">
            {t("Căn cứ")} {k.can_cu} · {t("nơi nhận")} {k.co_quan_nhan}
            {k.han_nop ? ` · ${t("hạn")} ${k.han_nop}` : ""}
          </div>
        </div>
        <span className="shrink-0 text-[11px] text-text-muted">
          {day}/{tong} {t("ô")}
        </span>
        <svg viewBox="0 0 16 16" className={"size-3.5 shrink-0 text-text-muted transition-transform " + (mo ? "rotate-90" : "")} fill="none">
          <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* FORM ĐIỀN ĐƯỢC */}
      {mo && (
        <div className="border-t border-border-subtle px-4 py-3">
          <div className="space-y-3">
            {k.o.map((o, i) => (
              <ONhap key={i} o={o} value={gt[i]} onChange={(v) => setGt((s) => ({ ...s, [i]: v }))} />
            ))}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border-subtle pt-3">
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-eligible-700 dark:text-eligible-300">
              <svg viewBox="0 0 16 16" className="size-3.5" fill="none">
                <path d="M3 8.5l3 3 6-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {t("AI không tự điền — code gợi ý, bạn duyệt")}
            </span>
            <div className="ml-auto flex gap-2">
              <button
                onClick={luuNhap}
                className="rounded-lg border border-border-strong px-3 py-1.5 text-[12.5px] font-medium text-text hover:bg-surface-2"
              >
                {daLuu ? t("Đã lưu ✓") : t("Lưu nháp")}
              </button>
              <button
                onClick={taiVe}
                className="rounded-lg bg-brand-600 px-3 py-1.5 text-[12.5px] font-medium text-white hover:bg-brand-700"
              >
                {t("Duyệt & tải")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Một ô nhập liệu — có nhãn, nguồn, và input SỬA ĐƯỢC. */
function ONhap({ o, value, onChange }: { o: OHoSo; value: string; onChange: (v: string) => void }) {
  const { t } = useI18n();
  const ng = NGUON_NHAN[o.nguon];
  const goc = o.gia_tri ?? "";
  const daSua = value !== goc;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <label className="text-[12px] font-medium text-text">{o.nhan}</label>
        <span className={"text-[10.5px] " + ng.cls}>
          {o.nguon === "nguoi" ? t("Doanh nghiệp tự khai") : t(ng.nhan)}
        </span>
      </div>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={o.nguon === "nguoi" ? t("Bạn tự khai ô này…") : "—"}
        className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13.5px] text-text outline-none placeholder:text-text-muted focus:border-brand-500"
      />
      {daSua && goc !== "" && (
        <p className="mt-0.5 text-[10.5px] text-text-muted">{t("Gốc hệ thống điền:")} {goc}</p>
      )}
    </div>
  );
}
