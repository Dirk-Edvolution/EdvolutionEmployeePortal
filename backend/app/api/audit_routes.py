"""
Audit log API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.app.utils.auth import login_required, admin_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService
from backend.app.services.audit_query_service import AuditQueryService

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')


@audit_bp.route('/logs', methods=['GET'])
@login_required
def get_audit_logs():
    """Get audit logs with optional filters (admins see all, users see their own)"""
    db = FirestoreService()
    current_email = get_current_user_email()

    # Parse query parameters
    user_email = request.args.get('user_email')
    resource_type = request.args.get('resource_type')
    resource_id = request.args.get('resource_id')
    action = request.args.get('action')
    limit = int(request.args.get('limit', 100))
    days = int(request.args.get('days', 30))  # Last N days

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Non-admins can only see their own logs
    if not is_admin(current_email):
        user_email = current_email

    logs = db.get_audit_logs(
        user_email=user_email,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )

    return jsonify([
        {
            'log_id': log_id,
            **log.to_dict(),
            'display_message': log.get_display_message()
        }
        for log_id, log in logs
    ]), 200


@audit_bp.route('/logs/resource/<resource_type>/<resource_id>', methods=['GET'])
@login_required
def get_resource_audit_trail(resource_type, resource_id):
    """Get complete audit trail for a specific resource"""
    db = FirestoreService()
    current_email = get_current_user_email()

    # Check if user has permission to view this resource's audit trail
    # For now, admins can see all, users can see their own resources
    if not is_admin(current_email):
        # Check if this is the user's own resource
        if resource_type == 'employee' and resource_id != current_email:
            return jsonify({'error': 'Permission denied'}), 403
        elif resource_type == 'timeoff_request':
            timeoff_request = db.get_timeoff_request(resource_id)
            if not timeoff_request or timeoff_request.employee_email != current_email:
                return jsonify({'error': 'Permission denied'}), 403

    logs = db.get_resource_audit_trail(resource_type, resource_id)

    return jsonify([
        {
            **log.to_dict(),
            'display_message': log.get_display_message()
        }
        for log in logs
    ]), 200


@audit_bp.route('/logs/summary', methods=['GET'])
@admin_required
def get_audit_summary():
    """Get summary statistics of audit logs (admin only)"""
    db = FirestoreService()

    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get all logs in the period
    all_logs = db.get_audit_logs(
        limit=10000,
        start_date=start_date,
        end_date=end_date
    )

    # Calculate statistics
    action_counts = {}
    user_counts = {}
    resource_type_counts = {}

    for _, log in all_logs:
        # Count by action
        action_counts[log.action.value] = action_counts.get(log.action.value, 0) + 1

        # Count by user
        user_counts[log.user_email] = user_counts.get(log.user_email, 0) + 1

        # Count by resource type
        resource_type_counts[log.resource_type] = resource_type_counts.get(log.resource_type, 0) + 1

    return jsonify({
        'period_days': days,
        'total_logs': len(all_logs),
        'action_counts': action_counts,
        'user_counts': user_counts,
        'resource_type_counts': resource_type_counts,
        'most_active_user': max(user_counts.items(), key=lambda x: x[1])[0] if user_counts else None,
        'most_common_action': max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None,
    }), 200


@audit_bp.route('/query', methods=['POST'])
@login_required
def natural_language_query():
    """Query audit logs with natural language (e.g., 'who approved mayra's vacation last week?')"""
    db = FirestoreService()
    current_email = get_current_user_email()

    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Use Gemini to parse the natural language query
    query_service = AuditQueryService()
    query_params = query_service.parse_natural_query(question)

    # Build date range if 'days' specified
    end_date = datetime.utcnow()
    start_date = None
    if query_params.get('days'):
        start_date = end_date - timedelta(days=query_params['days'])

    # If employee_name is mentioned, look up their email
    target_email = None
    if query_params.get('employee_name'):
        # Search for employee by name
        all_employees = db.list_employees(active_only=False)
        employee_name = query_params['employee_name'].lower()
        for emp in all_employees:
            if employee_name in emp.full_name.lower() or employee_name in emp.email.lower():
                target_email = emp.email
                break

    # Build query parameters
    user_email = query_params.get('user_email')
    action = query_params.get('action')
    resource_type = query_params.get('resource_type')
    resource_id = query_params.get('resource_id')

    # If we found a target employee by name, use their email as resource context
    # For "who approved mayra's vacation", we need to find mayra's timeoff requests
    if target_email and resource_type == 'timeoff_request':
        # Get all timeoff requests for this employee
        timeoff_requests = db.get_employee_timeoff_requests(target_email)
        if timeoff_requests:
            # Get audit logs for each request
            all_matching_logs = []
            for req_id, req in timeoff_requests:
                logs = db.get_resource_audit_trail(resource_type, req_id)
                for log in logs:
                    # Filter by action if specified
                    if action and log.action.value != action:
                        continue
                    # Filter by date range if specified
                    if start_date and log.timestamp < start_date:
                        continue
                    all_matching_logs.append({
                        'user_email': log.user_email,
                        'action': log.action.value,
                        'timestamp': log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp),
                        'details': log.details,
                        'resource_id': req_id
                    })

            # Generate natural language response
            response_text = query_service.generate_natural_response(question, all_matching_logs)

            return jsonify({
                'question': question,
                'answer': response_text,
                'logs': all_matching_logs[:10],  # Return top 10 logs
                'total_matches': len(all_matching_logs)
            }), 200

    # For employee-related queries (e.g., "who modified roberto's manager")
    elif target_email and resource_type == 'employee':
        logs = db.get_resource_audit_trail(resource_type, target_email)
        matching_logs = []
        for log in logs:
            # Filter by action if specified
            if action and log.action.value != action:
                continue
            # Filter by date range if specified
            if start_date and log.timestamp < start_date:
                continue
            matching_logs.append({
                'user_email': log.user_email,
                'action': log.action.value,
                'timestamp': log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp),
                'details': log.details
            })

        response_text = query_service.generate_natural_response(question, matching_logs)

        return jsonify({
            'question': question,
            'answer': response_text,
            'logs': matching_logs[:10],
            'total_matches': len(matching_logs)
        }), 200

    # General query (e.g., "what did dirk do yesterday")
    else:
        # Non-admins can only query their own actions
        if not is_admin(current_email):
            user_email = current_email

        logs = db.get_audit_logs(
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            limit=100,
            start_date=start_date,
            end_date=end_date
        )

        logs_data = [
            {
                'user_email': log.user_email,
                'action': log.action.value,
                'timestamp': log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp),
                'details': log.details
            }
            for _, log in logs
        ]

        response_text = query_service.generate_natural_response(question, logs_data)

        return jsonify({
            'question': question,
            'answer': response_text,
            'logs': logs_data[:10],
            'total_matches': len(logs_data)
        }), 200
