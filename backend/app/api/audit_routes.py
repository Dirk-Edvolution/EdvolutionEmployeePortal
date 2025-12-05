"""
Audit log API routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.app.utils.auth import login_required, admin_required, get_current_user_email, is_admin
from backend.app.services import FirestoreService

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
