"""HTML レポート生成モジュール（全世界・時系列対応）"""
import json
from config import REGIONS


def generate(results, trend, history, timestamp, all_fires=None, all_events=None):
    regions_json = json.dumps(_regions_for_map(results, trend), ensure_ascii=False)
    ships_json   = json.dumps(_ships_for_map(results), ensure_ascii=False)
    fires_json   = json.dumps(all_fires or _fires_for_map(results), ensure_ascii=False)
    events_json  = json.dumps(all_events or _events_for_map(results), ensure_ascii=False)
    history_json = json.dumps(_history_for_chart(history), ensure_ascii=False)
    cards_html   = ''.join(_card_html(rid, results[rid], trend[rid]) for rid in results)

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
           display: flex; gap: 14px; font-size: 11px; color: #aaa; flex-wrap: wrap; align-items: center; }}
.legend span {{ display: flex; align-items: center; gap: 4px; }}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
.toggle-btn {{ font-size: 11px; padding: 3px 10px; border-radius: 4px; cursor: pointer;
               border: 1px solid #3a3a5a; background: #2a2a4a; color: #eee;
               transition: opacity 0.2s; user-select: none; }}
.toggle-btn.off {{ opacity: 0.35; }}
.chart-section {{ padding: 14px; background: #16213e; border-bottom: 1px solid #2a2a4a; }}
.chart-section h2 {{ font-size: 13px; color: #aaa; margin-bottom: 10px; }}
.chart-wrap {{ position: relative; height: 200px; }}
.chart-legend {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }}
.chart-legend label {{ display: flex; align-items: center; gap: 5px; cursor: pointer;
                        font-size: 11px; padding: 2px 8px; border-radius: 4px;
                        background: #1a1a2e; color: #ccc; user-select: none; }}
.chart-legend label:hover {{ background: #2a2a4a; }}
.chart-legend input[type=checkbox] {{ width: 12px; height: 12px; cursor: pointer; margin: 0; flex-shrink: 0; }}
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
.tag.ship {{ background: #0d3d2a; color: #afa; }}
.divider {{ border: none; border-top: 1px solid #2a2a4a; margin: 8px 0; }}
.trend-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 6px 0; }}
.trend-table th {{ color: #666; font-weight: normal; padding: 2px 6px; text-align: right; font-size: 10px; }}
.trend-table td {{ padding: 3px 6px; text-align: right; color: #ccc; }}
.trend-table td:first-child {{ text-align: left; color: #888; }}
footer {{ padding: 10px; font-size: 11px; color: #555; text-align: center; }}
</style>
</head>
<body>

<header>
  <span style="font-size:22px">🌍</span>
  <h1>世界の緊張地帯 船舶・火災・紛争モニター</h1>
  <span class="updated">更新: {timestamp}</span>
</header>

<div class="legend">
  <button id="btn-ships" class="toggle-btn" onclick="toggleLayer('ships')">
    🚢 船舶 <span id="cnt-ships"></span>
  </button>
  <button id="btn-fires" class="toggle-btn" onclick="toggleLayer('fires')">
    🔥 火災 <span id="cnt-fires"></span>
  </button>
  <button id="btn-events" class="toggle-btn" onclick="toggleLayer('events')">
    📰 紛争 <span id="cnt-events"></span>
  </button>
  <span style="margin-left:6px; color:#555;">|</span>
  <span><span class="dot" style="background:#e74c3c"></span>軍用</span>
  <span><span class="dot" style="background:#a8d8a8"></span>船舶</span>
  <span><span class="dot" style="background:#f39c12"></span>タンカー</span>
  <span style="display:flex;align-items:center;gap:5px;">
    <span style="width:80px;height:8px;border-radius:4px;display:inline-block;
                 background:linear-gradient(to right,#cc4400,#ff8800,#ffff00,#ffffff);"></span>
    🔥 200MW → 1000MW+
  </span>
  <span><span class="dot" style="background:#c678dd"></span>紛争イベント</span>
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
  <h2>📈 指標別件数推移（過去7日間・全地域合計）</h2>
  <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
  <div class="chart-legend" id="chartLegend"></div>
</div>

<div class="cards">{cards_html}</div>

<footer>データソース: AISstream.io · NASA FIRMS · GDELT 2.0 — 研究・教育目的のみ</footer>

<script>
const regions  = {regions_json};
const ships    = {ships_json};
const fires    = {fires_json};
const events   = {events_json};
const histData = {history_json};
const SUPABASE_URL  = 'https://iuyiqlyqfhahwxiwoztd.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eWlxbHlxZmhhaHd4aXdvenRkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NDQxOTAsImV4cCI6MjA4OTUyMDE5MH0.VfCuijogWh9UizHIyPxvzD-HarBzrGRWKCyMNwKja3k';

// ── 地図（Canvas レンダラーで高速描画）──────────────────────────
const renderer   = L.canvas({{ padding: 0.5 }});
const map        = L.map('map').setView([20, 40], 3);
const shipLayer  = L.layerGroup().addTo(map);
const fireLayer  = L.layerGroup().addTo(map);
const eventLayer = L.layerGroup().addTo(map);

// レイヤー表示状態
const layerState = {{ ships: true, fires: true, events: true }};
const layerMap   = {{ ships: shipLayer, fires: fireLayer, events: eventLayer }};

function toggleLayer(name) {{
  layerState[name] = !layerState[name];
  const btn = document.getElementById('btn-' + name);
  btn.classList.toggle('off', !layerState[name]);
  const layer = layerMap[name];
  if (layerState[name]) {{ map.addLayer(layer); }} else {{ map.removeLayer(layer); }}
}}

function updateCount(name, n) {{
  const el = document.getElementById('cnt-' + name);
  if (el) el.textContent = n > 0 ? `(${{n}})` : '';
}}

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

// ── 火災・船舶レンダリング関数 ───────────────────────────────────
function fireColor(frp) {{
  // 対数スケール: 200MW→0、1000MW→1（以上は白）
  const t = Math.min(Math.log(frp / 200) / Math.log(5), 1);
  // 暗オレンジ→オレンジ→黄→白 の4段階グラデーション
  const stops = [[0xcc,0x44,0x00],[0xff,0x88,0x00],[0xff,0xff,0x00],[0xff,0xff,0xff]];
  const seg = t * (stops.length - 1);
  const i   = Math.min(Math.floor(seg), stops.length - 2);
  const s   = seg - i;
  const r   = Math.round(stops[i][0] + (stops[i+1][0] - stops[i][0]) * s);
  const g   = Math.round(stops[i][1] + (stops[i+1][1] - stops[i][1]) * s);
  const b   = Math.round(stops[i][2] + (stops[i+1][2] - stops[i][2]) * s);
  return `rgb(${{r}},${{g}},${{b}})`;
}}

function renderFires(data) {{
  fireLayer.clearLayers();
  data.forEach(f => {{
    const color  = fireColor(f.frp);
    const radius = Math.min(3 + Math.log10(Math.max(f.frp, 200) / 200) * 4, 10);
    L.circleMarker([f.lat, f.lon], {{ radius, color, fillColor: color, fillOpacity: 0.85, weight: 0, renderer }})
     .bindPopup(`<b>🔥 火災</b><br>強度: ${{f.frp}} MW<br>信頼度: ${{f.confidence}}<br>${{f.acq_date}} ${{f.acq_time}}`)
     .addTo(fireLayer);
  }});
  updateCount('fires', data.length);
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
  updateCount('ships', data.length);
}}

function renderEvents(data) {{
  eventLayer.clearLayers();
  data.forEach(e => {{
    const tone   = e.avg_tone || 0;
    const radius = Math.min(4 + Math.floor(e.num_articles / 10), 10);
    L.circleMarker([e.lat, e.lon], {{
      radius, color: '#c678dd', fillColor: '#c678dd', fillOpacity: 0.6, weight: 1, renderer
    }}).bindPopup(
      `<b>📰 ${{e.event_label || 'Conflict event'}}</b><br>` +
      `${{e.location || ''}}<br>` +
      `${{e.actor1 || '?'}} vs ${{e.actor2 || '?'}}<br>` +
      `Articles: ${{e.num_articles}}　Goldstein: ${{e.goldstein}}<br>` +
      (e.source_url ? `<a href="${{e.source_url}}" target="_blank" style="color:#88ccff">📎 Source</a>` : '')
    ).addTo(eventLayer);
  }});
  updateCount('events', data.length);
}}

// 初期表示（HTMLに埋め込まれた現在データ）
renderFires(fires);
renderShips(ships);
renderEvents(events);

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

  const ets = encodeURIComponent(ts);
  const [f, s] = await Promise.all([
    sbFetch(`fires?captured_at=eq.${{ets}}&select=lat,lon,frp,confidence,acq_date,acq_time`),
    sbFetch(`ships?captured_at=eq.${{ets}}&select=lat,lon,mmsi,name,flag,ship_type,type_label,sog,nav_status`),
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
const trendChart = new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: histData.labels,
    datasets: histData.datasets.map(d => ({{
      label:           d.label,
      data:            d.data,
      borderColor:     d.color,
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      pointRadius: 2,
      tension:     0.3,
      yAxisID:     d.label.includes('船舶') ? 'yShip' : 'yOther',
    }})),
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{
        ticks: {{
          color: '#666', font: {{ size: 10 }},
          maxTicksLimit: 40,
          callback: function(val, index) {{
            const label    = histData.labels[index] || '';
            const prevLabel= histData.labels[index - 1] || '';
            const [date, time]     = label.split(' ');
            const [prevDate]       = prevLabel.split(' ');
            if (date !== prevDate) return date;  // 日付が変わった時点で日付表示
            const n    = histData.labels.length;
            const step = Math.max(Math.floor(n / 8), 1);
            if (index % step === 0) return time;
            if (index === n - 1) return time;
            return null;
          }},
        }},
        grid: {{ color: '#2a2a4a' }},
      }},
      yShip:  {{ position: 'left',  ticks: {{ color: '#a8d8a8', font: {{ size: 10 }} }}, grid: {{ color: '#2a2a4a' }}, min: 0 }},
      yOther: {{ position: 'right', ticks: {{ color: '#888',    font: {{ size: 10 }} }}, grid: {{ drawOnChartArea: false }}, min: 0 }},
    }},
  }},
}});

// カスタム凡例（チェックボックス）
const legendEl = document.getElementById('chartLegend');
trendChart.data.datasets.forEach((ds, i) => {{
  const lbl = document.createElement('label');
  const cb  = document.createElement('input');
  cb.type    = 'checkbox';
  cb.checked = true;
  cb.style.accentColor = ds.borderColor;
  cb.onchange = () => {{ trendChart.setDatasetVisibility(i, cb.checked); trendChart.update(); }};
  const bar = document.createElement('span');
  bar.style.cssText = `width:16px;height:3px;background:${{ds.borderColor}};display:inline-block;border-radius:2px;flex-shrink:0;`;
  lbl.appendChild(cb);
  lbl.appendChild(bar);
  lbl.appendChild(document.createTextNode(ds.label));
  legendEl.appendChild(lbl);
}});
</script>
</body>
</html>'''


def _score_color(score):
    if score > 60: return '#e74c3c'
    if score > 30: return '#f39c12'
    return '#27ae60'


def _pct_cell(pct):
    if pct > 0:
        return f'<span class="up">▲{pct:+.0f}%</span>'
    if pct < 0:
        return f'<span class="down">▼{abs(pct):.0f}%</span>'
    return '<span style="color:#666">±0%</span>'


def _card_html(region_id, data, t):
    region_name = REGIONS[region_id]['name']
    ships       = data.get('ships', {})
    fires       = data.get('fires', {})
    surge_class = 'surge' if t['is_surge'] else ''
    surge_badge = ' 🚨' if t['is_surge'] else ''

    ts, tf, te = t['ships'], t['fires'], t['events']
    trend_html = f'''
<table class="trend-table">
  <tr><th></th><th>現在</th><th>7日比</th><th>24h比</th></tr>
  <tr><td>🚢 船舶</td><td>{ts["current"]}隻</td><td>{_pct_cell(ts["week_pct"])}</td><td>{_pct_cell(ts["day_pct"])}</td></tr>
  <tr><td>🔥 火災</td><td>{tf["current"]}件</td><td>{_pct_cell(tf["week_pct"])}</td><td>{_pct_cell(tf["day_pct"])}</td></tr>
  <tr><td>📰 紛争</td><td>{te["current"]}件</td><td>{_pct_cell(te["week_pct"])}</td><td>{_pct_cell(te["day_pct"])}</td></tr>
</table>'''

    ship_tags = ''.join(
        f'<span class="tag ship">{f} ({n})</span>'
        for f, n in list(ships.get('flags', {}).items())[:4]
    )

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

    events     = data.get('events', {})
    event_section = ''
    if events.get('count', 0) > 0:
        event_section = f'''
<hr class="divider">
<div class="section-title">📰 紛争イベント（GDELT）</div>
<div class="stats">
  <div class="stat"><span class="num" style="color:#c678dd">{events["count"]}</span><span class="label">件数</span></div>
  <div class="stat"><span class="num" style="color:#c678dd">{events["avg_goldstein"]}</span><span class="label">Goldstein平均</span></div>
  <div class="stat"><span class="num" style="color:#c678dd">{events["total_articles"]}</span><span class="label">報道記事数</span></div>
</div>'''

    return f'''
<div class="card {surge_class}">
  <div class="card-header">
    <span class="region-name">{region_name}{surge_badge}</span>
  </div>
  {trend_html}
  {ship_section}
  {fire_section}
  {event_section}
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


def _events_for_map(results):
    out = []
    seen = set()
    for rid, data in results.items():
        for e in data.get('events', {}).get('events', []):
            key = (e['lat'], e['lon'], e.get('event_code'))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                'lat':          e['lat'],
                'lon':          e['lon'],
                'event_label':  e.get('event_label', e.get('event_code', '')),
                'goldstein':    e.get('goldstein', 0),
                'num_articles': e.get('num_articles', 0),
                'actor1':       e.get('actor1', ''),
                'actor2':       e.get('actor2', ''),
                'location':     e.get('location', ''),
                'source_url':   e.get('source_url', ''),
            })
    return out


def _history_for_chart(history):
    """Chart.js 用にデータを整形（指標別の全地域合計件数）"""
    entries = history.get('entries', [])
    if not entries:
        return {'labels': [], 'datasets': []}

    labels, ships_total, fires_total, events_total = [], [], [], []
    for e in entries:
        ts = e['timestamp']
        try:
            labels.append(ts[5:16].replace('-', '/'))
        except Exception:
            labels.append(ts)
        regs = e.get('regions', {})
        ships_total.append(sum(r.get('ship_count', 0)  for r in regs.values()))
        fires_total.append(sum(r.get('fire_count', 0)  for r in regs.values()))
        events_total.append(sum(r.get('event_count', 0) for r in regs.values()))

    return {
        'labels': labels,
        'datasets': [
            {'label': '🚢 船舶',       'data': ships_total,  'color': '#a8d8a8'},
            {'label': '🔥 火災',       'data': fires_total,  'color': '#ff8800'},
            {'label': '📰 紛争イベント', 'data': events_total, 'color': '#c678dd'},
        ],
    }
