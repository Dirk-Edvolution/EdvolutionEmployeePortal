"""
Authentication routes for Google OAuth
"""
from flask import Blueprint, session, redirect, request, jsonify, url_for
from googleapiclient.discovery import build
from backend.app.utils.auth import (
    create_oauth_flow,
    credentials_to_dict,
    get_credentials_from_session,
)
from backend.app.services import FirestoreService
from backend.config.settings import FLASK_ENV
import time

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# In-memory state store for OAuth (simple dict with expiration)
# This works within a single Cloud Run container instance
_oauth_states = {}

def _clean_expired_states():
    """Remove expired states (older than 10 minutes)"""
    now = time.time()
    expired = [k for k, v in _oauth_states.items() if now - v['timestamp'] > 600]
    for k in expired:
        del _oauth_states[k]

def _store_state(state):
    """Store OAuth state"""
    _clean_expired_states()
    _oauth_states[state] = {'timestamp': time.time()}

def _verify_state(state):
    """Verify and remove OAuth state"""
    _clean_expired_states()
    return _oauth_states.pop(state, None) is not None


@auth_bp.route('/login')
def login():
    """Initiate OAuth flow"""
    import logging
    logger = logging.getLogger(__name__)

    # Build dynamic redirect URI based on current request host
    # This supports both production (rrhh.edvolution.io) and test URLs (test---employee-portal-...)
    host_url = request.host_url.rstrip('/')
    dynamic_redirect_uri = f"{host_url}/auth/callback"

    logger.info(f"Login: Using dynamic redirect URI: {dynamic_redirect_uri}")

    flow = create_oauth_flow(redirect_uri=dynamic_redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )

    # Store state in server-side memory instead of client session
    _store_state(state)

    logger.info(f"Login: Stored OAuth state in memory: {state}")
    logger.info(f"Login: Total stored states: {len(_oauth_states)}")

    return redirect(authorization_url)


@auth_bp.route('/callback')
def callback():
    """OAuth callback handler"""
    import logging
    logger = logging.getLogger(__name__)

    state_from_request = request.args.get('state')

    logger.info(f"Callback: Received state: {state_from_request}")
    logger.info(f"Callback: Total stored states: {len(_oauth_states)}")
    logger.info(f"Callback: Stored states: {list(_oauth_states.keys())}")

    # Verify state from server-side memory
    if not state_from_request or not _verify_state(state_from_request):
        return jsonify({
            'error': 'Invalid state parameter',
            'debug': {
                'request_state': state_from_request,
                'state_found_in_memory': state_from_request in _oauth_states if state_from_request else False
            }
        }), 400

    # Build same dynamic redirect URI as in login route
    host_url = request.host_url.rstrip('/')
    dynamic_redirect_uri = f"{host_url}/auth/callback"

    logger.info(f"Callback: Using dynamic redirect URI: {dynamic_redirect_uri}")

    flow = create_oauth_flow(redirect_uri=dynamic_redirect_uri)
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # Get user info
    oauth2_service = build('oauth2', 'v2', credentials=credentials)
    user_info = oauth2_service.userinfo().get().execute()

    session['user_email'] = user_info['email']
    session['user_name'] = user_info.get('name', '')
    session['user_picture'] = user_info.get('picture', '')

    # Ensure user exists in database and sync their data
    db = FirestoreService()
    employee = db.get_employee(user_info['email'])

    if employee:
        # Auto-sync: Update employee data from the OAuth user info on every login
        # This keeps names, photos, etc. in sync with Google Workspace
        needs_update = False
        
        if user_info.get('name') and employee.full_name != user_info.get('name'):
            employee.full_name = user_info.get('name', employee.full_name)
            needs_update = True
        
        if user_info.get('given_name') and employee.given_name != user_info.get('given_name'):
            employee.given_name = user_info.get('given_name', employee.given_name)
            needs_update = True
            
        if user_info.get('family_name') and employee.family_name != user_info.get('family_name'):
            employee.family_name = user_info.get('family_name', employee.family_name)
            needs_update = True
            
        if user_info.get('picture') and employee.photo_url != user_info.get('picture'):
            employee.photo_url = user_info.get('picture', employee.photo_url)
            needs_update = True
        
        if needs_update:
            from datetime import datetime
            employee.last_workspace_sync = datetime.utcnow()
            db.update_employee(employee)
    else:
        # If user doesn't exist, redirect to setup (admin should have synced)
        return redirect(url_for('auth.profile_setup'))

    return redirect('/dashboard')  # Frontend route


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')


@auth_bp.route('/profile-setup')
def profile_setup():
    """Handle first-time user setup"""
    # In production, this would redirect to a setup page
    # For now, return a message
    return jsonify({
        'message': 'Please contact your administrator to set up your profile',
        'email': session.get('user_email')
    })


@auth_bp.route('/status')
def status():
    """Check authentication status"""
    if 'credentials' not in session:
        return jsonify({'authenticated': False}), 200

    return jsonify({
        'authenticated': True,
        'user': {
            'email': session.get('user_email'),
            'name': session.get('user_name'),
            'picture': session.get('user_picture'),
        }
    }), 200
