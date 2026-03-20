"""HTML レポート生成モジュール（全世界・時系列対応）"""
import json
from config import REGIONS


def generate(results, trend, history, timestamp, global_aircraft=None):
    regions_json  = json.dumps(_regions_for_map(results, trend), ensure_ascii=False)
    aircraft_json = json.dumps(_aircraft_for_map(results, global_aircraft), ensure_ascii=False)
    ships_json    = json.dumps(_ships_for_map(results), ensure_ascii=False)
    fires_json    = json.dumps(_fires_for_map(results), ensure_ascii=False)
    history_json  = json.dumps(_history_for_chart(history), ensure_ascii=False)
    cards_html    = ''.join(_card_html(rid, results[rid], trend[rid]) for rid in results)

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>世界の緊張地帯 活動モニター</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #1a1a2e; color: #eee; }}
header {{ padding: 14px 20px; background: #16213e; border-bottom: 1px solid #2a2a4a;
          display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
header h1 {{ font-size: 17px; }}
.updated {{ font-size: 12px; color: #888; margin-left: auto; }}
#map {{ height: 50vh; }}
.legend {{ padding: 6px 16px; background: #16213e; border-bottom: 1px solid #2a2a4a;
           display: flex; gap: 14px; font-size: 11px; color: #aaa; flex-wrap: wrap; }}
.legend span {{ display: flex; align-items: center; gap: 4px; }}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
.chart-section {{ padding: 14px; background: #16213e; border-bottom: 1px solid #2a2a4a; }}
.chart-section h2 {{ font-size: 13px; color: #aaa; margin-bottom: 10px; }}
.chart-wrap {{ position: relative; height: 200px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 12px; padding: 12px; }}
.card {{ background: #16213e; border-radius: 10px; padding: 14px; border: 1px solid #2a2a4a; }}
.card.surge {{ border-color: #e74c3c; box-shadow: 0 0 8px rgba(231,76,60,0.3); }}
.card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.region-name {{ font-weight: 600; font-size: 14px; }}
.score {{ font-size: 12px; font-weight: bold; color: #fff; padding: 3px 10px; border-radius: 12px; }}
.trend {{ font-size: 11px; margin-bottom: 10px; color: #aaa; }}
.trend .up {{ color: #e74c3c; font-weight: bold; }}
.trend .down {{ color: #27ae60; }}
.section-title {{ font-size: 11px; color: #888; margin: 8px 0 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
.stats {{ display: flex; gap: 14px; margin-bottom: 4px; }}
.stat .num {{ display: block; font-size: 19px; font-weight: bold; color: #4fc3f7; }}
.stat .num.ship {{ color: #a8d8a8; }}
.stat .num.fire {{ color: #ff8c00; }}
.stat .label {{ font-size: 10px; color: #888; }}
.alert {{ background: #4a1010; border: 1px solid #c0392b; border-radius: 6px;
          padding: 7px 10px; font-size: 12px; margin: 6px 0; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; }}
.tag {{ font-size: 11px; padding: 2px 7px; border-radius: 4px; }}
.tag.air {{ background: #0f3460; color: #adf; }}
.tag.ship {{ background: #0d3d2a; color: #afa; }}
.divider {{ border: none; border-top: 1px solid #2a2a4a; margin: 8px 0; }}
footer {{ padding: 10px; font-size: 11px; color: #555; text-align: center; }}
</style>
</head>
<body>

<header>
  <span style="font-size:22px">🌍</span>
  <h1>世界の緊張地帯 航空・船舶・火災モニター</h1>
  <span class="updated">更新: {timestamp}</span>
</header>

<div class="legend">
  <span><span class="dot" style="background:#4fc3f7"></span>航空機</span>
  <span><span class="dot" style="background:#e74c3c"></span>緊急スコーク</span>
  <span><span class="dot" style="background:#a8d8a8"></span>船舶</span>
  <span><span class="dot" style="background:#f39c12"></span>タンカー</span>
  <span><span class="dot" style="background:#cc4400"></span>火災 20〜50MW</span>
  <span><span class="dot" style="background:#ff8800"></span>火災 50〜200MW</span>
  <span><span class="dot" style="background:#ffff00"></span>火災 200〜1000MW</span>
  <span><span class="dot" style="background:#ffffff"></span>火災 1000MW〜</span>
</div>

<div id="tsSection" style="display:none; padding:10px 16px; background:#16213e; border-bottom:1px solid #2a2a4a;">
  <div style="display:flex; align-items:center; gap:12px;">
    <span style="font-size:12px; color:#888;">⏱ 履歴</span>
    <input type="range" id="tsSlider" min="0" value="0" step="1" style="flex:1; accent-color:#4fc3f7;"
           oninput="onSliderChange(+this.value)">
    <span id="tsLabel" style="font-size:12px; color:#eee; min-width:130px; text-align:right;"></span>
    <button id="tsNowBtn" onclick="goToLatest()"
            style="font-size:11px; padding:3px 10px; background:#2a2a4a; color:#aaa;
                   border:1px solid #3a3a5a; border-radius:4px; cursor:pointer;">現在</button>
  </div>
</div>

<div id="map"></div>

<div class="chart-section">
  <h2>📈 地域別スコア推移（過去7日間）</h2>
  <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
</div>

<div class="cards">{cards_html}</div>

<footer>データソース: OpenSky Network (CC BY 4.0) · AISstream.io · NASA FIRMS — 研究・教育目的のみ</footer>

<script>
const regions  = {regions_json};
const aircraft = {aircraft_json};
const ships    = {ships_json};
const fires    = {fires_json};
const histData = {history_json};
const SUPABASE_URL  = 'https://iuyiqlyqfhahwxiwoztd.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eWlxbHlxZmhhaHd4aXdvenRkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NDQxOTAsImV4cCI6MjA4OTUyMDE5MH0.VfCuijogWh9UizHIyPxvzD-HarBzrGRWKCyMNwKja3k';

// ── 地図（Canvas レンダラーで高速描画）──────────────────────────
const renderer  = L.canvas({{ padding: 0.5 }});
const map       = L.map('map').setView([20, 40], 3);
const fireLayer = L.layerGroup().addTo(map);
const shipLayer = L.layerGroup().addTo(map);

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO'
}}).addTo(map);

// 監視地域ボックス
Object.entries(regions).forEach(([id, r]) => {{
  const color = r.surge ? '#e74c3c' : r.score > 60 ? '#e74c3c' : r.score > 30 ? '#f39c12' : '#27ae60';
  L.rectangle(r.bounds, {{ color, weight: r.surge ? 2 : 1, fillOpacity: r.surge ? 0.15 : 0.06, renderer }})
   .addTo(map)
   .bindTooltip(`${{r.name}}　スコア: ${{r.score}}${{r.surge ? ' 🚨急上昇' : ''}}`, {{ sticky: true }});
}});

// 航空機（Canvas・常に現在のデータ）
aircraft.forEach(a => {{
  const color = a.emergency ? '#e74c3c' : '#4fc3f7';
  const alt   = a.altitude != null ? Math.round(a.altitude) + ' m' : '不明';
  L.circleMarker([a.lat, a.lon], {{ radius: 3, color, fillColor: color, fillOpacity: 0.8, weight: 1, renderer }})
   .bindPopup(`<b>${{a.callsign || a.icao24}}</b><br>国: ${{a.country}}<br>高度: ${{alt}}`)
   .addTo(map);
}});

// ── 火災・船舶レンダリング関数 ───────────────────────────────────
function fireColor(frp) {{
  if (frp >= 1000) return '#ffffff';  // 白：超大規模
  if (frp >= 200)  return '#ffff00';  // 黄：大規模
  if (frp >= 50)   return '#ff8800';  // 明オレンジ：中規模
  return '#cc4400';                   // 暗いオレンジ：小規模（20〜50MW）
}}

function renderFires(data) {{
  fireLayer.clearLayers();
  data.forEach(f => {{
    const color  = fireColor(f.frp);
    const radius = f.frp >= 1000 ? 8 : f.frp >= 200 ? 6 : f.frp >= 50 ? 5 : 4;
    L.circleMarker([f.lat, f.lon], {{ radius, color, fillColor: color, fillOpacity: 0.8, weight: 0, renderer }})
     .bindPopup(`<b>🔥 火災</b><br>強度: ${{f.frp}} MW<br>信頼度: ${{f.confidence}}<br>${{f.acq_date}} ${{f.acq_time}}`)
     .addTo(fireLayer);
  }});
}}

function renderShips(data) {{
  shipLayer.clearLayers();
  data.forEach(s => {{
    const t     = s.ship_type || 0;
    const color = t === 35 ? '#e74c3c' : (t >= 80 && t <= 89) ? '#f39c12' : '#a8d8a8';
    const sog   = s.sog != null ? (+s.sog).toFixed(1) + ' kt' : '不明';
    L.circleMarker([s.lat, s.lon], {{ radius: 4, color, fillColor: color, fillOpacity: 0.7, weight: 1, renderer }})
     .bindPopup(`<b>🚢 ${{s.name || s.mmsi}}</b><br>種別: ${{s.type_label}}<br>速度: ${{sog}}<br>状態: ${{s.nav_status}}`)
     .addTo(shipLayer);
  }});
}}

// 初期表示（HTMLに埋め込まれた現在データ）
renderFires(fires);
renderShips(ships);

// ── タイムスライダー（Supabase 履歴） ───────────────────────────
let timestamps = [];

async function sbFetch(path) {{
  const res = await fetch(`${{SUPABASE_URL}}/rest/v1/${{path}}`, {{
    headers: {{ apikey: SUPABASE_ANON, Authorization: `Bearer ${{SUPABASE_ANON}}` }}
  }});
  return res.json();
}}

async function onSliderChange(idx) {{
  const ts  = timestamps[idx];
  const isLatest = idx === timestamps.length - 1;
  const d   = new Date(ts);
  const lbl = d.toLocaleString('ja-JP', {{ month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }});
  document.getElementById('tsLabel').textContent = isLatest ? `現在 (${{lbl}})` : lbl;
  document.getElementById('tsNowBtn').style.opacity = isLatest ? '0.4' : '1';

  const [f, s] = await Promise.all([
    sbFetch(`fires?captured_at=eq.${{ts}}&select=lat,lon,frp,confidence,acq_date,acq_time`),
    sbFetch(`ships?captured_at=eq.${{ts}}&select=lat,lon,mmsi,name,flag,ship_type,type_label,sog,nav_status`),
  ]);
  renderFires(f);
  renderShips(s);
}}

function goToLatest() {{
  const slider = document.getElementById('tsSlider');
  slider.value = timestamps.length - 1;
  onSliderChange(timestamps.length - 1);
}}

(async () => {{
  try {{
    const rows = await sbFetch('ship_timestamps?order=captured_at.desc&limit=200');
    for (const r of rows) {{ timestamps.push(r.captured_at); }}
    timestamps.reverse();
    if (timestamps.length < 2) return;
    const slider = document.getElementById('tsSlider');
    slider.max   = timestamps.length - 1;
    slider.value = timestamps.length - 1;
    onSliderChange(timestamps.length - 1);
    document.getElementById('tsSection').style.display = 'block';
  }} catch(e) {{ console.warn('Supabase 履歴取得失敗:', e); }}
}})();

// ── 時系列グラフ ────────────────────────────────────────────────
const COLORS = [
  '#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6',
  '#1abc9c','#e67e22','#34495e','#e91e63','#00bcd4','#8bc34a'
];

const ctx = document.getElementById('trendChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: histData.labels,
    datasets: histData.regions.map((r, i) => ({{
      label:       r.name,
      data:        r.scores,
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      pointRadius: 2,
      tension:     0.3,
    }})),
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#aaa', font: {{ size: 11 }}, boxWidth: 12 }} }},
    }},
    scales: {{
      x: {{ ticks: {{ color: '#666', maxTicksLimit: 12, font: {{ size: 10 }} }}, grid: {{ color: '#2a2a4a' }} }},
      y: {{ ticks: {{ color: '#666', font: {{ size: 10 }} }}, grid: {{ color: '#2a2a4a' }}, min: 0, max: 100 }},
    }},
  }},
}});
</script>
</body>
</html>'''


def _score_color(score):
    if score > 60: return '#e74c3c'
    if score > 30: return '#f39c12'
    return '#27ae60'


def _card_html(region_id, data, t):
    region_name = REGIONS[region_id]['name']
    score       = data['anomaly_score']
    ships       = data.get('ships', {})
    fires       = data.get('fires', {})
    surge_class = 'surge' if t['is_surge'] else ''

    # トレンド表示
    cp = t['change_pct']
    if cp > 0:
        trend_html = f'<div class="trend">ベースライン {t["baseline"]} → <span class="up">▲{cp:+.1f}%</span></div>'
    elif cp < 0:
        trend_html = f'<div class="trend">ベースライン {t["baseline"]} → <span class="down">▼{cp:.1f}%</span></div>'
    else:
        trend_html = ''

    surge_badge = ' 🚨 急上昇' if t['is_surge'] else ''

    air_tags = ''.join(
        f'<span class="tag air">{c} ({n})</span>'
        for c, n in list(data['countries'].items())[:5]
    )
    ship_tags = ''.join(
        f'<span class="tag ship">{f} ({n})</span>'
        for f, n in list(ships.get('flags', {}).items())[:4]
    )

    alert = ''
    if data['emergency']:
        labels = '、'.join(e['squawk_label'] for e in data['emergency'])
        alert = f'<div class="alert">🚨 緊急スコーク: {labels}</div>'

    ship_section = ''
    if ships.get('count', 0) > 0:
        ship_section = f'''
<hr class="divider">
<div class="section-title">🚢 船舶</div>
<div class="stats">
  <div class="stat"><span class="num ship">{ships["count"]}</span><span class="label">船舶</span></div>
  <div class="stat"><span class="num ship">{ships["tankers"]}</span><span class="label">タンカー</span></div>
  <div class="stat"><span class="num ship">{ships["military"]}</span><span class="label">軍用</span></div>
  <div class="stat"><span class="num ship">{ships["anchored"]}</span><span class="label">錨泊</span></div>
</div>
<div class="tags">{ship_tags}</div>'''

    fire_section = ''
    if fires.get('count', 0) > 0:
        fire_section = f'''
<hr class="divider">
<div class="section-title">🔥 火災（NASA FIRMS）</div>
<div class="stats">
  <div class="stat"><span class="num fire">{fires["count"]}</span><span class="label">検知数</span></div>
  <div class="stat"><span class="num fire">{fires["high_conf"]}</span><span class="label">高信頼</span></div>
  <div class="stat"><span class="num fire">{fires["intense"]}</span><span class="label">高強度</span></div>
  <div class="stat"><span class="num fire">{fires["total_frp"]}</span><span class="label">総強度MW</span></div>
</div>'''

    return f'''
<div class="card {surge_class}">
  <div class="card-header">
    <span class="region-name">{region_name}{surge_badge}</span>
    <span class="score" style="background:{_score_color(score)}">スコア {score}</span>
  </div>
  {trend_html}
  <div class="section-title">✈️ 航空機</div>
  <div class="stats">
    <div class="stat"><span class="num">{data["count"]}</span><span class="label">航空機</span></div>
    <div class="stat"><span class="num">{data["low_altitude"]}</span><span class="label">低高度</span></div>
    <div class="stat"><span class="num">{len(data["notable"])}</span><span class="label">注目国</span></div>
  </div>
  {alert}
  <div class="tags">{air_tags}</div>
  {ship_section}
  {fire_section}
</div>'''


def _regions_for_map(results, trend):
    out = {}
    for rid, data in results.items():
        r = REGIONS[rid]
        b = r['bounds']
        out[rid] = {
            'name':   r['name'],
            'center': r['center'],
            'bounds': [[b['lamin'], b['lomin']], [b['lamax'], b['lomax']]],
            'score':  data['anomaly_score'],
            'surge':  trend[rid]['is_surge'],
        }
    return out


def _aircraft_for_map(results, global_aircraft=None):
    # 全世界リストがあればそちらを優先、なければ地域データを集約
    source = global_aircraft if global_aircraft is not None else (
        a for data in results.values() for a in data.get('aircraft', [])
    )
    return [
        {
            'lat': a['lat'], 'lon': a['lon'],
            'icao24': a['icao24'], 'callsign': a['callsign'],
            'country': a['country'], 'altitude': a['altitude'],
            'emergency': a['squawk'] in ('7500', '7600', '7700') if a['squawk'] else False,
        }
        for a in source
        if not a.get('on_ground')
    ]


def _ships_for_map(results):
    out = []
    for rid, data in results.items():
        for s in data.get('ships', {}).get('ships', []):
            ship_type = s.get('ship_type', 0)
            out.append({
                'lat': s['lat'], 'lon': s['lon'],
                'mmsi': s['mmsi'], 'name': s.get('name', ''),
                'flag': s.get('flag', ''), 'sog': s.get('sog'),
                'nav_status': s.get('nav_status', '不明'),
                'type_label': s.get('type_label', 'その他'),
                'tanker':   80 <= ship_type <= 89,
                'military': ship_type == 35,
            })
    return out


def _fires_for_map(results):
    out = []
    for rid, data in results.items():
        for f in data.get('fires', {}).get('fires', []):
            out.append(f)
    return out


def _history_for_chart(history):
    """Chart.js 用にデータを整形"""
    entries = history.get('entries', [])
    if not entries:
        return {'labels': [], 'regions': []}

    labels = []
    for e in entries:
        ts = e['timestamp']
        # "2026-03-20 01:00:00" → "3/20 01:00"
        try:
            dt = ts[5:16].replace('-', '/').replace(' ', ' ')
            labels.append(dt)
        except Exception:
            labels.append(ts)

    region_data = []
    for rid, region in REGIONS.items():
        scores = [
            e['regions'].get(rid, {}).get('anomaly_score', 0)
            for e in entries
        ]
        region_data.append({
            'name':   region['name'],
            'scores': scores,
        })

    return {'labels': labels, 'regions': region_data}
