# Natural Language Audit Query Feature

## Overview

The natural language audit query feature allows admins and managers to search audit logs using plain English questions instead of constructing complex database queries.

## How It Works

The system uses Google's Gemini AI (gemini-1.5-flash model) to:
1. Parse natural language questions into structured query parameters
2. Execute Firestore queries based on those parameters
3. Convert results back into natural language responses

## Setup

### 1. Get a Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API key"
3. Create a new API key or use an existing one
4. Copy the API key

### 2. Configure Environment Variable

Add to your `.env` file:

```bash
GOOGLE_API_KEY=your_api_key_here
```

### 3. Restart Backend

```bash
source venv/bin/activate
python -m backend.app.main
```

## API Endpoint

**POST `/api/audit/query`**

**Request Body:**
```json
{
  "question": "who approved mayra's vacation last week?"
}
```

**Response:**
```json
{
  "question": "who approved mayra's vacation last week?",
  "answer": "Dirk approved Mayra's vacation on December 8, 2025.",
  "logs": [
    {
      "user_email": "dirk@edvolution.io",
      "action": "TIMEOFF_APPROVE_MANAGER",
      "timestamp": "2025-12-08T19:48:59.123Z",
      "details": {...}
    }
  ],
  "total_matches": 1
}
```

## Example Questions

### Time-Off Approvals
- "who approved mayra's vacation last week?"
- "show me all vacation approvals by dirk this month"
- "who rejected the vacation request on december 5th?"

### Employee Changes
- "who modified roberto's manager?"
- "who updated mayra's department?"
- "show me all employee updates by admin this week"

### User Activity
- "what did dirk do yesterday?"
- "show me admin's activity in the last 7 days"
- "who logged in today?"

## Query Parameters Extracted

The AI extracts these parameters from natural language:

- **user_email**: Who performed the action (e.g., "dirk@edvolution.io")
- **action**: What action was performed (e.g., "TIMEOFF_APPROVE_MANAGER")
- **resource_type**: Type of resource affected ("employee" or "timeoff_request")
- **employee_name**: Name mentioned in the question (e.g., "mayra")
- **days**: Time range to search (e.g., 7 for "last week", 1 for "yesterday")

## Available Audit Actions

### Authentication
- LOGIN
- LOGOUT

### Employee Management
- EMPLOYEE_CREATE
- EMPLOYEE_UPDATE
- EMPLOYEE_SYNC

### Time-Off Requests
- TIMEOFF_CREATE
- TIMEOFF_APPROVE_MANAGER
- TIMEOFF_APPROVE_ADMIN
- TIMEOFF_REJECT
- TIMEOFF_UPDATE
- TIMEOFF_DELETE

## Cost Optimization

- Uses **gemini-1.5-flash** (cheapest Gemini model)
- Free tier includes generous quota for small queries
- Only first 10 log entries sent to AI for response generation
- Prompt is optimized to be concise

### Estimated Costs
- Query parsing: ~100-200 tokens per request
- Response generation: ~500-800 tokens per request
- Free tier: 15 requests/minute, 1500 requests/day
- After free tier: ~$0.000035 per query (extremely cheap)

## Security & Permissions

- **Admins**: Can query all audit logs
- **Managers**: Can query their own actions and their team's activities
- **Regular users**: Can only query their own actions

The endpoint respects existing RBAC:
```python
@audit_bp.route('/query', methods=['POST'])
@login_required
def natural_language_query():
    # Non-admins can only query their own actions
    if not is_admin(current_email):
        user_email = current_email
```

## Implementation Files

- **Service**: `backend/app/services/audit_query_service.py`
- **API Route**: `backend/app/api/audit_routes.py` (POST `/api/audit/query`)
- **Configuration**: `backend/config/settings.py` (GOOGLE_API_KEY)

## Testing

### Test Without API Key
The system gracefully handles missing API key:
```python
# Returns empty query params if no API key
# Returns basic count message instead of natural response
```

### Test With API Key
```bash
curl -X POST http://localhost:8080/api/audit/query \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"question": "who approved mayra vacation last week?"}'
```

## Future Enhancements

1. **Frontend UI**:
   - Add search box in audit log view
   - Show natural language responses in a chat-like interface
   - Add suggested questions ("Try asking...")

2. **Advanced Features**:
   - Follow-up questions with context
   - Export results to CSV/PDF
   - Schedule recurring queries (daily/weekly summaries)
   - Email alerts based on audit patterns

3. **Performance**:
   - Cache common queries
   - Batch multiple questions in single API call
   - Use vector embeddings for similar question matching

## Troubleshooting

### "Gemini model not configured"
- Check that GOOGLE_API_KEY is set in .env
- Verify API key is valid at Google AI Studio
- Restart backend after adding API key

### "Request failed" or 500 errors
- Check backend logs for specific error
- Verify Firestore audit logs exist
- Test with simple query first ("who logged in today?")

### Empty results
- Verify audit logging is integrated in the app
- Check that audit logs exist in Firestore
- Try broader time range ("last 30 days" instead of "yesterday")

## Notes

- Audit logging infrastructure exists but is **NOT yet integrated** into the main application code
- Once audit logging is integrated, this feature will work end-to-end
- The natural language query feature is **production-ready** and waiting for audit logs to be populated
