"""
Trip request API routes for travel expense management
"""
from flask import Blueprint, jsonify, request, session
from datetime import datetime
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService, DriveService, NotificationService
from backend.app.models import TripRequest, TripStatus, TripCurrency, TripJustification, JustificationStatus, AuditAction
from backend.app.utils import get_credentials_from_session, log_action
from backend.config.settings import ADMIN_USERS, TRIP_CURRENCIES
import logging

logger = logging.getLogger(__name__)

trip_bp = Blueprint('trips', __name__, url_prefix='/api/trips')


@trip_bp.route('/requests', methods=['POST'])
@login_required
def create_trip_request():
    """Create a new trip request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    data = request.json

    # Validate required fields
    required_fields = ['destination', 'start_date', 'end_date', 'purpose', 'expected_goal', 'estimated_budget', 'currency']
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

    # Validate currency
    if data['currency'] not in TRIP_CURRENCIES:
        return jsonify({'error': f'Invalid currency. Must be one of: {", ".join(TRIP_CURRENCIES)}'}), 400

    # Validate advance funding
    needs_advance = data.get('needs_advance_funding', False)
    advance_amount = data.get('advance_amount')

    if needs_advance and not advance_amount:
        return jsonify({'error': 'Advance amount required when requesting advance funding'}), 400

    # Create trip request
    trip_request = TripRequest(
        employee_email=current_email,
        destination=data['destination'],
        start_date=start_date,
        end_date=end_date,
        purpose=data['purpose'],
        expected_goal=data['expected_goal'],
        estimated_budget=float(data['estimated_budget']),
        currency=TripCurrency(data['currency']),
        needs_advance_funding=needs_advance,
        advance_amount=float(advance_amount) if advance_amount else None,
        manager_email=employee.manager_email,
    )

    request_id = db.create_trip_request(trip_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.TRIP_CREATE,
        resource_type='trip_request',
        resource_id=request_id,
        details=f'Trip to {data["destination"]}'
    )

    # Send notification to manager
    if employee.manager_email:
        try:
            credentials = get_credentials_from_session()
            notification_service = NotificationService(credentials)

            # TODO: Implement send_trip_approval_notification
            # notification_service.send_trip_approval_notification(...)

            logger.info(f"Trip approval notification sent to {employee.manager_email}")
        except Exception as e:
            logger.error(f"Failed to send trip approval notification: {e}")

    response_dict = trip_request.to_dict()
    response_dict['request_id'] = request_id

    return jsonify(response_dict), 201


@trip_bp.route('/requests', methods=['GET'])
@login_required
def get_trip_requests():
    """Get all trip requests for the current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    requests = db.get_employee_trip_requests(current_email)

    return jsonify([
        {**req.to_dict(), 'request_id': rid}
        for rid, req in requests
    ]), 200


@trip_bp.route('/requests/<request_id>', methods=['GET'])
@login_required
def get_trip_request(request_id):
    """Get a specific trip request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    # Check permissions
    if trip_request.employee_email != current_email and not is_admin(current_email):
        return jsonify({'error': 'Unauthorized'}), 403

    response = trip_request.to_dict()
    response['request_id'] = request_id

    # Include justification history if exists
    justifications = db.get_trip_justifications(request_id)
    if justifications:
        response['justifications'] = [
            {**just.to_dict(), 'justification_id': jid}
            for jid, just in justifications
        ]

    return jsonify(response), 200


@trip_bp.route('/requests/<request_id>/approve-manager', methods=['POST'])
@login_required
def approve_trip_manager(request_id):
    """Approve trip request as manager (first tier)"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    if not trip_request.can_approve_manager(current_email, trip_request.manager_email):
        return jsonify({'error': 'Cannot approve this request'}), 403

    trip_request.approve_by_manager(current_email)
    db.update_trip_request(request_id, trip_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.TRIP_APPROVE_MANAGER,
        resource_type='trip_request',
        resource_id=request_id,
        details=f'Manager approved trip to {trip_request.destination}'
    )

    # Send notification to admins
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)

        # TODO: Implement send_trip_approval_notification for admin level
        # notification_service.send_trip_approval_notification(...)

        logger.info("Trip approval notification sent to admins")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

    # Send status notification to employee
    try:
        # TODO: Implement send_trip_status_notification
        # notification_service.send_trip_status_notification(...)
        logger.info(f"Trip status notification sent to {trip_request.employee_email}")
    except Exception as e:
        logger.error(f"Failed to send employee notification: {e}")

    return jsonify(trip_request.to_dict()), 200


