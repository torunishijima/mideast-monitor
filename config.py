# 監視対象地域（世界の緊張・紛争地帯）
REGIONS = {
    # 中東
    'red_sea': {
        'name': '紅海',
        'center': [20.0, 38.0],
        'bounds': {'lamin': 8.0, 'lomin': 28.0, 'lamax': 30.0, 'lomax': 46.0},
    },
    'strait_of_hormuz': {
        'name': 'ホルムズ海峡',
        'center': [26.0, 56.5],
        'bounds': {'lamin': 22.0, 'lomin': 52.0, 'lamax': 30.0, 'lomax': 62.0},
    },
    'eastern_med': {
        'name': '東地中海（イスラエル周辺）',
        'center': [33.0, 35.0],
        'bounds': {'lamin': 27.0, 'lomin': 28.0, 'lamax': 38.0, 'lomax': 42.0},
    },
    'persian_gulf': {
        'name': 'ペルシャ湾',
        'center': [25.5, 52.0],
        'bounds': {'lamin': 21.0, 'lomin': 46.0, 'lamax': 30.0, 'lomax': 60.0},
    },
    'suez_canal': {
        'name': 'スエズ運河周辺',
        'center': [30.5, 32.5],
        'bounds': {'lamin': 27.0, 'lomin': 29.0, 'lamax': 33.0, 'lomax': 36.0},
    },
    # ロシア・ウクライナ
    'eastern_ukraine': {
        'name': 'ウクライナ東部',
        'center': [49.0, 36.0],
        'bounds': {'lamin': 44.0, 'lomin': 28.0, 'lamax': 54.0, 'lomax': 42.0},
    },
    'black_sea': {
        'name': '黒海',
        'center': [43.0, 34.0],
        'bounds': {'lamin': 38.0, 'lomin': 24.0, 'lamax': 48.0, 'lomax': 44.0},
    },
    # 東アジア
    'taiwan_strait': {
        'name': '台湾海峡',
        'center': [24.5, 120.0],
        'bounds': {'lamin': 20.0, 'lomin': 114.0, 'lamax': 29.0, 'lomax': 126.0},
    },
    'south_china_sea': {
        'name': '南シナ海',
        'center': [13.0, 114.0],
        'bounds': {'lamin': 2.0, 'lomin': 105.0, 'lamax': 24.0, 'lomax': 122.0},
    },
    'korean_peninsula': {
        'name': '朝鮮半島',
        'center': [37.5, 127.0],
        'bounds': {'lamin': 32.0, 'lomin': 122.0, 'lamax': 44.0, 'lomax': 132.0},
    },
    # 東南アジア
    'strait_of_malacca': {
        'name': 'マラッカ海峡',
        'center': [4.0, 102.0],
        'bounds': {'lamin': -2.0, 'lomin': 96.0, 'lamax': 10.0, 'lomax': 108.0},
    },
    # 主要航路
    'gulf_of_aden': {
        'name': 'アデン湾',
        'center': [12.0, 48.0],
        'bounds': {'lamin': 8.0, 'lomin': 42.0, 'lamax': 16.0, 'lomax': 58.0},
    },
    'indian_ocean': {
        'name': 'インド洋（主要航路）',
        'center': [12.0, 65.0],
        'bounds': {'lamin': -5.0, 'lomin': 55.0, 'lamax': 25.0, 'lomax': 78.0},
    },
    'bay_of_bengal': {
        'name': 'ベンガル湾',
        'center': [13.0, 88.0],
        'bounds': {'lamin': 5.0, 'lomin': 80.0, 'lamax': 22.0, 'lomax': 98.0},
    },
    'western_med': {
        'name': '西地中海',
        'center': [38.0, 10.0],
        'bounds': {'lamin': 30.0, 'lomin': -6.0, 'lamax': 46.0, 'lomax': 22.0},
    },
}
