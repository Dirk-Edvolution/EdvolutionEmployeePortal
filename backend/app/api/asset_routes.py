"""
Asset request API routes for equipment and inventory management
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService
from backend.app.models import (
    AssetRequest,
    AssetCategory,
    EmployeeAsset,
    AssetStatus,
    AssetAuditLog,
    AuditAction
)
from backend.app.utils import get_credentials_from_session, log_action
from backend.config.settings import ADMIN_USERS, ASSET_CATEGORIES
import logging

logger = logging.getLogger(__name__)

asset_bp = Blueprint('assets', __name__, url_prefix='/api/assets')


@asset_bp.route('/requests', methods=['POST'])
@login_required
def create_asset_request():
    """Create a new asset request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    data = request.json

    # Validate required fields
    required_fields = ['category', 'business_justification']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate category
    if data['category'] not in ASSET_CATEGORIES:
        return jsonify({'error': f'Invalid category. Must be one of: {", ".join(ASSET_CATEGORIES)}'}), 400

    is_misc = data['category'] == 'misc'

    # Validate MISC category fields
    if is_misc:
        if not data.get('custom_description'):
            return jsonify({'error': 'Description required for miscellaneous items'}), 400
        if not data.get('purchase_url'):
            return jsonify({'error': 'Purchase URL required for miscellaneous items'}), 400
        if not data.get('estimated_cost'):
            return jsonify({'error': 'Estimated cost required for miscellaneous items'}), 400

    # Create asset request
    asset_request = AssetRequest(
        employee_email=current_email,
        category=AssetCategory(data['category']),
        business_justification=data['business_justification'],
        is_misc=is_misc,
        custom_description=data.get('custom_description') if is_misc else None,
        purchase_url=data.get('purchase_url') if is_misc else None,
        estimated_cost=float(data['estimated_cost']) if is_misc and data.get('estimated_cost') else None,
        manager_email=employee.manager_email,
    )

    request_id = db.create_asset_request(asset_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.ASSET_CREATE,
        resource_type='asset_request',
        resource_id=request_id,
        details=f'Asset request: {asset_request.display_name}'
    )

    # TODO: Send notification to manager
    if employee.manager_email:
        logger.info(f"Asset approval notification should be sent to {employee.manager_email}")

    response_dict = asset_request.to_dict()
    response_dict['request_id'] = request_id

    return jsonify(response_dict), 201


@asset_bp.route('/requests', methods=['GET'])
@login_required
def get_asset_requests():
    """Get all asset requests for the current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    requests = db.get_employee_asset_requests(current_email)

    return jsonify([
        {**req.to_dict(), 'request_id': rid}
        for rid, req in requests
    ]), 200


@asset_bp.route('/requests/<request_id>', methods=['GET'])
@login_required
def get_asset_request(request_id):
    """Get a specific asset request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset_request = db.get_asset_request(request_id)

    if not asset_request:
        return jsonify({'error': 'Asset request not found'}), 404

    # Check permissions
    if asset_request.employee_email != current_email and not is_admin(current_email):
        return jsonify({'error': 'Unauthorized'}), 403

    response = asset_request.to_dict()
    response['request_id'] = request_id

    return jsonify(response), 200


@asset_bp.route('/requests/<request_id>/approve-manager', methods=['POST'])
@login_required
def approve_asset_manager(request_id):
    """Approve asset request as manager (first tier)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset_request = db.get_asset_request(request_id)

    if not asset_request:
        return jsonify({'error': 'Asset request not found'}), 404

    if not asset_request.can_approve_manager(current_email, asset_request.manager_email):
        return jsonify({'error': 'Cannot approve this request'}), 403

    asset_request.approve_by_manager(current_email)
    db.update_asset_request(request_id, asset_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.ASSET_APPROVE_MANAGER,
        resource_type='asset_request',
        resource_id=request_id,
        details=f'Manager approved: {asset_request.display_name}'
    )

    # TODO: Send notification to admins
    logger.info("Asset approval notification should be sent to admins")

    return jsonify(asset_request.to_dict()), 200


@asset_bp.route('/requests/<request_id>/approve-admin', methods=['POST'])
@login_required
def approve_asset_admin(request_id):
    """Approve asset request as admin (final approval)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset_request = db.get_asset_request(request_id)

    if not asset_request:
        return jsonify({'error': 'Asset request not found'}), 404

    if not asset_request.can_approve_admin(current_email, ADMIN_USERS):
        return jsonify({'error': 'Cannot approve this request'}), 403

    asset_request.approve_by_admin(current_email)
    db.update_asset_request(request_id, asset_request)

    # Create employee asset in inventory
    employee_asset = EmployeeAsset(
        employee_email=asset_request.employee_email,
        asset_request_id=request_id,
        category=asset_request.category.value,
        description=asset_request.display_name,
        purchase_url=asset_request.purchase_url if asset_request.is_misc else None,
        purchase_cost=asset_request.estimated_cost if asset_request.is_misc else None,
    )

    asset_id = db.create_employee_asset(employee_asset)

    # Create audit log for asset creation
    audit_log = AssetAuditLog.create_log(
        asset_id=asset_id,
        changed_by=current_email,
        action='created',
        notes=f'Asset approved and added to inventory from request {request_id}'
    )
    db.create_asset_audit_log(audit_log)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.ASSET_APPROVE_ADMIN,
        resource_type='asset_request',
        resource_id=request_id,
        details=f'Admin approved: {asset_request.display_name}, created asset {asset_id}'
    )

    # TODO: Send notification to employee
    logger.info(f"Asset approval notification should be sent to {asset_request.employee_email}")

    response = asset_request.to_dict()
    response['request_id'] = request_id
    response['asset_id'] = asset_id

    return jsonify(response), 200


