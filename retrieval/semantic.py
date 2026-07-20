"""Tìm ngữ nghĩa (semantic search) trên kho luật bằng FAISS.

Vai trò: đứng TRƯỚC bộ khớp tất định, lo "tìm ĐÚNG văn bản/điều liên quan"
theo nghĩa của câu hỏi, thay cho lọc từ khóa cứng. KHÔNG quyết eligibility,
KHÔNG sinh số — phần đó vẫn của matcher + guard. Đây là lớp truy hồi, có thể
tắt (fallback về lọc từ khóa) nếu chưa build index.

Embedder để SWAP được: mặc định OpenAI text-embedding-3-small (nhanh, rẻ, đa
ngữ); có thể đổi sang model local (sentence-transformers) cho chạy offline.
"""

from __future__ import annotations

import json
import os

import numpy as np

EMB_MODEL = "text-embedding-3-small"
_DIM_CACHE: int | None = None


def _ensure_key() -> None:
    """Nạp OPENAI_API_KEY từ .env nếu chưa có trong env — KHÔNG in ra."""
    if os.getenv("OPENAI_API_KEY"):
        return
    for path in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8-sig"):
                line = line.strip()
                if line.startswith("OPENAI_API_KEY="):
                    os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
                    return


def embed_texts(texts: list[str], batch: int = 96) -> np.ndarray:
    """Nhúng danh sách câu → ma trận đã chuẩn hoá (để dùng inner product = cosine)."""
    _ensure_key()
    from openai import OpenAI

    cli = OpenAI()
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        chunk = [(t or " ")[:6000] for t in texts[i : i + batch]]
        r = cli.embeddings.create(model=EMB_MODEL, input=chunk)
        out.extend(d.embedding for d in r.data)
    arr = np.asarray(out, dtype="float32")
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def _meta_row(r: dict) -> dict:
    """Metadata giữ kèm mỗi vector — đủ để dựng thẻ văn bản như tab tra cứu."""
    return {
        "item_id": r.get("item_id"),
        "so": r.get("doc_number_str"),
        "title": r.get("title"),
        "loai": r.get("doc_type"),
        "linh_vuc": r.get("legal_area"),
        "co_quan": r.get("issuing_authority"),
        "nam": r.get("year"),
        "ngay": r.get("issue_date"),
        "tom_tat": (r.get("summary") or "")[:280],
        "url": r.get("source_url"),
    }


_META_COLS = [
    "item_id", "doc_number_str", "title", "doc_type", "legal_area",
    "issuing_authority", "issue_date", "year", "summary", "source_url",
]


def rebuild_meta(parquet_path: str, out_dir: str, limit: int | None = None) -> int:
    """Dựng lại meta.json từ parquet — KHÔNG nhúng lại (giữ index.faiss cũ).

    An toàn vì thứ tự dòng khớp: cùng parquet, cùng cách đọc, cùng limit → dòng i
    của meta vẫn ứng vector i của index. Dùng khi đổi trường meta mà vector không đổi.
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(parquet_path, columns=_META_COLS).to_pylist()
    if limit:
        rows = rows[:limit]
    meta = [_meta_row(r) for r in rows]
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return len(meta)


def _search_text(row: dict) -> str:
    """Câu đại diện cho một văn bản để nhúng: tiêu đề + tóm tắt + đầu toàn văn."""
    parts = [
        row.get("title") or "",
        row.get("summary") or "",
        (row.get("markdown") or "")[:1200],
    ]
    return "\n".join(p for p in parts if p)


def build(parquet_path: str, out_dir: str, limit: int | None = None) -> tuple[int, int]:
    """Đọc parquet → nhúng từng văn bản → dựng FAISS index → lưu index + meta."""
    import faiss
    import pyarrow.parquet as pq

    os.makedirs(out_dir, exist_ok=True)
    cols = [
        "item_id", "doc_number_str", "title", "doc_type", "legal_area",
        "issuing_authority", "issue_date", "year", "summary", "markdown", "source_url",
    ]
    rows = pq.read_table(parquet_path, columns=cols).to_pylist()
    if limit:
        rows = rows[:limit]
    emb = embed_texts([_search_text(r) for r in rows])
    idx = faiss.IndexFlatIP(emb.shape[1])
    idx.add(emb)
    faiss.write_index(idx, os.path.join(out_dir, "index.faiss"))
    meta = [_meta_row(r) for r in rows]
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return len(rows), int(emb.shape[1])


class SemanticIndex:
    """Load index đã build + tìm theo nghĩa."""

    def __init__(self, out_dir: str):
        import faiss

        self.idx = faiss.read_index(os.path.join(out_dir, "index.faiss"))
        self.meta = json.load(open(os.path.join(out_dir, "meta.json"), encoding="utf-8"))

    def search(self, query: str, k: int = 5) -> list[dict]:
        q = embed_texts([query])
        scores, ids = self.idx.search(q, k)
        out: list[dict] = []
        for score, i in zip(scores[0], ids[0]):
            if i < 0:
                continue
            m = dict(self.meta[i])
            m["score"] = round(float(score), 4)
            out.append(m)
        return out


if __name__ == "__main__":  # tiện build/test nhanh
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        n, d = build("data/vbpl_flagship.parquet", "data/faiss", limit=lim)
        print(f"BUILT {n} văn bản, dim={d} → data/faiss/")
    elif len(sys.argv) > 1 and sys.argv[1] == "rebuild-meta":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        n = rebuild_meta("data/vbpl_flagship.parquet", "data/faiss", limit=lim)
        print(f"REBUILT meta {n} văn bản → data/faiss/meta.json")
    elif len(sys.argv) > 1 and sys.argv[1] == "search":
        si = SemanticIndex("data/faiss")
        for r in si.search(" ".join(sys.argv[2:]) or "ưu đãi thuế cho doanh nghiệp công nghệ cao"):
            print(f"  {r['score']}  {r['so']}  {(r['title'] or '')[:70]}")
