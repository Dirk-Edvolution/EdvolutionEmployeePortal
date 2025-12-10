"""
Natural language audit log query service using Vertex AI Gemini
Cost-effective solution for querying audit logs with plain language
"""
import google.generativeai as genai
from typing import Dict, Any, Optional
import json
import logging
from backend.config.settings import GOOGLE_API_KEY

logger = logging.getLogger(__name__)


class AuditQueryService:
    """Service for querying audit logs with natural language using Gemini"""

    def __init__(self):
        # Configure Gemini API (uses free tier for small queries)
        if not GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not configured. Natural language audit queries will not work.")
            self.model = None
        else:
            genai.configure(api_key=GOOGLE_API_KEY)
            # Use gemini-flash-lite-latest (cheapest model for simple queries)
            self.model = genai.GenerativeModel('gemini-flash-lite-latest')

    def parse_natural_query(self, question: str) -> Dict[str, Any]:
        """
        Convert natural language question to Firestore query parameters

        Args:
            question: Natural language question like "who approved mayra's vacation last week?"

        Returns:
            Dict with query parameters: {user_email, action, resource_type, resource_id, days}
        """

        if not self.model:
            logger.error("Gemini model not configured. Cannot parse natural language query.")
            return {
                "user_email": None,
                "action": None,
                "resource_type": None,
                "resource_id": None,
                "employee_name": None,
                "days": None
            }

        # Define the prompt for Gemini to understand audit log structure
        prompt = f"""You are an audit log query assistant. Convert the user's natural language question into structured query parameters.

Available audit actions:
- LOGIN, LOGOUT
- EMPLOYEE_CREATE, EMPLOYEE_UPDATE, EMPLOYEE_SYNC
- TIMEOFF_CREATE, TIMEOFF_APPROVE_MANAGER, TIMEOFF_APPROVE_ADMIN, TIMEOFF_REJECT, TIMEOFF_UPDATE, TIMEOFF_DELETE

Available resource types:
- employee
- timeoff_request
- system

User question: "{question}"

Extract the following information and respond ONLY with valid JSON (no markdown, no explanation):
{{
    "user_email": "email@domain.com or null if asking about any user",
    "action": "SPECIFIC_ACTION or null if asking about any action",
    "resource_type": "employee or timeoff_request or null",
    "resource_id": "specific ID if mentioned or null",
    "employee_name": "name mentioned in question or null",
    "days": "number of days to look back (7 for last week, 30 for last month, etc) or null for all time"
}}

Examples:
Q: "who approved mayra's vacation last week?"
A: {{"user_email": null, "action": "TIMEOFF_APPROVE_MANAGER", "resource_type": "timeoff_request", "resource_id": null, "employee_name": "mayra", "days": 7}}

Q: "who modified roberto's manager?"
A: {{"user_email": null, "action": "EMPLOYEE_UPDATE", "resource_type": "employee", "resource_id": null, "employee_name": "roberto", "days": null}}

Q: "what did dirk do yesterday?"
A: {{"user_email": "dirk", "action": null, "resource_type": null, "resource_id": null, "employee_name": null, "days": 1}}

Now respond with JSON only:"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up response (remove markdown code blocks if present)
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            # Parse JSON response
            query_params = json.loads(result_text)
            logger.info(f"Parsed query: {query_params}")
            return query_params

        except Exception as e:
            logger.error(f"Failed to parse natural query: {str(e)}")
            # Return empty params on failure
            return {
                "user_email": None,
                "action": None,
                "resource_type": None,
                "resource_id": None,
                "employee_name": None,
                "days": None
            }

    def generate_natural_response(self, question: str, logs: list) -> str:
        """
        Convert audit log results into a natural language answer

        Args:
            question: Original user question
            logs: List of audit log entries

        Returns:
            Natural language response
        """
        if not logs:
            return "I couldn't find any audit logs matching your question."

        if not self.model:
            # Fallback to simple text response if model not configured
            return f"Found {len(logs)} audit log entries matching your question. (Natural language responses require GOOGLE_API_KEY to be configured)"

        # Format logs for Gemini
        logs_summary = []
        for log in logs[:10]:  # Limit to 10 most recent to save tokens
            logs_summary.append({
                'user': log.get('user_email'),
                'action': log.get('action'),
                'timestamp': log.get('timestamp'),
                'details': log.get('details')
            })

        prompt = f"""You are an audit log assistant. Answer the user's question based on the audit logs provided.

User question: "{question}"

Audit logs (most recent first):
{json.dumps(logs_summary, indent=2)}

Provide a clear, concise answer in 1-2 sentences. Be specific about WHO did WHAT and WHEN.
If multiple people performed the action, list them all.
Use friendly, natural language.

Response:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return f"Found {len(logs)} audit log entries matching your question."
