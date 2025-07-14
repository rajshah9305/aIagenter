# =============================================================================
# PHASE 1: UPDATED MAIN APPLICATION AND REQUIREMENTS
# =============================================================================

# File: main.py
# Purpose: Secure main application entry point
# =============================================================================

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Flask and extensions
from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO

# Import our modules
from src.models.database import db, init_db, create_tables
from src.config import get_config
from src.utils.responses import error_response

def create_app(config_name=None):
    """Application factory with secure configuration"""
    
    # Get configuration
    config_class = get_config(config_name)
    
    # Create Flask app
    app = Flask(
        __name__, 
        static_folder=str(project_root / 'static'),
        instance_relative_config=True
    )
    
    # Apply configuration
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    init_db(app)
    
    # Configure CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        async_mode='eventlet'
    )
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        create_tables(app)
    
    # Setup logging
    setup_logging(app)
    
    # Static file serving
    setup_static_routes(app)
    
    return app, socketio

def register_blueprints(app):
    """Register all Flask blueprints"""
    
    # Import blueprints
    from src.routes.agent import agent_bp
    from src.routes.workflow import workflow_bp
    from src.routes.orchestration import orchestration_bp
    from src.routes.monitoring import monitoring_bp
    from src.routes.task_management import task_management_bp
    from src.services.api_docs import api_docs_bp
    
    # Register with API prefix
    app.register_blueprint(agent_bp, url_prefix='/api')
    app.register_blueprint(workflow_bp, url_prefix='/api')
    app.register_blueprint(orchestration_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api')
    app.register_blueprint(task_management_bp, url_prefix='/api')
    app.register_blueprint(api_docs_bp, url_prefix='/api')
    
    app.logger.info("All blueprints registered successfully")

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return error_response("Bad request", status_code=400)
    
    @app.errorhandler(401)
    def unauthorized(error):
        return error_response("Unauthorized access", status_code=401)
    
    @app.errorhandler(403)
    def forbidden(error):
        return error_response("Access forbidden", status_code=403)
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response("Resource not found", status_code=404)
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response("Method not allowed", status_code=405)
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return error_response("Request entity too large", status_code=413)
    
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return error_response("Internal server error", status_code=500)
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        app.logger.error(f"Unexpected error: {error}", exc_info=True)
        return error_response("An unexpected error occurred", status_code=500)

def setup_static_routes(app):
    """Setup static file serving for SPA"""
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        """Serve static files for Single Page Application"""
        static_folder_path = app.static_folder
        
        if not static_folder_path:
            return error_response("Static folder not configured", status_code=404)
        
        # If path exists, serve it
        if path and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        
        # Otherwise serve index.html for SPA routing
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        
        return error_response("Frontend application not found", status_code=404)
    
    @app.before_request
    def log_request_info():
        """Log request information for debugging"""
        if app.config['DEBUG']:
            app.logger.debug(f"{request.method} {request.url}")

def setup_logging(app):
    """Setup application logging"""
    
    if not app.debug and not app.testing:
        # Create logs directory
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Setup file logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            logs_dir / 'agentorchestra.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        app.logger.info("AgentOrchestra application started")

def main():
    """Main application entry point"""
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        env_file = project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
        else:
            print(f"⚠️  No .env file found at {env_file}")
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env file loading")
    
    # Validate required environment variables
    required_env_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or environment configuration")
        sys.exit(1)
    
    # Get configuration name
    config_name = os.environ.get('FLASK_ENV', 'development')
    print(f"🚀 Starting AgentOrchestra in {config_name} mode")
    
    # Create application
    try:
        app, socketio = create_app(config_name)
        print("✅ Application created successfully")
    except Exception as e:
        print(f"❌ Failed to create application: {e}")
        sys.exit(1)
    
    # Get host and port
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    try:
        print(f"🌐 Starting server on http://{host}:{port}")
        
        # Run with SocketIO
        socketio.run(
            app,
            host=host,
            port=port,
            debug=app.config['DEBUG'],
            use_reloader=app.config['DEBUG']
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Application shutting down...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
    finally:
        print("✅ Cleanup completed")

if __name__ == '__main__':
    main()

# =============================================================================
# File: requirements.txt
# Purpose: Updated dependencies with validation and security
# =============================================================================

# Core Flask framework
Flask==3.0.0
Werkzeug==3.0.1

# Database
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.23

# CORS and WebSocket support
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
python-socketio==5.9.0
python-engineio==4.7.1
eventlet==0.33.3

# Input validation and serialization
marshmallow==3.20.2
flask-marshmallow==0.15.0

# Configuration management
python-dotenv==1.0.0

# HTTP requests
requests==2.31.0

# YAML support
PyYAML==6.0.1

# Async support
asyncio==3.4.3

# Security
bcrypt==4.1.2
cryptography==41.0.8

# Optional: For production deployment
gunicorn==21.2.0
gevent==23.9.1

# Optional: For Redis caching
redis==5.0.1

# Optional: For PostgreSQL support
psycopg2-binary==2.9.9

# Development dependencies (install with pip install -r requirements-dev.txt)
# pytest==7.4.3
# pytest-flask==1.3.0
# pytest-cov==4.1.0
# black==23.11.0
# flake8==6.1.0
# mypy==1.7.1

# =============================================================================
# File: requirements-dev.txt
# Purpose: Development dependencies
# =============================================================================

# Include production requirements
-r requirements.txt

# Testing
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code formatting and linting
black==23.11.0
flake8==6.1.0
isort==5.12.0

# Type checking
mypy==1.7.1

# Documentation
Sphinx==7.2.6

# Debugging
flask-debugtoolbar==0.13.1

# =============================================================================
# File: .gitignore
# Purpose: Updated gitignore for secure development
# =============================================================================

# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Flask
instance/

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml

# pytest
.pytest_cache/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# OS
.DS_Store
Thumbs.db

# Application specific
static/build/
node_modules/

# Secrets and sensitive files
secrets/
*.key
*.pem
*.crt

# =============================================================================
# File: setup_database.py
# Purpose: Database initialization script
# =============================================================================

#!/usr/bin/env python3
"""
Database setup script for AgentOrchestra
Run this script to initialize the database with sample data
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import create_app
from src.models.database import db
from src.models.user import User
from src.models.agent import Agent, Framework, AgentConfiguration
from src.models.workflow import Workflow, Task

def create_sample_data():
    """Create sample data for development"""
    
    print("Creating sample data...")
    
    # Create sample frameworks
    frameworks = [
        Framework(
            name='AutoGen',
            version='0.2.0',
            description='Microsoft AutoGen framework for conversational AI',
            connector_class='AutoGenConnector',
            status='active'
        ),
        Framework(
            name='CrewAI',
            version='0.1.0',
            description='CrewAI framework for role-based AI agents',
            connector_class='CrewAIConnector',
            status='active'
        ),
        Framework(
            name='LangGraph',
            version='0.1.0',
            description='LangChain graph-based agent framework',
            connector_class='LangGraphConnector',
            status='active'
        )
    ]
    
    for framework in frameworks:
        db.session.add(framework)
    
    # Create sample user
    sample_user = User(
        username='admin',
        email='admin@agentorchestra.ai',
        is_active=True
    )
    db.session.add(sample_user)
    
    # Commit frameworks and user first
    db.session.commit()
    
    # Create sample agents
    agents = [
        Agent(
            name='Research Assistant',
            framework='AutoGen',
            framework_id=1,
            description='AI agent for research and analysis tasks',
            status='active',
            capabilities='["research", "analysis", "reporting"]',
            tags='["research", "assistant"]'
        ),
        Agent(
            name='Content Creator',
            framework='CrewAI',
            framework_id=2,
            description='AI agent for content creation and writing',
            status='active',
            capabilities='["writing", "content_creation", "editing"]',
            tags='["content", "creative"]'
        ),
        Agent(
            name='Data Processor',
            framework='LangGraph',
            framework_id=3,
            description='AI agent for data processing and transformation',
            status='inactive',
            capabilities='["data_processing", "transformation", "analysis"]',
            tags='["data", "processing"]'
        )
    ]
    
    for agent in agents:
        db.session.add(agent)
    
    # Commit agents
    db.session.commit()
    
    # Create sample configurations
    configs = [
        AgentConfiguration(
            agent_id=1,
            key='model',
            value='gpt-4',
            value_type='string',
            environment='production'
        ),
        AgentConfiguration(
            agent_id=1,
            key='temperature',
            value='0.7',
            value_type='number',
            environment='production'
        ),
        AgentConfiguration(
            agent_id=2,
            key='max_tokens',
            value='2000',
            value_type='number',
            environment='production'
        )
    ]
    
    for config in configs:
        db.session.add(config)
    
    # Create sample workflow
    workflow = Workflow(
        name='Data Analysis Pipeline',
        description='Complete data analysis workflow',
        definition='{"nodes": [{"id": "node1", "type": "agent", "name": "Data Collector"}], "connections": []}',
        version='1.0',
        status='active',
        created_by=1,
        tags='["data", "analysis", "pipeline"]'
    )
    db.session.add(workflow)
    
    # Create sample task
    task = Task(
        name='Analyze Sales Data',
        description='Analyze Q4 sales data and generate report',
        agent_id=1,
        status='pending',
        priority=3,
        input_data='{"data_source": "sales_q4.csv", "output_format": "pdf"}',
        timeout_seconds=600
    )
    db.session.add(task)
    
    # Final commit
    db.session.commit()
    
    print("✅ Sample data created successfully")

def main():
    """Main setup function"""
    
    print("🚀 Setting up AgentOrchestra database...")
    
    # Load environment
    try:
        from dotenv import load_dotenv
        env_file = project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
    except ImportError:
        print("⚠️  python-dotenv not installed")
    
    # Validate SECRET_KEY
    if not os.environ.get('SECRET_KEY'):
        print("❌ SECRET_KEY environment variable is required")
        print("Please set SECRET_KEY in your .env file")
        sys.exit(1)
    
    # Create app
    config_name = os.environ.get('FLASK_ENV', 'development')
    app, _ = create_app(config_name)
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        
        # Check if we should create sample data
        create_samples = input("Create sample data? (y/N): ").lower().strip()
        if create_samples in ('y', 'yes'):
            create_sample_data()
        
    print("🎉 Database setup completed!")

if __name__ == '__main__':
    main()