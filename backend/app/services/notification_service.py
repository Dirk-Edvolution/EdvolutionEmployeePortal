"""
Notification service for Google Chat and Email
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Optional, List, Dict, Any
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.services.tasks_service import TasksService
from backend.config.settings import ENABLE_CHAT_NOTIFICATIONS, ENABLE_TASK_NOTIFICATIONS, TASK_DUE_DAYS, NOTIFICATION_RETRY_ATTEMPTS
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via Google Chat and Gmail"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials  # User credentials (for their own actions)
        self.notification_credentials = None  # Dedicated notification account credentials
        self.chat_service = None
        self.gmail_service = None
        self.tasks_service = None

    def _get_notification_credentials(self):
        """
        Load credentials for the dedicated notification account (hola@edvolution.io)
        from Google Secret Manager

        Returns:
            Credentials object or None if not available
        """
        if self.notification_credentials:
            return self.notification_credentials

        try:
            from google.cloud import secretmanager
            from google.oauth2.credentials import Credentials as OAuth2Credentials
            import json
            import os

            # Check if we have a notification account email configured
            notification_email = os.getenv('NOTIFICATION_ACCOUNT_EMAIL', 'hola@edvolution.io')

            # Try to load credentials from Secret Manager
            try:
                client = secretmanager.SecretManagerServiceClient()
                project_id = os.getenv('GCP_PROJECT_ID', 'edvolution-admon')
                secret_name = f"projects/{project_id}/secrets/notification-account-credentials/versions/latest"

                response = client.access_secret_version(request={"name": secret_name})
                credentials_json = json.loads(response.payload.data.decode('UTF-8'))

                # Create OAuth2 credentials from the JSON
                self.notification_credentials = OAuth2Credentials(
                    token=credentials_json.get('token'),
                    refresh_token=credentials_json.get('refresh_token'),
                    token_uri=credentials_json.get('token_uri'),
                    client_id=credentials_json.get('client_id'),
                    client_secret=credentials_json.get('client_secret'),
                    scopes=credentials_json.get('scopes')
                )

                logger.info(f"Loaded notification credentials for {notification_email} from Secret Manager")
                return self.notification_credentials

            except Exception as secret_error:
                logger.warning(f"Could not load notification credentials from Secret Manager: {secret_error}")
                logger.info("Falling back to user credentials for notifications")
                return None

        except Exception as e:
            logger.error(f"Error getting notification credentials: {e}")
            return None

    def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry a function with exponential backoff

        Args:
            func: Function to retry
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            Result from function call

        Raises:
            Last exception if all retries fail
        """
        max_attempts = NOTIFICATION_RETRY_ATTEMPTS
        backoff_delays = [60, 300, 900]  # 1 min, 5 min, 15 min

        last_error = None
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")

        raise last_error

    def _get_chat_service(self, impersonate_user=None):
        """
        Lazy load Google Chat service using Application Default Credentials for bot operations

        Args:
            impersonate_user: Optional user email to impersonate using domain-wide delegation

        Returns:
            Google Chat API service
        """
        # If impersonating a user, create a new delegated credential
        if impersonate_user:
            try:
                from google.auth import default
                from google.auth.transport.requests import Request

                # Get default credentials (service account)
                credentials, project = default(scopes=[
                    'https://www.googleapis.com/auth/chat.messages',
                    'https://www.googleapis.com/auth/chat.spaces'
                ])

                # Check if credentials support delegation
                if hasattr(credentials, 'with_subject'):
                    # Create delegated credentials to act as the user
                    delegated_credentials = credentials.with_subject(impersonate_user)

                    if not delegated_credentials.valid:
                        delegated_credentials.refresh(Request())

                    chat_service = build('chat', 'v1', credentials=delegated_credentials)
                    logger.info(f"Initialized Chat service with domain-wide delegation as {impersonate_user}")
                    return chat_service
                else:
                    logger.warning(f"Credentials do not support domain-wide delegation for {impersonate_user}")
            except Exception as e:
                logger.error(f"Failed to create delegated credentials for {impersonate_user}: {e}")

        # Standard bot service (for webhook responses)
        if not self.chat_service:
            from google.auth import default
            from google.auth.transport.requests import Request

            try:
                # Use ADC with chat.bot scope for bot operations
                credentials, project = default(scopes=['https://www.googleapis.com/auth/chat.bot'])

                # Refresh credentials if needed
                if not credentials.valid:
                    credentials.refresh(Request())

                self.chat_service = build('chat', 'v1', credentials=credentials)
                logger.info("Initialized Chat service with Application Default Credentials (bot scope)")
            except Exception as e:
                logger.warning(f"Could not initialize Chat service with ADC, falling back to user credentials: {e}")
                # Fallback to user credentials if ADC not available (local development)
                self.chat_service = build('chat', 'v1', credentials=self.credentials)

        return self.chat_service

    def _get_gmail_service(self):
        """
        Lazy load Gmail service using service account with domain-wide delegation

        Returns Gmail service authenticated as hola@edvolution.io via service account impersonation
        """
        if not self.gmail_service:
            try:
                from google.auth import default
                from google.auth.transport.requests import Request
                import os

                # Get the email to impersonate (default: hola@edvolution.io)
                impersonate_email = os.getenv('NOTIFICATION_ACCOUNT_EMAIL', 'hola@edvolution.io')

                # Use Application Default Credentials (service account in production)
                credentials, project = default()

                # Check if credentials support delegation (service account)
                if hasattr(credentials, 'with_subject'):
                    # Create delegated credentials to act as the notification account
                    scopes = [
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.settings.basic',
                        'https://www.googleapis.com/auth/gmail.settings.sharing'
                    ]
                    delegated_credentials = credentials.with_subject(impersonate_email).with_scopes(scopes)

                    if not delegated_credentials.valid:
                        delegated_credentials.refresh(Request())

                    self.gmail_service = build('gmail', 'v1', credentials=delegated_credentials)
                    logger.info(f"Gmail service initialized with service account delegation as {impersonate_email}")
                else:
                    # Fallback to user credentials for local development
                    logger.warning("Service account delegation not available, using user credentials for Gmail")
                    self.gmail_service = build('gmail', 'v1', credentials=self.credentials)

            except Exception as e:
                logger.error(f"Error initializing Gmail service: {e}", exc_info=True)
                # Fallback to user credentials
                self.gmail_service = build('gmail', 'v1', credentials=self.credentials)

        return self.gmail_service

    def _get_tasks_service(self):
        """Lazy load Tasks service"""
        if not self.tasks_service:
            self.tasks_service = TasksService(self.credentials)
        return self.tasks_service

    def send_chat_message(self, space_name: str, message_text: str) -> bool:
        """
        Send a message to a Google Chat space

        Args:
            space_name: The Google Chat space name (e.g., 'spaces/AAAAAAAAAAA')
            message_text: The message to send

        Returns:
            True if successful, False otherwise
        """
        try:
            chat = self._get_chat_service()

            message = {
                'text': message_text
            }

            response = chat.spaces().messages().create(
                parent=space_name,
                body=message
            ).execute()

            logger.info(f"Chat message sent successfully: {response.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send chat message: {str(e)}")
            return False

    def send_direct_message(self, user_email: str, message_text: str, impersonate_admin: str = None) -> bool:
        """
        Send a direct message to a user via Google Chat using service account with domain-wide delegation

        Impersonates hola@edvolution.io using service account with domain-wide delegation

        Args:
            user_email: The user's email address
            message_text: The message to send
            impersonate_admin: Email to impersonate (defaults to hola@edvolution.io)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use service account with domain-wide delegation to impersonate notification account
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            import os

            # Determine which account to impersonate (default to hola@edvolution.io)
            impersonate_email = impersonate_admin or os.getenv('NOTIFICATION_ACCOUNT_EMAIL', 'hola@edvolution.io')

            # Use Application Default Credentials (service account in production)
            from google.auth import default
            credentials, project = default()

            # Check if credentials support delegation (service account)
            if not hasattr(credentials, 'with_subject'):
                logger.error("Credentials do not support domain-wide delegation. Ensure service account is used.")
                return False

            # Create delegated credentials to act as the notification account
            scopes = [
                'https://www.googleapis.com/auth/chat.messages',
                'https://www.googleapis.com/auth/chat.spaces'
            ]
            delegated_credentials = credentials.with_subject(impersonate_email).with_scopes(scopes)

            if not delegated_credentials.valid:
                delegated_credentials.refresh(Request())

            # Build Chat service with delegated credentials
            chat = build('chat', 'v1', credentials=delegated_credentials)
            logger.info(f"Using service account to impersonate {impersonate_email} for Chat DM")

            # Find or create direct message space with the user
            try:
                # Try to find existing DM space between notification account and target user
                response = chat.spaces().findDirectMessage(name=f"users/{user_email}").execute()
                space_name = response.get('name')
                logger.info(f"Found existing DM space with {user_email}: {space_name}")
            except Exception as find_error:
                logger.info(f"No existing DM space found with {user_email}, creating new one")
                # Create new DM space
                response = chat.spaces().setup(body={
                    'space': {
                        'spaceType': 'DIRECT_MESSAGE'
                    },
                    'membershipInvitation': {
                        'user': {
                            'name': f'users/{user_email}'
                        }
                    }
                }).execute()
                space_name = response.get('space', {}).get('name')
                logger.info(f"Created new DM space with {user_email}: {space_name}")

            # Send the message to the DM space
            message = {'text': message_text}
            result = chat.spaces().messages().create(
                parent=space_name,
                body=message
            ).execute()

            logger.info(f"Successfully sent DM to {user_email} from notification account: {result.get('name')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send DM to {user_email}: {str(e)}", exc_info=True)
            return False

    def send_approval_chat_card(
        self,
        user_email: str,
        employee_name: str,
        employee_email: str,
        start_date: str,
        end_date: str,
        days_count: int,
        timeoff_type: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
        approval_level: str = "manager",
        portal_url: str = "http://localhost:8080",
        impersonate_admin: str = None
    ) -> bool:
        """
        Send an approval notification via Google Chat with interactive card using notification account

        Uses hola@edvolution.io credentials to send approval cards

        Args:
            user_email: Email of the approver
            employee_name: Name of employee requesting time off
            employee_email: Email of employee
            start_date: Start date
            end_date: End date
            days_count: Number of days
            timeoff_type: Type of time off
            notes: Optional notes
            request_id: Request ID
            approval_level: "manager" or "admin"
            portal_url: Base URL of the portal
            impersonate_admin: Deprecated (kept for backward compatibility)

        Returns:
            True if successful, False otherwise
        """
        if not ENABLE_CHAT_NOTIFICATIONS:
            logger.info("Chat notifications disabled, skipping")
            return True

        try:
            # Use service account with domain-wide delegation to impersonate notification account
            from google.auth import default
            from google.auth.transport.requests import Request
            import os

            # Determine which account to impersonate (default to hola@edvolution.io)
            impersonate_email = impersonate_admin or os.getenv('NOTIFICATION_ACCOUNT_EMAIL', 'hola@edvolution.io')

            # Use Application Default Credentials (service account in production)
            credentials, project = default()

            # Check if credentials support delegation (service account)
            if not hasattr(credentials, 'with_subject'):
                logger.error("Credentials do not support domain-wide delegation. Ensure service account is used.")
                return False

            # Create delegated credentials to act as the notification account
            scopes = [
                'https://www.googleapis.com/auth/chat.messages',
                'https://www.googleapis.com/auth/chat.spaces'
            ]
            delegated_credentials = credentials.with_subject(impersonate_email).with_scopes(scopes)

            if not delegated_credentials.valid:
                delegated_credentials.refresh(Request())

            # Build Chat service with delegated credentials
            chat = build('chat', 'v1', credentials=delegated_credentials)
            logger.info(f"Using service account to impersonate {impersonate_email} for Chat card")

            timeoff_label = timeoff_type.replace('_', ' ').title()

            # Create card message with interactive buttons
            card_message = {
                "text": f"🔔 New {approval_level.title()} Approval Required",
                "cardsV2": [{
                    "cardId": f"approval-{request_id}",
                    "card": {
                        "header": {
                            "title": f"Time-Off Approval Required",
                            "subtitle": f"{employee_name}'s {timeoff_label} Request",
                            "imageUrl": "https://fonts.gstatic.com/s/i/productlogos/calendar_2020q4/v13/web-24dp/logo_calendar_2020q4_color_1x_web_24dp.png"
                        },
                        "sections": [{
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": "Employee",
                                        "text": f"{employee_name}",
                                        "bottomLabel": employee_email
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Type",
                                        "text": timeoff_label
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Dates",
                                        "text": f"{start_date} to {end_date}"
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Duration",
                                        "text": f"{days_count} days"
                                    }
                                }
                            ]
                        }]
                    }
                }]
            }

            # Add notes if provided
            if notes:
                card_message["cardsV2"][0]["card"]["sections"][0]["widgets"].append({
                    "decoratedText": {
                        "topLabel": "Notes",
                        "text": notes,
                        "wrapText": True
                    }
                })

            # Add action buttons
            card_message["cardsV2"][0]["card"]["sections"].append({
                "widgets": [{
                    "buttonList": {
                        "buttons": [
                            {
                                "text": "View Request",
                                "onClick": {
                                    "openLink": {
                                        "url": f"{portal_url}/requests/{request_id}"
                                    }
                                }
                            }
                        ]
                    }
                }]
            })

            # Find or create DM space with the approver (using notification account)
            try:
                # Try to find existing DM space between notification account and approver
                response = chat.spaces().findDirectMessage(name=f"users/{user_email}").execute()
                space_name = response.get('name')
                logger.info(f"Found existing DM space with {user_email}: {space_name}")
            except Exception as find_error:
                logger.info(f"No existing DM space found with {user_email}, creating new one")
                # Create new DM space
                response = chat.spaces().setup(body={
                    'space': {
                        'spaceType': 'DIRECT_MESSAGE'
                    },
                    'membershipInvitation': {
                        'user': {
                            'name': f'users/{user_email}'
                        }
                    }
                }).execute()
                space_name = response.get('space', {}).get('name')
                logger.info(f"Created new DM space with {user_email}: {space_name}")

            # Send the card to the DM space
            result = chat.spaces().messages().create(
                parent=space_name,
                body=card_message
            ).execute()

            logger.info(f"Successfully sent approval card to {user_email} from notification account: {result.get('name')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send approval card to {user_email}: {str(e)}", exc_info=True)
            # Fall back to simple text message
            try:
                timeoff_label = timeoff_type.replace('_', ' ').title()
                simple_message = f"""🔔 **Time-Off Approval Required**

