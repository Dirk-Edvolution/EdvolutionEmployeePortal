"""
Scheduler service for daily reminders
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.app.services import FirestoreService, NotificationService
from backend.config.settings import ADMIN_USERS
from google.oauth2.credentials import Credentials
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background scheduler for sending daily reminders"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = FirestoreService()

    def start(self):
        """Start the scheduler"""
        # Schedule daily reminders at 9 AM
        self.scheduler.add_job(
            self.send_daily_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_reminders',
            name='Send daily time-off approval reminders',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Scheduler started - daily reminders will run at 9:00 AM")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def send_daily_reminders(self):
        """
        Send daily reminders for all pending time-off requests
        This runs automatically every day at 9 AM
        """
        logger.info("Starting daily reminder job...")

        try:
            # Get all pending requests (waiting for manager approval)
            pending_manager_requests = self._get_pending_manager_requests()
            logger.info(f"Found {len(pending_manager_requests)} requests pending manager approval")

            # Get all requests pending admin approval
            pending_admin_requests = self._get_pending_admin_requests()
            logger.info(f"Found {len(pending_admin_requests)} requests pending admin approval")

            # Send reminders for manager approvals
            for request_id, request, manager_email in pending_manager_requests:
                self._send_reminder(
                    request_id=request_id,
                    request=request,
                    approver_email=manager_email,
                    approval_level="manager"
                )

            # Send reminders for admin approvals
            for request_id, request in pending_admin_requests:
                for admin_email in ADMIN_USERS:
                    if admin_email:  # Skip empty strings
                        self._send_reminder(
                            request_id=request_id,
                            request=request,
                            approver_email=admin_email,
                            approval_level="admin"
                        )

            logger.info("Daily reminder job completed successfully")

        except Exception as e:
            logger.error(f"Error in daily reminder job: {str(e)}")

    def _get_pending_manager_requests(self):
        """Get all requests pending manager approval with manager info"""
        requests = []

        # Query all pending requests
        pending_docs = self.db.timeoff_ref.where('status', '==', 'pending').stream()

        for doc in pending_docs:
            data = doc.to_dict()
            manager_email = data.get('manager_email')

            if manager_email:
                # Get employee info
                employee = self.db.get_employee(data.get('employee_email'))

                requests.append((doc.id, data, manager_email))

        return requests

    def _get_pending_admin_requests(self):
        """Get all requests pending admin approval"""
        pending_docs = self.db.timeoff_ref.where('status', '==', 'manager_approved').stream()

        requests = []
        for doc in pending_docs:
            requests.append((doc.id, doc.to_dict()))

        return requests

    def _send_reminder(
        self,
        request_id: str,
        request: Dict[str, Any],
        approver_email: str,
        approval_level: str
    ):
        """
        Send a reminder notification for a specific request

        Args:
            request_id: The request ID
            request: The request data
            approver_email: Email of the approver
            approval_level: "manager" or "admin"
        """
        try:
            # Get employee info
            employee = self.db.get_employee(request.get('employee_email'))

            if not employee:
                logger.warning(f"Employee not found for request {request_id}")
                return

            # Get approver credentials (we need to use service account or admin credentials here)
            # For now, we'll log that a reminder should be sent
            # In production, you'd use a service account with domain-wide delegation

            logger.info(
                f"Reminder needed for {approver_email}: "
                f"{employee.full_name} ({request.get('timeoff_type')}) "
                f"{request.get('start_date')} - {request.get('end_date')}"
            )

            # TODO: Implement actual notification sending using service account credentials
            # For now, this logs the reminders that should be sent

        except Exception as e:
            logger.error(f"Error sending reminder for request {request_id}: {str(e)}")

    def send_reminder_now(
        self,
        credentials: Credentials,
        request_id: str,
        request: Dict[str, Any],
        approver_email: str,
        approval_level: str
    ):
        """
        Send a reminder immediately (called from API endpoints)

        Args:
            credentials: User credentials for sending notifications
            request_id: The request ID
            request: The request data
            approver_email: Email of the approver
            approval_level: "manager" or "admin"
        """
        try:
            # Get employee info
            employee = self.db.get_employee(request.get('employee_email'))

            if not employee:
                logger.warning(f"Employee not found for request {request_id}")
                return False

            # Create notification service
            notification_service = NotificationService(credentials)

            # Send notification
            success = notification_service.send_timeoff_approval_notification(
                approver_email=approver_email,
                employee_name=employee.full_name or employee.email,
                employee_email=employee.email,
                start_date=str(request.get('start_date')),
                end_date=str(request.get('end_date')),
                days_count=request.get('days_count'),
                timeoff_type=request.get('timeoff_type'),
                notes=request.get('notes'),
                request_id=request_id,
                approval_level=approval_level
            )

            return success

        except Exception as e:
            logger.error(f"Error sending immediate reminder for request {request_id}: {str(e)}")
            return False


# Global scheduler instance
_scheduler = None


def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
