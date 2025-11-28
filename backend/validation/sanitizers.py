"""Input sanitization utilities for Good Shepherd API."""

import html
import re
from typing import Any, Optional
from urllib.parse import urlparse

# Regex patterns for validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
SAFE_STRING_PATTERN = re.compile(r"^[\w\s\-.,!?@#$%&*()+=:;\"'<>/\[\]{}|\\~`]+$", re.UNICODE)

# Dangerous patterns to strip
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
    r"(--|;|/\*|\*/)",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
]


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string input by escaping HTML and limiting length.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Truncate to max length
    value = value[:max_length]
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    # Escape HTML entities
    value = html.escape(value)
    
    return value


def sanitize_html(value: str, max_length: int = 10000) -> str:
    """
    Sanitize HTML content by removing dangerous tags and attributes.
    
    Args:
        value: HTML string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized HTML string
    """
    if not value:
        return ""
    
    # Truncate
    value = value[:max_length]
    
    # Remove script tags and content
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous tags
    for tag in ["iframe", "object", "embed", "form", "input", "button"]:
        value = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(rf"<{tag}[^>]*>", "", value, flags=re.IGNORECASE)
    
    # Remove event handlers
    value = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+on\w+\s*=\s*\S+", "", value, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)
    
    return value


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    if not email or len(email) > 256:
        return False
    return bool(EMAIL_PATTERN.match(email))


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if valid UUID format
    """
    if not uuid_str:
        return False
    return bool(UUID_PATTERN.match(uuid_str))


def validate_url(url: str, allowed_schemes: Optional[list[str]] = None) -> bool:
    """
    Validate URL format and scheme.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: http, https)
        
    Returns:
        True if valid URL
    """
    if not url or len(url) > 2048:
        return False
    
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]
    
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in allowed_schemes
            and bool(parsed.netloc)
            and not any(c in url for c in ["<", ">", '"', "'", "{", "}"])
        )
    except Exception:
        return False


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """
    Sanitize a search query by removing potentially dangerous characters.
    
    Args:
        query: Search query to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized search query
    """
    if not query:
        return ""
    
    # Truncate
    query = query[:max_length]
    
    # Remove SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)
    
    # Remove special SQL characters
    query = re.sub(r"[;'\"\-\-]", "", query)
    
    # Strip whitespace
    query = query.strip()
    
    return query


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing path traversal and dangerous characters.
    
    Args:
        filename: Filename to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove path components
    filename = filename.replace("\\", "/")
    filename = filename.split("/")[-1]
    
    # Remove null bytes and other dangerous characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    
    # Remove path traversal attempts
    filename = filename.replace("..", "")
    
    # Keep only safe characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    
    # Truncate
    filename = filename[:max_length]
    
    return filename


def sanitize_json_value(value: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
    """
    Recursively sanitize JSON values.
    
    Args:
        value: JSON value to sanitize
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        
    Returns:
        Sanitized JSON value
    """
    if current_depth > max_depth:
        return None
    
    if isinstance(value, str):
        return sanitize_string(value)
    elif isinstance(value, dict):
        return {
            sanitize_string(str(k), max_length=100): sanitize_json_value(v, max_depth, current_depth + 1)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [sanitize_json_value(item, max_depth, current_depth + 1) for item in value[:1000]]
    elif isinstance(value, (int, float, bool, type(None))):
        return value
    else:
        return str(value)[:1000]


def check_for_injection(value: str) -> bool:
    """
    Check if a string contains potential injection patterns.
    
    Args:
        value: String to check
        
    Returns:
        True if potential injection detected
    """
    if not value:
        return False
    
    # Check SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    # Check XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False
