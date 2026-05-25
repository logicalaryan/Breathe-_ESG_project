"""
DEFRA 2023 GHG Conversion Factors for Corporate Travel Emissions.

Source: UK Department for Environment, Food & Rural Affairs (DEFRA)
        "Greenhouse Gas Reporting: Conversion Factors 2023"
        https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023

All values are in kg CO2 equivalent (CO2e) per unit.
Aviation factors include the Radiative Forcing Index (RFI) uplift.
"""

# =============================================================================
# FLIGHT EMISSION FACTORS — kg CO2e per passenger-km
# Source: DEFRA 2023, Business Travel – Air
# =============================================================================
FLIGHT_FACTORS = {
    # Short-haul: < 1,500 km (domestic & short international routes)
    "short_haul": {
        "economy":         0.25506,
        "premium_economy": 0.25506,  # No DEFRA distinction for short-haul premium
        "business":        0.38258,  # 1.5x economy (wider seats = more weight per pax)
        "first":           0.38258,  # Same as business for short-haul
    },
    # Long-haul: >= 1,500 km (intercontinental routes)
    "long_haul": {
        "economy":         0.19499,
        "premium_economy": 0.28641,  # 1.47x economy
        "business":        0.42869,  # 2.20x economy
        "first":           0.75109,  # 3.85x economy
    },
}

# km threshold that separates short-haul from long-haul
SHORT_HAUL_MAX_KM = 1500

# Normalise free-text ticket class strings to canonical keys
TICKET_CLASS_ALIASES = {
    "economy":         "economy",
    "eco":             "economy",
    "y":               "economy",
    "coach":           "economy",
    "premium economy": "premium_economy",
    "premium_economy": "premium_economy",
    "premium":         "premium_economy",
    "w":               "premium_economy",
    "business":        "business",
    "business class":  "business",
    "bus":             "business",
    "c":               "business",
    "j":               "business",
    "first":           "first",
    "first class":     "first",
    "f":               "first",
}

# =============================================================================
# HOTEL EMISSION FACTORS — kg CO2e per room-night
# Source: DEFRA 2023, Business Travel – Hotels
# Reflects average hotel energy consumption adjusted for regional grid intensity.
# =============================================================================
HOTEL_FACTORS = {
    "uk":            20.8,
    "europe":        16.5,
    "north_america": 31.2,
    "asia":          15.6,
    "middle_east":   24.5,
    "africa":        22.1,
    "latin_america": 14.3,
    "oceania":       28.9,
    "default":       26.4,   # Global average — used when country is unrecognised
}

# Map lowercase country names → hotel region key
COUNTRY_TO_HOTEL_REGION = {
    # United Kingdom
    "uk": "uk", "united kingdom": "uk", "great britain": "uk",
    "england": "uk", "scotland": "uk", "wales": "uk", "northern ireland": "uk",
    # Europe
    "france": "europe", "germany": "europe", "italy": "europe",
    "spain": "europe", "netherlands": "europe", "belgium": "europe",
    "sweden": "europe", "norway": "europe", "denmark": "europe",
    "finland": "europe", "switzerland": "europe", "austria": "europe",
    "portugal": "europe", "poland": "europe", "czech republic": "europe",
    "czechia": "europe", "hungary": "europe", "romania": "europe",
    "bulgaria": "europe", "greece": "europe", "ireland": "europe",
    "luxembourg": "europe", "croatia": "europe", "slovakia": "europe",
    "slovenia": "europe", "estonia": "europe", "latvia": "europe",
    "lithuania": "europe", "malta": "europe", "cyprus": "europe",
    # North America
    "usa": "north_america", "united states": "north_america",
    "us": "north_america", "canada": "north_america", "mexico": "north_america",
    # Asia
    "china": "asia", "japan": "asia", "india": "asia", "singapore": "asia",
    "south korea": "asia", "korea": "asia", "thailand": "asia",
    "malaysia": "asia", "indonesia": "asia", "vietnam": "asia",
    "philippines": "asia", "taiwan": "asia", "hong kong": "asia",
    "bangladesh": "asia", "pakistan": "asia", "sri lanka": "asia",
    "nepal": "asia", "cambodia": "asia", "myanmar": "asia",
    # Middle East
    "uae": "middle_east", "united arab emirates": "middle_east",
    "saudi arabia": "middle_east", "qatar": "middle_east",
    "kuwait": "middle_east", "bahrain": "middle_east", "oman": "middle_east",
    "jordan": "middle_east", "israel": "middle_east", "egypt": "middle_east",
    "turkey": "middle_east",
    # Africa
    "south africa": "africa", "nigeria": "africa", "kenya": "africa",
    "ethiopia": "africa", "ghana": "africa", "tanzania": "africa",
    # Latin America
    "brazil": "latin_america", "argentina": "latin_america",
    "colombia": "latin_america", "chile": "latin_america",
    "peru": "latin_america", "venezuela": "latin_america",
    # Oceania
    "australia": "oceania", "new zealand": "oceania",
}

# =============================================================================
# GROUND TRANSPORT EMISSION FACTORS — kg CO2e per passenger-km
# Source: DEFRA 2023, Business Travel – Land
# =============================================================================
GROUND_FACTORS = {
    "taxi":       0.14887,   # Average taxi / rideshare (petrol/diesel)
    "rental_car": 0.19211,   # Average petrol rental car (medium size)
    "train":      0.03548,   # UK average train (all traction types)
    "bus":        0.02735,   # Average local bus / coach
    "ev":         0.05302,   # Battery electric vehicle (UK grid average)
    "default":    0.14887,   # Fallback — same as taxi
}

# Normalise vendor name keywords → transport type key
VENDOR_TO_TRANSPORT_TYPE = {
    # Rideshare / Taxi
    "uber":          "taxi",
    "lyft":          "taxi",
    "bolt":          "taxi",
    "ola":           "taxi",
    "grab":          "taxi",
    "gett":          "taxi",
    "addison lee":   "taxi",
    "black cab":     "taxi",
    "taxi":          "taxi",
    "cab":           "taxi",
    # Rental car
    "hertz":         "rental_car",
    "avis":          "rental_car",
    "enterprise":    "rental_car",
    "budget":        "rental_car",
    "national":      "rental_car",
    "europcar":      "rental_car",
    "sixt":          "rental_car",
    "thrifty":       "rental_car",
    "dollar":        "rental_car",
    "alamo":         "rental_car",
    "rental":        "rental_car",
    # Train / Rail
    "national rail": "train",
    "trainline":     "train",
    "amtrak":        "train",
    "eurostar":      "train",
    "deutsche bahn": "train",
    "sncf":          "train",
    "renfe":         "train",
    "trenitalia":    "train",
    "thalys":        "train",
    "avlo":          "train",
    "thameslink":    "train",
    "gwr":           "train",
    "lner":          "train",
    "tfl rail":      "train",
    "crossrail":     "train",
    "rail":          "train",
    "train":         "train",
    # Bus / Coach
    "national express": "bus",
    "flixbus":          "bus",
    "greyhound":        "bus",
    "megabus":          "bus",
    "coach":            "bus",
    "bus":              "bus",
    # Electric vehicle
    "tesla":            "ev",
    "zipcar electric":  "ev",
    "electric":         "ev",
}
