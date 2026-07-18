# scripts/dev — script phát triển / thí nghiệm (KHÔNG thuộc đường chạy sản phẩm)

Đây là các script dùng MỘT LẦN trong 48h build: điều khiển GPU/container FPT để
train PhoBERT, tự động hoá trình duyệt (chụp ảnh demo), chẩn đoán corpus, tải/soi
dataset đánh giá (ViFactCheck, ViLegalNLI…), và các mảnh dò dữ liệu.

Chúng **không được `bff/`, `matcher/`, `guard/`, `frontend/` hay test import**, nên
được tách khỏi `scripts/` (nơi chỉ giữ script VẬN HÀNH) để repo gọn. Giữ lại trong
git vì chúng ghi lại quy trình (train guard, dựng corpus, đánh giá) — có thể chạy lại.

## Script VẬN HÀNH (vẫn ở `scripts/`, không nằm đây)
- `cron_giam_sat.py` — cron quét vbpl.vn cập nhật hiệu lực (② giám sát)
- `quet_hieu_luc.py` — đối chiếu trạng thái hiệu lực văn bản
- `moi_nguyen_van.py` — moi nguyên văn điều–khoản cho kho (curate)
- `build_corpus.py`, `split_corpus.py` — dựng/chia corpus
- `smoke_bff.py` — smoke test BFF
- `ham_cache_vbpl.py`, `filter_dn.py`, `kiem_dieu6.py`, `check_vb_moi*.py` — tiện ích giám sát/lọc
