"""
Static IATA Airport Code → (latitude, longitude) lookup table.

Covers ~120 major airports used in corporate business travel worldwide.
Coordinates are WGS84 decimal degrees.

Source: IATA Airport Database (public domain) / OurAirports dataset.
Used by the Haversine distance calculator to resolve flight distances
when origin/destination are given as airport codes rather than km values.
"""

# IATA_CODE: (latitude_decimal, longitude_decimal)
AIRPORT_COORDINATES = {
    # ── United Kingdom ─────────────────────────────────────────────────────
    "LHR": (51.4700,  -0.4543),   # London Heathrow
    "LGW": (51.1481,  -0.1903),   # London Gatwick
    "LCY": (51.5048,  -0.0495),   # London City
    "STN": (51.8850,   0.2350),   # London Stansted
    "MAN": (53.3537,  -2.2750),   # Manchester
    "BHX": (52.4539,  -1.7480),   # Birmingham
    "EDI": (55.9500,  -3.3725),   # Edinburgh
    "GLA": (55.8642,  -4.4331),   # Glasgow
    "BRS": (51.3827,  -2.7191),   # Bristol
    "NCL": (55.0375,  -1.6917),   # Newcastle
    # ── Europe ─────────────────────────────────────────────────────────────
    "CDG": (49.0097,   2.5478),   # Paris Charles de Gaulle
    "ORY": (48.7233,   2.3794),   # Paris Orly
    "AMS": (52.3086,   4.7639),   # Amsterdam Schiphol
    "FRA": (50.0333,   8.5706),   # Frankfurt
    "MUC": (48.3538,  11.7861),   # Munich
    "ZRH": (47.4647,   8.5492),   # Zurich
    "MAD": (40.4936,  -3.5668),   # Madrid Barajas
    "BCN": (41.2971,   2.0785),   # Barcelona
    "FCO": (41.8003,  12.2389),   # Rome Fiumicino
    "MXP": (45.6306,   8.7281),   # Milan Malpensa
    "VIE": (48.1103,  16.5697),   # Vienna
    "BRU": (50.9010,   4.4844),   # Brussels
    "CPH": (55.6181,  12.6561),   # Copenhagen
    "OSL": (60.1939,  11.1004),   # Oslo Gardermoen
    "ARN": (59.6519,  17.9186),   # Stockholm Arlanda
    "HEL": (60.3172,  24.9633),   # Helsinki
    "DUB": (53.4213,  -6.2700),   # Dublin
    "LIS": (38.7813,  -9.1359),   # Lisbon
    "WAW": (52.1657,  20.9671),   # Warsaw
    "PRG": (50.1008,  14.2600),   # Prague
    "BUD": (47.4298,  19.2611),   # Budapest
    "ATH": (37.9364,  23.9445),   # Athens
    "IST": (41.2753,  28.7519),   # Istanbul
    "OTP": (44.5711,  26.0850),   # Bucharest
    # ── North America ──────────────────────────────────────────────────────
    "JFK": (40.6413, -73.7781),   # New York JFK
    "EWR": (40.6895, -74.1745),   # Newark
    "LGA": (40.7772, -73.8726),   # New York LaGuardia
    "ORD": (41.9742, -87.9073),   # Chicago O'Hare
    "LAX": (33.9425,-118.4081),   # Los Angeles
    "SFO": (37.6213,-122.3790),   # San Francisco
    "SEA": (47.4502,-122.3088),   # Seattle
    "DFW": (32.8998, -97.0403),   # Dallas/Fort Worth
    "IAH": (29.9902, -95.3368),   # Houston
    "MIA": (25.7959, -80.2870),   # Miami
    "ATL": (33.6407, -84.4277),   # Atlanta
    "BOS": (42.3656, -71.0096),   # Boston
    "DCA": (38.8521, -77.0377),   # Washington Reagan
    "IAD": (38.9531, -77.4565),   # Washington Dulles
    "YYZ": (43.6777, -79.6248),   # Toronto Pearson
    "YVR": (49.1967,-123.1815),   # Vancouver
    "MEX": (19.4363, -99.0721),   # Mexico City
    # ── South America ──────────────────────────────────────────────────────
    "GRU": (-23.4356, -46.4731),  # São Paulo Guarulhos
    "EZE": (-34.8222, -58.5358),  # Buenos Aires
    "BOG": (  4.7016, -74.1469),  # Bogotá
    "SCL": (-33.3930, -70.7858),  # Santiago
    "LIM": (-12.0219, -77.1143),  # Lima
    # ── Middle East ────────────────────────────────────────────────────────
    "DXB": (25.2532,  55.3657),   # Dubai
    "AUH": (24.4330,  54.6511),   # Abu Dhabi
    "DOH": (25.2731,  51.6082),   # Doha
    "RUH": (24.9576,  46.6988),   # Riyadh
    "KWI": (29.2267,  47.9689),   # Kuwait City
    "BAH": (26.2708,  50.6336),   # Bahrain
    "AMM": (31.7226,  35.9932),   # Amman
    "TLV": (32.0055,  34.8854),   # Tel Aviv
    "CAI": (30.1219,  31.4056),   # Cairo
    # ── Africa ─────────────────────────────────────────────────────────────
    "JNB": (-26.1392,  28.2460),  # Johannesburg O.R. Tambo
    "CPT": (-33.9648,  18.6017),  # Cape Town
    "NBO": ( -1.3192,  36.9275),  # Nairobi
    "LOS": (  6.5774,   3.3214),  # Lagos
    "ADD": (  8.9778,  38.7993),  # Addis Ababa
    "ACC": (  5.6052,  -0.1668),  # Accra
    # ── South Asia ─────────────────────────────────────────────────────────
    "DEL": (28.5665,  77.1031),   # Delhi Indira Gandhi
    "BOM": (19.0896,  72.8656),   # Mumbai
    "BLR": (13.1986,  77.7066),   # Bangalore
    "MAA": (12.9900,  80.1693),   # Chennai
    "CCU": (22.6547,  88.4467),   # Kolkata
    "HYD": (17.2403,  78.4294),   # Hyderabad
    "CMB": ( 7.1808,  79.8841),   # Colombo
    "KTM": (27.6966,  85.3591),   # Kathmandu
    "DAC": (23.8433,  90.3978),   # Dhaka
    "KHI": (24.9065,  67.1608),   # Karachi
    "LHE": (31.5216,  74.4036),   # Lahore
    # ── Southeast Asia ─────────────────────────────────────────────────────
    "SIN": ( 1.3644, 103.9915),   # Singapore Changi
    "KUL": ( 2.7456, 101.7099),   # Kuala Lumpur
    "BKK": (13.9132, 100.6067),   # Bangkok Suvarnabhumi
    "CGK": (-6.1255, 106.6559),   # Jakarta
    "MNL": (14.5086, 121.0194),   # Manila
    "SGN": (10.8188, 106.6519),   # Ho Chi Minh City
    "HAN": (21.2212, 105.8072),   # Hanoi
    "RGN": (16.9073,  96.1332),   # Yangon
    # ── East Asia ──────────────────────────────────────────────────────────
    "PEK": (40.0799, 116.6031),   # Beijing Capital
    "PKX": (39.5095, 116.4105),   # Beijing Daxing
    "PVG": (31.1443, 121.8083),   # Shanghai Pudong
    "SHA": (31.1979, 121.3364),   # Shanghai Hongqiao
    "CAN": (23.3924, 113.2988),   # Guangzhou
    "SZX": (22.6393, 113.8107),   # Shenzhen
    "CTU": (30.5785, 103.9467),   # Chengdu
    "HKG": (22.3080, 113.9185),   # Hong Kong
    "TPE": (25.0777, 121.2326),   # Taipei Taoyuan
    "ICN": (37.4602, 126.4407),   # Seoul Incheon
    "NRT": (35.7647, 140.3864),   # Tokyo Narita
    "HND": (35.5494, 139.7798),   # Tokyo Haneda
    "KIX": (34.4347, 135.2440),   # Osaka Kansai
    # ── Oceania ────────────────────────────────────────────────────────────
    "SYD": (-33.9399, 151.1753),  # Sydney
    "MEL": (-37.6690, 144.8410),  # Melbourne
    "BNE": (-27.3842, 153.1175),  # Brisbane
    "PER": (-31.9385, 115.9672),  # Perth
    "AKL": (-37.0082, 174.7917),  # Auckland
}
