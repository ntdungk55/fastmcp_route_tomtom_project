
# Routing endpoints
CALCULATE_ROUTE_PATH = "/routing/1/calculateRoute/{origin}:{destination}/json"
DEFAULT_TRAVEL_MODE = {
    "car": "car",
    "bicycle": "bicycle",
    "foot": "pedestrian",
}

# Geocoding endpoints
GEOCODE_ADDRESS_PATH = "/search/2/geocode/{address}.json"
STRUCTURED_GEOCODE_PATH = "/search/2/structuredGeocode.json"
SEARCH_STREET_PATH = "/search/2/search/{query}.json"

# Traffic endpoints
TRAFFIC_FLOW_PATH = "/traffic/services/4/flowSegmentData/absolute/{zoom}/json"
