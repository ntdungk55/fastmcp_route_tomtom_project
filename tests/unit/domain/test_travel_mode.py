from app.domain.enums.travel_mode import TravelMode


class TestTravelMode:
    def test_valid_modes(self):
        """Test all valid travel modes."""
        assert TravelMode.CAR == "car"
        assert TravelMode.BICYCLE == "bicycle"
        assert TravelMode.FOOT == "foot"

    def test_enum_values(self):
        """Test enum can be created from string values."""
        assert TravelMode("car") == TravelMode.CAR
        assert TravelMode("bicycle") == TravelMode.BICYCLE
        assert TravelMode("foot") == TravelMode.FOOT

    def test_string_representation(self):
        """Test string representation."""
        assert str(TravelMode.CAR) == "TravelMode.CAR"
        assert str(TravelMode.BICYCLE) == "TravelMode.BICYCLE"
        assert str(TravelMode.FOOT) == "TravelMode.FOOT"
