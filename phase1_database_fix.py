# =============================================================================
# PHASE 1: CRITICAL FIXES - DATABASE AND MODELS
# =============================================================================

# File: src/models/database.py
# Purpose: Centralized database instance to prevent circular imports
# =============================================================================

from flask_sqlalchemy import SQLAlchemy

# Single database instance for the entire application
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        db.create_all()

# =============================================================================
# File: src/models/user.py  
# Purpose: User model (updated to fix circular imports)
# =============================================================================

from src.models.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

# =============================================================================
# File: src/models/agent.py
# Purpose: Agent-related models (updated imports)
# =============================================================================

from src.models.database import db
from datetime import datetime

class Framework(db.Model):
    __tablename__ = 'frameworks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    version = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    connector_class = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    agents = db.relationship('Agent', backref='framework_ref', lazy=True)

    def __repr__(self):
        return f'<Framework {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'connector_class': self.connector_class,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'agent_count': len(self.agents) if hasattr(self, 'agents') else 0
        }

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    framework = db.Column(db.String(50), nullable=False, index=True)
    framework_id = db.Column(db.Integer, db.ForeignKey('frameworks.id'), nullable=True)
    version = db.Column(db.String(20), nullable=False, default='1.0')
    status = db.Column(db.String(20), default='inactive', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
    endpoint = db.Column(db.String(255))
    capabilities = db.Column(db.Text)  # JSON string of capabilities list
    tags = db.Column(db.Text)  # JSON string of tags list
    
    # Relationships
    configurations = db.relationship('AgentConfiguration', backref='agent', lazy=True, cascade='all, delete-orphan')
    metrics = db.relationship('AgentMetric', backref='agent', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='agent', lazy=True)

    def __repr__(self):
        return f'<Agent {self.name}:{self.framework}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'framework': self.framework,
            'framework_id': self.framework_id,
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description,
            'endpoint': self.endpoint,
            'capabilities': json.loads(self.capabilities) if self.capabilities else [],
            'tags': json.loads(self.tags) if self.tags else [],
            'configuration_count': len(self.configurations) if hasattr(self, 'configurations') else 0
        }

class AgentConfiguration(db.Model):
    __tablename__ = 'agent_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False, index=True)
    key = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(20), default='string')  # string, json, boolean, number
    environment = db.Column(db.String(20), default='production', index=True)
    is_secret = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on agent_id, key, environment
    __table_args__ = (db.UniqueConstraint('agent_id', 'key', 'environment'),)

    def __repr__(self):
        return f'<AgentConfiguration {self.key}>'

    def to_dict(self):
        import json
        
        # Parse value based on type
        parsed_value = self.value
        if self.value_type == 'json':
            try:
                parsed_value = json.loads(self.value)
            except:
                parsed_value = self.value
        elif self.value_type == 'boolean':
            parsed_value = self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'number':
            try:
                parsed_value = float(self.value)
                if parsed_value.is_integer():
                    parsed_value = int(parsed_value)
            except:
                parsed_value = self.value
        
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'key': self.key,
            'value': "***hidden***" if self.is_secret else parsed_value,
            'value_type': self.value_type,
            'environment': self.environment,
            'is_secret': self.is_secret,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AgentMetric(db.Model):
    __tablename__ = 'agent_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False, index=True)
    metric_type = db.Column(db.String(50), nullable=False, index=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    tags = db.Column(db.Text)  # JSON string for additional tags
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AgentMetric {self.metric_name}:{self.value}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit,
            'tags': json.loads(self.tags) if self.tags else {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# =============================================================================
# File: src/models/workflow.py
# Purpose: Workflow-related models (MISSING FILE - NOW CREATED)
# =============================================================================

from src.models.database import db
from datetime import datetime
import json

class Workflow(db.Model):
    __tablename__ = 'workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    definition = db.Column(db.Text, nullable=False)  # JSON string of workflow definition
    version = db.Column(db.String(20), default='1.0')
    status = db.Column(db.String(20), default='draft', index=True)  # draft, active, deprecated
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = db.Column(db.Boolean, default=False)
    tags = db.Column(db.Text)  # JSON string of tags
    
    # Relationships
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Workflow {self.name}:{self.version}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'definition': json.loads(self.definition) if self.definition else {},
            'version': self.version,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_template': self.is_template,
            'tags': json.loads(self.tags) if self.tags else [],
            'execution_count': len(self.executions) if hasattr(self, 'executions') else 0
        }

class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, running, completed, failed, cancelled
    input_data = db.Column(db.Text)  # JSON string
    output_data = db.Column(db.Text)  # JSON string
    error_message = db.Column(db.Text)
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    started_at = db.Column(db.DateTime, index=True)
    completed_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    execution_context = db.Column(db.Text)  # JSON string for execution state
    priority = db.Column(db.Integer, default=5)  # 1-10, 1 being highest priority
    
    # Relationships
    steps = db.relationship('WorkflowStep', backref='execution', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='workflow_execution', lazy=True)

    def __repr__(self):
        return f'<WorkflowExecution {self.id}:{self.status}>'

    def to_dict(self):
        execution_time = None
        if self.started_at and self.completed_at:
            execution_time = (self.completed_at - self.started_at).total_seconds()
            
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'error_message': self.error_message,
            'started_by': self.started_by,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'execution_context': json.loads(self.execution_context) if self.execution_context else {},
            'priority': self.priority,
            'execution_time': execution_time,
            'step_count': len(self.steps) if hasattr(self, 'steps') else 0
        }

