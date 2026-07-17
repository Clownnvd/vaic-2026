"use client";

import { useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { ProfileRibbon } from "@/components/ProfileRibbon";
import { BffLoi, hoiBff } from "@/lib/api";
import { bocHoSo } from "@/lib/extract";
import { PROFILE_FIELDS, type Message, type Profile } from "@/lib/types";

const LOI_MO_DAU =
  "Để tìm đúng ưu đãi và quỹ mà bạn đủ điều kiện, cho mình biết vài thông tin về doanh nghiệp: ngành, vốn điều lệ, số nhân sự, chi cho R&D (theo % doanh thu), địa bàn, và có vốn FDI không?\n\nBạn cứ mô tả bằng một câu tự nhiên — gõ không dấu cũng được.";

const GOI_Y = [
  "Bên mình làm phần mềm ở Hà Nội, vốn 20 tỷ, 45 người, chi R&D khoảng 2,5% doanh thu, không có vốn FDI",
  "Cty bán dẫn tại Bắc Ninh, vốn 500 tỷ, 300 nhân sự, R&D 8%, có vốn FDI",
];

let dem = 0;
const nextId = () => `m${++dem}`;

export default function Page() {
  const [profile, setProfile] = useState<Profile>({});
  const [messages, setMessages] = useState<Message[]>([
    {
      id: nextId(),
      vaiTro: "tro-ly",
      dang: "hoi-ho-so",
      noiDung: LOI_MO_DAU,
      dangHoi: PROFILE_FIELDS.map((f) => f.key),
    },
  ]);
  const [dangBan, setDangBan] = useState(false);
  const [treMs, setTreMs] = useState<number | null>(null);
  const cuoiRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cuoiRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function them(m: Message) {
    setMessages((prev) => [...prev, m]);
  }

  async function xuLy(text: string) {
    them({ id: nextId(), vaiTro: "nguoi-dung", noiDung: text });
    setDangBan(true);

    // Bóc hồ sơ tạm ở client — sẽ chuyển hẳn sang agent slot-filling ở BFF.
    const hoSoMoi = bocHoSo(text, profile);
    setProfile(hoSoMoi);

    try {
      const d = await hoiBff(text, hoSoMoi);
      setTreMs(d.ms);

      if (d.dang === "hoi_ho_so") {
        them({
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "hoi-ho-so",
          noiDung: d.noi_dung,
          dangHoi: [],
        });
      } else {
        them({
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "ket-qua",
          noiDung: d.noi_dung,
          daQuet: 2646,
          chuongTrinh: d.chuong_trinh.map((c) => ({
            id: c.id,
            ten: c.ten,
            coQuan: c.co_quan,
            loai: "uu-dai-thue" as const,
            giaTri: c.gia_tri,
            giaTriKyVong: null,
            giaTriHienThi: c.gia_tri_ky_vong,
            hanNop: c.han_nop ?? undefined,
            doTinCay: c.do_tin_cay,
            duDieuKien: c.du_dieu_kien,
            thieu: c.thieu,
            hieuLucDaDoiChieu: false,
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
              },
            })),
          })),
        });
      }
    } catch (e) {
      them({
        id: nextId(),
        vaiTro: "tro-ly",
        dang: "van-ban",
        noiDung:
          e instanceof BffLoi
            ? e.message
            : "Có lỗi khi gọi hệ thống. Vui lòng thử lại.",
        grounding: "chua-du-can-cu",
      });
    } finally {
      setDangBan(false);
    }
  }

  const chuaHoi = messages.length === 1;

  return (
    <main className="flex h-dvh flex-col">
      <header className="border-b border-border-subtle bg-surface">
        <div className="mx-auto flex max-w-3xl items-center gap-2.5 px-4 py-3">
          <span className="flex size-7 items-center justify-center rounded-md bg-brand-600 font-bold text-white">
            P
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-[15px] font-semibold leading-none text-text">
              PolicyRadar
            </h1>
            <p className="mt-1 text-[11px] leading-none text-text-muted">
              Tìm đúng chính sách bạn đủ điều kiện — có căn cứ tới từng điều khoản
            </p>
          </div>
          {treMs !== null && (
            <span
              className="shrink-0 rounded border border-border-subtle px-1.5 py-0.5 font-mono text-[10px] text-text-muted"
              title="Thời gian phản hồi. Đề bài yêu cầu ≤ 5.000ms cho câu đơn giản."
            >
              {treMs}ms
            </span>
          )}
        </div>
      </header>

      <ProfileRibbon profile={profile} />

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-4">
          {messages.map((m) => (
            <ChatMessage key={m.id} m={m} />
          ))}
          {dangBan && (
            <p className="text-[12px] text-text-muted">Đang quét kho văn bản…</p>
          )}
          <div ref={cuoiRef} />
        </div>
      </div>

      <ChatInput onGui={xuLy} dangBan={dangBan} goiY={chuaHoi ? GOI_Y : []} />
    </main>
  );
}
