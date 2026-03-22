"""時系列データの管理モジュール"""
import json
import os
from datetime import datetime

HISTORY_PATH = 'public/data/history.json'
MAX_ENTRIES  = 168  # 7日分（24時間 × 7）


def load():
    """既存の履歴を読み込む"""
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'entries': []}


def append(history, timestamp, results):
    """新しいエントリを追加して古いものを削除"""
    entry = {
        'timestamp': timestamp,
        'regions': {
            rid: {
                'anomaly_score': data['anomaly_score'],
                'ship_score':    data.get('ship_score', 0),
                'fire_score':    data.get('fire_score', 0),
                'event_score':   data.get('event_score', 0),
                'ship_count':    data['ships']['count'],
                'fire_count':    data['fires']['count'],
                'event_count':   data['events']['count'],
            }
            for rid, data in results.items()
        },
    }
    history['entries'].append(entry)
    # 古いエントリを削除（最大件数を超えた分）
    if len(history['entries']) > MAX_ENTRIES:
        history['entries'] = history['entries'][-MAX_ENTRIES:]
    return history


def save(history):
    """履歴をファイルに保存"""
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, separators=(',', ':'))


def calc_trend_scores(history, results):
    """
    指標ごとに7日平均比・24時間前比を計算する
    - week_pct: 過去7日平均（168件）との比較
    - day_pct:  24時間前（24件前のエントリ）との比較
    - is_surge: いずれかの指標で24h比が50%以上変化
    """
    entries     = history['entries']
    week_entries = entries[-168:] if entries else []
    day_ago      = entries[-24] if len(entries) >= 24 else None

    trend = {}
    for rid in results:
        data    = results[rid]
        current = {
            'ships':  data['ships']['count'],
            'fires':  data['fires']['count'],
            'events': data['events']['count'],
        }
        is_surge   = False
        indicators = {}

        for key in ('ships', 'fires', 'events'):
            hist_key = {'ships': 'ship_count', 'fires': 'fire_count', 'events': 'event_count'}[key]
            cur      = current[key]

            # 7日平均比
            if week_entries:
                week_avg = sum(e['regions'].get(rid, {}).get(hist_key, 0) for e in week_entries) / len(week_entries)
                week_pct = round((cur - week_avg) / week_avg * 100, 1) if week_avg > 0.5 else 0
            else:
                week_avg, week_pct = cur, 0

            # 24時間前比
            if day_ago:
                day_val = day_ago['regions'].get(rid, {}).get(hist_key, 0)
                day_pct = round((cur - day_val) / day_val * 100, 1) if day_val > 0.5 else 0
            else:
                day_val, day_pct = cur, 0

            if abs(day_pct) >= 50:
                is_surge = True

            indicators[key] = {
                'current':  cur,
                'week_avg': round(week_avg, 1),
                'week_pct': week_pct,
                'day_val':  day_val if day_ago else cur,
                'day_pct':  day_pct,
            }

        trend[rid] = {**indicators, 'is_surge': is_surge}

    return trend
