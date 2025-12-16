"""
Gmail integration service for auto-responder
"""
from typing import Optional
from datetime import date
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GmailService:
    """Service for managing Gmail settings including vacation responder"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)

    def enable_vacation_responder(
        self,
        start_date: date,
        end_date: date,
        message: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Enable Gmail vacation auto-responder
        """
        try:
            # Convert dates to milliseconds since epoch
            start_time = int(start_date.strftime('%s')) * 1000
            end_time = int(end_date.strftime('%s')) * 1000 + 86400000  # Add 1 day in ms

            vacation_settings = {
                'enableAutoReply': True,
                'responseSubject': subject or 'Out of Office',
                'responseBodyHtml': message,
                'restrictToContacts': False,
                'restrictToDomain': False,
                'startTime': start_time,
                'endTime': end_time,
            }

            self.service.users().settings().updateVacation(
                userId='me',
                body=vacation_settings
            ).execute()

            return True

        except Exception as e:
            print(f"Error enabling vacation responder: {e}")
            return False

    def disable_vacation_responder(self) -> bool:
        """Disable Gmail vacation auto-responder"""
        try:
            vacation_settings = {
                'enableAutoReply': False,
            }

            self.service.users().settings().updateVacation(
                userId='me',
                body=vacation_settings
            ).execute()

            return True

        except Exception as e:
            print(f"Error disabling vacation responder: {e}")
            return False

    def get_vacation_responder_status(self) -> Optional[dict]:
        """Get current vacation responder settings"""
        try:
            settings = self.service.users().settings().getVacation(
                userId='me'
            ).execute()

            return settings

        except Exception as e:
            print(f"Error getting vacation responder status: {e}")
            return None

    def generate_ooo_message(
        self,
        employee_name: str,
        start_date: date,
        end_date: date,
        timeoff_type: str
    ) -> str:
        """Generate a standard OOO message"""
        type_text = {
            'vacation': 'on vacation',
            'sick_leave': 'out sick',
            'day_off': 'out of office'
        }.get(timeoff_type, 'out of office')

        message = f"""
        <p>Thank you for your email.</p>

        <p>I am currently {type_text} from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}
        and will have limited access to email.</p>

        <p>I will respond to your message when I return.</p>

        <p>For urgent matters, please contact my manager or team.</p>

        <p>Best regards,<br>
        {employee_name}</p>
        """

        return message.strip()
