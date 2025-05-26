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
        rv["code"] = self.status_code
        rv["message"] = self.message
        rv["status"] = HTTP_STATUS_CODES.get(self.status_code, "Unknown Error")
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


def create_api_error_response(status_code, message):
    """Create a JSON response for API errors."""
    return (
        jsonify(
            {
                "code": status_code,
                "message": message,
                "status": HTTP_STATUS_CODES.get(status_code, "Unknown Error"),
            }
        ),
        status_code,
    )


def handle_not_found(request_path):
    """Handle 404 errors."""
    if request_path.startswith("/api/"):
        return create_api_error_response(404, "Resource not found")
    return render_template("errors/404.html"), 404


def handle_internal_error(request_path):
    """Handle 500 errors."""
    db.session.rollback()  # Roll back db session in case of error
    if request_path.startswith("/api/"):
        return create_api_error_response(500, "Internal server error")
    return render_template("errors/500.html"), 500


def handle_unauthorized(error, request_path):
    """Handle 401 errors."""
    error_message = str(error)
    # For missing cookie, just redirect silently
    if 'Missing cookie "access_token_cookie"' in error_message:
        return redirect(url_for("auth.login"))

    # For other unauthorized errors
    if request_path.startswith("/api/"):
        return create_api_error_response(401, "Authentication required")
    return redirect(url_for("auth.login"))


def handle_forbidden(request_path):
    """Handle 403 errors."""
    if request_path.startswith("/api/"):
        return create_api_error_response(403, "Permission denied")
    return render_template("errors/403.html"), 403


def init_error_handlers(app):
    """Initialize error handlers for the application"""

    @app.errorhandler(APIError)
    def handle_api_error_wrapper(error):
        return handle_api_error(error)

    @app.errorhandler(404)
    def not_found_error(error):
        return handle_not_found(request.path)

    @app.errorhandler(500)
    def internal_error(error):
        return handle_internal_error(request.path)

    @app.errorhandler(401)
    def unauthorized_error(error):
        return handle_unauthorized(error, request.path)

    @app.errorhandler(403)
    def forbidden_error(error):
        return handle_forbidden(request.path)
