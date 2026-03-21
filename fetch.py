"""データ取得モジュール
- 船舶: AISstream.io（全地域を1接続で同時取得）
- 火災: NASA FIRMS（衛星による熱源検知）
- 紛争イベント: GDELT 2.0（15分ごと更新）
"""
import csv
import io
import os
import json
import asyncio
import zipfile
import requests
import websockets

from config import REGIONS


def fetch_all_aircraft(username=None, password=None):
    """OpenSky Network から全世界の航空機を一括取得して地域ごとに振り分け"""
    url  = 'https://opensky-network.org/api/states/all'
    auth = (username, password) if username and password else None
    print('✈️  OpenSky: 全世界データ取得中...')
    try:
        resp = requests.get(url, auth=auth, timeout=30)
        if resp.status_code == 200:
            states = resp.json().get('states', []) or []
            print(f'   → 全世界 {len(states)} 機取得')
            result = _assign_to_regions(states)
            result['_global'] = [
                parse_one_aircraft(s) for s in states
                if s and s[5] is not None and s[6] is not None
            ]
            return result
        elif resp.status_code == 429:
            print('   ⚠ OpenSky API レート制限')
            return {rid: [] for rid in REGIONS} | {'_global': []}
        else:
            print(f'   ⚠ OpenSky API エラー: {resp.status_code}')
            return {rid: [] for rid in REGIONS} | {'_global': []}
    except Exception as e:
        print(f'   ⚠ 航空機データ取得失敗: {e}')
        return {rid: [] for rid in REGIONS} | {'_global': []}


def _assign_to_regions(states):
    """全航空機を各地域のバウンディングボックスで振り分け"""
    result = {rid: [] for rid in REGIONS}
    for s in states:
        if s is None or s[5] is None or s[6] is None:
            continue
        lon, lat = s[5], s[6]
        for rid, region in REGIONS.items():
            b = region['bounds']
            if b['lamin'] <= lat <= b['lamax'] and b['lomin'] <= lon <= b['lomax']:
                result[rid].append(parse_one_aircraft(s))
    return result


def parse_one_aircraft(s):
    return {
        'icao24':   s[0],
        'callsign': (s[1] or '').strip(),
        'country':  s[2] or 'Unknown',
        'lon':       s[5],
        'lat':       s[6],
        'altitude':  s[7],
        'on_ground': s[8],
        'velocity':  s[9],
        'heading':   s[10],
        'squawk':    s[14],
    }


# 船舶の航行ステータス
NAV_STATUS = {
    0: '航行中', 1: '錨泊中', 2: '操縦不能',
    3: '操縦制限', 5: '係留中', 6: '座礁',
}

NOTABLE_SHIP_TYPES = {
    **{t: 'タンカー' for t in range(80, 90)},
    35: '軍用',
    40: '高速船', 49: '高速船',
}


async def _collect_all_ships(api_key, duration=120):
    """全地域を1接続で同時購読して船舶データを収集"""
    ships = {}  # MMSI をキーにして重複除去

    # 全地域のバウンディングボックスをまとめて送る
    bounding_boxes = [
        [
            [r['bounds']['lamin'], r['bounds']['lomin']],
            [r['bounds']['lamax'], r['bounds']['lomax']],
        ]
        for r in REGIONS.values()
    ]

    subscribe_msg = json.dumps({
        'APIKey': api_key,
        'BoundingBoxes': bounding_boxes,
        'FilterMessageTypes': ['PositionReport', 'ShipStaticData'],
    })

    try:
        async with websockets.connect(
            'wss://stream.aisstream.io/v0/stream',
            open_timeout=10,
        ) as ws:
            await ws.send(subscribe_msg)
            deadline = asyncio.get_event_loop().time() + duration
            while asyncio.get_event_loop().time() < deadline:
                try:
                    raw  = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg  = json.loads(raw)
                    mmsi = msg.get('MetaData', {}).get('MMSI')
                    if not mmsi:
                        continue
                    mtype = msg.get('MessageType')
                    if mtype == 'PositionReport':
                        meta = msg.get('MetaData', {})
                        pos  = msg.get('Message', {}).get('PositionReport', {})
                        lat  = pos.get('Latitude')  or meta.get('latitude')
                        lon  = pos.get('Longitude') or meta.get('longitude')
                        if lat is None or lon is None:
                            continue
                        entry = ships.setdefault(mmsi, {'mmsi': mmsi})
                        entry.update({
                            'lat': lat, 'lon': lon,
                            'sog': pos.get('Sog'),
                            'cog': pos.get('Cog'),
                            'nav_status': NAV_STATUS.get(pos.get('NavigationalStatus', -1), '不明'),
                            'name': (meta.get('ShipName') or '').strip(),
                        })
                    elif mtype == 'ShipStaticData':
                        static    = msg.get('Message', {}).get('ShipStaticData', {})
                        ship_type = static.get('Type', 0)
                        entry     = ships.setdefault(mmsi, {'mmsi': mmsi})
                        entry.update({
                            'name':        (static.get('Name') or '').strip(),
                            'flag':        static.get('Flag', ''),
                            'ship_type':   ship_type,
                            'type_label':  NOTABLE_SHIP_TYPES.get(ship_type, 'その他'),
                            'destination': (static.get('Destination') or '').strip(),
                        })
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(f'   ⚠ AISstream 接続エラー: {e}')
        return {}

    return {mmsi: s for mmsi, s in ships.items() if 'lat' in s and 'lon' in s}


