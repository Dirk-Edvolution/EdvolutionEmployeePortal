# Employee Portal - API Documentation

Complete REST API documentation for the Employee Portal.

## Base URL

- **Development:** `http://localhost:8080`
- **Production:** `https://your-service-url.run.app`

## Authentication

All API endpoints (except `/auth/*` and `/health`) require authentication via session cookies obtained through the OAuth flow.

### Session-based Authentication

1. User navigates to `/auth/login`
2. Redirected to Google OAuth
3. After authentication, session cookie is set
4. Session cookie is sent with all subsequent requests

---

## API Endpoints

### Authentication & Session Management

#### `GET /auth/login`
Initiate OAuth 2.0 login flow with Google Workspace.

**Response:**
- Redirects to Google OAuth consent screen

---

#### `GET /auth/callback`
OAuth callback handler (called by Google after user consent).

**Query Parameters:**
- `code` - Authorization code from Google
- `state` - State parameter for CSRF protection

**Response:**
- Redirects to `/dashboard` on success
- Returns error JSON on failure

---

#### `GET /auth/logout`
Logout current user and clear session.

**Response:**
- Redirects to `/`

---

#### `GET /auth/status`
Check current authentication status.

**Response:**
```json
{
  "authenticated": true,
  "user": {
    "email": "user@company.com",
    "name": "John Doe",
    "picture": "https://..."
  }
}
```

---

### Employee Management

#### `GET /api/employees/me`
Get current logged-in user's profile.

**Authentication:** Required

**Response:**
```json
{
  "email": "user@company.com",
  "workspace_id": "123456789",
  "given_name": "John",
  "family_name": "Doe",
  "full_name": "John Doe",
  "photo_url": "https://...",
  "manager_email": "manager@company.com",
  "department": "Engineering",
  "job_title": "Software Engineer",
  "location": "San Francisco",
  "country": "US",
  "region": "California",
  "vacation_days_per_year": 20,
  "is_admin": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_workspace_sync": "2024-01-15T10:30:00Z"
}
```

---

#### `PUT /api/employees/me`
Update current user's profile.

**Authentication:** Required

**Request Body:**
```json
{
  "location": "New York",
  "country": "US",
  "region": "New York",
  "vacation_days_per_year": 25
}
```

**Updatable Fields (by user):**
- `location`
- `country`
- `region`
- `vacation_days_per_year`

**Updatable Fields (by admin only):**
- `manager_email`
- `department`
- `job_title`
- `is_admin`

**Response:** Updated employee object (same format as GET)

---

#### `GET /api/employees/`
List all employees (filtered by permissions).

**Authentication:** Required

**Permissions:**
- **Admins:** See all employees
- **Managers:** See direct reports only
- **Regular users:** See empty list

**Response:**
```json
[
  {
    "email": "employee1@company.com",
    "full_name": "Alice Smith",
    ...
  },
  {
    "email": "employee2@company.com",
    "full_name": "Bob Johnson",
    ...
  }
]
```

---

#### `GET /api/employees/<email>`
Get specific employee by email.

**Authentication:** Required

**Permissions:**
- Admins can view any employee
- Managers can view their direct reports
- Users can view their own profile

**Path Parameters:**
- `email` - Employee email address

**Response:** Employee object

---

#### `PUT /api/employees/<email>`
Update employee profile (admin only).

**Authentication:** Admin required

**Path Parameters:**
- `email` - Employee email address

**Request Body:**
```json
{
  "manager_email": "newmanager@company.com",
  "job_title": "Senior Engineer",
  "department": "Platform",
  "vacation_days_per_year": 25,
  "country": "US",
  "region": "California"
}
```

**Response:** Updated employee object

**Note:** Changes to `manager_email`, `job_title`, `department`, and `location` are synced back to Google Workspace.

---

#### `POST /api/employees/sync`
Sync all employees from Google Workspace (admin only).

**Authentication:** Admin required

**Response:**
```json
{
  "success": true,
  "synced_count": 150,
  "message": "Successfully synced 150 employees from Workspace"
}
```

---

#### `GET /api/employees/team`
Get employees managed by current user.

**Authentication:** Required

**Response:** Array of employee objects for direct reports

---

### Time-off Request Management

#### `POST /api/timeoff/requests`
Create a new time-off request.

**Authentication:** Required

**Request Body:**
```json
{
  "start_date": "2024-07-01",
  "end_date": "2024-07-05",
  "timeoff_type": "vacation",
  "notes": "Summer vacation"
}
```

**Fields:**
- `start_date` (required) - ISO date string
- `end_date` (required) - ISO date string
- `timeoff_type` (required) - One of: `vacation`, `sick_leave`, `day_off`
- `notes` (optional) - Additional notes

**Response:**
```json
{
  "request_id": "abc123",
  "employee_email": "user@company.com",
  "start_date": "2024-07-01",
  "end_date": "2024-07-05",
  "timeoff_type": "vacation",
  "notes": "Summer vacation",
  "status": "pending",
  "manager_email": "manager@company.com",
  "days_count": 5,
  "created_at": "2024-06-15T10:30:00Z"
}
```

---

#### `GET /api/timeoff/requests/my`
Get current user's time-off requests.

**Authentication:** Required

**Query Parameters:**
- `year` (optional) - Filter by year (e.g., 2024)

**Response:**
```json
[
  {
    "request_id": "abc123",
    "employee_email": "user@company.com",
    "start_date": "2024-07-01",
    "end_date": "2024-07-05",
    "timeoff_type": "vacation",
    "status": "approved",
    "days_count": 5,
    ...
  }
]
```

