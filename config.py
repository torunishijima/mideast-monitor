# 監視対象地域（世界の緊張・紛争地帯）
REGIONS = {
    # 中東
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
    'suez_canal': {
        'name': 'スエズ運河周辺',
        'center': [30.5, 32.5],
        'bounds': {'lamin': 29.0, 'lomin': 31.5, 'lamax': 32.0, 'lomax': 33.5},
    },
    # ロシア・ウクライナ
    'eastern_ukraine': {
        'name': 'ウクライナ東部',
        'center': [48.5, 37.5],
        'bounds': {'lamin': 46.0, 'lomin': 33.0, 'lamax': 51.0, 'lomax': 40.0},
    },
    'black_sea': {
        'name': '黒海',
        'center': [43.0, 34.0],
        'bounds': {'lamin': 40.5, 'lomin': 27.5, 'lamax': 46.5, 'lomax': 41.0},
    },
    # 東アジア
    'taiwan_strait': {
        'name': '台湾海峡',
        'center': [24.5, 119.5],
        'bounds': {'lamin': 22.0, 'lomin': 117.0, 'lamax': 27.0, 'lomax': 122.0},
    },
    'south_china_sea': {
        'name': '南シナ海',
        'center': [13.0, 114.0],
        'bounds': {'lamin': 5.0, 'lomin': 108.0, 'lamax': 22.0, 'lomax': 120.0},
    },
    'korean_peninsula': {
        'name': '朝鮮半島',
        'center': [37.5, 127.0],
        'bounds': {'lamin': 34.0, 'lomin': 124.0, 'lamax': 42.0, 'lomax': 130.0},
    },
    # 東南アジア
    'strait_of_malacca': {
        'name': 'マラッカ海峡',
        'center': [3.5, 101.5],
        'bounds': {'lamin': 1.0, 'lomin': 99.0, 'lamax': 6.5, 'lomax': 104.0},
    },
}

# 軍事・外交的に注目すべき国
NOTABLE_COUNTRIES = [
    'United States', 'United Kingdom', 'Israel', 'Iran', 'France',
    'Saudi Arabia', 'Jordan', 'United Arab Emirates', 'Russia', 'Turkey',
    'China', 'North Korea', 'South Korea', 'Japan', 'Taiwan',
]

# 緊急スコークコード
EMERGENCY_SQUAWKS = {
    '7500': 'ハイジャック',
    '7600': '無線障害',
    '7700': '緊急事態',
}

# 低高度の閾値（メートル）
LOW_ALTITUDE_THRESHOLD = 3000
