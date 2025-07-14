from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    framework = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='inactive')  # inactive, active, paused, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
    
    # Relationships
    configurations = db.relationship('AgentConfiguration', backref='agent', lazy=True, cascade='all, delete-orphan')
    metrics = db.relationship('AgentMetric', backref='agent', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Agent {self.name}>'

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

class Framework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    connector_class = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, inactive, deprecated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AgentConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=False)
    environment = db.Column(db.String(20), default='production')  # development, staging, production
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AgentConfiguration {self.key}>'

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'key': self.key,
            'value': self.value,
            'environment': self.environment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AgentMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # performance, cost, task_specific, framework_level
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AgentMetric {self.metric_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

