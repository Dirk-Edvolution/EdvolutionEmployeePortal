"""
Time-off request model for tracking vacation, sick leave, and day off requests
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum


class TimeOffType(str, Enum):
    """Types of time-off requests"""
    VACATION = 'vacation'
    SICK_LEAVE = 'sick_leave'
    DAY_OFF = 'day_off'


class ApprovalStatus(str, Enum):
    """Status of approval workflow"""
    PENDING = 'pending'
    MANAGER_APPROVED = 'manager_approved'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class TimeOffRequest:
    """Time-off request model with two-tier approval workflow"""

    def __init__(
        self,
        employee_email: str,
        start_date: date,
        end_date: date,
        timeoff_type: TimeOffType,
        notes: Optional[str] = None,
        status: ApprovalStatus = ApprovalStatus.PENDING,
        manager_email: Optional[str] = None,
        manager_approved_at: Optional[datetime] = None,
        manager_approved_by: Optional[str] = None,
        admin_approved_at: Optional[datetime] = None,
        admin_approved_by: Optional[str] = None,
        rejected_at: Optional[datetime] = None,
        rejected_by: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
        autoresponder_enabled: bool = False,
        manager_task_id: Optional[str] = None,
        admin_task_ids: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        request_id: Optional[str] = None,
        holiday_region: Optional[str] = None,
        working_days_count: Optional[int] = None,
        **kwargs
    ):
        self.request_id = request_id
        self.employee_email = employee_email
        self.start_date = start_date if isinstance(start_date, date) else datetime.fromisoformat(start_date).date()
        self.end_date = end_date if isinstance(end_date, date) else datetime.fromisoformat(end_date).date()
        self.timeoff_type = TimeOffType(timeoff_type) if isinstance(timeoff_type, str) else timeoff_type
        self.notes = notes
        self.status = ApprovalStatus(status) if isinstance(status, str) else status
        self.manager_email = manager_email
        self.manager_approved_at = manager_approved_at
        self.manager_approved_by = manager_approved_by
        self.admin_approved_at = admin_approved_at
        self.admin_approved_by = admin_approved_by
        self.rejected_at = rejected_at
        self.rejected_by = rejected_by
        self.rejection_reason = rejection_reason
        self.calendar_event_id = calendar_event_id
        self.autoresponder_enabled = autoresponder_enabled
        self.manager_task_id = manager_task_id
        self.admin_task_ids = admin_task_ids or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.holiday_region = holiday_region
        self.working_days_count = working_days_count

    @property
    def days_count(self) -> int:
        """
        Calculate number of days in the request (calendar days)
        For working days count, use get_working_days_count()
        """
        return (self.end_date - self.start_date).days + 1

    def get_working_days_count(self, holiday_region: Optional[str] = None) -> int:
        """
        Calculate number of working days in the request
        Excludes weekends (Sat/Sun) and regional public holidays

        Args:
            holiday_region: Regional holiday calendar code

        Returns:
            Number of working days
        """
        from backend.app.services.holiday_service import HolidayService
        return HolidayService.count_working_days(
            self.start_date,
            self.end_date,
            holiday_region
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        def safe_isoformat(dt):
            """Safely convert datetime to ISO format, handling both datetime objects and strings"""
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt  # Already a string
            if isinstance(dt, datetime):
                return dt.isoformat()
            # Firestore DatetimeWithNanoseconds
            return dt.isoformat()

        return {
            'employee_email': self.employee_email,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'timeoff_type': self.timeoff_type.value,
            'notes': self.notes,
            'status': self.status.value,
            'manager_email': self.manager_email,
            'manager_approved_at': safe_isoformat(self.manager_approved_at),
            'manager_approved_by': self.manager_approved_by,
            'admin_approved_at': safe_isoformat(self.admin_approved_at),
            'admin_approved_by': self.admin_approved_by,
            'rejected_at': safe_isoformat(self.rejected_at),
            'rejected_by': self.rejected_by,
            'rejection_reason': self.rejection_reason,
            'calendar_event_id': self.calendar_event_id,
            'autoresponder_enabled': self.autoresponder_enabled,
            'manager_task_id': self.manager_task_id,
            'admin_task_ids': self.admin_task_ids,
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
            'days_count': self.days_count,
            'holiday_region': self.holiday_region,
            'working_days_count': self.working_days_count,
        }

    @classmethod
    def from_dict(cls, request_id: str, data: Dict[str, Any]) -> 'TimeOffRequest':
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
        # Admins can approve if:
        # 1. Status is manager_approved (normal flow)
        # 2. OR status is pending AND user is both manager and admin (skip manager approval step)
        is_admin = user_email in admin_users
        is_manager_approved = self.status == ApprovalStatus.MANAGER_APPROVED
        is_pending_and_is_manager = (
            self.status == ApprovalStatus.PENDING and
            user_email == self.manager_email
        )

        return is_admin and (is_manager_approved or is_pending_and_is_manager)
