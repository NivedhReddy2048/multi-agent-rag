"""Observability, Request Tracing, Structured Logging, and OpenTelemetry readiness."""

import time
import uuid
import json
from typing import Dict, Any, Optional
from core.logger import get_logger

logger = get_logger("core.observability")


class TraceContext:
    """Manages request tracing context across asynchronous execution steps."""

    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.spans: Dict[str, float] = {}

    def start_span(self, name: str):
        self.spans[name] = time.time()

    def end_span(self, name: str) -> float:
        if name in self.spans:
            duration_ms = round((time.time() - self.spans[name]) * 1000, 2)
            logger.info(json.dumps({
                "event": "span_completed",
                "request_id": self.request_id,
                "span_name": name,
                "duration_ms": duration_ms,
            }))
            return duration_ms
        return 0.0


class AuditLogger:
    """Structured audit logging for security events and critical operations."""

    @staticmethod
    def log_audit_event(action: str, actor: str, status: str, details: Dict[str, Any]):
        audit_entry = {
            "timestamp": time.time(),
            "action": action,
            "actor": actor,
            "status": status,
            "details": details,
        }
        logger.info(f"AUDIT_EVENT: {json.dumps(audit_entry)}")


# Global singleton instance
audit_logger = AuditLogger()
