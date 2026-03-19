"""中東地域 航空・船舶活動モニター"""
import json
import os
import time
import datetime

from config import REGIONS
from fetch import fetch_aircraft, parse_aircraft, fetch_ships
from analyze import analyze
from report import generate

# AISstream.io APIキー（GitHub Secrets / 環境変数で設定）
AISSTREAM_API_KEY = os.environ.get('AISSTREAM_API_KEY', '')

# 船舶データ収集時間（秒）。長いほど多くの船を捕捉できる
SHIP_COLLECT_SECONDS = 30


def main():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'🌍 中東地域モニタリング開始  {timestamp}\n')

    results = {}

    for region_id, region in REGIONS.items():
        print(f'📍 {region["name"]}')

        # 航空機
        raw = fetch_aircraft(region['bounds'])
        aircraft = parse_aircraft(raw)
        print(f'   ✈️  航空機: {len(aircraft)} 機')

        # 船舶
        print(f'   🚢 船舶データ収集中（{SHIP_COLLECT_SECONDS}秒）...')
        ships = fetch_ships(region['bounds'], api_key=AISSTREAM_API_KEY, duration=SHIP_COLLECT_SECONDS)
        print(f'   🚢 船舶: {len(ships)} 隻')

        result = analyze(aircraft, ships)
        results[region_id] = result

        score = result['anomaly_score']
        indicator = '🔴' if score > 60 else '🟡' if score > 30 else '🟢'
        print(f'   異常スコア: {score}  {indicator}')

        if result['emergency']:
            for e in result['emergency']:
                print(f'   🚨 緊急スコーク {e["squawk"]} ({e["squawk_label"]}): {e["callsign"] or e["icao24"]}')

        print()
        time.sleep(1)

    # HTML レポート（Netlify 用に public/index.html へ出力）
    html = generate(results, timestamp)
    os.makedirs('public', exist_ok=True)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('✅ レポート生成完了: public/index.html')

    # 履歴 JSON
    history = {
        'timestamp': timestamp,
        'regions': {
            k: {
                'count':           v['count'],
                'anomaly_score':   v['anomaly_score'],
                'aircraft_score':  v.get('aircraft_score', 0),
                'ship_score':      v.get('ship_score', 0),
                'low_altitude':    v['low_altitude'],
                'emergency_count': len(v['emergency']),
                'countries':       v['countries'],
                'ships': {
                    'count':    v['ships']['count'],
                    'tankers':  v['ships']['tankers'],
                    'military': v['ships']['military'],
                    'anchored': v['ships']['anchored'],
                    'flags':    v['ships']['flags'],
                },
            }
            for k, v in results.items()
        },
    }
    ts_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = f'history_{ts_str}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f'📊 履歴保存: {json_path}')


if __name__ == '__main__':
    main()
