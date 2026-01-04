"""
Tool/equipment request model for tracking work tool approvals
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ToolType(str, Enum):
    """Types of work tools"""
    HEADPHONES = 'headphones'
    LAPTOP = 'laptop'
    MONITOR = 'monitor'
    KEYBOARD_MOUSE = 'keyboard_mouse'
    CHAIR = 'chair'
    DESK = 'desk'
    CUSTOM = 'custom'


class ApprovalStatus(str, Enum):
    """Status of approval workflow"""
    PENDING = 'pending'
    MANAGER_APPROVED = 'manager_approved'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class ToolRequest:
    """Tool request model with two-tier approval workflow"""

    def __init__(
        self,
        employee_email: str,
        tool_type: ToolType,
        justification: str,
        custom_description: Optional[str] = None,
        custom_price: Optional[float] = None,
        custom_link: Optional[str] = None,
        status: ApprovalStatus = ApprovalStatus.PENDING,
        manager_email: Optional[str] = None,
        manager_approved_at: Optional[datetime] = None,
        manager_approved_by: Optional[str] = None,
        admin_approved_at: Optional[datetime] = None,
        admin_approved_by: Optional[str] = None,
        rejected_at: Optional[datetime] = None,
        rejected_by: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        self.request_id = request_id
        self.employee_email = employee_email
        self.tool_type = ToolType(tool_type) if isinstance(tool_type, str) else tool_type
        self.justification = justification
        self.custom_description = custom_description
        self.custom_price = float(custom_price) if custom_price is not None else None
        self.custom_link = custom_link
        self.status = ApprovalStatus(status) if isinstance(status, str) else status
        self.manager_email = manager_email
        self.manager_approved_at = manager_approved_at
        self.manager_approved_by = manager_approved_by
        self.admin_approved_at = admin_approved_at
        self.admin_approved_by = admin_approved_by
        self.rejected_at = rejected_at
        self.rejected_by = rejected_by
        self.rejection_reason = rejection_reason
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def display_name(self) -> str:
        """Get display name for the tool"""
        if self.tool_type == ToolType.CUSTOM:
            return self.custom_description or "Custom Tool"
        return self.tool_type.value.replace('_', ' ').title()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        def safe_isoformat(dt):
            """Safely convert datetime to ISO format"""
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            if isinstance(dt, datetime):
                return dt.isoformat()
            return dt.isoformat()

        return {
            'employee_email': self.employee_email,
            'tool_type': self.tool_type.value,
            'justification': self.justification,
            'custom_description': self.custom_description,
            'custom_price': self.custom_price,
            'custom_link': self.custom_link,
            'status': self.status.value,
            'manager_email': self.manager_email,
            'manager_approved_at': safe_isoformat(self.manager_approved_at),
            'manager_approved_by': self.manager_approved_by,
            'admin_approved_at': safe_isoformat(self.admin_approved_at),
            'admin_approved_by': self.admin_approved_by,
            'rejected_at': safe_isoformat(self.rejected_at),
            'rejected_by': self.rejected_by,
            'rejection_reason': self.rejection_reason,
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
            'display_name': self.display_name,
        }

    @classmethod
    def from_dict(cls, request_id: str, data: Dict[str, Any]) -> 'ToolRequest':
        """Create from Firestore dictionary"""
        data['request_id'] = request_id
        return cls(**data)

    def approve_by_manager(self, manager_email: str) -> None:
        """Approve request by manager (first tier)"""
        self.status = ApprovalStatus.MANAGER_APPROVED
        self.manager_approved_by = manager_email
        self.manager_approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def approve_by_admin(self, admin_email: str) -> None:
        """Approve request by admin (second tier, final approval)"""
        self.status = ApprovalStatus.APPROVED
        self.admin_approved_by = admin_email
        self.admin_approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self, rejector_email: str, reason: Optional[str] = None) -> None:
        """Reject the request"""
        self.status = ApprovalStatus.REJECTED
        self.rejected_by = rejector_email
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()

    def can_approve_manager(self, user_email: str, manager_email: str) -> bool:
        """Check if user can approve as manager"""
        return (
            self.status == ApprovalStatus.PENDING and
            user_email == manager_email and
            user_email != self.employee_email
        )

    def can_approve_admin(self, user_email: str, admin_users: List[str]) -> bool:
        """Check if user can approve as admin"""
        is_admin = user_email in admin_users
        is_manager_approved = self.status == ApprovalStatus.MANAGER_APPROVED
        is_pending_and_is_manager = (
            self.status == ApprovalStatus.PENDING and
            user_email == self.manager_email
        )

        return is_admin and (is_manager_approved or is_pending_and_is_manager)
