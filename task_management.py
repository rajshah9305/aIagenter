from flask import Blueprint, request, jsonify
from src.services.task_distribution import TaskDistributionEngine, TaskPriority, TaskStatus
from src.services.workflow_engine import WorkflowEngine, WorkflowDefinition, WorkflowNode, WorkflowConnection, NodeType
import json

task_management_bp = Blueprint('task_management', __name__)

# Global instances (in production, these would be properly managed)
task_engine = TaskDistributionEngine()
workflow_engine = WorkflowEngine(task_engine)

# Start engines
task_engine.start()
workflow_engine.start()

@task_management_bp.route('/tasks', methods=['POST'])
def submit_task():
    """Submit a new task for execution."""
    try:
        data = request.get_json()
        
        task_data = data.get('task_data', {})
        agent_id = data.get('agent_id')
        priority = TaskPriority(data.get('priority', 'normal'))
        timeout_seconds = data.get('timeout_seconds', 300)
        dependencies = data.get('dependencies', [])
        
        task_id = task_engine.submit_task(
            task_data=task_data,
            agent_id=agent_id,
            priority=priority,
            timeout_seconds=timeout_seconds,
            dependencies=dependencies
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task submitted successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@task_management_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of a specific task."""
    try:
        task = task_engine.task_queue.get_task(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
            
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/tasks/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """Get the result of a completed task."""
    try:
        result = task_engine.get_task_result(task_id)
        
        if result is None:
            return jsonify({
                'success': False,
                'error': 'Task not found or not completed'
            }), 404
            
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """Cancel a pending or queued task."""
    try:
        success = task_engine.cancel_task(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Task cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Task cannot be cancelled'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/tasks/agent/<agent_id>', methods=['GET'])
def get_agent_tasks(agent_id):
    """Get all tasks for a specific agent."""
    try:
        tasks = task_engine.get_agent_tasks(agent_id)
        
        return jsonify({
            'success': True,
            'tasks': tasks
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/tasks/stats', methods=['GET'])
def get_task_stats():
    """Get system-wide task statistics."""
    try:
        stats = task_engine.get_system_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/agents/<agent_id>/capabilities', methods=['POST'])
def register_agent_capabilities(agent_id):
    """Register capabilities for an agent."""
    try:
        data = request.get_json()
        capabilities = data.get('capabilities', [])
        
        task_engine.register_agent_capabilities(agent_id, capabilities)
        
        return jsonify({
            'success': True,
            'message': 'Agent capabilities registered successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# Workflow Management Routes

@task_management_bp.route('/workflows', methods=['POST'])
def create_workflow():
    """Create a new workflow definition."""
    try:
        data = request.get_json()
        
        workflow_def = WorkflowDefinition(
            name=data.get('name', ''),
            description=data.get('description', ''),
            version=data.get('version', '1.0')
        )
        
        # Add nodes
        for node_data in data.get('nodes', []):
            node = WorkflowNode(
                node_id=node_data['id'],
                node_type=NodeType(node_data['type']),
                name=node_data['name'],
                config=node_data.get('config', {}),
                position=node_data.get('position', {'x': 0, 'y': 0})
            )
            workflow_def.add_node(node)
            
        # Add connections
        for conn_data in data.get('connections', []):
            connection = WorkflowConnection(
                from_node_id=conn_data['from_node_id'],
                to_node_id=conn_data['to_node_id'],
                condition=conn_data.get('condition'),
                label=conn_data.get('label')
            )
            workflow_def.add_connection(connection)
            
        # Register workflow
        success = workflow_engine.register_workflow(workflow_def)
        
        if success:
            return jsonify({
                'success': True,
                'workflow_id': workflow_def.id,
                'message': 'Workflow created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Workflow validation failed'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@task_management_bp.route('/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get a workflow definition."""
    try:
        workflow_def = workflow_engine.workflow_definitions.get(workflow_id)
        
        if not workflow_def:
            return jsonify({
                'success': False,
                'error': 'Workflow not found'
            }), 404
            
        return jsonify({
            'success': True,
            'workflow': workflow_def.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/workflows', methods=['GET'])
def list_workflows():
    """List all workflow definitions."""
    try:
        workflows = []
        for workflow_def in workflow_engine.workflow_definitions.values():
            workflows.append({
                'id': workflow_def.id,
                'name': workflow_def.name,
                'description': workflow_def.description,
                'version': workflow_def.version,
                'node_count': len(workflow_def.nodes),
                'created_at': workflow_def.created_at.isoformat(),
                'updated_at': workflow_def.updated_at.isoformat()
            })
            
        return jsonify({
            'success': True,
            'workflows': workflows
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute a workflow."""
    try:
        data = request.get_json() or {}
        input_data = data.get('input_data', {})
        
        execution_id = workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data
        )
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'message': 'Workflow execution started'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@task_management_bp.route('/executions/<execution_id>', methods=['GET'])
def get_execution_status(execution_id):
    """Get the status of a workflow execution."""
    try:
        execution = workflow_engine.executions.get(execution_id)
        
        if not execution:
            return jsonify({
                'success': False,
                'error': 'Execution not found'
            }), 404
            
        return jsonify({
            'success': True,
            'execution': execution.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/executions/<execution_id>/progress', methods=['GET'])
def get_execution_progress(execution_id):
    """Get the progress of a workflow execution."""
    try:
        progress = workflow_engine.get_execution_progress(execution_id)
        
        if progress is None:
            return jsonify({
                'success': False,
                'error': 'Execution not found'
            }), 404
            
        return jsonify({
            'success': True,
            'progress': progress
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/executions/<execution_id>/pause', methods=['POST'])
def pause_execution(execution_id):
    """Pause a workflow execution."""
    try:
        success = workflow_engine.pause_execution(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Execution paused successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Execution not found or cannot be paused'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/executions/<execution_id>/resume', methods=['POST'])
def resume_execution(execution_id):
    """Resume a paused workflow execution."""
    try:
        success = workflow_engine.resume_execution(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Execution resumed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Execution not found or cannot be resumed'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/executions/<execution_id>/cancel', methods=['POST'])
def cancel_execution(execution_id):
    """Cancel a workflow execution."""
    try:
        success = workflow_engine.cancel_execution(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Execution cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Execution not found or cannot be cancelled'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@task_management_bp.route('/executions', methods=['GET'])
def list_executions():
    """List all workflow executions."""
    try:
        executions = []
        for execution in workflow_engine.executions.values():
            executions.append({
                'id': execution.id,
                'workflow_id': execution.workflow_def.id if execution.workflow_def else None,
                'workflow_name': execution.workflow_def.name if execution.workflow_def else None,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'progress': execution.get_progress()
            })
            
        return jsonify({
            'success': True,
            'executions': executions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

