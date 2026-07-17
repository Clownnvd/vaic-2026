/**
 * ⚠️ SEED DỰNG UI — KHÔNG PHẢI NGUỒN SỰ THẬT. PHẢI THAY TRƯỚC KHI DEMO.
 *
 * File này chỉ để dựng và kiểm thử giao diện khi backend chưa xong.
 *
 * Tên chương trình + số hiệu văn bản dưới đây là các văn bản CÓ THẬT, nhưng:
 *   - Số điều/khoản/điểm CHƯA đối chiếu corpus  → đánh dấu `chuaVerify: true`
 *   - Đoạn `trichDan` là VĂN PLACEHOLDER, không phải trích nguyên văn
 *   - Trạng thái hiệu lực CHƯA join API vbpl.vn
 *
 * Trước khi lên sân khấu: mọi Citation phải sinh ra từ corpus `tmquan/vbpl-vn`
 * (document → điều → khoản → điểm) và trạng thái hiệu lực phải join vbpl.vn API.
 * Để nguyên seed này mà demo = bịa điều luật = đúng thứ sản phẩm này chống.
 */

import type { ChuongTrinh, Profile } from "./types";

export const SEED_CANH_BAO =
  "Dữ liệu seed dựng UI — trích dẫn chưa đối chiếu corpus. Thay trước khi demo.";

/** Hồ sơ mẫu để thử luồng: DN phần mềm, có R&D, không FDI. */
export const HO_SO_MAU: Profile = {
  nganh: "Sản xuất phần mềm",
  von: 20_000_000_000,
  nhanSu: 45,
  chiRDPhanTram: 2.5,
  diaBan: "Hà Nội",
  fdi: false,
};

export const SEED_CHUONG_TRINH: ChuongTrinh[] = [
  {
    id: "ct-dnkhcn",
    ten: "Ưu đãi thuế TNDN cho doanh nghiệp khoa học và công nghệ",
    coQuan: "Bộ Khoa học và Công nghệ",
    loai: "uu-dai-thue",
    giaTri: "Miễn 4 năm, giảm 50% trong 9 năm tiếp theo (theo điều kiện chứng nhận)",
    giaTriKyVong: 3_400_000_000,
    hanNop: "Nộp hồ sơ chứng nhận quanh năm",
    doTinCay: 0.86,
    hieuLucDaDoiChieu: false,
    dieuKien: [
      {
        yeuCau: "Doanh thu từ sản phẩm hình thành từ kết quả KH&CN đạt tỷ lệ tối thiểu",
        hoSo: "Chi R&D 2,5% doanh thu — cần bổ sung tỷ lệ doanh thu từ sản phẩm KH&CN",
        trangThai: "chua-du-thong-tin",
        citation: {
          id: "c1",
          vanBan: "Nghị định 13/2019/NĐ-CP",
          coQuan: "Chính phủ",
          dieu: "Điều 6",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:13-2019-ND-CP",
        },
      },
      {
        yeuCau: "Được cấp Giấy chứng nhận doanh nghiệp khoa học và công nghệ",
        hoSo: "Chưa có — đây là bước cần làm trước",
        trangThai: "khong-dat",
        citation: {
          id: "c2",
          vanBan: "Nghị định 13/2019/NĐ-CP",
          coQuan: "Chính phủ",
          dieu: "Điều 4",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:13-2019-ND-CP",
        },
      },
    ],
  },
  {
    id: "ct-dnnvv-tuvan",
    ten: "Hỗ trợ chi phí tư vấn và chuyển đổi số cho doanh nghiệp nhỏ và vừa",
    coQuan: "Bộ Kế hoạch và Đầu tư",
    loai: "ho-tro-chi-phi",
    giaTri: "Hỗ trợ một phần chi phí theo quy mô doanh nghiệp",
    giaTriKyVong: 480_000_000,
    doTinCay: 0.81,
    hieuLucDaDoiChieu: false,
    dieuKien: [
      {
        yeuCau: "Đáp ứng tiêu chí xác định doanh nghiệp nhỏ và vừa",
        hoSo: "45 nhân sự, vốn 20 tỷ — thuộc nhóm doanh nghiệp nhỏ/vừa",
        trangThai: "dat",
        citation: {
          id: "c3",
          vanBan: "Nghị định 80/2021/NĐ-CP",
          coQuan: "Chính phủ",
          dieu: "Điều 5",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:80-2021-ND-CP",
        },
      },
      {
        yeuCau: "Không phải doanh nghiệp có vốn nhà nước / thuộc diện loại trừ",
        hoSo: "Không FDI, không vốn nhà nước",
        trangThai: "dat",
        citation: {
          id: "c4",
          vanBan: "Luật Hỗ trợ doanh nghiệp nhỏ và vừa 04/2017/QH14",
          coQuan: "Quốc hội",
          dieu: "Điều 4",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:04-2017-QH14",
        },
      },
    ],
  },
  {
    id: "ct-844",
    ten: "Đề án 844 — Hỗ trợ hệ sinh thái khởi nghiệp đổi mới sáng tạo quốc gia",
    coQuan: "Bộ Khoa học và Công nghệ",
    loai: "tai-tro",
    giaTri: "Tài trợ theo nhiệm vụ được phê duyệt",
    giaTriKyVong: 900_000_000,
    hanNop: "Theo đợt công bố nhiệm vụ hằng năm",
    doTinCay: 0.72,
    hieuLucDaDoiChieu: false,
    dieuKien: [
      {
        yeuCau: "Là doanh nghiệp khởi nghiệp đổi mới sáng tạo hoặc tổ chức hỗ trợ khởi nghiệp",
        hoSo: "Sản xuất phần mềm, chi R&D 2,5% — cần đối chiếu tiêu chí ĐMST",
        trangThai: "chua-du-thong-tin",
        citation: {
          id: "c5",
          vanBan: "Quyết định 844/QĐ-TTg",
          coQuan: "Thủ tướng Chính phủ",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:844-QD-TTg",
        },
      },
    ],
  },
  {
    id: "ct-natif",
    ten: "Quỹ Đổi mới công nghệ quốc gia — hỗ trợ đổi mới công nghệ",
    coQuan: "Quỹ Đổi mới công nghệ quốc gia (NATIF)",
    loai: "quy-ho-tro",
    giaTri: "Hỗ trợ lãi suất vay / tài trợ một phần kinh phí nhiệm vụ",
    giaTriKyVong: 1_200_000_000,
    hanNop: "Theo đợt tiếp nhận hồ sơ",
    doTinCay: 0.68,
    hieuLucDaDoiChieu: false,
    dieuKien: [
      {
        yeuCau: "Có nhiệm vụ đổi mới công nghệ được thẩm định",
        hoSo: "Chưa có hồ sơ nhiệm vụ",
        trangThai: "chua-du-thong-tin",
        citation: {
          id: "c6",
          vanBan: "Nghị định 76/2018/NĐ-CP",
          coQuan: "Chính phủ",
          trichDan: "[PLACEHOLDER — chờ trích nguyên văn từ corpus vbpl-vn]",
          docId: "vbpl:76-2018-ND-CP",
        },
      },
    ],
  },
];
