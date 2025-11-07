# Phân tích Coupling và Đề xuất Cải thiện Architecture

## 🔴 Vấn đề hiện tại: High Coupling

Bạn đúng - code hiện tại vẫn **highly coupled** với TomTom API. Mặc dù có Clean Architecture và Ports/Adapters pattern, nhưng vẫn có nhiều điểm coupling:

---

## 📊 Phân tích các điểm Coupling

### 1. **Hard-coded Imports** ❌
**File:** `app/di/container.py`, `app/di/providers/infrastructure_provider.py`, `app/di/factories/gateway_factory.py`

```python
# ❌ BAD: Hard-coded imports
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter
```

**Vấn đề:**
- Muốn đổi sang Google Maps → Phải sửa imports ở nhiều nơi
- Violates Dependency Inversion Principle

### 2. **Hard-coded Settings** ❌
**File:** `app/infrastructure/config/settings.py`

```python
# ❌ BAD: Settings hard-code TomTom
tomtom_base_url: str = Field(...)
tomtom_api_key: str = Field(...)
```

**Vấn đề:**
- Settings layer biết về TomTom cụ thể
- Muốn support nhiều providers → phải thêm nhiều fields

### 3. **Hard-coded Factory Class** ❌
**File:** `app/di/factories/gateway_factory.py`

```python
# ❌ BAD: Factory class hard-coded
class TomTomGatewayFactory:
    def create_routing_adapter(self, settings: Settings) -> TomTomRoutingAdapter:
        ...
```

**Vấn đề:**
- Factory class name hard-code provider name
- Muốn thêm Google Maps → phải tạo factory mới và sửa code

### 4. **Hard-coded Endpoints** ❌
**File:** `app/infrastructure/tomtom/endpoint.py`

```python
# ❌ BAD: Endpoints hard-code TomTom format
CALCULATE_ROUTE_PATH = "/routing/1/calculateRoute/{origin}:{destination}/json"
DEFAULT_TRAVEL_MODE = {
    "car": "car",
    "bicycle": "bicycle",
    "foot": "pedestrian",
}
```

**Vấn đề:**
- Endpoint format TomTom-specific
- Google Maps sẽ có format khác → cần thay đổi nhiều chỗ

### 5. **Hard-coded Mapper** ❌
**File:** `app/infrastructure/tomtom/adapters/routing_adapter.py`

```python
# ❌ BAD: Mapper hard-coded trong adapter
self._mapper = TomTomMapper()
```

**Vấn đề:**
- Adapter biết về mapper cụ thể
- Google Maps sẽ cần mapper khác → phải sửa adapter

---

## ✅ Giải pháp: Loosely Coupled Architecture

### Strategy 1: Configuration-Based Provider Selection

#### 1.1. Abstract Settings (`app/infrastructure/config/settings.py`)

```python
# ✅ GOOD: Generic settings
class MapProviderSettings(BaseModel):
    """Generic map provider settings."""
    provider_type: Literal["tomtom", "google_maps", "mapbox"] = Field(
        default_factory=lambda: os.getenv("MAP_PROVIDER", "tomtom")
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("MAP_PROVIDER_BASE_URL", "")
    )
    api_key: str = Field(
        default_factory=lambda: os.getenv("MAP_PROVIDER_API_KEY", "")
    )
    timeout_sec: int = Field(
        default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_SEC", "12")),
        ge=1, le=300
    )
```

#### 1.2. Provider Registry Pattern

```python
# ✅ GOOD: Provider registry
# app/infrastructure/maps/registry.py

from typing import Protocol, Dict, Type
from app.application.ports.routing_provider import RoutingProvider
from app.application.ports.geocoding_provider import GeocodingProvider
from app.infrastructure.config.settings import MapProviderSettings

class RoutingAdapterFactory(Protocol):
    def create(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> RoutingProvider:
        ...

class GeocodingAdapterFactory(Protocol):
    def create(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> GeocodingProvider:
        ...

class MapProviderRegistry:
    """Registry for map providers - allows switching providers via configuration."""
    
    def __init__(self):
        self._routing_factories: Dict[str, RoutingAdapterFactory] = {}
        self._geocoding_factories: Dict[str, GeocodingAdapterFactory] = {}
        self._traffic_factories: Dict[str, TrafficAdapterFactory] = {}
    
    def register_routing_provider(self, name: str, factory: RoutingAdapterFactory):
        """Register a routing provider factory."""
        self._routing_factories[name] = factory
    
    def register_geocoding_provider(self, name: str, factory: GeocodingAdapterFactory):
        """Register a geocoding provider factory."""
        self._geocoding_factories[name] = factory
    
    def get_routing_adapter(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> RoutingProvider:
        """Get routing adapter based on provider type in settings."""
        factory = self._routing_factories.get(settings.provider_type)
        if not factory:
            raise ValueError(f"Unknown map provider: {settings.provider_type}")
        return factory.create(settings, http_client)
    
    def get_geocoding_adapter(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> GeocodingProvider:
        """Get geocoding adapter based on provider type in settings."""
        factory = self._geocoding_factories.get(settings.provider_type)
        if not factory:
            raise ValueError(f"Unknown map provider: {settings.provider_type}")
        return factory.create(settings, http_client)

# Global registry instance
_map_provider_registry = MapProviderRegistry()

def get_map_provider_registry() -> MapProviderRegistry:
    return _map_provider_registry
```

