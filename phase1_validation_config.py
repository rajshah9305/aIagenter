# =============================================================================
# PHASE 1: INPUT VALIDATION AND CONFIGURATION MANAGEMENT
# =============================================================================

# File: src/utils/__init__.py
# Purpose: Make utils a package
# =============================================================================

# Empty file to make utils directory a Python package

# =============================================================================
# File: src/utils/validation.py
# Purpose: Input validation schemas and decorators
# =============================================================================

from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from functools import wraps
from flask import request, jsonify
import json

# Custom validators
def validate_non_empty_string(value):
    """Validate that string is not empty"""
    if not value or not value.strip():
        raise ValidationError("This field cannot be empty")

def validate_framework_name(value):
    """Validate framework name against supported frameworks"""
    valid_frameworks = [
        'AutoGen', 'CrewAI', 'LangGraph', 'MetaGPT', 'BabyAGI', 
        'MiniAGI', 'AgentVerse', 'OpenAgents', 'Cerebras', 'Orca'
    ]
    if value not in valid_frameworks:
        raise ValidationError(f"Framework must be one of: {', '.join(valid_frameworks)}")

def validate_status(value):
    """Validate status values"""
    valid_statuses = ['active', 'inactive', 'paused', 'error', 'starting', 'stopping']
    if value not in valid_statuses:
        raise ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")

def validate_priority(value):
    """Validate priority is between 1 and 10"""
    if not 1 <= value <= 10:
        raise ValidationError("Priority must be between 1 and 10")

# Base schemas
class BaseSchema(Schema):
    """Base schema with common functionality"""
    
    def handle_error(self, error, data, **kwargs):
        """Custom error handler"""
        raise ValidationError(error.messages)

# Agent-related schemas
class AgentSchema(BaseSchema):
    """Schema for agent creation and updates"""
    name = fields.Str(required=True, validate=validate_non_empty_string)
    framework = fields.Str(required=True, validate=validate_framework_name)
    version = fields.Str(missing='1.0', validate=validate_non_empty_string)
    description = fields.Str(missing='')
    endpoint = fields.Url(missing=None)
    capabilities = fields.List(fields.Str(), missing=[])
    tags = fields.List(fields.Str(), missing=[])
    status = fields.Str(missing='inactive', validate=validate_status)

class AgentUpdateSchema(BaseSchema):
    """Schema for agent updates (all fields optional)"""
    name = fields.Str(validate=validate_non_empty_string)
    framework = fields.Str(validate=validate_framework_name)
    version = fields.Str(validate=validate_non_empty_string)
    description = fields.Str()
    endpoint = fields.Url()
    capabilities = fields.List(fields.Str())
    tags = fields.List(fields.Str())
    status = fields.Str(validate=validate_status)

class AgentConfigurationSchema(BaseSchema):
    """Schema for agent configuration"""
    key = fields.Str(required=True, validate=validate_non_empty_string)
    value = fields.Raw(required=True)  # Can be any type
    value_type = fields.Str(missing='string', validate=lambda x: x in ['string', 'json', 'boolean', 'number'])
    environment = fields.Str(missing='production', validate=lambda x: x in ['development', 'staging', 'production'])
    is_secret = fields.Bool(missing=False)

# Task-related schemas
class TaskSchema(BaseSchema):
    """Schema for task creation"""
    name = fields.Str(required=True, validate=validate_non_empty_string)
    description = fields.Str(missing='')
    agent_id = fields.Int(missing=None)
    workflow_execution_id = fields.Int(missing=None)
    priority = fields.Int(missing=5, validate=validate_priority)
    input_data = fields.Dict(missing={})
    timeout_seconds = fields.Int(missing=300, validate=lambda x: x > 0)
    max_retries = fields.Int(missing=3, validate=lambda x: x >= 0)
    dependencies = fields.List(fields.Int(), missing=[])

