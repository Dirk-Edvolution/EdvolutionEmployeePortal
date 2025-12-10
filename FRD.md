# Functional Requirements Document (FRD)
# Employee Portal - Vacation & Time-off Management System

**Version:** 1.1
**Date:** 2025-12-10
**Status:** Active
**Project:** Employee Portal

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Stakeholders](#3-stakeholders)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Data Requirements](#6-data-requirements)
7. [Integration Requirements](#7-integration-requirements)
8. [Security Requirements](#8-security-requirements)
9. [User Roles and Permissions](#9-user-roles-and-permissions)
10. [Workflow Requirements](#10-workflow-requirements)
11. [Audit and Compliance](#11-audit-and-compliance)
12. [Constraints and Assumptions](#12-constraints-and-assumptions)

---

## 1. Executive Summary

The Employee Portal is a comprehensive vacation and time-off management system designed for organizations using Google Workspace. The system provides automated employee data synchronization, a two-tier approval workflow for time-off requests, seamless integration with Google Calendar and Gmail for out-of-office notifications, and real-time manager notifications via Google Chat and Google Tasks to streamline the approval process.

### Key Objectives
- Automate employee data management via Google Workspace integration
- Streamline time-off request and approval processes
- Provide role-based access control for employees, managers, and administrators
- Enable accurate vacation tracking and reporting
- Integrate with Google Calendar and Gmail for automated OOO management
- Automate manager notifications via Google Chat and Google Tasks for pending approvals

---

## 2. Project Overview

### 2.1 Purpose
Provide a centralized platform for managing employee time-off requests with automated approval workflows, Google Workspace synchronization, and comprehensive vacation tracking.

### 2.2 Scope

**In Scope:**
- Employee authentication via Google Workspace SSO
- Employee profile management with bidirectional Workspace sync
- Time-off request creation and management
- Two-tier approval workflow (Manager → Admin)
- Google Calendar integration for OOO events
- Gmail auto-responder automation
- Google Chat notifications to managers for pending approvals
- Google Tasks creation for manager approval reminders
- Vacation balance tracking and reporting
- Manager hierarchy management
- Natural language audit query system
- Contract and compensation tracking
- Performance evaluation records

**Out of Scope:**
- Payroll integration
- Benefits administration
- Recruitment/onboarding workflows
- Performance review workflows
- Third-party HR system integration (beyond Google Workspace)

### 2.3 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | Python 3.11+ with Flask |
| Database | Google Cloud Firestore |
| Authentication | Google OAuth 2.0 |
| Cloud Platform | Google Cloud Platform (GCP) |
| Hosting | Google Cloud Run |
| Frontend | React (implementation planned) |
| AI Integration | Google Gemini 1.5 Flash (for audit queries) |
| Notifications | Google Chat API |
| Task Management | Google Tasks API (Calendar Tasks) |

### 2.4 Deployment Model
- Cloud-native SaaS application
- Hosted on Google Cloud Run
- Auto-scaling based on demand
- Multi-region deployment capability

---

## 3. Stakeholders

| Role | Responsibilities | Access Level |
|------|------------------|--------------|
| Employees | Submit time-off requests, manage personal profile | User |
| Managers | Approve team time-off requests (tier 1), view team data | Manager |
| HR Administrators | Final approval (tier 2), manage all employees, system configuration | Admin |
| IT Administrators | System maintenance, Google Workspace integration | Admin |
| Executive Leadership | Reporting and analytics access | Admin |

---

## 4. Functional Requirements

### 4.1 Authentication & Session Management

#### FR-AUTH-001: Google Workspace SSO
**Priority:** CRITICAL
**Description:** Users must authenticate using their Google Workspace accounts.

**Requirements:**
- Support OAuth 2.0 authentication flow
- Integrate with Google Workspace domain
- Support "Internal" OAuth consent screen (Workspace users only)
- Maintain session state using secure cookies
- Automatic session expiration after inactivity

**Acceptance Criteria:**
- Users can login using their @company.com email
- Only active Workspace users can authenticate
- Session persists across page refreshes
- Session expires after configured timeout

#### FR-AUTH-002: Session Status
**Priority:** HIGH
**Description:** System must provide session status checking.

**Requirements:**
- API endpoint to check authentication status
- Return user profile information when authenticated
- Return appropriate status when not authenticated

#### FR-AUTH-003: Logout
**Priority:** HIGH
**Description:** Users must be able to logout and clear their session.

**Requirements:**
- Clear server-side session data
- Clear client-side cookies
- Redirect to home page after logout

---

### 4.2 Employee Management

#### FR-EMP-001: Employee Profile Viewing
**Priority:** CRITICAL
**Description:** Users must be able to view their employee profile.

**Requirements:**
- Display all personal information
- Show manager relationship
- Display department, job title, location
- Show vacation day allocation
- Display admin status
- Show contract information (if applicable)
- Display compensation details (redacted for non-admins)

**Acceptance Criteria:**
- GET /api/employees/me returns current user profile
- All fields populated from Firestore
- Photo URL displayed from Workspace

#### FR-EMP-002: Employee Profile Update
**Priority:** HIGH
**Description:** Users can update specific fields in their profile.

**User-Editable Fields:**
- Location (office/city)
- Country
- Region
- Vacation days per year allocation

**Admin-Only Editable Fields:**
- Manager assignment
- Department
- Job title
- Admin status
- Contract information
- Compensation details
- Performance evaluations

**Requirements:**
- Validate all input data
- Update timestamp on changes
- Sync specific fields back to Google Workspace
- Audit log all changes

**Acceptance Criteria:**
- PUT /api/employees/me updates allowed fields
- Validation errors return 400 status
- Changes reflected immediately in Firestore
- Workspace sync occurs for relevant fields

#### FR-EMP-003: Google Workspace Synchronization
**Priority:** CRITICAL
**Description:** System must sync employee data from Google Workspace.

**Requirements:**
- Pull all active users from Workspace Admin SDK
- Create new employee records for new users
- Update existing employee records with Workspace changes
- Mark suspended users as inactive
- Preserve local-only fields (vacation days, manager, etc.)
- Track last sync timestamp

**Sync Fields from Workspace:**
- Email (primary key)
- Workspace ID
- Given name, family name, full name
- Photo URL
- Organizational unit path
- Active/suspended status

**Local-Only Fields:**
- Manager email
- Vacation days per year
- Admin status
- Department
- Job title
- Contract information
- Compensation details

**Acceptance Criteria:**
- POST /api/employees/sync triggers synchronization
- All active Workspace users created/updated
- Suspended users marked inactive
- Sync completes within 60 seconds for 500 users
- Admin-only operation

#### FR-EMP-004: Bidirectional Sync
**Priority:** HIGH
**Description:** Changes to specific fields must sync back to Google Workspace.

**Synced Fields (Portal → Workspace):**
- Manager email
- Job title
- Department
- Location

**Requirements:**
- Update Workspace via Admin SDK API
- Handle API errors gracefully
- Retry failed syncs
- Log sync status

#### FR-EMP-005: Employee Listing
**Priority:** HIGH
**Description:** Users can list employees based on their permissions.

**Access Rules:**
- Admins: See all active employees
- Managers: See direct reports only
- Regular users: See empty list (or self only)

**Requirements:**
- Filter based on user role
- Return employee summary information
- Support pagination (future)
- Sort by name by default

**Acceptance Criteria:**
- GET /api/employees/ returns filtered list
- Respects role-based access control
- Returns 200 with empty array for regular users

#### FR-EMP-006: Manager Hierarchy
**Priority:** HIGH
**Description:** System must maintain and display manager-employee relationships.

**Requirements:**
- Store manager_email for each employee
- Support chain of command queries
- Admins can modify manager assignments
- Display team members for managers

**Acceptance Criteria:**
- GET /api/employees/team returns direct reports
- Manager changes update immediately
- Prevents circular manager relationships

#### FR-EMP-007: Contract Management
**Priority:** MEDIUM
**Description:** System tracks employee contract information.

**Contract Fields:**
- Contract type (permanent, temporary, contractor, intern)
- Contract start date
- Contract end date
- Contract document URL (Google Drive link)

**Requirements:**
- Admin-only access to view/edit
- Support document links to Google Drive
- Track contract expiration dates
- Alert on expiring contracts (future)

#### FR-EMP-008: Compensation Tracking
**Priority:** MEDIUM
**Description:** System stores compensation information securely.

**Compensation Fields:**
- Base salary
- Salary currency
- Bonus eligibility and type
- Bonus percentage
- Commission eligibility
- Commission notes

**Requirements:**
- Highly restricted access (admin only)
- Encrypted storage in Firestore
- Audit all access and changes
- Not synced to Workspace

#### FR-EMP-009: Performance Evaluations
**Priority:** LOW
**Description:** System stores performance evaluation records.

**Requirements:**
- Store evaluation history as list
- Track evaluation date, rating, notes
- Admin and manager access only
- Link to evaluation documents

---

### 4.3 Time-off Request Management

#### FR-TO-001: Time-off Request Creation
**Priority:** CRITICAL
**Description:** Employees must be able to create time-off requests.

**Request Fields:**
- Start date (required, ISO format)
- End date (required, ISO format)
- Time-off type (required: vacation, sick_leave, day_off)
- Notes (optional, text)

**Requirements:**
- Validate date range (end >= start)
- Calculate business days count
- Set initial status to "pending"
- Auto-assign to employee's manager
- Store creation timestamp
- Generate unique request ID
- Send Google Chat notification to assigned manager
- Create Google Tasks reminder in manager's task list

**Business Rules:**
- Cannot request time-off in the past
- Cannot overlap with existing approved requests
- Maximum 30 consecutive days per request
- Must have sufficient vacation days (for vacation type)

**Acceptance Criteria:**
- POST /api/timeoff/requests creates new request
- Returns 201 with request object
- Validation errors return 400
- Request visible in employee's request list

#### FR-TO-002: Time-off Request Viewing
**Priority:** CRITICAL
**Description:** Users can view time-off requests based on permissions.

**Access Rules:**
- Employees: View own requests
- Managers: View own + direct reports' requests
- Admins: View all requests

**Requirements:**
- Filter by year (optional)
- Display all request details
- Show approval status and history
- Display calendar sync status

**Acceptance Criteria:**
- GET /api/timeoff/requests/my returns user's requests
- GET /api/timeoff/requests/<id> returns specific request
- Respects access control rules
- Returns 403 for unauthorized access

#### FR-TO-003: Two-Tier Approval Workflow
**Priority:** CRITICAL
**Description:** Time-off requests require two-level approval: Manager then Admin.

**Workflow States:**
1. **pending** - Awaiting manager approval
2. **manager_approved** - Manager approved, awaiting admin approval
3. **approved** - Fully approved (both tiers)
4. **rejected** - Rejected by manager or admin

**Requirements:**
- Enforce sequential approval order
- Track approver email and timestamp for each tier
- Allow managers to approve only their direct reports
- Allow admins to provide final approval
- Special case: If manager is also admin, they can do both approvals

**Acceptance Criteria:**
- Manager approval moves status from pending → manager_approved
- Admin approval moves status from manager_approved → approved
- Cannot skip manager approval (unless manager=admin)
- Approval timestamps recorded accurately

#### FR-TO-004: Manager Approval (Tier 1)
**Priority:** CRITICAL
**Description:** Managers must approve time-off requests for their direct reports.

**Requirements:**
- Only assigned manager can approve
- Request must be in "pending" status
- Record manager email and approval timestamp
- Change status to "manager_approved"
- Notify admin of pending final approval (future)

**Authorization Rules:**
- User must be the assigned manager
- User cannot approve their own requests
- Request must be in pending state

**Acceptance Criteria:**
- POST /api/timeoff/requests/<id>/approve-manager succeeds
- Status changes to manager_approved
- Manager details recorded
- Returns 403 if not authorized

#### FR-TO-005: Admin Approval (Tier 2)
**Priority:** CRITICAL
**Description:** Admins provide final approval for time-off requests.

**Requirements:**
- Request must be in "manager_approved" status
- User must have admin role
- Record admin email and approval timestamp
- Change status to "approved"
- Optional: Auto-sync to calendar and enable autoresponder

**Special Case:**
- If admin is also the manager AND request is pending, admin can skip manager approval tier

**Acceptance Criteria:**
- POST /api/timeoff/requests/<id>/approve-admin succeeds
- Status changes to approved
- Admin details recorded
- Optional calendar sync performed
- Returns 403 if not authorized

#### FR-TO-006: Request Rejection
**Priority:** HIGH
**Description:** Managers and admins can reject time-off requests.

**Requirements:**
- Manager or admin can reject
- Rejection reason required (text field)
- Record rejector email and timestamp
- Change status to "rejected"
- Notify employee of rejection (future)

**Acceptance Criteria:**
- POST /api/timeoff/requests/<id>/reject succeeds
- Status changes to rejected
- Rejection reason stored
- Returns 400 if reason missing

#### FR-TO-007: Pending Approvals View
**Priority:** HIGH
**Description:** Show requests pending approval by current user.

**Requirements:**
- Managers see: Requests in "pending" status for their reports
- Admins see: Requests in "manager_approved" status
- Sort by creation date (oldest first)
- Display employee name and date range

**Acceptance Criteria:**
- GET /api/timeoff/requests/pending-approval returns filtered list
- Respects user role
- Empty array if no pending approvals

#### FR-TO-008: Time-off Types
**Priority:** MEDIUM
**Description:** System supports multiple time-off types.

**Supported Types:**
1. **vacation** - Paid vacation time, deducted from annual allowance
2. **sick_leave** - Sick leave, not deducted from vacation
3. **day_off** - Personal day off, flexible handling

**Requirements:**
- Enforce type enum validation
- Different calculation rules per type
- Different approval rules possible (future)

---

### 4.4 Google Calendar Integration

#### FR-CAL-001: Calendar Sync
**Priority:** HIGH
**Description:** Approved time-off requests can be synced to Google Calendar.

**Requirements:**
- Create all-day OOO event in user's primary calendar
- Set event title: "[OOO] Time Off - [Type]"
- Set event description with request details
- Mark as "Out of Office" event type
- Store calendar event ID in request
- Only employee can sync their own calendar
- Request must be in "approved" status

**Acceptance Criteria:**
- POST /api/timeoff/requests/<id>/sync-calendar creates event
- Event appears in Google Calendar
- Event ID stored in request record
- Returns 403 if not authorized or not approved

#### FR-CAL-002: Calendar Event Update
**Priority:** MEDIUM
**Description:** If request changes, calendar event should update.

**Requirements:**
- Update event if dates change
- Delete event if request rejected
- Handle calendar API errors gracefully

---

### 4.5 Gmail Integration

#### FR-GMAIL-001: Auto-responder Setup
**Priority:** HIGH
**Description:** Approved time-off requests can enable Gmail auto-responder.

**Requirements:**
- Enable Gmail vacation responder
- Set start date/time from request
- Set end date/time from request
- Set auto-responder message with OOO details
- Store autoresponder_enabled flag
- Only employee can enable their own autoresponder
- Request must be in "approved" status

**Acceptance Criteria:**
- POST /api/timeoff/requests/<id>/enable-autoresponder succeeds
- Vacation responder active in Gmail
- Flag stored in request record
- Returns 403 if not authorized or not approved

---

### 4.6 Vacation Tracking & Reporting

#### FR-VAC-001: Vacation Balance Calculation
**Priority:** CRITICAL
**Description:** System calculates vacation day usage and remaining balance.

**Requirements:**
- Track vacation_days_per_year per employee
- Calculate used days from approved "vacation" requests
- Calculate remaining days (total - used)
- Filter by calendar year
- Count only business days (exclude weekends)

**Formula:**
```
remaining_days = vacation_days_per_year - SUM(approved vacation requests in year)
```

**Acceptance Criteria:**
- GET /api/timeoff/vacation-summary returns accurate calculations
- Supports year parameter
- Defaults to current year
- Only counts approved vacation-type requests

#### FR-VAC-002: Vacation Summary
**Priority:** HIGH
**Description:** Display vacation summary for employees.

**Summary Fields:**
- Year
- Total allocated days
- Used days
- Remaining days
- Country/region
- List of vacation requests

**Acceptance Criteria:**
- Accurate calculation of used days
- Real-time updates after approvals
- Supports multi-year view (future)

---

### 4.7 Manager Notifications

#### FR-NOTIFY-001: Google Chat Notification on Request Creation
**Priority:** HIGH
**Description:** When a time-off request is created, the system automatically sends a notification to the assigned manager via Google Chat.

**Requirements:**
- Send notification immediately upon request creation
- Include employee name, request dates, and time-off type
- Include direct link to request details
- Use Google Chat API to send direct message to manager
- Handle cases where manager doesn't have Google Chat enabled
- Log notification delivery status

**Notification Message Format:**
```
🔔 New Time-Off Request Pending Your Approval

Employee: [Full Name]
Type: [Vacation/Sick Leave/Day Off]
Dates: [Start Date] to [End Date]
Duration: [X] days

Notes: [Employee notes if provided]

[View Request] [Approve] [Reject]
```

**Acceptance Criteria:**
- Chat message sent successfully to manager
- Message contains all required information
- Links functional and secure
- Failed notifications logged with error details
- Retry mechanism for temporary failures

#### FR-NOTIFY-002: Google Tasks Creation on Request Creation
**Priority:** HIGH
**Description:** When a time-off request is created, the system automatically creates a task in the manager's Google Tasks list.

**Requirements:**
- Create task in manager's default task list
- Task title: "Approve time-off: [Employee Name] - [Dates]"
- Task notes include full request details
- Set task due date to 2 business days from request creation
- Link task to time-off request URL
- Mark task as completed when manager approves/rejects
- Delete task if request is canceled

**Task Details:**
- **Title:** "Approve time-off: [Employee Name] - [Start] to [End]"
- **Due Date:** [Request Date + 2 business days]
- **Notes:** Full request details with approval link
- **Status:** needsAction
- **Task List:** Default list (or "Employee Portal Approvals" if custom list created)

**Acceptance Criteria:**
- Task created successfully in Google Tasks
- Task visible in manager's Google Calendar Tasks
- Task contains accurate information
- Task auto-completes on approval/rejection
- Failed task creation logged

#### FR-NOTIFY-003: Notification Retry Logic
**Priority:** MEDIUM
**Description:** System retries failed notifications with exponential backoff.

**Requirements:**
- Retry failed Chat notifications up to 3 times
- Retry failed Task creation up to 3 times
- Use exponential backoff (1 min, 5 min, 15 min)
- Log all retry attempts
- Alert admins if all retries fail
- Don't block request creation if notifications fail

**Acceptance Criteria:**
- Retry logic functions correctly
- Doesn't impact request creation performance
- Failed notifications tracked in audit logs

#### FR-NOTIFY-004: Notification Preferences
**Priority:** LOW
**Description:** Managers can configure notification preferences (future enhancement).

**Requirements:**
- Enable/disable Chat notifications
- Enable/disable Task creation
- Set custom notification schedule
- Batch notifications (hourly/daily digest)

**Acceptance Criteria:**
- Preferences stored per manager
- System respects preferences
- Default: All notifications enabled

#### FR-NOTIFY-005: Admin Notification on Manager Approval
**Priority:** MEDIUM
**Description:** When a manager approves a request, notify admin for final approval.

**Requirements:**
- Send Google Chat notification to all admins
- Create Google Task in admins' task lists
- Similar format to manager notifications
- Include manager approval details

**Acceptance Criteria:**
- Admins notified when manager approves
- Notification includes tier-1 approval info

---

### 4.8 Natural Language Audit Query

#### FR-AUDIT-001: Natural Language Query
**Priority:** LOW
**Description:** Admins can query audit logs using natural language.

**Requirements:**
- Accept plain English questions
- Use Google Gemini AI to parse questions
- Extract query parameters (user, action, date range, resource)
- Execute Firestore query
- Generate natural language response

**Example Questions:**
- "Who approved John's vacation last week?"
- "What did Alice do yesterday?"
- "Show me all manager approvals this month"

**Query Parameters Extracted:**
- user_email: Who performed the action
- action: Action type (LOGIN, TIMEOFF_APPROVE_MANAGER, etc.)
- resource_type: employee or timeoff_request
- employee_name: Employee mentioned in question
- days: Time range (1-365)

**Acceptance Criteria:**
- POST /api/audit/query accepts question
- Returns natural language answer
- Returns matching log entries
- Respects role-based access (admins only for full access)

#### FR-AUDIT-002: Audit Log Actions
**Priority:** LOW
**Description:** System tracks comprehensive audit actions.

**Action Types:**
- Authentication: LOGIN, LOGOUT
- Employee: EMPLOYEE_CREATE, EMPLOYEE_UPDATE, EMPLOYEE_SYNC
- Time-off: TIMEOFF_CREATE, TIMEOFF_APPROVE_MANAGER, TIMEOFF_APPROVE_ADMIN, TIMEOFF_REJECT, TIMEOFF_UPDATE, TIMEOFF_DELETE

**Note:** Audit logging infrastructure exists but NOT yet integrated into main application.

---

## 5. Non-Functional Requirements

### 5.1 Performance

#### NFR-PERF-001: Response Time
- API endpoints respond within 500ms (95th percentile)
- Page load time under 2 seconds
- Calendar sync completes within 5 seconds

#### NFR-PERF-002: Scalability
- Support 1000+ concurrent users
- Handle 500+ employees in single organization
- Support 10,000+ time-off requests per year

#### NFR-PERF-003: Availability
- 99.5% uptime SLA
- Planned maintenance windows during off-hours
- Auto-scaling on Google Cloud Run

### 5.2 Usability

#### NFR-USE-001: User Interface
- Responsive design for mobile/tablet/desktop
- Intuitive navigation
- Accessible (WCAG 2.1 Level AA compliance)
- Support for common browsers (Chrome, Firefox, Safari, Edge)

#### NFR-USE-002: Error Handling
- Clear error messages for users
- Validation feedback on forms
- Graceful degradation if external services unavailable

### 5.3 Security

#### NFR-SEC-001: Data Protection
- All data encrypted in transit (TLS 1.3)
- Data encrypted at rest in Firestore
- Sensitive fields (salary) separately encrypted
- Secure session management

#### NFR-SEC-002: Authentication
- OAuth 2.0 standard compliance
- Session timeout after 24 hours inactivity
- No password storage (delegated to Google)

#### NFR-SEC-003: Authorization
- Role-based access control (RBAC)
- Principle of least privilege
- API endpoint authorization checks

### 5.4 Compliance

#### NFR-COMP-001: Data Privacy
- GDPR compliance for EU employees
- Data retention policies
- Right to access personal data
- Right to deletion (anonymization)

#### NFR-COMP-002: Audit Trail
- All sensitive operations logged
- Immutable audit logs
- 7-year retention for compliance

---

## 6. Data Requirements

### 6.1 Employee Data Model

**Collection:** `employees`
**Document ID:** email address

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Primary key, work email |
| workspace_id | string | Yes | Google Workspace user ID |
| given_name | string | Yes | First name |
| family_name | string | Yes | Last name |
| full_name | string | Yes | Full name |
| display_name | string | Computed | Name with email |
| photo_url | string | No | Profile photo URL |
| manager_email | string | No | Manager's email |
| organizational_unit | string | No | Workspace OU path |
| department | string | No | Department name |
| job_title | string | No | Job title |
| location | string | No | Office/city location |
| country | string | No | Country code |
| region | string | No | Region/state |
| vacation_days_per_year | number | Yes | Annual vacation allocation |
| is_admin | boolean | Yes | Admin role flag |
| is_active | boolean | Yes | Active status |
| contract_type | string | No | Contract type |
| contract_start_date | timestamp | No | Contract start |
| contract_end_date | timestamp | No | Contract end |
| contract_document_url | string | No | Drive link |
| salary | number | No | Base salary |
| salary_currency | string | No | Currency code |
| has_bonus | boolean | No | Bonus eligibility |
| bonus_type | string | No | Bonus frequency |
| bonus_percentage | number | No | Bonus % |
| has_commission | boolean | No | Commission eligibility |
| commission_notes | string | No | Commission details |
| personal_address | string | No | Home address |
| working_address | string | No | Work address |
| spouse_partner_name | string | No | Partner name |
| spouse_partner_phone | string | No | Partner phone |
| spouse_partner_email | string | No | Partner email |
| evaluations | array | No | Performance evaluations |
| created_at | timestamp | Yes | Creation timestamp |
| updated_at | timestamp | Yes | Last update timestamp |
| last_workspace_sync | timestamp | No | Last Workspace sync |

### 6.2 Time-off Request Data Model

**Collection:** `timeoff_requests`
**Document ID:** Auto-generated

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| request_id | string | Auto | Document ID |
| employee_email | string | Yes | Requester email |
| start_date | string | Yes | ISO date (YYYY-MM-DD) |
| end_date | string | Yes | ISO date (YYYY-MM-DD) |
| timeoff_type | enum | Yes | vacation, sick_leave, day_off |
| notes | string | No | Additional notes |
| status | enum | Yes | pending, manager_approved, approved, rejected |
| manager_email | string | Yes | Assigned manager |
| manager_approved_at | timestamp | No | Manager approval time |
| manager_approved_by | string | No | Manager email |
| admin_approved_at | timestamp | No | Admin approval time |
| admin_approved_by | string | No | Admin email |
| rejected_at | timestamp | No | Rejection time |
| rejected_by | string | No | Rejector email |
| rejection_reason | string | No | Rejection reason |
| calendar_event_id | string | No | Google Calendar event ID |
| autoresponder_enabled | boolean | Yes | Gmail autoresponder status |
| days_count | number | Computed | Number of days |
| created_at | timestamp | Yes | Creation timestamp |
| updated_at | timestamp | Yes | Last update timestamp |

### 6.3 Audit Log Data Model

**Collection:** `audit_logs`
**Document ID:** Auto-generated

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| log_id | string | Auto | Document ID |
| user_email | string | Yes | Actor email |
| action | enum | Yes | Action type |
| resource_type | enum | Yes | employee, timeoff_request |
| resource_id | string | No | Affected resource ID |
| timestamp | timestamp | Yes | Action timestamp |
| details | object | No | Additional context |
| ip_address | string | No | Client IP |
| user_agent | string | No | Client user agent |

### 6.4 Data Retention

| Data Type | Retention Period | Notes |
|-----------|------------------|-------|
| Active employees | Indefinite | While employed |
| Inactive employees | 7 years | After termination |
| Time-off requests | 7 years | All statuses |
| Audit logs | 7 years | Immutable |
| Session data | 24 hours | Auto-expire |

---

## 7. Integration Requirements

### 7.1 Google Workspace Admin SDK

**Purpose:** Employee data synchronization

**API Scopes Required:**
- `https://www.googleapis.com/auth/admin.directory.user`
- `https://www.googleapis.com/auth/admin.directory.user.readonly`

**Operations:**
- List all users in domain
- Get user details
- Update user profile
- Suspend/unsuspend users

**Configuration:**
- Domain-wide delegation enabled
- Service account with admin privileges
- OAuth client authorized in Workspace Admin

### 7.2 Google Calendar API

**Purpose:** Out-of-office event creation

**API Scopes Required:**
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`

**Operations:**
- Create all-day events
- Update events
- Delete events
- Set event type as "outOfOffice"

**Configuration:**
- User OAuth consent required
- Access user's primary calendar

### 7.3 Gmail API

**Purpose:** Vacation auto-responder

**API Scopes Required:**
- `https://www.googleapis.com/auth/gmail.settings.basic`
- `https://www.googleapis.com/auth/gmail.settings.sharing`

**Operations:**
- Enable vacation responder
- Disable vacation responder
- Set vacation responder message
- Set start/end times

**Configuration:**
- User OAuth consent required
- Modify user's Gmail settings

### 7.4 Google Gemini AI API

**Purpose:** Natural language audit query parsing

**API Configuration:**
- API Key in environment variable
- Model: gemini-1.5-flash
- Cost optimization: Free tier usage

**Operations:**
- Parse natural language questions
- Generate natural language responses
- Extract structured query parameters

### 7.5 Google Chat API

**Purpose:** Real-time notifications to managers and admins

**API Scopes Required:**
- `https://www.googleapis.com/auth/chat.messages`
- `https://www.googleapis.com/auth/chat.messages.create`

**Operations:**
- Send direct messages to users
- Send messages to spaces (optional, future)
- Include interactive cards with action buttons
- Track message delivery status
- Handle webhook responses (for button clicks)

**Configuration:**
- Service account with domain-wide delegation
- Chat API enabled in Google Workspace
- Bot configured in Google Chat (optional for enhanced features)
- Fallback handling for users without Chat enabled

**Message Features:**
- Rich text formatting (bold, links)
- Interactive card buttons (View, Approve, Reject)
- Inline images and icons
- Threading support for follow-up messages

**Implementation Notes:**
- Use direct messages (DM) to manager's email
- Messages sent as system notifications
- Include deep links to Employee Portal
- Rate limiting: Max 1 message per second per user

### 7.6 Google Tasks API

**Purpose:** Task management integration for approval workflows

**API Scopes Required:**
- `https://www.googleapis.com/auth/tasks`

**Operations:**
- Create tasks in user's task lists
- Update task status (complete/incomplete)
- Delete tasks
- Set task due dates
- Add task notes with rich details
- List task lists for user
- Create custom task list ("Employee Portal Approvals")

**Configuration:**
- Service account with domain-wide delegation
- Tasks API enabled in GCP project
- Access manager's default task list or custom list
- Sync with Google Calendar Tasks view

**Task Features:**
- Title with key information
- Detailed notes with request data
- Due date (2 business days default)
- Links to approval page
- Auto-completion on approval/rejection
- Auto-deletion on request cancellation

**Implementation Notes:**
- Tasks visible in Google Calendar sidebar
- Tasks accessible via Google Tasks mobile app
- Due date triggers Calendar reminders
- Use task list ID or "@default" for default list
- Handle cases where user has deleted default list

---

## 8. Security Requirements

### 8.1 Authentication Requirements

#### SR-AUTH-001: OAuth 2.0 Implementation
- Use Google OAuth 2.0 authorization code flow
- Store access tokens encrypted
- Refresh tokens automatically
- Secure redirect URI configuration

#### SR-AUTH-002: Session Management
- Generate cryptographically secure session IDs
- Store session data server-side
- Set HTTPOnly and Secure cookie flags
- Implement CSRF protection
- Session timeout: 24 hours inactivity

### 8.2 Authorization Requirements

#### SR-AUTHZ-001: Role-Based Access Control
- Three roles: User, Manager, Admin
- Enforce permissions at API layer
- Verify authorization on every request
- No client-side authorization decisions

#### SR-AUTHZ-002: Data Access Rules
- Users access own data only
- Managers access direct reports' data
- Admins access all data
- Audit all admin actions

### 8.3 Data Security

#### SR-DATA-001: Encryption
- TLS 1.3 for all network communication
- Firestore encryption at rest (default)
- Additional encryption for sensitive fields (salary)
- Secure key management via GCP Secret Manager

#### SR-DATA-002: PII Protection
- Minimize PII collection
- Redact sensitive data in logs
- Secure disposal of PII
- Access logging for PII access

### 8.4 API Security

#### SR-API-001: Input Validation
- Validate all input parameters
- Sanitize user input
- Prevent SQL injection (N/A for Firestore)
- Prevent XSS attacks
- Maximum request size limits

#### SR-API-002: Rate Limiting
- Implement rate limiting per user
- Prevent brute force attacks
- Throttle excessive requests

### 8.5 Secrets Management

#### SR-SEC-001: Environment Variables
- Store secrets in Google Secret Manager
- Never commit secrets to version control
- Rotate secrets regularly
- Audit secret access

---

## 9. User Roles and Permissions

### 9.1 Role Definitions

#### Regular Employee (User)
**Capabilities:**
- View own employee profile
- Update limited profile fields (location, country, region)
- Create time-off requests for self
- View own time-off requests
- View vacation balance
- Sync approved requests to own calendar
- Enable own Gmail auto-responder

**Restrictions:**
- Cannot view other employees' data
- Cannot approve any requests
- Cannot access admin functions
- Cannot sync employee data

#### Manager
**Inherits:** All Regular Employee capabilities

**Additional Capabilities:**
- View direct reports' profiles
- View direct reports' time-off requests
- Approve direct reports' time-off requests (tier 1)
- Reject direct reports' time-off requests
- View team vacation calendars (future)

**Restrictions:**
- Cannot approve requests for non-reports
- Cannot access admin-only functions
- Cannot modify employee records
- Cannot perform final approval (tier 2)

#### Administrator (Admin)
**Inherits:** All Manager capabilities (for all employees)

**Additional Capabilities:**
- View all employee profiles
- Update all employee records
- Manage manager-employee relationships
- Sync employees from Google Workspace
- View all time-off requests
- Provide final approval for requests (tier 2)
- Reject any request
- Access audit logs
- Natural language audit queries
- System configuration
- View compensation and contract data

**Restrictions:**
- Cannot bypass two-tier approval (if not manager)

### 9.2 Permission Matrix

| Operation | Employee | Manager | Admin |
|-----------|----------|---------|-------|
| View own profile | ✓ | ✓ | ✓ |
| Update own profile (limited) | ✓ | ✓ | ✓ |
| View team profiles | ✗ | ✓ (reports only) | ✓ (all) |
| Update any profile | ✗ | ✗ | ✓ |
| Manage manager relationships | ✗ | ✗ | ✓ |
| Sync from Workspace | ✗ | ✗ | ✓ |
| Create time-off request | ✓ | ✓ | ✓ |
| View own requests | ✓ | ✓ | ✓ |
| View team requests | ✗ | ✓ (reports only) | ✓ (all) |
| Approve as manager (tier 1) | ✗ | ✓ (reports only) | ✓ (if manager) |
| Approve as admin (tier 2) | ✗ | ✗ | ✓ |
| Reject requests | ✗ | ✓ (reports only) | ✓ (all) |
| Sync to own calendar | ✓ | ✓ | ✓ |
| Enable own autoresponder | ✓ | ✓ | ✓ |
| View vacation balance | ✓ (own) | ✓ (own + team) | ✓ (all) |
| Access audit logs | ✗ | ✗ | ✓ |
| Natural language queries | ✗ | ✗ | ✓ |
| View compensation data | ✗ | ✗ | ✓ |

---

## 10. Workflow Requirements

### 10.1 Time-off Request Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Time-off Request Workflow                │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐
│  Employee   │
│   Creates   │
│   Request   │
└──────┬──────┘
       │
       │ System triggers:
       │ 1. Send Google Chat to Manager
       │ 2. Create Task in Manager's Tasks
       │
       ▼
┌─────────────┐
│   PENDING   │ ◄──────────────────┐
│  (awaiting  │                    │
│  manager)   │                    │
└──────┬──────┘                    │
       │                           │
       │ Manager approves          │ Rejection at
       │ + Task marked complete    │ any stage
       │                           │
       │ System triggers:          │
       │ 3. Send Chat to Admins    │
       │ 4. Create Task for Admins │
       │                           │
       ▼                           │
┌─────────────┐                    │
│  MANAGER    │                    │
│  APPROVED   │                    │
│ (awaiting   │                    │
│   admin)    │                    │
└──────┬──────┘                    │
       │                           │
       │ Admin approves            │
       │                           │
       ▼                           │
┌─────────────┐                    │
│  APPROVED   │                    │
│   (fully    │                    │
│  approved)  │                    │
└──────┬──────┘                    │
       │                           │
       │ Employee actions          │
       │ (optional)                │
       ├──────────────┐            │
       ▼              ▼            │
┌────────────┐  ┌──────────┐      │
│Sync to Cal │  │Enable    │      │
│            │  │Auto-resp │      │
└────────────┘  └──────────┘      │
                                  │
                                  │
       ┌──────────────────────────┘
       ▼
┌─────────────┐
│  REJECTED   │
│  (denied)   │
└─────────────┘
```

### 10.2 Manager-Admin Workflow States

#### State: PENDING
- **Description:** Newly created request awaiting manager review
- **Valid Transitions:** → MANAGER_APPROVED (manager approval), → REJECTED (rejection)
- **Actors:** Manager
- **Actions Available:** Approve (tier 1), Reject
- **Automated Actions:**
  - Google Chat notification sent to manager
  - Google Task created in manager's task list
  - Task due date: Request date + 2 business days

#### State: MANAGER_APPROVED
- **Description:** Manager approved, awaiting admin final approval
- **Valid Transitions:** → APPROVED (admin approval), → REJECTED (rejection)
- **Actors:** Admin
- **Actions Available:** Approve (tier 2), Reject
- **Automated Actions:**
  - Manager's Google Task marked as completed
  - Google Chat notification sent to all admins
  - Google Task created in each admin's task list
  - Task due date: Approval date + 2 business days

#### State: APPROVED
- **Description:** Fully approved by both manager and admin
- **Valid Transitions:** None (terminal state)
- **Actors:** Employee
- **Actions Available:** Sync to calendar, Enable autoresponder
- **Automated Actions:**
  - Admin's Google Task marked as completed
  - Notification sent to employee (future enhancement)

#### State: REJECTED
- **Description:** Rejected by manager or admin
- **Valid Transitions:** None (terminal state)
- **Actors:** None
- **Actions Available:** None
- **Automated Actions:**
  - All pending Google Tasks deleted/marked completed
  - Notification sent to employee with rejection reason (future enhancement)

### 10.3 Special Case: Manager is Admin

If the assigned manager is also an admin:
- Option 1: Manager approves first (tier 1), then as admin (tier 2) - two separate actions
- Option 2: Admin can skip directly to final approval if request is PENDING

**Implementation:** Admin approval endpoint allows approval of PENDING requests if user is both manager and admin.

---

## 11. Audit and Compliance

### 11.1 Audit Logging Requirements

#### AR-AUDIT-001: Logged Actions
All the following actions must be logged:

**Authentication:**
- LOGIN - User login
- LOGOUT - User logout

**Employee Management:**
- EMPLOYEE_CREATE - New employee added
- EMPLOYEE_UPDATE - Employee record modified
- EMPLOYEE_SYNC - Workspace sync performed

**Time-off Management:**
- TIMEOFF_CREATE - New request created
- TIMEOFF_APPROVE_MANAGER - Manager approval
- TIMEOFF_APPROVE_ADMIN - Admin approval
- TIMEOFF_REJECT - Request rejection
- TIMEOFF_UPDATE - Request modification
- TIMEOFF_DELETE - Request deletion

#### AR-AUDIT-002: Log Data Requirements
Each audit log must include:
- User email (actor)
- Action type
- Timestamp (UTC)
- Resource type and ID
- Before/after values (for updates)
- IP address
- User agent
- Request outcome (success/failure)

#### AR-AUDIT-003: Audit Log Access
- Audit logs are immutable
- Only admins can access audit logs
- Audit log access is itself audited
- 7-year retention policy

#### AR-AUDIT-004: Natural Language Query
- Admins can query audit logs via natural language
- Powered by Google Gemini AI
- Extracts query parameters from plain English
- Returns natural language responses

### 11.2 Compliance Requirements

#### CR-COMP-001: Data Privacy (GDPR)
- Right to access: Employees can export their data
- Right to deletion: Data anonymization on termination
- Data minimization: Only collect necessary data
- Consent tracking for data processing
- Privacy policy and terms of service

#### CR-COMP-002: Data Retention
- Active employee data: Retained while employed
- Terminated employees: 7 years after termination
- Time-off records: 7 years after request date
- Audit logs: 7 years immutable retention

#### CR-COMP-003: Right to Access
- Employees can view all their personal data
- Export functionality for data portability (future)
- Machine-readable format (JSON)

#### CR-COMP-004: Security Incident Response
- Incident detection and logging
- Breach notification within 72 hours
- Root cause analysis documentation
- Remediation and prevention measures

---

## 12. Constraints and Assumptions

### 12.1 Technical Constraints

#### TC-001: Google Workspace Dependency
- **Constraint:** System requires active Google Workspace domain
- **Impact:** Cannot be used by organizations without Workspace
- **Mitigation:** None - fundamental requirement

#### TC-002: Google Cloud Platform
- **Constraint:** Must be deployed on GCP
- **Impact:** Vendor lock-in to Google Cloud
- **Mitigation:** Architecture allows future migration to other clouds

#### TC-003: Internet Connectivity
- **Constraint:** Requires internet access for all operations
- **Impact:** Cannot function offline
- **Mitigation:** None - cloud-native application

#### TC-004: Browser Requirements
- **Constraint:** Modern browser with JavaScript enabled
- **Impact:** Limited support for legacy browsers
- **Mitigation:** Clear browser requirements documentation

### 12.2 Business Constraints

#### BC-001: Time-off Policies
- **Assumption:** All employees follow same approval workflow
- **Limitation:** Cannot customize workflows per department
- **Future:** Configurable workflows per organization unit

#### BC-002: Vacation Calculation
- **Assumption:** All vacation days counted equally
- **Limitation:** No half-days or hourly tracking
- **Future:** Hour-based tracking

#### BC-003: Manager Hierarchy
- **Assumption:** Single manager per employee
- **Limitation:** No matrix management support
- **Future:** Multiple approvers

#### BC-004: Language Support
- **Assumption:** English-only interface and documentation
- **Limitation:** No internationalization (i18n)
- **Future:** Multi-language support

### 12.3 Data Constraints

#### DC-001: Historical Data
- **Assumption:** No migration of historical time-off data
- **Impact:** Fresh start when system deployed
- **Mitigation:** Manual data import possible

#### DC-002: Workspace Sync Frequency
- **Assumption:** Manual sync triggered by admin
- **Limitation:** Not real-time
- **Future:** Automated daily sync

#### DC-003: Vacation Day Granularity
- **Assumption:** Full days only, no half-days
- **Impact:** Cannot request half-day off
- **Future:** Half-day and hour-based requests

### 12.4 Assumptions

#### AS-001: User Behavior
- Users have valid Google Workspace accounts
- Users can access internet during working hours
- Users understand time-off policies
- Managers respond to approval requests within 48 hours

#### AS-002: System Usage
- Average 100 time-off requests per month
- Peak usage during vacation seasons (summer, holidays)
- Average session duration 10-15 minutes
- Mobile usage approximately 30% of total

#### AS-003: Integration Reliability
- Google APIs available 99.9% of the time
- Workspace data accurate and up-to-date
- Calendar and Gmail APIs function as documented
- Gemini AI API responds within 5 seconds

#### AS-004: Organizational Structure
- Clear manager-employee relationships defined
- Admin users identified and configured
- Departments and locations standardized
- Vacation policies documented

---

## Appendix A: API Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /auth/login | No | Initiate OAuth login |
| GET | /auth/callback | No | OAuth callback handler |
| GET | /auth/logout | Yes | Logout and clear session |
| GET | /auth/status | No | Check authentication status |
| GET | /api/employees/me | Yes | Get current user profile |
| PUT | /api/employees/me | Yes | Update current user profile |
| GET | /api/employees/ | Yes | List employees (filtered) |
| GET | /api/employees/:email | Yes | Get specific employee |
| PUT | /api/employees/:email | Admin | Update employee |
| POST | /api/employees/sync | Admin | Sync from Workspace |
| GET | /api/employees/team | Manager | Get direct reports |
| POST | /api/timeoff/requests | Yes | Create time-off request |
| GET | /api/timeoff/requests/my | Yes | Get user's requests |
| GET | /api/timeoff/requests/:id | Yes | Get specific request |
| GET | /api/timeoff/requests/pending-approval | Yes | Get pending approvals |
| POST | /api/timeoff/requests/:id/approve-manager | Manager | Manager approval |
| POST | /api/timeoff/requests/:id/approve-admin | Admin | Admin approval |
| POST | /api/timeoff/requests/:id/reject | Manager/Admin | Reject request |
| POST | /api/timeoff/requests/:id/sync-calendar | Yes | Sync to calendar |
| POST | /api/timeoff/requests/:id/enable-autoresponder | Yes | Enable autoresponder |
| GET | /api/timeoff/vacation-summary | Yes | Get vacation summary |
| POST | /api/audit/query | Admin | Natural language query |
| GET | /health | No | Health check |
| GET | / | No | API info |

---

## Appendix B: Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid input data or validation error |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate request) |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service error (Calendar, Gmail) |
| 503 | Service Unavailable | Temporary service unavailable |

---

## Appendix C: Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| GCP_PROJECT_ID | Yes | Google Cloud project ID | my-project-123 |
| GOOGLE_CLIENT_ID | Yes | OAuth client ID | 123-abc.apps.googleusercontent.com |
| GOOGLE_CLIENT_SECRET | Yes | OAuth client secret | GOCSPX-abc123xyz789 |
| GOOGLE_REDIRECT_URI | Yes | OAuth redirect URI | https://example.com/auth/callback |
| GOOGLE_API_KEY | No | Gemini AI API key | AIza... |
| WORKSPACE_DOMAIN | Yes | Google Workspace domain | company.com |
| WORKSPACE_ADMIN_EMAIL | Yes | Workspace admin email | admin@company.com |
| ADMIN_USERS | Yes | Comma-separated admin emails | admin@company.com,hr@company.com |
| FLASK_SECRET_KEY | Yes | Flask session secret | random-secret-key-here |
| FLASK_ENV | No | Environment (production/development) | production |
| ENABLE_CHAT_NOTIFICATIONS | No | Enable Google Chat notifications | true |
| ENABLE_TASK_NOTIFICATIONS | No | Enable Google Tasks creation | true |
| NOTIFICATION_RETRY_ATTEMPTS | No | Max notification retry attempts | 3 |
| TASK_DUE_DAYS | No | Days until task due date | 2 |

**Note:** Google Chat and Tasks APIs use the same service account and OAuth scopes as other Google Workspace integrations. No separate API keys required.

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | System | Initial FRD creation |
| 1.1 | 2025-12-10 | System | Added Google Chat and Google Tasks integration for manager/admin notifications |

**Approval:**
- [ ] Product Owner: _________________ Date: _______
- [ ] Technical Lead: ________________ Date: _______
- [ ] Security Officer: ______________ Date: _______
- [ ] Compliance Officer: ____________ Date: _______

**Review Schedule:** Quarterly or upon major feature changes

---

*End of Functional Requirements Document*