#### 1.3. Provider Factories (TomTom)

```python
# ✅ GOOD: TomTom provider factory
# app/infrastructure/maps/providers/tomtom_factory.py

from app.infrastructure.maps.registry import RoutingAdapterFactory, GeocodingAdapterFactory
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.config.settings import MapProviderSettings

class TomTomRoutingAdapterFactory(RoutingAdapterFactory):
    def create(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> RoutingProvider:
        return TomTomRoutingAdapter(
            base_url=settings.base_url,
            api_key=settings.api_key,
            http=http_client,
            timeout_sec=settings.timeout_sec
        )

class TomTomGeocodingAdapterFactory(GeocodingAdapterFactory):
    def create(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> GeocodingProvider:
        return TomTomGeocodingAdapter(
            base_url=settings.base_url,
            api_key=settings.api_key,
            http=http_client,
            timeout_sec=settings.timeout_sec
        )

# Register in registry
def register_tomtom_providers():
    registry = get_map_provider_registry()
    registry.register_routing_provider("tomtom", TomTomRoutingAdapterFactory())
    registry.register_geocoding_provider("tomtom", TomTomGeocodingAdapterFactory())
```

#### 1.4. Provider Factories (Google Maps)

```python
# ✅ GOOD: Google Maps provider factory
# app/infrastructure/maps/providers/google_maps_factory.py

from app.infrastructure.maps.registry import RoutingAdapterFactory, GeocodingAdapterFactory
from app.infrastructure.google_maps.adapters.routing_adapter import GoogleMapsRoutingAdapter
from app.infrastructure.google_maps.adapters.geocoding_adapter import GoogleMapsGeocodingAdapter
from app.infrastructure.config.settings import MapProviderSettings

class GoogleMapsRoutingAdapterFactory(RoutingAdapterFactory):
    def create(self, settings: MapProviderSettings, http_client: AsyncApiClient) -> RoutingProvider:
        return GoogleMapsRoutingAdapter(
            base_url=settings.base_url,
            api_key=settings.api_key,
            http=http_client,
            timeout_sec=settings.timeout_sec
        )

# Register in registry
def register_google_maps_providers():
    registry = get_map_provider_registry()
    registry.register_routing_provider("google_maps", GoogleMapsRoutingAdapterFactory())
    registry.register_geocoding_provider("google_maps", GoogleMapsGeocodingAdapterFactory())
```

#### 1.5. Updated Container

```python
# ✅ GOOD: Container sử dụng registry
# app/di/container.py

from app.infrastructure.maps.registry import get_map_provider_registry
from app.infrastructure.maps.providers.tomtom_factory import register_tomtom_providers
from app.infrastructure.maps.providers.google_maps_factory import register_google_maps_providers

class Container:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        
        # Register all providers
        register_tomtom_providers()
        register_google_maps_providers()
        
        # Get registry
        self.registry = get_map_provider_registry()
    
    def _init_adapters(self):
        """Khởi tạo adapters từ registry - không biết về provider cụ thể."""
        map_settings = MapProviderSettings(
            provider_type=self.settings.map_provider_type,
            base_url=self.settings.map_provider_base_url,
            api_key=self.settings.map_provider_api_key,
            timeout_sec=self.settings.http_timeout_sec
        )
        
        # ✅ GOOD: Adapters được tạo từ registry - không hard-code
        self.routing_adapter = self.registry.get_routing_adapter(map_settings, self.http)
        self.geocoding_adapter = self.registry.get_geocoding_adapter(map_settings, self.http)
        # ...
```

---

### Strategy 2: Plugin-Based Architecture

#### 2.1. Plugin Discovery

```python
# ✅ GOOD: Auto-discover providers
# app/infrastructure/maps/plugins.py

import importlib
import pkgutil
from pathlib import Path

def discover_map_providers():
    """Auto-discover and register all map providers."""
    providers_dir = Path(__file__).parent / "providers"
    
    for module_info in pkgutil.iter_modules([str(providers_dir)]):
        if module_info.name.startswith("_"):
            continue
        
        try:
            module = importlib.import_module(f"app.infrastructure.maps.providers.{module_info.name}")
            if hasattr(module, "register_providers"):
                module.register_providers()
        except Exception as e:
            logger.warning(f"Failed to load provider {module_info.name}: {e}")
```

---

### Strategy 3: Abstraction Layer cho Endpoints và Mappers

#### 3.1. Endpoint Strategy

