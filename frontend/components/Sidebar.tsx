"use client";

import { useMemo } from "react";
import { Logo } from "@/components/Logo";
import { type CuocTroChuyen, nhomTheoThoiGian } from "@/lib/lichsu";

export type Khung = "chat" | "luat" | "hoso" | "giamsat";

export function Sidebar({
  khung,
  onKhung,
  lichSu,
  convId,
  onChon,
  onMoi,
  onXoa,
  mocNgay,
  mo,
  onDong,
  onMo,
}: {
  khung: Khung;
  onKhung: (k: Khung) => void;
  lichSu: CuocTroChuyen[];
  convId: string | null;
  onChon: (id: string) => void;
  onMoi: () => void;
  onXoa: (id: string) => void;
  mocNgay: number;
  mo: boolean;
  onDong: () => void;
  onMo: () => void;
}) {
  const daDung = useMemo(
    () => lichSu.filter((c) => c.messages.some((m) => m.vaiTro === "nguoi-dung")),
    [lichSu],
  );
  const nhom = useMemo(() => nhomTheoThoiGian(daDung, mocNgay), [daDung, mocNgay]);

  // ── RAIL (thu gọn): học từ mẫu Aceternity — collapse về thanh icon,
  //    KHÔNG ẩn hẳn. Mượt hơn, vẫn bấm được nav. (CSS transition, khỏi framer-motion.)
  const Rail = (
    <div className="hidden h-full w-14 shrink-0 flex-col items-center border-r border-border-subtle bg-surface-2 py-3 md:flex">
      <div className="mb-1"><Logo size={26} /></div>
      {/* nút MỞ luôn hiện rõ (không giấu sau hover) — cùng chỗ với « lúc mở */}
      <button
        onClick={onMo}
        title="Mở thanh bên"
        aria-label="Mở thanh bên"
        className="mb-2 flex size-9 items-center justify-center rounded-lg border border-border-strong text-text-muted hover:border-brand-400 hover:bg-surface hover:text-brand-600 dark:hover:text-brand-300"
      >
        <svg viewBox="0 0 20 20" className="size-[18px]" fill="none">
          <path d="M8 5l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M16 4v12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </button>
      <RailBtn onClick={() => { onMoi(); onKhung("chat"); }} label="Cuộc trò chuyện mới">
        <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </RailBtn>
      <RailBtn active={khung === "chat"} onClick={() => onKhung("chat")} label="Trợ lý tư vấn">
        <path d="M4 5h12v8H8l-4 3V5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      </RailBtn>
      <RailBtn active={khung === "hoso"} onClick={() => onKhung("hoso")} label="Soạn hồ sơ">
        <path d="M6 3h5l3 3v11H6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M11 3v3h3M8 11h4M8 14h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </RailBtn>
      <RailBtn active={khung === "giamsat"} onClick={() => onKhung("giamsat")} label="Giám sát">
        <path d="M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z" stroke="currentColor" strokeWidth="1.5" />
        <path d="M10 6v4l2.5 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </RailBtn>
      <RailBtn active={khung === "luat"} onClick={() => onKhung("luat")} label="Danh sách luật">
        <path d="M5 4h10v12H5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M8 8h4M8 11h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </RailBtn>
      <div className="mt-auto">
        <span className="flex size-8 items-center justify-center rounded-full bg-brand-600 text-[12px] font-semibold text-white" title="Doanh nghiệp">
          DN
        </span>
      </div>
    </div>
  );

  return (
    <>
      {/* nền mờ khi mở overlay trên mobile */}
      {mo && <div onClick={onDong} className="fixed inset-0 z-20 bg-black/40 md:hidden" aria-hidden />}

      {/* RAIL desktop khi thu gọn */}
      {!mo && Rail}

      {/* SIDEBAR đầy đủ */}
      <aside
        className={
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border-subtle bg-surface-2 transition-transform md:static " +
          (mo ? "translate-x-0" : "-translate-x-full md:hidden")
        }
      >
        <div className="flex items-center gap-2.5 px-4 py-4">
          <Logo size={32} />
          <div className="min-w-0 flex-1">
            <div className="text-[14px] font-semibold leading-tight text-text">PolicyRadar</div>
            <div className="text-[10.5px] leading-tight text-text-muted">Trợ lý chính sách · NIC</div>
          </div>
          <button
            onClick={onDong}
            className="shrink-0 rounded-md p-1 text-text-muted hover:bg-surface"
            aria-label="Thu gọn thanh bên"
            title="Thu gọn thanh bên"
          >
            <svg viewBox="0 0 20 20" className="size-[18px]" fill="none">
              <path d="M12 5l-5 5 5 5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M4 4v12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="px-3">
          <button
            onClick={() => { onMoi(); onKhung("chat"); }}
            className="flex w-full items-center gap-2 rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13px] font-medium text-text transition-colors hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/30"
          >
            <svg viewBox="0 0 20 20" className="size-4" fill="none">
              <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
            Cuộc trò chuyện mới
          </button>
        </div>

        <nav className="mt-3 px-3">
          <MucNav active={khung === "chat"} onClick={() => onKhung("chat")} nhan="Trợ lý tư vấn" />
          <MucNav active={khung === "hoso"} onClick={() => onKhung("hoso")} nhan="Soạn hồ sơ" />
          <MucNav active={khung === "giamsat"} onClick={() => onKhung("giamsat")} nhan="Giám sát chính sách" />
          <MucNav active={khung === "luat"} onClick={() => onKhung("luat")} nhan="Danh sách luật" />
        </nav>

        <div className="mt-4 flex-1 overflow-y-auto px-2 pb-3">
          <div className="px-2 pb-1 text-[10.5px] font-semibold uppercase tracking-wide text-text-muted">
            Lịch sử
          </div>
          {daDung.length === 0 && (
            <p className="px-2 py-3 text-[12px] leading-relaxed text-text-muted">
              Chưa có cuộc trò chuyện nào. Bắt đầu bằng cách mô tả doanh nghiệp của bạn.
            </p>
          )}
          {nhom.map((g) => (
            <div key={g.nhan} className="mb-2">
              <div className="px-2 py-1 text-[10.5px] font-medium text-text-muted">{g.nhan}</div>
              {g.items.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { onChon(c.id); onKhung("chat"); }}
                  className={
                    "group flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-[12.5px] transition-colors " +
                    (c.id === convId && khung === "chat"
                      ? "bg-brand-100 text-brand-900 dark:bg-brand-900/50 dark:text-brand-50"
                      : "text-text hover:bg-surface")
                  }
                >
                  <span className="min-w-0 flex-1 truncate">{c.tieuDe}</span>
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => { e.stopPropagation(); onXoa(c.id); }}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); onXoa(c.id); } }}
                    className="hidden shrink-0 rounded p-0.5 text-text-muted hover:text-blocked-600 group-hover:block"
                    aria-label="Xoá cuộc trò chuyện"
                  >
                    <svg viewBox="0 0 16 16" className="size-3.5" fill="none">
                      <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                    </svg>
                  </span>
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="border-t border-border-subtle p-2">
          <button className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left transition-colors hover:bg-surface">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[13px] font-semibold text-white">
              DN
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[12.5px] font-medium text-text">Doanh nghiệp</span>
              <span className="block truncate text-[10.5px] text-text-muted">Gói tra cứu chính sách</span>
            </span>
          </button>
        </div>
      </aside>
    </>
  );
}

function RailBtn({
  active,
  onClick,
  label,
  children,
}: {
  active?: boolean;
  onClick: () => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      className={
        "mb-1 flex size-9 items-center justify-center rounded-lg transition-colors " +
        (active ? "bg-brand-600 text-white" : "text-text-muted hover:bg-surface hover:text-text")
      }
    >
      <svg viewBox="0 0 20 20" className="size-[18px]">{children}</svg>
    </button>
  );
}

function MucNav({
  active,
  onClick,
  nhan,
}: {
  active: boolean;
  onClick: () => void;
  nhan: string;
}) {
  // text-only cho gọn, chuyên nghiệp (icon giữ ở rail lúc thu gọn)
  return (
    <button
      onClick={onClick}
      className={
        "mb-0.5 flex w-full items-center rounded-lg px-3 py-2 text-[13px] font-medium transition-colors " +
        (active ? "bg-brand-600 text-white" : "text-text hover:bg-surface")
      }
    >
      {nhan}
    </button>
  );
}
