"""
Request History Service - BLK-1-07: SaveRequestHistory
Lưu lịch sử request vào database để audit, analytics, và debugging.
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

from app.infrastructure.logging.logger import get_logger


@dataclass
class RequestHistoryRecord:
    """Record cho request history."""
    id: str
    request_id: str
    tool_name: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    status: str = "RECEIVED"  # RECEIVED, PROCESSING, SUCCESS, ERROR
    created_at: str = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"


class RequestHistoryService:
    """
    BLK-1-07: SaveRequestHistory - Lưu lịch sử request async
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self._logger = get_logger(__name__)
        self._db_path = db_path or "destinations.db"
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
        self._circuit_breaker_open = False
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize request_history table."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS request_history (
                        id TEXT PRIMARY KEY,
                        request_id TEXT UNIQUE NOT NULL,
                        tool_name TEXT NOT NULL,
                        arguments TEXT,  -- JSON string
                        user_id TEXT,
                        session_id TEXT,
                        client_id TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT,
                        completed_at TEXT,
                        duration_ms INTEGER,
                        error_code TEXT,
                        metadata TEXT  -- JSON string
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_history_request_id ON request_history(request_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_history_user_created ON request_history(user_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_history_tool_status ON request_history(tool_name, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_history_created_at ON request_history(created_at)")
                
                conn.commit()
                self._logger.info("Request history database initialized successfully")
                
        except Exception as e:
            self._logger.error(f"Failed to initialize request history database: {e}")
            raise
    
    async def save_request_history(self, record: RequestHistoryRecord) -> bool:
        """
        BLK-1-07: Save request history record
        
        Args:
            record: RequestHistoryRecord to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self._circuit_breaker_open:
            self._logger.warning("Circuit breaker is open, skipping request history save")
            return False
        
        try:
            # Sanitize arguments to remove sensitive data
            sanitized_arguments = self._sanitize_arguments(record.arguments)
            
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO request_history 
                    (id, request_id, tool_name, arguments, user_id, session_id, client_id, 
                     status, created_at, updated_at, completed_at, duration_ms, error_code, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.request_id,
                    record.tool_name,
                    json.dumps(sanitized_arguments),
                    record.user_id,
                    record.session_id,
                    record.client_id,
                    record.status,
                    record.created_at,
                    record.updated_at,
                    record.completed_at,
                    record.duration_ms,
                    record.error_code,
                    json.dumps(record.metadata) if record.metadata else None
                ))
                conn.commit()
            
            self._logger.info(f"BLK-1-07: Saved request history for {record.request_id}")
            self._reset_circuit_breaker()
            return True
            
        except Exception as e:
            self._logger.error(f"BLK-1-07: Failed to save request history for {record.request_id}: {e}")
            self._handle_circuit_breaker_failure()
            return False
    
    async def update_request_status(self, request_id: str, status: str, 
                                  completed_at: Optional[str] = None,
                                  duration_ms: Optional[int] = None,
                                  error_code: Optional[str] = None,
                                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update request status and completion info
        
        Args:
            request_id: Request ID to update
            status: New status (SUCCESS, ERROR, etc.)
            completed_at: Completion timestamp
            duration_ms: Request duration in milliseconds
            error_code: Error code if failed
            metadata: Additional metadata
            
        Returns:
            bool: True if updated successfully
        """
        if self._circuit_breaker_open:
            return False
        
        try:
            updated_at = datetime.utcnow().isoformat() + "Z"
            
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    UPDATE request_history 
                    SET status = ?, updated_at = ?, completed_at = ?, 
                        duration_ms = ?, error_code = ?, metadata = ?
                    WHERE request_id = ?
                """, (
                    status,
                    updated_at,
                    completed_at,
                    duration_ms,
                    error_code,
                    json.dumps(metadata) if metadata else None,
                    request_id
                ))
                conn.commit()
            
            self._logger.info(f"BLK-1-07: Updated request status for {request_id} to {status}")
            self._reset_circuit_breaker()
            return True
            
        except Exception as e:
            self._logger.error(f"BLK-1-07: Failed to update request status for {request_id}: {e}")
            self._handle_circuit_breaker_failure()
            return False
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize arguments to remove sensitive data
        
        Args:
            arguments: Raw arguments dict
            
        Returns:
            Dict: Sanitized arguments
        """
        if not arguments:
            return {}
        
        sanitized = {}
        sensitive_fields = {
            'api_key', 'token', 'password', 'secret', 'key',
            'credit_card', 'ssn', 'phone', 'email'
        }
        
        for key, value in arguments.items():
            key_lower = key.lower()
            
            # Check if field contains sensitive data
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_fields)
            
            if is_sensitive:
                # Mask sensitive data
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"***{value[-4:]}"
                else:
                    sanitized[key] = "***"
            else:
                # Keep non-sensitive data
                sanitized[key] = value
        
        return sanitized
    
    def _handle_circuit_breaker_failure(self):
        """Handle circuit breaker failure."""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.utcnow()
        
        # Open circuit breaker after 10 failures in 30 seconds
        if self._circuit_breaker_failures >= 10:
            self._circuit_breaker_open = True
            self._logger.warning("Circuit breaker opened due to repeated failures")
            
            # Schedule auto-close after 60 seconds
            asyncio.create_task(self._auto_close_circuit_breaker())
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on success."""
        self._circuit_breaker_failures = 0
        self._circuit_breaker_open = False
    
    async def _auto_close_circuit_breaker(self):
        """Auto-close circuit breaker after recovery period."""
        await asyncio.sleep(60)  # 60 seconds recovery period
        self._circuit_breaker_open = False
        self._circuit_breaker_failures = 0
        self._logger.info("Circuit breaker auto-closed after recovery period")
    
    async def get_request_history(self, user_id: Optional[str] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get request history for analytics
        
        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: Request history records
        """
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if user_id:
                    cursor = conn.execute("""
                        SELECT * FROM request_history 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM request_history 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                records = []
                for row in cursor.fetchall():
                    record = dict(row)
                    # Parse JSON fields
                    if record['arguments']:
                        record['arguments'] = json.loads(record['arguments'])
                    if record['metadata']:
                        record['metadata'] = json.loads(record['metadata'])
                    records.append(record)
                
                return records
                
        except Exception as e:
            self._logger.error(f"Failed to get request history: {e}")
            return []
    
    async def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get analytics data for the last N days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict: Analytics data
        """
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Error rate by tool
                error_rate_cursor = conn.execute("""
                    SELECT tool_name, 
                           COUNT(*) as total,
                           COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
                           ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'ERROR') / COUNT(*), 2) as error_rate_pct
                    FROM request_history
                    WHERE created_at > datetime('now', '-{} days')
                    GROUP BY tool_name
                    ORDER BY error_rate_pct DESC
                """.format(days))
                
                error_rates = [dict(row) for row in error_rate_cursor.fetchall()]
                
                # Average duration by tool
                duration_cursor = conn.execute("""
                    SELECT tool_name,
                           AVG(duration_ms) as avg_duration_ms,
                           COUNT(*) as success_count
                    FROM request_history
                    WHERE status = 'SUCCESS' AND duration_ms IS NOT NULL
                      AND created_at > datetime('now', '-{} days')
                    GROUP BY tool_name
                """.format(days))
                
                durations = [dict(row) for row in duration_cursor.fetchall()]
                
                # Total requests
                total_cursor = conn.execute("""
                    SELECT COUNT(*) as total_requests,
                           COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful_requests,
                           COUNT(*) FILTER (WHERE status = 'ERROR') as failed_requests
                    FROM request_history
                    WHERE created_at > datetime('now', '-{} days')
                """.format(days))
                
                totals = dict(total_cursor.fetchone())
                
                return {
                    "period_days": days,
                    "totals": totals,
                    "error_rates_by_tool": error_rates,
                    "average_durations_by_tool": durations
                }
                
        except Exception as e:
            self._logger.error(f"Failed to get analytics: {e}")
            return {}


# Factory function
def get_request_history_service(db_path: Optional[str] = None) -> RequestHistoryService:
    """Factory function để lấy request history service."""
    return RequestHistoryService(db_path)

