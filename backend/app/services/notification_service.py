"""
Notification service for Google Chat and Email
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Optional, List
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via Google Chat and Gmail"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.chat_service = None
        self.gmail_service = None

    def _get_chat_service(self):
        """Lazy load Google Chat service"""
        if not self.chat_service:
            self.chat_service = build('chat', 'v1', credentials=self.credentials)
        return self.chat_service

    def _get_gmail_service(self):
        """Lazy load Gmail service"""
        if not self.gmail_service:
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        return self.gmail_service

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

    def send_direct_message(self, user_email: str, message_text: str) -> bool:
        """
        Send a direct message to a user via Google Chat

        Args:
            user_email: The user's email address
            message_text: The message to send

        Returns:
            True if successful, False otherwise
        """
        try:
            chat = self._get_chat_service()

            # Create a DM space with the user
            space = chat.spaces().create(body={
                'type': 'DIRECT_MESSAGE',
                'singleUserBotDm': False,
                'displayName': f'DM with {user_email}'
            }).execute()

            # Send the message
            message = {
                'text': message_text
            }

            response = chat.spaces().messages().create(
                parent=space['name'],
                body=message
            ).execute()

            logger.info(f"Direct message sent to {user_email}: {response.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send direct message to {user_email}: {str(e)}")
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

        # Send both notifications
        email_success = self.send_email(
            to_email=approver_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body
        )

        # Try to send chat message (this may fail if user doesn't have chat enabled)
        chat_success = False
        try:
            chat_success = self.send_direct_message(approver_email, chat_message)
        except Exception as e:
            logger.warning(f"Could not send chat message to {approver_email}: {str(e)}")

        # Return True if at least one method succeeded
        return email_success or chat_success

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
