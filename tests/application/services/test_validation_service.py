"""
Tests for ValidationService.
"""
import pytest
from app.application.services.validation_service import ValidationService


class TestValidationService:
    """Test cases for ValidationService."""
    
    def test_safe_float_convert_with_float(self):
        """Test converting float to float."""
        service = ValidationService()
        result = service.safe_float_convert(3.14)
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_safe_float_convert_with_int(self):
        """Test converting int to float."""
        service = ValidationService()
        result = service.safe_float_convert(42)
        assert result == 42.0
        assert isinstance(result, float)
    
    def test_safe_float_convert_with_string(self):
        """Test converting string to float."""
        service = ValidationService()
        result = service.safe_float_convert("3.14")
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_safe_float_convert_with_whitespace_string(self):
        """Test converting string with whitespace to float."""
        service = ValidationService()
        result = service.safe_float_convert("  3.14  ")
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_safe_float_convert_invalid_string(self):
        """Test converting invalid string raises ValueError."""
        service = ValidationService()
        with pytest.raises(ValueError, match="Cannot convert 'invalid' to float"):
            service.safe_float_convert("invalid")
    
    def test_safe_float_convert_none(self):
        """Test converting None raises ValueError."""
        service = ValidationService()
        with pytest.raises(ValueError):
            service.safe_float_convert(None)
    
    def test_validate_coordinates_valid(self):
        """Test validating valid coordinates."""
        service = ValidationService()
        # Should not raise exception
        service.validate_coordinates(45.0, 90.0)
        service.validate_coordinates(-45.0, -90.0)
        service.validate_coordinates(0.0, 0.0)
    
    def test_validate_coordinates_invalid_latitude(self):
        """Test validating invalid latitude."""
        service = ValidationService()
        with pytest.raises(ValueError, match="Invalid latitude: 91"):
            service.validate_coordinates(91.0, 0.0)
        
        with pytest.raises(ValueError, match="Invalid latitude: -91"):
            service.validate_coordinates(-91.0, 0.0)
    
    def test_validate_coordinates_invalid_longitude(self):
        """Test validating invalid longitude."""
        service = ValidationService()
        with pytest.raises(ValueError, match="Invalid longitude: 181"):
            service.validate_coordinates(0.0, 181.0)
        
        with pytest.raises(ValueError, match="Invalid longitude: -181"):
            service.validate_coordinates(0.0, -181.0)
    
    def test_validate_non_empty_string_valid(self):
        """Test validating valid non-empty string."""
        service = ValidationService()
        # Should not raise exception
        service.validate_non_empty_string("hello", "test_field")
        service.validate_non_empty_string("  hello  ", "test_field")
    
    def test_validate_non_empty_string_empty(self):
        """Test validating empty string."""
        service = ValidationService()
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            service.validate_non_empty_string("", "test_field")
        
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            service.validate_non_empty_string("   ", "test_field")
    
    def test_validate_non_empty_string_none(self):
        """Test validating None string."""
        service = ValidationService()
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            service.validate_non_empty_string(None, "test_field")


