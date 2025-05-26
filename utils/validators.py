import re
from bleach import clean


def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks."""
    if not isinstance(text, str):
        return text
    return clean(text, strip=True)


def validate_username(username):
    """Validate username format."""
    if not username or len(username) < 3 or len(username) > 30:
        return False
    # Only allow letters, numbers, and underscores
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))


def validate_password(password):
    """Validate password strength."""
    if not password or len(password) < 8:
        return False
    # Require at least one uppercase, one lowercase, one number
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit


def validate_email(email):
    """Validate email format."""
    if not email:
        return False
    # Basic email format validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any directory components
    filename = re.sub(r'[/\\]', '', filename)
    # Only allow certain characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename
