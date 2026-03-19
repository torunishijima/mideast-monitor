"""データ取得モジュール
- 航空機: OpenSky Network（全世界を1回取得）
- 船舶: AISstream.io（全地域を1接続で同時取得）
"""
import os
import json
import asyncio
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
            return _assign_to_regions(states)
        elif resp.status_code == 429:
            print('   ⚠ OpenSky API レート制限')
            return {rid: [] for rid in REGIONS}
        else:
            print(f'   ⚠ OpenSky API エラー: {resp.status_code}')
            return {rid: [] for rid in REGIONS}
    except Exception as e:
        print(f'   ⚠ 航空機データ取得失敗: {e}')
        return {rid: [] for rid in REGIONS}


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
