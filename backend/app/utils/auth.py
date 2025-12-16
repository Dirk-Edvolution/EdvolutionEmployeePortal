"""
Authentication utilities for Google OAuth
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from backend.config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    OAUTH_SCOPES,
    ADMIN_USERS,
)
import os


# Disable OAuthlib's HTTPS verification when running locally
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def create_oauth_flow(redirect_uri=None):
    """Create OAuth flow for Google authentication"""
    if redirect_uri is None:
        redirect_uri = GOOGLE_REDIRECT_URI

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=OAUTH_SCOPES,
        redirect_uri=redirect_uri
    )
    return flow


def get_credentials_from_session():
    """Get Google credentials from Flask session"""
    if 'credentials' not in session:
        return None

    return Credentials(**session['credentials'])


def credentials_to_dict(credentials):
    """Convert credentials to dictionary for session storage"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_email = session.get('user_email')
        if user_email not in ADMIN_USERS:
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_current_user_email():
    """Get current logged-in user's email"""
    return session.get('user_email')


def is_admin(email: str) -> bool:
    """Check if user is an admin"""
    return email in ADMIN_USERS
