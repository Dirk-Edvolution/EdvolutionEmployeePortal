"""
Employee management API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from backend.app.utils.auth import login_required, admin_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService, WorkspaceService, HolidayService
from backend.app.utils import get_credentials_from_session

employee_bp = Blueprint('employees', __name__, url_prefix='/api/employees')


@employee_bp.route('/me', methods=['GET'])
@login_required
def get_current_employee():
    """Get current logged-in employee's profile"""
    db = FirestoreService()
    email = get_current_user_email()
    employee = db.get_employee(email)

    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    # Add is_admin flag based on ADMIN_USERS env variable
    profile = employee.to_dict()
    profile['is_admin'] = is_admin(email)

    return jsonify(profile), 200


@employee_bp.route('/me', methods=['PUT'])
@login_required
def update_current_employee():
    """Update current employee's profile"""
    db = FirestoreService()
    email = get_current_user_email()
    employee = db.get_employee(email)

    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    data = request.json

    # Allow employees to update certain fields
    updatable_fields = ['vacation_days_per_year', 'location', 'country', 'region', 'holiday_region']

    # Only admins can update these fields
    admin_fields = ['manager_email', 'department', 'job_title', 'is_admin']

    for field in updatable_fields:
        if field in data:
            setattr(employee, field, data[field])

    # If admin, allow updating admin fields
    if is_admin(email):
        for field in admin_fields:
            if field in data:
                setattr(employee, field, data[field])

    db.update_employee(employee)

    # Sync back to Workspace if admin fields changed
    if is_admin(email) and any(field in data for field in ['manager_email', 'job_title', 'department', 'location']):
        credentials = get_credentials_from_session()
        workspace = WorkspaceService(credentials)
        workspace.update_user_custom_fields(
            email=employee.email,
            manager_email=data.get('manager_email'),
            job_title=data.get('job_title'),
            department=data.get('department'),
            location=data.get('location')
        )

    return jsonify(employee.to_dict()), 200


@employee_bp.route('/', methods=['GET'])
@login_required
def list_employees():
    """List all employees (filtered by permissions) with vacation days info"""
    from datetime import datetime
    db = FirestoreService()
    current_email = get_current_user_email()

    if is_admin(current_email):
        # Admins see all employees
        employees = db.list_employees()
    else:
        # Regular users see their direct reports
        employees = db.get_employees_by_manager(current_email)

    # Enhance each employee with vacation days info
    current_year = datetime.now().year
    employees_data = []
    for emp in employees:
        emp_dict = emp.to_dict()

        # Calculate vacation days used this year (with error handling)
        try:
            used_days = db.calculate_used_vacation_days(emp.email, current_year)
            total_days = emp.vacation_days_per_year or 20
            remaining_days = total_days - used_days

            # Add vacation summary
            emp_dict['vacation_summary'] = {
                'total_days': total_days,
                'used_days': used_days,
                'remaining_days': remaining_days,
                'year': current_year
            }
        except Exception as e:
            # If calculation fails, provide defaults
            total_days = emp.vacation_days_per_year or 20
            emp_dict['vacation_summary'] = {
                'total_days': total_days,
                'used_days': 0,
                'remaining_days': total_days,
                'year': current_year
            }

        employees_data.append(emp_dict)

    return jsonify(employees_data), 200


