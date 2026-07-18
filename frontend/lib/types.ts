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

/** Lĩnh vực theo Điều 5 NĐ 80/2021 — CHỈ 2 nhóm, không phải ngành nghề tự do.
 *  Ngưỡng lao động khác nhau giữa 2 nhóm (200 vs 100) nên bắt buộc phải phân biệt. */
export type LinhVuc =
  | "nong_lam_thuy_san__cong_nghiep_xay_dung"
  | "thuong_mai_dich_vu";

/** Hồ sơ doanh nghiệp — các slot AI cần hỏi đủ trước khi match.
 *
 *  ⚠️ ĐÃ SỬA theo nguyên văn 80/2021/NĐ-CP + 13/2019/NĐ-CP. Bản cũ dựng quanh
 *  ĐIỀU KIỆN BỊA nên hỏi sai thứ:
 *    • `nhanSu` → `laoDongBhxh`: luật đếm "lao động CÓ THAM GIA BHXH bình quân
 *      năm", không phải đầu người. Hai đại lượng khác nhau.
 *    • `chiRDPhanTram` → `tyLeDtKhcn`: 13/2019 Đ12 K3 đòi doanh thu sản phẩm
 *      KH&CN ≥ 30% tổng doanh thu. "Chi R&D ≥ 1%" KHÔNG tồn tại trong văn bản.
 *    • thêm `doanhThu`: Đ5 dùng doanh thu ở MỌI ngưỡng — bản cũ không có field này.
 *    • thêm `linhVuc`: ngưỡng lao động đổi theo lĩnh vực.
 *    • thêm `nuLamChu`: Đ13 K2 nâng trần cho DN do phụ nữ làm chủ / nhiều lao
 *      động nữ / DN xã hội.
 */
export type Profile = {
  nganh?: string;
  linhVuc?: LinhVuc;
  /** tổng nguồn vốn của năm, VND */
  von?: number;
  /** tổng doanh thu của năm, VND */
  doanhThu?: number;
  /** lao động tham gia BHXH bình quân năm */
  laoDongBhxh?: number;
  /** doanh thu từ sản phẩm KH&CN, % tổng doanh thu */
  tyLeDtKhcn?: number;
  /** có Giấy chứng nhận doanh nghiệp KH&CN */
  coGcnKhcn?: boolean;
  /** do phụ nữ làm chủ / sử dụng nhiều lao động nữ / là DN xã hội */
  nuLamChu?: boolean;
  diaBan?: string;
  fdi?: boolean;
};

export type ProfileField = keyof Profile;

export const PROFILE_FIELDS: { key: ProfileField; nhan: string; goiY: string }[] = [
  { key: "linhVuc", nhan: "Lĩnh vực", goiY: "nông-lâm-thuỷ sản / CN-XD hay thương mại-dịch vụ" },
  { key: "laoDongBhxh", nhan: "Lao động BHXH", goiY: "bình quân năm, vd: 45 người" },
  { key: "doanhThu", nhan: "Doanh thu năm", goiY: "vd: 50 tỷ" },
  { key: "von", nhan: "Tổng nguồn vốn", goiY: "vd: 20 tỷ" },
  { key: "tyLeDtKhcn", nhan: "Doanh thu KH&CN", goiY: "% tổng doanh thu" },
  { key: "coGcnKhcn", nhan: "GCN DN KH&CN", goiY: "có / không" },
  { key: "nuLamChu", nhan: "Nữ làm chủ", goiY: "có / không — được nâng trần hỗ trợ" },
  { key: "nganh", nhan: "Ngành", goiY: "vd: sản xuất phần mềm" },
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
  /** Field người dùng cần khai để nâng độ tin cậy → 100% */
  canBoSung?: { field: string; nhan: string }[];
  /** true nếu hiệu lực đã được đối chiếu với API vbpl.vn */
  hieuLucDaDoiChieu: boolean;
  /** Trạng thái hiệu lực THẬT từ vbpl.vn (② của đề). undefined = chưa có. */
  hieuLuc?: HieuLuc;
};

/** Trạng thái hiệu lực văn bản — đối chiếu API vbpl.vn (Bộ Tư pháp). */
export type HieuLuc = {
  daDoiChieu: boolean;
  /** true=còn · false=hết · null=chưa xác định (KHÔNG đoán) */
  conHieuLuc: boolean | null;
  nhan: string;
  ma?: string;
  soQuanHe?: number;
  nguon?: string;
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
      /** Không đặt = câu trò chuyện/chuyển hướng (không badge). Đặt = câu có phán quyết. */
      grounding?: TrangThaiGrounding;
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
      /** ① LLM diễn giải luật + phán quyết guard lớp số */
      dienGiai?: DienGiai;
    };

/** Diễn giải LLM (① interpreting) đã qua guard kiểm số. */
export type DienGiai = {
  text: string;
  grounded: boolean;
  soBia: { raw: string; batDau: number; ketThuc: number }[];
  canhBao?: string | null;
};
