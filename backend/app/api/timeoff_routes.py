"""
Time-off request API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date
from backend.app.utils.auth import login_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService, CalendarService, GmailService, NotificationService
from backend.app.models import TimeOffRequest, TimeOffType, ApprovalStatus, AuditAction
from backend.app.utils import get_credentials_from_session, log_action
from backend.config.settings import ADMIN_USERS
import logging

logger = logging.getLogger(__name__)

timeoff_bp = Blueprint('timeoff', __name__, url_prefix='/api/timeoff')


@timeoff_bp.route('/requests', methods=['POST'])
@login_required
def create_timeoff_request():
    """Create a new time-off request"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404

    data = request.json

    # Validate required fields
    required_fields = ['start_date', 'end_date', 'timeoff_type']
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

    # Create request
    timeoff_request = TimeOffRequest(
        employee_email=current_email,
        start_date=start_date,
        end_date=end_date,
        timeoff_type=TimeOffType(data['timeoff_type']),
        notes=data.get('notes'),
        manager_email=employee.manager_email,
    )

    # Calculate working days based on employee's holiday region
    working_days = timeoff_request.get_working_days_count(employee.holiday_region)

    request_id = db.create_timeoff_request(timeoff_request)

    # Add working days to response
    response_dict = timeoff_request.to_dict()
    response_dict['working_days_count'] = working_days

    # Send notification to manager
    if employee.manager_email:
        try:
            credentials = get_credentials_from_session()
            notification_service = NotificationService(credentials)

            notification_result = notification_service.send_timeoff_approval_notification(
                approver_email=employee.manager_email,
                employee_name=employee.full_name or employee.email,
                employee_email=current_email,
                start_date=str(start_date),
                end_date=str(end_date),
                days_count=working_days,  # Use working days for notifications
                timeoff_type=data['timeoff_type'],
                notes=data.get('notes'),
                request_id=request_id,
                approval_level="manager"
            )

            # Store task ID if task was created
            if isinstance(notification_result, tuple):
                success, task_id = notification_result
                if task_id:
                    timeoff_request.manager_task_id = task_id
                    db.update_timeoff_request(request_id, timeoff_request)
                    logger.info(f"Manager task {task_id} created for request {request_id}")

            logger.info(f"Notification sent to manager {employee.manager_email} for request {request_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to manager: {str(e)}")

    return jsonify({
        'request_id': request_id,
        **response_dict
    }), 201


@timeoff_bp.route('/requests/my', methods=['GET'])
@login_required
def get_my_requests():
    """Get current user's time-off requests"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    year = request.args.get('year', type=int)
    requests = db.get_employee_timeoff_requests(current_email, year)

    # Add working days count to each request
    result = []
    for rid, req in requests:
        req_dict = req.to_dict()
        req_dict['request_id'] = rid
        req_dict['working_days_count'] = req.get_working_days_count(employee.holiday_region if employee else None)
        result.append(req_dict)

    return jsonify(result), 200


@timeoff_bp.route('/requests/<request_id>', methods=['GET'])
@login_required
def get_request(request_id):
    """Get specific time-off request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permissions
    employee = db.get_employee(current_email)
    is_requester = timeoff_request.employee_email == current_email
    is_manager = timeoff_request.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_requester or is_manager or is_user_admin):
        return jsonify({'error': 'Permission denied'}), 403

    return jsonify({'request_id': request_id, **timeoff_request.to_dict()}), 200


@timeoff_bp.route('/requests/pending-approval', methods=['GET'])
@login_required
def get_pending_approvals():
    """Get requests pending approval by current user"""
    db = FirestoreService()
    current_email = get_current_user_email()

    pending_requests = []

    # Get manager approvals
    manager_requests = db.get_pending_requests_for_manager(current_email)
    pending_requests.extend(manager_requests)

    # Get admin approvals if user is admin
    if is_admin(current_email):
        admin_requests = db.get_pending_requests_for_admin()
        pending_requests.extend(admin_requests)

    return jsonify([
        {'request_id': rid, **req.to_dict()}
        for rid, req in pending_requests
    ]), 200


