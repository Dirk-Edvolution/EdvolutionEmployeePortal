"""
Employee asset API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService
from backend.app.models.employee_asset import EmployeeAsset, AssetType, AssetCategory, AssetStatus
from backend.app.utils import log_action
from backend.app.models import AuditAction
from backend.config.settings import ADMIN_USERS
import logging

logger = logging.getLogger(__name__)

asset_bp = Blueprint('asset', __name__, url_prefix='/api/assets')


@asset_bp.route('/employees/<email>', methods=['GET'])
@login_required
def get_employee_assets(email):
    """Get all assets for a specific employee"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    # Check permission: must be admin, the employee's manager, or the employee themselves
    employee = db.get_employee(email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email
    is_self = email == current_email

    if not (current_user_is_admin or is_manager or is_self):
        return jsonify({'error': 'Permission denied'}), 403

    # Get assets
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    assets = db.get_employee_assets(email, active_only=active_only)

    return jsonify([
        {**asset.to_dict(), 'asset_id': asset_id}
        for asset_id, asset in assets
    ]), 200


@asset_bp.route('/employees/<email>', methods=['POST'])
@login_required
def create_employee_asset(email):
    """Create new asset for an employee (manager or admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    # Check permission: must be admin or the employee's manager
    employee = db.get_employee(email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email

    if not (current_user_is_admin or is_manager):
        return jsonify({'error': 'Permission denied - Only managers and admins can assign assets'}), 403

    data = request.json

    # Validate required fields
    required_fields = ['asset_type', 'category', 'description', 'assigned_date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Parse assigned_date
    try:
        assigned_date = datetime.fromisoformat(data['assigned_date']).date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Create asset
    asset = EmployeeAsset(
        employee_email=email,
        asset_type=AssetType(data['asset_type']),
        category=AssetCategory(data['category']),
        description=data['description'],
        assigned_date=assigned_date,
        assigned_by=current_email,
        serial_number=data.get('serial_number'),
        cost=float(data['cost']) if data.get('cost') else None,
        currency=data.get('currency', 'USD'),
        status=AssetStatus(data.get('status', 'active')),
        notes=data.get('notes'),
    )

    asset_id = db.create_employee_asset(asset)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.CREATE,
        resource_type='employee_asset',
        resource_id=asset_id,
        details={'employee': email, 'asset_type': data['asset_type'], 'category': data['category']}
    )

    response_dict = asset.to_dict()
    response_dict['asset_id'] = asset_id

    return jsonify(response_dict), 201


@asset_bp.route('/<asset_id>', methods=['GET'])
@login_required
def get_asset(asset_id):
    """Get a specific asset"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    asset = db.get_employee_asset(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permission
    employee = db.get_employee(asset.employee_email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email
    is_self = asset.employee_email == current_email

    if not (current_user_is_admin or is_manager or is_self):
        return jsonify({'error': 'Permission denied'}), 403

    response_dict = asset.to_dict()
    response_dict['asset_id'] = asset_id

    return jsonify(response_dict), 200


@asset_bp.route('/<asset_id>', methods=['PUT'])
@login_required
def update_asset(asset_id):
    """Update an asset (manager or admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    asset = db.get_employee_asset(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permission
    employee = db.get_employee(asset.employee_email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email

    if not (current_user_is_admin or is_manager):
        return jsonify({'error': 'Permission denied - Only managers and admins can update assets'}), 403

    data = request.json

    # Update fields
    if 'description' in data:
        asset.description = data['description']
    if 'serial_number' in data:
        asset.serial_number = data['serial_number']
    if 'cost' in data:
        asset.cost = float(data['cost']) if data['cost'] else None
    if 'currency' in data:
        asset.currency = data['currency']
    if 'status' in data:
        asset.status = AssetStatus(data['status'])
    if 'notes' in data:
        asset.notes = data['notes']
    if 'return_date' in data and data['return_date']:
        asset.return_date = datetime.fromisoformat(data['return_date']).date()

    db.update_employee_asset(asset_id, asset)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.UPDATE,
        resource_type='employee_asset',
        resource_id=asset_id,
        details={'employee': asset.employee_email}
    )

    response_dict = asset.to_dict()
    response_dict['asset_id'] = asset_id

    return jsonify(response_dict), 200


@asset_bp.route('/<asset_id>', methods=['DELETE'])
@login_required
def delete_asset(asset_id):
    """Delete an asset (admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    if not is_admin(current_email):
        return jsonify({'error': 'Permission denied - Only admins can delete assets'}), 403

    asset = db.get_employee_asset(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    db.delete_employee_asset(asset_id)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.DELETE,
        resource_type='employee_asset',
        resource_id=asset_id,
        details={'employee': asset.employee_email}
    )

    return jsonify({'message': 'Asset deleted successfully'}), 200


@asset_bp.route('/<asset_id>/return', methods=['POST'])
@login_required
def return_asset(asset_id):
    """Mark an asset as returned (manager or admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    asset = db.get_employee_asset(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permission
    employee = db.get_employee(asset.employee_email)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = employee.manager_email == current_email

    if not (current_user_is_admin or is_manager):
        return jsonify({'error': 'Permission denied'}), 403

    data = request.json
    return_date = date.today()
    if data.get('return_date'):
        try:
            return_date = datetime.fromisoformat(data['return_date']).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

    asset.return_asset(return_date)
    db.update_employee_asset(asset_id, asset)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.UPDATE,
        resource_type='employee_asset',
        resource_id=asset_id,
        details={'action': 'returned', 'return_date': return_date.isoformat()}
    )

    response_dict = asset.to_dict()
    response_dict['asset_id'] = asset_id

    return jsonify(response_dict), 200
