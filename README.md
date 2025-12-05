# Employee Portal - Vacation & Time-off Management System

A comprehensive employee portal for managing vacations and time-off requests, built on Google Cloud Platform with Google Workspace integration.

## Features

- **Google Workspace SSO** - Employees login with their Google Workspace accounts
- **Employee Management** - Automatically sync employee data from Workspace Admin Console
- **Bidirectional Sync** - Update employee profiles and sync back to Workspace
- **Manager Hierarchies** - Admin portal to manage employee-manager relationships
- **Time-off Requests** - Submit vacation, sick leave, and day off requests
- **Two-tier Approval** - Requires both manager AND admin approval
- **Google Calendar Integration** - Auto-sync approved time-off to calendar as OOO
- **Gmail Auto-responder** - Enable vacation responder automatically
- **Vacation Tracking** - View used and remaining vacation days
- **Flexible Policies** - Configurable vacation days per country/region/employee

## Technology Stack

### Backend
- Python 3.11
- Flask web framework
- Google Cloud Firestore (database)
- Google Workspace Admin SDK
- Google Calendar API
- Gmail API
- Google Cloud Run (hosting)

### Frontend
- React (to be implemented)
- Modern responsive UI

## Project Structure

```
employee-portal/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── auth_routes.py
│   │   │   ├── employee_routes.py
│   │   │   └── timeoff_routes.py
│   │   ├── models/           # Data models
│   │   │   ├── employee.py
│   │   │   └── timeoff_request.py
│   │   ├── services/         # Business logic services
│   │   │   ├── firestore_service.py
│   │   │   ├── workspace_service.py
│   │   │   ├── calendar_service.py
│   │   │   └── gmail_service.py
│   │   ├── utils/            # Utilities
│   │   │   └── auth.py
│   │   └── main.py           # Flask application
│   └── config/
│       └── settings.py       # Configuration
├── frontend/                 # React frontend (to be built)
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Setup Instructions

### Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   - Cloud Firestore API
   - Cloud Run API
   - Secret Manager API
   - Admin SDK API
   - Calendar API
   - Gmail API

2. **Google Workspace** with super admin access

3. **Google Cloud SDK** installed locally

### Step 1: Configure Google Workspace OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Select "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8080/auth/callback` (development)
   - `https://your-cloud-run-url/auth/callback` (production)
7. Save the Client ID and Client Secret

### Step 2: Enable Domain-wide Delegation (for Admin SDK)

1. Go to "APIs & Services" > "Credentials"
2. Find your OAuth client and note the Client ID
3. Go to your [Google Workspace Admin Console](https://admin.google.com)
4. Navigate to "Security" > "API Controls" > "Domain-wide Delegation"
5. Click "Add new" and enter:
   - Client ID: Your OAuth Client ID
   - OAuth Scopes:
     ```
     https://www.googleapis.com/auth/admin.directory.user,
     https://www.googleapis.com/auth/admin.directory.user.readonly,
     https://www.googleapis.com/auth/calendar,
     https://www.googleapis.com/auth/gmail.settings.basic
     ```

### Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   GCP_PROJECT_ID=your-project-id
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   WORKSPACE_DOMAIN=yourcompany.com
   WORKSPACE_ADMIN_EMAIL=admin@yourcompany.com
   ADMIN_USERS=admin@yourcompany.com,chro@yourcompany.com
   FLASK_SECRET_KEY=generate-a-secure-random-key
   ```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run Locally

```bash
python -m backend.app.main
```

The application will be available at `http://localhost:8080`

### Step 6: Deploy to Cloud Run

1. Build and push container:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/employee-portal
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy employee-portal \
     --image gcr.io/YOUR_PROJECT_ID/employee-portal \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID \
     --set-env-vars WORKSPACE_DOMAIN=yourcompany.com \
     --set-env-vars ADMIN_USERS=admin@yourcompany.com
   ```

3. Set secrets in Cloud Run:
   ```bash
   # Store secrets in Secret Manager
   echo -n "your-client-id" | gcloud secrets create google-client-id --data-file=-
   echo -n "your-client-secret" | gcloud secrets create google-client-secret --data-file=-
   echo -n "your-flask-secret" | gcloud secrets create flask-secret-key --data-file=-

   # Update Cloud Run to use secrets
   gcloud run services update employee-portal \
     --update-secrets GOOGLE_CLIENT_ID=google-client-id:latest \
     --update-secrets GOOGLE_CLIENT_SECRET=google-client-secret:latest \
     --update-secrets FLASK_SECRET_KEY=flask-secret-key:latest
   ```

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate OAuth login
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout
- `GET /auth/status` - Check authentication status

### Employees
- `GET /api/employees/me` - Get current user profile
- `PUT /api/employees/me` - Update current user profile
- `GET /api/employees/` - List employees (filtered by permissions)
- `GET /api/employees/<email>` - Get specific employee
- `PUT /api/employees/<email>` - Update employee (admin only)
- `POST /api/employees/sync` - Sync from Workspace (admin only)
- `GET /api/employees/team` - Get team members you manage

### Time-off Requests
- `POST /api/timeoff/requests` - Create time-off request
- `GET /api/timeoff/requests/my` - Get your requests
- `GET /api/timeoff/requests/<id>` - Get specific request
- `GET /api/timeoff/requests/pending-approval` - Get pending approvals
- `POST /api/timeoff/requests/<id>/approve-manager` - Manager approval
- `POST /api/timeoff/requests/<id>/approve-admin` - Admin approval
- `POST /api/timeoff/requests/<id>/reject` - Reject request
- `POST /api/timeoff/requests/<id>/sync-calendar` - Sync to calendar
- `POST /api/timeoff/requests/<id>/enable-autoresponder` - Enable Gmail OOO
- `GET /api/timeoff/vacation-summary` - Get vacation days summary

## Database Schema

### Employees Collection
```javascript
{
  email: string,                    // Primary key
  workspace_id: string,
  given_name: string,
  family_name: string,
  full_name: string,
  photo_url: string,
  manager_email: string,
  department: string,
  job_title: string,
  location: string,
  country: string,
  region: string,
  vacation_days_per_year: number,
  is_admin: boolean,
  is_active: boolean,
  created_at: timestamp,
  updated_at: timestamp,
  last_workspace_sync: timestamp
}
```

### Time-off Requests Collection
```javascript
{
  employee_email: string,
  start_date: string (ISO date),
  end_date: string (ISO date),
  timeoff_type: 'vacation' | 'sick_leave' | 'day_off',
  notes: string,
  status: 'pending' | 'manager_approved' | 'approved' | 'rejected',
  manager_email: string,
  manager_approved_at: timestamp,
  manager_approved_by: string,
  admin_approved_at: timestamp,
  admin_approved_by: string,
  rejected_at: timestamp,
  rejected_by: string,
  rejection_reason: string,
  calendar_event_id: string,
  autoresponder_enabled: boolean,
  created_at: timestamp,
  updated_at: timestamp,
  days_count: number
}
```

## Approval Workflow

1. **Employee** submits time-off request
2. **Manager** receives notification and must approve (tier 1)
3. **Admin** receives notification and must approve (tier 2)
4. Once approved, **Employee** can:
   - Sync to Google Calendar as OOO event
   - Enable Gmail auto-responder

## Security

- OAuth 2.0 with Google Workspace
- Session-based authentication
- Role-based access control (Employee, Manager, Admin)
- Secure cookie settings
- All secrets stored in Google Secret Manager

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black backend/
flake8 backend/
```

## License

Proprietary - Internal use only

## Support

For issues or questions, contact your IT administrator.
