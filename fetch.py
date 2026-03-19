"""データ取得モジュール
- 航空機: OpenSky Network（無料・認証不要）
- 船舶: AISstream.io（無料・APIキー必要）
"""
import os
import json
import asyncio
import requests
import websockets


def fetch_aircraft(bounds):
    """OpenSky Network から航空機データを取得"""
    url = 'https://opensky-network.org/api/states/all'
    params = {
        'lamin': bounds['lamin'],
        'lomin': bounds['lomin'],
        'lamax': bounds['lamax'],
        'lomax': bounds['lomax'],
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('states', []) or []
        elif resp.status_code == 429:
            print('  ⚠ OpenSky API レート制限。少し待ってください。')
            return []
        else:
            print(f'  ⚠ OpenSky API エラー: {resp.status_code}')
            return []
    except Exception as e:
        print(f'  ⚠ 航空機データ取得失敗: {e}')
        return []


def parse_aircraft(states):
    """OpenSky の生データを辞書リストに変換"""
    aircraft = []
    for s in states:
        if s is None or s[5] is None or s[6] is None:
            continue
        aircraft.append({
            'icao24':    s[0],
            'callsign':  (s[1] or '').strip(),
            'country':   s[2] or 'Unknown',
            'lon':        s[5],
            'lat':        s[6],
            'altitude':   s[7],
            'on_ground':  s[8],
            'velocity':   s[9],
            'heading':    s[10],
            'squawk':     s[14],
        })
    return aircraft


# 船舶の航行ステータス
NAV_STATUS = {
    0: '航行中',
    1: '錨泊中',
    2: '操縦不能',
    3: '操縦制限',
    5: '係留中',
    6: '座礁',
}

# 注目すべき船種コード
NOTABLE_SHIP_TYPES = {
    # タンカー
    80: 'タンカー', 81: 'タンカー', 82: 'タンカー', 83: 'タンカー',
    84: 'タンカー', 85: 'タンカー', 86: 'タンカー', 87: 'タンカー',
    # 軍用
    35: '軍用',
    # 高速船
    40: '高速船', 49: '高速船',
}


async def _collect_ships(bounds, api_key, duration=30):
    """WebSocket で AIS データを duration 秒間収集"""
    ships = {}  # MMSI をキーにして重複を除去

    subscribe_msg = json.dumps({
        'APIKey': api_key,
        'BoundingBoxes': [[
            [bounds['lamin'], bounds['lomin']],
            [bounds['lamax'], bounds['lomax']],
        ]],
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
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    mmsi = msg.get('MetaData', {}).get('MMSI')
                    if not mmsi:
                        continue

                    mtype = msg.get('MessageType')

                    if mtype == 'PositionReport':
                        meta = msg.get('MetaData', {})
                        pos  = msg.get('Message', {}).get('PositionReport', {})
                        lat = pos.get('Latitude') or meta.get('latitude')
                        lon = pos.get('Longitude') or meta.get('longitude')
                        if lat is None or lon is None:
                            continue
                        entry = ships.setdefault(mmsi, {'mmsi': mmsi})
                        entry.update({
                            'lat':      lat,
                            'lon':      lon,
                            'sog':      pos.get('Sog'),      # 速度 (knots)
                            'cog':      pos.get('Cog'),      # 針路
                            'nav_status': NAV_STATUS.get(pos.get('NavigationalStatus', -1), '不明'),
                            'name':     (meta.get('ShipName') or '').strip(),
                        })

                    elif mtype == 'ShipStaticData':
                        static = msg.get('Message', {}).get('ShipStaticData', {})
                        entry = ships.setdefault(mmsi, {'mmsi': mmsi})
                        ship_type = static.get('Type', 0)
                        entry.update({
                            'name':      (static.get('Name') or '').strip(),
                            'flag':      static.get('Flag', ''),
                            'ship_type': ship_type,
                            'type_label': NOTABLE_SHIP_TYPES.get(ship_type, 'その他'),
                            'destination': (static.get('Destination') or '').strip(),
                        })

                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        print(f'  ⚠ AISstream 接続エラー: {e}')
        return []

    # lat/lon があるものだけ返す
    return [s for s in ships.values() if 'lat' in s and 'lon' in s]


def fetch_ships(bounds, api_key=None, duration=30):
    """船舶データを取得（同期ラッパー）"""
    api_key = api_key or os.environ.get('AISSTREAM_API_KEY')
    if not api_key:
        return []

    try:
        return asyncio.run(_collect_ships(bounds, api_key, duration))
    except Exception as e:
        print(f'  ⚠ 船舶データ取得失敗: {e}')
        return []
