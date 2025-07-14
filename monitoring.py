from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
from src.services.monitoring_service import MetricsCollector, AlertingSystem, RealTimeMonitor
from src.services.communication_service import InterAgentCommunicationProtocol, MessageType, MessagePriority

monitoring_bp = Blueprint('monitoring', __name__)

# Global instances (in production, these would be properly managed)
metrics_collector = MetricsCollector()
alerting_system = AlertingSystem(metrics_collector)
real_time_monitor = RealTimeMonitor(metrics_collector, alerting_system)
iacp = InterAgentCommunicationProtocol()

# Start services
metrics_collector.start()
alerting_system.start()
real_time_monitor.start()
iacp.start()

# Metrics endpoints

@monitoring_bp.route('/monitoring/metrics/record', methods=['POST'])
def record_metric():
    """Record a new metric value."""
    try:
        data = request.get_json()
        
        metrics_collector.record_metric(
            agent_id=data['agent_id'],
            metric_name=data['metric_name'],
            value=data['value'],
            metric_type=data.get('metric_type', 'gauge'),
            unit=data.get('unit'),
            tags=data.get('tags', {})
        )
        
        return jsonify({'message': 'Metric recorded successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/metrics', methods=['GET'])
def get_metrics():
    """Get metrics with optional filtering."""
    try:
        agent_id = request.args.get('agent_id')
        metric_name = request.args.get('metric_name')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        start_time = None
        end_time = None
        
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str)
        
        metrics = metrics_collector.get_metrics(
            agent_id=agent_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time
        )
        
        # Convert datetime objects to ISO strings for JSON serialization
        serialized_metrics = []
        for metric in metrics:
            serialized_metric = dict(metric)
            serialized_metric['timestamp'] = metric['timestamp'].isoformat()
            serialized_metrics.append(serialized_metric)
        
        return jsonify(serialized_metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/metrics/aggregated', methods=['GET'])
def get_aggregated_metrics():
    """Get aggregated metrics."""
    try:
        agent_id = request.args.get('agent_id')
        aggregated = metrics_collector.get_aggregated_metrics(agent_id)
        return jsonify(aggregated)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/metrics/realtime/<agent_id>', methods=['GET'])
def get_realtime_metrics(agent_id):
    """Get real-time metrics for an agent."""
    try:
        metrics = metrics_collector.get_real_time_metrics(agent_id)
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alerting endpoints

@monitoring_bp.route('/monitoring/alerts/rules', methods=['POST'])
def create_alert_rule():
    """Create a new alert rule."""
    try:
        rule = request.get_json()
        rule_id = alerting_system.add_alert_rule(rule)
        
        return jsonify({
            'rule_id': rule_id,
            'message': 'Alert rule created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/alerts/rules/<rule_id>', methods=['DELETE'])
def delete_alert_rule(rule_id):
    """Delete an alert rule."""
    try:
        success = alerting_system.remove_alert_rule(rule_id)
        
        if success:
            return jsonify({'message': 'Alert rule deleted successfully'})
        else:
            return jsonify({'error': 'Alert rule not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history."""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = alerting_system.get_alert_history(limit)
        
        # Convert datetime objects to ISO strings
        serialized_history = []
        for alert in history:
            serialized_alert = dict(alert)
            serialized_alert['timestamp'] = alert['timestamp'].isoformat()
            serialized_history.append(serialized_alert)
        
        return jsonify(serialized_history)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Communication endpoints

@monitoring_bp.route('/monitoring/communication/register', methods=['POST'])
def register_agent_communication():
    """Register an agent with the communication protocol."""
    try:
        data = request.get_json()
        agent_id = data['agent_id']
        
        iacp.register_agent(agent_id)
        
        return jsonify({'message': 'Agent registered for communication'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/send', methods=['POST'])
def send_inter_agent_message():
    """Send a message between agents."""
    try:
        data = request.get_json()
        
        message_type = MessageType(data.get('message_type', 'request'))
        priority = MessagePriority(data.get('priority', 2))
        
        message_id = iacp.send_message(
            from_agent_id=data['from_agent_id'],
            to_agent_id=data['to_agent_id'],
            content=data['content'],
            message_type=message_type,
            priority=priority,
            ttl_seconds=data.get('ttl_seconds', 300),
            requires_ack=data.get('requires_ack', False)
        )
        
        return jsonify({
            'message_id': message_id,
            'status': 'sent'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/messages/<agent_id>', methods=['GET'])
def get_agent_messages(agent_id):
    """Get pending messages for an agent."""
    try:
        limit = request.args.get('limit', 10, type=int)
        messages = iacp.get_messages(agent_id, limit)
        
        # Convert messages to dictionaries
        serialized_messages = [msg.to_dict() for msg in messages]
        
        return jsonify(serialized_messages)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/acknowledge', methods=['POST'])
def acknowledge_message():
    """Acknowledge a message."""
    try:
        data = request.get_json()
        
        success = iacp.acknowledge_message(
            message_id=data['message_id'],
            agent_id=data['agent_id']
        )
        
        if success:
            return jsonify({'message': 'Message acknowledged'})
        else:
            return jsonify({'error': 'Failed to acknowledge message'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/broadcast', methods=['POST'])
def send_broadcast_message():
    """Send a broadcast message to a topic."""
    try:
        data = request.get_json()
        
        priority = MessagePriority(data.get('priority', 2))
        
        message_ids = iacp.send_broadcast(
            from_agent_id=data['from_agent_id'],
            topic=data['topic'],
            content=data['content'],
            priority=priority
        )
        
        return jsonify({
            'message_ids': message_ids,
            'recipients': len(message_ids)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/subscribe', methods=['POST'])
def subscribe_to_topic():
    """Subscribe an agent to a topic."""
    try:
        data = request.get_json()
        
        iacp.subscribe_to_topic(
            agent_id=data['agent_id'],
            topic=data['topic']
        )
        
        return jsonify({'message': 'Subscribed to topic successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/unsubscribe', methods=['POST'])
def unsubscribe_from_topic():
    """Unsubscribe an agent from a topic."""
    try:
        data = request.get_json()
        
        iacp.unsubscribe_from_topic(
            agent_id=data['agent_id'],
            topic=data['topic']
        )
        
        return jsonify({'message': 'Unsubscribed from topic successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/stats', methods=['GET'])
def get_communication_stats():
    """Get communication statistics."""
    try:
        stats = iacp.get_communication_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/communication/message/<message_id>/status', methods=['GET'])
def get_message_status(message_id):
    """Get the status of a message."""
    try:
        status = iacp.get_message_status(message_id)
        
        if status:
            return jsonify({
                'message_id': message_id,
                'status': status.value
            })
        else:
            return jsonify({'error': 'Message not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard endpoints

@monitoring_bp.route('/monitoring/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview data."""
    try:
        # Get aggregated metrics for all agents
        all_metrics = metrics_collector.get_aggregated_metrics()
        
        # Get recent alerts
        recent_alerts = alerting_system.get_alert_history(limit=5)
        
        # Get communication stats
        comm_stats = iacp.get_communication_stats()
        
        overview = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_agents': len(all_metrics),
            'active_alerts': len([a for a in recent_alerts if a['status'] == 'active']),
            'total_messages': comm_stats['total_messages'],
            'pending_messages': comm_stats['pending_messages'],
            'system_health': {
                'metrics_collector': 'running' if metrics_collector.is_running else 'stopped',
                'alerting_system': 'running' if alerting_system.is_running else 'stopped',
                'communication_protocol': 'running' if iacp.is_running else 'stopped'
            }
        }
        
        return jsonify(overview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/dashboard/agents', methods=['GET'])
def get_dashboard_agents():
    """Get agent data for dashboard."""
    try:
        all_metrics = metrics_collector.get_aggregated_metrics()
        
        agents_data = []
        for agent_id, metrics in all_metrics.items():
            agent_data = {
                'id': agent_id,
                'metrics': metrics,
                'real_time': metrics_collector.get_real_time_metrics(agent_id)
            }
            agents_data.append(agent_data)
        
        return jsonify(agents_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events (would be implemented with Flask-SocketIO)

def init_websocket_events(socketio):
    """Initialize WebSocket events for real-time updates."""
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('status', {'msg': 'Connected to AgentOrchestra monitoring'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('subscribe_metrics')
    def handle_subscribe_metrics(data):
        agent_id = data.get('agent_id')
        if agent_id:
            join_room(f'metrics_{agent_id}')
            emit('status', {'msg': f'Subscribed to metrics for agent {agent_id}'})
    
    @socketio.on('unsubscribe_metrics')
    def handle_unsubscribe_metrics(data):
        agent_id = data.get('agent_id')
        if agent_id:
            leave_room(f'metrics_{agent_id}')
            emit('status', {'msg': f'Unsubscribed from metrics for agent {agent_id}'})
    
    @socketio.on('subscribe_alerts')
    def handle_subscribe_alerts():
        join_room('alerts')
        emit('status', {'msg': 'Subscribed to alerts'})
    
    @socketio.on('unsubscribe_alerts')
    def handle_unsubscribe_alerts():
        leave_room('alerts')
        emit('status', {'msg': 'Unsubscribed from alerts'})

# Alert callback for real-time notifications
def alert_callback(alert):
    """Callback function for real-time alert notifications."""
    # In a real implementation, this would emit to WebSocket clients
    print(f"Real-time alert: {alert['message']}")

# Register alert callback
alerting_system.add_alert_callback(alert_callback)

