/**
 * PolicyRadar — mô hình dữ liệu lõi.
 *
 * Nguyên tắc: mọi khẳng định về chính sách PHẢI đi kèm Citation trỏ tới
 * điều–khoản–điểm trong kho văn bản. Không có căn cứ thì không khẳng định.
 */

/** Trích dẫn tới đúng điều–khoản–điểm của một văn bản pháp luật. */
export type Citation = {
  id: string;
  /** Số hiệu văn bản, vd "Nghị định 80/2021/NĐ-CP" */
  vanBan: string;
  /** Cơ quan ban hành */
  coQuan?: string;
  dieu?: string;
  khoan?: string;
  diem?: string;
  /** Trích nguyên văn đoạn làm căn cứ */
  trichDan: string;
  /** ID document trong corpus vbpl-vn — để truy ngược */
  docId?: string;
  url?: string;
};

/** Hồ sơ doanh nghiệp — các slot AI cần hỏi đủ trước khi match. */
export type Profile = {
  nganh?: string;
  /** vốn điều lệ, VND */
  von?: number;
  nhanSu?: number;
  /** chi R&D theo % doanh thu */
  chiRDPhanTram?: number;
  diaBan?: string;
  fdi?: boolean;
};

export type ProfileField = keyof Profile;

export const PROFILE_FIELDS: { key: ProfileField; nhan: string; goiY: string }[] = [
  { key: "nganh", nhan: "Ngành", goiY: "vd: sản xuất phần mềm" },
  { key: "von", nhan: "Vốn điều lệ", goiY: "vd: 20 tỷ" },
  { key: "nhanSu", nhan: "Nhân sự", goiY: "vd: 45 người" },
  { key: "chiRDPhanTram", nhan: "Chi R&D", goiY: "% doanh thu" },
  { key: "diaBan", nhan: "Địa bàn", goiY: "vd: Hà Nội" },
  { key: "fdi", nhan: "Vốn FDI", goiY: "có / không" },
];

/** Một điều kiện thụ hưởng đã được đối chiếu với hồ sơ. */
export type DieuKien = {
  /** Điều kiện theo luật, vd "Chi R&D ≥ 1% doanh thu" */
  yeuCau: string;
  /** Giá trị tương ứng trong hồ sơ DN, vd "2,5%" */
  hoSo: string;
  trangThai: "dat" | "khong-dat" | "chua-du-thong-tin";
  /** Căn cứ pháp lý cho ĐIỀU KIỆN này (không phải cho cả chương trình) */
  citation: Citation;
};

export type LoaiChuongTrinh =
  | "uu-dai-thue"
  | "quy-ho-tro"
  | "tai-tro"
  | "ho-tro-lai-suat"
  | "ho-tro-chi-phi";

export const LOAI_NHAN: Record<LoaiChuongTrinh, string> = {
  "uu-dai-thue": "Ưu đãi thuế",
  "quy-ho-tro": "Quỹ hỗ trợ",
  "tai-tro": "Tài trợ",
  "ho-tro-lai-suat": "Hỗ trợ lãi suất",
  "ho-tro-chi-phi": "Hỗ trợ chi phí",
};

/** Một chương trình ưu đãi/quỹ mà matcher trả về. */
export type ChuongTrinh = {
  id: string;
  ten: string;
  coQuan: string;
  loai: LoaiChuongTrinh;
  /** Mô tả giá trị bằng lời — luôn phải có căn cứ */
  giaTri: string;
  /** Giá trị kỳ vọng (VND) dùng để XẾP HẠNG. null = chưa lượng hoá được. */
  giaTriKyVong: number | null;
  /** Giá trị kỳ vọng đã format sẵn ở backend ("3,4 tỷ đ") — dùng khi có. */
  giaTriHienThi?: string;
  hanNop?: string;
  /** Vì sao DN đủ điều kiện — từng dòng có citation riêng */
  dieuKien: DieuKien[];
  /** Độ tin cậy của phép khớp, 0..1 */
  doTinCay: number;
  /** Backend đã kết luận đủ điều kiện chưa (tất định, không phải LLM đoán) */
  duDieuKien?: boolean;
  /** Tên ĐÍCH DANH điều kiện chưa đạt — "chưa, vì thiếu Y" */
  thieu?: string[];
  /** true nếu hiệu lực đã được đối chiếu với API vbpl.vn */
  hieuLucDaDoiChieu: boolean;
};

/** Nhãn kiểm chứng gắn lên mỗi câu trả lời của AI. */
export type TrangThaiGrounding = "du-can-cu" | "chua-du-can-cu" | "guard-chan";

export type Message =
  | { id: string; vaiTro: "nguoi-dung"; noiDung: string }
  | {
      id: string;
      vaiTro: "tro-ly";
      dang: "van-ban";
      noiDung: string;
      grounding: TrangThaiGrounding;
      citations?: Citation[];
      /** Đoạn bị guard tô đỏ (số/điều luật không có căn cứ) */
      canhBao?: string;
    }
  | {
      id: string;
      vaiTro: "tro-ly";
      dang: "hoi-ho-so";
      noiDung: string;
      dangHoi: ProfileField[];
    }
  | {
      id: string;
      vaiTro: "tro-ly";
      dang: "ket-qua";
      noiDung: string;
      chuongTrinh: ChuongTrinh[];
      /** tổng số văn bản đã quét để ra kết quả này */
      daQuet: number;
    };
