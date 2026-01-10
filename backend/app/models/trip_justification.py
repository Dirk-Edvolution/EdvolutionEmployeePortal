"""
Trip justification model for tracking expense justification submissions
Supports multiple resubmissions with admin feedback
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class JustificationStatus(str, Enum):
    """Status of justification review"""
    PENDING_REVIEW = 'pending_review'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class TripJustification:
    """Trip expense justification submission model"""

    def __init__(
        self,
        trip_request_id: str,
        employee_email: str,
        submission_number: int,
        status: JustificationStatus = JustificationStatus.PENDING_REVIEW,
        submitted_at: Optional[datetime] = None,
        submitted_by: Optional[str] = None,
        reviewed_at: Optional[datetime] = None,
        reviewed_by: Optional[str] = None,
        admin_feedback: Optional[str] = None,
        total_claimed: Optional[float] = None,
        total_approved: Optional[float] = None,
        notes: Optional[str] = None,
        justification_id: Optional[str] = None,
        **kwargs
    ):
        self.justification_id = justification_id
        self.trip_request_id = trip_request_id
        self.employee_email = employee_email
        self.submission_number = submission_number
        self.status = JustificationStatus(status) if isinstance(status, str) else status
        self.submitted_at = submitted_at or datetime.utcnow()
        self.submitted_by = submitted_by or employee_email
        self.reviewed_at = reviewed_at
        self.reviewed_by = reviewed_by
        self.admin_feedback = admin_feedback
        self.total_claimed = float(total_claimed) if total_claimed else None
        self.total_approved = float(total_approved) if total_approved else None
        self.notes = notes

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
            'trip_request_id': self.trip_request_id,
            'employee_email': self.employee_email,
            'submission_number': self.submission_number,
            'status': self.status.value,
            'submitted_at': safe_isoformat(self.submitted_at),
            'submitted_by': self.submitted_by,
            'reviewed_at': safe_isoformat(self.reviewed_at),
            'reviewed_by': self.reviewed_by,
            'admin_feedback': self.admin_feedback,
            'total_claimed': self.total_claimed,
            'total_approved': self.total_approved,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, justification_id: str, data: Dict[str, Any]) -> 'TripJustification':
        """Create from Firestore dictionary"""
        data['justification_id'] = justification_id
        return cls(**data)

    def approve(self, admin_email: str, total_approved: float, feedback: Optional[str] = None) -> None:
        """Admin approves the justification"""
        self.status = JustificationStatus.APPROVED
        self.reviewed_by = admin_email
        self.reviewed_at = datetime.utcnow()
        self.total_approved = total_approved
        self.admin_feedback = feedback

    def reject(self, admin_email: str, feedback: str) -> None:
        """Admin rejects the justification with feedback"""
        self.status = JustificationStatus.REJECTED
        self.reviewed_by = admin_email
        self.reviewed_at = datetime.utcnow()
        self.admin_feedback = feedback
