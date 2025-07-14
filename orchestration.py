from flask import Blueprint, request, jsonify
from src.services.orchestration_engine import OrchestrationEngine
from src.services.agent_registry import AgentRegistry

orchestration_bp = Blueprint('orchestration', __name__)

# Global instances (in production, these would be properly managed)
orchestration_engine = OrchestrationEngine()
agent_registry = AgentRegistry()

# Start the orchestration engine
orchestration_engine.start()

@orchestration_bp.route('/orchestration/agents/register', methods=['POST'])
def register_agent():
    """Register a new agent with the orchestration engine."""
    try:
        data = request.get_json()
        
        framework = data['framework']
        agent_config = data['config']
        
        # Register with orchestration engine
        agent_id = orchestration_engine.register_agent(framework, agent_config)
        
        # Register with discovery service
        agent_info = {
            'name': agent_config.get('name', f'{framework}_agent'),
            'framework': framework,
            'capabilities': agent_config.get('capabilities', []),
            'tags': agent_config.get('tags', []),
            'description': agent_config.get('description', ''),
            'version': agent_config.get('version', '1.0'),
            'metadata': agent_config.get('metadata', {})
        }
        
        agent_registry.register_agent(agent_id, agent_info)
        
        return jsonify({
            'agent_id': agent_id,
            'status': 'registered',
            'framework': framework
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/unregister', methods=['DELETE'])
def unregister_agent(agent_id):
    """Unregister an agent from the orchestration engine."""
    try:
        # Unregister from orchestration engine
        success1 = orchestration_engine.unregister_agent(agent_id)
        
        # Unregister from discovery service
        success2 = agent_registry.unregister_agent(agent_id)
        
        if success1 and success2:
            return jsonify({'message': 'Agent unregistered successfully'})
        else:
            return jsonify({'error': 'Agent not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/start', methods=['POST'])
def start_agent(agent_id):
    """Start an agent."""
    try:
        success = orchestration_engine.start_agent(agent_id)
        
        if success:
            agent_registry.update_agent_status(agent_id, 'active', 'healthy')
            return jsonify({'message': 'Agent started successfully'})
        else:
            return jsonify({'error': 'Failed to start agent'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/stop', methods=['POST'])
def stop_agent(agent_id):
    """Stop an agent."""
    try:
        success = orchestration_engine.stop_agent(agent_id)
        
        if success:
            agent_registry.update_agent_status(agent_id, 'inactive')
            return jsonify({'message': 'Agent stopped successfully'})
        else:
            return jsonify({'error': 'Failed to stop agent'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/pause', methods=['POST'])
def pause_agent(agent_id):
    """Pause an agent."""
    try:
        success = orchestration_engine.pause_agent(agent_id)
        
        if success:
            agent_registry.update_agent_status(agent_id, 'paused')
            return jsonify({'message': 'Agent paused successfully'})
        else:
            return jsonify({'error': 'Failed to pause agent'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/resume', methods=['POST'])
def resume_agent(agent_id):
    """Resume a paused agent."""
    try:
        success = orchestration_engine.resume_agent(agent_id)
        
        if success:
            agent_registry.update_agent_status(agent_id, 'active', 'healthy')
            return jsonify({'message': 'Agent resumed successfully'})
        else:
            return jsonify({'error': 'Failed to resume agent'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/status', methods=['GET'])
def get_agent_status(agent_id):
    """Get agent status."""
    try:
        status = orchestration_engine.get_agent_status(agent_id)
        
        if status:
            return jsonify({
                'agent_id': agent_id,
                'status': status.value if hasattr(status, 'value') else str(status)
            })
        else:
            return jsonify({'error': 'Agent not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/metrics', methods=['GET'])
def get_agent_metrics(agent_id):
    """Get agent metrics."""
    try:
        metrics = orchestration_engine.get_agent_metrics(agent_id)
        
        if metrics:
            return jsonify(metrics)
        else:
            return jsonify({'error': 'Agent not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/tasks/submit', methods=['POST'])
def submit_task():
    """Submit a task for execution."""
    try:
        data = request.get_json()
        
        agent_id = data['agent_id']
        task_data = data['task_data']
        priority = data.get('priority', 5)
        
        task_id = orchestration_engine.submit_task(agent_id, task_data, priority)
        
        return jsonify({
            'task_id': task_id,
            'status': 'queued',
            'agent_id': agent_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """Get task status."""
    try:
        status = orchestration_engine.get_task_status(task_id)
        
        if status:
            return jsonify({
                'task_id': task_id,
                'status': status
            })
        else:
            return jsonify({'error': 'Task not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/tasks/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """Get task result."""
    try:
        result = orchestration_engine.get_task_result(task_id)
        
        if result:
            return jsonify({
                'task_id': task_id,
                'result': result
            })
        else:
            return jsonify({'error': 'Task not completed or not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/messages/send', methods=['POST'])
def send_inter_agent_message():
    """Send a message between agents."""
    try:
        data = request.get_json()
        
        from_agent_id = data['from_agent_id']
        to_agent_id = data['to_agent_id']
        message = data['message']
        
        success = orchestration_engine.send_inter_agent_message(from_agent_id, to_agent_id, message)
        
        if success:
            return jsonify({'message': 'Message sent successfully'})
        else:
            return jsonify({'error': 'Failed to send message'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents', methods=['GET'])
def list_agents():
    """List all registered agents."""
    try:
        agents = orchestration_engine.list_agents()
        return jsonify(agents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/health', methods=['GET'])
def get_system_health():
    """Get system health information."""
    try:
        health = orchestration_engine.get_system_health()
        return jsonify(health)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/orchestration/agents/<agent_id>/config', methods=['PUT'])
def update_agent_config(agent_id):
    """Update agent configuration."""
    try:
        data = request.get_json()
        config_updates = data['config_updates']
        
        success = orchestration_engine.update_agent_config(agent_id, config_updates)
        
        if success:
            return jsonify({'message': 'Agent configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to update agent configuration'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Agent Discovery Routes

@orchestration_bp.route('/discovery/agents/search', methods=['POST'])
def search_agents():
    """Search for agents using multiple criteria."""
    try:
        query = request.get_json()
        agents = agent_registry.search_agents(query)
        return jsonify(agents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/agents/capability/<capability>', methods=['GET'])
def find_agents_by_capability(capability):
    """Find agents by capability."""
    try:
        agents = agent_registry.find_agents_by_capability(capability)
        return jsonify(agents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/agents/framework/<framework>', methods=['GET'])
def find_agents_by_framework(framework):
    """Find agents by framework."""
    try:
        agents = agent_registry.find_agents_by_framework(framework)
        return jsonify(agents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/agents/tag/<tag>', methods=['GET'])
def find_agents_by_tag(tag):
    """Find agents by tag."""
    try:
        agents = agent_registry.find_agents_by_tag(tag)
        return jsonify(agents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/capabilities', methods=['GET'])
def get_capabilities_catalog():
    """Get capabilities catalog."""
    try:
        catalog = agent_registry.get_capabilities_catalog()
        return jsonify(catalog)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/frameworks/summary', methods=['GET'])
def get_framework_summary():
    """Get framework summary."""
    try:
        summary = agent_registry.get_framework_summary()
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/discovery/agents/<agent_id>', methods=['GET'])
def get_agent_discovery_info(agent_id):
    """Get agent discovery information."""
    try:
        agent_info = agent_registry.get_agent_info(agent_id)
        
        if agent_info:
            return jsonify(agent_info)
        else:
            return jsonify({'error': 'Agent not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

