"""
Google Calendar integration service for OOO events
"""
from typing import Optional
from datetime import date, datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class CalendarService:
    """Service for managing Google Calendar events"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = build('calendar', 'v3', credentials=credentials)

    def create_ooo_event(
        self,
        start_date: date,
        end_date: date,
        title: str,
        description: str = ""
    ) -> Optional[str]:
        """
        Create an Out of Office event in Google Calendar
        Returns event ID if successful
        """
        try:
            # Calendar events use RFC3339 format
            # All-day events use date format without time
            event = {
                'summary': f'🏖️ OOO: {title}',
                'description': description,
                'start': {
                    'date': start_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    # End date is exclusive in Calendar API, so add 1 day
                    'date': (end_date + timedelta(days=1)).isoformat(),
                    'timeZone': 'UTC',
                },
                'transparency': 'transparent',  # Show as "Free" not "Busy"
                'visibility': 'public',
                'eventType': 'outOfOffice',
            }

            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            return created_event.get('id')

        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

    def update_ooo_event(
        self,
        event_id: str,
        start_date: date,
        end_date: date,
        title: str,
        description: str = ""
    ) -> bool:
        """Update an existing OOO event"""
        try:
            event = {
                'summary': f'🏖️ OOO: {title}',
                'description': description,
                'start': {
                    'date': start_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'date': (end_date + timedelta(days=1)).isoformat(),
                    'timeZone': 'UTC',
                },
                'transparency': 'transparent',
                'visibility': 'public',
                'eventType': 'outOfOffice',
            }

            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()

            return True

        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return False

    def delete_ooo_event(self, event_id: str) -> bool:
        """Delete an OOO event"""
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True

        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False

    def get_event(self, event_id: str) -> Optional[dict]:
        """Get calendar event details"""
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return event

        except Exception as e:
            print(f"Error fetching calendar event: {e}")
            return None