def fetch_all_ships(api_key=None, duration=120):
    """全地域の船舶データを1接続で取得して地域ごとに振り分け"""
    api_key = api_key or os.environ.get('AISSTREAM_API_KEY')
    if not api_key:
        return {rid: [] for rid in REGIONS}

    print(f'🚢  AISstream: 全地域を同時取得中（{duration}秒）...')
    try:
        all_ships = asyncio.run(_collect_all_ships(api_key, duration))
    except Exception as e:
        print(f'   ⚠ 船舶データ取得失敗: {e}')
        return {rid: [] for rid in REGIONS}

    print(f'   → 全世界 {len(all_ships)} 隻取得')
    return _assign_ships_to_regions(all_ships)


def _assign_ships_to_regions(ships_dict):
    result = {rid: [] for rid in REGIONS}
    for ship in ships_dict.values():
        lat, lon = ship['lat'], ship['lon']
        for rid, region in REGIONS.items():
            b = region['bounds']
            if b['lamin'] <= lat <= b['lamax'] and b['lomin'] <= lon <= b['lomax']:
                result[rid].append(ship)
    return result


# ── NASA FIRMS 火災・熱源データ ──────────────────────────────────────────────

def fetch_all_fires(map_key=None, day_range=1):
    """
    NASA FIRMS（VIIRS SNPP）から全地域の火災・熱源データを取得して振り分け
    - map_key: https://firms.modaps.eosdis.nasa.gov/api/map_key/ で無料取得
    - day_range: 過去何日分を取得するか（1〜10）
    - confidence: low / nominal / high
    """
    map_key = map_key or os.environ.get('NASA_FIRMS_MAP_KEY')
    if not map_key:
        return {rid: [] for rid in REGIONS}

    print('🔥  NASA FIRMS: 全地域の火災データ取得中...')
    all_fires = []
    seen = set()

    for rid, region in REGIONS.items():
        b = region['bounds']
        # area: W,S,E,N
        area = f"{b['lomin']},{b['lamin']},{b['lomax']},{b['lamax']}"
        url  = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/{area}/{day_range}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and 'latitude' in resp.text:
                reader = csv.DictReader(io.StringIO(resp.text))
                for row in reader:
                    key = (row['latitude'], row['longitude'], row['acq_date'], row['acq_time'])
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        all_fires.append({
                            'lat':        float(row['latitude']),
                            'lon':        float(row['longitude']),
                            'frp':        float(row.get('frp', 0)),      # 火災強度（MW）
                            'confidence': row.get('confidence', ''),
                            'acq_date':   row.get('acq_date', ''),
                            'acq_time':   row.get('acq_time', ''),
                            'daynight':   row.get('daynight', ''),
                        })
                    except (ValueError, KeyError):
                        continue
            elif resp.status_code == 429:
                print('   ⚠ FIRMS API レート制限')
            elif resp.status_code != 200:
                print(f'   ⚠ FIRMS API エラー: {resp.status_code}')
        except Exception as e:
            print(f'   ⚠ FIRMS 取得失敗 ({rid}): {e}')

    all_fires = [f for f in all_fires if f.get('frp', 0) >= 200]
    print(f'   → 全世界 {len(all_fires)} 件の熱源検知（200MW以上）')
    return _assign_fires_to_regions(all_fires)


