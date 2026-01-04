"""
Employee asset model for tracking company equipment and subscriptions
"""
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum


class AssetType(str, Enum):
    """Type of asset"""
    HARDWARE = 'hardware'
    SUBSCRIPTION = 'subscription'


class AssetCategory(str, Enum):
    """Category of asset"""
    # Hardware
    LAPTOP = 'laptop'
    MONITOR = 'monitor'
    KEYBOARD = 'keyboard'
    MOUSE = 'mouse'
    HEADPHONES = 'headphones'
    CHAIR = 'chair'
    DESK = 'desk'

    # Subscriptions
    WORKSPACE = 'workspace'
    MAILCHIMP = 'mailchimp'
    ODOO = 'odoo'
    GAIN = 'gain'
    OTHER = 'other'


class AssetStatus(str, Enum):
    """Status of asset"""
    ACTIVE = 'active'
    RETURNED = 'returned'
    DAMAGED = 'damaged'


class EmployeeAsset:
    """Employee asset model for tracking company equipment and subscriptions"""

    def __init__(
        self,
        employee_email: str,
        asset_type: AssetType,
        category: AssetCategory,
        description: str,
        assigned_date: date,
        assigned_by: str,
        serial_number: Optional[str] = None,
        cost: Optional[float] = None,
        currency: str = 'USD',
        status: AssetStatus = AssetStatus.ACTIVE,
        notes: Optional[str] = None,
        return_date: Optional[date] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        asset_id: Optional[str] = None,
        **kwargs
    ):
        self.asset_id = asset_id
        self.employee_email = employee_email
        self.asset_type = AssetType(asset_type) if isinstance(asset_type, str) else asset_type
        self.category = AssetCategory(category) if isinstance(category, str) else category
        self.description = description
        self.assigned_date = assigned_date if isinstance(assigned_date, date) else datetime.fromisoformat(assigned_date).date()
        self.assigned_by = assigned_by
        self.serial_number = serial_number
        self.cost = float(cost) if cost is not None else None
        self.currency = currency
        self.status = AssetStatus(status) if isinstance(status, str) else status
        self.notes = notes
        self.return_date = return_date if return_date is None or isinstance(return_date, date) else datetime.fromisoformat(return_date).date()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def is_hardware(self) -> bool:
        """Check if asset is hardware"""
        return self.asset_type == AssetType.HARDWARE

    @property
    def is_subscription(self) -> bool:
        """Check if asset is a subscription"""
        return self.asset_type == AssetType.SUBSCRIPTION

    @property
    def is_active(self) -> bool:
        """Check if asset is currently active"""
        return self.status == AssetStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        def safe_isoformat(dt):
            """Safely convert datetime/date to ISO format"""
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            if isinstance(dt, (datetime, date)):
                return dt.isoformat()
            return dt.isoformat()

        return {
            'employee_email': self.employee_email,
            'asset_type': self.asset_type.value,
            'category': self.category.value,
            'description': self.description,
            'assigned_date': safe_isoformat(self.assigned_date),
            'assigned_by': self.assigned_by,
            'serial_number': self.serial_number,
            'cost': self.cost,
            'currency': self.currency,
            'status': self.status.value,
            'notes': self.notes,
            'return_date': safe_isoformat(self.return_date),
            'created_at': safe_isoformat(self.created_at),
            'updated_at': safe_isoformat(self.updated_at),
        }

    @classmethod
    def from_dict(cls, asset_id: str, data: Dict[str, Any]) -> 'EmployeeAsset':
        """Create from Firestore dictionary"""
        data['asset_id'] = asset_id
        return cls(**data)

    def return_asset(self, return_date: Optional[date] = None) -> None:
        """Mark asset as returned"""
        self.status = AssetStatus.RETURNED
        self.return_date = return_date or date.today()
        self.updated_at = datetime.utcnow()

    def mark_damaged(self, notes: Optional[str] = None) -> None:
        """Mark asset as damaged"""
        self.status = AssetStatus.DAMAGED
        if notes:
            self.notes = f"{self.notes}\n{notes}" if self.notes else notes
        self.updated_at = datetime.utcnow()

    def reactivate(self) -> None:
        """Reactivate a returned or damaged asset"""
        self.status = AssetStatus.ACTIVE
        self.return_date = None
        self.updated_at = datetime.utcnow()
