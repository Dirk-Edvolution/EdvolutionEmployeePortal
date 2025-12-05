# Quick Setup Checklist

Follow these steps in order:

## ☑️ Step 1: Verify Prerequisites

```bash
gcloud --version  # Should show version
python3 --version # Should be 3.9+
```

## ☑️ Step 2: Login to Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

## ☑️ Step 3: Set Your Project

```bash
# Replace with YOUR project ID
gcloud config set project YOUR-PROJECT-ID
```

## ☑️ Step 4: Run Automated Setup

```bash
cd /home/dirk/employee-portal
./setup-gcp.sh
```

This enables all APIs and creates Firestore database.

## ☑️ Step 5: Create OAuth Credentials

**MANUAL STEP - Do this in browser:**

1. Go to: https://console.cloud.google.com/apis/credentials/consent
   - Select "Internal"
   - App name: "Employee Portal"
   - Save

2. Add scopes - paste all these:
   ```
   openid
   https://www.googleapis.com/auth/userinfo.email
   https://www.googleapis.com/auth/userinfo.profile
   https://www.googleapis.com/auth/admin.directory.user
   https://www.googleapis.com/auth/admin.directory.user.readonly
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/calendar.events
   https://www.googleapis.com/auth/gmail.settings.basic
   https://www.googleapis.com/auth/gmail.settings.sharing
   ```

3. Create OAuth Client:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Type: Web application
   - Redirect URI: `http://localhost:8080/auth/callback`
   - **SAVE THE CLIENT ID AND SECRET!**

4. Enable Domain-wide Delegation:
   - Go to: https://admin.google.com/ac/owl/domainwidedelegation
   - Add new
   - Paste Client ID and all scopes
   - Authorize

## ☑️ Step 6: Configure Application

```bash
cd /home/dirk/employee-portal
cp .env.example .env
nano .env
```

Update these values:
- `GCP_PROJECT_ID` - Your project ID
- `GOOGLE_CLIENT_ID` - From step 5
- `GOOGLE_CLIENT_SECRET` - From step 5
- `WORKSPACE_DOMAIN` - Your company domain
- `ADMIN_USERS` - Admin email addresses

Generate Flask secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## ☑️ Step 7: Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ☑️ Step 8: Run the Application

```bash
python -m backend.app.main
```

Open: http://localhost:8080

## ☑️ Step 9: Initial Setup

1. Login at: http://localhost:8080/auth/login
2. Sync employees (use browser console):
   ```javascript
   fetch('/api/employees/sync', {method: 'POST', credentials: 'include'})
     .then(r => r.json()).then(console.log)
   ```

## ✅ Done!

Your employee portal is now running locally!

---

## Deploy to Production

When ready:

```bash
./deploy.sh production
./setup-secrets.sh
```

Then add your Cloud Run URL to OAuth redirect URIs.
