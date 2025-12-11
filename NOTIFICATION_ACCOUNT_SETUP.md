# Notification Account Setup - hola@edvolution.io

This document explains how to set up a dedicated notification account for sending automated emails and Chat messages.

## Overview

The Employee Portal uses a dedicated Google Workspace account (`hola@edvolution.io`) to send all automated notifications:
- Email notifications (via Gmail API)
- Google Chat notifications (via Chat API)
- Google Tasks reminders (via Tasks API)

This approach is simpler and more reliable than using service accounts with domain-wide delegation.

## Why Use a Dedicated Notification Account?

✅ **Emails Work**: Real Gmail account can send emails via Gmail API
✅ **Chat Works**: Real user can send Chat DMs to other users
✅ **Tasks Work**: Can create tasks in other users' task lists
✅ **Simpler**: No complex domain-wide delegation setup needed
✅ **Audit Trail**: All notifications come from a recognizable "system" account

## Setup Steps

### Step 1: Create/Verify the Notification Account

1. Ensure `hola@edvolution.io` exists in Google Workspace
2. Set a strong password
3. Enable 2FA (recommended but optional)

### Step 2: Generate OAuth Credentials

1. **Log in as `hola@edvolution.io`** to the Employee Portal
2. Go to: `https://employee-portal-844588465159.us-central1.run.app/auth/login`
3. **Authorize all requested scopes**:
   - Gmail (for sending emails)
   - Chat (for sending Chat messages)
   - Tasks (for creating reminders)
   - Calendar (for OOO events)
4. **Copy the OAuth tokens** (will be stored in session)

### Step 3: Store Credentials in Secret Manager

The credentials need to be stored in Google Secret Manager so the backend can use them.

**Create the secret:**
```bash
# First, get the OAuth credentials from hola@edvolution.io's session
# Then create a secret with the credentials JSON

gcloud secrets create notification-account-credentials \
  --data-file=hola-credentials.json \
  --project=edvolution-admon
```

**Grant the service account access:**
```bash
gcloud secrets add-iam-policy-binding notification-account-credentials \
  --member="serviceAccount:employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=edvolution-admon
```

### Step 4: Update Environment Variables

Add to Cloud Run:
```bash
gcloud run services update employee-portal \
  --region us-central1 \
  --set-env-vars="NOTIFICATION_ACCOUNT_EMAIL=hola@edvolution.io"
```

### Step 5: Test

1. Create a time-off request
2. Manager should receive:
   - ✅ Email notification from hola@edvolution.io
   - ✅ Chat DM from hola@edvolution.io
   - ✅ Google Task reminder

## How It Works

```python
# When sending notifications:
1. Load credentials from Secret Manager for hola@edvolution.io
2. Use those credentials to:
   - Send email via Gmail API (as hola@edvolution.io)
   - Send Chat DM to manager (as hola@edvolution.io)
   - Create Task in manager's task list
```

## Security Considerations

- ✅ Credentials stored securely in Secret Manager (encrypted at rest)
- ✅ Only the service account can access the credentials
- ✅ All notifications clearly come from "hola@edvolution.io"
- ✅ Audit trail shows who created requests, not just that hola sent notifications
- ⚠️ If hola@ account is compromised, attacker could send notifications (but not access user data)

## Troubleshooting

### Emails not arriving
- Check hola@edvolution.io has Gmail enabled
- Verify Gmail API scope in credentials
- Check Secret Manager has valid credentials

### Chat messages not arriving
- Check hola@edvolution.io exists in Google Chat
- Verify Chat API scope in credentials
- Ensure target users have Chat enabled

### Credentials expired
- OAuth tokens expire after ~7 days of inactivity
- Re-authorize hola@edvolution.io via the portal
- Update credentials in Secret Manager

## Alternative: Refresh Token

For long-term automation, use a refresh token:

1. Generate offline access token for hola@edvolution.io
2. Store refresh token in Secret Manager
3. Backend automatically refreshes access tokens as needed
4. No manual re-authorization needed

This is the recommended approach for production.
