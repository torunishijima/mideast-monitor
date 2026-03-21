"""Claude API を使って GDELT イベントと記事を日本語でサマリー生成"""
import os
import requests
import anthropic

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')


def _fetch_article_titles(urls, max_articles=6):
    """記事URLからタイトルを取得（タイムアウト付き）"""
    titles = []
    for url in urls[:max_articles]:
        try:
            r = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            # <title>タグを簡易抽出
            text = r.text
            s = text.find('<title>')
            e = text.find('</title>', s)
            if s != -1 and e != -1:
                title = text[s+7:e].strip()[:120]
                titles.append(f'- {title} ({url})')
        except Exception:
            continue
    return titles


def generate_summary(events_global):
    """
    GDELTイベントリストを受け取り、Claude APIで日本語サマリーを生成して返す
    """
    if not ANTHROPIC_API_KEY or not events_global:
        return ''

    # 上位イベント（記事数多い順）を抽出
    sorted_events = sorted(events_global, key=lambda e: e.get('num_articles', 0), reverse=True)
    top_events = sorted_events[:30]

    # 記事URLを収集（重複除去）
    seen_urls, urls = set(), []
    for e in top_events:
        url = e.get('source_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            urls.append(url)

    # 記事タイトルを取得
    titles = _fetch_article_titles(urls)

    # イベントリストをテキスト化
    event_lines = []
    for e in top_events[:20]:
        event_lines.append(
            f"- {e.get('location','?')} | {e.get('actor1','?')} vs {e.get('actor2','?')} "
            f"| code:{e.get('event_code','?')} goldstein:{e.get('goldstein',0)} "
            f"articles:{e.get('num_articles',0)} tone:{e.get('avg_tone',0):.1f}"
        )

    prompt = f"""以下は世界の紛争・緊張イベントデータ（GDELT）と関連ニュース記事タイトルです。
日本語で簡潔にサマリーを作成してください。

【イベントデータ（上位20件）】
{chr(10).join(event_lines)}

【関連ニュース記事タイトル】
{chr(10).join(titles) if titles else '取得できませんでした'}

【サマリー作成の指示】
- 地域ごとにまとめる（中東、ウクライナ、東アジア、その他）
- 最も重要な動きを箇条書きで簡潔に
- 全体で300字以内
- 日本語のみで出力
- 見出しは絵文字を使ってわかりやすく"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=600,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f'   ⚠ Claude API サマリー生成失敗: {e}')
        return ''
