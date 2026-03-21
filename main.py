"""世界の緊張地帯 航空・船舶・火災活動モニター"""
import os
import datetime

from config import REGIONS
from fetch import fetch_all_ships, fetch_all_fires, fetch_all_events
from analyze import analyze
from report import generate
from history_store import load as load_history, append as append_history, save as save_history, calc_trend_scores
from supabase_store import save_fires, save_ships, save_events, save_region_stats, delete_old_data
from summarize import generate_summary


AISSTREAM_API_KEY  = os.environ.get('AISSTREAM_API_KEY', '')
NASA_FIRMS_MAP_KEY = os.environ.get('NASA_FIRMS_MAP_KEY', '')
SHIP_COLLECT_SECONDS = 300


def _fire_fingerprint(fires_by_region):
    """衛星データが更新されたかを判定するフィンガープリント"""
    times = set()
    for fires in fires_by_region.values():
        for f in fires:
            if f.get('acq_date') and f.get('acq_time'):
                times.add(f['acq_date'] + f['acq_time'])
    return '|'.join(sorted(times))


def main():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'🌍 世界モニタリング開始  {timestamp}\n')

    # データ取得
    fires_by_region  = fetch_all_fires(map_key=NASA_FIRMS_MAP_KEY)
    ships_by_region  = fetch_all_ships(
        api_key=AISSTREAM_API_KEY,
        duration=SHIP_COLLECT_SECONDS,
    )
    events_by_region = fetch_all_events()

    # 地域ごとに分析
    print()
    results = {}
    for region_id, region in REGIONS.items():
        ships  = ships_by_region.get(region_id, [])
        fires  = fires_by_region.get(region_id, [])
        events = events_by_region.get(region_id, [])
        results[region_id] = analyze(ships, fires, events)

    # Supabase に火災・船舶データを保存
    iso_ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_fires(fires_by_region, iso_ts)
    save_ships(ships_by_region, iso_ts)
    save_events(events_by_region, iso_ts)
    save_region_stats(results, iso_ts)
    delete_old_data(hours=48)

    # 履歴を更新してトレンドスコアを計算
    history = load_history()

    # 火災データ未更新の場合は前回値を引き継ぐ
    current_fp = _fire_fingerprint(fires_by_region)
    if current_fp == history.get('last_fire_fingerprint', '') and history['entries']:
        last = history['entries'][-1]
        for rid in results:
            results[rid]['fires']['count'] = last['regions'].get(rid, {}).get('fire_count', 0)
        print('   → 火災データ未更新のため前回値を引き継ぎ')
    else:
        history['last_fire_fingerprint'] = current_fp

    trend   = calc_trend_scores(history, results)
    history = append_history(history, timestamp, results)
    save_history(history)

    # 結果表示
    for region_id, region in REGIONS.items():
        t     = trend[region_id]
        surge = '🚨' if t['is_surge'] else ''
        ts, tf, te = t['ships'], t['fires'], t['events']
        print(f'{surge or "🌍"} {region["name"]}')
        print(f'   船舶 {ts["current"]}隻  7日比{ts["week_pct"]:+.0f}%  24h比{ts["day_pct"]:+.0f}%')
        print(f'   火災 {tf["current"]}件  7日比{tf["week_pct"]:+.0f}%  24h比{tf["day_pct"]:+.0f}%')
        print(f'   紛争 {te["current"]}件  7日比{te["week_pct"]:+.0f}%  24h比{te["day_pct"]:+.0f}%')

    # Claude API でサマリー生成
    print('\n📝 情勢サマリー生成中...')
    summary = generate_summary(events_by_region.get('_global', []))
    if summary:
        print(summary)

    # HTML レポート生成
    html = generate(results, trend, history, timestamp,
                    all_fires=fires_by_region.get('_global', []),
                    all_events=events_by_region.get('_global', []),
                    summary=summary)
    os.makedirs('public', exist_ok=True)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n✅ レポート生成完了: public/index.html')


if __name__ == '__main__':
    main()
