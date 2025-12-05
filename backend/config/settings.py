"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Cloud Configuration
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/callback')

# OAuth Scopes - Comprehensive list for all features
OAUTH_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.settings.sharing',
    'https://www.googleapis.com/auth/gmail.send',  # For sending notification emails
    'https://www.googleapis.com/auth/chat.messages',  # For Google Chat notifications
]

# Google Workspace Configuration
WORKSPACE_DOMAIN = os.getenv('WORKSPACE_DOMAIN')
WORKSPACE_ADMIN_EMAIL = os.getenv('WORKSPACE_ADMIN_EMAIL')

# Application Configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-me')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
PORT = int(os.getenv('PORT', 8080))

# Admin Users
ADMIN_USERS = os.getenv('ADMIN_USERS', '').split(',')

# Firestore Collections
EMPLOYEES_COLLECTION = os.getenv('EMPLOYEES_COLLECTION', 'employees')
TIMEOFF_REQUESTS_COLLECTION = os.getenv('TIMEOFF_REQUESTS_COLLECTION', 'timeoff_requests')
APPROVALS_COLLECTION = os.getenv('APPROVALS_COLLECTION', 'approvals')

# Organizational Units for Employee Management
EMPLOYEE_OU = os.getenv('EMPLOYEE_OU', '/Employees')
EXTERNAL_OU = os.getenv('EXTERNAL_OU', '/External')
OTHERS_OU = os.getenv('OTHERS_OU', '/Others')

# All available OUs
AVAILABLE_OUS = {
    'employees': EMPLOYEE_OU,
    'external': EXTERNAL_OU,
    'others': OTHERS_OU
}

# Time-off types
TIMEOFF_TYPES = ['vacation', 'sick_leave', 'day_off']

# Approval status
APPROVAL_STATUS = ['pending', 'manager_approved', 'approved', 'rejected']
