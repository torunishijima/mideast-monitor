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
    直近24時間のベースラインと現在値を比較してトレンドスコアを計算
    - baseline: 直近24件の平均スコア
    - trend_score: 現在値がベースラインより何%上昇しているか
    - is_surge: トレンドスコアが50%以上 = 急上昇フラグ
    """
    recent = history['entries'][-24:] if len(history['entries']) >= 2 else []
    trend = {}

    for rid in results:
        current = results[rid]['anomaly_score']
        if recent:
            baseline = sum(
                e['regions'].get(rid, {}).get('anomaly_score', 0)
                for e in recent
            ) / len(recent)
        else:
            baseline = current

        if baseline > 1:
            change_pct = (current - baseline) / baseline * 100
        else:
            change_pct = 0

        trend[rid] = {
            'current':    current,
            'baseline':   round(baseline, 1),
            'change_pct': round(change_pct, 1),
            'is_surge':   change_pct >= 50,
        }

    return trend
