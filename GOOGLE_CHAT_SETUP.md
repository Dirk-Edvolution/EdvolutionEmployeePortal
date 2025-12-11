# Google Chat Integration Setup Guide

This guide explains how to set up two-way communication with Google Chat for instant time-off approval/rejection.

## Overview

The Employee Portal now supports **instant approval/rejection** of time-off requests directly from Google Chat using interactive cards. Managers and admins receive beautiful interactive cards in Google Chat and can approve or reject with a single click!

## Features

✓ **Interactive Cards** - Beautiful, rich cards with all request details
✓ **One-Click Approval** - Approve or reject instantly from Chat
✓ **Two-Tier Workflow** - Manager approval → Admin approval
✓ **Real-time Updates** - Database updates happen immediately
✓ **Command Support** - Help, status, and pending commands
✓ **Smart Permissions** - Automatic permission validation

## Architecture

### Endpoints Created

1. **`POST /api/chat/webhook`** - Main webhook for Google Chat events
   - Handles ADDED_TO_SPACE, MESSAGE, and CARD_CLICKED events
   - Processes approval/rejection actions
   - Validates permissions automatically

2. **`POST /api/chat/send-approval-card`** - Helper to send approval cards
   - Called by NotificationService when new requests are created
   - Generates interactive cards with approval buttons

3. **`GET /api/chat/test`** - Health check endpoint

### Event Types Handled

#### 1. ADDED_TO_SPACE
When the bot is added to a Chat space, it sends a welcome message.

#### 2. MESSAGE
Supports these commands:
- `help` - Shows available commands
- `status` - Shows bot status
- `pending` - Shows user's pending approvals

#### 3. CARD_CLICKED
Handles button clicks from interactive cards:
- `approve_manager` - Manager approves request
- `approve_admin` - Admin gives final approval
- `reject_manager` - Manager rejects request
- `reject_admin` - Admin rejects request

## Setup Instructions

### Step 1: Create a Google Chat App

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project: `edvolution-admon`
3. Navigate to **APIs & Services** → **Enabled APIs & Services**
4. Click **+ ENABLE APIS AND SERVICES**
5. Search for **Google Chat API** and enable it

### Step 2: Configure the Chat App

1. Go to [Google Chat API Configuration](https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat)
2. Click **Configuration** tab
3. Fill in the details:

   **App name:** Employee Portal Approvals
   **Avatar URL:** `https://fonts.gstatic.com/s/i/productlogos/calendar/v7/192px.svg`
   **Description:** Time-off approval bot for Employee Portal

4. **Interactive features:**
   - ✓ Enable Interactive features
   - ✓ Receive 1:1 messages
   - ✓ Join spaces and group conversations

5. **Connection settings:**
   - Select **HTTP endpoint (webhook)**
   - **Webhook URL:**
     - Development: `https://your-ngrok-url.ngrok.io/api/chat/webhook`
     - Production: `https://employee-portal-5n2ivebvra-uc.a.run.app/api/chat/webhook`

6. **Slash commands:** (Optional)
   - `/pending` - Show pending approvals
   - `/help` - Show help

7. **Permissions:**
   - Select who can install: **Specific people and groups in your domain**
   - Add your email or group

8. Click **Save**

### Step 3: Expose Webhook for Development (Local Testing)

Since Google Chat needs a public HTTPS URL, use ngrok for local development:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start ngrok tunnel to your local backend
ngrok http 8080

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update the webhook URL in Google Chat API Configuration:
# https://abc123.ngrok.io/api/chat/webhook
```

### Step 4: Install the Bot in Google Chat

1. Open [Google Chat](https://chat.google.com)
2. Click **+** next to "Chat"
3. Search for "Employee Portal Approvals"
4. Click **Add** or **Message**
5. The bot will send you a welcome message

### Step 5: Test the Bot

Send these messages to test:

```
help
status
pending
```

### Step 6: Integrate with NotificationService

Update your `notification_service.py` to send Chat cards when time-off requests are created:

```python
from googleapiclient.discovery import build
import requests

