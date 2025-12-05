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

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Initiate OAuth flow"""
    flow = create_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )

    session['state'] = state
    return redirect(authorization_url)


@auth_bp.route('/callback')
def callback():
    """OAuth callback handler"""
    state = session.get('state')

    flow = create_oauth_flow()
    flow.fetch_token(authorization_response=request.url)

    if not state or state != request.args.get('state'):
        return jsonify({'error': 'Invalid state parameter'}), 400

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # Get user info
    oauth2_service = build('oauth2', 'v2', credentials=credentials)
    user_info = oauth2_service.userinfo().get().execute()

    session['user_email'] = user_info['email']
    session['user_name'] = user_info.get('name', '')
    session['user_picture'] = user_info.get('picture', '')

    # Ensure user exists in database
    db = FirestoreService()
    employee = db.get_employee(user_info['email'])

    if not employee:
        # If user doesn't exist, trigger a sync (admin should have synced, but just in case)
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