@employee_bp.route('/<email>', methods=['GET'])
@login_required
def get_employee(email):
    """Get specific employee by email"""
    db = FirestoreService()
    current_email = get_current_user_email()

    # Check permissions
    is_user_admin = is_admin(current_email)
    is_viewing_self = current_email == email

    employee = db.get_employee(email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email

    # Only allow access if: admin, self, or manager
    if not (is_user_admin or is_viewing_self or is_manager):
        return jsonify({'error': 'Permission denied'}), 403

    result = employee.to_dict()
    # Add metadata about viewing permissions
    result['_permissions'] = {
        'can_edit': is_user_admin,  # Only admins can edit
        'is_manager_view': is_manager and not is_user_admin,  # Manager viewing team member (read-only)
        'is_admin': is_user_admin
    }

    return jsonify(result), 200


@employee_bp.route('/<email>', methods=['PUT'])
@admin_required
def update_employee(email):
    """Update employee (admin only - managers have read-only access)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(email)

    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    data = request.json

    # Only admins can update employee fields
    # Managers have read-only access (they can only view their team members)
    updatable_fields = [
        'manager_email', 'department', 'job_title', 'location',
        'country', 'region', 'holiday_region', 'vacation_days_per_year',
        # HHRR fields
        'contract_type', 'contract_start_date', 'contract_end_date', 'contract_document_url',
        'salary', 'salary_currency', 'has_bonus', 'bonus_type', 'bonus_percentage',
        'has_commission', 'commission_notes',
        'personal_address', 'working_address',
        'spouse_partner_name', 'spouse_partner_phone', 'spouse_partner_email'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(employee, field, data[field])

    # IMPORTANT: is_admin is NOT updatable through this endpoint
    # Admin status is determined solely by the ADMIN_USERS environment variable
    # This prevents privilege escalation attacks

    db.update_employee(employee)

    # Sync back to Workspace (only for certain fields)
    if any(field in data for field in ['manager_email', 'job_title', 'department', 'location']):
        credentials = get_credentials_from_session()
        workspace = WorkspaceService(credentials)
        workspace.update_user_custom_fields(
            email=employee.email,
            manager_email=data.get('manager_email'),
            job_title=data.get('job_title'),
            department=data.get('department'),
            location=data.get('location')
        )

    return jsonify(employee.to_dict()), 200


@employee_bp.route('/sync', methods=['POST'])
@admin_required
def sync_from_workspace():
    """Sync ALL users from Google Workspace (admin only) - Refreshes data for all users"""
    credentials = get_credentials_from_session()
    workspace = WorkspaceService(credentials)
    db = FirestoreService()

    try:
        # Sync ALL users from Workspace (no filter)
        synced_count = workspace.sync_all_users_to_portal(db, filter_ou=None)
        return jsonify({
            'success': True,
            'synced_count': synced_count,
            'message': f'Successfully synced {synced_count} users from Google Workspace'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@employee_bp.route('/<email>/change-ou', methods=['POST'])
@admin_required
def change_user_ou(email):
    """Change user's Organizational Unit (admin only)"""
    from backend.config.settings import AVAILABLE_OUS

    data = request.json
    ou_key = data.get('ou_key')  # 'employees', 'external', or 'others'

    if not ou_key or ou_key not in AVAILABLE_OUS:
        return jsonify({'error': f'Invalid OU. Must be one of: {list(AVAILABLE_OUS.keys())}'}), 400

    ou_path = AVAILABLE_OUS[ou_key]

    credentials = get_credentials_from_session()
    workspace = WorkspaceService(credentials)
    db = FirestoreService()

    try:
        # Move user in Workspace
        success = workspace.move_user_to_ou(email, ou_path)
        if not success:
            return jsonify({'error': 'Failed to move user in Workspace'}), 500

        # Update employee record in Firestore
        employee = db.get_employee(email)
        if employee:
            employee.organizational_unit = ou_path.strip('/')
            employee.updated_at = datetime.utcnow()
            db.update_employee(employee)

        return jsonify({
            'success': True,
            'message': f'Successfully moved {email} to {ou_path}',
            'ou_path': ou_path
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@employee_bp.route('/team', methods=['GET'])
@login_required
def get_team():
    """Get employees managed by current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    team_members = db.get_employees_by_manager(current_email)

    return jsonify([emp.to_dict() for emp in team_members]), 200


@employee_bp.route('/<email>/evaluations', methods=['POST'])
@login_required
def add_evaluation(email):
    """Add performance evaluation (manager or manager's manager only)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(email)

    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    # Check if current user is the manager or manager's manager
    is_manager = employee.manager_email == current_email
    is_managers_manager = False
    if employee.manager_email:
        manager = db.get_employee(employee.manager_email)
        if manager and manager.manager_email == current_email:
            is_managers_manager = True

    if not (is_admin(current_email) or is_manager or is_managers_manager):
        return jsonify({'error': 'Permission denied'}), 403

    data = request.json
    evaluation = {
        'date': datetime.utcnow().isoformat(),
        'evaluator_email': current_email,
        'evaluation_text': data.get('evaluation_text', ''),
        'rating': data.get('rating'),  # Optional numeric rating
    }

    if not employee.evaluations:
        employee.evaluations = []
    employee.evaluations.append(evaluation)
    employee.updated_at = datetime.utcnow()

    db.update_employee(employee)

    return jsonify({'success': True, 'evaluation': evaluation}), 201


@employee_bp.route('/holiday-regions', methods=['GET'])
def get_holiday_regions():
    """Get list of available holiday regions for time-off calculations"""
    regions = HolidayService.get_available_regions()
    return jsonify({'regions': regions}), 200


@employee_bp.route('/holiday-regions/<region_code>/holidays/<int:year>', methods=['GET'])
def get_region_holidays(region_code: str, year: int):
    """
    Get all holidays for a specific region and year

    Args:
        region_code: Holiday region code (e.g., 'madrid', 'mexico')
        year: Year to get holidays for
    """
    holidays = HolidayService.get_year_holidays(year, region_code)

    # Convert date objects to ISO format strings
    holidays_serialized = [
        {
            'date': h['date'].isoformat(),
            'name': h['name'],
            'is_weekend': h['is_weekend']
        }
        for h in holidays
    ]

    return jsonify({
        'region': region_code,
        'year': year,
        'holidays': holidays_serialized
    }), 200
