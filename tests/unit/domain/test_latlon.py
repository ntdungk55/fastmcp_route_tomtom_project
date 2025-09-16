import pytest
from app.domain.value_objects.latlon import LatLon
from app.domain.errors import InvalidCoordinateError


class TestLatLon:
    def test_valid_coordinates(self):
        """Test valid latitude and longitude."""
        latlon = LatLon(lat=45.0, lon=90.0)
        assert latlon.lat == 45.0
        assert latlon.lon == 90.0

    def test_invalid_latitude_too_high(self):
        """Test latitude above 90 degrees."""
        with pytest.raises(InvalidCoordinateError, match="Invalid latitude: 91.0"):
            LatLon(lat=91.0, lon=0.0)

    def test_invalid_latitude_too_low(self):
        """Test latitude below -90 degrees."""
        with pytest.raises(InvalidCoordinateError, match="Invalid latitude: -91.0"):
            LatLon(lat=-91.0, lon=0.0)

    def test_invalid_longitude_too_high(self):
        """Test longitude above 180 degrees."""
        with pytest.raises(InvalidCoordinateError, match="Invalid longitude: 181.0"):
            LatLon(lat=0.0, lon=181.0)

    def test_invalid_longitude_too_low(self):
        """Test longitude below -180 degrees."""
        with pytest.raises(InvalidCoordinateError, match="Invalid longitude: -181.0"):
            LatLon(lat=0.0, lon=-181.0)

    def test_boundary_coordinates(self):
        """Test boundary values."""
        # Should not raise
        LatLon(lat=90.0, lon=180.0)
        LatLon(lat=-90.0, lon=-180.0)
        LatLon(lat=0.0, lon=0.0)
