"""
Firestore database service for employee portal
"""
from google.cloud import firestore
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from backend.config.settings import (
    GCP_PROJECT_ID,
    EMPLOYEES_COLLECTION,
    TIMEOFF_REQUESTS_COLLECTION,
)
from backend.app.models import Employee, TimeOffRequest, AuditLog


class FirestoreService:
    """Service for interacting with Firestore database"""

    def __init__(self):
        self.db = firestore.Client(project=GCP_PROJECT_ID)
        self.employees_ref = self.db.collection(EMPLOYEES_COLLECTION)
        self.timeoff_ref = self.db.collection(TIMEOFF_REQUESTS_COLLECTION)
        self.audit_log_ref = self.db.collection('audit_logs')

    # Employee operations
    def get_employee(self, email: str) -> Optional[Employee]:
        """Get employee by email"""
        doc = self.employees_ref.document(email).get()
        if doc.exists:
            return Employee.from_dict(doc.to_dict())
        return None

    def create_employee(self, employee: Employee) -> None:
        """Create new employee record"""
        self.employees_ref.document(employee.email).set(employee.to_dict())

    def update_employee(self, employee: Employee) -> None:
        """Update existing employee record"""
        employee.updated_at = datetime.utcnow()
        self.employees_ref.document(employee.email).update(employee.to_dict())

    def list_employees(self, active_only: bool = True) -> List[Employee]:
        """List all employees"""
        query = self.employees_ref
        if active_only:
            query = query.where('is_active', '==', True)

        docs = query.stream()
        return [Employee.from_dict(doc.to_dict()) for doc in docs]

    def get_employees_by_manager(self, manager_email: str) -> List[Employee]:
        """Get all employees managed by a specific manager"""
        docs = self.employees_ref.where('manager_email', '==', manager_email).stream()
        return [Employee.from_dict(doc.to_dict()) for doc in docs]

    def sync_employee_from_workspace(self, workspace_user: Dict[str, Any]) -> Employee:
        """Sync employee from Workspace, create or update as needed"""
        email = workspace_user['primaryEmail']
        existing = self.get_employee(email)

        if existing:
            existing.update_from_workspace(workspace_user)
            self.update_employee(existing)
            return existing
        else:
            new_employee = Employee.from_workspace_user(workspace_user)
            self.create_employee(new_employee)
            return new_employee

    # Time-off request operations
    def create_timeoff_request(self, request: TimeOffRequest) -> str:
        """Create new time-off request and return its ID"""
        doc_ref = self.timeoff_ref.document()
        doc_ref.set(request.to_dict())
        return doc_ref.id

    def get_timeoff_request(self, request_id: str) -> Optional[TimeOffRequest]:
        """Get time-off request by ID"""
        doc = self.timeoff_ref.document(request_id).get()
        if doc.exists:
            return TimeOffRequest.from_dict(request_id, doc.to_dict())
        return None

    def update_timeoff_request(self, request_id: str, request: TimeOffRequest) -> None:
        """Update time-off request"""
        request.updated_at = datetime.utcnow()
        self.timeoff_ref.document(request_id).update(request.to_dict())

    def get_employee_timeoff_requests(
        self, email: str, year: Optional[int] = None
    ) -> List[tuple[str, TimeOffRequest]]:
        """Get all time-off requests for an employee, optionally filtered by year"""
        query = self.timeoff_ref.where('employee_email', '==', email)

        docs = query.stream()
        requests = [(doc.id, TimeOffRequest.from_dict(doc.id, doc.to_dict())) for doc in docs]

        if year:
            requests = [
                (rid, req) for rid, req in requests
                if req.start_date.year == year or req.end_date.year == year
            ]

        # Sort by created_at, handling both datetime and string formats
        def get_sort_key(item):
            created_at = item[1].created_at
            if created_at is None:
                return datetime.min.replace(tzinfo=None)

            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at)
                    # Remove timezone info to make all datetimes naive for comparison
                    return dt.replace(tzinfo=None) if dt.tzinfo else dt
                except:
                    return datetime.min.replace(tzinfo=None)

            # Handle datetime objects - always remove timezone info
            try:
                if hasattr(created_at, 'tzinfo'):
                    return created_at.replace(tzinfo=None)
                else:
                    # Firestore DatetimeWithNanoseconds or other datetime-like objects
                    return datetime.min.replace(tzinfo=None)
            except:
                return datetime.min.replace(tzinfo=None)

        return sorted(requests, key=get_sort_key, reverse=True)

    def get_pending_requests_for_manager(self, manager_email: str) -> List[tuple[str, TimeOffRequest]]:
        """Get pending requests for employees managed by this manager"""
        query = self.timeoff_ref.where('manager_email', '==', manager_email).where('status', '==', 'pending')
        docs = query.stream()
        return [(doc.id, TimeOffRequest.from_dict(doc.id, doc.to_dict())) for doc in docs]

    def get_pending_requests_for_admin(self) -> List[tuple[str, TimeOffRequest]]:
        """Get requests pending admin approval"""
        query = self.timeoff_ref.where('status', '==', 'manager_approved')
        docs = query.stream()
        return [(doc.id, TimeOffRequest.from_dict(doc.id, doc.to_dict())) for doc in docs]

    def get_approved_requests_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[tuple[str, TimeOffRequest]]:
        """Get approved requests within a date range"""
        query = self.timeoff_ref.where('status', '==', 'approved')
        docs = query.stream()

        requests = [(doc.id, TimeOffRequest.from_dict(doc.id, doc.to_dict())) for doc in docs]

        # Filter by date range
        filtered = [
            (rid, req) for rid, req in requests
            if not (req.end_date < start_date or req.start_date > end_date)
        ]

        return filtered

    def calculate_used_vacation_days(self, email: str, year: int) -> int:
        """Calculate total vacation days used in a specific year"""
        requests = self.get_employee_timeoff_requests(email, year)

        total_days = 0
        for _, req in requests:
            if req.status == 'approved' and req.timeoff_type == 'vacation':
                total_days += req.days_count

        return total_days

    # Audit Log operations
    def create_audit_log(self, audit_log: AuditLog) -> str:
        """Create new audit log entry"""
        doc_ref = self.audit_log_ref.document()
        doc_ref.set(audit_log.to_dict())
        return doc_ref.id

    def get_audit_logs(
        self,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[tuple[str, AuditLog]]:
        """
        Get audit logs with optional filters

        Returns list of tuples (log_id, AuditLog)
        """
        query = self.audit_log_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)

        if user_email:
            query = query.where('user_email', '==', user_email)
        if resource_type:
            query = query.where('resource_type', '==', resource_type)
        if resource_id:
            query = query.where('resource_id', '==', resource_id)
        if action:
            query = query.where('action', '==', action)
        if start_date:
            query = query.where('timestamp', '>=', start_date.isoformat())
        if end_date:
            query = query.where('timestamp', '<=', end_date.isoformat())

        query = query.limit(limit)

        logs = []
        for doc in query.stream():
            logs.append((doc.id, AuditLog.from_dict(doc.id, doc.to_dict())))

        return logs

    def get_resource_audit_trail(self, resource_type: str, resource_id: str) -> List[AuditLog]:
        """Get complete audit trail for a specific resource"""
        logs = self.get_audit_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=1000
        )
        return [log for _, log in logs]
