"""Security middleware for FastAPI applications."""

from __future__ import annotations

import html
import re
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import SecurityConfig

# Injection detection patterns
SQL_INJECTION_PATTERNS = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",  # Single quotes, comments
    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",  # Equals followed by quote/comment
    r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",  # 'OR' patterns
    r"((\%27)|(\'))\s*((\%6F)|o|(\%4F))((\%72)|r|(\%52))",  # ' OR' with space
    r"((\%27)|(\'))\s*\d*\s*((\%3D)|(=))\s*\d*",  # ' = number patterns
    r"((\%27)|(\'))\s*\d*\s*((\%3D)|(=))\s*((\%27)|(\'))",  # ' = ' patterns
    r"((\%27)|(\'))\s*((\%6F)|o|(\%4F))((\%72)|r|(\%52))\s*\d*\s*((\%3D)|(=))\s*\d*",  # 'OR 1=1'
    r"(DROP\s+TABLE)|(DELETE\s+FROM)|(INSERT\s+INTO)|(UPDATE\s+.*\s+SET)",  # SQL commands
    r"(UNION\s+SELECT)|(SELECT\s+.*\s+FROM)",  # SELECT patterns
    r"(OR\s+\d+=\d+)",  # OR 1=1 pattern
]

XSS_PATTERNS = [
    r"<script[^>]*>[\s\S]*?</script>",  # Script tags
    r"javascript:\s*",  # javascript: protocol
    r"on\w+\s*=\s*['\"]",  # Event handlers (onclick, onload, etc.)
    r"<iframe[^>]*>[\s\S]*?</iframe>",  # Iframe tags
    r"<object[^>]*>[\s\S]*?</object>",  # Object tags
    r"<embed[^>]*>",  # Embed tags
    r"<form[^>]*>[\s\S]*?</form>",  # Form tags (for phishing)
    r"(alert|confirm|prompt)\s*\(",  # JavaScript dialogs
    r"document\.(cookie|location|write)",  # Document access
    r"window\.(location|open)",  # Window redirects
]


class SecurityValidator:
    """Security validation utilities for input sanitization and threat detection."""

    @staticmethod
    def detect_injection(value: Any, patterns: list[str]) -> bool:
        """Detect if value matches any injection patterns.
        
        Args:
            value: Value to check (typically string)
            patterns: List of regex patterns to match against
            
        Returns:
            True if injection pattern detected, False otherwise
        """
        if not isinstance(value, str) or not patterns:
            return False
        
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def sanitize_string(value: Any) -> str:
        """Sanitize string input by escaping HTML and removing null bytes.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Escape HTML entities
        value = html.escape(value)
        
        # Normalize whitespace (consecutive whitespace -> single space)
        value = re.sub(r'\s+', ' ', value)
        
        return value.strip()

    @staticmethod
    def validate_json_structure(data: Any, max_depth: int = 10, max_keys: int = 1000) -> bool:
        """Validate JSON structure for security concerns.
        
        Args:
            data: Parsed JSON data
            max_depth: Maximum allowed nesting depth
            max_keys: Maximum allowed keys at any level
            
        Returns:
            True if structure is valid, False if suspicious
        """
        def check_depth(obj: Any, current_depth: int) -> bool:
            if current_depth > max_depth:
                return False
            
            if isinstance(obj, dict):
                if len(obj) > max_keys:
                    return False
                for v in obj.values():
                    if not check_depth(v, current_depth + 1):
                        return False
            elif isinstance(obj, list):
                if len(obj) > max_keys:
                    return False
                for item in obj:
                    if not check_depth(item, current_depth + 1):
                        return False
            
            return True
        
        return check_depth(data, 1)

    @staticmethod
    def validate_field_name(name: str) -> bool:
        """Validate that a field name is safe (no injection characters).
        
        Args:
            name: Field name to validate
            
        Returns:
            True if field name is valid, False otherwise
        """
        if not isinstance(name, str):
            return False
        
        # Allow alphanumeric, underscores, hyphens
        # Reject names with special chars that could be used for injection
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return False
        
        # Additional checks for suspicious patterns
        suspicious = ['__', 'constructor', 'prototype', 'eval', 'function']
        return not any(s in name.lower() for s in suspicious)


def add_security_middleware(
    app: FastAPI,
    config: SecurityConfig | None = None,
) -> None:
    """Add security middleware to FastAPI app.

    Args:
        app: FastAPI application
        config: Security configuration
    """
    config = config or SecurityConfig()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=config.cors_methods,
        allow_headers=config.cors_headers,
        allow_credentials=True,
        max_age=600,
    )

    # Add trusted host middleware (if not allowing all)
    if "*" not in config.cors_origins:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.cors_origins,
        )

    # Add security headers middleware
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)

        if config.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if config.enable_xframe:
            response.headers["X-Frame-Options"] = "DENY"

        if config.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        if config.enable_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if config.enable_referrer_policy:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if config.content_security_policy:
            response.headers["Content-Security-Policy"] = config.content_security_policy

        return response
