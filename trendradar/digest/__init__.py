# coding=utf-8
"""
Dijest modülü.

Biriken günün haberlerini temaya göre gruplar, her habere AI ile 1-5
önem puanı verir ve Telegram için bir "dijest" mesajı üretir.

- scorer.py   : AI ile 1-5 önem puanlaması
- formatter.py: dijest mesaj düzeni (üstte tema-tema tam liste + puan,
                altta AI sıralaması)
"""

from trendradar.digest.scorer import score_news, apply_scores, DEFAULT_SCORE
from trendradar.digest.builder import build_digest_themes, categorize
from trendradar.digest.formatter import render_digest_telegram, DigestItem, DigestTheme
from trendradar.digest.sender import send_digest_telegram

__all__ = [
    "score_news",
    "apply_scores",
    "DEFAULT_SCORE",
    "build_digest_themes",
    "categorize",
    "render_digest_telegram",
    "send_digest_telegram",
    "DigestItem",
    "DigestTheme",
]
