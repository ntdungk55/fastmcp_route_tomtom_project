"""
API Constants cho toàn bộ application.
Thuộc Domain layer - core business constants.
"""
from typing import Dict, List


class TravelModeConstants:
    """Constants cho travel modes."""
    CAR = "car"
    BICYCLE = "bicycle"
    FOOT = "foot"
    MOTORCYCLE = "motorcycle"
    
    # Mapping từ domain travel mode sang TomTom API values
    TOMTOM_MAPPING = {
        CAR: "car",
        BICYCLE: "bicycle", 
        FOOT: "pedestrian",
        MOTORCYCLE: "motorcycle"
    }
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Lấy tất cả travel mode values."""
        return [cls.CAR, cls.BICYCLE, cls.FOOT, cls.MOTORCYCLE]
    
    @classmethod
    def get_tomtom_value(cls, domain_value: str) -> str:
        """Convert domain travel mode sang TomTom API value."""
        return cls.TOMTOM_MAPPING.get(domain_value, cls.CAR)


class RouteTypeConstants:
    """Constants cho route types."""
    FASTEST = "fastest"
    SHORTEST = "shortest"
    ECO = "eco"
    THRILLING = "thrilling"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Lấy tất cả route type values."""
        return [cls.FASTEST, cls.SHORTEST, cls.ECO, cls.THRILLING]


class LanguageConstants:
    """Constants cho languages."""
    VIETNAMESE = "vi-VN"
    ENGLISH = "en-US"
    ENGLISH_GB = "en-GB"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    
    DEFAULT = VIETNAMESE
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Lấy tất cả language values."""
        return [
            cls.VIETNAMESE, cls.ENGLISH, cls.ENGLISH_GB,
            cls.FRENCH, cls.GERMAN, cls.JAPANESE,
            cls.KOREAN, cls.CHINESE_SIMPLIFIED, cls.CHINESE_TRADITIONAL
        ]
    
    @classmethod
    def is_valid(cls, language: str) -> bool:
        """Kiểm tra language có hợp lệ không."""
        return language in cls.get_all_values()


class CountryConstants:
    """Constants cho country codes."""
    VIETNAM = "VN"
    USA = "US"
    UNITED_KINGDOM = "GB"
    FRANCE = "FR"
    GERMANY = "DE"
    JAPAN = "JP"
    KOREA = "KR"
    CHINA = "CN"
    SINGAPORE = "SG"
    THAILAND = "TH"
    MALAYSIA = "MY"
    INDONESIA = "ID"
    PHILIPPINES = "PH"
    
    DEFAULT = VIETNAM
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Lấy tất cả country code values."""
        return [
            cls.VIETNAM, cls.USA, cls.UNITED_KINGDOM,
            cls.FRANCE, cls.GERMANY, cls.JAPAN,
            cls.KOREA, cls.CHINA, cls.SINGAPORE,
            cls.THAILAND, cls.MALAYSIA, cls.INDONESIA, cls.PHILIPPINES
        ]


class LimitConstants:
    """Constants cho các giới hạn API."""
    DEFAULT_GEOCODING_LIMIT = 1
    MAX_GEOCODING_LIMIT = 100
    MIN_GEOCODING_LIMIT = 1
    
    DEFAULT_ROUTE_ALTERNATIVES = 1
    MAX_ROUTE_ALTERNATIVES = 5
    MIN_ROUTE_ALTERNATIVES = 1
    
    DEFAULT_TRAFFIC_ZOOM = 10
    MIN_TRAFFIC_ZOOM = 0
    MAX_TRAFFIC_ZOOM = 22


class CoordinateConstants:
    """Constants cho coordinate validation."""
    MIN_LATITUDE = -90.0
    MAX_LATITUDE = 90.0
    MIN_LONGITUDE = -180.0
    MAX_LONGITUDE = 180.0
    
    # Vietnam bounding box
    VIETNAM_MIN_LAT = 8.0
    VIETNAM_MAX_LAT = 24.0
    VIETNAM_MIN_LON = 102.0
    VIETNAM_MAX_LON = 110.0
