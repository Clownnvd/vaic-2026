# Deploy Railway — PolicyRadar (VAIC P1)

Hai service trên Railway từ cùng repo (monorepo).

## 🔗 Bản LIVE (đang chạy)
- **Ứng dụng**: https://vaic-2026-production.up.railway.app
- **BFF**: https://web-production-db4aa.up.railway.app — `GET /health` → `{"ok":true,"service":"policyradar-bff","so_chuong_trinh":7}`

## Service 1 — BFF (FastAPI, Python)
- **Root Directory**: `.` (gốc repo)
- **Build**: tự nhận `requirements.txt` + `.python-version` (Python 3.11)
- **Start**: `Procfile` → `uvicorn bff.main:app --host 0.0.0.0 --port $PORT`
- **Biến môi trường**:
  - `OPENAI_API_KEY` = key OpenAI (⚠️ key cũ đã lộ trong chat — **rotate key mới**)
  - `USE_LLM` = `1` (bật diễn giải GPT-4o + guard số)
  - `USE_GATEWAY` = `0` (gọi thẳng; nếu nộp cần proxy có log thì dựng LiteLLM riêng)
- **Data**: `data/corpus_slim/` (0.27MB metadata, đã commit) + `data/giam_sat_quet.json`
  + 2 cache vbpl flagship (đã commit). LuatIndex tự fallback corpus_slim khi thiếu splits_dn.

## Service 2 — Frontend (Next.js 16, Node)
- **Root Directory**: `frontend`
- **Package manager**: **pnpm** (có `pnpm-lock.yaml`, đã pin `packageManager: pnpm@9.15.9`).
  ⚠️ pnpm ≥10 làm `sharp` fail build — Railway tự nhận pnpm, ĐỪNG ép npm.
- **Build**: `pnpm install && pnpm build` (nixpacks tự chạy)
- **Start**: `pnpm start` (đã dùng `$PORT`)
- **Biến môi trường (BUILD-TIME)**:
  - `NEXT_PUBLIC_BFF_URL` = URL public của Service 1 (vd `https://policyradar-bff.up.railway.app`)

## Thứ tự
1. Deploy BFF trước → lấy URL public.
2. Đặt `NEXT_PUBLIC_BFF_URL` = URL đó cho Frontend → deploy Frontend.

## Service 3 (tuỳ chọn) — Cron cập nhật giám sát ②
Để giám sát "sống" (cập nhật hiệu lực hằng ngày) thay vì snapshot tĩnh:
- **Root Directory**: `.`
- **Cron schedule**: `0 2 * * *` (02:00 mỗi ngày)
- **Command**: `python scripts/cron_giam_sat.py --lo 300`
- Mỗi lần: quét FRESH các VB đang theo dõi (bắt đổi trạng thái) + 300 VB xoay
  vòng (rolling) → sau ~9 ngày phủ hết kho. Diff `còn→hết` = văn bản VỪA CHẾT,
  ghi `data/giam_sat_thay_doi.json`. BFF đọc `giam_sat_quet.json` đã cập nhật.
- KHÔNG cào real-time 24/7 (không cần + tốn); API vbpl.vn nhanh (~300 VB/12s).

## Kiểm nhanh sau deploy
- `GET {BFF}/health` → `{"ok":true,"service":"policyradar-bff","so_chuong_trinh":7}`
- Mở Frontend → chat "doanh nghiệp sản xuất, 45 lao động, doanh thu 50 tỷ, vốn 20 tỷ, có GCN DN KH&CN, doanh thu KH&CN 45%" → ra 7 chương trình.
- Trang Giám sát → 949 văn bản đối chiếu vbpl.vn (598 còn / 290 hết hiệu lực toàn bộ / 60 hết một phần / 1 chưa có hiệu lực), lọc Miền/Tỉnh + ghim.
