"""分析モジュール: 船舶・火災・紛争データを集計する"""
from collections import Counter


def analyze(ship_list=None, fire_list=None, event_list=None):
    ship_list  = ship_list  or []
    fire_list  = fire_list  or []
    event_list = event_list or []

    return {
        'ships':  _analyze_ships(ship_list),
        'fires':  _analyze_fires(fire_list),
        'events': _analyze_events(event_list),
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
    return {
        'count':        total,
        'tankers':      len(tankers),
        'military':     len(military),
        'anchored':     len(anchored),
        'flags':        dict(flags.most_common(10)),
        'destinations': dict(destinations.most_common(5)),
        'ships':        ship_list,
    }


def _empty_ships():
    return {
        'count': 0, 'tankers': 0, 'military': 0, 'anchored': 0,
        'flags': {}, 'destinations': {}, 'ships': [],
    }


def _analyze_fires(fire_list):
    if not fire_list:
        return _empty_fires()

    # 高信頼度の火災のみ（low は除外）
    high_conf = [f for f in fire_list if f.get('confidence', '').lower() != 'low']
    # 超大規模火災（FRP 1000MW以上）
    intense   = [f for f in high_conf if f.get('frp', 0) >= 1000]
    total_frp = sum(f.get('frp', 0) for f in high_conf)

    return {
        'count':      len(fire_list),
        'high_conf':  len(high_conf),
        'intense':    len(intense),
        'total_frp':  round(total_frp, 1),
        'fires':      fire_list,
    }


def _empty_fires():
    return {
        'count': 0, 'high_conf': 0, 'intense': 0,
        'total_frp': 0.0, 'fires': [],
    }


def _analyze_events(event_list):
    if not event_list:
        return _empty_events()

    total          = len(event_list)
    avg_goldstein  = sum(e.get('goldstein', 0) for e in event_list) / total
    total_articles = sum(e.get('num_articles', 0) for e in event_list)

    return {
        'count':          total,
        'avg_goldstein':  round(avg_goldstein, 2),
        'total_articles': total_articles,
        'events':         event_list,
    }


def _empty_events():
    return {
        'count': 0, 'avg_goldstein': 0.0, 'total_articles': 0,
        'anomaly_score': 0.0, 'events': [],
    }
