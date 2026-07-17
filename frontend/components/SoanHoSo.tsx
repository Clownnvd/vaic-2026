"use client";

import { useEffect, useState } from "react";
import {
  type KetQuaHoSo,
  type KhungHoSo,
  type OHoSo,
  NGUON_NHAN,
  sinhHoSo,
} from "@/lib/hoso";
import type { Profile } from "@/lib/types";

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://localhost:8000";

type CtItem = { id: string; ten: string; co_quan: string };

/** UI Profile (camelCase) → khoá backend (snake) — dùng lại khi sinh hồ sơ. */
function sangBackend(p: Profile): Record<string, unknown> {
  const r: Record<string, unknown> = {};
  if (p.nganh) r.ten_to_chuc = p.nganh; // tên tổ chức tạm; DN sẽ tự sửa
  if (p.linhVuc) r.linh_vuc = p.linhVuc;
  if (p.von !== undefined) r.von = p.von;
  if (p.doanhThu !== undefined) r.doanh_thu = p.doanhThu;
  if (p.laoDongBhxh !== undefined) r.lao_dong_bhxh = p.laoDongBhxh;
  if (p.tyLeDtKhcn !== undefined) r.ty_le_dt_khcn = p.tyLeDtKhcn;
  return r;
}

/**
 * ③ SOẠN HỒ SƠ xin tài trợ — structure-then-fill.
 * CODE điền phần biết chắc (từ hồ sơ DN / corpus), AI KHÔNG gõ ô nào,
 * phần còn lại DN tự khai. Luôn là BẢN NHÁP chờ duyệt (write-gate).
 */