**Employee:** {employee_name} ({employee_email})
**Type:** {timeoff_label}
**Dates:** {start_date} to {end_date} ({days_count} days)"""

                if notes:
                    simple_message += f"\n**Notes:** {notes}"

                simple_message += f"\n\nPlease log in to the Employee Portal to review this {approval_level} approval request."

                return self.send_direct_message(user_email, simple_message)
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")
                return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email via Gmail API

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            from_email: Sender email (defaults to authenticated user)

        Returns:
            True if successful, False otherwise
        """
        try:
            gmail = self._get_gmail_service()

            # Create message
            if body_html:
                message = MIMEMultipart('alternative')
                part1 = MIMEText(body_text, 'plain')
                part2 = MIMEText(body_html, 'html')
                message.attach(part1)
                message.attach(part2)
            else:
                message = MIMEText(body_text)

            message['To'] = to_email
            if from_email:
                message['From'] = from_email
            message['Subject'] = subject

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send message
            response = gmail.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent successfully to {to_email}: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_timeoff_approval_notification(
        self,
        approver_email: str,
        employee_name: str,
        employee_email: str,
        start_date: str,
        end_date: str,
        days_count: int,
        timeoff_type: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
        approval_level: str = "manager"  # "manager" or "admin"
    ) -> bool:
        """
        Send approval notification via both email and chat

        Args:
            approver_email: Email of the person who needs to approve
            employee_name: Name of employee requesting time off
            employee_email: Email of employee requesting time off
            start_date: Start date of time off
            end_date: End date of time off
            days_count: Number of days
            timeoff_type: Type of time off (vacation, sick_leave, day_off)
            notes: Optional notes from employee
            request_id: Request ID for creating approval links
            approval_level: "manager" or "admin"

        Returns:
            True if at least one notification method succeeded
        """
        timeoff_label = timeoff_type.replace('_', ' ').title()
        level_label = approval_level.title()

        # Prepare message content
        subject = f"Time Off Approval Required: {employee_name}"

        text_body = f"""
Hello,

{employee_name} ({employee_email}) has requested time off that requires your approval as {level_label}.

Request Details:
- Employee: {employee_name}
- Type: {timeoff_label}
- Start Date: {start_date}
- End Date: {end_date}
- Days: {days_count}
"""

        if notes:
            text_body += f"- Notes: {notes}\n"

        text_body += """
Please log in to the Employee Portal to review and approve/reject this request.

This is an automated reminder. You will receive daily notifications until the request is processed.

Thank you,
Employee Portal System
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #667eea;">Time Off Approval Required</h2>
    <p>Hello,</p>
    <p><strong>{employee_name}</strong> ({employee_email}) has requested time off that requires your approval as <strong>{level_label}</strong>.</p>

    <div style="background: #f5f7fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #667eea;">Request Details</h3>
        <ul style="list-style: none; padding: 0;">
            <li><strong>Employee:</strong> {employee_name}</li>
            <li><strong>Type:</strong> {timeoff_label}</li>
            <li><strong>Start Date:</strong> {start_date}</li>
            <li><strong>End Date:</strong> {end_date}</li>
            <li><strong>Days:</strong> {days_count}</li>
"""

        if notes:
            html_body += f"            <li><strong>Notes:</strong> {notes}</li>\n"

        html_body += """
        </ul>
    </div>

    <p>Please log in to the <strong>Employee Portal</strong> to review and approve/reject this request.</p>

    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This is an automated reminder. You will receive daily notifications until the request is processed.
    </p>

    <p style="color: #999; font-size: 11px;">
        Employee Portal System
    </p>
</body>
</html>
"""

        # Chat message (simpler format)
        chat_message = f"""
🔔 **Time Off Approval Required**

**Employee:** {employee_name} ({employee_email})
**Type:** {timeoff_label}
**Dates:** {start_date} to {end_date} ({days_count} days)
"""

        if notes:
            chat_message += f"**Notes:** {notes}\n"

        chat_message += f"\nPlease log in to the Employee Portal to review this {level_label} approval request."

        # Send email notification
        email_success = self.send_email(
            to_email=approver_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body
        )

        # Send Google Chat card notification (if enabled)
        chat_success = False
        if ENABLE_CHAT_NOTIFICATIONS:
            try:
                chat_success = self.send_approval_chat_card(
                    user_email=approver_email,
                    employee_name=employee_name,
                    employee_email=employee_email,
                    start_date=start_date,
                    end_date=end_date,
                    days_count=days_count,
                    timeoff_type=timeoff_type,
                    notes=notes,
                    request_id=request_id,
                    approval_level=approval_level
                )
            except Exception as e:
                logger.warning(f"Could not send chat card to {approver_email}: {str(e)}")

        # Create Google Task (if enabled)
        task_id = None
        if ENABLE_TASK_NOTIFICATIONS:
            try:
                tasks_service = self._get_tasks_service()
                task_id = tasks_service.create_approval_task(
                    user_email=approver_email,
                    employee_name=employee_name,
                    employee_email=employee_email,
                    start_date=start_date,
                    end_date=end_date,
                    days_count=days_count,
                    timeoff_type=timeoff_type,
                    notes=notes,
                    request_id=request_id,
                    approval_level=approval_level,
                    due_days=TASK_DUE_DAYS
                )
                if task_id:
                    logger.info(f"Created task {task_id} for {approver_email}")
            except Exception as e:
                logger.warning(f"Could not create task for {approver_email}: {str(e)}")

        # Return True if at least one method succeeded, and return task_id if created
        success = email_success or chat_success
        return (success, task_id) if task_id else success

    def send_timeoff_status_notification(
        self,
        employee_email: str,
        employee_name: str,
        start_date: str,
        end_date: str,
        days_count: int,
        timeoff_type: str,
        status: str,
        rejection_reason: Optional[str] = None
    ) -> bool:
        """
        Notify employee about their time-off request status change

        Args:
            employee_email: Employee's email
            employee_name: Employee's name
            start_date: Start date
            end_date: End date
            days_count: Number of days
            timeoff_type: Type of time off
            status: New status (approved, rejected, etc.)
            rejection_reason: Reason if rejected

        Returns:
            True if successful
        """
        timeoff_label = timeoff_type.replace('_', ' ').title()
        status_label = status.replace('_', ' ').title()

        if status == 'approved':
            subject = f"Time Off Request Approved: {start_date} - {end_date}"
            emoji = "✅"
        elif status == 'rejected':
            subject = f"Time Off Request Declined: {start_date} - {end_date}"
            emoji = "❌"
        elif status == 'manager_approved':
            subject = f"Time Off Request Pending Final Approval: {start_date} - {end_date}"
            emoji = "⏳"
        else:
            subject = f"Time Off Request Status Update: {start_date} - {end_date}"
            emoji = "ℹ️"

        text_body = f"""
Hello {employee_name},

Your time off request has been updated.

Status: {status_label}

Request Details:
- Type: {timeoff_label}
- Start Date: {start_date}
- End Date: {end_date}
- Days: {days_count}
"""

        if rejection_reason:
            text_body += f"\nReason: {rejection_reason}\n"

        if status == 'approved':
            text_body += "\nYour time off has been approved. Please sync it to your calendar from the Employee Portal.\n"
        elif status == 'manager_approved':
            text_body += "\nYour manager has approved this request. It now requires HR/Admin approval.\n"

        text_body += """
Thank you,
Employee Portal System
"""

        # Send email
        email_success = self.send_email(
            to_email=employee_email,
            subject=subject,
            body_text=text_body
        )

        # Send chat notification
        chat_message = f"{emoji} **Time Off Request {status_label}**\n\n"
        chat_message += f"**Dates:** {start_date} to {end_date} ({days_count} days)\n"
        chat_message += f"**Type:** {timeoff_label}\n"

        if rejection_reason:
            chat_message += f"**Reason:** {rejection_reason}\n"

        try:
            self.send_direct_message(employee_email, chat_message)
        except Exception as e:
            logger.warning(f"Could not send chat message to {employee_email}: {str(e)}")

        return email_success