@timeoff_bp.route('/requests/<request_id>/approve-manager', methods=['POST'])
@login_required
def approve_as_manager(request_id):
    """Approve time-off request as manager (first tier)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check if user can approve as manager
    if not timeoff_request.can_approve_manager(current_email, timeoff_request.manager_email):
        return jsonify({'error': 'You are not authorized to approve this request as manager'}), 403

    timeoff_request.approve_by_manager(current_email)
    db.update_timeoff_request(request_id, timeoff_request)

    # Complete manager's task
    if timeoff_request.manager_task_id:
        try:
            credentials = get_credentials_from_session()
            from backend.app.services import TasksService
            tasks_service = TasksService(credentials)
            tasks_service.complete_task(timeoff_request.manager_task_id)
            logger.info(f"Completed manager task {timeoff_request.manager_task_id}")
        except Exception as e:
            logger.error(f"Failed to complete manager task: {str(e)}")

    # Send notification to admins and create tasks
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)
        employee = db.get_employee(timeoff_request.employee_email)

        # Calculate working days for notifications
        working_days = timeoff_request.get_working_days_count(employee.holiday_region if employee else None)

        admin_task_ids = []
        for admin_email in ADMIN_USERS:
            if admin_email:  # Skip empty strings
                notification_result = notification_service.send_timeoff_approval_notification(
                    approver_email=admin_email,
                    employee_name=employee.full_name if employee else timeoff_request.employee_email,
                    employee_email=timeoff_request.employee_email,
                    start_date=str(timeoff_request.start_date),
                    end_date=str(timeoff_request.end_date),
                    days_count=working_days,  # Use working days
                    timeoff_type=timeoff_request.timeoff_type.value,
                    notes=timeoff_request.notes,
                    request_id=request_id,
                    approval_level="admin"
                )

                # Store task IDs if tasks were created
                if isinstance(notification_result, tuple):
                    success, task_id = notification_result
                    if task_id:
                        admin_task_ids.append(task_id)

        # Update request with admin task IDs
        if admin_task_ids:
            timeoff_request.admin_task_ids = admin_task_ids
            db.update_timeoff_request(request_id, timeoff_request)
            logger.info(f"Admin tasks created for request {request_id}: {admin_task_ids}")

        logger.info(f"Notifications sent to admins for request {request_id}")

        # Notify employee about manager approval
        if employee:
            notification_service.send_timeoff_status_notification(
                employee_email=timeoff_request.employee_email,
                employee_name=employee.full_name or employee.email,
                start_date=str(timeoff_request.start_date),
                end_date=str(timeoff_request.end_date),
                days_count=working_days,  # Use working days
                timeoff_type=timeoff_request.timeoff_type.value,
                status='manager_approved'
            )
    except Exception as e:
        logger.error(f"Failed to send notifications: {str(e)}")

    return jsonify({
        'message': 'Request approved by manager, pending admin approval',
        'request_id': request_id,
        **timeoff_request.to_dict()
    }), 200


@timeoff_bp.route('/requests/<request_id>/approve-admin', methods=['POST'])
@login_required
def approve_as_admin(request_id):
    """Approve time-off request as admin (second tier, final)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check if user can approve as admin
    if not timeoff_request.can_approve_admin(current_email, ADMIN_USERS):
        return jsonify({'error': 'You are not authorized to approve this request as admin'}), 403

    timeoff_request.approve_by_admin(current_email)
    db.update_timeoff_request(request_id, timeoff_request)

    # Complete all admin tasks
    if timeoff_request.admin_task_ids:
        try:
            credentials = get_credentials_from_session()
            from backend.app.services import TasksService
            tasks_service = TasksService(credentials)
            for task_id in timeoff_request.admin_task_ids:
                try:
                    tasks_service.complete_task(task_id)
                    logger.info(f"Completed admin task {task_id}")
                except Exception as task_error:
                    logger.error(f"Failed to complete task {task_id}: {task_error}")
        except Exception as e:
            logger.error(f"Failed to complete admin tasks: {str(e)}")

    # Add to calendar and enable autoresponder if requested
    data = request.json or {}
    sync_calendar = data.get('sync_calendar', False)
    enable_autoresponder = data.get('enable_autoresponder', False)

    if sync_calendar or enable_autoresponder:
        employee = db.get_employee(timeoff_request.employee_email)
        # Note: This would need the employee's credentials, not the admin's
        # In practice, this would be triggered by the employee after approval
        pass

    # Send notification to employee
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)
        employee = db.get_employee(timeoff_request.employee_email)

        if employee:
            # Calculate working days for notification
            working_days = timeoff_request.get_working_days_count(employee.holiday_region)

            notification_service.send_timeoff_status_notification(
                employee_email=timeoff_request.employee_email,
                employee_name=employee.full_name or employee.email,
                start_date=str(timeoff_request.start_date),
                end_date=str(timeoff_request.end_date),
                days_count=working_days,  # Use working days
                timeoff_type=timeoff_request.timeoff_type.value,
                status='approved'
            )
            logger.info(f"Approval notification sent to employee for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to employee: {str(e)}")

    return jsonify({
        'message': 'Request fully approved',
        'request_id': request_id,
        **timeoff_request.to_dict()
    }), 200


