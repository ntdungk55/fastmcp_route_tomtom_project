"""Dependency Injection Container - Wire tất cả dependencies theo Clean Architecture v5."""

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Use Cases
from app.application.use_cases.analyze_route_traffic import AnalyzeRouteTraffic
from app.application.use_cases.calculate_route import CalculateRoute
from app.application.use_cases.check_address_traffic import CheckAddressTraffic
from app.application.use_cases.delete_destination import DeleteDestinationUseCase
from app.application.use_cases.geocode_address import GeocodeAddress
from app.application.use_cases.get_detailed_route import GetDetailedRouteUseCase
from app.application.use_cases.get_intersection_position import GetIntersectionPosition
from app.application.use_cases.get_street_center import GetStreetCenter
from app.application.use_cases.get_traffic_condition import GetTrafficCondition
from app.application.use_cases.list_destinations import ListDestinationsUseCase
from app.application.use_cases.save_destination import SaveDestinationUseCase
from app.application.use_cases.update_destination import UpdateDestinationUseCase

# Infrastructure
from app.infrastructure.adapters.memory_destination_repository import MemoryDestinationRepository
from app.infrastructure.persistence.repositories.sqlite_destination_repository import SQLiteDestinationRepository
from app.infrastructure.persistence.migrations.create_destinations_table import run_migrations
from app.infrastructure.config.settings import Settings
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter

# Services
from app.application.services.validation_service import get_validation_service
from app.application.services.request_handler import get_request_handler_service
from app.infrastructure.config.api_config import get_config_service


class Container:
    """DI Container quản lý tất cả dependencies theo Clean Architecture v5.
    
    Chức năng: Wire các Use Cases với Adapters và cung cấp dependencies
    Kiến trúc: Dependency Injection pattern với providers, scopes, factories
    """
    
    # Type annotations for linter
    save_destination: 'SaveDestinationUseCase'
    
    def __init__(self, settings: Settings | None = None):
        """Khởi tạo container với settings."""
        self.logger = get_logger("container")
        self.settings = settings or Settings()
        self.settings.validate()

        # Infrastructure layer - HTTP client
        self.http = AsyncApiClient()
        
        # Services
        self.config_service = get_config_service()
        self.validation_service = get_validation_service()
        self.request_handler = get_request_handler_service()
        
        # Infrastructure layer - TomTom Adapters
        self._init_adapters()
        
        # Infrastructure layer - Repositories
        self._init_repositories()
        
        # Application layer - Use Cases
        self._init_use_cases()
    
    async def initialize_database(self):
        """Initialize database with migrations (async)."""
        try:
            await run_migrations()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _init_adapters(self):
        """Khởi tạo tất cả TomTom adapters."""
        base_config = {
            "base_url": self.settings.tomtom_base_url,
            "api_key": self.settings.tomtom_api_key,
            "http": self.http,
            "timeout_sec": self.settings.http_timeout_sec,
        }
        
        # Routing adapter (đã có sẵn)
        self.routing_adapter = TomTomRoutingAdapter(**base_config)
        
        # Geocoding adapter (mới)
        self.geocoding_adapter = TomTomGeocodingAdapter(**base_config)
        
        # Traffic adapter (mới)
        self.traffic_adapter = TomTomTrafficAdapter(**base_config)
    
    def _init_repositories(self):
        """Khởi tạo tất cả repositories."""
        # Use SQLite repository instead of memory repository
        self.destination_repository = SQLiteDestinationRepository(
            database_path=self.settings.database_path
        )
    
    
    def _init_use_cases(self):
        """Khởi tạo tất cả Use Cases với dependency injection."""
        
        # Routing Use Cases
        self.calculate_route = CalculateRoute(self.routing_adapter)
        
        # Geocoding Use Cases
        self.geocode_address = GeocodeAddress(self.geocoding_adapter)
        self.get_intersection_position = GetIntersectionPosition(self.geocoding_adapter)
        self.get_street_center = GetStreetCenter(self.geocoding_adapter)
        
        # Traffic Use Cases
        self.get_traffic_condition = GetTrafficCondition(self.traffic_adapter)
        self.analyze_route_traffic = AnalyzeRouteTraffic(self.traffic_adapter)
        
        # Composite Use Cases (cần nhiều adapters)
        self.check_address_traffic = CheckAddressTraffic(
            geocoding=self.geocoding_adapter,
            traffic=self.traffic_adapter
        )
        
        # Destination Use Cases
        self.save_destination = SaveDestinationUseCase(
            destination_repository=self.destination_repository,
            geocoding_provider=self.geocoding_adapter
        )
        self.list_destinations = ListDestinationsUseCase(self.destination_repository)
        self.delete_destination = DeleteDestinationUseCase(self.destination_repository)
        self.update_destination = UpdateDestinationUseCase(
            destination_repository=self.destination_repository,
            geocoding_provider=self.geocoding_adapter
        )
        
        # Detailed Route Use Case (composite use case)
        self.get_detailed_route = GetDetailedRouteUseCase(
            destination_repository=self.destination_repository,
            geocoding_provider=self.geocoding_adapter,
            routing_provider=self.routing_adapter
        )