export function SoanHoSo({ profile }: { profile: Profile }) {
  const [ct, setCt] = useState<CtItem[]>([]);
  const [chon, setChon] = useState<string>("");
  const [kq, setKq] = useState<KetQuaHoSo | null>(null);
  const [dangTai, setDangTai] = useState(false);
  const [loi, setLoi] = useState("");

  useEffect(() => {
    fetch(`${BFF}/chuong-trinh`)
      .then((r) => r.json())
      .then((d) => setCt(d.chuong_trinh ?? []))
      .catch(() => {});
  }, []);

  async function sinh(id: string) {
    setChon(id);
    setDangTai(true);
    setLoi("");
    setKq(null);
    try {
      setKq(await sinhHoSo(id, sangBackend(profile)));
    } catch (e) {
      setLoi(e instanceof Error ? e.message : "Lỗi sinh hồ sơ");
    } finally {
      setDangTai(false);
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-5 py-5">
        <div className="mb-4">
          <h2 className="text-[16px] font-semibold text-text">Soạn hồ sơ xin tài trợ</h2>
          <p className="mt-1 text-[13px] leading-relaxed text-text-muted">
            Hệ thống dựng khung hồ sơ và điền sẵn phần biết chắc từ hồ sơ doanh nghiệp và
            văn bản pháp luật. <b>AI không tự gõ ô nào</b> — phần còn lại bạn tự khai, và
            mọi bản đều là <b>bản nháp chờ bạn duyệt</b> trước khi nộp.
          </p>
        </div>

        {/* chọn chương trình */}
        <div className="mb-4">
          <div className="mb-1.5 text-[12px] font-medium text-text-muted">
            Chọn chương trình để dựng bộ hồ sơ:
          </div>
          <div className="flex flex-wrap gap-2">
            {ct.map((c) => (
              <button
                key={c.id}
                onClick={() => sinh(c.id)}
                className={
                  "rounded-lg border px-3 py-2 text-left text-[13px] transition-colors " +
                  (chon === c.id
                    ? "border-brand-500 bg-brand-50 text-brand-800 dark:bg-brand-900/40 dark:text-brand-100"
                    : "border-border-strong bg-surface text-text hover:border-brand-400")
                }
              >
                <div className="font-medium">{c.ten}</div>
                <div className="text-[11px] text-text-muted">{c.co_quan}</div>
              </button>
            ))}
          </div>
        </div>

        {dangTai && <p className="text-[13px] text-text-muted">Đang dựng khung hồ sơ…</p>}
        {loi && (
          <p className="rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[13px] text-blocked-600 dark:bg-blocked-500/10">
            {loi}
          </p>
        )}

        {kq && (kq.khung?.length ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 rounded-lg border border-caution-300 bg-caution-50 px-3.5 py-2.5 text-[12.5px] text-caution-800 dark:border-caution-700 dark:bg-caution-500/10 dark:text-caution-200">
              <svg viewBox="0 0 16 16" className="size-4 shrink-0" fill="none">
                <path d="M8 1.5l6 11H2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
                <path d="M8 6.5v3M8 11v.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
              <span>
                <b>Bản nháp — chờ bạn duyệt.</b> Số liệu do hệ thống điền từ hồ sơ; hãy đối
                chiếu trước khi nộp. Hệ thống không tự nộp hộ.
              </span>
            </div>

            {kq.khung.map((k) => (
              <KhungCard key={k.ma} k={k} />
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-border-subtle bg-surface px-4 py-3 text-[13px] text-text-muted">
            {kq.text || "Chương trình này chưa gắn biểu mẫu hồ sơ trong kho."}
          </p>
        ))}
      </div>
    </div>
  );
}

function KhungCard({ k }: { k: KhungHoSo }) {
  return (
    <article className="overflow-hidden rounded-xl border border-border-subtle bg-surface">
      <div className="flex flex-wrap items-center gap-2 border-b border-border-subtle px-4 py-3">
        <span className="rounded-md bg-brand-50 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
          {k.ma}
        </span>
        <h3 className="text-[14px] font-semibold text-text">{k.ten}</h3>
        <span className="ml-auto text-[11px] text-text-muted">
          Điền {Math.round(k.phan_tram_day * 100)}%
        </span>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 border-b border-border-subtle px-4 py-2 text-[11.5px] text-text-muted">
        <span>Căn cứ: <b className="font-mono text-text">{k.can_cu}</b></span>
        <span>Nơi nhận: {k.co_quan_nhan}</span>
        {k.han_nop && <span>Hạn nộp: {k.han_nop}</span>}
      </div>

      <div className="divide-y divide-border-subtle">
        {k.o.map((o, i) => (
          <ODong key={i} o={o} />
        ))}
      </div>

      {k.thieu.length > 0 && (
        <div className="border-t border-border-subtle bg-caution-50/50 px-4 py-2 text-[11.5px] text-caution-700 dark:bg-caution-500/5 dark:text-caution-300">
          Còn thiếu (bạn tự khai): {k.thieu.join(", ")}
        </div>
      )}

      <div className="flex items-center gap-2 border-t border-border-subtle px-4 py-2.5">
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-eligible-700 dark:text-eligible-300">
          <svg viewBox="0 0 16 16" className="size-3.5" fill="none">
            <path d="M3 8.5l3 3 6-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          AI không gõ ô nào — code điền, người duyệt
        </span>
        <button className="ml-auto rounded-lg bg-brand-600 px-3 py-1.5 text-[12.5px] font-medium text-white hover:bg-brand-700">
          Duyệt & tải bản nháp
        </button>
      </div>
    </article>
  );
}

function ODong({ o }: { o: OHoSo }) {
  const ng = NGUON_NHAN[o.nguon];
  return (
    <div className="flex items-start gap-3 px-4 py-2">
      <span
        className={
          "mt-1.5 size-1.5 shrink-0 rounded-full " +
          (o.da_dien ? "bg-eligible-500" : "bg-border-strong")
        }
      />
      <div className="min-w-0 flex-1">
        <div className="text-[12px] text-text-muted">{o.nhan}</div>
        <div className={"text-[13.5px] " + (o.da_dien ? "font-medium text-text" : "italic text-text-muted")}>
          {o.gia_tri ?? "— để trống, doanh nghiệp tự khai"}
        </div>
      </div>
      <span className={"shrink-0 text-[10.5px] " + ng.cls}>{ng.nhan}</span>
    </div>
  );
}
