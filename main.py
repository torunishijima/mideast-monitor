"""世界の緊張地帯 航空・船舶活動モニター"""
import json
import os
import time
import datetime

from config import REGIONS
from fetch import fetch_all_aircraft, fetch_all_ships
from analyze import analyze
from report import generate

AISSTREAM_API_KEY = os.environ.get('AISSTREAM_API_KEY', '')
OPENSKY_USERNAME  = os.environ.get('OPENSKY_USERNAME', '')
OPENSKY_PASSWORD  = os.environ.get('OPENSKY_PASSWORD', '')
SHIP_COLLECT_SECONDS = 120


def main():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'🌍 世界モニタリング開始  {timestamp}\n')

    # 航空機・船舶を並列取得（それぞれ1回ずつ）
    aircraft_by_region = fetch_all_aircraft(
        username=OPENSKY_USERNAME,
        password=OPENSKY_PASSWORD,
    )
    ships_by_region = fetch_all_ships(
        api_key=AISSTREAM_API_KEY,
        duration=SHIP_COLLECT_SECONDS,
    )

    # 地域ごとに分析
    print()
    results = {}
    for region_id, region in REGIONS.items():
        aircraft = aircraft_by_region.get(region_id, [])
        ships    = ships_by_region.get(region_id, [])
        result   = analyze(aircraft, ships)
        results[region_id] = result

        score     = result['anomaly_score']
        indicator = '🔴' if score > 60 else '🟡' if score > 30 else '🟢'
        print(f'{indicator} {region["name"]}: 航空機 {len(aircraft)}機 / 船舶 {len(ships)}隻 / スコア {score}')

        if result['emergency']:
            for e in result['emergency']:
                print(f'   🚨 緊急スコーク {e["squawk"]} ({e["squawk_label"]}): {e["callsign"] or e["icao24"]}')

    # HTML レポート
    html = generate(results, timestamp)
    os.makedirs('public', exist_ok=True)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n✅ レポート生成完了: public/index.html')

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
    with open(f'history_{ts_str}.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f'📊 履歴保存: history_{ts_str}.json')


if __name__ == '__main__':
    main()
