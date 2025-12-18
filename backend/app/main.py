"""
Main Flask application for Employee Portal
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from backend.config.settings import FLASK_SECRET_KEY, FLASK_ENV
from backend.app.api import auth_bp, employee_bp, timeoff_bp, audit_bp, chat_bp
import os


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder='../../frontend/dist')

    # Configure proxy fix for Cloud Run load balancer
    # This makes Flask correctly detect HTTPS when behind a reverse proxy
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_proto=1,  # Trust X-Forwarded-Proto header for scheme (http/https)
        x_host=1    # Trust X-Forwarded-Host header for hostname
    )

    # Configuration
    app.secret_key = FLASK_SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = True  # Always use secure cookies
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Use Lax instead of None for better compatibility
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_NAME'] = 'session'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime

    # Make sessions permanent so they're actually saved
    from flask import session as flask_session
    @app.before_request
    def make_session_permanent():
        flask_session.permanent = True

    # Enable CORS
    CORS(app, supports_credentials=True, origins=[
        'http://localhost:3000',
        'http://localhost:8080',
        'https://*.run.app',
        'https://employee-portal-5n2ivebvra-uc.a.run.app',
        'https://rrhh.edvolution.io'
    ])

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(timeoff_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(chat_bp)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200

    # Root endpoint - serve frontend entry point
    @app.route('/')
    def index():
        return serve_frontend('index.html')

    # Serve frontend static files (for production)
    @app.route('/<path:path>')
    def serve_frontend(path):
        # API and Auth routes should be handled by blueprints, but just in case:
        if path.startswith('api/') or path.startswith('auth/'):
            return jsonify({'error': 'Not found'}), 404

        frontend_dir = os.path.join(app.static_folder)
        if os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        else:
            # SPA Fallback for non-API routes
            return send_from_directory(frontend_dir, 'index.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
