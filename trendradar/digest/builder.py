# coding=utf-8
"""
Dijest tema oluşturucu.

Pipeline'dan gelen iki farklı veri kümesini (hotlist keyword grupları +
kaynağa göre gruplu RSS) tek bir TR-yatırımcı tema setine bucket'lar.
Hiçbir haber elenmez; hiçbir temaya uymayan "📰 Diğer"e düşer (gizlenmez).
"""

import re
from typing import Any, Dict, List

# Tema tanımları: (görünen ad, başlık/kaynak içinde aranan regex)
# Sıra ÖNEMLİ — ilk eşleşen tema kazanır.
_THEMES = [
    ("🇹🇷 BIST / Türk Hisseleri", re.compile(
        r"\b(BIST|XU100|XU030|borsa istanbul|THYAO|GARAN|AKBNK|ISCTR|YKBNK|"
        r"ASELS|KCHOL|SASA|EREGL|TUPRS|FROTO|TCELL|PETKM|TOGG|halka arz|"
        r"bilanço|temettü)\b", re.IGNORECASE)),
    ("💱 Döviz / TL / TCMB", re.compile(
        r"\b(TCMB|merkez bankası|dolar|euro|sterlin|kur|TL|türk lirası|faiz|"
        r"enflasyon|TÜFE|ÜFE|rezerv|para politikası)\b", re.IGNORECASE)),
    ("🛢️ Emtia / Enerji", re.compile(
        r"\b(altın|gram altın|ons|gümüş|petrol|brent|ham petrol|doğalgaz|"
        r"OPEC|emtia|bakır|gold|silver|oil|crude)\b", re.IGNORECASE)),
    ("₿ Kripto", re.compile(
        r"\b(bitcoin|btc|ethereum|eth|kripto|crypto|coin|blockchain|"
        r"altcoin|stablecoin|token)\b", re.IGNORECASE)),
    ("🇨🇳 Çin", re.compile(
        r"(çin|china|yuan|renminbi|PBoC|A-?hisse|A股|人民币|shanghai|"
        r"WallStreetCN|CLS|CaiLianShe)", re.IGNORECASE)),
    ("🌍 Küresel Piyasalar", re.compile(
        r"\b(Fed|FOMC|Powell|ECB|Lagarde|S&P|Nasdaq|Dow|Wall Street|"
        r"treasury|bond|stocks|earnings|Nvidia|Apple|Tesla|OpenAI|"
        r"recession|jobs|inflation|rate)\b", re.IGNORECASE)),
]

_OTHER = "📰 Diğer"


def categorize(title: str, source: str = "") -> str:
    """Bir haberi sabit TR-yatırımcı temalarından birine atar."""
    hay = f"{title} {source}"
    for name, pattern in _THEMES:
        if pattern.search(hay):
            return name
    return _OTHER


def _norm_time(item: Dict[str, Any]) -> str:
    """time_display / last_time ('HH-MM') -> 'HH:MM'."""
    t = item.get("time_display") or item.get("last_time") or item.get("first_time") or ""
    if isinstance(t, str) and re.fullmatch(r"\d{1,2}-\d{2}", t):
        return t.replace("-", ":")
    return t if isinstance(t, str) else ""


def _flatten_hotlist(stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for stat in stats or []:
        for it in stat.get("titles", []):
            out.append({
                "title": it.get("title", ""),
                "source": it.get("source_name", "") or it.get("source", ""),
                "url": it.get("url") or it.get("mobileUrl") or "",
                "time": _norm_time(it),
            })
    return out


def _flatten_rss(rss_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for src in rss_items or []:
        source_name = src.get("source_name", "") or src.get("name", "")
        for it in src.get("titles", []):
            out.append({
                "title": it.get("title", ""),
                "source": it.get("source_name", "") or source_name,
                "url": it.get("url") or it.get("mobileUrl") or "",
                "time": _norm_time(it),
            })
    return out


def build_digest_themes(
    hotlist_stats: List[Dict[str, Any]],
    rss_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Hotlist + RSS öğelerini sabit temalara bucket'lar.

    Returns: [{"name": tema, "items": [{"id","title","source","url","time"}, ...]}]
             Temalar _THEMES sırasına göre, en sonda 📰 Diğer. Boş tema atlanır.
    """
    flat = _flatten_hotlist(hotlist_stats) + _flatten_rss(rss_items)

    # tekilleştir (aynı başlık birden çok kaynaktan gelebilir)
    seen = set()
    unique = []
    for it in flat:
        key = (it["title"].strip().lower(), it["source"])
        if not it["title"].strip() or key in seen:
            continue
        seen.add(key)
        unique.append(it)

    # id ata + kategorize et
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for idx, it in enumerate(unique, 1):
        it["id"] = idx
        theme = categorize(it["title"], it["source"])
        buckets.setdefault(theme, []).append(it)

    # tema sırasını koru (_THEMES + Diğer en sonda)
    order = [name for name, _ in _THEMES] + [_OTHER]
    themes = []
    for name in order:
        if buckets.get(name):
            themes.append({"name": name, "items": buckets[name]})
    return themes
