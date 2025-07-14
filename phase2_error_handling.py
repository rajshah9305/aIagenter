# =============================================================================
# PHASE 2: COMPREHENSIVE ERROR HANDLING MIDDLEWARE
# =============================================================================

# File: src/middleware/error_handler.py
# Purpose: Centralized error handling middleware with logging and monitoring
# =============================================================================

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from src.models.database import db
from src.utils.responses import error_response

logger = logging.getLogger(__name__)

class ErrorType:
    """Error type constants"""
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class AgentOrchestraException(Exception):
    """Base exception class for AgentOrchestra"""
    
    def __init__(self, 
                 message: str, 
                 error_type: str = ErrorType.SYSTEM_ERROR,
                 status_code: int = 500,
                 details: Dict[str, Any] = None,
                 original_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()

class ValidationException(AgentOrchestraException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            status_code=400,
            details=details
        )

class DatabaseException(AgentOrchestraException):
    """Database operation error exception"""
    
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_type=ErrorType.DATABASE_ERROR,
            status_code=500,
            original_exception=original_exception
        )

class AuthenticationException(AgentOrchestraException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            status_code=401
        )

class AuthorizationException(AgentOrchestraException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            status_code=403
        )

class BusinessLogicException(AgentOrchestraException):
    """Business logic error exception"""
    
    def __init__(self, message: str, status_code: int = 400, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_type=ErrorType.BUSINESS_LOGIC_ERROR,
            status_code=status_code,
            details=details
        )

class ExternalServiceException(AgentOrchestraException):
    """External service error exception"""
    
    def __init__(self, service_name: str, message: str, original_exception: Exception = None):
        super().__init__(
            message=f"External service '{service_name}' error: {message}",
            error_type=ErrorType.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details={'service': service_name},
            original_exception=original_exception
        )