---

#### `GET /api/timeoff/requests/<request_id>`
Get specific time-off request.

**Authentication:** Required

**Permissions:**
- Requester can view their own requests
- Manager can view team requests
- Admin can view all requests

**Path Parameters:**
- `request_id` - Request ID

**Response:** Time-off request object

---

#### `GET /api/timeoff/requests/pending-approval`
Get requests pending approval by current user.

**Authentication:** Required

**Returns:**
- For managers: Requests pending manager approval
- For admins: Requests pending admin approval (already manager-approved)

**Response:** Array of time-off request objects

---

#### `POST /api/timeoff/requests/<request_id>/approve-manager`
Approve time-off request as manager (first tier).

**Authentication:** Required

**Permissions:**
- Must be the employee's manager
- Request must be in `pending` status

**Path Parameters:**
- `request_id` - Request ID

**Response:**
```json
{
  "message": "Request approved by manager, pending admin approval",
  "request_id": "abc123",
  "status": "manager_approved",
  ...
}
```

---

#### `POST /api/timeoff/requests/<request_id>/approve-admin`
Approve time-off request as admin (second tier, final approval).

**Authentication:** Admin required

**Permissions:**
- Must be an admin user
- Request must be in `manager_approved` status

**Path Parameters:**
- `request_id` - Request ID

**Request Body (optional):**
```json
{
  "sync_calendar": true,
  "enable_autoresponder": true
}
```

**Response:**
```json
{
  "message": "Request fully approved",
  "request_id": "abc123",
  "status": "approved",
  ...
}
```

---

#### `POST /api/timeoff/requests/<request_id>/reject`
Reject time-off request.

**Authentication:** Required

**Permissions:**
- Manager or admin can reject

**Path Parameters:**
- `request_id` - Request ID

**Request Body:**
```json
{
  "reason": "Insufficient coverage during this period"
}
```

**Response:**
```json
{
  "message": "Request rejected",
  "request_id": "abc123",
  "status": "rejected",
  "rejection_reason": "Insufficient coverage during this period",
  ...
}
```

---

#### `POST /api/timeoff/requests/<request_id>/sync-calendar`
Sync approved request to Google Calendar.

**Authentication:** Required

**Permissions:**
- Only the requester can sync their own calendar
- Request must be `approved`

**Path Parameters:**
- `request_id` - Request ID

**Response:**
```json
{
  "message": "Successfully synced to Google Calendar",
  "event_id": "calendar_event_123"
}
```

**Note:** Creates an all-day OOO event in the user's primary calendar.

---

#### `POST /api/timeoff/requests/<request_id>/enable-autoresponder`
Enable Gmail auto-responder for approved request.

**Authentication:** Required

**Permissions:**
- Only the requester can enable their own autoresponder
- Request must be `approved`

**Path Parameters:**
- `request_id` - Request ID

**Response:**
```json
{
  "message": "Gmail auto-responder enabled successfully"
}
```

**Note:** Sets up vacation responder with automatic start/end dates.

---

#### `GET /api/timeoff/vacation-summary`
Get vacation days summary for current user.

**Authentication:** Required

**Query Parameters:**
- `year` (optional) - Year to calculate (defaults to current year)

**Response:**
```json
{
  "year": 2024,
  "total_days": 20,
  "used_days": 8,
  "remaining_days": 12,
  "country": "US",
  "region": "California"
}
```

---

### Health & Status

#### `GET /health`
Health check endpoint.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy"
}
```

---

#### `GET /`
API information endpoint.

**Authentication:** Not required

**Response:**
```json
{
  "name": "Employee Portal API",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Error Response Format

```json
{
  "error": "Error message describing what went wrong"
}
```

---

## Time-off Request Statuses

1. **`pending`** - Awaiting manager approval
2. **`manager_approved`** - Manager approved, awaiting admin approval
3. **`approved`** - Fully approved (both tiers)
4. **`rejected`** - Rejected by manager or admin

---

## Time-off Types

- **`vacation`** - Paid vacation time
- **`sick_leave`** - Sick leave
- **`day_off`** - Personal day off

---

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

---

## CORS

CORS is enabled for:
- `http://localhost:3000` (frontend development)
- `http://localhost:8080` (backend development)
- `https://*.run.app` (Cloud Run deployments)

---

## Example Usage

### Python Example

```python
import requests

# Login and get session
session = requests.Session()
session.get('http://localhost:8080/auth/login')

# Create time-off request
response = session.post(
    'http://localhost:8080/api/timeoff/requests',
    json={
        'start_date': '2024-07-01',
        'end_date': '2024-07-05',
        'timeoff_type': 'vacation',
        'notes': 'Summer vacation'
    }
)
print(response.json())

# Get vacation summary
summary = session.get('http://localhost:8080/api/timeoff/vacation-summary')
print(summary.json())
```

### JavaScript/Fetch Example

```javascript
// Create time-off request
const response = await fetch('/api/timeoff/requests', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    start_date: '2024-07-01',
    end_date: '2024-07-05',
    timeoff_type: 'vacation',
    notes: 'Summer vacation'
  })
});

const result = await response.json();
console.log(result);
```

---

## Webhooks & Notifications

Currently not implemented. Future versions may include:
- Email notifications for approvals
- Slack integration
- Calendar change notifications

---

For more information, see [README.md](README.md) and [SETUP_GUIDE.md](SETUP_GUIDE.md).
