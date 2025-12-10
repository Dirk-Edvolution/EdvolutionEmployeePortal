"""
Google Chat webhook API routes for time-off approval via Chat
"""
from flask import Blueprint, jsonify, request
from backend.app.services import FirestoreService, ChatAIService
from backend.app.models import ApprovalStatus
from backend.config.settings import ADMIN_USERS
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def create_approval_card(request_id, employee_name, employee_email, start_date, end_date,
                         days_count, timeoff_type, notes, approval_level):
    """
    Create an interactive Google Chat card for time-off approval

    Args:
        request_id: The time-off request ID
        employee_name: Name of the employee
        employee_email: Email of the employee
        start_date: Start date of time-off
        end_date: End date of time-off
        days_count: Number of days
        timeoff_type: Type of time-off (vacation, sick, etc)
        notes: Additional notes from employee
        approval_level: 'manager' or 'admin'
    """
    card = {
        "cardsV2": [{
            "cardId": f"timeoff-approval-{request_id}",
            "card": {
                "header": {
                    "title": f"Time-Off Request Approval ({approval_level.title()})",
                    "subtitle": f"Request from {employee_name}",
                    "imageUrl": "https://fonts.gstatic.com/s/i/productlogos/calendar/v7/192px.svg",
                    "imageType": "CIRCLE"
                },
                "sections": [
                    {
                        "header": "Request Details",
                        "widgets": [
                            {
                                "decoratedText": {
                                    "topLabel": "Employee",
                                    "text": employee_name,
                                    "bottomLabel": employee_email
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Time-Off Type",
                                    "text": timeoff_type.replace('_', ' ').title(),
                                    "icon": {
                                        "knownIcon": "EVENT_SEAT"
                                    }
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Duration",
                                    "text": f"{start_date} to {end_date}",
                                    "bottomLabel": f"{days_count} day(s)",
                                    "icon": {
                                        "knownIcon": "CALENDAR"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }]
    }

    # Add notes section if present
    if notes:
        card["cardsV2"][0]["card"]["sections"].append({
            "header": "Notes",
            "widgets": [
                {
                    "textParagraph": {
                        "text": notes
                    }
                }
            ]
        })

    # Add action buttons
    card["cardsV2"][0]["card"]["sections"].append({
        "widgets": [
            {
                "buttonList": {
                    "buttons": [
                        {
                            "text": "✓ Approve",
                            "onClick": {
                                "action": {
                                    "function": f"approve_{approval_level}",
                                    "parameters": [
                                        {
                                            "key": "request_id",
                                            "value": request_id
                                        }
                                    ]
                                }
                            },
                            "color": {
                                "red": 0.0,
                                "green": 0.7,
                                "blue": 0.0
                            }
                        },
                        {
                            "text": "✗ Reject",
                            "onClick": {
                                "action": {
                                    "function": f"reject_{approval_level}",
                                    "parameters": [
                                        {
                                            "key": "request_id",
                                            "value": request_id
                                        }
                                    ]
                                }
                            },
                            "color": {
                                "red": 0.9,
                                "green": 0.0,
                                "blue": 0.0
                            }
                        }
                    ]
                }
            }
        ]
    })

    return card


def create_simple_text_response(text):
    """Create a simple text response for Google Chat"""
    return {
        "text": text
    }


def create_status_card(title, message, success=True):
    """Create a status card for operation results"""
    color = {"red": 0.0, "green": 0.7, "blue": 0.0} if success else {"red": 0.9, "green": 0.0, "blue": 0.0}
    icon = "CHECK_CIRCLE" if success else "ERROR"

    return {
        "cardsV2": [{
            "cardId": "status-card",
            "card": {
                "header": {
                    "title": title,
                    "subtitle": message
                },
                "sections": [{
                    "widgets": [{
                        "decoratedText": {
                            "text": message,
                            "icon": {
                                "knownIcon": icon
                            }
                        }
                    }]
                }]
            }
        }]
    }


@chat_bp.route('/webhook', methods=['POST'])
def chat_webhook():
    """
    Handle Google Chat webhook events

    This endpoint handles:
    - ADDED_TO_SPACE: When bot is added to a space
    - MESSAGE: When someone messages the bot
    - CARD_CLICKED: When interactive card buttons are clicked
    """
    try:
        event = request.get_json()
        # Log the full event for debugging
        logger.info(f"Received Chat event - Full payload: {event}")

        # Google Chat uses different event structures
        # Check for both 'type' and 'eventType' fields
        event_type = event.get('type') or event.get('eventType')

        # Also check for message directly without type
        if not event_type and event.get('message'):
            event_type = 'MESSAGE'

        logger.info(f"Event type: {event_type}")

        # Handle bot added to space
        if event_type == 'ADDED_TO_SPACE':
            space_type = event.get('space', {}).get('type', 'Unknown')
            return jsonify({
                "text": f"👋 Hello! I'm the Employee Portal Time-Off Approval Bot.\n\n"
                        f"I'll send you time-off approval requests here in {space_type}.\n\n"
                        f"You can approve or reject requests directly from the interactive cards I send."
            })

        # Handle messages
        elif event_type == 'MESSAGE':
            message_text = event.get('message', {}).get('text', '').lower().strip()
            user_name = event.get('user', {}).get('displayName', 'there')

            # Simple command handling
            if 'help' in message_text:
                return jsonify({
                    "text": f"Hello {user_name}! 👋\n\n"
                            f"*Available Commands:*\n"
                            f"• `help` - Show this help message\n"
                            f"• `status` - Check bot status\n"
                            f"• `pending` - Show your pending approvals\n\n"
                            f"*How it works:*\n"
                            f"I'll automatically send you time-off approval requests as interactive cards. "
                            f"Simply click the Approve or Reject buttons to process them instantly!"
                })

            elif 'status' in message_text:
                return jsonify({
                    "text": "✅ Bot is online and ready to handle time-off approvals!"
                })

            elif 'pending' in message_text:
                # Get user email from the event
                user_email = event.get('user', {}).get('email')
                if not user_email:
                    return jsonify({
                        "text": "❌ Could not identify your email address."
                    })

                # Query pending approvals for this user
                db = FirestoreService()

                # Check if user is manager
                manager_requests = db.get_pending_requests_for_manager(user_email)

                # Check if user is admin
                admin_requests = []
                if user_email in ADMIN_USERS:
                    admin_requests = db.get_pending_requests_for_admin()

                total_pending = len(manager_requests) + len(admin_requests)

                if total_pending == 0:
                    return jsonify({
                        "text": f"✅ You have no pending time-off approvals, {user_name}!"
                    })
                else:
                    response_text = f"📋 You have *{total_pending}* pending approval(s):\n\n"

                    if manager_requests:
                        response_text += f"*Manager Approvals:* {len(manager_requests)}\n"

                    if admin_requests:
                        response_text += f"*Admin Approvals:* {len(admin_requests)}\n"

                    response_text += "\nYou'll receive interactive cards for each request."

                    return jsonify({"text": response_text})

            else:
                # Use quick responses for queries
                user_email = event.get('user', {}).get('email')
                if not user_email:
                    return jsonify({
                        "text": "❌ Could not identify your email address."
                    })

                try:
                    # Create AI service instance
                    ai_service = ChatAIService(user_email)

                    # Use quick responses (no Gemini AI for now)
                    intent = ai_service.extract_intent(message_text)
                    quick_response = ai_service.quick_response(intent['intent'])

                    if quick_response:
                        return jsonify({"text": quick_response})

                    # For other queries, provide helpful message
                    return jsonify({
                        "text": f"Hello {user_name}! 👋\n\n"
                                f"I can help you with:\n"
                                f"• `vacation days` - Check your remaining days\n"
                                f"• `my requests` - View your time-off requests\n"
                                f"• `pending` - See pending approvals\n\n"
                                f"Or visit: https://rrhh.edvolution.io"
                    })

                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    return jsonify({
                        "text": f"Hello {user_name}! Type `help` to see what I can do."
                    })

        # Handle card button clicks (interactive actions)
        elif event_type == 'CARD_CLICKED':
            action = event.get('action', {})
            action_name = action.get('actionMethodName')
            parameters = action.get('parameters', [])
            user_email = event.get('user', {}).get('email')
            user_name = event.get('user', {}).get('displayName', 'User')

            # Extract request_id from parameters
            request_id = None
            for param in parameters:
                if param.get('key') == 'request_id':
                    request_id = param.get('value')
                    break

            if not request_id:
                return jsonify(create_status_card(
                    "Error",
                    "Could not find request ID",
                    success=False
                ))

            db = FirestoreService()
            timeoff_request = db.get_timeoff_request(request_id)

            if not timeoff_request:
                return jsonify(create_status_card(
                    "Error",
                    f"Request {request_id} not found",
                    success=False
                ))

            # Handle approval actions
            if action_name == 'approve_manager':
                # Check permissions
                if not timeoff_request.can_approve_manager(user_email, timeoff_request.manager_email):
                    return jsonify(create_status_card(
                        "Permission Denied",
                        "You are not authorized to approve this request as manager",
                        success=False
                    ))

                # Approve as manager
                timeoff_request.approve_by_manager(user_email)
                db.update_timeoff_request(request_id, timeoff_request)

                # TODO: Send notification to admins
                logger.info(f"Manager {user_email} approved request {request_id} via Chat")

                return jsonify(create_status_card(
                    "✓ Approved (Manager)",
                    f"{user_name} approved the time-off request. Forwarded to admin for final approval.",
                    success=True
                ))

            elif action_name == 'approve_admin':
                # Check permissions
                if not timeoff_request.can_approve_admin(user_email, ADMIN_USERS):
                    return jsonify(create_status_card(
                        "Permission Denied",
                        "You are not authorized to approve this request as admin",
                        success=False
                    ))

                # Approve as admin (final approval)
                timeoff_request.approve_by_admin(user_email)
                db.update_timeoff_request(request_id, timeoff_request)

                # TODO: Send notification to employee
                logger.info(f"Admin {user_email} approved request {request_id} via Chat")

                employee = db.get_employee(timeoff_request.employee_email)
                employee_name = employee.full_name if employee else timeoff_request.employee_email

                return jsonify(create_status_card(
                    "✓ Fully Approved",
                    f"{user_name} gave final approval. {employee_name}'s time-off request is now approved!",
                    success=True
                ))

            elif action_name in ['reject_manager', 'reject_admin']:
                # Check permissions
                is_manager = timeoff_request.manager_email == user_email
                is_user_admin = user_email in ADMIN_USERS

                if not (is_manager or is_user_admin):
                    return jsonify(create_status_card(
                        "Permission Denied",
                        "You are not authorized to reject this request",
                        success=False
                    ))

                # Reject the request
                timeoff_request.reject(user_email, reason="Rejected via Google Chat")
                db.update_timeoff_request(request_id, timeoff_request)

                # TODO: Send notification to employee
                logger.info(f"User {user_email} rejected request {request_id} via Chat")

                employee = db.get_employee(timeoff_request.employee_email)
                employee_name = employee.full_name if employee else timeoff_request.employee_email

                return jsonify(create_status_card(
                    "✗ Rejected",
                    f"{user_name} rejected {employee_name}'s time-off request.",
                    success=False
                ))

            else:
                return jsonify(create_status_card(
                    "Unknown Action",
                    f"Unknown action: {action_name}",
                    success=False
                ))

        # Unknown event type or no type field - send a default response
        else:
            if event_type is None:
                logger.warning(f"Event with no type field - sending default help message")
                return jsonify({
                    "text": "👋 Hello! I'm the Edvolution CHRO bot.\n\n"
                            "*Commands:*\n"
                            "• Type `help` for available commands\n"
                            "• Type `status` to check bot status\n"
                            "• Type `pending` to see your pending approvals"
                })
            else:
                logger.warning(f"Unknown Chat event type: {event_type}")
                return jsonify({"text": "Event received"}), 200

    except Exception as e:
        logger.error(f"Error handling Chat webhook: {str(e)}", exc_info=True)
        return jsonify({
            "text": f"❌ Error processing request: {str(e)}"
        }), 500


@chat_bp.route('/send-approval-card', methods=['POST'])
def send_approval_card():
    """
    Helper endpoint to send approval cards to Google Chat

    This would be called by the NotificationService when a new time-off request is created.

    Expected JSON body:
    {
        "space_name": "spaces/...",
        "request_id": "...",
        "employee_name": "...",
        "employee_email": "...",
        "start_date": "...",
        "end_date": "...",
        "days_count": 5,
        "timeoff_type": "vacation",
        "notes": "...",
        "approval_level": "manager"
    }
    """
    try:
        data = request.get_json()

        # Create the approval card
        card = create_approval_card(
            request_id=data['request_id'],
            employee_name=data['employee_name'],
            employee_email=data['employee_email'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            days_count=data['days_count'],
            timeoff_type=data['timeoff_type'],
            notes=data.get('notes', ''),
            approval_level=data['approval_level']
        )

        # TODO: Send card to Google Chat space using Chat API
        # This requires setting up Google Chat API client with credentials
        # For now, return the card structure

        return jsonify({
            "success": True,
            "message": "Approval card created",
            "card": card
        }), 200

    except Exception as e:
        logger.error(f"Error creating approval card: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify the Chat blueprint is working"""
    return jsonify({
        "status": "ok",
        "message": "Google Chat webhook endpoint is active",
        "webhook_url": "/api/chat/webhook"
    }), 200