class TaskUpdateSchema(BaseSchema):
    """Schema for task updates"""
    name = fields.Str(validate=validate_non_empty_string)
    description = fields.Str()
    agent_id = fields.Int()
    status = fields.Str(validate=lambda x: x in ['pending', 'assigned', 'running', 'completed', 'failed', 'cancelled'])
    priority = fields.Int(validate=validate_priority)
    input_data = fields.Dict()
    output_data = fields.Dict()
    error_message = fields.Str()

# Workflow-related schemas
class WorkflowNodeSchema(BaseSchema):
    """Schema for workflow nodes"""
    id = fields.Str(required=True)
    type = fields.Str(required=True, validate=lambda x: x in ['agent', 'condition', 'action', 'parallel', 'sequential'])
    name = fields.Str(required=True, validate=validate_non_empty_string)
    config = fields.Dict(missing={})
    position = fields.Dict(missing={'x': 0, 'y': 0})

class WorkflowConnectionSchema(BaseSchema):
    """Schema for workflow connections"""
    from_node_id = fields.Str(required=True)
    to_node_id = fields.Str(required=True)
    condition = fields.Str(missing=None)
    label = fields.Str(missing=None)

class WorkflowDefinitionSchema(BaseSchema):
    """Schema for workflow definition"""
    nodes = fields.List(fields.Nested(WorkflowNodeSchema), required=True, validate=lambda x: len(x) > 0)
    connections = fields.List(fields.Nested(WorkflowConnectionSchema), missing=[])
    variables = fields.Dict(missing={})

class WorkflowSchema(BaseSchema):
    """Schema for workflow creation"""
    name = fields.Str(required=True, validate=validate_non_empty_string)
    description = fields.Str(missing='')
    definition = fields.Nested(WorkflowDefinitionSchema, required=True)
    version = fields.Str(missing='1.0', validate=validate_non_empty_string)
    is_template = fields.Bool(missing=False)
    tags = fields.List(fields.Str(), missing=[])

class WorkflowUpdateSchema(BaseSchema):
    """Schema for workflow updates"""
    name = fields.Str(validate=validate_non_empty_string)
    description = fields.Str()
    definition = fields.Nested(WorkflowDefinitionSchema)
    version = fields.Str(validate=validate_non_empty_string)
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'deprecated'])
    is_template = fields.Bool()
    tags = fields.List(fields.Str())

class WorkflowExecutionSchema(BaseSchema):
    """Schema for workflow execution"""
    input_data = fields.Dict(missing={})
    priority = fields.Int(missing=5, validate=validate_priority)

# Validation decorators
def validate_json(schema_class):
    """Decorator to validate JSON input against a schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get JSON data
                data = request.get_json(force=True)
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No JSON data provided'
                    }), 400
                
                # Validate against schema
                schema = schema_class()
                try:
                    validated_data = schema.load(data)
                except ValidationError as err:
                    return jsonify({
                        'success': False,
                        'error': 'Validation failed',
                        'details': err.messages
                    }), 400
                
                # Add validated data to request
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON: {str(e)}'
                }), 400
        return decorated_function
    return decorator

def validate_query_params(**param_schemas):
    """Decorator to validate query parameters"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validated_params = {}
                errors = {}
                
                for param_name, schema_field in param_schemas.items():
                    param_value = request.args.get(param_name)
                    
                    if param_value is not None:
                        try:
                            # Deserialize and validate
                            if isinstance(schema_field, fields.Int):
                                validated_params[param_name] = int(param_value)
                            elif isinstance(schema_field, fields.Bool):
                                validated_params[param_name] = param_value.lower() in ('true', '1', 'yes')
                            elif isinstance(schema_field, fields.List):
                                validated_params[param_name] = param_value.split(',')
                            else:
                                validated_params[param_name] = param_value
                            
                            # Validate using field validators
                            schema_field.deserialize(validated_params[param_name])
                            
                        except (ValueError, ValidationError) as e:
                            errors[param_name] = str(e)
                
                if errors:
                    return jsonify({
                        'success': False,
                        'error': 'Query parameter validation failed',
                        'details': errors
                    }), 400
                
                # Add validated params to request
                request.validated_params = validated_params
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Parameter validation error: {str(e)}'
                }), 400
        return decorated_function
    return decorator

