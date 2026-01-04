"""
Tool request API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService, NotificationService
from backend.app.models.tool_request import ToolRequest, ToolType, ApprovalStatus
from backend.app.utils import get_credentials_from_session, log_action
from backend.app.models import AuditAction
from backend.config.settings import ADMIN_USERS, TOOLS_PROCUREMENT_EMAIL
import logging

logger = logging.getLogger(__name__)

tool_bp = Blueprint('tool', __name__, url_prefix='/api/tool')


@tool_bp.route('/requests', methods=['POST'])
@login_required
def create_tool_request():
    """Create a new tool request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    data = request.json

    # Validate required fields
    required_fields = ['tool_type', 'justification']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate custom tool fields
    if data['tool_type'] == 'custom':
        if not data.get('custom_description') or not data.get('custom_price') or not data.get('custom_link'):
            return jsonify({'error': 'Custom tools require description, price, and link'}), 400

    # Create request
    tool_request = ToolRequest(
        employee_email=current_email,
        tool_type=ToolType(data['tool_type']),
        justification=data['justification'],
        custom_description=data.get('custom_description'),
        custom_price=float(data['custom_price']) if data.get('custom_price') else None,
        custom_link=data.get('custom_link'),
        manager_email=employee.manager_email,
    )

    request_id = db.create_tool_request(tool_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.CREATE,
        resource_type='tool_request',
        resource_id=request_id,
        details={'tool_type': data['tool_type']}
    )

    response_dict = tool_request.to_dict()
    response_dict['request_id'] = request_id

    return jsonify(response_dict), 201


@tool_bp.route('/requests', methods=['GET'])
@login_required
def get_my_tool_requests():
    """Get all tool requests for current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    requests = db.get_employee_tool_requests(current_email)

    return jsonify([
        {**req.to_dict(), 'request_id': req_id}
        for req_id, req in requests
    ]), 200


@tool_bp.route('/requests/pending', methods=['GET'])
@login_required
def get_pending_tool_approvals():
    """Get pending tool requests for approval"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    # Get requests pending manager approval
    employee = db.get_employee(current_email)
    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    manager_requests = db.get_pending_tool_requests_for_manager(current_email)

    # Get requests pending admin approval (if user is admin)
    admin_requests = []
    if current_user_is_admin:
        admin_requests = db.get_pending_tool_requests_for_admin()

    # Combine and format
    all_requests = []

    for req_id, req in manager_requests:
        all_requests.append({
            **req.to_dict(),
            'request_id': req_id,
            'approval_level': 'manager'
        })

    for req_id, req in admin_requests:
        # Don't duplicate if already in manager_requests
        if not any(r['request_id'] == req_id for r in all_requests):
            all_requests.append({
                **req.to_dict(),
                'request_id': req_id,
                'approval_level': 'admin'
            })

    return jsonify(all_requests), 200


@tool_bp.route('/requests/<request_id>/approve-manager', methods=['POST'])
@login_required
def approve_tool_as_manager(request_id):
    """Approve tool request as manager"""
    db = FirestoreService()
    current_email = get_current_user_email()

    tool_request = db.get_tool_request(request_id)
    if not tool_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission
    if not tool_request.can_approve_manager(current_email, tool_request.manager_email):
        return jsonify({'error': 'Permission denied'}), 403

    # Approve
    tool_request.approve_by_manager(current_email)
    db.update_tool_request(request_id, tool_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.APPROVE,
        resource_type='tool_request',
        resource_id=request_id,
        details={'approval_level': 'manager'}
    )

    return jsonify(tool_request.to_dict()), 200


@tool_bp.route('/requests/<request_id>/approve-admin', methods=['POST'])
@login_required
def approve_tool_as_admin(request_id):
    """Approve tool request as admin (final approval)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    tool_request = db.get_tool_request(request_id)
    if not tool_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission
    if not tool_request.can_approve_admin(current_email, ADMIN_USERS):
        return jsonify({'error': 'Permission denied'}), 403

    # Approve
    tool_request.approve_by_admin(current_email)
    db.update_tool_request(request_id, tool_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.APPROVE,
        resource_type='tool_request',
        resource_id=request_id,
        details={'approval_level': 'admin', 'final_approval': True}
    )

    # Send email to procurement with CC to employee and manager
    try:
        employee = db.get_employee(tool_request.employee_email)
        if employee:
            credentials = get_credentials_from_session()
            if credentials:
                notification_service = NotificationService(credentials)

                # Build tool details
                tool_details = f"Tool Type: {tool_request.display_name}\n"
                if tool_request.tool_type == ToolType.CUSTOM:
                    tool_details += f"Description: {tool_request.custom_description}\n"
                    tool_details += f"Price: {tool_request.custom_price}\n"
                    tool_details += f"Product Link: {tool_request.custom_link}\n"

                email_body = f"""
Tool Request Approved

Employee: {employee.full_name} ({tool_request.employee_email})
Manager: {tool_request.manager_email}

{tool_details}

Justification: {tool_request.justification}

Please proceed with procurement.
                """

                notification_service.send_email(
                    to_email=TOOLS_PROCUREMENT_EMAIL,
                    subject=f"Tool Request Approval - {employee.full_name} - {tool_request.display_name}",
                    body_text=email_body,
                    # TODO: Add CC to employee and manager
                )

                logger.info(f"Tool approval email sent to {TOOLS_PROCUREMENT_EMAIL} for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to send tool approval email: {e}")
        # Don't fail the approval if email fails

    return jsonify(tool_request.to_dict()), 200


@tool_bp.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
def reject_tool_request(request_id):
    """Reject tool request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    data = request.json

    tool_request = db.get_tool_request(request_id)
    if not tool_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission (manager or admin can reject)
    current_user_is_admin = is_admin(current_email)
    is_manager = current_email == tool_request.manager_email

    if not (is_manager or current_user_is_admin):
        return jsonify({'error': 'Permission denied'}), 403

    # Reject
    reason = data.get('reason', '')
    tool_request.reject(current_email, reason)
    db.update_tool_request(request_id, tool_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.REJECT,
        resource_type='tool_request',
        resource_id=request_id,
        details={'reason': reason}
    )

    return jsonify(tool_request.to_dict()), 200
