"""
JARVIS Audit Log Module

Structured, append-only audit trail for all tool executions, confirmations,
and security events. Separate from operational logging (loguru).
"""

import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from loguru import logger


class AuditEventType(str, Enum):
    """Types of audit events."""
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMATION_GRANTED = "confirmation_granted"
    CONFIRMATION_DENIED = "confirmation_denied"
    UNDO_TRIGGERED = "undo_triggered"
    RED_ACTION_BLOCKED = "red_action_blocked"
    HIGH_CONFIDENCE_AUTO = "high_confidence_auto"
    LOW_CONFIDENCE_ESCALATED = "low_confidence_escalated"
    AMBIGUITY_DETECTED = "ambiguity_detected"


@dataclass
class AuditEvent:
    """Single audit event record."""
    timestamp: float
    event_type: str
    tool_name: str
    action: str
    risk_level: str
    args_summary: str
    result_summary: str
    confidence: float
    user_confirmed: Optional[bool] = None
    undo_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class AuditLog:
    """Append-only structured audit log.
    
    Writes JSONL (one JSON object per line) to data/audit.jsonl.
    Queryable by tool, risk level, time range.
    """
    
    def __init__(self, log_path: str = "./data/audit.jsonl"):
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[AuditEvent] = []
        self._buffer_limit = 50  # flush to disk every N events
        
        logger.info(f"Audit log initialized: {self._log_path}")
    
    def log(self, event: AuditEvent) -> None:
        """Record an audit event."""
        self._buffer.append(event)
        
        # Append to file
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Audit log write failed: {e}")
        
        # Flush buffer periodically
        if len(self._buffer) >= self._buffer_limit:
            self._buffer.clear()
    
    def log_tool_execution(self, tool_name: str, action: str, risk_level: str,
                           args: dict, result: str, confidence: float = 1.0,
                           user_confirmed: bool | None = None) -> None:
        """Log a tool execution event."""
        args_summary = json.dumps(args, ensure_ascii=False, default=str)[:500]
        result_summary = str(result)[:500]
        
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.TOOL_EXECUTED,
            tool_name=tool_name,
            action=action,
            risk_level=risk_level,
            args_summary=args_summary,
            result_summary=result_summary,
            confidence=confidence,
            user_confirmed=user_confirmed,
        )
        self.log(event)
    
    def log_confirmation(self, tool_name: str, action: str, risk_level: str,
                         granted: bool, details: str = "") -> None:
        """Log a confirmation request/grant/deny."""
        event_type = (AuditEventType.CONFIRMATION_GRANTED if granted
                      else AuditEventType.CONFIRMATION_DENIED)
        
        event = AuditEvent(
            timestamp=time.time(),
            event_type=event_type,
            tool_name=tool_name,
            action=action,
            risk_level=risk_level,
            args_summary=details[:500],
            result_summary="granted" if granted else "denied",
            confidence=1.0,
            user_confirmed=granted,
        )
        self.log(event)
    
    def log_undo(self, tool_name: str, action: str, undo_id: str) -> None:
        """Log an undo event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.UNDO_TRIGGERED,
            tool_name=tool_name,
            action=action,
            risk_level="yellow",
            args_summary="",
            result_summary=f"undo_id={undo_id}",
            confidence=1.0,
            undo_id=undo_id,
        )
        self.log(event)
    
    def query(self, tool_name: str | None = None, risk_level: str | None = None,
              since: float | None = None, limit: int = 100) -> list[AuditEvent]:
        """Query audit events with optional filters."""
        events = []
        try:
            if not self._log_path.exists():
                return []
            
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event = AuditEvent(**data)
                        
                        if tool_name and event.tool_name != tool_name:
                            continue
                        if risk_level and event.risk_level != risk_level:
                            continue
                        if since and event.timestamp < since:
                            continue
                        
                        events.append(event)
                        if len(events) >= limit:
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Audit query failed: {e}")
        
        return events
    
    def flush(self) -> None:
        """Force flush buffer to disk."""
        self._buffer.clear()


# Global audit log instance
_audit_log: AuditLog | None = None


def get_audit_log() -> AuditLog:
    """Get or create the global audit log instance."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


__all__ = [
    "AuditLog", "AuditEvent", "AuditEventType",
    "get_audit_log",
]
