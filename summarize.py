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

    prompt = f"""あなたは地政学・国際安全保障の専門アナリストです。
以下のGDELTデータとニュース記事をもとに、約1000文字の分析記事を日本語で書いてください。

【GDELTイベントデータ（記事数上位20件）】
{chr(10).join(event_lines)}

【一次ソース記事】
{chr(10).join(articles) if articles else '取得できませんでした'}

【執筆ルール】
- 記事タイトルをつける（本質を突いた1行）
- リード：何が起きているか2〜3文で端的に
- 本文：①事実整理 ②なぜ今か ③構造的読解 ④展開予測 ⑤日本への含意
- 約1000文字・日本語のみ・客観的な論調
- 見出しは絵文字を使う"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2500,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f'   ⚠ Claude API サマリー生成失敗: {e}')
        return ''
