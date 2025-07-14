# SERVICE ARCHITECTURE IMPROVEMENTS FOR AGENTORCHESTRA

## 1. CREATE SERVICE REGISTRY

# Create: src/services/__init__.py
import threading
from typing import Dict, Any, Optional
from contextlib import contextmanager

class ServiceRegistry:
    """Central service registry for managing application services"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._started = False
    
    def register(self, name: str, service: Any) -> None:
        """Register a service"""
        with self._lock:
            self._services[name] = service
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        with self._lock:
            return self._services.get(name)
    
    def start_all(self) -> None:
        """Start all registered services"""
        with self._lock:
            if self._started:
                return
            
            for name, service in self._services.items():
                if hasattr(service, 'start'):
                    try:
                        service.start()
                        print(f"✅ Started service: {name}")
                    except Exception as e:
                        print(f"❌ Failed to start service {name}: {e}")
            
            self._started = True
    
    def stop_all(self) -> None:
        """Stop all registered services"""
        with self._lock:
            if not self._started:
                return
            
            for name, service in self._services.items():
                if hasattr(service, 'stop'):
                    try:
                        service.stop()
                        print(f"✅ Stopped service: {name}")
                    except Exception as e:
                        print(f"❌ Failed to stop service {name}: {e}")
            
            self._started = False
    
    @contextmanager
    def service_context(self):
        """Context manager for service lifecycle"""
        try:
            self.start_all()
            yield self
        finally:
            self.stop_all()

# Global service registry instance
registry = ServiceRegistry()

## 2. IMPROVED ORCHESTRATION ENGINE WITH SERVICE COORDINATION

# Updated: src/services/orchestration_engine.py
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.connectors.base import FrameworkConnector, AgentStatus, TaskStatus
from src.connectors.autogen_connector import AutoGenConnector
from src.connectors.crewai_connector import CrewAIConnector
from src.services import registry

class OrchestrationEngine:
    """Improved orchestration engine with proper service coordination"""
    
    def __init__(self):
        self.connectors: Dict[str, FrameworkConnector] = {}
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        self.message_bus: List[Dict[str, Any]] = []
        self.is_running = False
        self.worker_thread = None
        self._lock = threading.RLock()
        
        # Register with service registry
        registry.register('orchestration_engine', self)
        
        # Initialize connectors
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize framework connectors"""
        self.connectors['autogen'] = AutoGenConnector()
        self.connectors['crewai'] = CrewAIConnector()
    
    def start(self):
        """Start the orchestration engine"""
        with self._lock:
            if self.is_running:
                return
                
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("🚀 Orchestration engine started")
    
    def stop(self):
        """Stop the orchestration engine"""
        with self._lock:
            self.is_running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            print("🛑 Orchestration engine stopped")
    
    def health_check(self) -> Dict[str, Any]:
        """Get health status"""
        with self._lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'registered_agents': len(self.agent_registry),
                'queued_tasks': len(self.task_queue),
                'running_tasks': len(self.running_tasks),
                'connectors': list(self.connectors.keys()),
                'thread_alive': self.worker_thread.is_alive() if self.worker_thread else False
            }
    
    # ... rest of the methods remain the same but with proper thread safety
    
    def _worker_loop(self):
        """Thread-safe worker loop"""
        while self.is_running:
            try:
                with self._lock:
                    # Process tasks safely
                    if self.task_queue:
                        task_info = self.task_queue.pop(0)
                        self._execute_task(task_info)
                
                self._check_running_tasks()
                self._cleanup_message_bus()
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error in orchestration worker loop: {e}")
                time.sleep(1)

## 3. IMPROVED ROUTE HANDLERS WITH DEPENDENCY INJECTION

# Updated: src/routes/orchestration.py
from flask import Blueprint, request, jsonify
from src.services import registry
from src.utils.validation import validate_json, AgentSchema
from src.utils.error_handlers import standardize_response, handle_database_error, handle_not_found

orchestration_bp = Blueprint('orchestration', __name__)

def get_orchestration_engine():
    """Get orchestration engine from service registry"""
    engine = registry.get('orchestration_engine')
    if not engine:
        raise RuntimeError("Orchestration engine not available")
    return engine

def get_agent_registry():
    """Get agent registry from service registry"""
    agent_registry = registry.get('agent_registry')
    if not agent_registry:
        raise RuntimeError("Agent registry not available")
    return agent_registry

