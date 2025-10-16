"""
System Error Handler Service - BLK-1-06: HandleSystemError
Xử lý system errors với logging, alerting và recovery actions.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.infrastructure.logging.logger import get_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecoveryAction(Enum):
    """Recovery actions."""
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    CIRCUIT_BREAK = "CIRCUIT_BREAK"
    ALERT_OPS = "ALERT_OPS"
    RESTART_SERVICE = "RESTART_SERVICE"


@dataclass
class SystemErrorContext:
    """System error context."""
    error_code: str
    error_message: str
    severity: ErrorSeverity
    component: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class RecoveryPlan:
    """Recovery plan for system error."""
    actions: List[RecoveryAction]
    retry_count: int = 0
    max_retries: int = 3
    backoff_seconds: int = 1
    alert_ops: bool = False
    fallback_available: bool = False


class SystemErrorHandlerService:
    """
    BLK-1-06: HandleSystemError - Xử lý system errors với logging và recovery
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._error_counts = {}  # Track error counts for circuit breaking
        self._recovery_plans = self._initialize_recovery_plans()
    
    def _initialize_recovery_plans(self) -> Dict[str, RecoveryPlan]:
        """Initialize recovery plans for different error types."""
        return {
            "API_KEY_NOT_CONFIGURED": RecoveryPlan(
                actions=[RecoveryAction.ALERT_OPS],
                alert_ops=True,
                fallback_available=False
            ),
            "API_KEY_INVALID": RecoveryPlan(
                actions=[RecoveryAction.ALERT_OPS],
                alert_ops=True,
                fallback_available=False
            ),
            "API_KEY_UNAUTHORIZED": RecoveryPlan(
                actions=[RecoveryAction.ALERT_OPS],
                alert_ops=True,
                fallback_available=False
            ),
            "RATE_LIMIT": RecoveryPlan(
                actions=[RecoveryAction.RETRY, RecoveryAction.CIRCUIT_BREAK],
                max_retries=1,
                backoff_seconds=60,
                fallback_available=False
            ),
            "TIMEOUT": RecoveryPlan(
                actions=[RecoveryAction.RETRY, RecoveryAction.CIRCUIT_BREAK],
                max_retries=3,
                backoff_seconds=2,
                fallback_available=False
            ),
            "SERVICE_UNAVAILABLE": RecoveryPlan(
                actions=[RecoveryAction.CIRCUIT_BREAK, RecoveryAction.ALERT_OPS],
                alert_ops=True,
                fallback_available=False
            ),
            "EXTERNAL_API_ERROR": RecoveryPlan(
                actions=[RecoveryAction.RETRY, RecoveryAction.CIRCUIT_BREAK],
                max_retries=3,
                backoff_seconds=1,
                fallback_available=False
            )
        }
    
    async def handle_system_error(self, error_context: SystemErrorContext) -> Dict[str, Any]:
        """
        BLK-1-06: Handle system error
        
        Args:
            error_context: System error context
            
        Returns:
            Dict: Error handling result
        """
        self._logger.error(f"BLK-1-06: Handling system error {error_context.error_code}")
        
        # Log error with context
        await self._log_system_error(error_context)
        
        # Get recovery plan
        recovery_plan = self._recovery_plans.get(
            error_context.error_code, 
            RecoveryPlan(actions=[RecoveryAction.ALERT_OPS])
        )
        
        # Execute recovery actions
        recovery_result = await self._execute_recovery_actions(error_context, recovery_plan)
        
        # Update error counts for circuit breaking
        self._update_error_counts(error_context.error_code)
        
        # Alert operations if needed
        if recovery_plan.alert_ops:
            await self._alert_operations(error_context)
        
        return {
            "error_handled": True,
            "error_code": error_context.error_code,
            "severity": error_context.severity.value,
            "recovery_actions": [action.value for action in recovery_plan.actions],
            "recovery_result": recovery_result,
            "alerted_ops": recovery_plan.alert_ops,
            "timestamp": error_context.timestamp
        }
    
    async def _log_system_error(self, error_context: SystemErrorContext):
        """Log system error with full context."""
        log_data = {
            "error_code": error_context.error_code,
            "error_message": error_context.error_message,
            "severity": error_context.severity.value,
            "component": error_context.component,
            "request_id": error_context.request_id,
            "user_id": error_context.user_id,
            "timestamp": error_context.timestamp,
            "metadata": error_context.metadata
        }
        
        # Log at appropriate level based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(f"CRITICAL SYSTEM ERROR: {error_context.error_code}", extra=log_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            self._logger.error(f"HIGH SEVERITY ERROR: {error_context.error_code}", extra=log_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self._logger.warning(f"MEDIUM SEVERITY ERROR: {error_context.error_code}", extra=log_data)
        else:
            self._logger.info(f"LOW SEVERITY ERROR: {error_context.error_code}", extra=log_data)
    
    async def _execute_recovery_actions(self, error_context: SystemErrorContext, 
                                      recovery_plan: RecoveryPlan) -> Dict[str, Any]:
        """Execute recovery actions."""
        results = {}
        
        for action in recovery_plan.actions:
            try:
                if action == RecoveryAction.RETRY:
                    results["retry"] = await self._handle_retry(error_context, recovery_plan)
                elif action == RecoveryAction.CIRCUIT_BREAK:
                    results["circuit_break"] = await self._handle_circuit_break(error_context)
                elif action == RecoveryAction.FALLBACK:
                    results["fallback"] = await self._handle_fallback(error_context)
                elif action == RecoveryAction.ALERT_OPS:
                    results["alert_ops"] = await self._alert_operations(error_context)
                elif action == RecoveryAction.RESTART_SERVICE:
                    results["restart_service"] = await self._handle_service_restart(error_context)
            except Exception as e:
                self._logger.error(f"Failed to execute recovery action {action.value}: {e}")
                results[action.value.lower()] = {"success": False, "error": str(e)}
        
        return results
    
    async def _handle_retry(self, error_context: SystemErrorContext, 
                          recovery_plan: RecoveryPlan) -> Dict[str, Any]:
        """Handle retry logic."""
        if recovery_plan.retry_count >= recovery_plan.max_retries:
            return {
                "success": False,
                "reason": "Max retries exceeded",
                "retry_count": recovery_plan.retry_count,
                "max_retries": recovery_plan.max_retries
            }
        
        # Increment retry count
        recovery_plan.retry_count += 1
        
        # Calculate backoff delay
        delay = recovery_plan.backoff_seconds * (2 ** (recovery_plan.retry_count - 1))
        
        self._logger.info(f"BLK-1-06: Scheduling retry {recovery_plan.retry_count}/{recovery_plan.max_retries} after {delay}s")
        
        # Schedule retry (in real implementation, this would be handled by the calling service)
        return {
            "success": True,
            "retry_count": recovery_plan.retry_count,
            "max_retries": recovery_plan.max_retries,
            "backoff_delay": delay,
            "next_retry_at": (datetime.utcnow().timestamp() + delay)
        }
    
    async def _handle_circuit_break(self, error_context: SystemErrorContext) -> Dict[str, Any]:
        """Handle circuit breaker."""
        error_key = f"{error_context.component}:{error_context.error_code}"
        
        # Update error count
        if error_key not in self._error_counts:
            self._error_counts[error_key] = {"count": 0, "last_error": None}
        
        self._error_counts[error_key]["count"] += 1
        self._error_counts[error_key]["last_error"] = error_context.timestamp
        
        # Check if circuit should be opened
        error_count = self._error_counts[error_key]["count"]
        
        if error_count >= 10:  # Open circuit after 10 errors
            self._logger.critical(f"BLK-1-06: Opening circuit breaker for {error_key} after {error_count} errors")
            return {
                "success": True,
                "action": "circuit_opened",
                "error_count": error_count,
                "component": error_context.component
            }
        
        return {
            "success": True,
            "action": "error_counted",
            "error_count": error_count,
            "circuit_threshold": 10
        }
    
    async def _handle_fallback(self, error_context: SystemErrorContext) -> Dict[str, Any]:
        """Handle fallback mechanism."""
        # In a real implementation, this would switch to a backup service
        self._logger.info(f"BLK-1-06: Attempting fallback for {error_context.error_code}")
        
        return {
            "success": False,
            "reason": "No fallback available",
            "error_code": error_context.error_code
        }
    
    async def _alert_operations(self, error_context: SystemErrorContext) -> Dict[str, Any]:
        """Alert operations team."""
        alert_message = f"SYSTEM ERROR ALERT: {error_context.error_code}"
        alert_details = {
            "error_code": error_context.error_code,
            "error_message": error_context.error_message,
            "severity": error_context.severity.value,
            "component": error_context.component,
            "request_id": error_context.request_id,
            "timestamp": error_context.timestamp,
            "metadata": error_context.metadata
        }
        
        # Log critical alert
        self._logger.critical(f"OPS ALERT: {alert_message}", extra=alert_details)
        
        # In a real implementation, this would send alerts to:
        # - Slack/Discord channels
        # - Email notifications
        # - PagerDuty/Opsgenie
        # - Monitoring systems (Prometheus, DataDog, etc.)
        
        return {
            "success": True,
            "alert_sent": True,
            "alert_message": alert_message,
            "alert_details": alert_details
        }
    
    async def _handle_service_restart(self, error_context: SystemErrorContext) -> Dict[str, Any]:
        """Handle service restart."""
        # In a real implementation, this would trigger service restart
        self._logger.critical(f"BLK-1-06: Service restart required for {error_context.error_code}")
        
        return {
            "success": False,
            "reason": "Service restart not implemented",
            "error_code": error_context.error_code
        }
    
    def _update_error_counts(self, error_code: str):
        """Update error counts for monitoring."""
        # This would typically update metrics in a monitoring system
        pass
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        return {
            "status": "healthy",
            "error_counts": self._error_counts,
            "circuit_breakers": {
                key: {"open": count["count"] >= 10, "error_count": count["count"]}
                for key, count in self._error_counts.items()
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def reset_circuit_breaker(self, component: str, error_code: str) -> Dict[str, Any]:
        """Reset circuit breaker for a component."""
        error_key = f"{component}:{error_code}"
        
        if error_key in self._error_counts:
            self._error_counts[error_key] = {"count": 0, "last_error": None}
            self._logger.info(f"BLK-1-06: Reset circuit breaker for {error_key}")
            return {"success": True, "component": component, "error_code": error_code}
        
        return {"success": False, "reason": "Circuit breaker not found"}


# Factory function
def get_system_error_handler_service() -> SystemErrorHandlerService:
    """Factory function để lấy system error handler service."""
    return SystemErrorHandlerService()

