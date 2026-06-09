# coding=utf-8
"""Dijest çekirdeği için lokal kendi-kendine test (canlı AI gerektirmez)."""

from trendradar.digest import scorer
from trendradar.digest.formatter import render_digest_telegram


class FakeClient:
    """Verilen id'lere sahte ama deterministik puan döndüren sahte AI client."""

    def __init__(self, fence=True):
        self.fence = fence

    def chat(self, messages, **kwargs):
        # user mesajındaki "N. ..." satırlarından id'leri çıkar
        user = messages[-1]["content"]
        ids = []
        for line in user.splitlines():
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:4]:
                try:
                    ids.append(int(line.split(".")[0]))
                except ValueError:
                    pass
        body = ", ".join(f'{{"id": {i}, "score": {1 + (i % 5)}}}' for i in ids)
        arr = f"[{body}]"
        return f"```json\n{arr}\n```" if self.fence else arr


def test_parse_variants():
    assert scorer._parse_scores('[{"id":1,"score":5}]') == {1: 5}
    assert scorer._parse_scores('```json\n[{"id":2,"score":3}]\n```') == {2: 3}
    # bozuk JSON (eksik kapanış) -> repair
    got = scorer._parse_scores('[{"id":3,"score":4},{"id":4,"score":9}')
    assert got.get(3) == 4 and got.get(4) == 5, got  # 9 -> 5'e clamp
    print("OK  _parse_scores (fence/repair/clamp)")


def test_score_news():
    items = [{"id": i, "title": f"Haber {i}", "source": "Test"} for i in range(1, 7)]
    sc = scorer.score_news(items, FakeClient(fence=True), batch_size=4)
    assert len(sc) == 6, sc
    assert all(1 <= v <= 5 for v in sc.values()), sc
    scorer.apply_scores(items, sc)
    assert all("score" in it for it in items)
    print(f"OK  score_news (6 haber, 2 batch) -> {sc}")


def test_formatter():
    themes = [
        {"name": "BIST / Borsa İstanbul", "items": [
            {"id": 1, "title": "THYAO rekor yolcu sayısı açıkladı", "source": "Bloomberg HT",
             "url": "https://x/1", "time": "14:30", "score": 4},
            {"id": 2, "title": "GARAN ikinci çeyrek bilançosu beklentiyi aştı", "source": "AA Ekonomi",
             "url": "https://x/2", "time": "11:05", "score": 5},
        ]},
        {"name": "Döviz / TL", "items": [
            {"id": 3, "title": "TCMB rezervlerde artış bildirdi", "source": "Reuters",
             "url": "https://x/3", "time": "09:50", "score": 5},
        ]},
        {"name": "Kripto", "items": [
            {"id": 4, "title": "Bitcoin 70 bin doları test etti", "source": "CoinDesk",
             "url": "", "time": "16:20", "score": 3},
        ]},
    ]
    out = render_digest_telegram(themes, "9 Haziran, Akşam", now_str="2026-06-09 20:00", top_n=5)
    assert "GÜNÜN DİJESTİ" in out
    assert "TÜM HABERLER" in out and "(4)" in out
    assert "AI Sıralaması" in out
    assert "5️⃣" in out and "4️⃣" in out and "3️⃣" in out
    # link ve kaçış
    assert '<a href="https://x/2">' in out
    # boş haber penceresi
    empty = render_digest_telegram([], "Test", top_n=5)
    assert "eşleşen haber yok" in empty
    print("OK  render_digest_telegram (düzen + link + boş durum)")
    print("\n----- ÖRNEK ÇIKTI -----")
    print(out)


if __name__ == "__main__":
    test_parse_variants()
    test_score_news()
    test_formatter()
    print("\n✅ Tüm dijest çekirdek testleri geçti.")