def _assign_fires_to_regions(fires):
    result = {rid: [] for rid in REGIONS}
    for fire in fires:
        lat, lon = fire['lat'], fire['lon']
        for rid, region in REGIONS.items():
            b = region['bounds']
            if b['lamin'] <= lat <= b['lamax'] and b['lomin'] <= lon <= b['lomax']:
                result[rid].append(fire)
    return result


# ── GDELT 2.0 紛争イベント ────────────────────────────────────────────────────

# CAMEO EventRootCode: 18=Use of force, 19=Armed force, 20=Mass violence
CONFLICT_ROOT_CODES = {'18', '19', '20'}


def fetch_all_events():
    """GDELT 2.0 から過去1時間分（4ファイル）の紛争イベントを取得して地域ごとに振り分け"""
    import datetime, re
    print('📰  GDELT: 過去1時間分の紛争イベント取得中...')
    try:
        # 最新ファイルのURL取得
        resp = requests.get(
            'http://data.gdeltproject.org/gdeltv2/lastupdate.txt', timeout=15
        )
        export_url = None
        for line in resp.text.strip().split('\n'):
            parts = line.strip().split(' ')
            if len(parts) == 3 and 'export' in parts[2]:
                export_url = parts[2]
                break
        if not export_url:
            print('   ⚠ GDELT: ファイルURL取得失敗')
            return {rid: [] for rid in REGIONS}

        # 最新ファイルのタイムスタンプから過去1時間分（4ファイル）のURLを生成
        m = re.search(r'(\d{14})\.export', export_url)
        if not m:
            return {rid: [] for rid in REGIONS}
        latest_dt = datetime.datetime.strptime(m.group(1), '%Y%m%d%H%M%S')
        base_url  = export_url[:export_url.index(m.group(1))]
        urls = [
            f'{base_url}{(latest_dt - datetime.timedelta(minutes=15*i)).strftime("%Y%m%d%H%M%S")}.export.CSV.zip'
            for i in range(4)
        ]

        # 各ファイルを取得してパース（重複はGLOBALEVENTIDで除去）
        events = []
        seen_ids = set()
        for url in urls:
            try:
                r = requests.get(url, timeout=30)
                if r.status_code != 200:
                    continue
                with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                    with zf.open(zf.namelist()[0]) as f:
                        content = f.read().decode('utf-8', errors='replace')
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    row = line.split('\t')
                    if len(row) < 58:
                        continue
                    try:
                        if row[28] not in CONFLICT_ROOT_CODES:
                            continue
                        event_id = row[0]
                        if event_id in seen_ids:
                            continue
                        seen_ids.add(event_id)
                        lat = float(row[56]) if row[56] else None
                        lon = float(row[57]) if row[57] else None
                        if lat is None or lon is None or (lat == 0 and lon == 0):
                            continue
                        events.append({
                            'lat':          lat,
                            'lon':          lon,
                            'event_code':   row[26],
                            'event_root':   row[28],
                            'goldstein':    float(row[30]) if row[30] else 0.0,
                            'num_articles': int(row[33])   if row[33] else 0,
                            'avg_tone':     float(row[34]) if row[34] else 0.0,
                            'actor1':       row[6],
                            'actor2':       row[16],
                            'location':     row[52],
                        })
                    except (ValueError, IndexError):
                        continue
            except Exception:
                continue

        print(f'   → 全世界 {len(events)} 件の紛争イベント（CAMEO 18-20、過去1時間）')
        return _assign_events_to_regions(events)

    except Exception as e:
        print(f'   ⚠ GDELT 取得失敗: {e}')
        return {rid: [] for rid in REGIONS}


def _assign_events_to_regions(events):
    result = {rid: [] for rid in REGIONS}
    for event in events:
        lat, lon = event['lat'], event['lon']
        for rid, region in REGIONS.items():
            b = region['bounds']
            if b['lamin'] <= lat <= b['lamax'] and b['lomin'] <= lon <= b['lomax']:
                result[rid].append(event)
    return result
