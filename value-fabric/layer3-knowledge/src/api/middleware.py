"""Security middleware for input validation and sanitization."""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging_config import get_logger

logger = get_logger(__name__)

# Security patterns for injection detection
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(\b(OR|AND)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
    r"(--|#|\/\*|\*\/)",
    r"(\b(LOAD_FILE|INTO\s+OUTFILE|DUMPFILE)\b)",
    r"(\b(WAITFOR\s+DELAY|BENCHMARK|SLEEP)\b)",
]

XSS_PATTERNS = [
    r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
    r"javascript\s*:",
    r"on\w+\s*=",
    r"<\s*iframe[^>]*>",
    r"<\s*object[^>]*>",
    r"<\s*embed[^>]*>",
    r"<\s*link[^>]*>",
    r"<\s*meta[^>]*>",
]

NOSQL_INJECTION_PATTERNS = [
    r"(\$where|\$ne|\$gt|\$lt|\$in|\$nin)",
    r"(\{.*\$.*\})",
    r"(true\s*\|\s*false)",
    r"(\.\s*\.)",
]

COMMAND_INJECTION_PATTERNS = [
    # Command separators and redirections (require surrounding context)
    r"(;\s*\||\|\s*|\|\||&&|\$\(|\`\s*\w+|\|\s*\w+)",
    # Common command-line tools used in attacks
    r"\b(curl|wget|nc|netcat|ssh|ftp|telnet)\b",
    # Dangerous file operations
    r"\b(rm\s+-rf|mv\s+.*\s+/dev/null|dd\s+if=)\b",
    # Scripting language invocations
    r"\b(python|perl|ruby|php)\s+(-c|-e|--eval)",
]


