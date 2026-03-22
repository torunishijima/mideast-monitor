"""Supabase への火災・船舶履歴データ保存モジュール"""
import os
import datetime
import requests

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')


def _headers():
    return {
        'apikey':        SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type':  'application/json',
        'Prefer':        'return=minimal',
    }


def _post(table, rows):
    if not rows:
        return
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        resp = requests.post(
            f'{SUPABASE_URL}/rest/v1/{table}',
            headers=_headers(),
            json=rows[i:i + batch_size],
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            print(f'   ⚠ Supabase {table} 保存エラー: {resp.status_code} {resp.text[:120]}')


def save_fires(fires_by_region, captured_at):
    """全地域の火災データを保存（重複除去）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    seen, rows = set(), []
    for fires in fires_by_region.values():
        for f in fires:
            key = (f['lat'], f['lon'], f.get('acq_date'), f.get('acq_time'))
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'captured_at': captured_at,
                'lat':         f['lat'],
                'lon':         f['lon'],
                'frp':         f['frp'],
                'confidence':  f.get('confidence', ''),
                'acq_date':    f.get('acq_date', ''),
                'acq_time':    f.get('acq_time', ''),
                'daynight':    f.get('daynight', ''),
            })

    _post('fires', rows)
    print(f'   → Supabase: 火災 {len(rows)} 件保存')


def save_ships(ships_by_region, captured_at):
    """全地域の船舶データを保存（MMSI重複除去）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    seen, rows = set(), []
    for ships in ships_by_region.values():
        for s in ships:
            mmsi = s.get('mmsi')
            if mmsi in seen:
                continue
            seen.add(mmsi)
            rows.append({
                'captured_at': captured_at,
                'mmsi':        mmsi,
                'lat':         s['lat'],
                'lon':         s['lon'],
                'name':        s.get('name', ''),
                'flag':        s.get('flag', ''),
                'ship_type':   s.get('ship_type', 0),
                'type_label':  s.get('type_label', ''),
                'sog':         s.get('sog'),
                'nav_status':  s.get('nav_status', ''),
                'destination': s.get('destination', ''),
            })

    _post('ships', rows)
    print(f'   → Supabase: 船舶 {len(rows)} 隻保存')


def save_region_stats(results, captured_at):
    """地域ごとの件数データを永続保存"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    rows = []
    for region_id, data in results.items():
        ships = data.get('ships', {})
        fires = data.get('fires', {})
        rows.append({
            'captured_at':        captured_at,
            'region_id':          region_id,
            'ship_count':         ships.get('count', 0),
            'tanker_count':       ships.get('tankers', 0),
            'military_count':     ships.get('military', 0),
            'anchored_count':     ships.get('anchored', 0),
            'fire_count':         fires.get('count', 0),
            'high_conf_fire_count': fires.get('high_conf', 0),
            'intense_fire_count': fires.get('intense', 0),
            'total_frp':          fires.get('total_frp', 0.0),
            'event_count':        data.get('events', {}).get('count', 0),
        })

    _post('region_stats', rows)
    print(f'   → Supabase: 地域統計 {len(rows)} 地域保存')


def save_events(events_by_region, captured_at):
    """全地域の紛争イベントデータを保存（重複除去）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    seen, rows = set(), []
    for events in events_by_region.values():
        for e in events:
            key = (e['lat'], e['lon'], e.get('event_code'))
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'captured_at':  captured_at,
                'lat':          e['lat'],
                'lon':          e['lon'],
                'event_code':   e.get('event_code', ''),
                'event_root':   e.get('event_root', ''),
                'goldstein':    e.get('goldstein', 0.0),
                'num_articles': e.get('num_articles', 0),
                'avg_tone':     e.get('avg_tone', 0.0),
                'actor1':       e.get('actor1', ''),
                'actor2':       e.get('actor2', ''),
                'location':     e.get('location', ''),
            })

    _post('events', rows)
    print(f'   → Supabase: 紛争イベント {len(rows)} 件保存')


def delete_old_data(hours=48):
    """古いデータを削除（デフォルト48時間以前）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    for table in ('fires', 'ships', 'events'):
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/{table}?captured_at=lt.{cutoff}',
            headers=_headers(),
            timeout=15,
        )
    print(f'   → Supabase: {hours}時間以前のデータ削除完了')
