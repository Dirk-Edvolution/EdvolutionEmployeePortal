# Integration QA Protocol
# Employee Portal - Comprehensive Testing Plan

**Version:** 1.0
**Date:** 2025-12-10
**Test Environment:** Development (localhost:8080) and Production
**Execution:** Manual or Automated

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Environment Setup](#2-test-environment-setup)
3. [Test Data Preparation](#3-test-data-preparation)
4. [Authentication & Session Tests](#4-authentication--session-tests)
5. [Employee Management Tests](#5-employee-management-tests)
6. [Time-off Request Tests](#6-time-off-request-tests)
7. [Approval Workflow Tests](#7-approval-workflow-tests)
8. [Google Calendar Integration Tests](#8-google-calendar-integration-tests)
9. [Gmail Integration Tests](#9-gmail-integration-tests)
10. [Vacation Tracking Tests](#10-vacation-tracking-tests)
11. [Role-Based Access Control Tests](#11-role-based-access-control-tests)
12. [Natural Language Audit Query Tests](#12-natural-language-audit-query-tests)
13. [Error Handling Tests](#13-error-handling-tests)
14. [Performance Tests](#14-performance-tests)
15. [Security Tests](#15-security-tests)
16. [Test Summary Template](#16-test-summary-template)

---

## 1. Overview

### 1.1 Purpose
This document provides a comprehensive integration testing protocol for the Employee Portal system. It covers all major features, workflows, and integration points.

### 1.2 Scope
- End-to-end integration testing
- API endpoint testing
- Google Workspace integration testing
- Role-based access control verification
- Error handling validation
- Performance benchmarking

### 1.3 Test Approach
- Black-box testing from user perspective
- Integration testing across system components
- API-level testing using curl/Postman
- Manual verification of Google Calendar/Gmail changes
- Automated test scripts where applicable

### 1.4 Prerequisites
- Access to test Google Workspace domain
- Test user accounts with different roles (Employee, Manager, Admin)
- Backend running on localhost:8080 or production URL
- curl, jq, or Postman installed for API testing
- Access to Google Calendar and Gmail for test accounts

### 1.5 Test Accounts Required

| Role | Email | Manager | Purpose |
|------|-------|---------|---------|
| Admin | admin@company.com | - | System administration tests |
| Manager | manager@company.com | admin@company.com | Manager workflow tests |
| Employee 1 | employee1@company.com | manager@company.com | Standard employee tests |
| Employee 2 | employee2@company.com | manager@company.com | Secondary employee tests |
| Employee 3 | employee3@company.com | - | Independent employee tests |

---

## 2. Test Environment Setup

### 2.1 Environment Verification

**Test ID:** ENV-001
**Priority:** Critical
**Description:** Verify test environment is properly configured

**Pre-conditions:**
- Backend application deployed
- Environment variables configured
- Google Workspace access configured

**Test Steps:**
1. Check backend is running:
   ```bash
   curl http://localhost:8080/health
   ```
2. Expected response: `{"status": "healthy"}`
3. Verify API info endpoint:
   ```bash
   curl http://localhost:8080/
   ```
4. Expected response contains: `"name": "Employee Portal API"`

**Pass Criteria:**
- Both endpoints return 200 status
- Responses match expected format

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 2.2 Database Connectivity

**Test ID:** ENV-002
**Priority:** Critical
**Description:** Verify Firestore database connectivity

**Test Steps:**
1. Attempt to list employees (as admin):
   ```bash
   curl http://localhost:8080/api/employees/ \
     -b cookies.txt
   ```
2. Should return employee list or empty array (not error)

**Pass Criteria:**
- Returns 200 status or 401 (if not authenticated)
- No database connection errors

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 3. Test Data Preparation

### 3.1 Initial Setup Script

**Test ID:** DATA-001
**Priority:** Critical
**Description:** Set up test data in the system

**Test Steps:**

1. Login as admin user (manual via browser):
   ```
   http://localhost:8080/auth/login
   ```

2. Sync employees from Workspace:
   ```bash
   curl -X POST http://localhost:8080/api/employees/sync \
     -b cookies.txt
   ```

3. Verify employees synced:
   ```bash
   curl http://localhost:8080/api/employees/ \
     -b cookies.txt | jq 'length'
   ```

4. Configure manager relationships (if needed):
   ```bash
   curl -X PUT http://localhost:8080/api/employees/employee1@company.com \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "manager_email": "manager@company.com"
     }'
   ```

5. Set vacation days for test users:
   ```bash
   curl -X PUT http://localhost:8080/api/employees/employee1@company.com \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "vacation_days_per_year": 20
     }'
   ```

**Pass Criteria:**
- All employees synced from Workspace
- Manager relationships configured
- Vacation days set

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 4. Authentication & Session Tests

### 4.1 Google OAuth Login

**Test ID:** AUTH-001
**Priority:** Critical
**Description:** Verify Google OAuth login flow

**Pre-conditions:**
- Test user account exists in Google Workspace
- OAuth credentials configured

**Test Steps:**
1. Open browser to: `http://localhost:8080/auth/login`
2. Should redirect to Google OAuth consent screen
3. Login with test user credentials
4. Grant permissions if prompted
5. Should redirect back to `/auth/callback`
6. Should set session cookie
7. Should redirect to dashboard or home

**Pass Criteria:**
- OAuth flow completes successfully
- Session cookie set (check browser dev tools)
- User authenticated in system

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 4.2 Session Status Check

**Test ID:** AUTH-002
**Priority:** High
**Description:** Verify session status endpoint

**Pre-conditions:**
- User logged in from AUTH-001

**Test Steps:**
1. Check authentication status:
   ```bash
   curl http://localhost:8080/auth/status -b cookies.txt
   ```

2. Expected response:
   ```json
   {
     "authenticated": true,
     "user": {
       "email": "employee1@company.com",
       "name": "Employee One",
       "picture": "https://..."
     }
   }
   ```

**Pass Criteria:**
- Returns authenticated: true
- User details populated correctly

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 4.3 Logout

**Test ID:** AUTH-003
**Priority:** High
**Description:** Verify logout functionality

**Pre-conditions:**
- User logged in

**Test Steps:**
1. Call logout endpoint:
   ```bash
   curl http://localhost:8080/auth/logout -b cookies.txt -L
   ```

2. Verify session cleared:
   ```bash
   curl http://localhost:8080/auth/status -b cookies.txt
   ```

3. Expected response:
   ```json
   {
     "authenticated": false
   }
   ```

**Pass Criteria:**
- Logout successful
- Session cleared
- Subsequent requests not authenticated

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 4.4 Unauthenticated Access

**Test ID:** AUTH-004
**Priority:** Critical
**Description:** Verify protected endpoints reject unauthenticated requests

**Pre-conditions:**
- No active session (logged out)

**Test Steps:**
1. Attempt to access protected endpoint:
   ```bash
   curl http://localhost:8080/api/employees/me
   ```

2. Expected response: 401 Unauthorized
   ```json
   {
     "error": "Authentication required"
   }
   ```

3. Try multiple protected endpoints:
   - GET /api/employees/
   - GET /api/timeoff/requests/my
   - POST /api/timeoff/requests

**Pass Criteria:**
- All protected endpoints return 401
- No data leaked to unauthenticated users

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 4.5 Session Timeout

**Test ID:** AUTH-005
**Priority:** Medium
**Description:** Verify session expires after timeout period

**Pre-conditions:**
- User logged in
- Session timeout configured (24 hours default)

**Test Steps:**
1. Login and save session cookie
2. Wait for session timeout period (or manually expire in backend)
3. Attempt to access protected endpoint:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt
   ```

**Pass Criteria:**
- Expired session returns 401 Unauthorized
- User must re-authenticate

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip (time-consuming)

---

## 5. Employee Management Tests

### 5.1 View Own Profile

**Test ID:** EMP-001
**Priority:** Critical
**Description:** Employee can view their own profile

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Get own profile:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt | jq
   ```

2. Verify response contains:
   - email, given_name, family_name, full_name
   - manager_email
   - department, job_title, location
   - vacation_days_per_year
   - is_admin, is_active

**Pass Criteria:**
- Returns 200 status
- All profile fields populated
- Data matches Workspace data

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.2 Update Own Profile (Allowed Fields)

**Test ID:** EMP-002
**Priority:** High
**Description:** Employee can update allowed profile fields

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Update allowed fields:
   ```bash
   curl -X PUT http://localhost:8080/api/employees/me \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "location": "New York Office",
       "country": "US",
       "region": "New York",
       "vacation_days_per_year": 22
     }'
   ```

2. Verify update successful (200 status)

3. Verify changes persisted:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt | jq '.location, .vacation_days_per_year'
   ```

**Pass Criteria:**
- Update returns 200 status
- Changes reflected in subsequent GET
- Allowed fields updated successfully

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.3 Update Own Profile (Restricted Fields)

**Test ID:** EMP-003
**Priority:** High
**Description:** Employee CANNOT update admin-only fields

**Pre-conditions:**
- Logged in as employee1@company.com (non-admin)

**Test Steps:**
1. Attempt to update restricted fields:
   ```bash
   curl -X PUT http://localhost:8080/api/employees/me \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "manager_email": "someone-else@company.com",
       "is_admin": true,
       "salary": 999999
     }'
   ```

2. Should return error or ignore restricted fields

3. Verify fields NOT changed:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt | jq '.manager_email, .is_admin, .salary'
   ```

**Pass Criteria:**
- Restricted fields not modified
- Original values preserved
- May return 403 Forbidden or silently ignore

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.4 List Employees (Admin)

**Test ID:** EMP-004
**Priority:** Critical
**Description:** Admin can list all employees

**Pre-conditions:**
- Logged in as admin@company.com

**Test Steps:**
1. List all employees:
   ```bash
   curl http://localhost:8080/api/employees/ -b cookies.txt | jq 'length'
   ```

2. Verify returns array of employees
3. Count should match total employees in Workspace

**Pass Criteria:**
- Returns 200 status
- Array contains all employees
- Each employee has required fields

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.5 List Employees (Manager)

**Test ID:** EMP-005
**Priority:** High
**Description:** Manager can list only direct reports

**Pre-conditions:**
- Logged in as manager@company.com
- manager has direct reports configured

**Test Steps:**
1. List employees as manager:
   ```bash
   curl http://localhost:8080/api/employees/ -b cookies.txt | jq
   ```

2. Verify returns only direct reports

**Pass Criteria:**
- Returns 200 status
- Only direct reports returned
- No access to other employees

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.6 List Employees (Regular User)

**Test ID:** EMP-006
**Priority:** High
**Description:** Regular employee cannot list other employees

**Pre-conditions:**
- Logged in as employee1@company.com (not manager, not admin)

**Test Steps:**
1. Attempt to list employees:
   ```bash
   curl http://localhost:8080/api/employees/ -b cookies.txt | jq
   ```

2. Should return empty array or only self

**Pass Criteria:**
- Returns 200 status
- Empty array or self only
- No access to other employees' data

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.7 Get Specific Employee (Admin)

**Test ID:** EMP-007
**Priority:** High
**Description:** Admin can view any employee profile

**Pre-conditions:**
- Logged in as admin@company.com

**Test Steps:**
1. Get specific employee:
   ```bash
   curl http://localhost:8080/api/employees/employee1@company.com -b cookies.txt | jq
   ```

2. Verify full profile returned

**Pass Criteria:**
- Returns 200 status
- Full employee profile returned
- Includes all fields

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.8 Get Specific Employee (Unauthorized)

**Test ID:** EMP-008
**Priority:** Critical
**Description:** Regular user cannot view other employees' profiles

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Attempt to get another employee:
   ```bash
   curl http://localhost:8080/api/employees/employee2@company.com -b cookies.txt
   ```

2. Should return 403 Forbidden

**Pass Criteria:**
- Returns 403 status
- No data leaked
- Error message clear

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.9 Update Employee (Admin)

**Test ID:** EMP-009
**Priority:** High
**Description:** Admin can update any employee profile

**Pre-conditions:**
- Logged in as admin@company.com

**Test Steps:**
1. Update employee record:
   ```bash
   curl -X PUT http://localhost:8080/api/employees/employee1@company.com \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "manager_email": "manager@company.com",
       "job_title": "Senior Engineer",
       "department": "Engineering",
       "vacation_days_per_year": 25
     }'
   ```

2. Verify update successful

3. Verify changes in Workspace (for synced fields):
   - Check Google Admin Console for job_title, department updates

**Pass Criteria:**
- Returns 200 status
- Local fields updated in Firestore
- Synced fields updated in Workspace

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.10 Workspace Sync

**Test ID:** EMP-010
**Priority:** Critical
**Description:** Admin can sync employees from Workspace

**Pre-conditions:**
- Logged in as admin@company.com
- Workspace has active users

**Test Steps:**
1. Get employee count before sync:
   ```bash
   curl http://localhost:8080/api/employees/ -b cookies.txt | jq 'length'
   ```

2. Trigger sync:
   ```bash
   curl -X POST http://localhost:8080/api/employees/sync -b cookies.txt
   ```

3. Expected response:
   ```json
   {
     "success": true,
     "synced_count": 150,
     "message": "Successfully synced 150 employees from Workspace"
   }
   ```

4. Verify employee count after sync

**Pass Criteria:**
- Sync completes successfully
- All Workspace users synced
- Existing employees updated
- New employees created
- Returns accurate count

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 5.11 Get Team Members (Manager)

**Test ID:** EMP-011
**Priority:** High
**Description:** Manager can view their team members

**Pre-conditions:**
- Logged in as manager@company.com
- Has direct reports configured

**Test Steps:**
1. Get team members:
   ```bash
   curl http://localhost:8080/api/employees/team -b cookies.txt | jq
   ```

2. Verify returns only direct reports

**Pass Criteria:**
- Returns 200 status
- Only direct reports returned
- Each employee record complete

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 6. Time-off Request Tests

### 6.1 Create Vacation Request

**Test ID:** TO-001
**Priority:** Critical
**Description:** Employee can create vacation request

**Pre-conditions:**
- Logged in as employee1@company.com
- Has manager assigned
- Has vacation days available

**Test Steps:**
1. Create vacation request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-01",
       "end_date": "2025-07-05",
       "timeoff_type": "vacation",
       "notes": "Summer vacation"
     }'
   ```

2. Expected response (201 Created):
   ```json
   {
     "request_id": "abc123",
     "employee_email": "employee1@company.com",
     "start_date": "2025-07-01",
     "end_date": "2025-07-05",
     "timeoff_type": "vacation",
     "status": "pending",
     "manager_email": "manager@company.com",
     "days_count": 5,
     "created_at": "..."
   }
   ```

3. Save request_id for subsequent tests

**Pass Criteria:**
- Returns 201 status
- Request created with correct fields
- Status is "pending"
- Manager assigned correctly
- Days count calculated correctly (5 days)

**Actual Result:** _____________

**Request ID:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.2 Create Sick Leave Request

**Test ID:** TO-002
**Priority:** High
**Description:** Employee can create sick leave request

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Create sick leave request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-06-15",
       "end_date": "2025-06-15",
       "timeoff_type": "sick_leave",
       "notes": "Doctor appointment"
     }'
   ```

**Pass Criteria:**
- Returns 201 status
- Request created successfully
- Type is "sick_leave"
- Days count is 1

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.3 Create Day Off Request

**Test ID:** TO-003
**Priority:** High
**Description:** Employee can create day off request

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Create day off request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-06-20",
       "end_date": "2025-06-20",
       "timeoff_type": "day_off",
       "notes": "Personal day"
     }'
   ```

**Pass Criteria:**
- Returns 201 status
- Type is "day_off"

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.4 Invalid Request - Past Dates

**Test ID:** TO-004
**Priority:** High
**Description:** System rejects requests for past dates

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Attempt to create request with past dates:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2024-01-01",
       "end_date": "2024-01-05",
       "timeoff_type": "vacation",
       "notes": "Past vacation"
     }'
   ```

2. Should return 400 Bad Request

**Pass Criteria:**
- Returns 400 status
- Error message indicates past dates not allowed
- Request not created

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.5 Invalid Request - End Before Start

**Test ID:** TO-005
**Priority:** High
**Description:** System rejects requests where end_date < start_date

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Attempt invalid date range:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-10",
       "end_date": "2025-07-05",
       "timeoff_type": "vacation"
     }'
   ```

**Pass Criteria:**
- Returns 400 status
- Error message clear
- Request not created

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.6 Invalid Request - Missing Required Fields

**Test ID:** TO-006
**Priority:** High
**Description:** System validates required fields

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Attempt request without timeoff_type:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-01",
       "end_date": "2025-07-05"
     }'
   ```

2. Should return 400 Bad Request

**Pass Criteria:**
- Returns 400 status
- Error indicates missing field
- Request not created

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.7 Invalid Request - Invalid Type

**Test ID:** TO-007
**Priority:** Medium
**Description:** System validates timeoff_type enum

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Attempt invalid timeoff_type:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-01",
       "end_date": "2025-07-05",
       "timeoff_type": "invalid_type"
     }'
   ```

**Pass Criteria:**
- Returns 400 status
- Error indicates invalid type
- Valid types listed in error

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.8 View Own Requests

**Test ID:** TO-008
**Priority:** Critical
**Description:** Employee can view their own requests

**Pre-conditions:**
- Logged in as employee1@company.com
- Has created requests (from TO-001, TO-002, TO-003)

**Test Steps:**
1. Get own requests:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/my -b cookies.txt | jq
   ```

2. Verify all created requests returned

**Pass Criteria:**
- Returns 200 status
- All user's requests returned
- Requests sorted by date
- Each request has complete data

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.9 View Requests by Year

**Test ID:** TO-009
**Priority:** Medium
**Description:** Filter requests by year

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Get requests for 2025:
   ```bash
   curl "http://localhost:8080/api/timeoff/requests/my?year=2025" -b cookies.txt | jq
   ```

2. Verify only 2025 requests returned

**Pass Criteria:**
- Returns 200 status
- Only specified year returned
- Filtering works correctly

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.10 View Specific Request

**Test ID:** TO-010
**Priority:** High
**Description:** Employee can view specific request details

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request_id from TO-001

**Test Steps:**
1. Get specific request:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/REQUEST_ID -b cookies.txt | jq
   ```

**Pass Criteria:**
- Returns 200 status
- Full request details returned
- All fields populated

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 6.11 Cannot View Others' Requests

**Test ID:** TO-011
**Priority:** Critical
**Description:** Employee cannot view other employees' requests

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request_id from employee2's request

**Test Steps:**
1. Attempt to view another employee's request:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/OTHER_REQUEST_ID -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- No data leaked

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 7. Approval Workflow Tests

### 7.1 Manager Views Pending Approvals

**Test ID:** APPR-001
**Priority:** Critical
**Description:** Manager can view pending approval requests

**Pre-conditions:**
- Logged in as manager@company.com
- Have pending requests from direct reports (from TO-001)

**Test Steps:**
1. Get pending approvals:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/pending-approval -b cookies.txt | jq
   ```

2. Verify shows requests in "pending" status for direct reports

**Pass Criteria:**
- Returns 200 status
- Shows only direct reports' pending requests
- Status is "pending"
- Sorted by creation date

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.2 Manager Approves Request (Tier 1)

**Test ID:** APPR-002
**Priority:** Critical
**Description:** Manager can approve direct report's request

**Pre-conditions:**
- Logged in as manager@company.com
- Have request_id from TO-001 in "pending" status

**Test Steps:**
1. Approve request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/approve-manager \
     -b cookies.txt | jq
   ```

2. Expected response:
   ```json
   {
     "message": "Request approved by manager, pending admin approval",
     "request_id": "REQUEST_ID",
     "status": "manager_approved"
   }
   ```

3. Verify status changed:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/REQUEST_ID -b cookies.txt | jq '.status'
   ```

4. Should return "manager_approved"

**Pass Criteria:**
- Returns 200 status
- Status changes to "manager_approved"
- manager_approved_by and manager_approved_at set
- Timestamp recorded

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.3 Manager Cannot Approve Non-Report Request

**Test ID:** APPR-003
**Priority:** Critical
**Description:** Manager cannot approve requests from non-direct reports

**Pre-conditions:**
- Logged in as manager@company.com
- Have request_id from employee not managed by this manager

**Test Steps:**
1. Attempt to approve:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/OTHER_REQUEST_ID/approve-manager \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- Request status unchanged
- Clear error message

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.4 Manager Cannot Approve Own Request

**Test ID:** APPR-004
**Priority:** High
**Description:** Manager cannot approve their own time-off request

**Pre-conditions:**
- Logged in as manager@company.com
- Have request created by manager@company.com

**Test Steps:**
1. Manager creates own request
2. Manager attempts to approve own request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/OWN_REQUEST_ID/approve-manager \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- Request status unchanged
- Cannot self-approve

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.5 Admin Views Pending Admin Approvals

**Test ID:** APPR-005
**Priority:** Critical
**Description:** Admin views requests pending final approval

**Pre-conditions:**
- Logged in as admin@company.com
- Have requests in "manager_approved" status (from APPR-002)

**Test Steps:**
1. Get pending admin approvals:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/pending-approval -b cookies.txt | jq
   ```

2. Verify shows "manager_approved" requests

**Pass Criteria:**
- Returns 200 status
- Shows requests in "manager_approved" status
- All requests awaiting admin approval visible

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.6 Admin Approves Request (Tier 2)

**Test ID:** APPR-006
**Priority:** Critical
**Description:** Admin provides final approval

**Pre-conditions:**
- Logged in as admin@company.com
- Have request_id in "manager_approved" status

**Test Steps:**
1. Approve request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/approve-admin \
     -b cookies.txt | jq
   ```

2. Expected response:
   ```json
   {
     "message": "Request fully approved",
     "request_id": "REQUEST_ID",
     "status": "approved"
   }
   ```

3. Verify status:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/REQUEST_ID -b cookies.txt | jq '.status'
   ```

4. Should return "approved"

**Pass Criteria:**
- Returns 200 status
- Status changes to "approved"
- admin_approved_by and admin_approved_at set
- Fully approved

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.7 Admin Cannot Approve Pending Request

**Test ID:** APPR-007
**Priority:** High
**Description:** Admin cannot skip manager approval (normal case)

**Pre-conditions:**
- Logged in as admin@company.com
- Have request in "pending" status (not manager_approved)

**Test Steps:**
1. Attempt admin approval of pending request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/PENDING_REQUEST_ID/approve-admin \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden (unless admin is also the manager)
- Request status unchanged
- Manager approval required first

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.8 Admin as Manager Can Do Both Approvals

**Test ID:** APPR-008
**Priority:** Medium
**Description:** If admin is also the manager, can approve directly

**Pre-conditions:**
- Admin user (admin@company.com) is assigned as manager
- Have request in "pending" status for this admin-manager

**Test Steps:**
1. Admin-manager approves directly:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/approve-admin \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 200 status
- Skip to "approved" status directly
- OR require two separate approval calls

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] N/A

---

### 7.9 Manager Rejects Request

**Test ID:** APPR-009
**Priority:** High
**Description:** Manager can reject direct report's request

**Pre-conditions:**
- Logged in as manager@company.com
- Have request in "pending" status

**Test Steps:**
1. Reject request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/reject \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "reason": "Insufficient team coverage during this period"
     }'
   ```

2. Expected response:
   ```json
   {
     "message": "Request rejected",
     "request_id": "REQUEST_ID",
     "status": "rejected",
     "rejection_reason": "Insufficient team coverage during this period"
   }
   ```

**Pass Criteria:**
- Returns 200 status
- Status changes to "rejected"
- Rejection reason stored
- rejected_by and rejected_at set

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.10 Admin Rejects Request

**Test ID:** APPR-010
**Priority:** High
**Description:** Admin can reject any request

**Pre-conditions:**
- Logged in as admin@company.com
- Have request in any status (pending or manager_approved)

**Test Steps:**
1. Reject request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/reject \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "reason": "Company-wide vacation freeze this month"
     }'
   ```

**Pass Criteria:**
- Returns 200 status
- Status changes to "rejected"
- Rejection reason stored

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.11 Rejection Requires Reason

**Test ID:** APPR-011
**Priority:** Medium
**Description:** Rejection must include a reason

**Pre-conditions:**
- Logged in as manager or admin

**Test Steps:**
1. Attempt rejection without reason:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REQUEST_ID/reject \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{}'
   ```

**Pass Criteria:**
- Returns 400 Bad Request
- Error indicates reason required
- Request status unchanged

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.12 Cannot Approve Already Approved Request

**Test ID:** APPR-012
**Priority:** Medium
**Description:** Cannot re-approve already approved request

**Pre-conditions:**
- Have request in "approved" status (from APPR-006)

**Test Steps:**
1. Attempt to approve again:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/APPROVED_REQUEST_ID/approve-admin \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 400 or 409 status
- Error indicates already approved
- Status unchanged

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 7.13 Cannot Approve Rejected Request

**Test ID:** APPR-013
**Priority:** Medium
**Description:** Cannot approve rejected request

**Pre-conditions:**
- Have request in "rejected" status

**Test Steps:**
1. Attempt to approve rejected request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/REJECTED_REQUEST_ID/approve-manager \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 400 or 409 status
- Error indicates request rejected
- Status unchanged

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 8. Google Calendar Integration Tests

### 8.1 Sync Approved Request to Calendar

**Test ID:** CAL-001
**Priority:** High
**Description:** Employee can sync approved request to Google Calendar

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request in "approved" status (from APPR-006)
- Calendar API access granted

**Test Steps:**
1. Sync to calendar:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/APPROVED_REQUEST_ID/sync-calendar \
     -b cookies.txt | jq
   ```

2. Expected response:
   ```json
   {
     "message": "Successfully synced to Google Calendar",
     "event_id": "calendar_event_123"
   }
   ```

3. Verify in Google Calendar:
   - Open employee1@company.com's Google Calendar
   - Check for OOO event on specified dates
   - Verify event marked as "Out of Office"

**Pass Criteria:**
- Returns 200 status
- Event ID returned
- Event visible in Google Calendar
- Event shows as all-day OOO event
- Date range matches request

**Actual Result:** _____________

**Calendar Event Visible:** [ ] Yes [ ] No

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 8.2 Cannot Sync Non-Approved Request

**Test ID:** CAL-002
**Priority:** High
**Description:** Cannot sync pending or rejected requests

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request in "pending" or "rejected" status

**Test Steps:**
1. Attempt to sync non-approved request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/PENDING_REQUEST_ID/sync-calendar \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- Error indicates request not approved
- No calendar event created

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 8.3 Cannot Sync Others' Requests

**Test ID:** CAL-003
**Priority:** Critical
**Description:** Cannot sync another employee's calendar

**Pre-conditions:**
- Logged in as employee1@company.com
- Have approved request from employee2@company.com

**Test Steps:**
1. Attempt to sync another employee's request:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/OTHER_APPROVED_REQUEST_ID/sync-calendar \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- No calendar access for other users
- No event created

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 8.4 Calendar Event Details

**Test ID:** CAL-004
**Priority:** Medium
**Description:** Verify calendar event has correct details

**Pre-conditions:**
- Completed CAL-001 successfully

**Test Steps:**
1. Manually check Google Calendar event:
   - Event title contains "OOO" or "Time Off"
   - Event description contains request details
   - Event type is "Out of Office"
   - Event is all-day
   - Event covers exact date range

**Pass Criteria:**
- All event details correct
- Proper OOO formatting
- Dates match exactly

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 8.5 Calendar Sync Idempotency

**Test ID:** CAL-005
**Priority:** Low
**Description:** Re-syncing updates existing event (doesn't duplicate)

**Pre-conditions:**
- Request already synced to calendar

**Test Steps:**
1. Sync again:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/APPROVED_REQUEST_ID/sync-calendar \
     -b cookies.txt
   ```

2. Check calendar for duplicate events

**Pass Criteria:**
- No duplicate events created
- Existing event updated OR error returned

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

## 9. Gmail Integration Tests

### 9.1 Enable Auto-responder for Approved Request

**Test ID:** GMAIL-001
**Priority:** High
**Description:** Employee can enable Gmail auto-responder

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request in "approved" status
- Gmail API access granted

**Test Steps:**
1. Enable auto-responder:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/APPROVED_REQUEST_ID/enable-autoresponder \
     -b cookies.txt | jq
   ```

2. Expected response:
   ```json
   {
     "message": "Gmail auto-responder enabled successfully"
   }
   ```

3. Verify in Gmail:
   - Go to Gmail settings
   - Check "Vacation responder" is enabled
   - Verify start/end dates match request
   - Verify auto-responder message contains OOO info

**Pass Criteria:**
- Returns 200 status
- Vacation responder enabled in Gmail
- Start/end dates correct
- Auto-responder message appropriate

**Actual Result:** _____________

**Gmail Responder Active:** [ ] Yes [ ] No

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 9.2 Cannot Enable for Non-Approved Request

**Test ID:** GMAIL-002
**Priority:** High
**Description:** Cannot enable auto-responder for pending/rejected requests

**Pre-conditions:**
- Logged in as employee1@company.com
- Have request not in "approved" status

**Test Steps:**
1. Attempt to enable auto-responder:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/PENDING_REQUEST_ID/enable-autoresponder \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- No auto-responder enabled
- Error message clear

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 9.3 Cannot Enable for Others

**Test ID:** GMAIL-003
**Priority:** Critical
**Description:** Cannot enable auto-responder for another employee

**Pre-conditions:**
- Logged in as employee1@company.com
- Have approved request from employee2@company.com

**Test Steps:**
1. Attempt to enable another's auto-responder:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/OTHER_APPROVED_REQUEST_ID/enable-autoresponder \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns 403 Forbidden
- No access to other users' Gmail
- Security boundary enforced

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 9.4 Auto-responder Message Content

**Test ID:** GMAIL-004
**Priority:** Medium
**Description:** Verify auto-responder message content

**Pre-conditions:**
- Completed GMAIL-001 successfully

**Test Steps:**
1. Manually check Gmail vacation responder settings:
   - Message includes OOO notification
   - Message includes return date
   - Message professional and appropriate

**Pass Criteria:**
- Message content appropriate
- Dates included
- Professional formatting

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 10. Vacation Tracking Tests

### 10.1 Get Vacation Summary

**Test ID:** VAC-001
**Priority:** Critical
**Description:** Employee can view vacation day summary

**Pre-conditions:**
- Logged in as employee1@company.com
- Has vacation_days_per_year set (e.g., 20)
- Has approved vacation requests for current year

**Test Steps:**
1. Get vacation summary:
   ```bash
   curl http://localhost:8080/api/timeoff/vacation-summary -b cookies.txt | jq
   ```

2. Expected response:
   ```json
   {
     "year": 2025,
     "total_days": 20,
     "used_days": 5,
     "remaining_days": 15,
     "country": "US",
     "region": "California"
   }
   ```

**Pass Criteria:**
- Returns 200 status
- Total days matches vacation_days_per_year
- Used days accurately calculated from approved requests
- Remaining days = total - used
- Correct year returned

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 10.2 Vacation Calculation Accuracy

**Test ID:** VAC-002
**Priority:** Critical
**Description:** Verify vacation days calculation is accurate

**Pre-conditions:**
- Know exact vacation requests and days

**Test Steps:**
1. List all approved vacation requests for employee:
   ```bash
   curl "http://localhost:8080/api/timeoff/requests/my?year=2025" -b cookies.txt | \
     jq '[.[] | select(.timeoff_type == "vacation" and .status == "approved")]'
   ```

2. Manually calculate total days from requests

3. Compare with vacation summary used_days

**Pass Criteria:**
- Manual calculation matches used_days
- Only approved vacation requests counted
- Sick leave and day_off not counted
- Only current year counted

**Actual Result:** _____________

**Manual Count:** _______ days

**System Count:** _______ days

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 10.3 Vacation Summary by Year

**Test ID:** VAC-003
**Priority:** Medium
**Description:** Can get vacation summary for specific year

**Pre-conditions:**
- Logged in as employee1@company.com

**Test Steps:**
1. Get summary for 2025:
   ```bash
   curl "http://localhost:8080/api/timeoff/vacation-summary?year=2025" -b cookies.txt | jq
   ```

2. Get summary for 2024:
   ```bash
   curl "http://localhost:8080/api/timeoff/vacation-summary?year=2024" -b cookies.txt | jq
   ```

3. Verify different used_days for different years

**Pass Criteria:**
- Year parameter works correctly
- Each year calculated independently
- Correct requests included per year

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 10.4 Negative Balance Handling

**Test ID:** VAC-004
**Priority:** Medium
**Description:** System handles negative vacation balance

**Pre-conditions:**
- Employee has used more days than allocated (edge case)

**Test Steps:**
1. Get vacation summary with negative balance:
   ```bash
   curl http://localhost:8080/api/timeoff/vacation-summary -b cookies.txt | jq
   ```

2. Check if remaining_days can be negative

**Pass Criteria:**
- System handles negative balance gracefully
- Displays negative remaining_days OR shows 0
- No calculation errors

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] N/A

---

### 10.5 Sick Leave Not Counted

**Test ID:** VAC-005
**Priority:** High
**Description:** Sick leave and day_off do not reduce vacation balance

**Pre-conditions:**
- Employee has approved sick_leave and day_off requests

**Test Steps:**
1. Note vacation balance
2. Create and approve sick_leave request
3. Check vacation balance again

**Pass Criteria:**
- Vacation balance unchanged
- Only "vacation" type counted
- Sick leave and day_off excluded

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 11. Role-Based Access Control Tests

### 11.1 RBAC Matrix Verification

**Test ID:** RBAC-001
**Priority:** Critical
**Description:** Verify complete RBAC matrix

**Pre-conditions:**
- Have employee, manager, and admin test accounts

**Test Steps:**
Execute all operations as each role and verify access:

| Operation | Employee | Manager | Admin |
|-----------|----------|---------|-------|
| View own profile | ✓ | ✓ | ✓ |
| Update own profile | ✓ (limited) | ✓ (limited) | ✓ (limited) |
| View other profiles | ✗ | ✓ (reports) | ✓ (all) |
| Update other profiles | ✗ | ✗ | ✓ |
| Create time-off | ✓ | ✓ | ✓ |
| View own requests | ✓ | ✓ | ✓ |
| View other requests | ✗ | ✓ (reports) | ✓ (all) |
| Approve manager tier | ✗ | ✓ (reports) | ✓ |
| Approve admin tier | ✗ | ✗ | ✓ |
| Sync Workspace | ✗ | ✗ | ✓ |

**Pass Criteria:**
- All access controls enforced
- No privilege escalation possible
- 403 errors for unauthorized access

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 11.2 Admin Privilege Escalation Test

**Test ID:** RBAC-002
**Priority:** Critical
**Description:** Regular user cannot escalate to admin

**Pre-conditions:**
- Logged in as employee1@company.com (non-admin)

**Test Steps:**
1. Attempt to set own is_admin to true:
   ```bash
   curl -X PUT http://localhost:8080/api/employees/me \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"is_admin": true}'
   ```

2. Verify is_admin unchanged:
   ```bash
   curl http://localhost:8080/api/employees/me -b cookies.txt | jq '.is_admin'
   ```

**Pass Criteria:**
- is_admin remains false
- Cannot self-promote to admin
- Field modification blocked

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 11.3 Manager Scope Limitation

**Test ID:** RBAC-003
**Priority:** High
**Description:** Manager can only access direct reports' data

**Pre-conditions:**
- Logged in as manager@company.com
- Have employee3@company.com NOT managed by this manager

**Test Steps:**
1. Attempt to view non-report employee:
   ```bash
   curl http://localhost:8080/api/employees/employee3@company.com -b cookies.txt
   ```

2. Attempt to view non-report time-off request:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/NON_REPORT_REQUEST_ID -b cookies.txt
   ```

**Pass Criteria:**
- Both return 403 Forbidden
- Manager scope properly limited
- No data leakage

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

## 12. Natural Language Audit Query Tests

### 12.1 Setup Audit Query System

**Test ID:** AUDIT-001
**Priority:** Low
**Description:** Verify audit query system configured

**Pre-conditions:**
- GOOGLE_API_KEY environment variable set
- Logged in as admin@company.com

**Test Steps:**
1. Check if Gemini API key configured (check logs or settings)
2. Verify audit logs exist in system

**Pass Criteria:**
- API key configured
- Audit logs collection exists
- Feature available

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

### 12.2 Natural Language Query - Approvals

**Test ID:** AUDIT-002
**Priority:** Low
**Description:** Query approval actions using natural language

**Pre-conditions:**
- Logged in as admin@company.com
- Audit logging integrated (Note: may not be integrated yet)

**Test Steps:**
1. Ask natural language question:
   ```bash
   curl -X POST http://localhost:8080/api/audit/query \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"question": "who approved employee1 vacation last week?"}'
   ```

2. Expected response:
   ```json
   {
     "question": "who approved employee1 vacation last week?",
     "answer": "Manager approved Employee1's vacation on Dec 8, 2025.",
     "logs": [...],
     "total_matches": 1
   }
   ```

**Pass Criteria:**
- Returns natural language answer
- Includes relevant audit logs
- Answer accurate

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

### 12.3 Natural Language Query - User Activity

**Test ID:** AUDIT-003
**Priority:** Low
**Description:** Query user activity

**Pre-conditions:**
- Logged in as admin@company.com

**Test Steps:**
1. Query user activity:
   ```bash
   curl -X POST http://localhost:8080/api/audit/query \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"question": "what did employee1 do yesterday?"}'
   ```

**Pass Criteria:**
- Returns activity summary
- Natural language response
- Relevant audit logs

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

### 12.4 Audit Query Access Control

**Test ID:** AUDIT-004
**Priority:** Medium
**Description:** Non-admins cannot query all audit logs

**Pre-conditions:**
- Logged in as employee1@company.com (non-admin)

**Test Steps:**
1. Attempt audit query:
   ```bash
   curl -X POST http://localhost:8080/api/audit/query \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"question": "show all approvals this month"}'
   ```

**Pass Criteria:**
- Returns 403 Forbidden OR only own actions
- Non-admins restricted
- No data leakage

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

## 13. Error Handling Tests

### 13.1 Invalid JSON Handling

**Test ID:** ERR-001
**Priority:** Medium
**Description:** System handles malformed JSON gracefully

**Test Steps:**
1. Send invalid JSON:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{invalid json}'
   ```

**Pass Criteria:**
- Returns 400 Bad Request
- Error message indicates JSON parse error
- No server crash

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 13.2 Missing Content-Type

**Test ID:** ERR-002
**Priority:** Low
**Description:** System handles missing Content-Type header

**Test Steps:**
1. Send request without Content-Type:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -b cookies.txt \
     -d '{"start_date": "2025-07-01"}'
   ```

**Pass Criteria:**
- Returns 400 or 415 status
- Clear error message
- Or accepts and parses correctly

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 13.3 Non-Existent Resource

**Test ID:** ERR-003
**Priority:** Medium
**Description:** 404 for non-existent resources

**Test Steps:**
1. Request non-existent time-off request:
   ```bash
   curl http://localhost:8080/api/timeoff/requests/nonexistent123 -b cookies.txt
   ```

2. Request non-existent employee:
   ```bash
   curl http://localhost:8080/api/employees/nonexistent@company.com -b cookies.txt
   ```

**Pass Criteria:**
- Returns 404 Not Found
- Clear error message
- No data leakage

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 13.4 SQL Injection Protection (N/A for Firestore)

**Test ID:** ERR-004
**Priority:** Low
**Description:** Verify no SQL injection vulnerabilities

**Note:** Firestore is NoSQL, but test input sanitization

**Test Steps:**
1. Send SQL-like payload:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-01",
       "end_date": "2025-07-05",
       "timeoff_type": "vacation",
       "notes": "Test; DROP TABLE employees;--"
     }'
   ```

**Pass Criteria:**
- Input sanitized or safely stored
- No code execution
- Notes stored as plain text

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] N/A

---

### 13.5 XSS Protection

**Test ID:** ERR-005
**Priority:** High
**Description:** Prevent XSS attacks in user input

**Test Steps:**
1. Send XSS payload:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "start_date": "2025-07-01",
       "end_date": "2025-07-05",
       "timeoff_type": "vacation",
       "notes": "<script>alert(\"XSS\")</script>"
     }'
   ```

2. Retrieve request and verify script not executed when displayed

**Pass Criteria:**
- Input sanitized or properly escaped
- No script execution in UI
- Data stored safely

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 13.6 Workspace API Failure Handling

**Test ID:** ERR-006
**Priority:** High
**Description:** System handles Google Workspace API failures

**Test Steps:**
1. Simulate Workspace API unavailable (requires test setup)
2. OR disconnect network temporarily
3. Attempt employee sync:
   ```bash
   curl -X POST http://localhost:8080/api/employees/sync -b cookies.txt
   ```

**Pass Criteria:**
- Returns 502 Bad Gateway or 500
- Error message indicates external service issue
- System remains stable
- Partial data not corrupted

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

### 13.7 Calendar API Failure Handling

**Test ID:** ERR-007
**Priority:** Medium
**Description:** Graceful handling of Calendar API errors

**Test Steps:**
1. Revoke Calendar API access for test user
2. Attempt to sync time-off to calendar:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests/APPROVED_REQUEST_ID/sync-calendar \
     -b cookies.txt
   ```

**Pass Criteria:**
- Returns appropriate error status (502 or 500)
- Error message clear
- Request status unchanged
- No partial state

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

## 14. Performance Tests

### 14.1 Response Time - List Employees

**Test ID:** PERF-001
**Priority:** Medium
**Description:** Verify employee list response time

**Pre-conditions:**
- Database has 100+ employees

**Test Steps:**
1. Measure response time:
   ```bash
   time curl http://localhost:8080/api/employees/ -b cookies.txt -o /dev/null -w "%{time_total}\n"
   ```

**Pass Criteria:**
- Response time < 500ms (95th percentile)
- Acceptable performance

**Actual Result:** _________ ms

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 14.2 Response Time - Vacation Summary

**Test ID:** PERF-002
**Priority:** Medium
**Description:** Vacation calculation performance

**Test Steps:**
1. Measure response time:
   ```bash
   time curl http://localhost:8080/api/timeoff/vacation-summary -b cookies.txt -o /dev/null -w "%{time_total}\n"
   ```

**Pass Criteria:**
- Response time < 500ms
- Calculation efficient

**Actual Result:** _________ ms

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 14.3 Workspace Sync Performance

**Test ID:** PERF-003
**Priority:** Medium
**Description:** Employee sync completes in reasonable time

**Pre-conditions:**
- Workspace has 100+ users

**Test Steps:**
1. Time the sync operation:
   ```bash
   time curl -X POST http://localhost:8080/api/employees/sync -b cookies.txt
   ```

**Pass Criteria:**
- Completes within 60 seconds for 500 users
- No timeout errors

**Actual Result:** _________ seconds for _______ users

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 14.4 Concurrent Request Handling

**Test ID:** PERF-004
**Priority:** Low
**Description:** System handles concurrent requests

**Test Steps:**
1. Send 10 concurrent requests:
   ```bash
   for i in {1..10}; do
     curl http://localhost:8080/api/employees/me -b cookies.txt &
   done
   wait
   ```

2. Verify all complete successfully

**Pass Criteria:**
- All requests return 200
- No timeouts or errors
- Consistent response times

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Skip

---

## 15. Security Tests

### 15.1 HTTPS Enforcement

**Test ID:** SEC-001
**Priority:** Critical (Production only)
**Description:** Production enforces HTTPS

**Pre-conditions:**
- Testing production environment

**Test Steps:**
1. Attempt HTTP connection:
   ```bash
   curl http://production-url.com/api/employees/me
   ```

**Pass Criteria:**
- Redirects to HTTPS OR connection refused
- No data sent over HTTP

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] N/A (Dev)

---

### 15.2 Cookie Security Flags

**Test ID:** SEC-002
**Priority:** High
**Description:** Session cookies have security flags

**Test Steps:**
1. Login and inspect cookies in browser dev tools
2. Check cookie attributes:
   - HTTPOnly: true
   - Secure: true (in production)
   - SameSite: Lax or Strict

**Pass Criteria:**
- HTTPOnly flag set
- Secure flag set (production)
- SameSite configured

**Actual Result:** _____________

**Cookie Flags:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 15.3 CSRF Protection

**Test ID:** SEC-003
**Priority:** High
**Description:** Cross-Site Request Forgery protection

**Test Steps:**
1. Attempt POST request without session cookie:
   ```bash
   curl -X POST http://localhost:8080/api/timeoff/requests \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-07-01", "end_date": "2025-07-05", "timeoff_type": "vacation"}'
   ```

**Pass Criteria:**
- Returns 401 Unauthorized
- CSRF token required or session validated
- Protected against CSRF

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 15.4 Password/Secret Exposure

**Test ID:** SEC-004
**Priority:** Critical
**Description:** No secrets exposed in responses or errors

**Test Steps:**
1. Trigger various errors and check responses
2. Check API responses for sensitive data
3. Verify no OAuth secrets, API keys, or database credentials exposed

**Pass Criteria:**
- No secrets in error messages
- No secrets in API responses
- Stack traces sanitized

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked

---

### 15.5 Rate Limiting (if implemented)

**Test ID:** SEC-005
**Priority:** Low
**Description:** Rate limiting prevents abuse

**Test Steps:**
1. Send many requests rapidly:
   ```bash
   for i in {1..100}; do
     curl http://localhost:8080/api/employees/me -b cookies.txt
   done
   ```

**Pass Criteria:**
- Rate limiting triggers after threshold
- Returns 429 Too Many Requests
- Prevents brute force

**Actual Result:** _____________

**Status:** [ ] Pass [ ] Fail [ ] Blocked [ ] Not Implemented

---

## 16. Test Summary Template

### Test Execution Summary

**Test Date:** ___________
**Tester:** ___________
**Environment:** [ ] Development [ ] Production
**Build/Version:** ___________

#### Results Overview

| Category | Total | Pass | Fail | Blocked | Skip |
|----------|-------|------|------|---------|------|
| Authentication | 5 | ___ | ___ | ___ | ___ |
| Employee Management | 11 | ___ | ___ | ___ | ___ |
| Time-off Requests | 11 | ___ | ___ | ___ | ___ |
| Approval Workflow | 13 | ___ | ___ | ___ | ___ |
| Calendar Integration | 5 | ___ | ___ | ___ | ___ |
| Gmail Integration | 4 | ___ | ___ | ___ | ___ |
| Vacation Tracking | 5 | ___ | ___ | ___ | ___ |
| RBAC | 3 | ___ | ___ | ___ | ___ |
| Audit Query | 4 | ___ | ___ | ___ | ___ |
| Error Handling | 7 | ___ | ___ | ___ | ___ |
| Performance | 4 | ___ | ___ | ___ | ___ |
| Security | 5 | ___ | ___ | ___ | ___ |
| **TOTAL** | **77** | ___ | ___ | ___ | ___ |

#### Pass Rate

**Overall Pass Rate:** _______% (Pass / (Total - Skip - Blocked))

#### Critical Issues Found

1. _________________________________
2. _________________________________
3. _________________________________

#### Recommendations

1. _________________________________
2. _________________________________
3. _________________________________

#### Sign-off

**QA Engineer:** ___________________ Date: ___________

**Product Owner:** _________________ Date: ___________

---

## Appendix A: Test Data Cleanup

After testing, clean up test data:

```bash
# Delete test time-off requests (admin only)
# Note: Delete functionality may not be implemented

# Reset employee vacation days to defaults
curl -X PUT http://localhost:8080/api/employees/employee1@company.com \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"vacation_days_per_year": 20}'

# Remove test calendar events (manual)
# - Go to Google Calendar
# - Delete test OOO events

# Disable test auto-responders (manual)
# - Go to Gmail settings
# - Disable vacation responder
```

---

## Appendix B: Automation Scripts

### Quick Test Script (Bash)

```bash
#!/bin/bash
# quick-test.sh - Run basic smoke tests

BASE_URL="http://localhost:8080"
COOKIES="cookies.txt"

echo "=== Employee Portal Integration Tests ==="

# Test 1: Health check
echo "Test: Health check"
curl -s "$BASE_URL/health" | grep -q "healthy" && echo "✓ PASS" || echo "✗ FAIL"

# Test 2: API info
echo "Test: API info"
curl -s "$BASE_URL/" | grep -q "Employee Portal API" && echo "✓ PASS" || echo "✗ FAIL"

# Test 3: Auth status (should be unauthenticated)
echo "Test: Auth status"
curl -s "$BASE_URL/auth/status" | grep -q '"authenticated":false' && echo "✓ PASS" || echo "✗ FAIL"

echo "=== Basic smoke tests complete ==="
```

### Python Test Script

```python
#!/usr/bin/env python3
"""
integration_tests.py - Automated integration tests
"""
import requests
import json

BASE_URL = "http://localhost:8080"
session = requests.Session()

def test_health():
    """Test health endpoint"""
    resp = session.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
    print("✓ Health check passed")

def test_api_info():
    """Test API info endpoint"""
    resp = session.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Employee Portal API"
    print("✓ API info passed")

def test_unauthenticated_access():
    """Test protected endpoint without auth"""
    resp = session.get(f"{BASE_URL}/api/employees/me")
    assert resp.status_code == 401
    print("✓ Unauthenticated access blocked")

if __name__ == "__main__":
    print("Running automated integration tests...")
    test_health()
    test_api_info()
    test_unauthenticated_access()
    print("\n✓ All automated tests passed!")
```

---

## Appendix C: Manual Testing Checklist

### Quick Manual Test Checklist

- [ ] Login with Google OAuth
- [ ] View own employee profile
- [ ] Create vacation request
- [ ] Login as manager
- [ ] View pending approvals
- [ ] Approve request (tier 1)
- [ ] Login as admin
- [ ] Approve request (tier 2)
- [ ] Login as employee
- [ ] Sync to Google Calendar
- [ ] Enable Gmail auto-responder
- [ ] Check vacation balance
- [ ] Verify calendar event created
- [ ] Verify Gmail responder active
- [ ] Logout

---

*End of Integration QA Protocol*
