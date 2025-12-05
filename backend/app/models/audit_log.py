"""
Audit log model for tracking all important actions in the system
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class AuditAction(str, Enum):
    """Types of auditable actions"""
    # Authentication
    LOGIN = 'login'
    LOGOUT = 'logout'

    # Employee Management
    EMPLOYEE_CREATE = 'employee_create'
    EMPLOYEE_UPDATE = 'employee_update'
    EMPLOYEE_SYNC = 'employee_sync'
    EMPLOYEE_VIEW = 'employee_view'
    EMPLOYEE_MOVE_OU = 'employee_move_ou'

    # Time-off Requests
    TIMEOFF_CREATE = 'timeoff_create'
    TIMEOFF_UPDATE = 'timeoff_update'
    TIMEOFF_DELETE = 'timeoff_delete'
    TIMEOFF_APPROVE_MANAGER = 'timeoff_approve_manager'
    TIMEOFF_APPROVE_ADMIN = 'timeoff_approve_admin'
    TIMEOFF_REJECT = 'timeoff_reject'

    # Evaluations
    EVALUATION_CREATE = 'evaluation_create'

    # System
    SYNC_WORKSPACE = 'sync_workspace'


class AuditLog:
    """Audit log entry for tracking system actions"""

    def __init__(
        self,
        user_email: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        log_id: Optional[str] = None,
        **kwargs
    ):
        self.log_id = log_id
        self.user_email = user_email
        self.action = AuditAction(action) if isinstance(action, str) else action
        self.resource_type = resource_type  # 'employee', 'timeoff_request', 'evaluation', etc.
        self.resource_id = resource_id  # ID of the resource being acted upon
        self.details = details or {}  # Additional context about the action
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        return {
            'user_email': self.user_email,
            'action': self.action.value,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, log_id: str, data: Dict[str, Any]) -> 'AuditLog':
        """Create from Firestore dictionary"""
        data['log_id'] = log_id
        # Convert timestamp string back to datetime if needed
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def get_display_message(self) -> str:
        """Get human-readable description of the action"""
        action_messages = {
            AuditAction.LOGIN: f"{self.user_email} logged in",
            AuditAction.LOGOUT: f"{self.user_email} logged out",
            AuditAction.EMPLOYEE_CREATE: f"{self.user_email} created employee record for {self.resource_id}",
            AuditAction.EMPLOYEE_UPDATE: f"{self.user_email} updated employee {self.resource_id}",
            AuditAction.EMPLOYEE_SYNC: f"{self.user_email} synced employees from Google Workspace",
            AuditAction.EMPLOYEE_VIEW: f"{self.user_email} viewed employee {self.resource_id}",
            AuditAction.EMPLOYEE_MOVE_OU: f"{self.user_email} moved {self.resource_id} to {self.details.get('new_ou', 'unknown')} OU",
            AuditAction.TIMEOFF_CREATE: f"{self.user_email} created time-off request {self.resource_id}",
            AuditAction.TIMEOFF_UPDATE: f"{self.user_email} updated time-off request {self.resource_id}",
            AuditAction.TIMEOFF_DELETE: f"{self.user_email} deleted time-off request {self.resource_id}",
            AuditAction.TIMEOFF_APPROVE_MANAGER: f"{self.user_email} approved time-off request {self.resource_id} as manager",
            AuditAction.TIMEOFF_APPROVE_ADMIN: f"{self.user_email} gave final approval to time-off request {self.resource_id}",
            AuditAction.TIMEOFF_REJECT: f"{self.user_email} rejected time-off request {self.resource_id}",
            AuditAction.EVALUATION_CREATE: f"{self.user_email} added evaluation for {self.resource_id}",
            AuditAction.SYNC_WORKSPACE: f"{self.user_email} synced data from Google Workspace",
        }

        return action_messages.get(self.action, f"{self.user_email} performed {self.action.value} on {self.resource_type} {self.resource_id}")
