"""
Request Result Updater Service - BLK-1-13: UpdateRequestResult
Cập nhật kết quả request vào request history.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.application.services.request_history_service import (
    RequestHistoryService, get_request_history_service
)
from app.infrastructure.logging.logger import get_logger


class RequestResultUpdaterService:
    """
    BLK-1-13: UpdateRequestResult - Cập nhật kết quả request vào request history
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self._logger = get_logger(__name__)
        self._request_history_service = get_request_history_service(db_path)
    
    async def update_request_result(self, request_id: str, status: str, 
                                  result_data: Optional[Dict[str, Any]] = None,
                                  error_data: Optional[Dict[str, Any]] = None,
                                  duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        BLK-1-13: Update request result in history
        
        Args:
            request_id: Request ID
            status: Request status (SUCCESS | ERROR)
            result_data: Success result data
            error_data: Error data
            duration_ms: Request duration in milliseconds
            
        Returns:
            Dict: Update result
        """
        self._logger.info(f"BLK-1-13: Updating request result for {request_id} with status {status}")
        
        try:
            # Prepare metadata
            metadata = {}
            
            if status == "SUCCESS" and result_data:
                # Extract success metrics
                if "route_data" in result_data:
                    route_data = result_data["route_data"]
                    summary = route_data.get("summary", {})
                    
                    metadata.update({
                        "route_distance_m": summary.get("length_in_meters"),
                        "route_duration_s": summary.get("travel_time_in_seconds"),
                        "traffic_delay_s": summary.get("traffic_delay_in_seconds"),
                        "route_type": "success"
                    })
                
                if "metadata" in result_data:
                    api_metadata = result_data["metadata"]
                    metadata.update({
                        "api_provider": api_metadata.get("provider"),
                        "api_version": api_metadata.get("api_version"),
                        "api_duration_ms": api_metadata.get("request_duration_ms"),
                        "api_attempts": api_metadata.get("attempt")
                    })
            
            elif status == "ERROR" and error_data:
                # Extract error metrics
                metadata.update({
                    "error_category": error_data.get("category"),
                    "error_type": error_data.get("type"),
                    "error_code": error_data.get("code"),
                    "retry_after": error_data.get("retry_after")
                })
                
                # Add internal error details if available
                if "internal" in error_data:
                    internal = error_data["internal"]
                    metadata.update({
                        "internal_error_code": internal.get("code"),
                        "internal_severity": internal.get("severity")
                    })
            
            # Update request history
            success = await self._request_history_service.update_request_status(
                request_id=request_id,
                status=status,
                completed_at=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration_ms,
                error_code=error_data.get("code") if error_data else None,
                metadata=metadata
            )
            
            if success:
                self._logger.info(f"BLK-1-13: Successfully updated request result for {request_id}")
                return {
                    "success": True,
                    "request_id": request_id,
                    "status": status,
                    "message": "Request result updated successfully"
                }
            else:
                self._logger.error(f"BLK-1-13: Failed to update request result for {request_id}")
                return {
                    "success": False,
                    "request_id": request_id,
                    "error": "Failed to update request history"
                }
                
        except Exception as e:
            self._logger.error(f"BLK-1-13: Exception updating request result for {request_id}: {e}")
            return {
                "success": False,
                "request_id": request_id,
                "error": str(e)
            }
    
    async def update_success_result(self, request_id: str, route_data: Dict[str, Any],
                                  api_metadata: Dict[str, Any],
                                  duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Update success result
        
        Args:
            request_id: Request ID
            route_data: Route data from API
            api_metadata: API metadata
            duration_ms: Request duration
            
        Returns:
            Dict: Update result
        """
        result_data = {
            "route_data": route_data,
            "metadata": api_metadata
        }
        
        return await self.update_request_result(
            request_id=request_id,
            status="SUCCESS",
            result_data=result_data,
            duration_ms=duration_ms
        )
    
    async def update_error_result(self, request_id: str, error_data: Dict[str, Any],
                                duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Update error result
        
        Args:
            request_id: Request ID
            error_data: Error data
            duration_ms: Request duration
            
        Returns:
            Dict: Update result
        """
        return await self.update_request_result(
            request_id=request_id,
            status="ERROR",
            error_data=error_data,
            duration_ms=duration_ms
        )
    
    async def update_validation_error_result(self, request_id: str, 
                                           validation_errors: list,
                                           duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Update validation error result
        
        Args:
            request_id: Request ID
            validation_errors: List of validation errors
            duration_ms: Request duration
            
        Returns:
            Dict: Update result
        """
        error_data = {
            "category": "USER_ERROR",
            "type": "VALIDATION_ERROR",
            "code": "VALIDATION_ERROR",
            "validation_errors": validation_errors
        }
        
        return await self.update_request_result(
            request_id=request_id,
            status="ERROR",
            error_data=error_data,
            duration_ms=duration_ms
        )
    
    async def get_request_analytics(self, request_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific request
        
        Args:
            request_id: Request ID
            
        Returns:
            Dict: Request analytics
        """
        try:
            history = await self._request_history_service.get_request_history(limit=1)
            
            # Find the specific request
            request_data = None
            for record in history:
                if record.get("request_id") == request_id:
                    request_data = record
                    break
            
            if not request_data:
                return {
                    "success": False,
                    "error": "Request not found",
                    "request_id": request_id
                }
            
            # Calculate analytics
            analytics = {
                "request_id": request_id,
                "tool_name": request_data.get("tool_name"),
                "status": request_data.get("status"),
                "created_at": request_data.get("created_at"),
                "completed_at": request_data.get("completed_at"),
                "duration_ms": request_data.get("duration_ms"),
                "error_code": request_data.get("error_code")
            }
            
            # Add metadata analytics
            metadata = request_data.get("metadata", {})
            if metadata:
                analytics.update({
                    "route_distance_m": metadata.get("route_distance_m"),
                    "route_duration_s": metadata.get("route_duration_s"),
                    "traffic_delay_s": metadata.get("traffic_delay_s"),
                    "api_provider": metadata.get("api_provider"),
                    "api_duration_ms": metadata.get("api_duration_ms"),
                    "api_attempts": metadata.get("api_attempts")
                })
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            self._logger.error(f"BLK-1-13: Failed to get analytics for request {request_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics from request history
        
        Returns:
            Dict: System metrics
        """
        try:
            # Get analytics for last 24 hours
            analytics = await self._request_history_service.get_analytics(days=1)
            
            return {
                "success": True,
                "metrics": analytics
            }
            
        except Exception as e:
            self._logger.error(f"BLK-1-13: Failed to get system metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Factory function
def get_request_result_updater_service(db_path: Optional[str] = None) -> RequestResultUpdaterService:
    """Factory function để lấy request result updater service."""
    return RequestResultUpdaterService(db_path)

