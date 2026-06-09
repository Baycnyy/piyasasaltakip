# coding=utf-8
"""
Dijest için basit, bağımsız Telegram gönderici.

Hazır HTML dijest metnini Telegram'ın 4096 karakter sınırına göre satır
sınırlarında böler ve sendMessage'a yollar. Normal rapor sender'ına
bağımlı değildir (ham metin gönderir).
"""

import time
from typing import List, Optional

import requests

_TG_LIMIT = 3800  # 4096'nın altında güvenli marj (HTML + emoji bayt payı)


def _split_by_lines(text: str, limit: int = _TG_LIMIT) -> List[str]:
    """Metni satır sınırlarında <= limit parçalara böler (HTML satırları bütün kalır)."""
    chunks: List[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate.encode("utf-8")) > limit and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]


def send_digest_telegram(
    bot_token: str,
    chat_id: str,
    text: str,
    proxy_url: Optional[str] = None,
    batch_interval: float = 1.0,
) -> bool:
    """Dijest metnini Telegram'a (HTML) gönderir. Tümü başarılıysa True."""
    if not bot_token or not chat_id or not text.strip():
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    parts = _split_by_lines(text)
    all_ok = True

    for i, part in enumerate(parts, 1):
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, proxies=proxies, timeout=30)
            ok = resp.status_code == 200 and resp.json().get("ok", False)
            if ok:
                print(f"[Dijest] Telegram {i}/{len(parts)} gönderildi")
            else:
                all_ok = False
                print(f"[Dijest] Telegram {i}/{len(parts)} BAŞARISIZ: {resp.text[:200]}")
        except Exception as e:
            all_ok = False
            print(f"[Dijest] Telegram gönderim hatası: {e}")
        if i < len(parts):
            time.sleep(batch_interval)

    return all_ok
