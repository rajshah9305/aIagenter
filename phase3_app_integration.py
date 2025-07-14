# Phase 3: Updated Application Integration
# File: src/app.py (Updated with Phase 3 optimizations)

import os
from flask import Flask, request, g, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import redis
import time
from datetime import datetime

# Import core components
from src.config import get_config
from src.models.database import db
from src.extensions import init_extensions
from src.monitoring import init_monitoring, metrics_collector, alert_manager
from src.tasks.celery_config import make_celery
from src.utils.db_optimization import QueryOptimizer, CacheManager
from src.routes import register_routes
from src.middleware.error_handling import ErrorHandler
from src.middleware.request_middleware import RequestMiddleware

def create_app(config_name='development'):
    """Create and configure Flask application with Phase 3 optimizations"""
    
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions with optimizations
    extensions = init_extensions(app)
    
    # Initialize monitoring system
    monitoring_components = init_monitoring(app)
    
    # Initialize Celery for background tasks
    celery = make_celery(app)
    app.celery = celery
    
    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # Initialize SocketIO for real-time communication
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=False
    )
    
    # Setup middleware
    setup_middleware(app, extensions, monitoring_components)
    
    # Register routes
    register_routes(app)
    
    # Setup real-time monitoring endpoints
    setup_realtime_monitoring(app, socketio, monitoring_components)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Application lifecycle hooks
    setup_lifecycle_hooks(app, monitoring_components)
    
    return app, socketio

def setup_middleware(app, extensions, monitoring_components):
    """Setup application middleware"""
    
    # Error handling middleware
    error_handler = ErrorHandler()
    error_handler.init_app(app)
    
    # Request middleware for metrics and monitoring
    request_middleware = RequestMiddleware(
        metrics_collector=monitoring_components['metrics_collector'],
        cache_manager=extensions['cache_manager']
    )
    request_middleware.init_app(app)
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        g.start_time = time.time()
        g.request_id = request_middleware.generate_request_id()
        
        # Log request start
        app.logger.debug(f"Request {g.request_id} started: {request.method} {request.url}")
        
        # Check system health
        if hasattr(g, 'request_id') and g.request_id.endswith('000'):  # Every 1000th request
            check_system_health(app, monitoring_components)
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Record metrics
            is_error = response.status_code >= 400
            monitoring_components['metrics_collector'].record_request(duration, is_error)
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
                
            # Log request completion
            app.logger.debug(f"Request {getattr(g, 'request_id', 'unknown')} completed: "
                           f"{response.status_code} in {duration:.3f}s")
        
        return response

def setup_realtime_monitoring(app, socketio, monitoring_components):
    """Setup real-time monitoring with WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        app.logger.info("Client connected to monitoring")
        
        # Send initial metrics
        metrics = monitoring_components['metrics_collector'].get_real_time_metrics()
        socketio.emit('metrics_update', metrics)
        
        # Send active alerts
        alerts = monitoring_components['alert_manager'].get_active_alerts()
        socketio.emit('alerts_update', [alert.__dict__ for alert in alerts])
    
    @socketio.on('subscribe_metrics')
    def handle_metrics_subscription(data):
        """Handle metrics subscription"""
        interval = data.get('interval', 10)  # Default 10 seconds
        
        # Start periodic metrics broadcast
        def send_metrics():
            while True:
                try:
                    metrics = monitoring_components['metrics_collector'].get_real_time_metrics()
                    socketio.emit('metrics_update', metrics)
                    
                    # Check and send alerts
                    monitoring_components['alert_manager'].check_alerts(metrics)
                    alerts = monitoring_components['alert_manager'].get_active_alerts()
                    socketio.emit('alerts_update', [alert.__dict__ for alert in alerts])
                    
                    socketio.sleep(interval)
                except Exception as e:
                    app.logger.error(f"Error broadcasting metrics: {e}")
                    socketio.sleep(interval)
        
        socketio.start_background_task(send_metrics)
    
    @socketio.on('request_system_info')
    def handle_system_info_request():
        """Handle system information request"""
        system_info = get_system_information(monitoring_components)
        socketio.emit('system_info', system_info)

def setup_error_handlers(app):
    """Setup custom error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'error_type': 'NOT_FOUND',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_type': 'INTERNAL_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'error_type': 'RATE_LIMIT',
            'timestamp': datetime.utcnow().isoformat()
        }), 429

def setup_lifecycle_hooks(app, monitoring_components):
    """Setup application lifecycle hooks"""
    
    @app.before_first_request
    def before_first_request():
        """Execute before first request"""
        app.logger.info("AgentOrchestra application starting up...")
        
        # Warm up cache
        try:
            from src.tasks.maintenance import cache_warmup
            cache_warmup.delay()
        except Exception as e:
            app.logger.warning(f"Cache warmup failed: {e}")
    
    def cleanup():
        """Cleanup function for app shutdown"""
        app.logger.info("AgentOrchestra application shutting down...")
        
        # Stop metrics collection
        monitoring_components['metrics_collector'].stop_collection()
        
        # Close database connections
        db.session.remove()
        
        app.logger.info("Cleanup completed")
    
    # Register cleanup function
    import atexit
    atexit.register(cleanup)

