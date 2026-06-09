# coding=utf-8
"""
Dijest önem puanlaması.

Haberleri AI'ya verip her birine 1-5 önem puanı aldırır. AI yalnızca
ÖNERİ verir; hiçbir haberi elemez. Puan alınamayan haber DEFAULT_SCORE
ile gösterilir (gizlenmez).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

try:
    from json_repair import repair_json
except Exception:  # pragma: no cover - json_repair her zaman kurulu olmalı
    repair_json = None

DEFAULT_SCORE = 3          # AI puan veremezse kullanılacak nötr puan
MIN_SCORE = 1
MAX_SCORE = 5
DEFAULT_BATCH_SIZE = 120   # tek AI çağrısında değerlendirilecek max haber

_PROMPT_FILE = "digest_score_prompt.txt"


class ChatClient(Protocol):
    """AIClient ile uyumlu minimal arayüz (test için sahte client de geçilebilir)."""

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str: ...


def _config_root() -> Path:
    return Path(__file__).parent.parent.parent / "config"


def load_score_prompt(prompt_path: Optional[Path] = None) -> tuple:
    """digest_score_prompt.txt dosyasını [system]/[user] olarak ayrıştırır."""
    path = prompt_path or (_config_root() / _PROMPT_FILE)
    content = path.read_text(encoding="utf-8")
    system = ""
    user = ""
    if "[system]" in content and "[user]" in content:
        parts = content.split("[user]")
        system_part = parts[0]
        user = parts[1].strip() if len(parts) > 1 else ""
        if "[system]" in system_part:
            system = system_part.split("[system]")[1].strip()
    else:
        user = content
    return system, user


def _build_news_list(items: List[Dict[str, Any]]) -> str:
    """Puanlanacak haberleri numaralı metin listesine çevirir."""
    lines = []
    for it in items:
        src = it.get("source", "")
        title = (it.get("title", "") or "").replace("\n", " ").strip()
        prefix = f"[{src}] " if src else ""
        lines.append(f"{it['id']}. {prefix}{title}")
    return "\n".join(lines)


def _parse_scores(raw: str) -> Dict[int, int]:
    """AI yanıtından {id: score} çıkarır. Bozuk JSON'u onarmayı dener."""
    if not raw:
        return {}
    text = raw.strip()
    # ```json ... ``` çitlerini temizle
    if "```" in text:
        segments = text.split("```")
        # en uzun parçayı al (genelde gövde)
        text = max(segments, key=len)
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    text = text.strip()

    data = None
    try:
        data = json.loads(text)
    except Exception:
        if repair_json is not None:
            try:
                data = json.loads(repair_json(text))
            except Exception:
                data = None
    if not isinstance(data, list):
        return {}

    out: Dict[int, int] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        try:
            _id = int(entry.get("id"))
            score = int(round(float(entry.get("score"))))
        except (TypeError, ValueError):
            continue
        out[_id] = max(MIN_SCORE, min(MAX_SCORE, score))
    return out


def _chunks(seq: List[Any], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def score_news(
    items: List[Dict[str, Any]],
    client: ChatClient,
    batch_size: int = DEFAULT_BATCH_SIZE,
    prompt_path: Optional[Path] = None,
    debug: bool = False,
) -> Dict[int, int]:
    """
    Haberlere 1-5 önem puanı verir.

    Args:
        items: [{"id": int, "title": str, "source": str}, ...]
        client: .chat(messages)->str arayüzü olan AI istemcisi
        batch_size: tek çağrıda işlenecek haber sayısı
    Returns:
        {id: 1-5}  — puanlanamayanlar sözlükte yer almaz (çağıran DEFAULT_SCORE uygular)
    """
    if not items:
        return {}

    system, user_tmpl = load_score_prompt(prompt_path)
    scores: Dict[int, int] = {}

    for batch in _chunks(items, max(1, batch_size)):
        news_list = _build_news_list(batch)
        user = user_tmpl.replace("{news_count}", str(len(batch))).replace(
            "{news_list}", news_list
        )
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        try:
            raw = client.chat(messages)
        except Exception as e:
            if debug:
                print(f"[Dijest] Puanlama çağrısı başarısız: {e}")
            continue

        batch_scores = _parse_scores(raw)
        if debug:
            print(f"[Dijest] {len(batch)} haber → {len(batch_scores)} puan alındı")
        scores.update(batch_scores)

    return scores


def apply_scores(
    items: List[Dict[str, Any]], scores: Dict[int, int], default: int = DEFAULT_SCORE
) -> None:
    """items listesindeki her öğeye 'score' alanı ekler (yerinde)."""
    for it in items:
        it["score"] = scores.get(it["id"], default)
