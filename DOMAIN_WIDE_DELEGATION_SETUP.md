# Domain-Wide Delegation Setup for Google Chat Notifications

This guide explains how to enable **domain-wide delegation** so the Employee Portal can send proactive Google Chat messages to users (like Google Drive does).

## Why Domain-Wide Delegation?

Google Chat bots with service accounts cannot proactively send DM messages **UNLESS** they use domain-wide delegation to impersonate users. This is how Google Workspace apps like Drive, Calendar, etc. send you notifications.

## Prerequisites

- Google Workspace Admin access
- Service account: `employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com`
- OAuth Client ID: `115131457162383560161`

---

## Step 1: Enable Domain-Wide Delegation on Service Account

1. Go to [Google Cloud Console - IAM & Admin - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?project=edvolution-admon)

2. Find service account: `employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com`

3. Click on the service account

4. Go to **"Advanced Settings"** section

5. Click **"Enable Google Workspace Domain-wide Delegation"**

6. Save the OAuth2 Client ID: `115131457162383560161`

---

## Step 2: Authorize API Scopes in Google Workspace Admin Console

1. Go to [Google Workspace Admin Console](https://admin.google.com)

2. Navigate to: **Security** → **Access and data control** → **API Controls**

3. Click **"Manage Domain Wide Delegation"**

4. Click **"Add new"**

5. Enter the Client ID: `115131457162383560161`

6. Add the following OAuth Scopes (comma-separated):
   ```
   https://www.googleapis.com/auth/chat.messages,https://www.googleapis.com/auth/chat.spaces
   ```

7. Click **"Authorize"**

---

## Step 3: Verify Configuration

Run this test to verify domain-wide delegation works:

```bash
python3 << 'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build

# This should be your service account credentials
SCOPES = [
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.spaces'
]

# Test impersonation
USER_EMAIL = 'dirk@edvolution.io'

try:
    from google.auth import default
    credentials, project = default(scopes=SCOPES)

    if hasattr(credentials, 'with_subject'):
        delegated_creds = credentials.with_subject(USER_EMAIL)
        chat = build('chat', 'v1', credentials=delegated_creds)
        print(f"✅ Domain-wide delegation is configured correctly!")
        print(f"   Service can impersonate: {USER_EMAIL}")
    else:
        print("❌ Credentials do not support domain-wide delegation")
        print("   Make sure you're using a service account with delegation enabled")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   Domain-wide delegation may not be set up correctly")
EOF
```

---

## Step 4: Update Application Code (Already Done)

The code has been updated to support domain-wide delegation:

### How It Works
1. **Admin Impersonation**: When sending notifications, the service impersonates `WORKSPACE_ADMIN_EMAIL` (dirk@edvolution.io)
2. **Credential Delegation**: `NotificationService._get_chat_service(impersonate_user=admin_email)` uses `credentials.with_subject(admin_email)`
3. **DM Space Creation**: Acting as the admin, the service finds or creates a DM space with the target user
4. **Message Delivery**: The interactive card is sent to the DM space
5. **User Experience**: The approver receives a Google Chat notification (just like Google Drive sends notifications)

### Code Changes
- `NotificationService._get_chat_service(impersonate_user=email)` - supports user impersonation
- `send_direct_message(user_email, message, impersonate_admin=email)` - uses delegation to send DMs
- `send_approval_chat_card(..., impersonate_admin=email)` - uses delegation to send interactive cards
- Both methods default to using `WORKSPACE_ADMIN_EMAIL` from settings

---

## Step 5: Test Proactive Notifications

After completing setup, test by creating a time-off request:

1. Log into the Employee Portal
2. Create a time-off request
3. The manager should receive:
   - ✅ Email notification (works now)
   - ✅ Google Chat DM (will work after domain-wide delegation)

Check logs:
```bash
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=employee-portal AND textPayload=~"domain-wide delegation"' --limit 10 --format="table(timestamp,textPayload)" --freshness=1h
```

---

## Security Considerations

**Domain-wide delegation is powerful** - it allows the service account to act as any user in your domain.

**Best practices:**
1. ✅ Only grant minimum required scopes (`chat.messages`, `chat.spaces`)
2. ✅ Limit to one service account
3. ✅ Monitor usage via Cloud Logging
4. ✅ Document who has access
5. ✅ Review periodically

**What the service can do:**
- ✅ Send Chat messages on behalf of users
- ✅ Create spaces on behalf of users
- ❌ Cannot read messages (we didn't request that scope)
- ❌ Cannot access other Google Workspace data (Drive, Gmail, etc.)

---

## Troubleshooting

### Error: "Request had insufficient authentication scopes"
- Make sure you authorized the scopes in Admin Console (Step 2)
- Wait 10-15 minutes for changes to propagate

### Error: "Domain-wide delegation is not enabled"
- Complete Step 1 to enable delegation on the service account
- Redeploy the application

### Still not working?
1. Check Admin Console → Security → API Controls → Domain-wide delegation
2. Verify Client ID matches: `115131457162383560161`
3. Verify scopes are exactly: `https://www.googleapis.com/auth/chat.messages,https://www.googleapis.com/auth/chat.spaces`
4. Check Cloud Run service account is `employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com`

---

## Alternative: Chat Space Instead of DMs

If you prefer not to use domain-wide delegation, you can:

1. **Create a Chat Space** (e.g., "HR Approvals")
2. **Add all managers/admins** to the space
3. **Add the bot** to the space
4. **Send notifications to the space** instead of DMs

This way:
- ✅ No domain-wide delegation needed
- ✅ All approvers see all requests
- ✅ Transparent approval process
- ❌ Less private (everyone sees everyone's requests)

---

## Resources

- [Domain-Wide Delegation Guide](https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority)
- [Google Chat API - User Authentication](https://developers.google.com/workspace/chat/authenticate-authorize-chat-user)
- [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes#chat)
