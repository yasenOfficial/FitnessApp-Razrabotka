from flask import jsonify, request, render_template, redirect, url_for
from werkzeug.http import HTTP_STATUS_CODES
from extensions import db

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['code'] = self.status_code
        rv['message'] = self.message
        rv['status'] = HTTP_STATUS_CODES.get(self.status_code, 'Unknown Error')
        return rv

class ResourceNotFoundError(APIError):
    """Exception for resource not found errors"""
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message=message, status_code=404, payload=payload)

class AuthenticationError(APIError):
    """Exception for authentication errors"""
    def __init__(self, message="Authentication required", payload=None):
        super().__init__(message=message, status_code=401, payload=payload)

class AuthorizationError(APIError):
    """Exception for authorization errors"""
    def __init__(self, message="Permission denied", payload=None):
        super().__init__(message=message, status_code=403, payload=payload)

class ValidationError(APIError):
    """Exception for validation errors"""
    def __init__(self, message="Validation error", payload=None):
        super().__init__(message=message, status_code=400, payload=payload)

def handle_api_error(error):
    """Handler for API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def init_error_handlers(app):
    """Initialize error handlers for the application"""
    
    @app.errorhandler(APIError)
    def handle_api_error_wrapper(error):
        return handle_api_error(error)

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'code': 404,
                'message': 'Resource not found',
                'status': 'Not Found'
            }), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Roll back db session in case of error
        if request.path.startswith('/api/'):
            return jsonify({
                'code': 500,
                'message': 'Internal server error',
                'status': 'Internal Server Error'
            }), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(401)
    def unauthorized_error(error):
        error_message = str(error)
        if 'Missing cookie "access_token_cookie"' in error_message:
            if request.path.startswith('/api/'):
                return jsonify({
                    'code': 401,
                    'message': 'Your session has expired. Please log in again.',
                    'status': 'Unauthorized',
                    'redirect': url_for('auth.login')
                }), 401
            return redirect(url_for('auth.login'))

        if request.path.startswith('/api/'):
            return jsonify({
                'code': 401,
                'message': 'Authentication required',
                'status': 'Unauthorized',
                'redirect': url_for('auth.login')
            }), 401
        return redirect(url_for('auth.login'))

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'code': 403,
                'message': 'Permission denied',
                'status': 'Forbidden'
            }), 403
        return render_template('errors/403.html'), 403 