class NotificationService:
    def send_timeoff_approval_notification(self, approver_email, employee_name,
                                           employee_email, start_date, end_date,
                                           days_count, timeoff_type, notes,
                                           request_id, approval_level):
        # Existing email/task notification code...

        # Send to Google Chat
        self._send_chat_card(
            approver_email=approver_email,
            request_id=request_id,
            employee_name=employee_name,
            employee_email=employee_email,
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            timeoff_type=timeoff_type,
            notes=notes,
            approval_level=approval_level
        )

    def _send_chat_card(self, approver_email, **kwargs):
        """Send approval card to Google Chat"""
        try:
            # Build Chat API client
            chat_service = build('chat', 'v1', credentials=self.credentials)

            # Find or create DM space with approver
            # This requires the Chat API and proper OAuth scopes
            # For now, you can use the /api/chat/send-approval-card endpoint

            # Option 1: Direct Chat API call
            # space_name = self._get_or_create_dm_space(approver_email)
            # chat_service.spaces().messages().create(...)

            # Option 2: Internal API call (simpler for now)
            requests.post('http://localhost:8080/api/chat/send-approval-card', json={
                'request_id': kwargs['request_id'],
                'employee_name': kwargs['employee_name'],
                'employee_email': kwargs['employee_email'],
                'start_date': kwargs['start_date'],
                'end_date': kwargs['end_date'],
                'days_count': kwargs['days_count'],
                'timeoff_type': kwargs['timeoff_type'],
                'notes': kwargs.get('notes', ''),
                'approval_level': kwargs['approval_level']
            })
        except Exception as e:
            logger.error(f"Failed to send Chat card: {e}")
```

## Interactive Card Example

When a time-off request is created, the approver receives a card like this:

```
╔══════════════════════════════════════╗
║  Time-Off Request Approval (Manager) ║
║  Request from John Doe               ║
╠══════════════════════════════════════╣
║ Request Details                      ║
║                                      ║
║ Employee                             ║
║ John Doe                             ║
║ john@edvolution.io                   ║
║                                      ║
║ Time-Off Type                        ║
║ 🪑 Vacation                          ║
║                                      ║
║ Duration                             ║
║ 📅 2025-12-20 to 2025-12-27          ║
║ 7 day(s)                             ║
║                                      ║
║ Notes                                ║
║ Family vacation to the mountains     ║
║                                      ║
║  [✓ Approve]    [✗ Reject]          ║
╚══════════════════════════════════════╝
```

## Workflow

### Manager Approval Flow

1. Employee creates time-off request via portal
2. Manager receives interactive card in Google Chat
3. Manager clicks **✓ Approve** button
4. System updates request status to "Manager Approved"
5. Admin receives interactive card in Google Chat
6. Manager receives confirmation message

### Admin Approval Flow

1. Admin receives card after manager approval
2. Admin clicks **✓ Approve** button
3. System marks request as "Approved" (final)
4. Employee receives notification
5. Admin receives confirmation message

### Rejection Flow

1. Manager or Admin clicks **✗ Reject** button
2. System marks request as "Rejected"
3. Employee receives rejection notification
4. Approver receives confirmation

## Testing Locally

### Test the webhook endpoint:

```bash
# Test ADDED_TO_SPACE event
curl -X POST http://localhost:8080/api/chat/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ADDED_TO_SPACE",
    "space": {"type": "ROOM"},
    "user": {"displayName": "Test User"}
  }'

# Test MESSAGE event
curl -X POST http://localhost:8080/api/chat/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "MESSAGE",
    "message": {"text": "help"},
    "user": {"displayName": "Test User"}
  }'

# Test health check
curl http://localhost:8080/api/chat/test
```

## Deployment

### Update CORS Settings

Make sure Google Chat can access your webhook. In `main.py`:

```python
CORS(app, supports_credentials=True, origins=[
    'http://localhost:3000',
    'http://localhost:8080',
    'https://*.run.app',
    'https://employee-portal-5n2ivebvra-uc.a.run.app',
    'https://chat.googleapis.com'  # Add this
])
```

### Production Webhook URL

After deploying to Cloud Run:

```
https://employee-portal-5n2ivebvra-uc.a.run.app/api/chat/webhook
```

Update this URL in the Google Chat API Configuration.

## Required OAuth Scopes

Add these scopes to your Google OAuth consent screen:

- `https://www.googleapis.com/auth/chat.bot` - For bot interactions
- `https://www.googleapis.com/auth/chat.spaces` - For space management
- `https://www.googleapis.com/auth/chat.messages` - For sending messages

## Security Considerations

