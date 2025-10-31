from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidWindSpeedError(DomainError):
    """Raised when wind speed value is invalid."""
    pass


@dataclass(frozen=True)
class WindSpeed:
    """Value object for wind speed with validation."""
    value: float  # Wind speed in m/s
    units: str = "metric"  # "metric" (m/s) or "imperial" (mph)
    
    def __post_init__(self) -> None:
        """Validate wind speed value."""
        valid_units = ["metric", "imperial"]
        if self.units not in valid_units:
            raise InvalidWindSpeedError(
                f"Invalid wind speed units: {self.units}. Must be one of: {valid_units}",
                entity_id="wind_speed",
                field="units",
                value=self.units
            )
        
        # Validate speed range (reasonable weather wind speeds)
        # Max recorded wind speed ~400 km/h = 111 m/s
        max_speed_mps = 150.0  # Allow some buffer
        
        if self.value < 0:
            raise InvalidWindSpeedError(
                f"Wind speed cannot be negative: {self.value}",
                entity_id="wind_speed",
                field="value",
                value=self.value
            )
        
        if self.units == "metric":  # m/s
            if self.value > max_speed_mps:
                raise InvalidWindSpeedError(
                    f"Wind speed seems unreasonably high: {self.value} m/s",
                    entity_id="wind_speed",
                    field="value",
                    value=self.value
                )
        elif self.units == "imperial":  # mph
            max_speed_mph = max_speed_mps * 2.237
            if self.value > max_speed_mph:
                raise InvalidWindSpeedError(
                    f"Wind speed seems unreasonably high: {self.value} mph",
                    entity_id="wind_speed",
                    field="value",
                    value=self.value
                )
    
    def to_mps(self) -> float:
        """Convert wind speed to meters per second."""
        if self.units == "metric":
            return self.value
        elif self.units == "imperial":
            return self.value * 0.44704  # mph to m/s
        return self.value
    
    def to_mph(self) -> float:
        """Convert wind speed to miles per hour."""
        if self.units == "imperial":
            return self.value
        elif self.units == "metric":
            return self.value * 2.237  # m/s to mph
        return self.value
    
    def to_kmh(self) -> float:
        """Convert wind speed to kilometers per hour."""
        mps = self.to_mps()
        return mps * 3.6
    
    def __str__(self) -> str:
        """String representation with unit."""
        if self.units == "metric":
            return f"{self.value:.1f} m/s"
        elif self.units == "imperial":
            return f"{self.value:.1f} mph"
        return str(self.value)
    
    def __eq__(self, other) -> bool:
        """Equality comparison (compare in same units)."""
        if not isinstance(other, WindSpeed):
            return False
        # Convert both to m/s for comparison
        return abs(self.to_mps() - other.to_mps()) < 0.1



