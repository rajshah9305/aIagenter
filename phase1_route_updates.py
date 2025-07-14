# =============================================================================
# PHASE 1: UPDATED ROUTE FILES WITH VALIDATION AND RESPONSES
# =============================================================================

# File: src/routes/agent.py
# Purpose: Updated agent routes with validation and standardized responses
# =============================================================================

from flask import Blueprint, request
from src.models.database import db
from src.models.agent import Agent, AgentConfiguration, AgentMetric, Framework
from src.utils.validation import validate_json, validate_query_params, AgentSchema, AgentUpdateSchema, AgentConfigurationSchema
from src.utils.responses import success_response, error_response, not_found_response, database_error_response
from marshmallow import fields
import json
from datetime import datetime

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('/agents', methods=['GET'])
@validate_query_params(
    status=fields.Str(),
    framework=fields.Str(),
    page=fields.Int(),
    per_page=fields.Int()
)
def get_agents():
    """Get all agents with optional filtering and pagination"""
    try:
        # Get validated query parameters
        params = getattr(request, 'validated_params', {})
        
        # Build query
        query = Agent.query
        
        # Apply filters
        if 'status' in params:
            query = query.filter(Agent.status == params['status'])
        if 'framework' in params:
            query = query.filter(Agent.framework == params['framework'])
        
        # Pagination
        page = params.get('page', 1)
        per_page = min(params.get('per_page', 20), 100)  # Max 100 per page
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        agents_data = [agent.to_dict() for agent in paginated.items]
        
        return success_response(
            data=agents_data,
            meta={
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            },
            message=f"Retrieved {len(agents_data)} agents"
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve agents")

@agent_bp.route('/agents', methods=['POST'])
@validate_json(AgentSchema)
def create_agent():
    """Create a new agent with validation"""
    try:
        data = request.validated_data
        
        # Check if agent name already exists
        existing = Agent.query.filter_by(name=data['name']).first()
        if existing:
            return error_response(
                "Agent with this name already exists",
                status_code=409
            )
        
        # Create agent
        agent = Agent(
            name=data['name'],
            framework=data['framework'],
            version=data['version'],
            description=data['description'],
            endpoint=data.get('endpoint'),
            status=data['status'],
            capabilities=json.dumps(data['capabilities']),
            tags=json.dumps(data['tags'])
        )
        
        db.session.add(agent)
        db.session.commit()
        
        return success_response(
            data=agent.to_dict(),
            message="Agent created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to create agent")

@agent_bp.route('/agents/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent by ID"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        return success_response(
            data=agent.to_dict(),
            message="Agent retrieved successfully"
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve agent")

@agent_bp.route('/agents/<int:agent_id>', methods=['PUT'])
@validate_json(AgentUpdateSchema)
def update_agent(agent_id):
    """Update an agent with validation"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        data = request.validated_data
        
        # Update fields
        for field in ['name', 'framework', 'version', 'description', 'endpoint', 'status']:
            if field in data:
                setattr(agent, field, data[field])
        
        if 'capabilities' in data:
            agent.capabilities = json.dumps(data['capabilities'])
        if 'tags' in data:
            agent.tags = json.dumps(data['tags'])
        
        agent.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response(
            data=agent.to_dict(),
            message="Agent updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to update agent")

@agent_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        agent_name = agent.name
        db.session.delete(agent)
        db.session.commit()
        
        return success_response(
            message=f"Agent '{agent_name}' deleted successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to delete agent")

@agent_bp.route('/agents/<int:agent_id>/config', methods=['GET'])
def get_agent_config(agent_id):
    """Get agent configuration"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        configs = AgentConfiguration.query.filter_by(agent_id=agent_id).all()
        config_data = [config.to_dict() for config in configs]
        
        return success_response(
            data=config_data,
            message=f"Retrieved {len(config_data)} configuration items"
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve agent configuration")

@agent_bp.route('/agents/<int:agent_id>/config', methods=['POST'])
@validate_json(AgentConfigurationSchema)
def create_agent_config(agent_id):
    """Create agent configuration with validation"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        data = request.validated_data
        
        # Check if configuration key already exists for this environment
        existing = AgentConfiguration.query.filter_by(
            agent_id=agent_id,
            key=data['key'],
            environment=data['environment']
        ).first()
        
        if existing:
            return error_response(
                f"Configuration key '{data['key']}' already exists for environment '{data['environment']}'",
                status_code=409
            )
        
        # Create configuration
        config = AgentConfiguration(
            agent_id=agent_id,
            key=data['key'],
            value=json.dumps(data['value']) if data['value_type'] == 'json' else str(data['value']),
            value_type=data['value_type'],
            environment=data['environment'],
            is_secret=data['is_secret']
        )
        
        db.session.add(config)
        db.session.commit()
        
        return success_response(
            data=config.to_dict(),
            message="Configuration created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to create configuration")

@agent_bp.route('/agents/<int:agent_id>/metrics', methods=['GET'])
@validate_query_params(
    metric_type=fields.Str(),
    metric_name=fields.Str(),
    start_date=fields.DateTime(),
    end_date=fields.DateTime(),
    limit=fields.Int()
)
def get_agent_metrics(agent_id):
    """Get agent metrics with filtering"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return not_found_response("Agent", agent_id)
        
        params = getattr(request, 'validated_params', {})
        
        # Build query
        query = AgentMetric.query.filter_by(agent_id=agent_id)
        
        # Apply filters
        if 'metric_type' in params:
            query = query.filter(AgentMetric.metric_type == params['metric_type'])
        if 'metric_name' in params:
            query = query.filter(AgentMetric.metric_name == params['metric_name'])
        if 'start_date' in params:
            query = query.filter(AgentMetric.timestamp >= params['start_date'])
        if 'end_date' in params:
            query = query.filter(AgentMetric.timestamp <= params['end_date'])
        
        # Limit results
        limit = params.get('limit', 100)
        metrics = query.order_by(AgentMetric.timestamp.desc()).limit(limit).all()
        
        metrics_data = [metric.to_dict() for metric in metrics]
        
        return success_response(
            data=metrics_data,
            message=f"Retrieved {len(metrics_data)} metrics"
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve metrics")

@agent_bp.route('/frameworks', methods=['GET'])
def get_frameworks():
    """Get all available frameworks"""
    try:
        frameworks = Framework.query.filter_by(status='active').all()
        frameworks_data = [framework.to_dict() for framework in frameworks]
        
        return success_response(
            data=frameworks_data,
            message=f"Retrieved {len(frameworks_data)} frameworks"
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve frameworks")

# =============================================================================
# File: src/routes/workflow.py  
# Purpose: Updated workflow routes with validation
# =============================================================================

from flask import Blueprint, request
from src.models.database import db
from src.models.workflow import Workflow, WorkflowExecution, WorkflowStep, Task
from src.utils.validation import validate_json, validate_query_params, WorkflowSchema, WorkflowUpdateSchema, WorkflowExecutionSchema, TaskSchema, TaskUpdateSchema
from src.utils.responses import success_response, error_response, not_found_response, database_error_response
from marshmallow import fields
import json
from datetime import datetime

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/workflows', methods=['GET'])
@validate_query_params(
    status=fields.Str(),
    is_template=fields.Bool(),
    page=fields.Int(),
    per_page=fields.Int()
)
def get_workflows():
    """Get all workflows with filtering and pagination"""
    try:
        params = getattr(request, 'validated_params', {})
        
        # Build query
        query = Workflow.query
        
        # Apply filters
        if 'status' in params:
            query = query.filter(Workflow.status == params['status'])
        if 'is_template' in params:
            query = query.filter(Workflow.is_template == params['is_template'])
        
        # Pagination
        page = params.get('page', 1)
        per_page = min(params.get('per_page', 20), 100)
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        workflows_data = [workflow.to_dict() for workflow in paginated.items]
        
        return success_response(
            data=workflows_data,
            meta={
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page
            }
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve workflows")

@workflow_bp.route('/workflows', methods=['POST'])
@validate_json(WorkflowSchema)
def create_workflow():
    """Create a new workflow with validation"""
    try:
        data = request.validated_data
        
        # Check if workflow name already exists
        existing = Workflow.query.filter_by(name=data['name']).first()
        if existing:
            return error_response(
                "Workflow with this name already exists",
                status_code=409
            )
        
        # Create workflow
        workflow = Workflow(
            name=data['name'],
            description=data['description'],
            definition=json.dumps(data['definition']),
            version=data['version'],
            is_template=data['is_template'],
            tags=json.dumps(data['tags'])
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return success_response(
            data=workflow.to_dict(),
            message="Workflow created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to create workflow")

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get a specific workflow by ID"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return not_found_response("Workflow", workflow_id)
        
        return success_response(data=workflow.to_dict())
        
    except Exception as e:
        return database_error_response("Failed to retrieve workflow")

@workflow_bp.route('/workflows/<int:workflow_id>/execute', methods=['POST'])
@validate_json(WorkflowExecutionSchema)
def execute_workflow(workflow_id):
    """Execute a workflow with validation"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return not_found_response("Workflow", workflow_id)
        
        if workflow.status != 'active':
            return error_response(
                "Cannot execute inactive workflow",
                status_code=400
            )
        
        data = request.validated_data
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            input_data=json.dumps(data['input_data']),
            priority=data['priority'],
            status='pending'
        )
        
        db.session.add(execution)
        db.session.commit()
        
        return success_response(
            data=execution.to_dict(),
            message="Workflow execution started",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to execute workflow")

@workflow_bp.route('/tasks', methods=['GET'])
@validate_query_params(
    status=fields.Str(),
    agent_id=fields.Int(),
    priority=fields.Int(),
    page=fields.Int(),
    per_page=fields.Int()
)
def get_tasks():
    """Get all tasks with filtering"""
    try:
        params = getattr(request, 'validated_params', {})
        
        # Build query
        query = Task.query
        
        # Apply filters
        if 'status' in params:
            query = query.filter(Task.status == params['status'])
        if 'agent_id' in params:
            query = query.filter(Task.agent_id == params['agent_id'])
        if 'priority' in params:
            query = query.filter(Task.priority == params['priority'])
        
        # Order by priority and creation time
        query = query.order_by(Task.priority.asc(), Task.created_at.asc())
        
        # Pagination
        page = params.get('page', 1)
        per_page = min(params.get('per_page', 20), 100)
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        tasks_data = [task.to_dict() for task in paginated.items]
        
        return success_response(
            data=tasks_data,
            meta={
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page
            }
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve tasks")

@workflow_bp.route('/tasks', methods=['POST'])
@validate_json(TaskSchema)
def create_task():
    """Create a new task with validation"""
    try:
        data = request.validated_data
        
        # Validate agent exists if specified
        if data.get('agent_id'):
            from src.models.agent import Agent
            agent = Agent.query.get(data['agent_id'])
            if not agent:
                return not_found_response("Agent", data['agent_id'])
        
        # Create task
        task = Task(
            name=data['name'],
            description=data['description'],
            agent_id=data.get('agent_id'),
            workflow_execution_id=data.get('workflow_execution_id'),
            priority=data['priority'],
            input_data=json.dumps(data['input_data']),
            timeout_seconds=data['timeout_seconds'],
            max_retries=data['max_retries'],
            dependencies=json.dumps(data['dependencies'])
        )
        
        db.session.add(task)
        db.session.commit()
        
        return success_response(
            data=task.to_dict(),
            message="Task created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to create task")

@workflow_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@validate_json(TaskUpdateSchema)
def update_task(task_id):
    """Update a task with validation"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return not_found_response("Task", task_id)
        
        data = request.validated_data
        
        # Update fields
        for field in ['name', 'description', 'agent_id', 'status', 'priority', 'error_message']:
            if field in data:
                setattr(task, field, data[field])
        
        if 'input_data' in data:
            task.input_data = json.dumps(data['input_data'])
        if 'output_data' in data:
            task.output_data = json.dumps(data['output_data'])
        
        # Update timestamps based on status
        if data.get('status') == 'assigned' and not task.assigned_at:
            task.assigned_at = datetime.utcnow()
        elif data.get('status') == 'running' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif data.get('status') in ['completed', 'failed'] and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response(
            data=task.to_dict(),
            message="Task updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to update task")

# =============================================================================
# File: src/routes/user.py (CREATE NEW FILE)
# Purpose: User management routes (was missing from original codebase)
# =============================================================================

from flask import Blueprint, request
from src.models.database import db
from src.models.user import User
from src.utils.validation import validate_json, validate_query_params
from src.utils.responses import success_response, error_response, not_found_response, database_error_response
from marshmallow import Schema, fields
from marshmallow import validates, ValidationError

user_bp = Blueprint('user', __name__)

class UserSchema(Schema):
    """Schema for user creation"""
    username = fields.Str(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(required=True)
    is_active = fields.Bool(missing=True)
    
    @validates('username')
    def validate_username(self, value):
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')

class UserUpdateSchema(Schema):
    """Schema for user updates"""
    username = fields.Str(validate=lambda x: len(x) >= 3)
    email = fields.Email()
    is_active = fields.Bool()

@user_bp.route('/users', methods=['GET'])
@validate_query_params(
    is_active=fields.Bool(),
    page=fields.Int(),
    per_page=fields.Int()
)
def get_users():
    """Get all users with filtering"""
    try:
        params = getattr(request, 'validated_params', {})
        
        query = User.query
        
        if 'is_active' in params:
            query = query.filter(User.is_active == params['is_active'])
        
        # Pagination
        page = params.get('page', 1)
        per_page = min(params.get('per_page', 20), 100)
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users_data = [user.to_dict() for user in paginated.items]
        
        return success_response(
            data=users_data,
            meta={
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page
            }
        )
        
    except Exception as e:
        return database_error_response("Failed to retrieve users")

@user_bp.route('/users', methods=['POST'])
@validate_json(UserSchema)
def create_user():
    """Create a new user"""
    try:
        data = request.validated_data
        
        user = User(
            username=data['username'],
            email=data['email'],
            is_active=data['is_active']
        )
        
        db.session.add(user)
        db.session.commit()
        
        return success_response(
            data=user.to_dict(),
            message="User created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to create user")

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID"""
    try:
        user = User.query.get(user_id)
        if not user:
            return not_found_response("User", user_id)
        
        return success_response(data=user.to_dict())
        
    except Exception as e:
        return database_error_response("Failed to retrieve user")

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@validate_json(UserUpdateSchema)
def update_user(user_id):
    """Update a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return not_found_response("User", user_id)
        
        data = request.validated_data
        
        # Check username uniqueness if updating
        if 'username' in data and data['username'] != user.username:
            existing = User.query.filter_by(username=data['username']).first()
            if existing:
                return error_response(
                    "Username already exists",
                    status_code=409
                )
        
        # Update fields
        for field in ['username', 'email', 'is_active']:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return success_response(
            data=user.to_dict(),
            message="User updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to update user")

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return not_found_response("User", user_id)
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return success_response(
            message=f"User '{username}' deleted successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return database_error_response("Failed to delete user")