# Getting Started - Employee Portal Setup

Follow these steps to get your Employee Portal running from scratch.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Google Cloud Project created
- [ ] Google Workspace domain with Super Admin access
- [ ] Python 3.9+ installed
- [ ] Google Cloud SDK (gcloud CLI) installed

---

## Part 1: Install Prerequisites

### Install Google Cloud SDK

**On Linux/macOS:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

**On Windows:**
Download from: https://cloud.google.com/sdk/docs/install

**Verify installation:**
```bash
gcloud --version
python3 --version
```

---

## Part 2: Configure Google Cloud Project

### 1. Login to Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

### 2. Set Your Project

```bash
# Replace with your actual project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 3. Enable Required APIs

Copy and paste this entire block:

```bash
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable admin.googleapis.com
gcloud services enable calendar-json.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

This takes 2-3 minutes. Wait for it to complete.

### 4. Create Firestore Database

```bash
gcloud firestore databases create --region=us-central1
```

✅ **GCP setup complete!**

---

## Part 3: Configure OAuth Credentials

### Step 1: Create OAuth Consent Screen

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select **"Internal"** (for Workspace users only)
3. Fill in:
   - **App name**: `Employee Portal`
   - **User support email**: Your admin email
   - **Developer contact**: Your admin email
4. Click **"Save and Continue"**

### Step 2: Add OAuth Scopes

Click **"Add or Remove Scopes"** and add these:

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

Click **"Update"** then **"Save and Continue"**.

### Step 3: Create OAuth Client ID

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
3. Application type: **"Web application"**
4. Name: `Employee Portal`
5. **Authorized redirect URIs**:
   - Add: `http://localhost:8080/auth/callback`
6. Click **"Create"**

**IMPORTANT:** Save the **Client ID** and **Client Secret** that appear!

Example:
- Client ID: `123456789-abc123.apps.googleusercontent.com`
- Client Secret: `GOCSPX-abc123xyz789`

### Step 4: Enable Domain-wide Delegation

1. In the Credentials page, find your OAuth 2.0 Client
2. Click the edit icon (pencil)
3. Note the **Client ID** (just the numbers at the start)
4. Go to: https://admin.google.com/ac/owl/domainwidedelegation
5. Click **"Add new"**
6. Paste the **Client ID** (numeric part)
7. Paste all the OAuth scopes from Step 2 (comma-separated, no spaces)
8. Click **"Authorize"**

✅ **OAuth setup complete!**

---

## Part 4: Configure the Application

### 1. Navigate to Project Directory

```bash
cd /home/dirk/employee-portal
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Edit the .env File

Open the file:
```bash
nano .env
```

Update these values with YOUR information:

```bash
# Your GCP Project ID
GCP_PROJECT_ID=your-project-id-here

# Google OAuth (from Part 3, Step 3)
GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

# Your Workspace Domain
WORKSPACE_DOMAIN=yourcompany.com
WORKSPACE_ADMIN_EMAIL=admin@yourcompany.com

# Generate a secure secret key
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Admin users (comma-separated, no spaces)
ADMIN_USERS=admin@yourcompany.com,chro@yourcompany.com
```

**Press Ctrl+O to save, Ctrl+X to exit**

Or generate the secret key separately:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

✅ **Application configured!**

---

## Part 5: Run the Application Locally

### Start the Server

```bash
# Make sure you're in the project directory and venv is activated
cd /home/dirk/employee-portal
source venv/bin/activate

# Run the application
python -m backend.app.main
```

You should see:
```
 * Running on http://0.0.0.0:8080