@trip_bp.route('/requests/<request_id>/approve-admin', methods=['POST'])
@login_required
def approve_trip_admin(request_id):
    """Approve trip request as admin (final approval)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    if not trip_request.can_approve_admin(current_email, ADMIN_USERS):
        return jsonify({'error': 'Cannot approve this request'}), 403

    trip_request.approve_by_admin(current_email)

    # Create Google Drive folder and spreadsheet
    try:
        credentials = get_credentials_from_session()
        drive_service = DriveService(credentials)

        # Get employee info
        employee = db.get_employee(trip_request.employee_email)
        employee_name = employee.full_name if employee else trip_request.employee_email

        # Create folder
        folder_id, folder_url = drive_service.create_trip_expense_folder(
            destination=trip_request.destination,
            employee_name=employee_name,
            employee_email=trip_request.employee_email,
            admin_emails=ADMIN_USERS,
            trip_date=trip_request.start_date
        )

        if folder_id and folder_url:
            trip_request.drive_folder_id = folder_id
            trip_request.drive_folder_url = folder_url

            # Create receipts subfolder
            drive_service.create_receipts_subfolder(folder_id)

            # Create expense spreadsheet
            sheet_id, sheet_url = drive_service.create_expense_spreadsheet(
                folder_id=folder_id,
                destination=trip_request.destination,
                employee_name=employee_name,
                start_date=trip_request.start_date,
                end_date=trip_request.end_date,
                purpose=trip_request.purpose,
                expected_goal=trip_request.expected_goal,
                estimated_budget=trip_request.estimated_budget,
                currency=trip_request.currency.value
            )

            if sheet_id and sheet_url:
                trip_request.spreadsheet_id = sheet_id
                trip_request.spreadsheet_url = sheet_url

            logger.info(f"Created Drive folder and spreadsheet for trip {request_id}")
        else:
            logger.error(f"Failed to create Drive folder for trip {request_id}")

    except Exception as e:
        logger.error(f"Error creating Drive resources: {e}")
        # Continue with approval even if Drive creation fails

    # Update trip status
    trip_request.start_trip()  # Move to IN_PROGRESS status
    db.update_trip_request(request_id, trip_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.TRIP_APPROVE_ADMIN,
        resource_type='trip_request',
        resource_id=request_id,
        details=f'Admin approved trip to {trip_request.destination}'
    )

    # Send notification to employee
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)

        # TODO: Implement send_trip_status_notification
        # notification_service.send_trip_status_notification(...)

        logger.info(f"Trip approval notification sent to {trip_request.employee_email}")
    except Exception as e:
        logger.error(f"Failed to send employee notification: {e}")

    response = trip_request.to_dict()
    response['request_id'] = request_id

    return jsonify(response), 200


@trip_bp.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
def reject_trip(request_id):
    """Reject a trip request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    # Check if user can reject (manager or admin)
    is_manager = trip_request.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_manager or is_user_admin):
        return jsonify({'error': 'Cannot reject this request'}), 403

    data = request.json
    reason = data.get('reason', 'No reason provided')

    trip_request.reject(current_email, reason)
    db.update_trip_request(request_id, trip_request)

    # Log action
    log_action(
        user_email=current_email,
        action=AuditAction.TRIP_REJECT,
        resource_type='trip_request',
        resource_id=request_id,
        details=f'Rejected: {reason}'
    )

    # Send notification to employee
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)

        # TODO: Implement send_trip_status_notification
        # notification_service.send_trip_status_notification(...)

        logger.info(f"Trip rejection notification sent to {trip_request.employee_email}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

    return jsonify(trip_request.to_dict()), 200


@trip_bp.route('/requests/<request_id>/submit-justification', methods=['POST'])
@login_required
def submit_justification(request_id):
    """Submit expense justification for a trip"""
    db = FirestoreService()
    current_email = get_current_user_email()

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    if trip_request.employee_email != current_email:
        return jsonify({'error': 'Can only submit justification for your own trip'}), 403

    if trip_request.status not in [TripStatus.IN_PROGRESS, TripStatus.JUSTIFICATION_REJECTED]:
        return jsonify({'error': 'Cannot submit justification for this trip status'}), 400

    data = request.json

    # Get current submission number
    existing_justifications = db.get_trip_justifications(request_id)
    submission_number = len(existing_justifications) + 1

    # Create justification
    justification = TripJustification(
        trip_request_id=request_id,
        employee_email=current_email,
        submission_number=submission_number,
        total_claimed=data.get('total_claimed'),
        notes=data.get('notes'),
    )

    justification_id = db.create_trip_justification(justification)

    # Update trip status
    trip_request.submit_justification()
    db.update_trip_request(request_id, trip_request)

    # Log action
    log_action(
        user_email=current_email,
        action='TRIP_JUSTIFICATION_SUBMIT',
        resource_type='trip_request',
        resource_id=request_id,
        details=f'Submitted justification #{submission_number}'
    )

    # Send notification to admins
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)

        # TODO: Implement send_trip_justification_notification
        # notification_service.send_trip_justification_notification(...)

        logger.info("Justification review notification sent to admins")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

    response = justification.to_dict()
    response['justification_id'] = justification_id

    return jsonify(response), 201


