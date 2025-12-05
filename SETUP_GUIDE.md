# Employee Portal - Complete Setup Guide

This guide will walk you through setting up the Employee Portal from scratch on Google Cloud Platform.

## Table of Contents
1. [Google Cloud Setup](#google-cloud-setup)
2. [Google Workspace Configuration](#google-workspace-configuration)
3. [OAuth Configuration](#oauth-configuration)
4. [Local Development](#local-development)
5. [Production Deployment](#production-deployment)
6. [Post-Deployment](#post-deployment)

---

## Google Cloud Setup

### 1. Create or Select a Project

```bash
# Create a new project
gcloud projects create employee-portal-prod --name="Employee Portal"

# Set as active project
gcloud config set project employee-portal-prod
```

### 2. Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    admin.googleapis.com \
    calendar-json.googleapis.com \
    gmail.googleapis.com \
    cloudbuild.googleapis.com
```

### 3. Initialize Firestore

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Add your GCP project
3. Navigate to Firestore Database
4. Click "Create Database"
5. Select "Production mode"
6. Choose location: `us-central1` (or your preferred region)

Alternatively, use `gcloud`:

```bash
gcloud firestore databases create --region=us-central1
```

---

## Google Workspace Configuration

### 1. Verify Domain Ownership

Ensure your Google Workspace domain is verified in Google Cloud Console:

1. Go to [Cloud Console](https://console.cloud.google.com)
2. Navigate to "IAM & Admin" > "Settings"
3. Verify your domain is listed

### 2. Grant Super Admin Access

The account used for setup must have:
- Super Admin role in Google Workspace
- Project Owner or Editor role in GCP

---

## OAuth Configuration

### 1. Create OAuth Consent Screen

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to "APIs & Services" > "OAuth consent screen"
3. Select "Internal" (for Workspace users only)
4. Fill in:
   - **App name**: Employee Portal
   - **User support email**: Your admin email
   - **Developer contact**: Your admin email
5. Click "Save and Continue"

### 2. Add OAuth Scopes

Add the following scopes:

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

### 3. Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. Application type: "Web application"
4. Name: "Employee Portal"
5. Authorized redirect URIs:
   - `http://localhost:8080/auth/callback` (for development)
   - `https://YOUR-SERVICE-URL/auth/callback` (add after deployment)
6. Click "Create"
7. **Save the Client ID and Client Secret** - you'll need these!

### 4. Enable Domain-wide Delegation

1. In the Credentials page, find your OAuth 2.0 Client
2. Copy the **Client ID** (numeric format)
3. Go to [Google Workspace Admin Console](https://admin.google.com)
4. Navigate to "Security" > "Access and data control" > "API Controls"
5. Click "Manage Domain Wide Delegation"
6. Click "Add new"
7. Enter:
   - **Client ID**: Paste the Client ID from step 2
   - **OAuth Scopes**: Paste all the scopes from step 2 above
8. Click "Authorize"

---

## Local Development

### 1. Clone and Setup

```bash
cd /home/dirk/employee-portal

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env
```

Fill in these required values:

```bash
GCP_PROJECT_ID=employee-portal-prod
GCP_LOCATION=us-central1

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

WORKSPACE_DOMAIN=yourcompany.com
WORKSPACE_ADMIN_EMAIL=admin@yourcompany.com

FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=development
PORT=8080

ADMIN_USERS=admin@yourcompany.com,chro@yourcompany.com
```

### 3. Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 4. Run Locally

```bash
python -m backend.app.main
```

Open browser to `http://localhost:8080`

### 5. Test the Flow

1. Click login and authenticate with your Workspace account
2. As admin, navigate to `/api/employees/sync` to sync all users
3. Test creating a time-off request
4. Test the approval workflow

---

## Production Deployment

### 1. Prepare for Deployment

```bash
# Ensure you're in the project directory
cd /home/dirk/employee-portal

# Set environment variables for deployment
export GCP_PROJECT_ID=employee-portal-prod
export GCP_LOCATION=us-central1
export WORKSPACE_DOMAIN=yourcompany.com
export ADMIN_USERS=admin@yourcompany.com,chro@yourcompany.com
```

### 2. Deploy to Cloud Run

```bash
# Run the deployment script
./deploy.sh production
```

The script will:
- Build the Docker container
- Push to Google Container Registry
- Deploy to Cloud Run
- Output the service URL

### 3. Configure Secrets

```bash
# Run the secrets setup script
./setup-secrets.sh
```

You'll be prompted for:
- Google OAuth Client ID
- Google OAuth Client Secret
- Workspace Admin Email

The script will:
- Create secrets in Secret Manager
- Grant Cloud Run access to secrets
- Update the service to use secrets

### 4. Update OAuth Redirect URI

1. Copy the Cloud Run service URL from deployment output
2. Go to [Google Cloud Console](https://console.cloud.google.com)
3. Navigate to "APIs & Services" > "Credentials"
4. Edit your OAuth 2.0 Client
5. Add authorized redirect URI: `https://YOUR-SERVICE-URL/auth/callback`
6. Click "Save"

### 5. Update Environment Variables

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe employee-portal --region us-central1 --format 'value(status.url)')

# Update redirect URI
gcloud run services update employee-portal \
    --region us-central1 \
    --set-env-vars GOOGLE_REDIRECT_URI=${SERVICE_URL}/auth/callback
```

---

## Post-Deployment

### 1. Initial User Sync

1. Login to the portal as a super admin
2. Navigate to the admin panel
3. Click "Sync from Workspace" to import all users
4. Verify employees appear correctly

### 2. Configure Manager Relationships

For each employee:
1. Go to employee profile (admin view)
2. Set their manager using the manager email field
3. Save changes (this syncs back to Workspace)

### 3. Set Vacation Policies

For employees in different countries/regions:
1. Edit employee profile
2. Set `country` and `region` fields
3. Set `vacation_days_per_year` according to policy
4. Save changes

### 4. Test Complete Workflow

**As Employee:**
1. Login with your Workspace account
2. View your vacation summary
3. Create a time-off request
4. Wait for approvals

**As Manager:**
1. Login as a manager
2. View pending approvals
3. Approve the request

**As Admin:**
1. Login as admin
2. View manager-approved requests
3. Give final approval

**Back as Employee:**
1. View approved request
2. Sync to Google Calendar
3. Enable Gmail auto-responder
4. Verify calendar shows OOO
5. Verify Gmail has vacation responder

---

## Monitoring and Maintenance

### View Logs

```bash
# View recent logs
gcloud run services logs read employee-portal --region us-central1 --limit 50

# Stream logs
gcloud run services logs tail employee-portal --region us-central1
```

### Update the Application

```bash
# Make your code changes, then redeploy
./deploy.sh production
```

### Backup Firestore

```bash
# Export Firestore data
gcloud firestore export gs://employee-portal-backups/$(date +%Y%m%d)
```

---

## Troubleshooting

### Issue: "Not authenticated" error

**Solution:** Clear browser cookies and try logging in again.

### Issue: "Admin directory API not enabled"

**Solution:**
```bash
gcloud services enable admin.googleapis.com
```

### Issue: "Insufficient permissions"

**Solution:**
1. Verify Domain-wide Delegation is configured
2. Check OAuth scopes are correct
3. Ensure you're using a super admin account

### Issue: Calendar/Gmail integration not working

**Solution:**
1. Verify user has granted all OAuth scopes
2. Check user consented to all permissions
3. User may need to logout and login again

---

## Security Best Practices

1. **Secrets:** Never commit `.env` or credentials to version control
2. **Admin Access:** Limit admin users to HR and executive team
3. **Audit Logs:** Regularly review Cloud Run and Firestore logs
4. **Updates:** Keep dependencies updated with `pip install -U`
5. **HTTPS:** Always use HTTPS in production (Cloud Run does this automatically)

---

## Next Steps

Now that your Employee Portal is set up:

1. **Build the Frontend:** Create a React UI for better UX
2. **Add Email Notifications:** Integrate SendGrid or Cloud Messaging
3. **Reporting:** Build vacation analytics dashboard
4. **Mobile App:** Consider a mobile interface
5. **Integrations:** Add Slack notifications for approvals

---

## Support

For questions or issues:
- Check the logs: `gcloud run services logs read employee-portal`
- Review Firestore data in Firebase Console
- Contact your GCP admin or development team

---

**Congratulations!** Your Employee Portal is now live and ready to use! 🎉