@timeoff_bp.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    """Reject time-off request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Check permissions - manager or admin can reject
    is_manager = timeoff_request.manager_email == current_email
    is_user_admin = is_admin(current_email)

    if not (is_manager or is_user_admin):
        return jsonify({'error': 'Permission denied'}), 403

    data = request.json or {}
    reason = data.get('reason')

    timeoff_request.reject(current_email, reason)
    db.update_timeoff_request(request_id, timeoff_request)

    # Clean up pending tasks
    try:
        credentials = get_credentials_from_session()
        from backend.app.services import TasksService
        tasks_service = TasksService(credentials)

        # Delete or complete manager task if exists
        if timeoff_request.manager_task_id:
            try:
                tasks_service.delete_task(timeoff_request.manager_task_id)
                logger.info(f"Deleted manager task {timeoff_request.manager_task_id} after rejection")
            except Exception as task_error:
                logger.warning(f"Could not delete manager task: {task_error}")

        # Delete or complete admin tasks if exist
        if timeoff_request.admin_task_ids:
            for task_id in timeoff_request.admin_task_ids:
                try:
                    tasks_service.delete_task(task_id)
                    logger.info(f"Deleted admin task {task_id} after rejection")
                except Exception as task_error:
                    logger.warning(f"Could not delete admin task {task_id}: {task_error}")
    except Exception as e:
        logger.error(f"Failed to clean up tasks after rejection: {str(e)}")

    # Send notification to employee
    try:
        credentials = get_credentials_from_session()
        notification_service = NotificationService(credentials)
        employee = db.get_employee(timeoff_request.employee_email)

        if employee:
            # Calculate working days for notification
            working_days = timeoff_request.get_working_days_count(employee.holiday_region)

            notification_service.send_timeoff_status_notification(
                employee_email=timeoff_request.employee_email,
                employee_name=employee.full_name or employee.email,
                start_date=str(timeoff_request.start_date),
                end_date=str(timeoff_request.end_date),
                days_count=working_days,  # Use working days
                timeoff_type=timeoff_request.timeoff_type.value,
                status='rejected',
                rejection_reason=reason
            )
            logger.info(f"Rejection notification sent to employee for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to employee: {str(e)}")

    return jsonify({
        'message': 'Request rejected',
        'request_id': request_id,
        **timeoff_request.to_dict()
    }), 200


@timeoff_bp.route('/requests/<request_id>', methods=['PUT'])
@login_required
def update_timeoff_request(request_id):
    """Update a time-off request (only if pending and by requester)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Only the requester can update their own request
    if timeoff_request.employee_email != current_email:
        return jsonify({'error': 'Permission denied'}), 403

    # Can only update pending requests
    if timeoff_request.status != ApprovalStatus.PENDING:
        return jsonify({'error': 'Can only update pending requests'}), 400

    data = request.json

    # Update allowed fields
    if 'start_date' in data:
        try:
            timeoff_request.start_date = datetime.fromisoformat(data['start_date']).date()
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400

    if 'end_date' in data:
        try:
            timeoff_request.end_date = datetime.fromisoformat(data['end_date']).date()
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400

    # Validate dates
    if timeoff_request.end_date < timeoff_request.start_date:
        return jsonify({'error': 'End date must be after start date'}), 400

    if 'timeoff_type' in data:
        timeoff_request.timeoff_type = TimeOffType(data['timeoff_type'])

    if 'notes' in data:
        timeoff_request.notes = data['notes']

    # Note: days_count is automatically calculated as a property
    # Working days are calculated dynamically based on employee's holiday_region
    timeoff_request.updated_at = datetime.utcnow()

    db.update_timeoff_request(request_id, timeoff_request)

    return jsonify({
        'message': 'Request updated successfully',
        'request_id': request_id,
        **timeoff_request.to_dict()
    }), 200


