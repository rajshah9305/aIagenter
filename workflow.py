from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.workflow import Workflow, WorkflowExecution, WorkflowStep, Task
from datetime import datetime
import json

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """Get all workflows"""
    try:
        status = request.args.get('status')
        
        query = Workflow.query
        if status:
            query = query.filter(Workflow.status == status)
            
        workflows = query.all()
        return jsonify([workflow.to_dict() for workflow in workflows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    try:
        data = request.get_json()
        
        workflow = Workflow(
            name=data['name'],
            description=data.get('description', ''),
            definition=json.dumps(data['definition']),
            version=data.get('version', '1.0')
        )
        
        db.session.add(workflow)
        db.session.commit()
        return jsonify(workflow.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get a specific workflow by ID"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        return jsonify(workflow.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update a workflow"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        data = request.get_json()
        
        workflow.name = data.get('name', workflow.name)
        workflow.description = data.get('description', workflow.description)
        if 'definition' in data:
            workflow.definition = json.dumps(data['definition'])
        workflow.version = data.get('version', workflow.version)
        workflow.status = data.get('status', workflow.status)
        workflow.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(workflow.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows/<int:workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """Delete a workflow"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        db.session.delete(workflow)
        db.session.commit()
        return jsonify({'message': 'Workflow deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows/<int:workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute a workflow"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status='running'
        )
        
        db.session.add(execution)
        db.session.commit()
        
        # TODO: Implement actual workflow execution logic
        # For now, just return the execution record
        
        return jsonify(execution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/workflows/<int:workflow_id>/executions', methods=['GET'])
def get_workflow_executions(workflow_id):
    """Get executions for a specific workflow"""
    try:
        executions = WorkflowExecution.query.filter_by(workflow_id=workflow_id).all()
        return jsonify([execution.to_dict() for execution in executions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/executions/<int:execution_id>', methods=['GET'])
def get_execution(execution_id):
    """Get a specific execution by ID"""
    try:
        execution = WorkflowExecution.query.get_or_404(execution_id)
        return jsonify(execution.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/executions/<int:execution_id>/steps', methods=['GET'])
def get_execution_steps(execution_id):
    """Get steps for a specific execution"""
    try:
        steps = WorkflowStep.query.filter_by(execution_id=execution_id).all()
        return jsonify([step.to_dict() for step in steps])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with optional filtering"""
    try:
        status = request.args.get('status')
        agent_id = request.args.get('agent_id', type=int)
        
        query = Task.query
        if status:
            query = query.filter(Task.status == status)
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
            
        tasks = query.order_by(Task.priority.asc(), Task.created_at.asc()).all()
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        task = Task(
            name=data['name'],
            description=data.get('description', ''),
            agent_id=data.get('agent_id'),
            workflow_execution_id=data.get('workflow_execution_id'),
            priority=data.get('priority', 5),
            input_data=json.dumps(data.get('input_data', {}))
        )
        
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        task.name = data.get('name', task.name)
        task.description = data.get('description', task.description)
        task.agent_id = data.get('agent_id', task.agent_id)
        task.status = data.get('status', task.status)
        task.priority = data.get('priority', task.priority)
        
        if 'input_data' in data:
            task.input_data = json.dumps(data['input_data'])
        if 'output_data' in data:
            task.output_data = json.dumps(data['output_data'])
        
        task.error_message = data.get('error_message', task.error_message)
        
        # Update timestamps based on status
        if data.get('status') == 'assigned' and not task.assigned_at:
            task.assigned_at = datetime.utcnow()
        elif data.get('status') == 'running' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif data.get('status') in ['completed', 'failed'] and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/tasks/<int:task_id>/assign/<int:agent_id>', methods=['POST'])
def assign_task(task_id, agent_id):
    """Assign a task to an agent"""
    try:
        task = Task.query.get_or_404(task_id)
        task.agent_id = agent_id
        task.status = 'assigned'
        task.assigned_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

