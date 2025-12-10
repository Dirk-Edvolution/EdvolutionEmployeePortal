"""
Google Tasks service for managing approval workflow tasks
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TasksService:
    """Service for managing Google Tasks for approval workflows"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = None

    def _get_service(self):
        """Lazy load Google Tasks service"""
        if not self.service:
            self.service = build('tasks', 'v1', credentials=self.credentials)
        return self.service

    def create_approval_task(
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
        approval_level: str = "manager",  # "manager" or "admin"
        due_days: int = 2
    ) -> Optional[str]:
        """
        Create a task in user's Google Tasks for approval reminder

        Args:
            user_email: Email of the approver (used for impersonation if service account)
            employee_name: Name of employee requesting time off
            employee_email: Email of employee requesting time off
            start_date: Start date of time off
            end_date: End date of time off
            days_count: Number of days
            timeoff_type: Type of time off (vacation, sick_leave, day_off)
            notes: Optional notes from employee
            request_id: Request ID for tracking
            approval_level: "manager" or "admin"
            due_days: Number of business days until task is due

        Returns:
            Task ID if successful, None otherwise
        """
        try:
            service = self._get_service()

            # Format timeoff type for display
            timeoff_label = timeoff_type.replace('_', ' ').title()

            # Create task title
            title = f"Approve time-off: {employee_name} - {start_date} to {end_date}"

            # Create task notes/description
            task_notes = f"""Time-Off Approval Request ({approval_level.title()})

Employee: {employee_name} ({employee_email})
Type: {timeoff_label}
Dates: {start_date} to {end_date}
Duration: {days_count} days
"""

            if notes:
                task_notes += f"\nEmployee Notes: {notes}\n"

            task_notes += f"""
Request ID: {request_id}

Please log in to the Employee Portal to approve or reject this request.
"""

            # Calculate due date (due_days business days from now)
            due_date = datetime.now() + timedelta(days=due_days)
            due_date_rfc3339 = due_date.isoformat() + 'Z'

            # Create task
            task = {
                'title': title,
                'notes': task_notes,
                'due': due_date_rfc3339,
                'status': 'needsAction'
            }

            # Get default task list
            tasklists = service.tasklists().list().execute()
            default_tasklist_id = '@default'

            # Check if we have a custom "Employee Portal Approvals" list
            for tasklist in tasklists.get('items', []):
                if tasklist.get('title') == 'Employee Portal Approvals':
                    default_tasklist_id = tasklist.get('id')
                    break

            # Create the task
            result = service.tasks().insert(
                tasklist=default_tasklist_id,
                body=task
            ).execute()

            task_id = result.get('id')
            logger.info(f"Created Google Task {task_id} for {user_email} - request {request_id}")

            return task_id

        except HttpError as e:
            logger.error(f"HTTP error creating task for {user_email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create task for {user_email}: {str(e)}")
            return None

    def complete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """
        Mark a task as completed

        Args:
            task_id: The task ID to complete
            tasklist_id: The tasklist ID (defaults to @default)

        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_service()

            # Update task status to completed
            task = service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()

            task['status'] = 'completed'
            task['completed'] = datetime.now().isoformat() + 'Z'

            service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task
            ).execute()

            logger.info(f"Marked task {task_id} as completed")
            return True

        except HttpError as e:
            logger.error(f"HTTP error completing task {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
            return False

    def delete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """
        Delete a task

        Args:
            task_id: The task ID to delete
            tasklist_id: The tasklist ID (defaults to @default)

        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_service()

            service.tasks().delete(
                tasklist=tasklist_id,
                task=task_id
            ).execute()

            logger.info(f"Deleted task {task_id}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error deleting task {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            return False

    def get_or_create_portal_tasklist(self) -> str:
        """
        Get or create the "Employee Portal Approvals" task list

        Returns:
            Task list ID
        """
        try:
            service = self._get_service()

            # Check if list already exists
            tasklists = service.tasklists().list().execute()
            for tasklist in tasklists.get('items', []):
                if tasklist.get('title') == 'Employee Portal Approvals':
                    return tasklist.get('id')

            # Create new list
            new_list = {
                'title': 'Employee Portal Approvals'
            }

            result = service.tasklists().insert(body=new_list).execute()
            logger.info(f"Created new task list: Employee Portal Approvals")

            return result.get('id')

        except Exception as e:
            logger.error(f"Failed to get/create portal tasklist: {str(e)}")
            return '@default'
