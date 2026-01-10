# Deployment Instructions: Employee Portal with Trip & Asset Management

## Prerequisites

- Google Cloud Project with billing enabled
- GitHub repository access
- gcloud CLI installed and authenticated
- Node.js and npm installed (for frontend build)

---

## Part 1: Google Cloud Console Setup

### 1.1 Configure OAuth Consent Screen & Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services > OAuth consent screen**
4. Ensure all required scopes are added:
   - openid
   - userinfo.email
   - userinfo.profile
   - admin.directory.user
   - calendar
   - gmail.send
   - chat.messages
   - tasks
   - **drive.file** ⬅️ NEW
   - **spreadsheets** ⬅️ NEW

5. Navigate to **APIs & Services > Credentials**
6. Click on your OAuth 2.0 Client ID
7. Add **Authorized redirect URIs**:
   ```
   https://rrhh.edvolution.io/auth/callback
   https://papepe.edvolution.io/auth/callback
   http://localhost:8080/auth/callback (for local testing)
   ```

### 1.2 Enable Required APIs

Ensure these APIs are enabled in your project:
- Cloud Firestore API
- Google Drive API ⬅️ NEW
- Google Sheets API ⬅️ NEW
- Cloud Run API
- Cloud Build API
- Gmail API
- Google Calendar API
- Google Chat API
- Google Tasks API
- Admin SDK API

**Enable them with:**
```bash
gcloud services enable firestore.googleapis.com
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable calendar-json.googleapis.com
gcloud services enable chat.googleapis.com
gcloud services enable tasks.googleapis.com
gcloud services enable admin.googleapis.com
```

### 1.3 Configure Firestore

1. Go to **Firestore > Data**
2. Ensure database is in **Native mode**
3. The following collections will be auto-created on first use:
   - `employees`
   - `timeoff_requests`
   - `trip_requests` ⬅️ NEW
   - `trip_justifications` ⬅️ NEW
   - `asset_requests` ⬅️ NEW
   - `employee_assets` ⬅️ NEW
   - `asset_audit_logs` ⬅️ NEW
   - `audit_logs`

---

## Part 2: Local Development Setup

### 2.1 Clone and Configure Repository

```bash
# Clone the repository
git clone https://github.com/Dirk-Edvolution/EdvolutionEmployeePortal.git
cd EdvolutionEmployeePortal

# Checkout the feature branch
git checkout claude/extend-approval-workflow-qcf8s

# Pull latest changes
git pull origin claude/extend-approval-workflow-qcf8s
```

### 2.2 Backend Configuration

Create `.env` file in the `backend/` directory:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

# Google Workspace Configuration
WORKSPACE_DOMAIN=edvolution.io
WORKSPACE_ADMIN_EMAIL=admin@edvolution.io

# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=development
PORT=8080

# Admin Users (semicolon or comma separated)
ADMIN_USERS=admin1@edvolution.io;admin2@edvolution.io

# Firestore Collections (defaults are fine, or customize)
EMPLOYEES_COLLECTION=employees
TIMEOFF_REQUESTS_COLLECTION=timeoff_requests
TRIP_REQUESTS_COLLECTION=trip_requests
TRIP_JUSTIFICATIONS_COLLECTION=trip_justifications
ASSET_REQUESTS_COLLECTION=asset_requests
EMPLOYEE_ASSETS_COLLECTION=employee_assets
ASSET_AUDIT_LOGS_COLLECTION=asset_audit_logs

# Notification Configuration
ENABLE_CHAT_NOTIFICATIONS=true
ENABLE_TASK_NOTIFICATIONS=true
```

### 2.3 Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2.4 Build Frontend

```bash
cd frontend
npm run build
```

This creates `frontend/dist/` directory that Flask serves.

### 2.5 Run Locally

```bash
cd backend
python -m app.main
```

Access at `http://localhost:8080`

---

## Part 3: Deploy to Cloud Run

### 3.1 Set Environment Variables

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export SERVICE_NAME=employee-portal
```

### 3.2 Build Frontend for Production

```bash
cd frontend
npm run build
cd ..
```

### 3.3 Deploy to Cloud Run

```bash
# From project root directory
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars "GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com" \
  --set-env-vars "GOOGLE_CLIENT_SECRET=your-client-secret" \
  --set-env-vars "WORKSPACE_DOMAIN=edvolution.io" \
  --set-env-vars "WORKSPACE_ADMIN_EMAIL=admin@edvolution.io" \
  --set-env-vars "FLASK_SECRET_KEY=your-production-secret-key" \
  --set-env-vars "FLASK_ENV=production" \
  --set-env-vars "ADMIN_USERS=admin1@edvolution.io;admin2@edvolution.io" \
  --set-env-vars "ENABLE_CHAT_NOTIFICATIONS=true" \
  --set-env-vars "ENABLE_TASK_NOTIFICATIONS=true" \
  --max-instances 10 \
  --min-instances 0 \
  --memory 512Mi \
  --timeout 300
```

**Note:** The deployment will automatically use dynamic OAuth redirect URIs based on the request host.

### 3.4 Alternative: Deploy via Cloud Build

Create `cloudbuild.yaml` in project root:

```yaml
steps:
  # Build frontend
  - name: 'node:18'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['install']

  - name: 'node:18'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['run', 'build']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'employee-portal'
      - '--source=.'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'

