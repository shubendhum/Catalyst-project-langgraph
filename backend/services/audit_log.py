"""
Audit Log Service
Append-only JSONL-based decision and action logging
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from utils.logging_utils import get_logger, get_request_id

logger = get_logger(__name__)


class AuditLogger:
    """
    Append-only audit logger for agent decisions and actions
    
    Stores logs as JSONL files with simple rotation strategy
    """
    
    def __init__(self, log_path: str = "/app/data/audit"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Current log file
        self.current_file = self._get_log_file()
        
        logger.info(f"Audit logger initialized: {self.log_path}")
    
    def _get_log_file(self) -> Path:
        """Get current log file path with date-based rotation"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_path / f"audit-{date_str}.jsonl"
    
    def log_decision(
        self,
        agent: str,
        action: str,
        decision: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an agent decision
        
        Args:
            agent: Agent name (e.g., 'planner', 'coder')
            action: Action type (e.g., 'task_planned', 'code_generated')
            decision: Decision data
            context: Additional context
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "decision",
            "agent": agent,
            "action": action,
            "decision": decision,
            "context": context or {},
            "request_id": get_request_id()
        }
        
        self._write_entry(entry)
    
    def log_tool_call(
        self,
        agent: str,
        tool: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log a tool call
        
        Args:
            agent: Agent name
            tool: Tool name
            inputs: Tool inputs
            outputs: Tool outputs (if successful)
            error: Error message (if failed)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "tool_call",
            "agent": agent,
            "tool": tool,
            "inputs": inputs,
            "outputs": outputs,
            "error": error,
            "success": error is None,
            "request_id": get_request_id()
        }
        
        self._write_entry(entry)
    
    def log_code_change(
        self,
        agent: str,
        file_path: str,
        operation: str,
        diff: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Log a code change
        
        Args:
            agent: Agent name
            file_path: File that was changed
            operation: Operation type ('create', 'modify', 'delete')
            diff: Git-style diff (optional)
            reason: Reason for change (optional)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "code_change",
            "agent": agent,
            "file_path": file_path,
            "operation": operation,
            "diff": diff,
            "reason": reason,
            "request_id": get_request_id()
        }
        
        self._write_entry(entry)
    
    def log_test_result(
        self,
        agent: str,
        test_type: str,
        results: Dict[str, Any],
        passed: bool
    ):
        """
        Log test results
        
        Args:
            agent: Agent name
            test_type: Type of test ('unit', 'e2e', 'integration')
            results: Test results data
            passed: Whether tests passed
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "test_result",
            "agent": agent,
            "test_type": test_type,
            "results": results,
            "passed": passed,
            "request_id": get_request_id()
        }
        
        self._write_entry(entry)
    
    def log_error(
        self,
        agent: str,
        error: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an error
        
        Args:
            agent: Agent name
            error: Error message
            context: Additional context
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "error",
            "agent": agent,
            "error": error,
            "context": context or {},
            "request_id": get_request_id()
        }
        
        self._write_entry(entry)
    
    def _write_entry(self, entry: Dict[str, Any]):
        """Write entry to log file"""
        try:
            # Check if we need to rotate (new day)
            current_file = self._get_log_file()
            if current_file != self.current_file:
                self.current_file = current_file
                logger.info(f"Rotated audit log to: {self.current_file}")
            
            # Append entry as JSON line
            with open(self.current_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)
    
    def query_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agent: Optional[str] = None,
        log_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Query audit logs
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            agent: Filter by agent
            log_type: Filter by log type
            limit: Maximum entries to return
            
        Returns:
            List of log entries
        """
        entries = []
        
        try:
            # Get log files to search
            if start_date:
                start = datetime.fromisoformat(start_date)
            else:
                start = datetime.utcnow().replace(day=1)  # Start of month
            
            if end_date:
                end = datetime.fromisoformat(end_date)
            else:
                end = datetime.utcnow()
            
            # Iterate through date range
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                log_file = self.log_path / f"audit-{date_str}.jsonl"
                
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        for line in f:
                            if len(entries) >= limit:
                                return entries
                            
                            try:
                                entry = json.loads(line)
                                
                                # Apply filters
                                if agent and entry.get('agent') != agent:
                                    continue
                                if log_type and entry.get('type') != log_type:
                                    continue
                                
                                entries.append(entry)
                            except json.JSONDecodeError:
                                continue
                
                # Next day
                current = current.replace(day=current.day + 1)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}", exc_info=True)
            return []


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    
    if _audit_logger is None:
        log_path = os.getenv("AUDIT_LOG_PATH", "/app/data/audit")
        _audit_logger = AuditLogger(log_path)
    
    return _audit_logger
