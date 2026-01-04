from .auth_routes import auth_bp
from .employee_routes import employee_bp
from .timeoff_routes import timeoff_bp
from .audit_routes import audit_bp
from .chat_routes import chat_bp
from .travel_routes import travel_bp
from .tool_routes import tool_bp
from .asset_routes import asset_bp

__all__ = ['auth_bp', 'employee_bp', 'timeoff_bp', 'audit_bp', 'chat_bp', 'travel_bp', 'tool_bp', 'asset_bp']
