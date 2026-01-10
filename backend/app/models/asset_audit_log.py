"""
Asset audit log model for tracking all changes to employee assets
"""
from datetime import datetime
from typing import Optional, Dict, Any


class AssetAuditLog:
    """Audit log for asset inventory changes"""

    def __init__(
        self,
        asset_id: str,
        changed_by: str,
        action: str,
        field_changed: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        notes: Optional[str] = None,
        changed_at: Optional[datetime] = None,
        log_id: Optional[str] = None,
        **kwargs
    ):
        self.log_id = log_id
        self.asset_id = asset_id
        self.changed_by = changed_by
        self.action = action  # created, updated, status_changed, reassigned, deleted
        self.field_changed = field_changed
        self.old_value = old_value
        self.new_value = new_value
        self.notes = notes
        self.changed_at = changed_at or datetime.utcnow()

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
            'asset_id': self.asset_id,
            'changed_by': self.changed_by,
            'action': self.action,
            'field_changed': self.field_changed,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'notes': self.notes,
            'changed_at': safe_isoformat(self.changed_at),
        }

    @classmethod
    def from_dict(cls, log_id: str, data: Dict[str, Any]) -> 'AssetAuditLog':
        """Create from Firestore dictionary"""
        data['log_id'] = log_id
        return cls(**data)

    @staticmethod
    def create_log(
        asset_id: str,
        changed_by: str,
        action: str,
        field_changed: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        notes: Optional[str] = None
    ) -> 'AssetAuditLog':
        """Factory method to create an audit log entry"""
        return AssetAuditLog(
            asset_id=asset_id,
            changed_by=changed_by,
            action=action,
            field_changed=field_changed,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            notes=notes
        )