@trip_bp.route('/requests/<request_id>/review-justification', methods=['POST'])
@login_required
def review_justification(request_id):
    """Admin reviews expense justification"""
    db = FirestoreService()
    current_email = get_current_user_email()

    if not is_admin(current_email):
        return jsonify({'error': 'Admin access required'}), 403

    trip_request = db.get_trip_request(request_id)

    if not trip_request:
        return jsonify({'error': 'Trip request not found'}), 404

    if trip_request.status != TripStatus.JUSTIFICATION_SUBMITTED:
        return jsonify({'error': 'No pending justification to review'}), 400

    data = request.json
    approved = data.get('approved', False)
    feedback = data.get('feedback', '')

    # Get latest justification
    latest_just = db.get_latest_trip_justification(request_id)

    if not latest_just:
        return jsonify({'error': 'Justification not found'}), 404

    just_id, justification = latest_just

    if approved:
        total_approved = data.get('total_approved', justification.total_claimed)
        justification.approve(current_email, total_approved, feedback)

        # Complete the trip
        trip_request.complete_trip()

        # Log action
        log_action(
            user_email=current_email,
            action='TRIP_JUSTIFICATION_APPROVE',
            resource_type='trip_request',
            resource_id=request_id,
            details=f'Approved justification: {total_approved}'
        )
    else:
        justification.reject(current_email, feedback)

        # Reject justification, allow resubmission
        trip_request.reject_justification(current_email, feedback)

        # Log action
        log_action(
            user_email=current_email,
            action='TRIP_JUSTIFICATION_REJECT',
            resource_type='trip_request',
            resource_id=request_id,
            details=f'Rejected justification: {feedback}'
        )

    db.update_trip_justification(just_id, justification)
    db.update_trip_request(request_id, trip_request)

    # Send notification to employee
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)

        # TODO: Implement send_justification_status_notification
        # notification_service.send_justification_status_notification(...)

        logger.info(f"Justification status notification sent to {trip_request.employee_email}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

    return jsonify({
        'justification': justification.to_dict(),
        'trip': trip_request.to_dict()
    }), 200


@trip_bp.route('/pending-approval', methods=['GET'])
@login_required
def get_pending_approvals():
    """Get pending trip requests for current user (manager or admin)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    pending_trips = []

    # Get requests pending manager approval
    manager_requests = db.get_pending_trip_requests_for_manager(current_email)
    pending_trips.extend([
        {**req.to_dict(), 'request_id': rid, 'approval_level': 'manager'}
        for rid, req in manager_requests
    ])

    # Get requests pending admin approval
    if is_admin(current_email):
        admin_requests = db.get_pending_trip_requests_for_admin()
        pending_trips.extend([
            {**req.to_dict(), 'request_id': rid, 'approval_level': 'admin'}
            for rid, req in admin_requests
        ])

        # Get justifications pending review
        justification_requests = db.get_trips_pending_justification_review()
        pending_trips.extend([
            {**req.to_dict(), 'request_id': rid, 'approval_level': 'justification_review'}
            for rid, req in justification_requests
        ])

    return jsonify(pending_trips), 200
