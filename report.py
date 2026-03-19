"""HTML レポート生成モジュール"""
import json
from config import REGIONS


def generate(results, timestamp):
    regions_json  = json.dumps(_regions_for_map(results), ensure_ascii=False)
    aircraft_json = json.dumps(_aircraft_for_map(results), ensure_ascii=False)
    ships_json    = json.dumps(_ships_for_map(results), ensure_ascii=False)
    cards_html    = ''.join(_card_html(rid, results[rid]) for rid in results)

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>世界の緊張地帯 活動モニター</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #1a1a2e; color: #eee; }}
header {{ padding: 14px 20px; background: #16213e; border-bottom: 1px solid #2a2a4a;
          display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
header h1 {{ font-size: 17px; }}
.updated {{ font-size: 12px; color: #888; margin-left: auto; }}
#map {{ height: 52vh; }}
.legend {{ padding: 8px 20px; background: #16213e; border-bottom: 1px solid #2a2a4a;
           display: flex; gap: 16px; font-size: 12px; color: #aaa; flex-wrap: wrap; }}
.legend span {{ display: flex; align-items: center; gap: 5px; }}
.dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 14px; padding: 14px; }}
.card {{ background: #16213e; border-radius: 10px; padding: 14px; border: 1px solid #2a2a4a; }}
.card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
.region-name {{ font-weight: 600; font-size: 14px; }}
.score {{ font-size: 12px; font-weight: bold; color: #fff; padding: 3px 10px; border-radius: 12px; }}
.section-title {{ font-size: 11px; color: #888; margin: 10px 0 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
.stats {{ display: flex; gap: 16px; margin-bottom: 4px; }}
.stat .num {{ display: block; font-size: 20px; font-weight: bold; color: #4fc3f7; }}
.stat .num.ship {{ color: #a8d8a8; }}
.stat .label {{ font-size: 11px; color: #888; }}
.alert {{ background: #4a1010; border: 1px solid #c0392b; border-radius: 6px;
          padding: 8px 10px; font-size: 12px; margin: 8px 0; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }}
.tag {{ font-size: 11px; padding: 3px 8px; border-radius: 4px; }}
.tag.air {{ background: #0f3460; color: #adf; }}
.tag.ship {{ background: #0d3d2a; color: #afa; }}
.divider {{ border: none; border-top: 1px solid #2a2a4a; margin: 10px 0; }}
footer {{ padding: 12px; font-size: 11px; color: #555; text-align: center; }}
</style>
</head>
<body>

<header>
  <span style="font-size:22px">🌍</span>
  <h1>世界の緊張地帯 航空・船舶活動モニター</h1>
  <span class="updated">更新: {timestamp}</span>
</header>

<div class="legend">
  <span><span class="dot" style="background:#4fc3f7"></span>航空機</span>
  <span><span class="dot" style="background:#e74c3c"></span>緊急スコーク</span>
  <span><span class="dot" style="background:#a8d8a8"></span>船舶（通常）</span>
  <span><span class="dot" style="background:#f39c12"></span>タンカー</span>
  <span><span class="dot" style="background:#e74c3c"></span>軍用船</span>
</div>

<div id="map"></div>
<div class="cards">{cards_html}</div>

<footer>データソース: OpenSky Network (CC BY 4.0)・AISstream.io — 研究・教育目的のみ</footer>

<script>
const regions  = {regions_json};
const aircraft = {aircraft_json};
const ships    = {ships_json};

const map = L.map('map').setView([26, 45], 5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO'
}}).addTo(map);

Object.entries(regions).forEach(([id, r]) => {{
  const color = r.score > 60 ? '#e74c3c' : r.score > 30 ? '#f39c12' : '#27ae60';
  L.rectangle(r.bounds, {{ color, weight: 1.5, fillOpacity: 0.08 }}).addTo(map)
   .bindTooltip(`${{r.name}}　スコア: ${{r.score}}`, {{ sticky: true }});
}});

aircraft.forEach(a => {{
  const color = a.emergency ? '#e74c3c' : '#4fc3f7';
  const alt = a.altitude != null ? Math.round(a.altitude) + ' m' : '不明';
  L.circleMarker([a.lat, a.lon], {{ radius: 4, color, fillColor: color, fillOpacity: 0.85, weight: 1 }})
   .bindPopup(`<b>${{a.callsign || a.icao24}}</b><br>国: ${{a.country}}<br>高度: ${{alt}}<br>地域: ${{a.region}}`)
   .addTo(map);
}});

ships.forEach(s => {{
  const color = s.military ? '#e74c3c' : s.tanker ? '#f39c12' : '#a8d8a8';
  const sog = s.sog != null ? s.sog.toFixed(1) + ' kt' : '不明';
  L.circleMarker([s.lat, s.lon], {{ radius: 5, color, fillColor: color, fillOpacity: 0.75, weight: 1 }})
   .bindPopup(`<b>🚢 ${{s.name || s.mmsi}}</b><br>種別: ${{s.type_label || 'その他'}}<br>旗国: ${{s.flag || '不明'}}<br>速度: ${{sog}}<br>状態: ${{s.nav_status || '不明'}}<br>目的地: ${{s.destination || '不明'}}`)
   .addTo(map);
}});
</script>
</body>
</html>'''


def _score_color(score):
    if score > 60: return '#e74c3c'
    if score > 30: return '#f39c12'
    return '#27ae60'


def _card_html(region_id, data):
    region_name = REGIONS[region_id]['name']
    score       = data['anomaly_score']
    ships       = data.get('ships', {})

    air_tags = ''.join(
        f'<span class="tag air">{c} ({n})</span>'
        for c, n in list(data['countries'].items())[:5]
    )
    ship_tags = ''.join(
        f'<span class="tag ship">{f} ({n})</span>'
        for f, n in list(ships.get('flags', {}).items())[:5]
    )

    alert = ''
    if data['emergency']:
        labels = '、'.join(e['squawk_label'] for e in data['emergency'])
        alert = f'<div class="alert">🚨 緊急スコーク: {labels}</div>'

    ship_section = ''
    if ships.get('count', 0) > 0:
        dest_str = '　'.join(
            f'{d}({n})' for d, n in list(ships.get('destinations', {}).items())[:3]
        )
        ship_section = f'''
<hr class="divider">
<div class="section-title">🚢 船舶</div>
<div class="stats">
  <div class="stat"><span class="num ship">{ships["count"]}</span><span class="label">船舶</span></div>
  <div class="stat"><span class="num ship">{ships["tankers"]}</span><span class="label">タンカー</span></div>
  <div class="stat"><span class="num ship">{ships["military"]}</span><span class="label">軍用</span></div>
  <div class="stat"><span class="num ship">{ships["anchored"]}</span><span class="label">錨泊</span></div>
</div>
{"<div style='font-size:11px;color:#888;margin-top:4px'>目的地: " + dest_str + "</div>" if dest_str else ""}
<div class="tags">{ship_tags}</div>'''

    return f'''
<div class="card">
  <div class="card-header">
    <span class="region-name">{region_name}</span>
    <span class="score" style="background:{_score_color(score)}">スコア {score}</span>
  </div>
  <div class="section-title">✈️ 航空機</div>
  <div class="stats">
    <div class="stat"><span class="num">{data["count"]}</span><span class="label">航空機</span></div>
    <div class="stat"><span class="num">{data["low_altitude"]}</span><span class="label">低高度</span></div>
    <div class="stat"><span class="num">{len(data["notable"])}</span><span class="label">注目国</span></div>
  </div>
  {alert}
  <div class="tags">{air_tags}</div>
  {ship_section}
</div>'''


def _regions_for_map(results):
    out = {}
    for rid, data in results.items():
        r = REGIONS[rid]
        b = r['bounds']
        out[rid] = {
            'name':   r['name'],
            'center': r['center'],
            'bounds': [[b['lamin'], b['lomin']], [b['lamax'], b['lomax']]],
            'score':  data['anomaly_score'],
        }
    return out


def _aircraft_for_map(results):
    out = []
    for rid, data in results.items():
        region_name = REGIONS[rid]['name']
        for a in data['aircraft']:
            out.append({
                'lat': a['lat'], 'lon': a['lon'],
                'icao24': a['icao24'], 'callsign': a['callsign'],
                'country': a['country'], 'altitude': a['altitude'],
                'region': region_name,
                'emergency': a['squawk'] in ('7500', '7600', '7700') if a['squawk'] else False,
            })
    return out


def _ships_for_map(results):
    out = []
    for rid, data in results.items():
        region_name = REGIONS[rid]['name']
        for s in data.get('ships', {}).get('ships', []):
            ship_type = s.get('ship_type', 0)
            out.append({
                'lat': s['lat'], 'lon': s['lon'],
                'mmsi': s['mmsi'], 'name': s.get('name', ''),
                'flag': s.get('flag', ''), 'sog': s.get('sog'),
                'nav_status': s.get('nav_status', '不明'),
                'destination': s.get('destination', ''),
                'type_label': s.get('type_label', 'その他'),
                'tanker':   80 <= ship_type <= 89,
                'military': ship_type == 35,
                'region':   region_name,
            })
    return out
