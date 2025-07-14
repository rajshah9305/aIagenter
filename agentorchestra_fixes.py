# CRITICAL FIXES FOR AGENTORCHESTRA

## 1. FIX CIRCULAR IMPORTS

# Create: src/models/database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Update: src/models/user.py
from src.models.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

# Update: src/models/agent.py
from src.models.database import db
from datetime import datetime

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    framework = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='inactive')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
    
    configurations = db.relationship('AgentConfiguration', backref='agent', lazy=True, cascade='all, delete-orphan')
    metrics = db.relationship('AgentMetric', backref='agent', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'framework': self.framework,
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description
        }

# Create: src/models/workflow.py (MISSING FILE)
from src.models.database import db
from datetime import datetime
import json

class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    definition = db.Column(db.Text)  # JSON string
    version = db.Column(db.String(20), default='1.0')
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'definition': json.loads(self.definition) if self.definition else {},
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WorkflowExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    input_data = db.Column(db.Text)  # JSON string
    output_data = db.Column(db.Text)  # JSON string
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    steps = db.relationship('WorkflowStep', backref='execution', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WorkflowStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey('workflow_execution.id'), nullable=False)
    step_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    input_data = db.Column(db.Text)
    output_data = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'step_name': self.step_name,
            'status': self.status,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    workflow_execution_id = db.Column(db.Integer, db.ForeignKey('workflow_execution.id'))
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.Integer, default=5)
    input_data = db.Column(db.Text)
    output_data = db.Column(db.Text)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_id': self.agent_id,
            'workflow_execution_id': self.workflow_execution_id,
            'status': self.status,
            'priority': self.priority,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

## 2. SECURE MAIN APPLICATION

# Updated: main.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.database import db  # Updated import
from src.models.agent import Agent, Framework, AgentConfiguration, AgentMetric
from src.models.workflow import Workflow, WorkflowExecution, WorkflowStep, Task
from src.routes.agent import agent_bp
from src.routes.workflow import workflow_bp
from src.routes.orchestration import orchestration_bp
from src.routes.monitoring import monitoring_bp
from src.routes.task_management import task_management_bp
from src.services.api_docs import api_docs_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Secure configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Enable CORS
    CORS(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(agent_bp, url_prefix='/api')
    app.register_blueprint(workflow_bp, url_prefix='/api')
    app.register_blueprint(orchestration_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api')
    app.register_blueprint(task_management_bp, url_prefix='/api')
    app.register_blueprint(api_docs_bp, url_prefix='/api')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404

    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

## 3. ADD INPUT VALIDATION

# Create: src/utils/validation.py
from marshmallow import Schema, fields, ValidationError
from functools import wraps
from flask import request, jsonify

class AgentSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x) > 0)
    framework = fields.Str(required=True, validate=lambda x: x in ['AutoGen', 'CrewAI', 'LangGraph', 'MetaGPT', 'BabyAGI'])
    version = fields.Str(missing='1.0')
    description = fields.Str(missing='')
    configuration = fields.Dict(missing={})

class TaskSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(missing='')
    agent_id = fields.Int()
    priority = fields.Int(missing=5, validate=lambda x: 1 <= x <= 10)
    input_data = fields.Dict(missing={})

class WorkflowSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(missing='')
    definition = fields.Dict(required=True)
    version = fields.Str(missing='1.0')

def validate_json(schema_class):
    """Decorator to validate JSON input against a schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                schema = schema_class()
                validated_data = schema.load(data)
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
            except Exception as e:
                return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400
        return decorated_function
    return decorator

## 4. STANDARDIZE ERROR HANDLING

# Create: src/utils/error_handlers.py
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def standardize_response(success=True, data=None, message=None, error=None, status_code=200):
    """Standardize API response format"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
        logger.error(f"API Error: {error}")
    
    return jsonify(response), status_code

def handle_database_error(e):
    """Handle database-related errors"""
    db.session.rollback()
    return standardize_response(
        success=False,
        error="Database operation failed",
        status_code=500
    )

def handle_not_found(resource_type, resource_id):
    """Handle resource not found errors"""
    return standardize_response(
        success=False,
        error=f"{resource_type} with ID {resource_id} not found",
        status_code=404
    )

## 5. ADD ENVIRONMENT CONFIGURATION

# Create: .env.example
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
FLASK_DEBUG=True
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO

# Updated: requirements.txt
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.0.5
marshmallow==3.20.1
flask-marshmallow==0.15.0
python-dotenv==1.0.0
eventlet==0.33.3
python-socketio==5.8.0
python-engineio==4.7.1
requests==2.31.0
PyYAML==6.0.1