class ErrorHandler:
    """Centralized error handler for the application"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.error_stats = {}
        self._setup_logging()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handling for Flask app"""
        self.app = app
        
        # Register error handlers
        app.register_error_handler(AgentOrchestraException, self._handle_custom_exception)
        app.register_error_handler(ValidationError, self._handle_validation_error)
        app.register_error_handler(SQLAlchemyError, self._handle_database_error)
        app.register_error_handler(HTTPException, self._handle_http_exception)
        app.register_error_handler(Exception, self._handle_generic_exception)
        
        # Add before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def _setup_logging(self):
        """Setup error logging configuration"""
        # Create formatter for error logs
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        
        # Create error handler for file logging
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Add to logger
        logger.addHandler(error_handler)
    
    def _before_request(self):
        """Execute before each request"""
        g.start_time = datetime.utcnow()
        g.request_id = self._generate_request_id()
        
        # Log request start
        logger.debug(f"Request {g.request_id} started: {request.method} {request.url}")
    
    def _after_request(self, response):
        """Execute after each request"""
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            # Add request ID to response headers
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            # Log request completion
            logger.debug(f"Request {getattr(g, 'request_id', 'unknown')} completed: "
                        f"{response.status_code} in {duration:.3f}s")
        
        return response
    
    def _teardown_request(self, error):
        """Execute at the end of each request"""
        if error:
            logger.error(f"Request teardown error: {error}")
            # Ensure database session is cleaned up
            db.session.rollback()
    
    def _handle_custom_exception(self, error: AgentOrchestraException):
        """Handle custom AgentOrchestra exceptions"""
        self._log_error(error, error.error_type)
        self._update_error_stats(error.error_type)
        
        response_data = {
            'success': False,
            'error': error.message,
            'error_type': error.error_type,
            'timestamp': error.timestamp.isoformat(),
            'request_id': getattr(g, 'request_id', None)
        }
        
        if error.details:
            response_data['details'] = error.details
        
        # Include stack trace in debug mode
        if self.app and self.app.debug and error.original_exception:
            response_data['debug_info'] = {
                'original_exception': str(error.original_exception),
                'traceback': traceback.format_exception(
                    type(error.original_exception),
                    error.original_exception,
                    error.original_exception.__traceback__
                )
            }
        
        return jsonify(response_data), error.status_code
    
    def _handle_validation_error(self, error: ValidationError):
        """Handle Marshmallow validation errors"""
        self._log_error(error, ErrorType.VALIDATION_ERROR)
        self._update_error_stats(ErrorType.VALIDATION_ERROR)
        
        return error_response(
            "Validation failed",
            status_code=400,
            details=error.messages,
            error_code=ErrorType.VALIDATION_ERROR
        )
    
    def _handle_database_error(self, error: SQLAlchemyError):
        """Handle SQLAlchemy database errors"""
        db.session.rollback()
        
        self._log_error(error, ErrorType.DATABASE_ERROR)
        self._update_error_stats(ErrorType.DATABASE_ERROR)
        
        # Determine specific error type
        if isinstance(error, IntegrityError):
            message = "Data integrity constraint violation"
            status_code = 409
        elif isinstance(error, OperationalError):
            message = "Database operation failed"
            status_code = 503
        else:
            message = "Database error occurred"
            status_code = 500
        
        response_data = {
            'success': False,
            'error': message,
            'error_type': ErrorType.DATABASE_ERROR,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': getattr(g, 'request_id', None)
        }
        
        # Include debug info in development
        if self.app and self.app.debug:
            response_data['debug_info'] = {
                'original_error': str(error),
                'error_class': error.__class__.__name__
            }
        
        return jsonify(response_data), status_code
    
    def _handle_http_exception(self, error: HTTPException):
        """Handle HTTP exceptions"""
        self._log_error(error, f"http_{error.code}")
        self._update_error_stats(f"http_{error.code}")
        
        return error_response(
            error.description or f"HTTP {error.code} error",
            status_code=error.code,
            error_code=f"HTTP_{error.code}"
        )
    
    def _handle_generic_exception(self, error: Exception):
        """Handle unexpected exceptions"""
        self._log_error(error, ErrorType.UNKNOWN_ERROR, include_traceback=True)
        self._update_error_stats(ErrorType.UNKNOWN_ERROR)
        
        response_data = {
            'success': False,
            'error': "An unexpected error occurred",
            'error_type': ErrorType.UNKNOWN_ERROR,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': getattr(g, 'request_id', None)
        }
        
        # Include debug info in development
        if self.app and self.app.debug:
            response_data['debug_info'] = {
                'original_error': str(error),
                'error_class': error.__class__.__name__,
                'traceback': traceback.format_exception(type(error), error, error.__traceback__)
            }
        
        return jsonify(response_data), 500
    
    def _log_error(self, error: Exception, error_type: str, include_traceback: bool = False):
        """Log error with context information"""
        context = {
            'error_type': error_type,
            'request_id': getattr(g, 'request_id', None),
            'url': request.url if request else None,
            'method': request.method if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'remote_addr': request.remote_addr if request else None
        }
        
        if include_traceback:
            logger.error(
                f"Error: {error} | Context: {context}",
                exc_info=True
            )
        else:
            logger.error(f"Error: {error} | Context: {context}")
    
    def _update_error_stats(self, error_type: str):
        """Update error statistics"""
        current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
        
        if current_hour not in self.error_stats:
            self.error_stats[current_hour] = {}
        
        if error_type not in self.error_stats[current_hour]:
            self.error_stats[current_hour][error_type] = 0
        
        self.error_stats[current_hour][error_type] += 1
        
        # Keep only last 24 hours of stats
        if len(self.error_stats) > 24:
            oldest_hour = min(self.error_stats.keys())
            del self.error_stats[oldest_hour]
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_error_stats(self) -> Dict[str, Dict[str, int]]:
        """Get error statistics"""
        return self.error_stats.copy()
    
    def clear_error_stats(self):
        """Clear error statistics"""
        self.error_stats.clear()

# =============================================================================
# File: src/middleware/decorators.py
# Purpose: Error handling decorators for routes and services
# =============================================================================

from functools import wraps
from typing import Callable, Type, Union, List
import logging

logger = logging.getLogger(__name__)

def handle_errors(*exception_types: Type[Exception], 
                 error_type: str = ErrorType.SYSTEM_ERROR,
                 log_error: bool = True,
                 reraise: bool = False):
    """Decorator to handle specific exceptions"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {e}")
                
                if reraise:
                    raise AgentOrchestraException(
                        message=str(e),
                        error_type=error_type,
                        original_exception=e
                    )
                
                return None
        return wrapper
    return decorator

def database_transaction(rollback_on_error: bool = True):
    """Decorator to handle database transactions"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                db.session.commit()
                return result
            except Exception as e:
                if rollback_on_error:
                    db.session.rollback()
                
                if isinstance(e, SQLAlchemyError):
                    raise DatabaseException(
                        message="Database operation failed",
                        original_exception=e
                    )
                else:
                    raise
        return wrapper
    return decorator