@orchestration_bp.route('/orchestration/agents/register', methods=['POST'])
@validate_json(AgentSchema)
def register_agent():
    """Register a new agent with validation"""
    try:
        data = request.validated_data
        engine = get_orchestration_engine()
        agent_registry = get_agent_registry()
        
        # Register with orchestration engine
        agent_id = engine.register_agent(data['framework'], data)
        
        # Register with discovery service
        agent_info = {
            'name': data['name'],
            'framework': data['framework'],
            'capabilities': data.get('capabilities', []),
            'tags': data.get('tags', []),
            'description': data.get('description', ''),
            'version': data.get('version', '1.0'),
            'metadata': data.get('metadata', {})
        }
        
        agent_registry.register_agent(agent_id, agent_info)
        
        return standardize_response(
            success=True,
            data={
                'agent_id': agent_id,
                'framework': data['framework']
            },
            message='Agent registered successfully',
            status_code=201
        )
        
    except Exception as e:
        return standardize_response(
            success=False,
            error=str(e),
            status_code=500
        )

@orchestration_bp.route('/orchestration/health', methods=['GET'])
def get_system_health():
    """Get comprehensive system health"""
    try:
        health_data = {}
        
        # Get health from all registered services
        for service_name in ['orchestration_engine', 'task_engine', 'metrics_collector']:
            service = registry.get(service_name)
            if service and hasattr(service, 'health_check'):
                health_data[service_name] = service.health_check()
            else:
                health_data[service_name] = {'status': 'not_available'}
        
        return standardize_response(
            success=True,
            data=health_data
        )
        
    except Exception as e:
        return standardize_response(
            success=False,
            error=str(e),
            status_code=500
        )

## 4. APPLICATION FACTORY PATTERN

# Updated: src/app.py (New file to replace main.py)
import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.database import db
from src.services import registry
from src.services.orchestration_engine import OrchestrationEngine
from src.services.task_distribution import TaskDistributionEngine
from src.services.monitoring_service import MetricsCollector, AlertingSystem
from src.services.agent_registry import AgentRegistry

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration
    app.config.from_object(f'src.config.{config_name.title()}Config')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register blueprints
    from src.routes.agent import agent_bp
    from src.routes.workflow import workflow_bp
    from src.routes.orchestration import orchestration_bp
    from src.routes.monitoring import monitoring_bp
    from src.routes.task_management import task_management_bp
    from src.services.api_docs import api_docs_bp
    
    app.register_blueprint(agent_bp, url_prefix='/api')
    app.register_blueprint(workflow_bp, url_prefix='/api')
    app.register_blueprint(orchestration_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api')
    app.register_blueprint(task_management_bp, url_prefix='/api')
    app.register_blueprint(api_docs_bp, url_prefix='/api')
    
    # Initialize services
    with app.app_context():
        init_services()
        db.create_all()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return standardize_response(
            success=False,
            error="Resource not found",
            status_code=404
        )
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return standardize_response(
            success=False,
            error="Internal server error",
            status_code=500
        )
    
    return app, socketio

def init_services():
    """Initialize and register all services"""
    # Create service instances
    orchestration_engine = OrchestrationEngine()
    task_engine = TaskDistributionEngine()
    metrics_collector = MetricsCollector()
    alerting_system = AlertingSystem(metrics_collector)
    agent_registry = AgentRegistry()
    
    # Register services
    registry.register('orchestration_engine', orchestration_engine)
    registry.register('task_engine', task_engine)
    registry.register('metrics_collector', metrics_collector)
    registry.register('alerting_system', alerting_system)
    registry.register('agent_registry', agent_registry)
    
    # Start services
    registry.start_all()

## 5. CONFIGURATION MANAGEMENT

# Create: src/config.py
import os
from datetime import timedelta

class BaseConfig:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Service configurations
    TASK_QUEUE_SIZE = int(os.environ.get('TASK_QUEUE_SIZE', '1000'))
    METRICS_RETENTION_HOURS = int(os.environ.get('METRICS_RETENTION_HOURS', '24'))
    
    # Security
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    BCRYPT_LOG_ROUNDS = 12
    
    # Performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///agentorchestra_dev.db'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:pass@localhost/agentorchestra'
    LOG_LEVEL = 'INFO'
    
    # Production security
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 0,
    }

class TestingConfig(BaseConfig):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'WARNING'

## 6. UPDATED MAIN ENTRY POINT

# Updated: main.py
import os
from src.app import create_app
from src.services import registry

def main():
    """Main application entry point"""
    config_name = os.environ.get('FLASK_ENV', 'development')
    app, socketio = create_app(config_name)
    
    try:
        # Use service registry context for proper lifecycle management
        with registry.service_context():
            socketio.run(
                app, 
                host='0.0.0.0', 
                port=int(os.environ.get('PORT', 5000)),
                debug=app.config['DEBUG']
            )
    except KeyboardInterrupt:
        print("🛑 Application shutting down...")
    finally:
        print("✅ Cleanup completed")

if __name__ == '__main__':
    main()