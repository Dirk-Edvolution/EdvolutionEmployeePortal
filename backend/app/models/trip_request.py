"""
Trip request model for tracking travel expense requests and approvals
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum


class TripStatus(str, Enum):
    """Status of trip request workflow"""
    PENDING = 'pending'
    MANAGER_APPROVED = 'manager_approved'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    JUSTIFICATION_SUBMITTED = 'justification_submitted'
    JUSTIFICATION_REJECTED = 'justification_rejected'
    COMPLETED = 'completed'


class TripCurrency(str, Enum):
    """Supported currencies for trip expenses"""
    MXN = 'MXN'
    USD = 'USD'
    EUR = 'EUR'
    COP = 'COP'
    CLP = 'CLP'


class TripRequest:
    """Trip request model with two-tier approval workflow and expense tracking"""

    def __init__(
        self,
        employee_email: str,
        destination: str,
        start_date: date,
        end_date: date,
        purpose: str,
        expected_goal: str,
        estimated_budget: float,
        currency: TripCurrency,
        needs_advance_funding: bool = False,
        advance_amount: Optional[float] = None,
        status: TripStatus = TripStatus.PENDING,
        manager_email: Optional[str] = None,
        manager_approved_at: Optional[datetime] = None,
        manager_approved_by: Optional[str] = None,
        admin_approved_at: Optional[datetime] = None,
        admin_approved_by: Optional[str] = None,
        rejected_at: Optional[datetime] = None,
        rejected_by: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        drive_folder_id: Optional[str] = None,
        drive_folder_url: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        spreadsheet_url: Optional[str] = None,
        manager_task_id: Optional[str] = None,
        admin_task_ids: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        self.request_id = request_id
        self.employee_email = employee_email
        self.destination = destination
        self.start_date = start_date if isinstance(start_date, date) else datetime.fromisoformat(start_date).date()
        self.end_date = end_date if isinstance(end_date, date) else datetime.fromisoformat(end_date).date()
        self.purpose = purpose
        self.expected_goal = expected_goal
        self.estimated_budget = float(estimated_budget)
        self.currency = TripCurrency(currency) if isinstance(currency, str) else currency
        self.needs_advance_funding = needs_advance_funding
        self.advance_amount = float(advance_amount) if advance_amount else None
        self.status = TripStatus(status) if isinstance(status, str) else status
        self.manager_email = manager_email
        self.manager_approved_at = manager_approved_at
        self.manager_approved_by = manager_approved_by
        self.admin_approved_at = admin_approved_at
        self.admin_approved_by = admin_approved_by
        self.rejected_at = rejected_at
        self.rejected_by = rejected_by
        self.rejection_reason = rejection_reason
        self.drive_folder_id = drive_folder_id
        self.drive_folder_url = drive_folder_url
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet_url = spreadsheet_url
        self.manager_task_id = manager_task_id
        self.admin_task_ids = admin_task_ids or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def days_count(self) -> int:
        """Calculate number of days in the trip"""
        return (self.end_date - self.start_date).days + 1

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
            'destination': self.destination,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'purpose': self.purpose,
            'expected_goal': self.expected_goal,
            'estimated_budget': self.estimated_budget,
            'currency': self.currency.value,
            'needs_advance_funding': self.needs_advance_funding,
            'advance_amount': self.advance_amount,
            'status': self.status.value,
            'manager_email': self.manager_email,
            'manager_approved_at': safe_isoformat(self.manager_approved_at),
            'manager_approved_by': self.manager_approved_by,
            'admin_approved_at': safe_isoformat(self.admin_approved_at),
            'admin_approved_by': self.admin_approved_by,
            'rejected_at': safe_isoformat(self.rejected_at),
            'rejected_by': self.rejected_by,
            'rejection_reason': self.rejection_reason,
            'drive_folder_id': self.drive_folder_id,
            'drive_folder_url': self.drive_folder_url,
            'spreadsheet_id': self.spreadsheet_id,
            'spreadsheet_url': self.spreadsheet_url,
            'manager_task_id': self.manager_task_id,
            'admin_task_ids': self.admin_task_ids,
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
            'days_count': self.days_count,
        }

    @classmethod
    def from_dict(cls, request_id: str, data: Dict[str, Any]) -> 'TripRequest':
        """Create from Firestore dictionary"""
        data['request_id'] = request_id
        return cls(**data)

    def approve_by_manager(self, manager_email: str) -> None:
        """Approve request by manager (first tier)"""
        self.status = TripStatus.MANAGER_APPROVED
        self.manager_approved_by = manager_email
        self.manager_approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def approve_by_admin(self, admin_email: str) -> None:
        """Approve request by admin (second tier, final approval)"""
        self.status = TripStatus.APPROVED
        self.admin_approved_by = admin_email
        self.admin_approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self, rejector_email: str, reason: Optional[str] = None) -> None:
        """Reject the request"""
        self.status = TripStatus.REJECTED
        self.rejected_by = rejector_email
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()

    def start_trip(self) -> None:
        """Mark trip as in progress"""
        self.status = TripStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def submit_justification(self) -> None:
        """Employee submits expense justification"""
        self.status = TripStatus.JUSTIFICATION_SUBMITTED
        self.updated_at = datetime.utcnow()

    def reject_justification(self, admin_email: str, reason: str) -> None:
        """Admin rejects expense justification"""
        self.status = TripStatus.JUSTIFICATION_REJECTED
        self.updated_at = datetime.utcnow()

    def complete_trip(self) -> None:
        """Mark trip as completed (justification approved)"""
        self.status = TripStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def can_approve_manager(self, user_email: str, manager_email: str) -> bool:
        """Check if user can approve as manager"""
        return (
            self.status == TripStatus.PENDING and
            user_email == manager_email and
            user_email != self.employee_email
        )

    def can_approve_admin(self, user_email: str, admin_users: List[str]) -> bool:
        """Check if user can approve as admin"""
        is_admin = user_email in admin_users
        is_manager_approved = self.status == TripStatus.MANAGER_APPROVED
        is_pending_and_is_manager = (
            self.status == TripStatus.PENDING and
            user_email == self.manager_email
        )
        return is_admin and (is_manager_approved or is_pending_and_is_manager)
