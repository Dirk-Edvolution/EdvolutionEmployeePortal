"""
Audit logging utilities
"""
from flask import request
from typing import Optional, Dict, Any
from backend.app.models import AuditLog, AuditAction
from backend.app.services import FirestoreService


def log_action(
    user_email: str,
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log an action to the audit trail

    Args:
        user_email: Email of the user performing the action
        action: The action being performed
        resource_type: Type of resource ('employee', 'timeoff_request', etc.)
        resource_id: ID of the resource being acted upon
        details: Additional context about the action

    Returns:
        str: The ID of the created audit log entry
    """
    # Get IP address and user agent from request context
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None

    audit_log = AuditLog(
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )

    db = FirestoreService()
    log_id = db.create_audit_log(audit_log)

    return log_id
