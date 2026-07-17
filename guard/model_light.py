"""Model nhẹ: char n-gram hashing → MLP. Chạy CPU ~30 giây.

MỤC ĐÍCH: verify cả 4 đòn ra được biểu đồ TRƯỚC khi đốt GPU cho PhoBERT.
Nếu pipeline sai thì sai ở đây, mất 30 giây — không phải mất 20 phút GPU.

Đây là BASELINE thật, không phải đồ chơi: nó cũng là dòng "sàn" để so với
PhoBERT trong bảng ablation.
"""

from __future__ import annotations

from zlib import crc32

import numpy as np
import torch
import torch.nn as nn

DIM = 2048  # số chiều hash cho mỗi vế


def _ngram_hash(s: str, dim: int = DIM, n_lo: int = 3, n_hi: int = 5) -> np.ndarray:
    """char n-gram (3..5) → vector nhị phân đã hash. Không cần vocab, không cần fit.

    ⚠️ Dùng crc32 chứ KHÔNG dùng hash() của Python: hash() cho chuỗi bị salt ngẫu
    nhiên mỗi process → mỗi lần chạy ra feature khác nhau → model lưu ra vô dụng,
    train/infer lệch nhau. (Cùng lỗi đã tránh ở scripts/split_corpus.py.)
    """
    v = np.zeros(dim, dtype=np.float32)
    s = s.lower()
    for n in range(n_lo, n_hi + 1):
        for i in range(len(s) - n + 1):
            v[crc32(s[i : i + n].encode("utf-8", "ignore")) % dim] = 1.0
    return v


def featurize(premise: str, hypothesis: str) -> np.ndarray:
    """[premise, hypothesis, premise*hypothesis] — tích là tín hiệu GIAO NHAU.

    Với NLI grounding, thứ đáng quan tâm là: điều hypothesis nói CÓ trong premise không.
    Tích element-wise chính là 'n-gram nào xuất hiện ở cả hai'.
    """
    p = _ngram_hash(premise[:2000])
    h = _ngram_hash(hypothesis[:2000])
    return np.concatenate([p, h, p * h])


class GuardNhe(nn.Module):
    def __init__(self, d_in: int = DIM * 3, d_hid: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_hid),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(d_hid, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def grounding_margin_loss(logits: torch.Tensor, y: torch.Tensor, margin: float = 2.0) -> torch.Tensor:
    """Ép KHOẢNG CÁCH giữa logit đúng và logit sai ≥ margin.

    Cross-entropy chỉ cần đoán đúng lớp. Với guard, ta cần model TỰ TIN TÁCH BẠCH
    grounded vs bịa — vì ngưỡng refuse cắt trên khoảng cách đó.
    """
    dung = logits.gather(1, y.view(-1, 1)).squeeze(1)
    sai = logits.gather(1, (1 - y).view(-1, 1)).squeeze(1)
    return torch.relu(margin - (dung - sai)).mean()