options:
  logging: CLOUD_LOGGING_ONLY
```

Then deploy:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

---

## Part 4: Domain Mapping

### 4.1 Map papepe.edvolution.io

```bash
# Map the domain to Cloud Run service
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain papepe.edvolution.io \
  --region $REGION
```

### 4.2 Update DNS Records

Follow the instructions from the command output to add DNS records to your domain registrar:
- **Type**: A or CNAME
- **Name**: papepe
- **Value**: (provided by Cloud Run)

### 4.3 Map rrhh.edvolution.io (if not already mapped)

```bash
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain rrhh.edvolution.io \
  --region $REGION
```

### 4.4 Verify Domain Mappings

```bash
gcloud run domain-mappings list --region $REGION
```

---

## Part 5: Post-Deployment Configuration

### 5.1 Initialize Data

1. Access the application at `https://papepe.edvolution.io`
2. Login with admin account
3. Sync employees from Google Workspace
4. Verify employee manager assignments

### 5.2 Test Workflows

**Test Time-Off Request (Existing):**
- Create a vacation request
- Verify manager receives notification
- Approve as manager
- Verify admin receives notification
- Approve as admin
- Verify calendar event creation

**Test Trip Request (New):**
- Create a trip request
- Verify manager approval workflow
- Verify admin approval workflow
- Check that Google Drive folder is created
- Check that expense spreadsheet is created and shared
- Test justification submission
- Test justification rejection/resubmission

**Test Asset Request (New):**
- Create asset request (keyboard, laptop, etc.)
- Verify approval workflow
- Verify asset is added to inventory
- Test manager editing asset inventory
- Verify audit log tracking

### 5.3 Monitor Logs

```bash
# View Cloud Run logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50

# Stream logs in real-time
gcloud run services logs tail $SERVICE_NAME --region $REGION
```

---

## Part 6: Rollback and Troubleshooting

### 6.1 Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service $SERVICE_NAME --region $REGION

# Rollback to specific revision
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions REVISION_NAME=100 \
  --region $REGION
```

### 6.2 Common Issues

**Issue: OAuth redirect URI mismatch**
- **Solution**: Ensure both `papepe.edvolution.io` and `rrhh.edvolution.io` are added to authorized redirect URIs in Google Cloud Console

**Issue: Drive API permission denied**
- **Solution**: Ensure user has granted Drive and Sheets scopes during OAuth consent

**Issue: Firestore permission denied**
- **Solution**: Verify Cloud Run service account has Firestore permissions

**Issue: CORS errors**
- **Solution**: Verify `papepe.edvolution.io` is in CORS origins list in `backend/app/main.py`

### 6.3 Debug Mode

To enable debug logs, set environment variable:

```bash
gcloud run services update $SERVICE_NAME \
  --set-env-vars "FLASK_ENV=development" \
  --region $REGION
```

---

## Part 7: Git Workflow

### 7.1 Commit Changes

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add trip and asset approval workflows

- Added trip request models and routes
- Added asset request models and inventory tracking
- Integrated Google Drive for expense tracking
- Extended approval workflow to trips and assets
- Added support for papepe.edvolution.io domain"

# Push to feature branch
git push -u origin claude/extend-approval-workflow-qcf8s
```

### 7.2 Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select base: `main` (or your main branch)
4. Select compare: `claude/extend-approval-workflow-qcf8s`
5. Title: "Add Trip and Asset Approval Workflows"
6. Description: Link to `IMPLEMENTATION_STATUS.md`
7. Request review from team
8. Merge after approval

---

## Part 8: Continuous Deployment (Optional)

### 8.1 Set up GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy employee-portal \
            --source . \
            --region us-central1 \
            --platform managed \
            --allow-unauthenticated
```

### 8.2 Add Secrets to GitHub

1. Go to repository Settings > Secrets and variables > Actions
2. Add secret: `GCP_SA_KEY` with service account JSON key

---

## Summary Checklist

- [ ] OAuth redirect URIs configured for both domains
- [ ] Drive and Sheets APIs enabled
- [ ] Required OAuth scopes added to consent screen
- [ ] Environment variables configured
- [ ] Frontend built successfully
- [ ] Deployed to Cloud Run
- [ ] Domain mappings created and DNS configured
- [ ] SSL certificates provisioned (automatic by Cloud Run)
- [ ] Admin users configured in ADMIN_USERS env var
- [ ] Tested time-off workflow (existing)
- [ ] Tested trip request workflow (new)
- [ ] Tested asset request workflow (new)
- [ ] Verified Drive folder creation
- [ ] Verified expense spreadsheet creation
- [ ] Verified asset inventory tracking
- [ ] Logs monitored for errors
- [ ] Branch merged to main (after testing)

---

## Support and Maintenance

- **Logs**: `gcloud run services logs read employee-portal --region us-central1`
- **Metrics**: Cloud Run > Services > employee-portal > Metrics
- **Errors**: Cloud Run > Services > employee-portal > Logs (filter by severity=ERROR)
- **Firestore**: Console > Firestore > Data (view/edit collections)
- **Drive Folders**: Shared drives or employee Google Drive (search "Trip -")

For issues, check `IMPLEMENTATION_STATUS.md` for what's completed and what might be pending.