def validate_input(schema_class):
    """Decorator to validate input data"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            
            try:
                data = request.get_json()
                if not data:
                    raise ValidationException("No input data provided")
                
                schema = schema_class()
                validated_data = schema.load(data)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                
                return func(*args, **kwargs)
                
            except ValidationError as e:
                raise ValidationException(
                    message="Input validation failed",
                    details=e.messages
                )
        return wrapper
    return decorator

def require_service(service_name: str):
    """Decorator to ensure a service is available"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from src.services.service_manager import service_manager
            
            service = service_manager.get_service(service_name)
            if not service:
                raise BusinessLogicException(
                    f"Required service '{service_name}' is not available"
                )
            
            # Add service to kwargs
            kwargs[f'{service_name}_service'] = service
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, 
                    delay: float = 1.0,
                    backoff_factor: float = 2.0,
                    exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """Decorator to retry function on failure"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}, "
                                     f"retrying in {current_delay}s")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            # If we get here, all retries failed
            raise last_exception
        return wrapper
    return decorator

def log_execution_time(threshold_seconds: float = 1.0):
    """Decorator to log execution time if it exceeds threshold"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                if execution_time > threshold_seconds:
                    logger.warning(f"Function {func.__name__} took {execution_time:.3f}s to execute "
                                 f"(threshold: {threshold_seconds}s)")
        return wrapper
    return decorator

# =============================================================================
# File: src/middleware/request_middleware.py
# Purpose: Request processing middleware
# =============================================================================

import time
import logging
from flask import Flask, request, g, jsonify
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class RequestMiddleware:
    """Request processing middleware"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.request_stats = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        self.app = app
        
        app.before_request(self._before_request)
        app.after_request(self._after_request)
    
    def _before_request(self):
        """Process before each request"""
        g.start_time = time.time()
        g.request_id = self._generate_request_id()
        
        # Rate limiting check (basic implementation)
        if self._check_rate_limit():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'error_type': 'rate_limit_error'
            }), 429
        
        # Log request
        self._log_request()
    
    def _after_request(self, response):
        """Process after each request"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Add headers
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            # Update stats
            self._update_request_stats(response.status_code, duration)
            
            # Log response
            self._log_response(response, duration)
        
        return response
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _check_rate_limit(self) -> bool:
        """Check if request should be rate limited"""
        # Basic rate limiting implementation
        # In production, use Redis or similar
        client_ip = request.remote_addr
        current_minute = datetime.utcnow().strftime('%Y-%m-%d-%H-%M')
        
        key = f"{client_ip}:{current_minute}"
        
        if key not in self.request_stats:
            self.request_stats[key] = 0
        
        self.request_stats[key] += 1
        
        # Allow 100 requests per minute per IP
        return self.request_stats[key] > 100
    
    def _log_request(self):
        """Log incoming request"""
        logger.info(f"Request {g.request_id}: {request.method} {request.url} "
                   f"from {request.remote_addr}")
    
    def _log_response(self, response, duration: float):
        """Log outgoing response"""
        logger.info(f"Response {g.request_id}: {response.status_code} "
                   f"in {duration:.3f}s")
        
        # Log slow requests
        if duration > 2.0:
            logger.warning(f"Slow request {g.request_id}: {duration:.3f}s for "
                         f"{request.method} {request.url}")
    
    def _update_request_stats(self, status_code: int, duration: float):
        """Update request statistics"""
        current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
        
        if current_hour not in self.request_stats:
            self.request_stats[current_hour] = {
                'total_requests': 0,
                'status_codes': {},
                'total_duration': 0.0,
                'slow_requests': 0
            }
        
        stats = self.request_stats[current_hour]
        stats['total_requests'] += 1
        stats['total_duration'] += duration
        
        if status_code not in stats['status_codes']:
            stats['status_codes'][status_code] = 0
        stats['status_codes'][status_code] += 1
        
        if duration > 2.0:
            stats['slow_requests'] += 1
    
    def get_request_stats(self) -> dict:
        """Get request statistics"""
        return self.request_stats.copy()

# Global middleware instances
error_handler = ErrorHandler()
request_middleware = RequestMiddleware()