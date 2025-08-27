"""
Authentication Middleware for Claude-AGI
========================================

Provides WSGI/ASGI middleware for authentication and security:
- Request authentication
- CORS handling
- Security headers
- Rate limiting
- Request logging
- Error handling
"""

import time
import logging
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlparse
from flask import Flask, request, g, jsonify
from werkzeug.exceptions import TooManyRequests

from .jwt_manager import JWTManager
from .rbac import RBACManager
from .user_manager import UserManager
from .decorators import extract_token

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Authentication middleware for Flask applications
    
    Provides centralized authentication, CORS, security headers,
    and request logging functionality.
    """
    
    def __init__(self, app: Flask, 
                 jwt_manager: JWTManager,
                 rbac_manager: RBACManager,
                 user_manager: UserManager,
                 cors_origins: Optional[List[str]] = None,
                 security_headers: bool = True,
                 rate_limiting: bool = True):
        """
        Initialize authentication middleware
        
        Args:
            app: Flask application
            jwt_manager: JWT token manager
            rbac_manager: RBAC manager
            user_manager: User manager
            cors_origins: Allowed CORS origins
            security_headers: Enable security headers
            rate_limiting: Enable basic rate limiting
        """
        self.app = app
        self.jwt_manager = jwt_manager
        self.rbac_manager = rbac_manager
        self.user_manager = user_manager
        self.cors_origins = cors_origins or ['http://localhost:3000']
        self.security_headers = security_headers
        self.rate_limiting = rate_limiting
        
        # Rate limiting storage (use Redis in production)
        self.rate_limit_storage: Dict[str, List[float]] = {}
        
        # Store managers in app context
        app.jwt_manager = jwt_manager
        app.rbac_manager = rbac_manager  
        app.user_manager = user_manager
        
        # Register middleware hooks
        self._register_hooks()
        
        logger.info("Auth middleware initialized")
    
    def _register_hooks(self):
        """Register Flask request/response hooks"""
        
        @self.app.before_request
        def before_request():
            """Process request before routing"""
            
            # Start request timing
            g.request_start_time = time.time()
            
            # Handle CORS preflight
            if request.method == 'OPTIONS':
                return self._handle_cors_preflight()
            
            # Apply rate limiting
            if self.rate_limiting and not self._check_rate_limit():
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Log request
            self._log_request()
            
            # Set default user context
            g.current_user = None
            g.current_user_id = None
            g.current_username = None
            g.user_roles = []
            g.user_permissions = []
            g.token_payload = None
            
            # Try to authenticate if token present (optional)
            self._try_authenticate()
        
        @self.app.after_request
        def after_request(response):
            """Process response after request"""
            
            # Add CORS headers
            self._add_cors_headers(response)
            
            # Add security headers
            if self.security_headers:
                self._add_security_headers(response)
            
            # Log response
            self._log_response(response)
            
            return response
        
        @self.app.errorhandler(401)
        def handle_unauthorized(error):
            """Handle authentication errors"""
            return jsonify({
                "error": "Authentication required",
                "message": "Please provide a valid authentication token"
            }), 401
        
        @self.app.errorhandler(403)
        def handle_forbidden(error):
            """Handle authorization errors"""
            return jsonify({
                "error": "Access forbidden", 
                "message": "You don't have permission to access this resource"
            }), 403
        
        @self.app.errorhandler(429)
        def handle_rate_limit(error):
            """Handle rate limit errors"""
            return jsonify({
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later."
            }), 429
    
    def _handle_cors_preflight(self):
        """Handle CORS preflight requests"""
        from flask import Response
        
        response = Response()
        response.status_code = 200
        
        # Add CORS headers
        origin = request.headers.get('Origin')
        if self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization, X-Requested-With'
        )
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed for CORS"""
        if not origin:
            return False
        
        # Allow all origins in development
        if 'localhost' in origin or '127.0.0.1' in origin:
            return True
        
        # Check configured origins
        return origin in self.cors_origins
    
    def _check_rate_limit(self, 
                         max_requests: int = 1000, 
                         window_minutes: int = 60) -> bool:
        """Basic rate limiting check"""
        
        # Get client identifier
        client_id = request.remote_addr
        if hasattr(g, 'current_user_id') and g.current_user_id:
            client_id = g.current_user_id
        
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Initialize if not exists
        if client_id not in self.rate_limit_storage:
            self.rate_limit_storage[client_id] = []
        
        # Clean old requests
        self.rate_limit_storage[client_id] = [
            req_time for req_time in self.rate_limit_storage[client_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.rate_limit_storage[client_id]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limit_storage[client_id].append(now)
        return True
    
    def _try_authenticate(self):
        """Try to authenticate user if token is present"""
        try:
            token = extract_token()
            if not token:
                return
            
            # Verify token
            payload = self.jwt_manager.verify_token(token)
            if not payload:
                return
            
            # Get user info
            user_id = payload.get('user_id')
            username = payload.get('username')
            
            if not user_id or not username:
                return
            
            # Verify user exists and is active
            user = self.user_manager.get_user(user_id)
            if not user or user.status.value != 'active':
                return
            
            # Set context
            g.current_user = user
            g.current_user_id = user_id
            g.current_username = username
            g.user_roles = payload.get('roles', [])
            g.user_permissions = payload.get('permissions', [])
            g.token_payload = payload
            
        except Exception as e:
            # Log error but don't fail request
            logger.debug("Optional authentication failed: %s", e)
    
    def _add_cors_headers(self, response):
        """Add CORS headers to response"""
        origin = request.headers.get('Origin')
        
        if self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY' 
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        response.headers.pop('Server', None)
    
    def _log_request(self):
        """Log incoming request"""
        logger.info(
            "REQUEST: %s %s from %s (User-Agent: %s)",
            request.method,
            request.path,
            request.remote_addr,
            request.headers.get('User-Agent', 'unknown')
        )
    
    def _log_response(self, response):
        """Log response details"""
        duration = time.time() - g.request_start_time if hasattr(g, 'request_start_time') else 0
        
        logger.info(
            "RESPONSE: %s %s -> %d (%s) in %.3fs",
            request.method,
            request.path,
            response.status_code,
            getattr(g, 'current_username', 'anonymous'),
            duration
        )


class SecurityMiddleware:
    """
    Additional security middleware
    
    Provides enhanced security features beyond basic auth.
    """
    
    def __init__(self, app: Flask,
                 max_content_length: int = 16 * 1024 * 1024,  # 16MB
                 trusted_proxies: Optional[List[str]] = None,
                 block_suspicious_user_agents: bool = True):
        """
        Initialize security middleware
        
        Args:
            app: Flask application
            max_content_length: Maximum request content length
            trusted_proxies: List of trusted proxy IPs
            block_suspicious_user_agents: Block suspicious user agents
        """
        self.app = app
        self.max_content_length = max_content_length
        self.trusted_proxies = trusted_proxies or []
        self.block_suspicious_user_agents = block_suspicious_user_agents
        
        # Suspicious patterns
        self.suspicious_patterns = [
            'sqlmap', 'nmap', 'masscan', 'nikto', 'dirb', 'dirbuster',
            'burp', 'owasp zap', 'acunetix', 'nessus'
        ]
        
        app.config['MAX_CONTENT_LENGTH'] = max_content_length
        
        self._register_security_hooks()
        
        logger.info("Security middleware initialized")
    
    def _register_security_hooks(self):
        """Register security hooks"""
        
        @self.app.before_request
        def security_check():
            """Perform security checks"""
            
            # Check user agent
            if self.block_suspicious_user_agents:
                if not self._check_user_agent():
                    logger.warning(
                        "Blocked suspicious user agent: %s from %s",
                        request.headers.get('User-Agent', ''),
                        request.remote_addr
                    )
                    return jsonify({"error": "Blocked"}), 403
            
            # Check for common attack patterns
            if self._check_attack_patterns():
                logger.warning(
                    "Blocked potential attack from %s: %s %s",
                    request.remote_addr,
                    request.method,
                    request.path
                )
                return jsonify({"error": "Blocked"}), 403
            
            # Validate request size
            if request.content_length and request.content_length > self.max_content_length:
                logger.warning(
                    "Blocked oversized request from %s: %d bytes",
                    request.remote_addr,
                    request.content_length
                )
                return jsonify({"error": "Request too large"}), 413
    
    def _check_user_agent(self) -> bool:
        """Check if user agent is suspicious"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        if not user_agent:
            return False  # Block empty user agents
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if pattern in user_agent:
                return False
        
        return True
    
    def _check_attack_patterns(self) -> bool:
        """Check for common attack patterns"""
        
        # SQL injection patterns
        sql_patterns = [
            'union select', 'or 1=1', 'and 1=1', 'exec(', 'script>',
            'javascript:', 'vbscript:', 'onload=', 'onerror='
        ]
        
        # Check URL and query parameters
        full_path = request.full_path.lower()
        
        for pattern in sql_patterns:
            if pattern in full_path:
                return True
        
        # Check POST data if present
        try:
            if request.is_json and request.get_json():
                json_str = str(request.get_json()).lower()
                for pattern in sql_patterns:
                    if pattern in json_str:
                        return True
        except:
            pass
        
        return False


class RequestContextMiddleware:
    """
    Request context middleware
    
    Provides request-scoped context and utilities.
    """
    
    def __init__(self, app: Flask):
        """Initialize request context middleware"""
        self.app = app
        
        @app.before_request
        def setup_context():
            """Setup request context"""
            g.request_id = self._generate_request_id()
            g.request_start = time.time()
        
        logger.info("Request context middleware initialized")
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]


def create_middleware_stack(app: Flask,
                          jwt_manager: JWTManager,
                          rbac_manager: RBACManager,
                          user_manager: UserManager,
                          **kwargs) -> tuple:
    """
    Create complete middleware stack
    
    Args:
        app: Flask application
        jwt_manager: JWT manager
        rbac_manager: RBAC manager
        user_manager: User manager
        **kwargs: Additional middleware options
        
    Returns:
        Tuple of middleware instances
    """
    
    # Request context (first)
    context_middleware = RequestContextMiddleware(app)
    
    # Security middleware
    security_middleware = SecurityMiddleware(
        app,
        max_content_length=kwargs.get('max_content_length', 16 * 1024 * 1024),
        trusted_proxies=kwargs.get('trusted_proxies', []),
        block_suspicious_user_agents=kwargs.get('block_suspicious_user_agents', True)
    )
    
    # Auth middleware (last)
    auth_middleware = AuthMiddleware(
        app,
        jwt_manager=jwt_manager,
        rbac_manager=rbac_manager,
        user_manager=user_manager,
        cors_origins=kwargs.get('cors_origins', ['http://localhost:3000']),
        security_headers=kwargs.get('security_headers', True),
        rate_limiting=kwargs.get('rate_limiting', True)
    )
    
    return context_middleware, security_middleware, auth_middleware