1. **Webhook Verification** - Consider adding signature verification for production:
   ```python
   # Verify requests are from Google Chat
   # https://developers.google.com/chat/api/guides/message-formats/events#verify-authenticity
   ```

2. **Permission Validation** - Already implemented in the code:
   - Managers can only approve their direct reports
   - Admins can approve any request
   - All actions are logged

3. **Rate Limiting** - Consider adding rate limiting for webhook endpoints

## Troubleshooting

### Bot doesn't respond
- Check ngrok is running and URL is correct
- Verify webhook URL in Google Chat API Configuration
- Check backend logs: `tail -f backend.log`

### Permission errors
- Ensure user email matches in event and database
- Check ADMIN_USERS in .env file
- Verify manager_email in employee records

### Cards don't appear
- Verify JSON structure matches Google Chat card format
- Check Chat API is enabled
- Ensure proper OAuth scopes are granted

### Approval notifications not received

**SOLUTION: Domain-Wide Delegation Required**

Proactive Google Chat notifications require **domain-wide delegation** to be configured. This allows the service account to impersonate an admin user and send DM messages on their behalf (just like Google Drive sends you notifications).

**Setup Status:**
- ✅ Code is updated to support domain-wide delegation
- ⚠️ **Admin Console configuration required** (see [DOMAIN_WIDE_DELEGATION_SETUP.md](DOMAIN_WIDE_DELEGATION_SETUP.md))

**After domain-wide delegation is configured:**
- ✅ Managers receive Google Chat cards automatically when time-off requests are created
- ✅ Admins receive Google Chat cards when manager approves
- ✅ Employees receive Google Chat status updates
- ✅ All users also receive email notifications

**Without domain-wide delegation:**
- ❌ No proactive Chat notifications
- ✅ Users receive **email notifications** for approvals
- ✅ The bot CAN respond to commands like `pending`, `help`, `status`
- ✅ Users can check pending approvals by messaging the bot with `pending`

**To enable proactive Chat notifications:**
1. Follow the setup guide: [DOMAIN_WIDE_DELEGATION_SETUP.md](DOMAIN_WIDE_DELEGATION_SETUP.md)
2. Update Google Workspace Admin Console with the OAuth scope: `https://www.googleapis.com/auth/chat.messages`
3. Wait 10-15 minutes for changes to propagate
4. Test by creating a time-off request

If Chat notifications still aren't working after setup:

1. **Check if Chat notifications are enabled:**
   ```bash
   # In .env file
   ENABLE_CHAT_NOTIFICATIONS=true
   ```

2. **Verify the bot has been added to a DM with the user:**
   - Open Google Chat
   - Search for "Employee Portal Approvals" (or your bot name)
   - Start a conversation with the bot
   - Send "help" to verify it responds

3. **Check Application Default Credentials:**
   The bot uses ADC (Application Default Credentials) to send messages, not user OAuth credentials.

   For Cloud Run (production):
   - The service account is automatically used
   - No additional configuration needed

   For local development:
   - Install gcloud CLI
   - Run: `gcloud auth application-default login`
   - This creates local ADC credentials

4. **Test the notification system:**
   ```bash
   python3 test_chat_notification.py
   ```
   Enter your email when prompted to test if messages are delivered.

5. **Check Cloud Run logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=employee-portal" --limit 50 --format=json
   ```
   Look for errors like:
   - "Failed to send approval card"
   - "Could not find existing DM space"
   - "Failed to create DM space"

6. **Verify the bot can create DM spaces:**
   The bot must have the `chat.bot` scope to create DM spaces and send messages.
   This is configured automatically when using Application Default Credentials.

## Next Steps

1. ✅ Implement Google Chat API client in NotificationService
2. ✅ Add space management (DM creation)
3. ✅ Add webhook signature verification
4. ✅ Add rejection reason dialog
5. ✅ Add audit logging for Chat actions
6. ✅ Monitor and analytics

## Resources

- [Google Chat API Documentation](https://developers.google.com/chat)
- [Interactive Card Designer](https://addons.gsuite.google.com/uikit/builder)
- [Webhook Guide](https://developers.google.com/chat/api/guides/message-formats/events)
- [Card Reference](https://developers.google.com/chat/api/reference/rest/v1/cards)

## Support

For issues or questions, check:
- Backend logs: `tail -f backend.log`
- Test endpoint: `http://localhost:8080/api/chat/test`
- Google Chat API logs in GCP Console
