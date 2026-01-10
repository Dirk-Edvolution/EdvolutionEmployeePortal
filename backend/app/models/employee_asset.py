"""
Employee asset model for tracking equipment and tools held by employees
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class AssetStatus(str, Enum):
    """Status of an asset in inventory"""
    ACTIVE = 'active'
    RETURNED = 'returned'
    DAMAGED = 'damaged'
    LOST = 'lost'


class EmployeeAsset:
    """Employee asset model for inventory tracking"""

    def __init__(
        self,
        employee_email: str,
        asset_request_id: Optional[str],
        category: str,
        description: str,
        purchase_date: Optional[datetime] = None,
        purchase_cost: Optional[float] = None,
        status: AssetStatus = AssetStatus.ACTIVE,
        current_holder: Optional[str] = None,
        notes: Optional[str] = None,
        serial_number: Optional[str] = None,
        purchase_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        asset_id: Optional[str] = None,
        **kwargs
    ):
        self.asset_id = asset_id
        self.employee_email = employee_email
        self.asset_request_id = asset_request_id
        self.category = category
        self.description = description
        self.purchase_date = purchase_date or datetime.utcnow()
        self.purchase_cost = float(purchase_cost) if purchase_cost else None
        self.status = AssetStatus(status) if isinstance(status, str) else status
        self.current_holder = current_holder or employee_email
        self.notes = notes
        self.serial_number = serial_number
        self.purchase_url = purchase_url
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

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
            'asset_request_id': self.asset_request_id,
            'category': self.category,
            'description': self.description,
            'purchase_date': safe_isoformat(self.purchase_date),
            'purchase_cost': self.purchase_cost,
            'status': self.status.value,
            'current_holder': self.current_holder,
            'notes': self.notes,
            'serial_number': self.serial_number,
            'purchase_url': self.purchase_url,
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
        }

    @classmethod
    def from_dict(cls, asset_id: str, data: Dict[str, Any]) -> 'EmployeeAsset':
        """Create from Firestore dictionary"""
        data['asset_id'] = asset_id
        return cls(**data)

    def update_status(self, new_status: AssetStatus, notes: Optional[str] = None) -> None:
        """Update asset status"""
        self.status = AssetStatus(new_status) if isinstance(new_status, str) else new_status
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()

    def transfer_to(self, new_holder_email: str, notes: Optional[str] = None) -> None:
        """Transfer asset to another employee"""
        self.current_holder = new_holder_email
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()
