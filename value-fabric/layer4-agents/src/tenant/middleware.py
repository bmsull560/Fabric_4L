"""FastAPI middleware for tenant extraction.

Extracts tenant context from request headers or JWT tokens.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from .context import TenantContext, set_current_tenant


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant context from requests.
    
    Extracts tenant information from:
    - X-Tenant-ID header
    - JWT token claims (tenant_id, user_id)
    - Query parameters (for WebSocket support)
    
    Example:
        app.add_middleware(TenantMiddleware)
    """
    
    def __init__(
        self,
        app,
        header_name: str = "X-Tenant-ID",
        jwt_tenant_claim: str = "tenant_id",
        jwt_user_claim: str = "user_id",
    ):
        """Initialize middleware.
        
        Args:
            app: FastAPI application
            header_name: Header containing tenant ID
            jwt_tenant_claim: JWT claim for tenant
            jwt_user_claim: JWT claim for user
        """
        super().__init__(app)
        self.header_name = header_name
        self.jwt_tenant_claim = jwt_tenant_claim
        self.jwt_user_claim = jwt_user_claim
    
    async def dispatch(self, request: Request, call_next):
        """Process request with tenant context.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Extract tenant from request
        tenant = self._extract_tenant(request)
        
        # Set context
        set_current_tenant(tenant)
        
        # Add tenant to request state
        request.state.tenant = tenant
        
        # Process request
        response = await call_next(request)
        
        # Add tenant headers to response (for debugging)
        if tenant:
            response.headers["X-Tenant-ID-Resolved"] = tenant.tenant_id
        
        return response
    
    def _extract_tenant(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Tenant context or None
        """
        tenant_id: Optional[str] = None
        user_id: Optional[str] = None
        
        # Try header first
        tenant_id = request.headers.get(self.header_name)
        
        # Try JWT token if no header
        if not tenant_id:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                tenant_id, user_id = self._parse_jwt(token)
        
        # Try query parameter (for WebSocket support)
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")
        
        if not tenant_id:
            return None
        
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
        )
    
    def _parse_jwt(self, token: str) -> tuple:
        """Parse JWT token for tenant and user claims.
        
        Args:
            token: JWT token string
            
        Returns:
            (tenant_id, user_id) tuple
        """
        try:
            import jwt
            
            # Decode without verification (claims extraction only)
            # In production, verify signature
            payload = jwt.decode(token, options={"verify_signature": False})
            
            tenant_id = payload.get(self.jwt_tenant_claim)
            user_id = payload.get(self.jwt_user_claim)
            
            return tenant_id, user_id
        except Exception:
            return None, None
