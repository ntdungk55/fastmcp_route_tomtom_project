"""Request handler service for processing MCP requests."""

from typing import Dict, Any
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RequestHandlerService:
    """Service for handling MCP requests."""
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        try:
            logger.debug(f"Handling request: {request.get('method', 'unknown')}")
            
            # Basic request validation
            if not isinstance(request, dict):
                raise ValueError("Request must be a dictionary")
            
            if 'method' not in request:
                raise ValueError("Request must contain 'method' field")
            
            # Request is valid
            return {
                "status": "valid",
                "request_id": request.get('id', 'unknown')
            }
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            raise


def get_request_handler_service() -> RequestHandlerService:
    """Factory function to get request handler service instance."""
    return RequestHandlerService()