class SecurityValidator:
    """Security validation utilities for input sanitization."""
    
    @staticmethod
    def detect_injection(value: str, patterns: List[str]) -> bool:
        """Detect if value matches any injection patterns."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        for pattern in patterns:
            if re.search(pattern, value_lower, re.IGNORECASE | re.MULTILINE):
                return True
        return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent XSS."""
        if not isinstance(value, str):
            return value
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize whitespace
        value = ' '.join(value.split())
        
        return value
    
    @staticmethod
    def validate_json_structure(data: Any, max_depth: int = 10) -> bool:
        """Validate JSON structure to prevent deep recursion attacks."""
        if max_depth <= 0:
            return False
        
        if isinstance(data, dict):
            if len(data) > 1000:  # Prevent large object attacks
                return False
            return all(SecurityValidator.validate_json_structure(v, max_depth - 1) for v in data.values())
        elif isinstance(data, list):
            if len(data) > 1000:  # Prevent large array attacks
                return False
            return all(SecurityValidator.validate_json_structure(item, max_depth - 1) for item in data)
        else:
            return True
    
    @staticmethod
    def validate_field_name(name: str) -> bool:
        """Validate field names to prevent injection."""
        if not isinstance(name, str):
            return False
        
        # Only allow alphanumeric, underscore, and dash
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
    
    @staticmethod
    def sanitize_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters."""
        sanitized = {}
        for key, value in params.items():
            if SecurityValidator.validate_field_name(key):
                if isinstance(value, str):
                    sanitized[key] = SecurityValidator.sanitize_string(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        SecurityValidator.sanitize_string(item) if isinstance(item, str) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
        return sanitized


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for input validation and sanitization."""

    # Paths that skip security validation (RDF/Turtle data triggers false positives)
    # Also skip graph query endpoints that accept natural language queries
    SKIP_VALIDATION_PATHS = frozenset({
        "/v1/ingest", "/v1/sync", "/v1/batch/ingest",
        "/v1/query/graph", "/v1/query", "/v1/graph/query", "/query/graph", "/graph/query",
    })

    def __init__(self, app, strict_mode: bool = True):
        """Initialize security middleware.

        Args:
            app: FastAPI application
            strict_mode: If True, blocks requests on security violations
        """
        super().__init__(app)
        self.strict_mode = strict_mode
        # Pre-compute normalized paths for efficient lookup
        self._normalized_skip_paths = frozenset(
            p.rstrip('/').lower() for p in self.SKIP_VALIDATION_PATHS
        )

    def _should_skip_validation(self, path: str) -> bool:
        """Check if path should skip security validation.

        Handles trailing slashes and case-insensitive matching for robustness.

        Args:
            path: Request path to check

        Returns:
            True if path should skip validation
        """
        # Normalize path: remove trailing slash, lowercase
        normalized = path.rstrip('/').lower()
        return normalized in self._normalized_skip_paths

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through security validation."""
        # Skip validation for RDF ingestion endpoints and graph query endpoints
        if self._should_skip_validation(request.url.path):
            logger.debug(f"Skipping validation for {request.url.path}")
            return await call_next(request)

        violations = []

        # Validate query parameters
        query_params = dict(request.query_params)
        sanitized_query = SecurityValidator.sanitize_query_params(query_params)
        
        for key, value in query_params.items():
            if isinstance(value, str):
                if SecurityValidator.detect_injection(value, SQL_INJECTION_PATTERNS):
                    violations.append(f"SQL injection detected in query parameter '{key}'")
                if SecurityValidator.detect_injection(value, XSS_PATTERNS):
                    violations.append(f"XSS detected in query parameter '{key}'")
                if SecurityValidator.detect_injection(value, COMMAND_INJECTION_PATTERNS):
                    violations.append(f"Command injection detected in query parameter '{key}'")
        
        # Validate request body for JSON requests
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.body()
                if body:
                    json_data = json.loads(body.decode('utf-8'))
                    
                    # Validate JSON structure
                    if not SecurityValidator.validate_json_structure(json_data):
                        violations.append("Invalid JSON structure - possible recursion attack")
                    
                    # Scan JSON values for injection patterns
                    self._validate_json_data(json_data, violations)
                    
            except json.JSONDecodeError:
                # Invalid JSON will be handled by FastAPI
                pass
            except Exception as e:
                logger.warning(f"Error validating request body: {e}")
        
        # Log violations and handle response
        if violations:
            logger.warning(
                "Security violations detected",
                extra={
                    "violations": violations,
                    "path": request.url.path,
                    "method": request.method,
                    "client_host": request.client.host if request.client else None,
                }
            )
            
            if self.strict_mode:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Security validation failed",
                        "violations": violations
                    }
                )
        
        # Update request with sanitized query params
        request._query_params = sanitized_query
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    def _validate_json_data(self, data: Any, violations: List[str], path: str = "") -> None:
        """Recursively validate JSON data for injection patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if not SecurityValidator.validate_field_name(key):
                    violations.append(f"Invalid field name: {current_path}")
                
                if isinstance(value, str):
                    self._check_string_injections(value, current_path, violations)
                elif isinstance(value, (dict, list)):
                    self._validate_json_data(value, violations, current_path)
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                
                if isinstance(item, str):
                    self._check_string_injections(item, current_path, violations)
                elif isinstance(item, (dict, list)):
                    self._validate_json_data(item, violations, current_path)
    
    @staticmethod
    def _is_rdf_data(value: str) -> bool:
        """Check if string looks like RDF/Turtle data (not injection)."""
        # Look for RDF/Turtle-specific patterns that indicate legitimate data
        rdf_indicators = [
            "@prefix",  # Turtle prefix declaration
            "@base",  # Turtle base declaration
            "rdf:type",  # RDF type predicate
            "http://",  # HTTP URLs in RDF
            "https://",  # HTTPS URLs in RDF
        ]
        # Check for multiple RDF indicators to reduce false positives
        indicator_count = sum(1 for ind in rdf_indicators if ind in value)
        # Also check for Turtle-specific URI syntax <...>
        has_uri_syntax = "<http" in value and ">" in value
        return indicator_count >= 2 or (indicator_count >= 1 and has_uri_syntax)

    def _check_string_injections(self, value: str, path: str, violations: List[str]) -> None:
        """Check string value for various injection patterns."""
        # Skip injection checks for legitimate RDF/Turtle data which contains
        # URLs with special characters like < > : that trigger false positives
        if self._is_rdf_data(value):
            return

        # Skip short common text patterns that trigger false positives
        if len(value) < 50 and " " in value and not any(c in value for c in "<>;|&`$()[]"):
            return

        if SecurityValidator.detect_injection(value, SQL_INJECTION_PATTERNS):
            violations.append(f"SQL injection detected in field '{path}'")
        
        if SecurityValidator.detect_injection(value, XSS_PATTERNS):
            violations.append(f"XSS detected in field '{path}'")
        
        if SecurityValidator.detect_injection(value, NOSQL_INJECTION_PATTERNS):
            violations.append(f"NoSQL injection detected in field '{path}'")
        
        if SecurityValidator.detect_injection(value, COMMAND_INJECTION_PATTERNS):
            violations.append(f"Command injection detected in field '{path}'")


def add_security_middleware(app, strict_mode: bool = True) -> None:
    """Add security middleware to FastAPI application.
    
    Args:
        app: FastAPI application
        strict_mode: If True, blocks requests on security violations
    """
    app.add_middleware(SecurityMiddleware, strict_mode=strict_mode)