@timeoff_bp.route('/requests/<request_id>', methods=['DELETE'])
@login_required
def delete_timeoff_request(request_id):
    """Delete a time-off request (only if pending and by requester)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Only the requester can delete their own request
    if timeoff_request.employee_email != current_email:
        return jsonify({'error': 'Permission denied'}), 403

    # Can only delete pending requests
    if timeoff_request.status != ApprovalStatus.PENDING:
        return jsonify({'error': 'Can only delete pending requests'}), 400

    # Delete the request
    db.timeoff_ref.document(request_id).delete()

    return jsonify({
        'message': 'Request deleted successfully',
        'request_id': request_id
    }), 200


@timeoff_bp.route('/requests/<request_id>/sync-calendar', methods=['POST'])
@login_required
def sync_to_calendar(request_id):
    """Sync approved request to Google Calendar"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Only the requester can sync their own calendar
    if timeoff_request.employee_email != current_email:
        return jsonify({'error': 'Permission denied'}), 403

    # Request must be approved
    if timeoff_request.status != ApprovalStatus.APPROVED:
        return jsonify({'error': 'Request must be approved first'}), 400

    # Sync to calendar
    credentials = get_credentials_from_session()
    calendar_service = CalendarService(credentials)

    employee = db.get_employee(current_email)
    title = f"{timeoff_request.timeoff_type.value.replace('_', ' ').title()}"
    description = timeoff_request.notes or ""

    event_id = calendar_service.create_ooo_event(
        start_date=timeoff_request.start_date,
        end_date=timeoff_request.end_date,
        title=title,
        description=description
    )

    if event_id:
        timeoff_request.calendar_event_id = event_id
        db.update_timeoff_request(request_id, timeoff_request)

        return jsonify({
            'message': 'Successfully synced to Google Calendar',
            'event_id': event_id
        }), 200
    else:
        return jsonify({'error': 'Failed to create calendar event'}), 500


@timeoff_bp.route('/requests/<request_id>/enable-autoresponder', methods=['POST'])
@login_required
def enable_autoresponder(request_id):
    """Enable Gmail auto-responder for approved request"""
    db = FirestoreService()
    current_email = get_current_user_email()

    timeoff_request = db.get_timeoff_request(request_id)
    if not timeoff_request:
        return jsonify({'error': 'Request not found'}), 404

    # Only the requester can enable their own autoresponder
    if timeoff_request.employee_email != current_email:
        return jsonify({'error': 'Permission denied'}), 403

    # Request must be approved
    if timeoff_request.status != ApprovalStatus.APPROVED:
        return jsonify({'error': 'Request must be approved first'}), 400

    # Enable autoresponder
    credentials = get_credentials_from_session()
    gmail_service = GmailService(credentials)

    employee = db.get_employee(current_email)
    message = gmail_service.generate_ooo_message(
        employee_name=employee.full_name,
        start_date=timeoff_request.start_date,
        end_date=timeoff_request.end_date,
        timeoff_type=timeoff_request.timeoff_type.value
    )

    success = gmail_service.enable_vacation_responder(
        start_date=timeoff_request.start_date,
        end_date=timeoff_request.end_date,
        message=message
    )

    if success:
        timeoff_request.autoresponder_enabled = True
        db.update_timeoff_request(request_id, timeoff_request)

        return jsonify({
            'message': 'Gmail auto-responder enabled successfully'
        }), 200
    else:
        return jsonify({'error': 'Failed to enable auto-responder'}), 500


@timeoff_bp.route('/vacation-summary', methods=['GET'])
@login_required
def get_vacation_summary():
    """Get vacation days summary for current user"""
    db = FirestoreService()
    current_email = get_current_user_email()
    employee = db.get_employee(current_email)

    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    year = request.args.get('year', datetime.now().year, type=int)

    used_days = db.calculate_used_vacation_days(current_email, year)
    total_days = employee.vacation_days_per_year
    remaining_days = total_days - used_days

    return jsonify({
        'year': year,
        'total_days': total_days,
        'used_days': used_days,
        'remaining_days': remaining_days,
        'country': employee.country,
        'region': employee.region,
    }), 200
