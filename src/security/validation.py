"""
Input Validation and Security Hardening for Claude-AGI
=======================================================

Implements comprehensive input validation:
- SQL injection prevention
- XSS protection
- Command injection prevention
- Path traversal protection
- JSON schema validation
"""

import re
import html
from typing import Any, Dict, List, Optional, Annotated
from pydantic import BaseModel, field_validator, Field, StringConstraints
from fastapi import HTTPException

import logging

logger = logging.getLogger(__name__)


# Security Validators

# Use Annotated with StringConstraints for Pydantic v2
SecureString = Annotated[str, StringConstraints(min_length=1, max_length=1000, strip_whitespace=True)]
SecureText = Annotated[str, StringConstraints(min_length=1, max_length=10000, strip_whitespace=True)]


# SQL Injection Detection

SQL_INJECTION_PATTERNS = [
    r"(\bOR\b.*=.*)",
    r"(\bAND\b.*=.*)",
    r"(;.*DROP\b)",
    r"(;.*DELETE\b)",
    r"(;.*UPDATE\b)",
    r"(;.*INSERT\b)",
    r"(UNION.*SELECT)",
    r"(\/\*.*\*\/)",  # SQL comments
    r"(--.*)",  # SQL comments
    r"(xp_.*)",  # SQL Server extended procedures
    r"(sp_.*)",  # SQL Server stored procedures
]

def check_sql_injection(text: str) -> bool:
    """
    Check if text contains potential SQL injection

    Returns:
        True if suspicious pattern found
    """
    if not text:
        return False

    text_upper = text.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_upper, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {pattern}")
            return True

    return False


# XSS Detection

XSS_PATTERNS = [
    r"<script[^>]*>",
    r"</script>",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

def check_xss(text: str) -> bool:
    """
    Check if text contains potential XSS

    Returns:
        True if suspicious pattern found
    """
    if not text:
        return False

    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potential XSS detected: {pattern}")
            return True

    return False


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML by escaping special characters

    Returns:
        Escaped text safe for HTML display
    """
    return html.escape(text)


# Command Injection Detection

COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$]",  # Shell metacharacters
    r"\$\(",  # Command substitution
    r"\.\./",  # Path traversal
]

def check_command_injection(text: str) -> bool:
    """
    Check if text contains potential command injection

    Returns:
        True if suspicious pattern found
    """
    if not text:
        return False

    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, text):
            logger.warning(f"Potential command injection detected: {pattern}")
            return True

    return False


# Path Traversal Detection

def check_path_traversal(path: str) -> bool:
    """
    Check if path contains traversal attempts

    Returns:
        True if suspicious pattern found
    """
    if not path:
        return False

    suspicious_patterns = ["../", "..\\", "%2e%2e", "..%2f", "..%5c"]

    for pattern in suspicious_patterns:
        if pattern in path.lower():
            logger.warning(f"Potential path traversal detected: {pattern}")
            return True

    return False


# Comprehensive Validation

def validate_input(
    text: str,
    check_sql: bool = True,
    check_xss_injection: bool = True,
    check_cmd: bool = True,
    max_length: int = 10000
) -> str:
    """
    Comprehensive input validation

    Args:
        text: Input text to validate
        check_sql: Check for SQL injection
        check_xss_injection: Check for XSS
        check_cmd: Check for command injection
        max_length: Maximum allowed length

    Returns:
        Validated text

    Raises:
        HTTPException if validation fails
    """
    if not text:
        return text

    # Length check
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Input too long (max: {max_length} characters)"
        )

    # SQL injection check
    if check_sql and check_sql_injection(text):
        raise HTTPException(
            status_code=400,
            detail="Invalid input: potential SQL injection detected"
        )

    # XSS check
    if check_xss_injection and check_xss(text):
        raise HTTPException(
            status_code=400,
            detail="Invalid input: potential XSS detected"
        )

    # Command injection check
    if check_cmd and check_command_injection(text):
        raise HTTPException(
            status_code=400,
            detail="Invalid input: potential command injection detected"
        )

    return text


# Secure Request Models

class SecureThoughtRequest(BaseModel):
    """Secure thought generation request"""
    stream_type: str = Field(..., pattern="^(PRIMARY|SUBCONSCIOUS|EMOTIONAL|CREATIVE|META)$")
    context: Dict[str, Any] = Field(default_factory=dict)
    emotional_state: Optional[str] = Field(None, pattern="^(NEUTRAL|CURIOUS|CONTEMPLATIVE|EXCITED|CONCERNED|FRUSTRATED|SATISFIED)$")

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        """Validate context dict"""
        if not isinstance(v, dict):
            raise ValueError("Context must be a dictionary")

        # Check each value
        for key, value in v.items():
            if isinstance(value, str):
                # Validate string values
                validate_input(value, max_length=1000)

        return v


class SecureMemoryQuery(BaseModel):
    """Secure memory query request"""
    query: SecureString = Field(..., min_length=1, max_length=500)
    memory_type: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate query string"""
        return validate_input(v, max_length=500)

    @field_validator("memory_type")
    @classmethod
    def validate_memory_type(cls, v):
        """Validate memory type"""
        if v and v not in ["WORKING", "EPISODIC", "SEMANTIC"]:
            raise ValueError("Invalid memory type")
        return v


class SecureConversationRequest(BaseModel):
    """Secure conversation request"""
    message: SecureText = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = Field(None, pattern="^[a-zA-Z0-9_-]{1,50}$")
    emotional_context: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        """Validate message"""
        return validate_input(v, max_length=5000)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        """Validate conversation ID format"""
        if v and not re.match(r"^[a-zA-Z0-9_-]{1,50}$", v):
            raise ValueError("Invalid conversation ID format")
        return v


# Content Security Policy

CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],  # Adjust based on needs
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}

def get_csp_header() -> str:
    """
    Generate Content Security Policy header

    Returns:
        CSP header string
    """
    policies = []
    for directive, sources in CSP_POLICY.items():
        policy = f"{directive} {' '.join(sources)}"
        policies.append(policy)

    return "; ".join(policies)


# Security Headers

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": get_csp_header(),
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def get_security_headers() -> Dict[str, str]:
    """
    Get all security headers

    Returns:
        Dictionary of security headers
    """
    return SECURITY_HEADERS.copy()


# Input Sanitization

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.replace("../", "").replace("..\\", "")

    # Allow only alphanumeric, dash, underscore, and dot
    filename = re.sub(r"[^\w\-.]", "_", filename)

    # Remove leading dots
    filename = filename.lstrip(".")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values

    Args:
        data: Dictionary to sanitize
        max_depth: Maximum recursion depth

    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return {}

    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        if not isinstance(key, str):
            key = str(key)
        key = validate_input(key, max_length=100)

        # Sanitize value
        if isinstance(value, str):
            value = validate_input(value, max_length=10000)
        elif isinstance(value, dict):
            value = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            value = [
                sanitize_dict(item, max_depth - 1) if isinstance(item, dict)
                else validate_input(str(item), max_length=1000) if isinstance(item, str)
                else item
                for item in value[:100]  # Limit list length
            ]

        sanitized[key] = value

    return sanitized