@asset_bp.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
def reject_asset(request_id):
    """Reject an asset request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset_request = db.get_asset_request(request_id)

    if not asset_request:
        return jsonify({'error': 'Asset request not found'}), 404

    # Check if user can reject (manager or admin)
    is_manager = asset_request.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_manager or is_user_admin):
        return jsonify({'error': 'Cannot reject this request'}), 403

    data = request.json
    reason = data.get('reason', 'No reason provided')

    asset_request.reject(current_email, reason)
    db.update_asset_request(request_id, asset_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.ASSET_REJECT,
        resource_type='asset_request',
        resource_id=request_id,
        details=f'Rejected: {reason}'
    )

    # TODO: Send notification to employee
    logger.info(f"Asset rejection notification should be sent to {asset_request.employee_email}")

    return jsonify(asset_request.to_dict()), 200


@asset_bp.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    """Get assets for current user or all assets (admin/manager)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    # Check if requesting all assets
    all_assets = request.args.get('all', 'false').lower() == 'true'
    employee_email = request.args.get('employee_email')

    if all_assets or employee_email:
        # Only admins can view all assets or other employees' assets
        if not is_admin(current_email):
            # Managers can view their team's assets
            employee = db.get_employee(current_email)
            if employee and employee_email:
                target_employee = db.get_employee(employee_email)
                if not target_employee or target_employee.manager_email != current_email:
                    return jsonify({'error': 'Unauthorized'}), 403
            else:
                return jsonify({'error': 'Unauthorized'}), 403

    if all_assets:
        assets = db.get_all_employee_assets()
    elif employee_email:
        assets = db.get_employee_assets(employee_email)
    else:
        assets = db.get_employee_assets(current_email)

    return jsonify([
        {**asset.to_dict(), 'asset_id': aid}
        for aid, asset in assets
    ]), 200


@asset_bp.route('/inventory/<asset_id>', methods=['GET'])
@login_required
def get_asset(asset_id):
    """Get a specific asset"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset = db.get_employee_asset(asset_id)

    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permissions
    if asset.employee_email != current_email and not is_admin(current_email):
        # Check if user is manager
        employee = db.get_employee(asset.employee_email)
        if not employee or employee.manager_email != current_email:
            return jsonify({'error': 'Unauthorized'}), 403

    response = asset.to_dict()
    response['asset_id'] = asset_id

    # Include audit trail
    audit_logs = db.get_asset_audit_logs(asset_id)
    response['audit_trail'] = [
        {**log.to_dict(), 'log_id': lid}
        for lid, log in audit_logs
    ]

    return jsonify(response), 200


@asset_bp.route('/inventory/<asset_id>', methods=['PUT'])
@login_required
def update_asset(asset_id):
    """Update an asset (manager or admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset = db.get_employee_asset(asset_id)

    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permissions - must be manager or admin
    employee = db.get_employee(asset.employee_email)
    is_manager = employee and employee.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_manager or is_user_admin):
        return jsonify({'error': 'Only managers and admins can update assets'}), 403

    data = request.json
    old_asset_dict = asset.to_dict()

    # Track changes for audit log
    changes = []

    # Update allowed fields
    if 'status' in data:
        old_status = asset.status.value if asset.status else None
        asset.update_status(AssetStatus(data['status']), data.get('notes'))
        if old_status != data['status']:
            changes.append(AssetAuditLog.create_log(
                asset_id=asset_id,
                changed_by=current_email,
                action='status_changed',
                field_changed='status',
                old_value=old_status,
                new_value=data['status'],
                notes=data.get('notes')
            ))

    if 'current_holder' in data:
        old_holder = asset.current_holder
        asset.transfer_to(data['current_holder'], data.get('notes'))
        if old_holder != data['current_holder']:
            changes.append(AssetAuditLog.create_log(
                asset_id=asset_id,
                changed_by=current_email,
                action='reassigned',
                field_changed='current_holder',
                old_value=old_holder,
                new_value=data['current_holder'],
                notes=data.get('notes')
            ))

    if 'description' in data:
        old_description = asset.description
        asset.description = data['description']
        if old_description != data['description']:
            changes.append(AssetAuditLog.create_log(
                asset_id=asset_id,
                changed_by=current_email,
                action='updated',
                field_changed='description',
                old_value=old_description,
                new_value=data['description']
            ))

    if 'serial_number' in data:
        old_serial = asset.serial_number
        asset.serial_number = data['serial_number']
        if old_serial != data['serial_number']:
            changes.append(AssetAuditLog.create_log(
                asset_id=asset_id,
                changed_by=current_email,
                action='updated',
                field_changed='serial_number',
                old_value=old_serial,
                new_value=data['serial_number']
            ))

    if 'notes' in data and 'status' not in data and 'current_holder' not in data:
        old_notes = asset.notes
        asset.notes = data['notes']
        if old_notes != data['notes']:
            changes.append(AssetAuditLog.create_log(
                asset_id=asset_id,
                changed_by=current_email,
                action='updated',
                field_changed='notes',
                old_value=old_notes,
                new_value=data['notes']
            ))

    # Save asset
    db.update_employee_asset(asset_id, asset)

    # Create audit logs for all changes
    for change in changes:
        db.create_asset_audit_log(change)

    # Log action
    log_action(
        user_email=current_email,
        action='ASSET_INVENTORY_UPDATE',
        resource_type='employee_asset',
        resource_id=asset_id,
        details=f'Updated asset: {len(changes)} change(s)'
    )

    response = asset.to_dict()
    response['asset_id'] = asset_id

    return jsonify(response), 200


