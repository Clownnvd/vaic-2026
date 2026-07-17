# Deploy Railway — PolicyRadar (VAIC P1)

Hai service trên Railway từ cùng repo (monorepo).

## Service 1 — BFF (FastAPI, Python)
- **Root Directory**: `.` (gốc repo)
- **Build**: tự nhận `requirements.txt` + `runtime.txt` (Python 3.11)
- **Start**: `Procfile` → `uvicorn bff.main:app --host 0.0.0.0 --port $PORT`
- **Biến môi trường**:
  - `OPENAI_API_KEY` = key OpenAI (⚠️ key cũ đã lộ trong chat — **rotate key mới**)
  - `USE_LLM` = `1` (bật diễn giải GPT-4o + guard số)
  - `USE_GATEWAY` = `0` (gọi thẳng; nếu nộp cần proxy có log thì dựng LiteLLM riêng)
- **Data**: `data/corpus_slim/` (0.27MB metadata, đã commit) + `data/giam_sat_quet.json`
  + 2 cache vbpl flagship (đã commit). LuatIndex tự fallback corpus_slim khi thiếu splits_dn.

## Service 2 — Frontend (Next.js 16, Node)
- **Root Directory**: `frontend`
- **Build**: `npm ci && npm run build`
- **Start**: `npm run start` (đã dùng `$PORT`)
- **Biến môi trường (BUILD-TIME)**:
  - `NEXT_PUBLIC_BFF_URL` = URL public của Service 1 (vd `https://policyradar-bff.up.railway.app`)

## Thứ tự
1. Deploy BFF trước → lấy URL public.
2. Đặt `NEXT_PUBLIC_BFF_URL` = URL đó cho Frontend → deploy Frontend.

## Kiểm nhanh sau deploy
- `GET {BFF}/health` → `{"ok":true,"so_chuong_trinh":2}`
- Mở Frontend → chat "công ty phần mềm Hà Nội 45 lao động doanh thu 50 tỷ..." → ra 2 chương trình.
- Trang Giám sát → thấy mục "156 hết hiệu lực".
