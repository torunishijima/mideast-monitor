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


def delete_old_data(hours=48):
    """古いデータを削除（デフォルト48時間以前）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    for table in ('fires', 'ships'):
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/{table}?captured_at=lt.{cutoff}',
            headers=_headers(),
            timeout=15,
        )
    print(f'   → Supabase: {hours}時間以前のデータ削除完了')
