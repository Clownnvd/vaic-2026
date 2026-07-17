"""Dựng corpus flagship cho PolicyRadar từ HuggingFace `tmquan/vbpl-vn`.

Chiến lược TẢI–LỌC–XOÁ: mỗi shard tải về temp → lọc → ghi rows khớp vào writer
→ xoá shard. Không bao giờ ôm 2GB cùng lúc.

Lọc 3 tầng:
  1. markdown chạm ≥1 keyword chính sách (so trên bản đã lower)
  2. doc_type ∈ {nghi_dinh, thong_tu, quyet_dinh, nghi_quyet}  — bỏ nhiễu
  3. year ≥ 2018                                              — bỏ văn bản cổ

⚠️ Dataset KHÔNG có field hiệu lực (còn/hết). Bước này chỉ lấy corpus;
   trạng thái hiệu lực phải join API vbpl.vn ở phần monitoring.

⚠️ Shard xếp KHÔNG đều (shard 0 toàn văn bản 1950). Phải duyệt đủ 32 shard,
   cấm suy con số từ một shard.

Chạy:
    uv run --python 3.11 --with pyarrow python scripts/build_corpus.py
    uv run --python 3.11 --with pyarrow python scripts/build_corpus.py --shards 2   # thử nhanh
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

BASE_URL = "https://huggingface.co/datasets/tmquan/vbpl-vn/resolve/main"
TONG_SHARD = 32

KEYWORDS = [
    "công nghệ cao",
    "doanh nghiệp nhỏ và vừa",
    "ưu đãi",
    "đổi mới sáng tạo",
    "khởi nghiệp",
    "hỗ trợ doanh nghiệp",
    "chuyển đổi số",
    "khoa học và công nghệ",
]

# ⚠️ SỬA 17/07: THÊM "luat".
# Bản đầu chỉ có 4 loại → tự tay loại bỏ LUẬT, văn bản có hiệu lực CAO NHẤT.
# Hậu quả thật: Luật CNC 133/2025, Luật Đầu tư 143/2025, Luật TNDN 67/2025,
# Luật KH,CN&ĐMST 93/2025 đều "không có trong corpus" — nhưng là do MÌNH loại,
# không phải dump thiếu. Matcher không trích được Luật = trích thiếu tầng cao nhất.
DOC_TYPES = ["luat", "nghi_dinh", "thong_tu", "quyet_dinh", "nghi_quyet"]
NAM_TOI_THIEU = 2018

# Cột đọc từ shard (đọc thừa = tốn RAM vì markdown rất nặng)
COLS_DOC = [
    "item_id",
    "doc_number",
    "title",
    "doc_type",
    "legal_type",
    "legal_area",
    "issuing_authority",
    "issue_date",
    "year",
    "summary",
    "markdown",
    "structure_json",
    "source_url",
]

# Schema đầu ra cố định — chốt cứng để 32 shard ghi chung 1 file không vênh
OUT_SCHEMA = pa.schema(
    [
        ("item_id", pa.string()),
        ("doc_number", pa.list_(pa.string())),
        ("doc_number_str", pa.string()),
        ("title", pa.string()),
        ("doc_type", pa.string()),
        ("legal_type", pa.string()),
        ("legal_area", pa.string()),
        ("issuing_authority", pa.string()),
        ("issue_date", pa.string()),
        ("year", pa.int32()),
        ("summary", pa.string()),
        ("markdown", pa.string()),
        ("structure_json", pa.string()),
        ("source_url", pa.string()),
    ]
)


def nam_max_shard(i: int) -> int | None:
    """Đọc footer parquet qua HTTP range → year lớn nhất của shard. Vài KB, không tải file.

    Parquet lưu min/max từng cột trong footer. Nếu year_max < 2018 thì shard đó
    CHẮC CHẮN không có dòng nào lọt lọc → khỏi tải 55MB.
    Đây là suy luận từ thống kê chính xác, KHÔNG phải ngoại suy mẫu.
    Trả None nếu không đọc được stats → cứ tải cho an toàn.
    """
    try:
        import fsspec

        url = f"{BASE_URL}/documents-{i:05d}-of-{TONG_SHARD:05d}.parquet"
        with fsspec.filesystem("http").open(url, "rb") as f:
            pf = pq.ParquetFile(f)
            idx = pf.schema_arrow.get_field_index("year")
            hi = None
            for rg in range(pf.num_row_groups):
                st = pf.metadata.row_group(rg).column(idx).statistics
                if st is None or not st.has_min_max:
                    return None  # thiếu stats → không dám kết luận
                hi = st.max if hi is None else max(hi, st.max)
            return hi
    except Exception:  # noqa: BLE001
        return None


def tai_shard(i: int, dich: Path, thu_lai: int = 3) -> None:
    """Tải 1 shard về temp, có retry vì mạng hackathon hay rớt."""
    ten = f"documents-{i:05d}-of-{TONG_SHARD:05d}.parquet"
    url = f"{BASE_URL}/{ten}"

    for lan in range(1, thu_lai + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "policyradar/0.1"})
            with urllib.request.urlopen(req, timeout=120) as r, dich.open("wb") as f:
                tong = 0
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                    tong += len(chunk)
                    print(f"\r  tải {tong / 1e6:5.1f} MB", end="", flush=True)
            print(f"\r  tải {tong / 1e6:5.1f} MB ✓", flush=True)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"\n  ! lỗi mạng lần {lan}/{thu_lai}: {e}")
            dich.unlink(missing_ok=True)
            if lan == thu_lai:
                raise
            time.sleep(3 * lan)


def loc_bang(tbl: pa.Table) -> tuple[pa.Table, dict[str, int]]:
    """Lọc 3 tầng, trả về (bảng khớp, số lần chạm từng keyword)."""
    md_lower = pc.utf8_lower(tbl["markdown"])

    mask_kw = None
    dem_kw: dict[str, int] = {}
    for kw in KEYWORDS:
        m = pc.fill_null(pc.match_substring(md_lower, kw.lower()), False)
        dem_kw[kw] = pc.sum(pc.cast(m, pa.int32())).as_py() or 0
        mask_kw = m if mask_kw is None else pc.or_(mask_kw, m)

    mask_type = pc.is_in(tbl["doc_type"], value_set=pa.array(DOC_TYPES))
    mask_year = pc.greater_equal(tbl["year"], NAM_TOI_THIEU)

    mask = pc.and_(pc.fill_null(mask_kw, False), pc.fill_null(mask_type, False))
    mask = pc.and_(mask, pc.fill_null(mask_year, False))

    return tbl.filter(mask), dem_kw


def chuan_hoa(tbl: pa.Table) -> pa.Table:
    """Thêm doc_number_str (join list) rồi ép về OUT_SCHEMA."""
    dn_str = pc.binary_join(pc.cast(tbl["doc_number"], pa.list_(pa.string())), ", ")
    tbl = tbl.append_column("doc_number_str", dn_str)
    return tbl.select(OUT_SCHEMA.names).cast(OUT_SCHEMA)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=TONG_SHARD, help="số shard duyệt")
    ap.add_argument("--start", type=int, default=0, help="bắt đầu từ shard nào")
    ap.add_argument("--out", type=Path, default=Path("./data"))
    ap.add_argument(
        "--no-skip",
        action="store_true",
        help="tải hết, không dùng footer để bỏ shard (dùng khi nghi ngờ stats)",
    )
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    f_parquet = args.out / "vbpl_flagship.parquet"
    f_jsonl = args.out / "vbpl_flagship.jsonl"
    tmp = args.out / "_shard_tmp.parquet"

    writer: pq.ParquetWriter | None = None
    tong_doc = 0
    tong_khop = 0
    dem_kw_tong: dict[str, int] = {k: 0 for k in KEYWORDS}
    dem_type: dict[str, int] = {}
    nam_min: int | None = None
    nam_max: int | None = None
    bo_qua: list[int] = []
    t0 = time.time()

    het = min(args.start + args.shards, TONG_SHARD)
    print(f"Corpus flagship — duyệt shard {args.start}..{het - 1} / {TONG_SHARD}")
    print(f"Lọc: keyword({len(KEYWORDS)}) ∧ doc_type∈{DOC_TYPES} ∧ year≥{NAM_TOI_THIEU}\n")

    try:
        for i in range(args.start, het):
            print(f"[shard {i:02d}]", end=" ", flush=True)

            if not args.no_skip:
                hi = nam_max_shard(i)
                if hi is not None and hi < NAM_TOI_THIEU:
                    bo_qua.append(i)
                    print(f"bỏ qua — year_max={hi} < {NAM_TOI_THIEU} (khỏi tải 55MB)")
                    continue
            print()

            tai_shard(i, tmp)

            pf = pq.ParquetFile(tmp)
            khop_shard = 0
            for rg in range(pf.num_row_groups):
                tbl = pf.read_row_group(rg, columns=COLS_DOC)
                tong_doc += tbl.num_rows

                # theo dõi dải năm — để biết shard nào chứa gì, không đoán mò
                y_lo = pc.min(tbl["year"]).as_py()
                y_hi = pc.max(tbl["year"]).as_py()
                if y_lo is not None:
                    nam_min = y_lo if nam_min is None else min(nam_min, y_lo)
                if y_hi is not None:
                    nam_max = y_hi if nam_max is None else max(nam_max, y_hi)

                loc, dem_kw = loc_bang(tbl)
                for k, v in dem_kw.items():
                    dem_kw_tong[k] += v

                if loc.num_rows:
                    ra = chuan_hoa(loc)
                    if writer is None:
                        writer = pq.ParquetWriter(f_parquet, OUT_SCHEMA, compression="zstd")
                    writer.write_table(ra)
                    khop_shard += ra.num_rows

                    for x in pc.value_counts(loc["doc_type"]):
                        k = x["values"].as_py()
                        dem_type[k] = dem_type.get(k, 0) + x["counts"].as_py()

                del tbl, loc

            tong_khop += khop_shard
            pf.close()
            tmp.unlink(missing_ok=True)  # XOÁ ngay — không ôm 2GB
            print(
                f"  +{khop_shard:4d} khớp  |  cộng dồn {tong_khop:6d}/{tong_doc:6d}"
                f"  |  năm {nam_min}–{nam_max}\n"
            )
    finally:
        if writer is not None:
            writer.close()
        tmp.unlink(missing_ok=True)

    def in_thong_ke() -> None:
        print(f"\n  Dải năm đã gặp: {nam_min}–{nam_max}")
        print("\n  Chạm keyword (TRƯỚC lọc type/year):")
        for k, v in sorted(dem_kw_tong.items(), key=lambda x: -x[1]):
            print(f"    {k:26} {v:6,}")

    if tong_khop == 0:
        print(f"0/{tong_doc:,} văn bản khớp cả 3 tầng lọc.")
        in_thong_ke()
        print(
            "\n  → Nếu keyword có chạm mà vẫn 0 khớp: shard này toàn văn bản cũ,"
            f"\n    bị chặn bởi year≥{NAM_TOI_THIEU}. Thử --start ở shard cao hơn."
        )
        return

    # JSONL để đọc bằng mắt: bỏ markdown/structure_json (quá nặng), giữ preview
    print("Ghi JSONL (preview, không kèm toàn văn)…")
    tbl = pq.read_table(f_parquet)
    with f_jsonl.open("w", encoding="utf-8") as f:
        for row in tbl.select(
            [
                "item_id",
                "doc_number_str",
                "title",
                "doc_type",
                "issuing_authority",
                "issue_date",
                "year",
                "legal_area",
                "summary",
                "source_url",
            ]
        ).to_pylist():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    mb_p = f_parquet.stat().st_size / 1e6
    mb_j = f_jsonl.stat().st_size / 1e6

    print("\n" + "=" * 58)
    print(f"XONG sau {time.time() - t0:.0f}s")
    print(f"  Shard tải    : {het - args.start - len(bo_qua)}/{het - args.start}")
    if bo_qua:
        print(f"  Shard bỏ qua : {len(bo_qua)} (year_max<{NAM_TOI_THIEU}) → {bo_qua}")
    print(f"  Đã quét      : {tong_doc:,} văn bản")
    print(f"  Subset khớp  : {tong_khop:,} văn bản  ({tong_khop / tong_doc * 100:.1f}%)")
    print(f"  Parquet      : {f_parquet}  ({mb_p:.1f} MB)")
    print(f"  JSONL        : {f_jsonl}  ({mb_j:.1f} MB)")

    print("\n  Chạm keyword (trong phạm vi đã quét, TRƯỚC lọc type/year):")
    for k, v in sorted(dem_kw_tong.items(), key=lambda x: -x[1]):
        print(f"    {k:26} {v:6,}")

    print("\n  doc_type trong subset:")
    for k, v in sorted(dem_type.items(), key=lambda x: -x[1]):
        print(f"    {k:26} {v:6,}")

    if args.shards < TONG_SHARD:
        print(f"\n  ⚠ MỚI DUYỆT {args.shards}/{TONG_SHARD} SHARD — số trên KHÔNG dùng cho slide.")
        print("    Shard xếp không đều, phải chạy đủ 32 shard mới có full-count.")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
