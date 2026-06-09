# coding=utf-8
"""
Dijest mesaj formatı (Telegram HTML).

Düzen (Brom'un kuralı): üstte TÜM haberler tema-tema ve puanlı (hiçbiri
gizlenmez), en altta AI'nın puan sıralaması (yalnızca öneri).
"""

import html
from typing import Any, Dict, List

# Basit tip takma adları (dict tabanlı, esnek)
DigestItem = Dict[str, Any]      # {"id","title","source","url","time","score"}
DigestTheme = Dict[str, Any]     # {"name": str, "items": List[DigestItem]}

_KEYCAP = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}


def _score_icon(score: int) -> str:
    return _KEYCAP.get(int(score), "3️⃣")


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _render_item(it: DigestItem) -> str:
    score = it.get("score", 3)
    title = _esc((it.get("title", "") or "").strip())
    url = it.get("url") or ""
    source = it.get("source", "")
    time = it.get("time", "")

    title_html = f'<a href="{_esc(url)}">{title}</a>' if url else title
    tail = []
    if source:
        tail.append(_esc(source))
    if time:
        tail.append(_esc(time))
    suffix = f"  <i>{' · '.join(tail)}</i>" if tail else ""
    return f"{_score_icon(score)} {title_html}{suffix}"


def render_digest_telegram(
    themes: List[DigestTheme],
    window_label: str,
    now_str: str = "",
    top_n: int = 8,
) -> str:
    """
    Dijest mesajını Telegram HTML olarak üretir.

    Args:
        themes: [{"name": str, "items": [DigestItem,...]}, ...]
                Her tema içindeki items zaten puana göre sıralı gelmeli.
        window_label: pencere etiketi (örn. "9 Haziran, Akşam")
        now_str: üretim zamanı (footer)
        top_n: alttaki AI sıralamasında gösterilecek haber sayısı
    """
    total = sum(len(t.get("items", [])) for t in themes)

    lines: List[str] = []
    lines.append("<b>\U0001F4CB GÜNÜN DİJESTİ</b>")
    if window_label:
        lines.append(f"<b>{_esc(window_label)}</b>")
    lines.append("")

    if total == 0:
        lines.append("Bu pencerede eşleşen haber yok.")
        return "\n".join(lines)

    # ─── Üst bölüm: TÜM haberler, tema-tema, puanlı ───
    lines.append(f"<b>\U0001F4CA TÜM HABERLER</b> ({total})")
    lines.append("")
    for theme in themes:
        items = theme.get("items", [])
        if not items:
            continue
        lines.append(f"<b>[{_esc(theme.get('name',''))}]</b> ({len(items)})")
        for it in items:
            lines.append(_render_item(it))
        lines.append("")

    # ─── Alt bölüm: AI sıralaması (öneri) ───
    all_items = [it for t in themes for it in t.get("items", [])]
    ranked = sorted(all_items, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    if ranked:
        lines.append("─" * 12)
        lines.append("<b>⭐ AI Sıralaması</b> <i>(öneri — son söz sende)</i>")
        for it in ranked:
            title = _esc((it.get("title", "") or "").strip())
            url = it.get("url") or ""
            title_html = f'<a href="{_esc(url)}">{title}</a>' if url else title
            src = f"  <i>{_esc(it.get('source',''))}</i>" if it.get("source") else ""
            lines.append(f"{_score_icon(it.get('score',3))} {title_html}{src}")

    if now_str:
        lines.append("")
        lines.append(f"<i>{_esc(now_str)}</i>")

    return "\n".join(lines)