@asset_bp.route('/inventory', methods=['POST'])
@login_required
def add_asset_manually():
    """Manually add an asset to inventory (manager or admin only)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    data = request.json

    # Validate required fields
    required_fields = ['employee_email', 'category', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check permissions - must be manager of employee or admin
    target_employee = db.get_employee(data['employee_email'])
    if not target_employee:
        return jsonify({'error': 'Employee not found'}), 404

    is_manager = target_employee.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_manager or is_user_admin):
        return jsonify({'error': 'Only managers and admins can add assets'}), 403

    # Create asset
    employee_asset = EmployeeAsset(
        employee_email=data['employee_email'],
        asset_request_id=None,  # Manually added, no request
        category=data['category'],
        description=data['description'],
        purchase_date=datetime.fromisoformat(data['purchase_date']).date() if data.get('purchase_date') else None,
        purchase_cost=float(data['purchase_cost']) if data.get('purchase_cost') else None,
        serial_number=data.get('serial_number'),
        purchase_url=data.get('purchase_url'),
        notes=data.get('notes'),
    )

    asset_id = db.create_employee_asset(employee_asset)

    # Create audit log
    audit_log = AssetAuditLog.create_log(
        asset_id=asset_id,
        changed_by=current_email,
        action='created',
        notes='Manually added to inventory'
    )
    db.create_asset_audit_log(audit_log)

    # Log action
    log_action(
        user_email=current_email,
        action='ASSET_INVENTORY_ADD',
        resource_type='employee_asset',
        resource_id=asset_id,
        details=f'Manually added asset: {employee_asset.description}'
    )

    response = employee_asset.to_dict()
    response['asset_id'] = asset_id

    return jsonify(response), 201


@asset_bp.route('/pending-approval', methods=['GET'])
@login_required
def get_pending_approvals():
    """Get pending asset requests for current user (manager or admin)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    pending_assets = []

    # Get requests pending manager approval
    manager_requests = db.get_pending_asset_requests_for_manager(current_email)
    pending_assets.extend([
        {**req.to_dict(), 'request_id': rid, 'approval_level': 'manager'}
        for rid, req in manager_requests
    ])

    # Get requests pending admin approval
    if is_admin(current_email):
        admin_requests = db.get_pending_asset_requests_for_admin()
        pending_assets.extend([
            {**req.to_dict(), 'request_id': rid, 'approval_level': 'admin'}
            for rid, req in admin_requests
        ])

    return jsonify(pending_assets), 200


@asset_bp.route('/audit/<asset_id>', methods=['GET'])
@login_required
def get_asset_audit_trail(asset_id):
    """Get audit trail for a specific asset"""
    db = FirestoreService()
    current_email = get_current_user_email()

    asset = db.get_employee_asset(asset_id)

    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    # Check permissions
    if asset.employee_email != current_email and not is_admin(current_email):
        # Check if user is manager
        employee = db.get_employee(asset.employee_email)
        if not employee or employee.manager_email != current_email:
            return jsonify({'error': 'Unauthorized'}), 403

    audit_logs = db.get_asset_audit_logs(asset_id)

    return jsonify([
        {**log.to_dict(), 'log_id': lid}
        for lid, log in audit_logs
    ]), 200
