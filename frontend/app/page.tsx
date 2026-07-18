"use client";

import { useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { DanhSachLuat } from "@/components/DanhSachLuat";
import { GiamSat } from "@/components/GiamSat";
import { ProfilePanel } from "@/components/ProfilePanel";
import { Sidebar, type Khung } from "@/components/Sidebar";
import { SoanHoSo } from "@/components/SoanHoSo";
import { LangToggle, useI18n } from "@/lib/i18n";
import { BffLoi, hoiBff, sangUI } from "@/lib/api";
import { bocHoSo } from "@/lib/extract";
import {
  type CuocTroChuyen,
  datTieuDe,
  luuLichSu,
  taiLichSu,
} from "@/lib/lichsu";
import {
  PROFILE_FIELDS,
  type LoaiChuongTrinh,
  type Message,
  type Profile,
} from "@/lib/types";

const LOI_MO_DAU =
  "Để tìm đúng ưu đãi và quỹ mà bạn đủ điều kiện, cho mình biết vài thông tin về doanh nghiệp: lĩnh vực (nông-lâm-thuỷ sản/công nghiệp-xây dựng hay thương mại-dịch vụ), số lao động tham gia BHXH bình quân năm, tổng doanh thu, tổng nguồn vốn, có Giấy chứng nhận DN KH&CN không, và tỷ lệ doanh thu từ sản phẩm KH&CN.\n\nBạn cứ mô tả bằng một câu tự nhiên — gõ không dấu cũng được.";

const GOI_Y = [
  "Bên mình làm phần mềm (công nghiệp) ở Hà Nội, 45 lao động, doanh thu 50 tỷ, vốn 20 tỷ, có giấy chứng nhận DN KH&CN, doanh thu từ sản phẩm KH&CN khoảng 45%",
  "Cty thương mại - dịch vụ tại Bắc Ninh, 150 lao động, doanh thu 120 tỷ, vốn 60 tỷ, có vốn FDI",
];

let dem = 0;
const nextId = () => `m${Date.now().toString(36)}-${++dem}`;

function hoiThoaiMoi(): CuocTroChuyen {
  const now = Date.now();
  return {
    id: `c${now.toString(36)}-${++dem}`,
    tieuDe: "Cuộc trò chuyện mới",
    taoLuc: now,
    suaLuc: now,
    profile: {},
    messages: [
      {
        id: nextId(),
        vaiTro: "tro-ly",
        dang: "hoi-ho-so",
        noiDung: LOI_MO_DAU,
        dangHoi: PROFILE_FIELDS.map((f) => f.key),
      },
    ],
  };
}

export default function Page() {
  const { t } = useI18n();
  const [lichSu, setLichSu] = useState<CuocTroChuyen[]>([]);
  const [convId, setConvId] = useState<string | null>(null);
  const [khung, setKhungRaw] = useState<Khung>("chat");
  const [sidebarMo, setSidebarMo] = useState(true); // mở mặc định (desktop); toggle được như Claude

  // giữ trang đang xem qua refresh (F5 không nhảy về chat)
  const setKhung = (k: Khung) => {
    setKhungRaw(k);
    if (typeof window !== "undefined") localStorage.setItem("policyradar.khung", k);
  };
  useEffect(() => {
    const k = typeof window !== "undefined" ? localStorage.getItem("policyradar.khung") : null;
    if (k === "chat" || k === "luat" || k === "hoso" || k === "giamsat") setKhungRaw(k);
  }, []);
  const [dangBan, setDangBan] = useState(false);
  const [treMs, setTreMs] = useState<number | null>(null);
  const [mocNgay, setMocNgay] = useState(0);
  const cuoiRef = useRef<HTMLDivElement>(null);

  // nạp lịch sử 1 lần
  useEffect(() => {
    setMocNgay(Date.now());
    const ds = taiLichSu();
    if (ds.length === 0) {
      const c = hoiThoaiMoi();
      setLichSu([c]);
      setConvId(c.id);
    } else {
      setLichSu(ds);
      setConvId(ds[0].id);
    }
  }, []);

  const conv = lichSu.find((c) => c.id === convId) ?? null;
  const messages = conv?.messages ?? [];
  const profile = conv?.profile ?? {};

  useEffect(() => {
    cuoiRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, khung]);

  function capNhat(id: string, sua: (c: CuocTroChuyen) => CuocTroChuyen) {
    setLichSu((prev) => {
      const ds = prev.map((c) => (c.id === id ? { ...sua(c), suaLuc: Date.now() } : c));
      luuLichSu(ds);
      return ds;
    });
  }

  function themTin(id: string, m: Message) {
    capNhat(id, (c) => {
      const messages = [...c.messages, m];
      return { ...c, messages, tieuDe: datTieuDe(messages) };
    });
  }

  function moi() {
    // như Claude: nếu đang có một chat RỖNG (chưa gõ gì) thì dùng lại nó,
    // đừng tạo thêm chat rỗng chất đống trong lịch sử.
    const rong = lichSu.find((c) => !c.messages.some((m) => m.vaiTro === "nguoi-dung"));
    if (rong) {
      setConvId(rong.id);
      setTreMs(null);
      return;
    }
    const c = hoiThoaiMoi();
    setLichSu((prev) => {
      const ds = [c, ...prev];
      luuLichSu(ds);
      return ds;
    });
    setConvId(c.id);
    setTreMs(null);
  }

  function xoa(id: string) {
    setLichSu((prev) => {
      const ds = prev.filter((c) => c.id !== id);
      luuLichSu(ds);
      if (id === convId) {
        if (ds.length > 0) setConvId(ds[0].id);
        else {
          const c = hoiThoaiMoi();
          ds.unshift(c);
          luuLichSu(ds);
          setConvId(c.id);
        }
      }
      return ds;
    });
  }

  async function xuLy(text: string) {
    if (!convId) return;
    const id = convId;
    themTin(id, { id: nextId(), vaiTro: "nguoi-dung", noiDung: text });
    setDangBan(true);

    const hoSoMoi = bocHoSo(text, profile);
    capNhat(id, (c) => ({ ...c, profile: hoSoMoi }));

    try {
      const d = await hoiBff(text, hoSoMoi);
      setTreMs(d.ms);

      // GPT trích hồ sơ ở server (chính xác hơn regex) → đồng bộ vào panel
      if (d.ho_so_moi) {
        const hsGPT = sangUI(d.ho_so_moi);
        capNhat(id, (c) => ({ ...c, profile: { ...c.profile, ...hsGPT } }));
      }

      if (d.dang === "van_ban") {
        // câu meta/lạc đề, ngoài phạm vi, hồ sơ vô lý → trả lời văn bản THẲNG,
        // KHÔNG phải lỗi, KHÔNG gắn badge "chưa đủ căn cứ" (đây là câu trò chuyện,
        // không phải phán quyết về một điều luật).
        themTin(id, {
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "van-ban",
          noiDung: d.noi_dung,
        });
      } else if (d.dang === "hoi_ho_so") {
        themTin(id, {
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "hoi-ho-so",
          noiDung: d.noi_dung,
          dangHoi: [],
        });
      } else {
        themTin(id, {
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "ket-qua",
          noiDung: d.noi_dung,
          daQuet: 2646,
          dienGiai: d.dien_giai
            ? {
                text: d.dien_giai.text,
                grounded: d.dien_giai.grounded,
                soBia: d.dien_giai.so_bia.map((s) => ({
                  raw: s.raw,
                  batDau: s.bat_dau,
                  ketThuc: s.ket_thuc,
                })),
                canhBao: d.dien_giai.canh_bao,
              }
            : undefined,
          chuongTrinh: d.chuong_trinh.map((c) => ({
            id: c.id,
            ten: c.ten,
            coQuan: c.co_quan,
            loai: (c.loai?.replace(/_/g, "-") ?? "uu-dai-thue") as LoaiChuongTrinh,
            giaTri: c.gia_tri,
            giaTriKyVong: null,
            giaTriHienThi: c.gia_tri_ky_vong ?? undefined,
            giaTriNhan: c.gia_tri_nhan ?? undefined,
            hanNop: c.han_nop ?? undefined,
            doTinCay: c.do_tin_cay,
            duDieuKien: c.du_dieu_kien,
            xacQuyet: c.xac_quyet,
            thieu: c.thieu,
            canBoSung: c.can_bo_sung,
            hieuLucDaDoiChieu: c.hieu_luc?.da_doi_chieu ?? false,
            hieuLuc: c.hieu_luc
              ? {
                  daDoiChieu: c.hieu_luc.da_doi_chieu,
                  conHieuLuc: c.hieu_luc.con_hieu_luc,
                  nhan: c.hieu_luc.nhan,
                  ma: c.hieu_luc.ma,
                  soQuanHe: c.hieu_luc.so_quan_he,
                  nguon: c.hieu_luc.nguon,
                }
              : undefined,
            dieuKien: c.dieu_kien.map((k) => ({
              yeuCau: k.yeu_cau,
              hoSo: k.doi_chieu,
              trangThai:
                k.trang_thai === "dat"
                  ? ("dat" as const)
                  : k.trang_thai === "khong_dat"
                    ? ("khong-dat" as const)
                    : ("chua-du-thong-tin" as const),
              citation: {
                id: k.citation.khoa,
                vanBan: k.citation.hien_thi,
                trichDan: k.citation.trich,
                docId: k.citation.doc_id ?? undefined,
                url: k.citation.url ?? undefined,
              },
            })),
          })),
        });
      }
    } catch (e) {
      themTin(id, {
        id: nextId(),
        vaiTro: "tro-ly",
        dang: "van-ban",
        noiDung:
          e instanceof BffLoi ? e.message : t("Có lỗi khi gọi hệ thống. Vui lòng thử lại."),
        grounding: "chua-du-can-cu",
      });
    } finally {
      setDangBan(false);
    }
  }

  const chuaHoi = messages.length === 1;

  return (
    <div className="flex h-dvh">
      <Sidebar
        khung={khung}
        onKhung={setKhung}
        lichSu={lichSu}
        convId={convId}
        onChon={setConvId}
        onMoi={moi}
        onXoa={xoa}
        mocNgay={mocNgay}
        mo={sidebarMo}
        onDong={() => setSidebarMo(false)}
        onMo={() => setSidebarMo(true)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b border-border-subtle bg-surface px-4 py-2.5">
          {/* ☰ chỉ MOBILE (desktop thu gọn đã có RAIL icon để mở lại) */}
          {!sidebarMo && (
            <button
              onClick={() => setSidebarMo(true)}
              className="-ml-1 rounded-md p-1.5 text-text-muted hover:bg-surface-2 md:hidden"
              aria-label={t("Mở thanh bên")}
              title={t("Mở thanh bên")}
            >
              <svg viewBox="0 0 20 20" className="size-5" fill="none">
                <path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
            </button>
          )}
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-[15px] font-semibold leading-none text-text">
              {khung === "luat"
                ? t("Danh sách luật")
                : khung === "hoso"
                  ? t("Soạn hồ sơ xin tài trợ")
                  : khung === "giamsat"
                    ? t("Giám sát chính sách")
                    : t("Trợ lý tư vấn chính sách")}
            </h1>
            <p className="mt-1 truncate text-[11px] leading-none text-text-muted">
              {khung === "luat"
                ? t("Tra cứu văn bản trong corpus — tìm kiếm, lọc theo tiêu chí")
                : khung === "hoso"
                  ? t("Dựng khung hồ sơ, điền sẵn từ hồ sơ DN — bản nháp chờ duyệt")
                  : khung === "giamsat"
                    ? t("Theo dõi hiệu lực + văn bản liên quan, đối chiếu vbpl.vn")
                    : t("Tìm đúng chính sách bạn đủ điều kiện — có căn cứ tới từng điều khoản")}
            </p>
          </div>
          {khung === "chat" && treMs !== null && (
            <span
              className="shrink-0 rounded border border-border-subtle px-1.5 py-0.5 font-mono text-[10px] text-text-muted"
              title={t("Thời gian phản hồi. Đề bài yêu cầu ≤ 5.000ms cho câu đơn giản.")}
            >
              {treMs}ms
            </span>
          )}
          {/* nút đổi ngôn ngữ trên nav trên cùng */}
          <LangToggle />
        </header>

        {khung === "luat" ? (
          <DanhSachLuat />
        ) : khung === "hoso" ? (
          <SoanHoSo profile={profile} />
        ) : khung === "giamsat" ? (
          <GiamSat />
        ) : (
          <div className="flex min-h-0 flex-1">
            {/* cột chat */}
            <div className="flex min-w-0 flex-1 flex-col">
              <div className="flex-1 overflow-y-auto">
                <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-4">
                  {messages.map((m) => (
                    <ChatMessage key={m.id} m={m} />
                  ))}
                  {dangBan && (
                    <p className="text-[12px] text-text-muted">{t("Đang quét kho văn bản…")}</p>
                  )}
                  <div ref={cuoiRef} />
                </div>
              </div>
              <ChatInput onGui={xuLy} dangBan={dangBan} goiY={chuaHoi ? GOI_Y : []} />
            </div>

            {/* panel hồ sơ dọc bên phải */}
            <ProfilePanel profile={profile} />
          </div>
        )}
      </main>
    </div>
  );
}