```python
# ✅ GOOD: Endpoint strategy pattern
# app/infrastructure/maps/endpoints/endpoint_strategy.py

from typing import Protocol
from app.domain.enums.travel_mode import TravelMode

class EndpointStrategy(Protocol):
    """Strategy for building API endpoints."""
    
    def build_routing_url(self, origin: LatLon, destination: LatLon) -> str:
        """Build routing API URL."""
        ...
    
    def build_geocoding_url(self, address: str) -> str:
        """Build geocoding API URL."""
        ...
    
    def map_travel_mode(self, mode: TravelMode) -> str:
        """Map domain travel mode to API format."""
        ...

# TomTom implementation
class TomTomEndpointStrategy:
    def build_routing_url(self, origin: LatLon, destination: LatLon) -> str:
        return f"/routing/1/calculateRoute/{origin.lat},{origin.lon}:{destination.lat},{destination.lon}/json"
    
    def map_travel_mode(self, mode: TravelMode) -> str:
        return {
            TravelMode.CAR: "car",
            TravelMode.BICYCLE: "bicycle",
            TravelMode.FOOT: "pedestrian",
        }.get(mode, "car")

# Google Maps implementation
class GoogleMapsEndpointStrategy:
    def build_routing_url(self, origin: LatLon, destination: LatLon) -> str:
        return "/directions/json"
    
    def map_travel_mode(self, mode: TravelMode) -> str:
        return {
            TravelMode.CAR: "driving",
            TravelMode.BICYCLE: "bicycling",
            TravelMode.FOOT: "walking",
        }.get(mode, "driving")
```

#### 3.2. Mapper Factory

```python
# ✅ GOOD: Mapper factory
# app/infrastructure/maps/mappers/mapper_factory.py

from typing import Protocol, Dict

class ResponseMapper(Protocol):
    """Protocol for mapping API responses to domain models."""
    def to_domain_route_plan(self, payload: dict) -> RoutePlan:
        ...

class MapperFactory:
    """Factory for creating response mappers."""
    
    def __init__(self):
        self._mappers: Dict[str, Type[ResponseMapper]] = {}
    
    def register_mapper(self, provider: str, mapper_class: Type[ResponseMapper]):
        """Register a mapper for a provider."""
        self._mappers[provider] = mapper_class
    
    def create_mapper(self, provider: str) -> ResponseMapper:
        """Create mapper for provider."""
        mapper_class = self._mappers.get(provider)
        if not mapper_class:
            raise ValueError(f"Unknown provider mapper: {provider}")
        return mapper_class()

# Usage
mapper_factory = MapperFactory()
mapper_factory.register_mapper("tomtom", TomTomMapper)
mapper_factory.register_mapper("google_maps", GoogleMapsMapper)

# In adapter
def __init__(self, provider_type: str, ...):
    mapper_factory = get_mapper_factory()
    self._mapper = mapper_factory.create_mapper(provider_type)
```

---

## 📝 Checklist Migration với Architecture mới

### Migration TomTom → Google Maps sẽ chỉ cần:

1. ✅ **Tạo Google Maps Adapters** (trong `app/infrastructure/maps/providers/google_maps/`)
2. ✅ **Tạo Google Maps Factories** (implement factory interfaces)
3. ✅ **Register factories** (1 dòng code: `register_google_maps_providers()`)
4. ✅ **Thay đổi config** (`.env`: `MAP_PROVIDER=google_maps`)

**Không cần sửa:**
- ❌ Container code
- ❌ DI Providers
- ❌ Use Cases
- ❌ Domain logic
- ❌ Settings structure (chỉ thay giá trị)

---

## 🎯 Lợi ích của Architecture mới

### 1. **Low Coupling** ✅
- Container không biết về provider cụ thể
- Chỉ cần biết Protocol/Interface
- Providers có thể thay đổi mà không ảnh hưởng core code

### 2. **Open/Closed Principle** ✅
- Mở để extension (thêm provider mới)
- Đóng cho modification (không cần sửa code cũ)

### 3. **Configuration-Based** ✅
- Switch provider chỉ bằng config
- Có thể test với nhiều providers dễ dàng

### 4. **Plugin Architecture** ✅
- Có thể load providers dynamically
- Dễ dàng thêm/bớt providers

---

## 📊 So sánh

| Aspect | Current (High Coupling) | Proposed (Low Coupling) |
|--------|------------------------|-------------------------|
| **Migration effort** | ~15 files cần sửa | ~3 files (chỉ tạo mới) |
| **Container changes** | Phải sửa imports & code | Không cần sửa |
| **Settings changes** | Phải thay field names | Chỉ thay giá trị |
| **Test with multiple providers** | Khó (phải sửa code) | Dễ (chỉ đổi config) |
| **Adding new provider** | ~15 files cần sửa | ~3 files (tạo mới) |

---

## 🚀 Recommendation

**Nên refactor sang architecture mới này** vì:
1. Migration dễ hơn 80%
2. Code maintainable hơn
3. Test-friendly hơn
4. Future-proof (dễ thêm providers)

**Trade-off:**
- Tốn thời gian refactor ban đầu (~1-2 ngày)
- Nhưng tiết kiệm rất nhiều thời gian sau này

---

## 📖 Tham khảo Patterns

- **Strategy Pattern**: Cho endpoints và mappers
- **Factory Pattern**: Cho adapter creation
- **Registry Pattern**: Cho provider management
- **Plugin Pattern**: Cho dynamic loading
- **Dependency Inversion**: Cho loose coupling


