# coding=utf-8
"""
Dijest modülü.

Biriken günün haberlerini temaya göre gruplar, her habere AI ile 1-5
önem puanı verir ve Telegram için bir "dijest" mesajı üretir.

- scorer.py   : AI ile 1-5 önem puanlaması
- formatter.py: dijest mesaj düzeni (üstte tema-tema tam liste + puan,
                altta AI sıralaması)
"""

from trendradar.digest.scorer import score_news, DEFAULT_SCORE
from trendradar.digest.formatter import render_digest_telegram, DigestItem, DigestTheme

__all__ = [
    "score_news",
    "DEFAULT_SCORE",
    "render_digest_telegram",
    "DigestItem",
    "DigestTheme",
]
