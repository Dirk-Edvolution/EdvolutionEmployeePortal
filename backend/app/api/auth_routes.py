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

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Initiate OAuth flow"""
    import logging
    logger = logging.getLogger(__name__)

    flow = create_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )

    session['state'] = state
    session.modified = True  # Explicitly mark session as modified

    logger.info(f"Login: Set state in session: {state}")
    logger.info(f"Login: Session keys after setting state: {list(session.keys())}")

    return redirect(authorization_url)


@auth_bp.route('/callback')
def callback():
    """OAuth callback handler"""
    import logging
    logger = logging.getLogger(__name__)

    state_from_session = session.get('state')
    state_from_request = request.args.get('state')

    logger.info(f"Session state: {state_from_session}, Request state: {state_from_request}")
    logger.info(f"Session keys: {list(session.keys())}")
    logger.info(f"Request URL: {request.url}")

    if not state_from_session or state_from_session != state_from_request:
        return jsonify({
            'error': 'Invalid state parameter',
            'debug': {
                'session_state': state_from_session,
                'request_state': state_from_request,
                'session_has_state': 'state' in session
            }
        }), 400

    flow = create_oauth_flow()
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
