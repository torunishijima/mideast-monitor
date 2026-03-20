"""世界の緊張地帯 航空・船舶・火災活動モニター"""
import json
import os
import datetime

from config import REGIONS
from fetch import fetch_all_aircraft, fetch_all_ships, fetch_all_fires
from analyze import analyze
from report import generate
from history_store import load as load_history, append as append_history, save as save_history, calc_trend_scores
from supabase_store import save_fires, save_ships, delete_old_data

AISSTREAM_API_KEY  = os.environ.get('AISSTREAM_API_KEY', '')
OPENSKY_USERNAME   = os.environ.get('OPENSKY_USERNAME', '')
OPENSKY_PASSWORD   = os.environ.get('OPENSKY_PASSWORD', '')
NASA_FIRMS_MAP_KEY = os.environ.get('NASA_FIRMS_MAP_KEY', '')
SHIP_COLLECT_SECONDS = 120


def main():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'🌍 世界モニタリング開始  {timestamp}\n')

    # データ取得
    aircraft_by_region = fetch_all_aircraft(
        username=OPENSKY_USERNAME,
        password=OPENSKY_PASSWORD,
    )
    global_aircraft = aircraft_by_region.pop('_global', [])
    fires_by_region = fetch_all_fires(map_key=NASA_FIRMS_MAP_KEY)
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
        fires    = fires_by_region.get(region_id, [])
        result   = analyze(aircraft, ships, fires)
        results[region_id] = result

    # Supabase に火災・船舶データを保存
    iso_ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_fires(fires_by_region, iso_ts)
    save_ships(ships_by_region, iso_ts)
    delete_old_data(hours=48)

    # 履歴を更新してトレンドスコアを計算
    history = load_history()
    trend   = calc_trend_scores(history, results)
    history = append_history(history, timestamp, results)
    save_history(history)

    # 結果表示
    for region_id, region in REGIONS.items():
        data  = results[region_id]
        t     = trend[region_id]
        score = data['anomaly_score']
        surge = '🚨 急上昇!' if t['is_surge'] else ''
        indicator = '🔴' if score > 60 else '🟡' if score > 30 else '🟢'
        aircraft = aircraft_by_region.get(region_id, [])
        ships    = ships_by_region.get(region_id, [])
        fires    = fires_by_region.get(region_id, [])
        print(f'{indicator} {region["name"]}: 航空機 {len(aircraft)}機 / 船舶 {len(ships)}隻 / 火災 {len(fires)}件 / スコア {score} {surge}')
        if t['change_pct'] != 0:
            print(f'   ベースライン {t["baseline"]} → 現在 {t["current"]} ({t["change_pct"]:+.1f}%)')

        if data['emergency']:
            for e in data['emergency']:
                print(f'   🚨 緊急スコーク {e["squawk"]} ({e["squawk_label"]}): {e["callsign"] or e["icao24"]}')

    # HTML レポート生成
    html = generate(results, trend, history, timestamp, global_aircraft=global_aircraft)
    os.makedirs('public', exist_ok=True)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n✅ レポート生成完了: public/index.html')


if __name__ == '__main__':
    main()
