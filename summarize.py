"""Claude API を使って GDELT イベントと記事を日本語でサマリー生成"""
import os
import requests
import anthropic

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')


def _fetch_article_content(urls, max_articles=8):
    """記事URLからタイトルと本文冒頭を取得"""
    articles = []
    for url in urls[:max_articles]:
        try:
            r = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            text = r.text
            # タイトル抽出
            s = text.find('<title>')
            e = text.find('</title>', s)
            title = text[s+7:e].strip()[:120] if s != -1 and e != -1 else ''
            # <p>タグから本文冒頭を抽出（最大500文字）
            body = ''
            pos = 0
            chunks = []
            while len(body) < 500:
                s = text.find('<p', pos)
                if s == -1:
                    break
                e = text.find('</p>', s)
                if e == -1:
                    break
                chunk = text[s:e]
                # タグ除去
                import re
                chunk = re.sub(r'<[^>]+>', '', chunk).strip()
                if len(chunk) > 30:
                    chunks.append(chunk)
                    body += chunk + ' '
                pos = e + 4
            if title or body:
                articles.append(f'【{title}】\n{body[:500]}')
        except Exception:
            continue
    return articles


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

    # 記事タイトルと本文冒頭を取得
    articles = _fetch_article_content(urls)

    # イベントリストをテキスト化
    event_lines = []
    for e in top_events[:20]:
        event_lines.append(
            f"- {e.get('location','?')} | {e.get('actor1','?')} vs {e.get('actor2','?')} "
            f"| code:{e.get('event_code','?')} goldstein:{e.get('goldstein',0)} "
            f"articles:{e.get('num_articles',0)} tone:{e.get('avg_tone',0):.1f}"
        )

    prompt = f"""以下は世界の紛争・緊張イベントデータ（GDELT）と関連ニュース記事の内容です。
日本語で詳細なサマリーを作成してください。

【イベントデータ（上位20件）】
{chr(10).join(event_lines)}

【関連ニュース記事】
{chr(10).join(articles) if articles else '取得できませんでした'}

【サマリー作成の指示】
- 地域ごとにまとめる（🕌 中東、🇺🇦 ウクライナ・東欧、🌏 東アジア、🌍 その他）
- 各地域で起きている主要な出来事を具体的に説明する
- 関係するアクター（国・組織・人物）や背景も含める
- 重要度が高い情報は詳しく、低いものは簡潔に
- 見出しは絵文字を使ってわかりやすく
- 日本語のみで出力"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1500,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f'   ⚠ Claude API サマリー生成失敗: {e}')
        return ''
