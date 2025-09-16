
from dataclasses import dataclass

@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float
