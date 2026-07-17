"use client";

import { useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { ProfileRibbon } from "@/components/ProfileRibbon";
import { bocHoSo, thieuTruong } from "@/lib/extract";
import { SEED_CHUONG_TRINH } from "@/lib/seed";
import { PROFILE_FIELDS, type Message, type Profile } from "@/lib/types";

/** Đủ 4 trường này là matcher chạy được; 2 trường còn lại chỉ tinh chỉnh thứ hạng. */
const TRUONG_LOI = ["nganh", "von", "nhanSu", "chiRDPhanTram"] as const;

const LOI_MO_DAU =
  "Để tìm đúng ưu đãi và quỹ mà bạn đủ điều kiện, cho mình biết vài thông tin về doanh nghiệp: ngành, vốn điều lệ, số nhân sự, chi cho R&D (theo % doanh thu), địa bàn, và có vốn FDI không?\n\nBạn cứ mô tả bằng một câu tự nhiên cũng được.";

const GOI_Y = [
  "Bên mình làm phần mềm ở Hà Nội, vốn 20 tỷ, 45 người, chi R&D khoảng 2,5% doanh thu, không có vốn FDI",
  "Công ty bán dẫn tại Bắc Ninh, vốn 500 tỷ, 300 nhân sự, R&D 8%, có vốn FDI",
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
  const cuoiRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cuoiRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function them(m: Message) {
    setMessages((prev) => [...prev, m]);
  }

  function xuLy(text: string) {
    them({ id: nextId(), vaiTro: "nguoi-dung", noiDung: text });
    setDangBan(true);

    // TẠM: bóc hồ sơ tại client. Bản thật do agent lo (xem lib/extract.ts).
    const hoSoMoi = bocHoSo(text, profile);
    setProfile(hoSoMoi);

    const thieuLoi = TRUONG_LOI.filter((k) => hoSoMoi[k] === undefined);

    setTimeout(() => {
      if (thieuLoi.length > 0) {
        const ten = thieuLoi
          .map((k) => PROFILE_FIELDS.find((f) => f.key === k)!.nhan.toLowerCase())
          .join(", ");
        them({
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "hoi-ho-so",
          noiDung: `Mình ghi nhận rồi. Còn thiếu ${ten} — bạn bổ sung giúp mình để quét cho chính xác nhé.`,
          dangHoi: thieuLoi.slice(),
        });
      } else {
        const conThieu = thieuTruong(hoSoMoi);
        const ghiChu =
          conThieu.length > 0
            ? ` Còn thiếu ${conThieu
                .map((k) => PROFILE_FIELDS.find((f) => f.key === k)!.nhan.toLowerCase())
                .join(", ")} — bổ sung thì thứ hạng sẽ chuẩn hơn.`
            : "";

        const ketQua = [...SEED_CHUONG_TRINH].sort(
          (a, b) => (b.giaTriKyVong ?? 0) - (a.giaTriKyVong ?? 0),
        );

        them({
          id: nextId(),
          vaiTro: "tro-ly",
          dang: "ket-qua",
          noiDung: `Với hồ sơ này, mình tìm thấy ${ketQua.length} chương trình đáng theo đuổi.${ghiChu}`,
          chuongTrinh: ketQua,
          daQuet: 158822,
        });
      }
      setDangBan(false);
    }, 420);
  }

  const chuaHoi = messages.length === 1;

  return (
    <main className="flex h-dvh flex-col">
      <header className="border-b border-border-subtle bg-surface">
        <div className="mx-auto flex max-w-3xl items-center gap-2.5 px-4 py-3">
          <span className="flex size-7 items-center justify-center rounded-md bg-brand-600 font-bold text-white">
            P
          </span>
          <div>
            <h1 className="text-[15px] font-semibold leading-none text-text">
              PolicyRadar
            </h1>
            <p className="mt-1 text-[11px] leading-none text-text-muted">
              Tìm đúng chính sách bạn đủ điều kiện — có căn cứ tới từng điều khoản
            </p>
          </div>
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
