"""
Travel request model for tracking business travel and expense approvals
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum


class DisbursementType(str, Enum):
    """Type of disbursement for travel expenses"""
    ADVANCE = 'advance'  # Money provided before travel
    REIMBURSEMENT = 'reimbursement'  # Money returned after travel


class ExpenseCategory(str, Enum):
    """Categories for travel expenses"""
    AIRFARE = 'airfare'
    ACCOMMODATION = 'accommodation'
    MEALS = 'meals'
    TRANSPORTATION = 'transportation'
    CONFERENCE_FEES = 'conference_fees'
    OTHER = 'other'


class ApprovalStatus(str, Enum):
    """Status of approval workflow"""
    PENDING = 'pending'
    MANAGER_APPROVED = 'manager_approved'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class TravelRequest:
    """Travel request model with two-tier approval workflow"""

    def __init__(
        self,
        employee_email: str,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        purpose: str,
        expenses: List[Dict[str, Any]],  # List of {category, description, estimated_cost}
        total_estimated_cost: float,
        currency: str,
        disbursement_type: DisbursementType,
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
        self.origin = origin
        self.destination = destination
        self.start_date = start_date if isinstance(start_date, date) else datetime.fromisoformat(start_date).date()
        self.end_date = end_date if isinstance(end_date, date) else datetime.fromisoformat(end_date).date()
        self.purpose = purpose
        self.expenses = expenses or []
        self.total_estimated_cost = float(total_estimated_cost)
        self.currency = currency
        self.disbursement_type = DisbursementType(disbursement_type) if isinstance(disbursement_type, str) else disbursement_type
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
    def duration_days(self) -> int:
        """Calculate number of days for the trip"""
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
            'origin': self.origin,
            'destination': self.destination,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'purpose': self.purpose,
            'expenses': self.expenses,
            'total_estimated_cost': self.total_estimated_cost,
            'currency': self.currency,
            'disbursement_type': self.disbursement_type.value,
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
            'duration_days': self.duration_days,
        }

    @classmethod
    def from_dict(cls, request_id: str, data: Dict[str, Any]) -> 'TravelRequest':
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

    def get_expense_summary(self) -> Dict[str, float]:
        """Get expenses grouped by category"""
        summary = {}
        for expense in self.expenses:
            category = expense.get('category', 'other')
            cost = float(expense.get('estimated_cost', 0))
            summary[category] = summary.get(category, 0) + cost
        return summary
