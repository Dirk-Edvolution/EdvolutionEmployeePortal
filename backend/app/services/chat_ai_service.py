"""
Gemini AI-powered assistant for Google Chat
Handles natural language queries about time-off, vacation days, and HR requests
"""
import google.generativeai as genai
from backend.config.settings import GOOGLE_API_KEY
from backend.app.services import FirestoreService
from backend.app.models import TimeOffType
from datetime import datetime, date
import logging
import json
import re

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)


class ChatAIService:
    """AI-powered chat assistant using Gemini"""

    def __init__(self, user_email):
        self.user_email = user_email
        self.db = FirestoreService()
        # Use the latest Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def get_user_context(self):
        """Get user's context for AI (vacation days, pending requests, etc.)"""
        try:
            employee = self.db.get_employee(self.user_email)
            if not employee:
                return None

            # Get vacation summary
            year = datetime.now().year
            used_days = self.db.calculate_used_vacation_days(self.user_email, year)
            remaining_days = employee.vacation_days_per_year - used_days

            # Get pending requests
            requests = self.db.get_employee_timeoff_requests(self.user_email, year)
            pending = [r for rid, r in requests if r.status.value == 'pending']
            approved = [r for rid, r in requests if r.status.value == 'approved']

            # Get pending approvals if manager
            pending_approvals = []
            if employee.manager_email == self.user_email or self.user_email in ['dirk@edvolution.io']:
                pending_approvals = self.db.get_pending_requests_for_manager(self.user_email)

            context = {
                'full_name': employee.full_name,
                'email': employee.email,
                'department': employee.department,
                'vacation_days_total': employee.vacation_days_per_year,
                'vacation_days_used': used_days,
                'vacation_days_remaining': remaining_days,
                'pending_requests_count': len(pending),
                'approved_requests_count': len(approved),
                'pending_approvals_count': len(pending_approvals),
                'is_manager': len(pending_approvals) > 0
            }

            return context
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return None

    def process_query(self, message):
        """
        Process a natural language query using Gemini

        Args:
            message: The user's message

        Returns:
            str: AI-generated response
        """
        try:
            # Get user context
            context = self.get_user_context()
            if not context:
                return "❌ I couldn't find your employee profile. Please contact HR."

            # Build prompt with context
            prompt = f"""You are an HR assistant for Edvolution. Help the employee with their question.

Employee Information:
- Name: {context['full_name']}
- Email: {context['email']}
- Department: {context['department']}
- Vacation days per year: {context['vacation_days_total']}
- Vacation days used this year: {context['vacation_days_used']}
- Vacation days remaining: {context['vacation_days_remaining']}
- Pending time-off requests: {context['pending_requests_count']}
- Approved time-off requests: {context['approved_requests_count']}
{f"- Pending approval requests (as manager): {context['pending_approvals_count']}" if context['is_manager'] else ""}

Employee's Question: {message}

Instructions:
- Be helpful and friendly
- Use the employee information above to answer their question
- If they ask about vacation days, use the numbers provided
- If they want to create a time-off request, tell them to use the portal at https://rrhh.edvolution.io
- If they're a manager and ask about approvals, tell them they have {context.get('pending_approvals_count', 0)} pending requests
- Keep responses concise (2-3 sentences max)
- Use emojis sparingly

Answer:"""

            # Generate response
            response = self.model.generate_content(prompt)

            return response.text

        except Exception as e:
            logger.error(f"Error processing query with Gemini: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error processing your request: {str(e)}"

    def extract_intent(self, message):
        """
        Extract the user's intent from their message

        Returns:
            dict: Intent information
        """
        message_lower = message.lower()

        # Check for various intents
        if any(word in message_lower for word in ['vacation', 'days left', 'how many', 'remaining']):
            return {'intent': 'check_vacation', 'confidence': 0.9}

        if any(word in message_lower for word in ['request', 'time off', 'leave', 'sick', 'day off']):
            return {'intent': 'create_request', 'confidence': 0.8}

        if any(word in message_lower for word in ['status', 'pending', 'approved', 'my requests']):
            return {'intent': 'check_status', 'confidence': 0.85}

        if any(word in message_lower for word in ['approve', 'approval', 'pending approval']):
            return {'intent': 'check_approvals', 'confidence': 0.85}

        return {'intent': 'general_query', 'confidence': 0.5}

    def quick_response(self, intent_type):
        """
        Generate a quick response without AI for simple queries

        Args:
            intent_type: The type of intent detected

        Returns:
            str: Quick response or None if AI should handle it
        """
        context = self.get_user_context()
        if not context:
            return None

        if intent_type == 'check_vacation':
            return (f"📊 **Your Vacation Days ({datetime.now().year})**\n\n"
                   f"• Total: {context['vacation_days_total']} days\n"
                   f"• Used: {context['vacation_days_used']} days\n"
                   f"• **Remaining: {context['vacation_days_remaining']} days**")

        if intent_type == 'check_status':
            return (f"📋 **Your Time-Off Requests**\n\n"
                   f"• Pending: {context['pending_requests_count']}\n"
                   f"• Approved: {context['approved_requests_count']}\n\n"
                   f"View details at https://rrhh.edvolution.io")

        if intent_type == 'check_approvals' and context['is_manager']:
            return (f"✅ **Pending Approvals**\n\n"
                   f"You have {context['pending_approvals_count']} request(s) waiting for your approval.\n\n"
                   f"View them at https://rrhh.edvolution.io")

        if intent_type == 'create_request':
            return (f"📝 **Create Time-Off Request**\n\n"
                   f"To create a time-off request, please visit:\n"
                   f"https://rrhh.edvolution.io\n\n"
                   f"You have {context['vacation_days_remaining']} vacation days remaining.")

        return None
