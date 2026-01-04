"""
Travel request API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService, NotificationService
from backend.app.models.travel_request import TravelRequest, DisbursementType, ApprovalStatus
from backend.app.utils import get_credentials_from_session, log_action
from backend.app.models import AuditAction
from backend.config.settings import ADMIN_USERS, FINANCE_EMAIL
import logging

logger = logging.getLogger(__name__)

travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')


@travel_bp.route('/requests', methods=['POST'])
@login_required
def create_travel_request():
    """Create a new travel request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    data = request.json

    # Validate required fields
    required_fields = ['origin', 'destination', 'start_date', 'end_date', 'purpose', 'expenses', 'total_estimated_cost', 'disbursement_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Parse dates
    try:
        start_date = datetime.fromisoformat(data['start_date']).date()
        end_date = datetime.fromisoformat(data['end_date']).date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Validate dates
    if end_date < start_date:
        return jsonify({'error': 'End date must be after start date'}), 400

    # Validate expenses
    if not isinstance(data['expenses'], list) or len(data['expenses']) == 0:
        return jsonify({'error': 'At least one expense is required'}), 400

    # Create request
    travel_request = TravelRequest(
        employee_email=current_email,
        origin=data['origin'],
        destination=data['destination'],
        start_date=start_date,
        end_date=end_date,
        purpose=data['purpose'],
        expenses=data['expenses'],
        total_estimated_cost=float(data['total_estimated_cost']),
        currency=employee.salary_currency,  # Use employee's payroll currency
        disbursement_type=DisbursementType(data['disbursement_type']),
        manager_email=employee.manager_email,
    )

    request_id = db.create_travel_request(travel_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.CREATE,
        resource_type='travel_request',
        resource_id=request_id,
        details={'destination': data['destination'], 'amount': data['total_estimated_cost']}
    )

    response_dict = travel_request.to_dict()
    response_dict['request_id'] = request_id

    return jsonify(response_dict), 201


@travel_bp.route('/requests', methods=['GET'])
@login_required
def get_my_travel_requests():
    """Get all travel requests for current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    requests = db.get_employee_travel_requests(current_email)

    return jsonify([
        {**req.to_dict(), 'request_id': req_id}
        for req_id, req in requests
    ]), 200


@travel_bp.route('/requests/pending', methods=['GET'])
@login_required
def get_pending_travel_approvals():
    """Get pending travel requests for approval"""
    db = FirestoreService()
    current_email = get_current_user_email()
    current_user_is_admin = is_admin(current_email)

    # Get requests pending manager approval
    employee = db.get_employee(current_email)
    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    manager_requests = db.get_pending_travel_requests_for_manager(current_email)

    # Get requests pending admin approval (if user is admin)
    admin_requests = []
    if current_user_is_admin:
        admin_requests = db.get_pending_travel_requests_for_admin()

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


@travel_bp.route('/requests/<request_id>/approve-manager', methods=['POST'])
@login_required
def approve_travel_as_manager(request_id):
    """Approve travel request as manager"""
    db = FirestoreService()
    current_email = get_current_user_email()

    travel_request = db.get_travel_request(request_id)
    if not travel_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission
    if not travel_request.can_approve_manager(current_email, travel_request.manager_email):
        return jsonify({'error': 'Permission denied'}), 403

    # Approve
    travel_request.approve_by_manager(current_email)
    db.update_travel_request(request_id, travel_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.APPROVE,
        resource_type='travel_request',
        resource_id=request_id,
        details={'approval_level': 'manager'}
    )

    return jsonify(travel_request.to_dict()), 200


@travel_bp.route('/requests/<request_id>/approve-admin', methods=['POST'])
@login_required
def approve_travel_as_admin(request_id):
    """Approve travel request as admin (final approval)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    travel_request = db.get_travel_request(request_id)
    if not travel_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission
    if not travel_request.can_approve_admin(current_email, ADMIN_USERS):
        return jsonify({'error': 'Permission denied'}), 403

    # Approve
    travel_request.approve_by_admin(current_email)
    db.update_travel_request(request_id, travel_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.APPROVE,
        resource_type='travel_request',
        resource_id=request_id,
        details={'approval_level': 'admin', 'final_approval': True}
    )

    # Send email to finance with CC to employee and manager
    try:
        employee = db.get_employee(travel_request.employee_email)
        if employee:
            credentials = get_credentials_from_session()
            if credentials:
                notification_service = NotificationService(credentials)

                # Build expense summary
                expense_summary = ""
                for expense in travel_request.expenses:
                    expense_summary += f"- {expense['category']}: {expense['description']} - {expense['estimated_cost']} {travel_request.currency}\n"

                email_body = f"""
Travel Request Approved

Employee: {employee.full_name} ({travel_request.employee_email})
Manager: {travel_request.manager_email}

Travel Details:
- Origin: {travel_request.origin}
- Destination: {travel_request.destination}
- Dates: {travel_request.start_date} to {travel_request.end_date} ({travel_request.duration_days} days)
- Purpose: {travel_request.purpose}

Expenses:
{expense_summary}

Total Estimated Cost: {travel_request.total_estimated_cost} {travel_request.currency}
Disbursement Type: {travel_request.disbursement_type.value.upper()}

Please process the payment accordingly.
                """

                notification_service.send_email(
                    to_email=FINANCE_EMAIL,
                    subject=f"Travel Approval - {employee.full_name} - {travel_request.destination}",
                    body_text=email_body,
                    # TODO: Add CC to employee and manager
                )

                logger.info(f"Travel approval email sent to {FINANCE_EMAIL} for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to send travel approval email: {e}")
        # Don't fail the approval if email fails

    return jsonify(travel_request.to_dict()), 200


@travel_bp.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
def reject_travel_request(request_id):
    """Reject travel request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    data = request.json

    travel_request = db.get_travel_request(request_id)
    if not travel_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permission (manager or admin can reject)
    current_user_is_admin = is_admin(current_email)
    is_manager = current_email == travel_request.manager_email

    if not (is_manager or current_user_is_admin):
        return jsonify({'error': 'Permission denied'}), 403

    # Reject
    reason = data.get('reason', '')
    travel_request.reject(current_email, reason)
    db.update_travel_request(request_id, travel_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.REJECT,
        resource_type='travel_request',
        resource_id=request_id,
        details={'reason': reason}
    )

    return jsonify(travel_request.to_dict()), 200
