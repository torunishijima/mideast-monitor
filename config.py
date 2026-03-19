# 監視対象地域
REGIONS = {
    'red_sea': {
        'name': '紅海',
        'center': [20.0, 38.0],
        'bounds': {'lamin': 12.0, 'lomin': 32.0, 'lamax': 28.0, 'lomax': 44.0},
    },
    'strait_of_hormuz': {
        'name': 'ホルムズ海峡',
        'center': [26.0, 56.5],
        'bounds': {'lamin': 24.5, 'lomin': 55.0, 'lamax': 27.5, 'lomax': 58.5},
    },
    'eastern_med': {
        'name': '東地中海（イスラエル周辺）',
        'center': [32.0, 35.5],
        'bounds': {'lamin': 29.0, 'lomin': 33.0, 'lamax': 36.0, 'lomax': 38.0},
    },
    'persian_gulf': {
        'name': 'ペルシャ湾',
        'center': [25.5, 52.0],
        'bounds': {'lamin': 23.0, 'lomin': 48.0, 'lamax': 28.0, 'lomax': 57.0},
    },
}

# 軍事・外交的に注目すべき国
NOTABLE_COUNTRIES = [
    'United States', 'United Kingdom', 'Israel', 'Iran', 'France',
    'Saudi Arabia', 'Jordan', 'United Arab Emirates', 'Russia', 'Turkey',
]

# 緊急スコークコード
EMERGENCY_SQUAWKS = {
    '7500': 'ハイジャック',
    '7600': '無線障害',
    '7700': '緊急事態',
}

# 低高度の閾値（メートル）
LOW_ALTITUDE_THRESHOLD = 3000