# =============================================================================
# File: src/utils/responses.py
# Purpose: Standardized API response formatting
# =============================================================================

from flask import jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def success_response(data=None, message=None, status_code=200, meta=None):
    """Create a standardized success response"""
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if meta:
        response['meta'] = meta
    
    return jsonify(response), status_code

def error_response(error, status_code=400, details=None, error_code=None):
    """Create a standardized error response"""
    response = {
        'success': False,
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['details'] = details
    if error_code:
        response['error_code'] = error_code
    
    # Log error for debugging
    logger.error(f"API Error {status_code}: {error} | Details: {details}")
    
    return jsonify(response), status_code

def not_found_response(resource_type, resource_id=None):
    """Create a not found error response"""
    if resource_id:
        message = f"{resource_type} with ID '{resource_id}' not found"
    else:
        message = f"{resource_type} not found"
    
    return error_response(message, status_code=404, error_code='NOT_FOUND')

def validation_error_response(validation_errors):
    """Create a validation error response"""
    return error_response(
        "Validation failed",
        status_code=400,
        details=validation_errors,
        error_code='VALIDATION_ERROR'
    )

def database_error_response(operation="Database operation"):
    """Create a database error response"""
    return error_response(
        f"{operation} failed",
        status_code=500,
        error_code='DATABASE_ERROR'
    )

def unauthorized_response(message="Authentication required"):
    """Create an unauthorized response"""
    return error_response(
        message,
        status_code=401,
        error_code='UNAUTHORIZED'
    )

def forbidden_response(message="Access denied"):
    """Create a forbidden response"""
    return error_response(
        message,
        status_code=403,
        error_code='FORBIDDEN'
    )

# =============================================================================
# File: src/config.py
# Purpose: Secure configuration management
# =============================================================================

import os
from datetime import timedelta
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class BaseConfig:
    """Base configuration with secure defaults"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    TASK_QUEUE_SIZE = int(os.environ.get('TASK_QUEUE_SIZE', '1000'))
    METRICS_RETENTION_HOURS = int(os.environ.get('METRICS_RETENTION_HOURS', '24'))
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', '20'))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', '100'))
    
    # Service settings
    ORCHESTRATION_WORKER_THREADS = int(os.environ.get('ORCHESTRATION_WORKER_THREADS', '4'))
    TASK_EXECUTION_TIMEOUT = int(os.environ.get('TASK_EXECUTION_TIMEOUT', '300'))
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', '30'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    
    # External services
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        pass

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR}/agentorchestra_dev.db'
    
    # Security (relaxed for development)
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True
    
    @staticmethod
    def init_app(app):
        """Initialize development app"""
        import logging
        logging.basicConfig(level=logging.DEBUG)

class TestingConfig(BaseConfig):
    """Testing configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Database (in-memory for fast tests)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Security (disabled for testing)
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Disable external services for testing
    TASK_QUEUE_SIZE = 10
    METRICS_RETENTION_HOURS = 1
    
    # Override secret key for tests
    SECRET_KEY = 'test-secret-key-not-for-production'
    
    @staticmethod
    def init_app(app):
        """Initialize testing app"""
        import logging
        logging.disable(logging.CRITICAL)

class ProductionConfig(BaseConfig):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required for production")
    
    # Enhanced security for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 10
    }
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    @staticmethod
    def init_app(app):
        """Initialize production app"""
        import logging
        from logging.handlers import RotatingFileHandler
        
        # File logging
        if not app.debug:
            file_handler = RotatingFileHandler(
                'logs/agentorchestra.log',
                maxBytes=10240000,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('AgentOrchestra startup')

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])

# =============================================================================
# File: .env.example
# Purpose: Environment variable template
# =============================================================================

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///agentorchestra.db

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Application Settings
TASK_QUEUE_SIZE=1000
METRICS_RETENTION_HOURS=24
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Service Settings
ORCHESTRATION_WORKER_THREADS=4
TASK_EXECUTION_TIMEOUT=300
HEALTH_CHECK_INTERVAL=30

# External Services
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Optional: External API Keys (when needed)
# OPENAI_API_KEY=your-openai-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key