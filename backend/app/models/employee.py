"""
Employee model representing user data from Google Workspace
"""
from datetime import datetime
from typing import Optional, Dict, Any


class Employee:
    """Employee model with Workspace sync capabilities"""

    def __init__(
        self,
        email: str,
        workspace_id: str,
        given_name: str,
        family_name: str,
        full_name: str,
        photo_url: Optional[str] = None,
        manager_email: Optional[str] = None,
        organizational_unit: Optional[str] = None,  # Google Workspace OU path
        department: Optional[str] = None,  # Department/team name
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        holiday_region: Optional[str] = None,  # Regional holiday calendar for time-off calculations
        vacation_days_per_year: int = 20,
        is_admin: bool = False,
        is_active: bool = True,
        # Contract information
        contract_type: Optional[str] = None,  # "permanent", "temporary", "contractor", "intern"
        contract_start_date: Optional[datetime] = None,
        contract_end_date: Optional[datetime] = None,
        contract_document_url: Optional[str] = None,  # Google Drive link
        # Compensation
        salary: Optional[float] = None,
        salary_currency: str = 'USD',
        has_bonus: bool = False,
        bonus_type: Optional[str] = None,  # "quarterly", "annual"
        bonus_percentage: Optional[float] = None,
        has_commission: bool = False,
        commission_notes: Optional[str] = None,
        # Addresses
        personal_address: Optional[str] = None,
        working_address: Optional[str] = None,
        # Personal contacts
        spouse_partner_name: Optional[str] = None,
        spouse_partner_phone: Optional[str] = None,
        spouse_partner_email: Optional[str] = None,
        # Performance evaluations (list of dicts)
        evaluations: Optional[list] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_workspace_sync: Optional[datetime] = None,
        **kwargs
    ):
        self.email = email
        self.workspace_id = workspace_id
        self.given_name = given_name
        self.family_name = family_name
        self.full_name = full_name
        self.photo_url = photo_url
        self.manager_email = manager_email
        self.organizational_unit = organizational_unit
        self.department = department
        self.job_title = job_title
        self.location = location
        self.country = country
        self.region = region
        self.holiday_region = holiday_region
        self.vacation_days_per_year = vacation_days_per_year
        self.is_admin = is_admin
        self.is_active = is_active
        # Contract
        self.contract_type = contract_type
        self.contract_start_date = contract_start_date
        self.contract_end_date = contract_end_date
        self.contract_document_url = contract_document_url
        # Compensation
        self.salary = salary
        self.salary_currency = salary_currency
        self.has_bonus = has_bonus
        self.bonus_type = bonus_type
        self.bonus_percentage = bonus_percentage
        self.has_commission = has_commission
        self.commission_notes = commission_notes
        # Addresses
        self.personal_address = personal_address
        self.working_address = working_address
        # Personal contacts
        self.spouse_partner_name = spouse_partner_name
        self.spouse_partner_phone = spouse_partner_phone
        self.spouse_partner_email = spouse_partner_email
        # Evaluations
        self.evaluations = evaluations or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_workspace_sync = last_workspace_sync

    @property
    def display_name(self) -> str:
        """Return display name with email in parentheses"""
        return f"{self.full_name} ({self.email})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert employee to dictionary for Firestore"""
        return {
            'email': self.email,
            'workspace_id': self.workspace_id,
            'given_name': self.given_name,
            'family_name': self.family_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'photo_url': self.photo_url,
            'manager_email': self.manager_email,
            'organizational_unit': self.organizational_unit,
            'department': self.department,
            'job_title': self.job_title,
            'location': self.location,
            'country': self.country,
            'region': self.region,
            'holiday_region': self.holiday_region,
            'vacation_days_per_year': self.vacation_days_per_year,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            # Contract
            'contract_type': self.contract_type,
            'contract_start_date': self.contract_start_date,
            'contract_end_date': self.contract_end_date,
            'contract_document_url': self.contract_document_url,
            # Compensation
            'salary': self.salary,
            'salary_currency': self.salary_currency,
            'has_bonus': self.has_bonus,
            'bonus_type': self.bonus_type,
            'bonus_percentage': self.bonus_percentage,
            'has_commission': self.has_commission,
            'commission_notes': self.commission_notes,
            # Addresses
            'personal_address': self.personal_address,
            'working_address': self.working_address,
            # Personal contacts
            'spouse_partner_name': self.spouse_partner_name,
            'spouse_partner_phone': self.spouse_partner_phone,
            'spouse_partner_email': self.spouse_partner_email,
            # Evaluations
            'evaluations': self.evaluations,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_workspace_sync': self.last_workspace_sync,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Employee':
        """Create employee from Firestore dictionary"""
        return cls(**data)

    @classmethod
    def from_workspace_user(cls, workspace_user: Dict[str, Any]) -> 'Employee':
        """Create employee from Google Workspace user data"""
        name = workspace_user.get('name', {})

        return cls(
            email=workspace_user['primaryEmail'],
            workspace_id=workspace_user['id'],
            given_name=name.get('givenName', ''),
            family_name=name.get('familyName', ''),
            full_name=name.get('fullName', ''),
            photo_url=workspace_user.get('thumbnailPhotoUrl'),
            organizational_unit=workspace_user.get('orgUnitPath', '').strip('/'),
            is_active=not workspace_user.get('suspended', False),
            last_workspace_sync=datetime.utcnow(),
        )

    def update_from_workspace(self, workspace_user: Dict[str, Any]) -> None:
        """Update employee data from Workspace user"""
        name = workspace_user.get('name', {})

        self.given_name = name.get('givenName', self.given_name)
        self.family_name = name.get('familyName', self.family_name)
        self.full_name = name.get('fullName', self.full_name)
        self.photo_url = workspace_user.get('thumbnailPhotoUrl', self.photo_url)
        self.organizational_unit = workspace_user.get('orgUnitPath', '').strip('/')
        self.is_active = not workspace_user.get('suspended', False)
        self.last_workspace_sync = datetime.utcnow()
        self.updated_at = datetime.utcnow()
