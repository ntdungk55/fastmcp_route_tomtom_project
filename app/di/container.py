
from app.application.use_cases.calculate_route import CalculateRoute
from app.infrastructure.config.settings import Settings
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter


class Container:
    def __init__(self, settings: Settings | None = None):
        self.logger = get_logger("container")
        self.settings = settings or Settings()
        self.settings.validate()

        self.http = AsyncApiClient()
        self.routing_adapter = TomTomRoutingAdapter(
            base_url=self.settings.tomtom_base_url,
            api_key=self.settings.tomtom_api_key,
            http=self.http,
            timeout_sec=self.settings.http_timeout_sec,
        )
        self.calculate_route = CalculateRoute(self.routing_adapter)
