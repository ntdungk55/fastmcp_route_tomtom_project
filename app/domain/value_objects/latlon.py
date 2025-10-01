
from dataclasses import dataclass

from app.domain.errors import InvalidCoordinateError


@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat <= 90):
            raise InvalidCoordinateError(
                f"Invalid latitude: {self.lat}",
                entity_id="latlon",
                field="lat",
                value=self.lat
            )
        if not (-180 <= self.lon <= 180):
            raise InvalidCoordinateError(
                f"Invalid longitude: {self.lon}",
                entity_id="latlon",
                field="lon",
                value=self.lon
            )
