"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  type BoLoc,
  type Facets,
  type TrangLuat,
  type VanBan,
  nhanLoai,
  traFacets,
  traLuat,
} from "@/lib/luat";

const CS = 20;

/** Danh sách luật — tra cứu corpus 2.669 văn bản: tìm kiếm + lọc + phân trang. */
export function DanhSachLuat() {
  const [loc, setLoc] = useState<BoLoc>({ trang: 1, cs: CS });
  const [data, setData] = useState<TrangLuat | null>(null);
  const [facets, setFacets] = useState<Facets | null>(null);
  const [dangTai, setDangTai] = useState(false);
  const [loi, setLoi] = useState("");
  const [oTim, setOTim] = useState("");
  const timRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // facets 1 lần
  useEffect(() => {
    traFacets().then(setFacets).catch(() => {});
  }, []);

  // tải khi bộ lọc đổi
  useEffect(() => {
    let huy = false;
    setDangTai(true);
    setLoi("");
    traLuat(loc)
      .then((d) => {
        if (!huy) setData(d);
      })
      .catch((e) => {
        if (!huy) setLoi(e instanceof Error ? e.message : "Lỗi tải");
      })
      .finally(() => {
        if (!huy) setDangTai(false);
      });
    return () => {
      huy = true;
    };
  }, [loc]);

  // debounce ô tìm
  function onTim(v: string) {
    setOTim(v);
    if (timRef.current) clearTimeout(timRef.current);
    timRef.current = setTimeout(() => {
      setLoc((l) => ({ ...l, q: v, trang: 1 }));
    }, 300);
  }

  function datLoc(k: keyof BoLoc, v: string) {
    setLoc((l) => ({ ...l, [k]: v || undefined, trang: 1 }));
  }

  const soLocDang = useMemo(
    () => [loc.doc_type, loc.linh_vuc, loc.co_quan, loc.nam].filter(Boolean).length,
    [loc],
  );

  return (
    <div className="flex h-full flex-col">
      {/* thanh tìm + lọc */}
      <div className="border-b border-border-subtle bg-surface px-5 py-3.5">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <svg
                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-muted"
                viewBox="0 0 20 20"
                fill="none"
              >
                <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.6" />
                <path d="m14 14 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
              <input
                value={oTim}
                onChange={(e) => onTim(e.target.value)}
                placeholder="Tìm theo số hiệu, tiêu đề, cơ quan… (gõ không dấu cũng được)"
                className="w-full rounded-lg border border-border-strong bg-surface-2 py-2 pl-9 pr-3 text-[13px] text-text outline-none placeholder:text-text-muted focus:border-brand-500"
              />
            </div>
            {(soLocDang > 0 || loc.q) && (
              <button
                onClick={() => {
                  setOTim("");
                  setLoc({ trang: 1, cs: CS });
                }}
                className="shrink-0 rounded-lg border border-border-subtle px-3 py-2 text-[12px] text-text-muted hover:bg-surface-2"
              >
                Xoá lọc
              </button>
            )}
          </div>

          {/* dropdown lọc theo tiêu chí */}
          <div className="mt-2.5 flex flex-wrap gap-2">
            <LocChon
              nhan="Loại văn bản"
              gt={loc.doc_type ?? ""}
              opts={facets?.doc_type}
              nhanGt={nhanLoai}
              onChon={(v) => datLoc("doc_type", v)}
            />
            <LocChon
              nhan="Lĩnh vực"
              gt={loc.linh_vuc ?? ""}
              opts={facets?.linh_vuc}
              onChon={(v) => datLoc("linh_vuc", v)}
            />
            <LocChon
              nhan="Cơ quan"
              gt={loc.co_quan ?? ""}
              opts={facets?.co_quan}
              onChon={(v) => datLoc("co_quan", v)}
            />
            <LocChon
              nhan="Năm"
              gt={loc.nam ?? ""}
              opts={facets?.nam}
              onChon={(v) => datLoc("nam", v)}
            />
          </div>
        </div>
      </div>

      {/* kết quả */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-5 py-4">
          <div className="mb-3 flex items-center justify-between text-[12px] text-text-muted">
            <span>
              {dangTai
                ? "Đang tải…"
                : data
                  ? `${data.tong.toLocaleString("vi-VN")} văn bản` +
                    (loc.q ? ` khớp "${loc.q}"` : "")
                  : ""}
            </span>
            {data && data.so_trang > 1 && (
              <span>
                Trang {data.trang}/{data.so_trang}
              </span>
            )}
          </div>

          {loi && (
            <p className="rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[13px] text-blocked-600 dark:bg-blocked-500/10">
              {loi}
            </p>
          )}

          <div className="flex flex-col gap-2">
            {data?.van_ban.map((v) => (
              <TheLuat key={v.item_id} v={v} />
            ))}
            {!dangTai && data && data.van_ban.length === 0 && (
              <p className="py-12 text-center text-[13px] text-text-muted">
                Không có văn bản nào khớp. Thử bỏ bớt bộ lọc.
              </p>
            )}
          </div>

          {data && data.so_trang > 1 && (
            <PhanTrang
              trang={data.trang}
              soTrang={data.so_trang}
              onTrang={(t) => {
                setLoc((l) => ({ ...l, trang: t }));
                document.querySelector("[data-luat-top]")?.scrollIntoView();
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function LocChon({
  nhan,
  gt,
  opts,
  nhanGt,
  onChon,
}: {
  nhan: string;
  gt: string;
  opts?: { gia_tri: string; so_luong: number }[];
  nhanGt?: (v: string) => string;
  onChon: (v: string) => void;
}) {
  const co = gt !== "";
  return (
    <div className="relative">
      <select
        value={gt}
        onChange={(e) => onChon(e.target.value)}
        className={
          "cursor-pointer appearance-none rounded-lg border py-1.5 pl-3 pr-8 text-[12px] outline-none focus:border-brand-500 " +
          (co
            ? "border-brand-300 bg-brand-50 text-brand-800 dark:border-brand-700 dark:bg-brand-900/40 dark:text-brand-100"
            : "border-border-strong bg-surface-2 text-text-muted")
        }
      >
        <option value="">{nhan}: tất cả</option>
        {opts?.map((o) => (
          <option key={o.gia_tri} value={o.gia_tri}>
            {(nhanGt ? nhanGt(o.gia_tri) : o.gia_tri)} ({o.so_luong})
          </option>
        ))}
      </select>
      <svg
        className="pointer-events-none absolute right-2.5 top-1/2 size-3.5 -translate-y-1/2 text-text-muted"
        viewBox="0 0 20 20"
        fill="none"
      >
        <path d="m6 8 4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    </div>
  );
}

function TheLuat({ v }: { v: VanBan }) {
  // cả thẻ là link → bấm đâu cũng mở trang văn bản trên vbpl.vn.
  // Không có nguồn thì để <div> (không bấm được), tránh link chết.
  const Bọc = v.nguon_url ? "a" : "div";
  const props = v.nguon_url
    ? { href: v.nguon_url, target: "_blank", rel: "noreferrer" }
    : {};
  return (
    <Bọc
      {...props}
      className={
        "group block rounded-xl border border-border-subtle bg-surface px-4 py-3 transition-colors " +
        (v.nguon_url ? "cursor-pointer hover:border-brand-400 hover:bg-brand-50/40 dark:hover:bg-brand-900/20" : "")
      }
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-md bg-brand-50 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
          {v.so_hieu || "—"}
        </span>
        <span className="rounded-md border border-border-subtle px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-text-muted">
          {nhanLoai(v.doc_type)}
        </span>
        {v.nam && <span className="text-[11px] text-text-muted">{v.nam}</span>}
        {v.nguon_url && (
          <span className="ml-auto text-[11px] text-brand-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-brand-300">
            Mở trên vbpl.vn ↗
          </span>
        )}
      </div>
      <h3 className="mt-1.5 text-[13.5px] font-medium leading-snug text-text group-hover:text-brand-800 dark:group-hover:text-brand-100">
        {v.tieu_de}
      </h3>
      {v.tom_tat && (
        <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-text-muted">{v.tom_tat}</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-text-muted">
        {v.co_quan && (
          <span className="inline-flex items-center gap-1">
            <svg viewBox="0 0 16 16" className="size-3.5 shrink-0" fill="none">
              <path d="M2 6l6-3 6 3M3 6v6M13 6v6M2 13h12M6 8v3M10 8v3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {v.co_quan}
          </span>
        )}
        {v.linh_vuc && v.linh_vuc !== "Chưa phân loại" && (
          <span className="inline-flex items-center gap-1">
            <svg viewBox="0 0 16 16" className="size-3.5 shrink-0" fill="none">
              <path d="M2 5a1 1 0 0 1 1-1h3l1.5 1.5H13a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
            </svg>
            {v.linh_vuc}
          </span>
        )}
      </div>
    </Bọc>
  );
}

function PhanTrang({
  trang,
  soTrang,
  onTrang,
}: {
  trang: number;
  soTrang: number;
  onTrang: (t: number) => void;
}) {
  // hiện tối đa 7 nút: đầu … quanh trang hiện tại … cuối
  const nums: (number | "…")[] = [];
  const them = (n: number) => nums.push(n);
  if (soTrang <= 7) {
    for (let i = 1; i <= soTrang; i++) them(i);
  } else {
    them(1);
    if (trang > 3) nums.push("…");
    for (let i = Math.max(2, trang - 1); i <= Math.min(soTrang - 1, trang + 1); i++) them(i);
    if (trang < soTrang - 2) nums.push("…");
    them(soTrang);
  }

  const nut =
    "min-w-8 rounded-md border px-2 py-1 text-[12px] transition-colors disabled:opacity-40";

  return (
    <div className="mt-5 flex items-center justify-center gap-1.5">
      <button
        className={nut + " border-border-strong text-text-muted hover:bg-surface-2"}
        disabled={trang <= 1}
        onClick={() => onTrang(trang - 1)}
      >
        ‹
      </button>
      {nums.map((n, i) =>
        n === "…" ? (
          <span key={`e${i}`} className="px-1 text-[12px] text-text-muted">
            …
          </span>
        ) : (
          <button
            key={n}
            onClick={() => onTrang(n)}
            className={
              nut +
              (n === trang
                ? " border-brand-600 bg-brand-600 font-semibold text-white"
                : " border-border-strong text-text hover:bg-surface-2")
            }
          >
            {n}
          </button>
        ),
      )}
      <button
        className={nut + " border-border-strong text-text-muted hover:bg-surface-2"}
        disabled={trang >= soTrang}
        onClick={() => onTrang(trang + 1)}
      >
        ›
      </button>
    </div>
  );
}