def check_system_health(app, monitoring_components):
    """Periodic system health check"""
    try:
        # Get current metrics
        metrics = monitoring_components['metrics_collector'].get_real_time_metrics()
        
        # Check for critical conditions
        system_metrics = metrics.get('system', {})
        
        if system_metrics.get('memory_usage', 0) > 90:
            app.logger.warning(f"High memory usage: {system_metrics['memory_usage']:.1f}%")
        
        if system_metrics.get('cpu_usage', 0) > 85:
            app.logger.warning(f"High CPU usage: {system_metrics['cpu_usage']:.1f}%")
        
        # Trigger alerts check
        monitoring_components['alert_manager'].check_alerts(metrics)
        
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")

def get_system_information(monitoring_components):
    """Get comprehensive system information"""
    try:
        metrics = monitoring_components['metrics_collector'].get_real_time_metrics()
        alerts = monitoring_components['alert_manager'].get_active_alerts()
        alert_stats = monitoring_components['alert_manager'].get_alert_statistics()
        query_stats = monitoring_components.get('query_optimizer', {})
        
        return {
            'metrics': metrics,
            'alerts': {
                'active': [alert.__dict__ for alert in alerts],
                'statistics': alert_stats
            },
            'performance': {
                'query_stats': getattr(query_stats, 'get_query_statistics', lambda: {})(),
                'cache_info': 'Cache information would be here'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'error': f"Failed to get system information: {e}",
            'timestamp': datetime.utcnow().isoformat()
        }

# File: src/middleware/request_middleware.py

import time
import uuid
import hashlib
from flask import request, g, current_app
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RequestMiddleware:
    """Enhanced request middleware with metrics and caching"""
    
    def __init__(self, metrics_collector=None, cache_manager=None):
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.request_count = 0
        
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        self.request_count += 1
        unique_string = f"{time.time()}-{self.request_count}-{uuid.uuid4().hex[:8]}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def _before_request(self):
        """Execute before each request"""
        g.start_time = time.time()
        g.request_id = self.generate_request_id()
        
        # Log request details
        if current_app.config.get('DEBUG'):
            logger.debug(f"Request {g.request_id}: {request.method} {request.url}")
            if request.is_json:
                logger.debug(f"Request body: {request.get_json()}")
        
        # Add request to audit log for important endpoints
        if self._is_important_endpoint(request.endpoint):
            self._audit_log_request()
    
    def _after_request(self, response):
        """Execute after each request"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Record metrics if collector is available
            if self.metrics_collector:
                is_error = response.status_code >= 400
                self.metrics_collector.record_request(duration, is_error)
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                logger.warning(f"Slow request {g.request_id}: {duration:.3f}s - "
                             f"{request.method} {request.url}")
            
            # Log errors
            if response.status_code >= 500:
                logger.error(f"Server error {g.request_id}: {response.status_code} - "
                           f"{request.method} {request.url}")
            elif response.status_code >= 400:
                logger.warning(f"Client error {g.request_id}: {response.status_code} - "
                             f"{request.method} {request.url}")
        
        return response
    
    def _teardown_request(self, error):
        """Execute at the end of each request"""
        if error:
            logger.error(f"Request teardown error {getattr(g, 'request_id', 'unknown')}: {error}")
    
    def _is_important_endpoint(self, endpoint: Optional[str]) -> bool:
        """Check if endpoint requires audit logging"""
        if not endpoint:
            return False
        
        important_endpoints = [
            'agents.create_agent',
            'agents.update_agent', 
            'agents.delete_agent',
            'agents.start_agent',
            'agents.stop_agent',
            'workflows.create_workflow',
            'workflows.execute_workflow',
            'frameworks.create_framework'
        ]
        
        return endpoint in important_endpoints
    
    def _audit_log_request(self):
        """Log request for audit trail"""
        audit_logger = logging.getLogger('agentorchestra.audit')
        
        audit_data = {
            'request_id': g.request_id,
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'timestamp': time.time()
        }
        
        # Don't log sensitive data in request body
        if request.is_json:
            body = request.get_json()
            # Remove sensitive fields
            safe_body = {k: v for k, v in body.items() 
                        if k not in ['password', 'secret', 'token', 'key']}
            audit_data['request_body'] = safe_body
        
        audit_logger.info(f"Audit: {audit_data}")

# File: src/routes/monitoring.py (New monitoring routes)

from flask import Blueprint, jsonify, request
from src.monitoring import metrics_collector, alert_manager
from src.extensions import query_optimizer, cache_manager
from src.utils.validation import validate_request
from src.utils.responses import success_response, error_response

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/metrics', methods=['GET'])
def get_real_time_metrics():
    """Get real-time system metrics"""
    try:
        metrics = metrics_collector.get_real_time_metrics()
        return success_response(data=metrics)
    except Exception as e:
        return error_response(f"Failed to get metrics: {e}", status_code=500)

@monitoring_bp.route('/metrics/history', methods=['GET'])
def get_metrics_history():
    """Get historical metrics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # This would typically query the database for historical metrics
        # For now, return current metrics
        metrics = metrics_collector.get_real_time_metrics()
        
        return success_response(data={
            'current': metrics,
            'hours': hours,
            'message': 'Historical metrics endpoint - implementation pending'
        })
    except Exception as e:
        return error_response(f"Failed to get metrics history: {e}", status_code=500)

@monitoring_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """Get active alerts"""
    try:
        active_alerts = alert_manager.get_active_alerts()
        alert_data = [
            {
                'rule_name': alert.rule_name,
                'level': alert.level.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved
            }
            for alert in active_alerts
        ]
        
        return success_response(data=alert_data)
    except Exception as e:
        return error_response(f"Failed to get alerts: {e}", status_code=500)

@monitoring_bp.route('/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    try:
        hours = request.args.get('hours', 24, type=int)
        alert_history = alert_manager.get_alert_history(hours)
        
        history_data = [
            {
                'rule_name': alert.rule_name,
                'level': alert.level.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alert_history
        ]
        
        return success_response(data=history_data)
    except Exception as e:
        return error_response(f"Failed to get alert history: {e}", status_code=500)

@monitoring_bp.route('/alerts/statistics', methods=['GET'])
def get_alert_statistics():
    """Get alert statistics"""
    try:
        stats = alert_manager.get_alert_statistics()
        return success_response(data=stats)
    except Exception as e:
        return error_response(f"Failed to get alert statistics: {e}", status_code=500)

@monitoring_bp.route('/performance', methods=['GET'])
def get_performance_info():
    """Get performance information"""
    try:
        performance_data = {
            'query_statistics': {},
            'cache_info': {
                'status': 'active' if cache_manager else 'disabled'
            },
            'system_info': metrics_collector.get_real_time_metrics()
        }
        
        if query_optimizer:
            performance_data['query_statistics'] = query_optimizer.get_query_statistics()
        
        return success_response(data=performance_data)
    except Exception as e:
        return error_response(f"Failed to get performance info: {e}", status_code=500)

@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': metrics_collector.get_real_time_metrics().get('timestamp'),
            'services': {
                'database': 'healthy',  # Would check DB connection
                'redis': 'healthy' if cache_manager else 'disabled',
                'metrics_collector': 'healthy' if metrics_collector else 'disabled',
                'alert_manager': 'healthy' if alert_manager else 'disabled'
            }
        }
        
        # Check if any critical alerts are active
        critical_alerts = [
            alert for alert in alert_manager.get_active_alerts()
            if alert.level.value == 'critical'
        ]
        
        if critical_alerts:
            health_status['status'] = 'degraded'
            health_status['critical_alerts'] = len(critical_alerts)
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return success_response(data=health_status), status_code
        
    except Exception as e:
        return error_response(f"Health check failed: {e}", status_code=500)

# File: src/routes/__init__.py (Updated)

from flask import Blueprint
from src.routes.agents import agents_bp
from src.routes.frameworks import frameworks_bp
from src.routes.workflows import workflows_bp
from src.routes.dashboard import dashboard_bp
from src.routes.monitoring import monitoring_bp  # New monitoring routes

def register_routes(app):
    """Register all route blueprints"""
    
    # API prefix
    api_prefix = '/api'
    
    # Register existing blueprints
    app.register_blueprint(agents_bp, url_prefix=f'{api_prefix}/agents')
    app.register_blueprint(frameworks_bp, url_prefix=f'{api_prefix}/frameworks')
    app.register_blueprint(workflows_bp, url_prefix=f'{api_prefix}/workflows')
    app.register_blueprint(dashboard_bp, url_prefix=f'{api_prefix}/dashboard')
    
    # Register new monitoring blueprint
    app.register_blueprint(monitoring_bp, url_prefix=f'{api_prefix}/monitoring')
    
    # Health check route at root level
    @app.route('/health')
    def root_health():
        """Simple health check"""
        return {'status': 'healthy', 'service': 'agentorchestra'}
    
    # API info route
    @app.route(f'{api_prefix}/')
    def api_info():
        """API information endpoint"""
        return {
            'service': 'AgentOrchestra API',
            'version': '1.0.0',
            'endpoints': {
                'agents': f'{api_prefix}/agents',
                'frameworks': f'{api_prefix}/frameworks',
                'workflows': f'{api_prefix}/workflows',
                'dashboard': f'{api_prefix}/dashboard',
                'monitoring': f'{api_prefix}/monitoring',
                'health': '/health'
            }
        }