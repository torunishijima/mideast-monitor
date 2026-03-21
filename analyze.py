"""分析モジュール: 船舶・火災データから異常スコアを計算"""
from collections import Counter


def analyze(ship_list=None, fire_list=None):
    """
    異常スコア（0〜100）の計算:
    - タンカー・軍用船が多い     → スコア上昇
    - 錨泊船が多い（通過回避）   → スコア上昇
    - 高強度火災（FRP高い）が多い → スコア上昇
    """
    ship_list = ship_list or []
    fire_list = fire_list or []

    ship_result = _analyze_ships(ship_list)
    fire_result = _analyze_fires(fire_list)

    # 複合スコア（船舶・火災を均等に）
    s_score  = ship_result['anomaly_score']
    f_score  = fire_result['anomaly_score']
    combined = min(round(s_score * 0.5 + f_score * 0.5, 1), 100.0)

    return {
        'ships':        ship_result,
        'fires':        fire_result,
        'anomaly_score': combined,
        'ship_score':   s_score,
        'fire_score':   f_score,
    }



def _analyze_ships(ship_list):
    if not ship_list:
        return _empty_ships()

    flags        = Counter()
    tankers      = []
    military     = []
    anchored     = []
    destinations = Counter()

    for s in ship_list:
        flag = s.get('flag') or s.get('country', 'Unknown')
        flags[flag] += 1

        ship_type = s.get('ship_type', 0)
        # タンカー（80-89）
        if 80 <= ship_type <= 89:
            tankers.append(s)
        # 軍用（35）
        if ship_type == 35:
            military.append(s)
        # 錨泊中
        if s.get('nav_status') == '錨泊中':
            anchored.append(s)

        dest = s.get('destination', '').strip()
        if dest:
            destinations[dest] += 1

    total = len(ship_list)
    score = 0.0
    score += (len(tankers)  / total) * 30
    score += (len(military) / total) * 40
    score += (len(anchored) / total) * 20
    score += min(len(military) * 10, 10)

    return {
        'count':        total,
        'tankers':      len(tankers),
        'military':     len(military),
        'anchored':     len(anchored),
        'flags':        dict(flags.most_common(10)),
        'destinations': dict(destinations.most_common(5)),
        'anomaly_score': min(round(score, 1), 100.0),
        'ships':        ship_list,
    }


def _empty_ships():
    return {
        'count': 0, 'tankers': 0, 'military': 0, 'anchored': 0,
        'flags': {}, 'destinations': {}, 'anomaly_score': 0.0, 'ships': [],
    }


def _analyze_fires(fire_list):
    if not fire_list:
        return _empty_fires()

    # 高信頼度の火災のみ（low は除外）
    high_conf = [f for f in fire_list if f.get('confidence', '').lower() != 'low']
    # 高強度火災（FRP 50MW以上）
    intense   = [f for f in high_conf if f.get('frp', 0) >= 50]
    total_frp = sum(f.get('frp', 0) for f in high_conf)

    # スコア: 高信頼度の件数と強度で計算
    score = 0.0
    score += min(len(high_conf) * 2, 40)   # 件数（最大40点）
    score += min(len(intense) * 5, 40)      # 高強度（最大40点）
    score += min(total_frp / 500, 20)       # 総強度（最大20点）

    return {
        'count':      len(fire_list),
        'high_conf':  len(high_conf),
        'intense':    len(intense),
        'total_frp':  round(total_frp, 1),
        'anomaly_score': min(round(score, 1), 100.0),
        'fires':      fire_list,
    }


def _empty_fires():
    return {
        'count': 0, 'high_conf': 0, 'intense': 0,
        'total_frp': 0.0, 'anomaly_score': 0.0, 'fires': [],
    }