```

### Test the Application

1. Open browser to: http://localhost:8080
2. You should see: `{"name": "Employee Portal API", "version": "1.0.0", "status": "running"}`
3. Go to: http://localhost:8080/auth/login
4. Login with your Google Workspace account
5. Grant all permissions when asked

### Initial Setup (First Time Only)

After logging in as an admin:

1. **Sync Employees from Workspace:**
   ```bash
   curl -X POST http://localhost:8080/api/employees/sync \
     -H "Cookie: session=YOUR_SESSION_COOKIE"
   ```

   Or use your browser's console:
   ```javascript
   fetch('/api/employees/sync', {method: 'POST', credentials: 'include'})
     .then(r => r.json()).then(console.log)
   ```

2. **Verify employees were synced:**
   ```bash
   curl http://localhost:8080/api/employees/ \
     -H "Cookie: session=YOUR_SESSION_COOKIE"
   ```

✅ **Application is running!**

---

## Part 6: Test the Complete Workflow

### As an Employee:

1. Login to: http://localhost:8080/auth/login
2. Check your profile:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt
   ```
3. Check vacation summary:
   ```bash
   curl http://localhost:8080/api/timeoff/vacation-summary -b cookies.txt
   ```
4. Create a time-off request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2024-12-20",
       "end_date": "2024-12-27",
       "timeoff_type": "vacation",
       "notes": "Christmas holidays"
     }'
   ```

### As a Manager:

1. Login as a manager account
2. View pending approvals:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/pending-approval -b cookies.txt
   ```
3. Approve a request (replace REQUEST_ID):
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/approve-manager \
     -b cookies.txt
   ```

### As an Admin:

1. Login as an admin
2. View manager-approved requests:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/pending-approval -b cookies.txt
   ```
3. Final approval:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/approve-admin \
     -b cookies.txt
   ```

### After Approval (Employee):

1. Sync to Google Calendar:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/sync-calendar \
     -b cookies.txt
   ```
2. Enable Gmail auto-responder:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/enable-autoresponder \
     -b cookies.txt
   ```

✅ **Complete workflow tested!**

---

## Part 7: Deploy to Production (Cloud Run)

Once everything works locally, deploy to production:

### 1. Update OAuth Redirect URI

Before deploying, you need to know your Cloud Run URL. First deployment:

```bash
cd /home/dirk/employee-portal
./deploy.sh production
```

The script will output your service URL, like:
```
https://employee-portal-abc123-uc.a.run.app
```

### 2. Add Production Redirect URI

1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client
3. Add authorized redirect URI:
   ```
   https://employee-portal-abc123-uc.a.run.app/auth/callback
   ```
4. Save

### 3. Set Up Secrets

```bash
./setup-secrets.sh
```

Enter your OAuth credentials when prompted.

### 4. Update Environment Variables

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe employee-portal --region us-central1 --format 'value(status.url)')

# Update the redirect URI
gcloud run services update employee-portal \
  --region us-central1 \
  --set-env-vars GOOGLE_REDIRECT_URI=${SERVICE_URL}/auth/callback \
  --set-env-vars FLASK_ENV=production
```

### 5. Test Production

Open your Cloud Run URL in a browser and test the login flow!

✅ **Production deployment complete!**

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied" errors
```bash
# Make sure scripts are executable
chmod +x *.sh
```

### "Not authenticated" in API calls
- Clear cookies and login again
- Check that session cookies are being sent

### OAuth errors
- Verify redirect URI matches exactly
- Check Domain-wide Delegation is configured
- Ensure all scopes are added

### Firestore errors
- Ensure Firestore database is created
- Check application default credentials: `gcloud auth application-default login`

---

## Next Steps

Now that your portal is running:

1. **Build a Frontend UI** - Create React interface in `frontend/`
2. **Add Email Notifications** - Integrate SendGrid or similar
3. **Customize Workflow** - Adjust approval logic as needed
4. **Add Analytics** - Track vacation usage patterns
5. **Mobile Access** - Consider a mobile-friendly UI

---

## Quick Reference

**Start development server:**
```bash
cd /home/dirk/employee-portal
source venv/bin/activate
python -m backend.app.main
```

**Deploy to production:**
```bash
./deploy.sh production
```

**View logs:**
```bash
gcloud run services logs read employee-portal --region us-central1 --limit 50
```

**Access Firestore data:**
https://console.firebase.google.com/

---

**Need help?** Check [README.md](README.md), [SETUP_GUIDE.md](SETUP_GUIDE.md), and [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