class WorkflowStep(db.Model):
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey('workflow_executions.id'), nullable=False, index=True)
    step_name = db.Column(db.String(100), nullable=False, index=True)
    step_type = db.Column(db.String(50), nullable=False)  # agent, condition, action, parallel, sequential
    status = db.Column(db.String(20), default='pending', index=True)
    order_index = db.Column(db.Integer, nullable=False)  # Order of execution
    input_data = db.Column(db.Text)  # JSON string
    output_data = db.Column(db.Text)  # JSON string
    configuration = db.Column(db.Text)  # JSON string for step-specific config
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    def __repr__(self):
        return f'<WorkflowStep {self.step_name}:{self.status}>'

    def to_dict(self):
        execution_time = None
        if self.started_at and self.completed_at:
            execution_time = (self.completed_at - self.started_at).total_seconds()
            
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'step_name': self.step_name,
            'step_type': self.step_type,
            'status': self.status,
            'order_index': self.order_index,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'configuration': json.loads(self.configuration) if self.configuration else {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'execution_time': execution_time
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True, index=True)
    workflow_execution_id = db.Column(db.Integer, db.ForeignKey('workflow_executions.id'), nullable=True, index=True)
    workflow_step_id = db.Column(db.Integer, db.ForeignKey('workflow_steps.id'), nullable=True, index=True)
    status = db.Column(db.String(20), default='pending', index=True)
    priority = db.Column(db.Integer, default=5, index=True)  # 1-10, 1 being highest
    input_data = db.Column(db.Text)  # JSON string
    output_data = db.Column(db.Text)  # JSON string
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    assigned_at = db.Column(db.DateTime, index=True)
    started_at = db.Column(db.DateTime, index=True)
    completed_at = db.Column(db.DateTime, index=True)
    timeout_seconds = db.Column(db.Integer, default=300)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    dependencies = db.Column(db.Text)  # JSON string of task IDs this task depends on

    def __repr__(self):
        return f'<Task {self.name}:{self.status}>'

    def to_dict(self):
        execution_time = None
        if self.started_at and self.completed_at:
            execution_time = (self.completed_at - self.started_at).total_seconds()
            
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_id': self.agent_id,
            'workflow_execution_id': self.workflow_execution_id,
            'workflow_step_id': self.workflow_step_id,
            'status': self.status,
            'priority': self.priority,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'timeout_seconds': self.timeout_seconds,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'dependencies': json.loads(self.dependencies) if self.dependencies else [],
            'execution_time': execution_time
        }

# Relationship for workflow step
WorkflowStep.tasks = db.relationship('Task', backref='workflow_step', lazy=True)