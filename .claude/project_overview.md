---
name: プロジェクト概要
description: mideast-monitorの構成・データソース・実装内容
type: project
---

## プロジェクト概要
世界の緊張地帯（中東・ウクライナ・東アジア等）の船舶・火災・紛争イベントをリアルタイム監視するWebアプリ。

**Why:** 地政学的リスクの可視化。スコアではなく生データの変化で異常を察知する。

## ホスティング・実行環境
- **フロントエンド**: Netlify（`public/` フォルダを静的配信）
- **バックエンド**: GitHub Actions（毎時UTC0分に `python3 main.py` を実行）
- **DB**: Supabase（PostgreSQL）

## データソース
| データ | ソース | 更新頻度 | 保存 |
|--------|--------|---------|------|
| 船舶 | AISstream.io WebSocket（300秒収集） | 毎時 | Supabase 48時間 |
| 火災 | NASA FIRMS VIIRS（200MW以上） | 毎時（衛星は1日1〜2回） | Supabase 48時間 |
| 紛争イベント | GDELT 2.0（CAMEO 18/19/20、過去1時間分4ファイル） | 毎時 | Supabase 48時間 |
| 地域統計 | 上記の集計 | 毎時 | Supabase 無期限 |
| 時系列 | history.json（7日分168エントリ） | 毎時 | ローカルファイル |

## ファイル構成
- `main.py` — メイン処理（取得→分析→保存→レポート生成）
- `fetch.py` — データ取得（AISstream/FIRMS/GDELT）
- `analyze.py` — 分析（船舶・火災・イベントの件数集計）
- `report.py` — HTML生成（Leaflet地図・Chart.js・カード）
- `history_store.py` — history.jsonの読み書き・トレンド計算
- `supabase_store.py` — Supabaseへの保存・削除
- `config.py` — 監視エリア15地域の定義

## 監視エリア（config.py）
中東5（紅海・ホルムズ・東地中海・ペルシャ湾・スエズ）、ロシア・ウクライナ2（ウクライナ東部・黒海）、東アジア3（台湾海峡・南シナ海・朝鮮半島）、東南アジア1（マラッカ）、主要航路4（アデン湾・インド洋・ベンガル湾・西地中海）

## Supabaseテーブル
- `ships`: mmsi, lat, lon, name, flag, ship_type, type_label, sog, nav_status, destination, captured_at
- `fires`: lat, lon, frp, confidence, acq_date, acq_time, daynight, captured_at
- `events`: lat, lon, event_code, event_root, goldstein, num_articles, avg_tone, actor1, actor2, location, captured_at
- `region_stats`: region_id, aircraft_count, ship_count, tanker_count, military_count, anchored_count, fire_count, high_conf_fire_count, intense_fire_count, total_frp, event_count, captured_at
- `ship_timestamps`（ビュー）: タイムスライダー用のタイムスタンプ一覧

## 主な表示機能
- **地図**: Leaflet.js + Canvasレンダラー。船舶（種別で色分け）・火災（強度グラデーション200〜1000MW）・GDELTイベント（種別で赤/オレンジ/紫）をトグルボタンでオンオフ
- **タイムスライダー**: Supabaseから過去48時間の船舶・火災データを取得して地図を更新
- **グラフ**: 船舶・火災・紛争の全地域合計件数の7日間推移（Chart.js）
- **カード**: 地域ごとに船舶・火災・紛争の現在件数 + 7日平均比 + 24h比を表示

## 設計上の判断
- **スコア廃止**: 複合スコアは根拠が不明確なため、指標別の変化率（7日比・24h比）に変更
- **航空機データ廃止**: OpenSkyは軍用機が映らず実用性が低いと判断
- **火災フィルター**: 200MW以上（農業焼き畑などのノイズを除去）
- **火災引き継ぎ**: 衛星フィンガープリントで未更新時は前回値を使用（グラフ安定化）
- **GDELT**: 過去1時間分（4ファイル）を取得してGLOBALEVENTIDで重複除去
- **火災・GDELT全世界表示**: 地図は全世界、カードの増減比較はエリア限定
