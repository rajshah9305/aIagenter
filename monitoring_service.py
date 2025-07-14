import threading
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

class MetricsCollector:
    """
    Collects and aggregates metrics from agents and framework connectors.
    """
    
    def __init__(self, retention_hours: int = 24):
        self.metrics_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = {}
        self.retention_hours = retention_hours
        self.is_running = False
        self.collector_thread = None
        self.aggregation_thread = None
        
    def start(self):
        """Start the metrics collection service."""
        if self.is_running:
            return
            
        self.is_running = True
        self.collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.aggregation_thread = threading.Thread(target=self._aggregation_loop, daemon=True)
        
        self.collector_thread.start()
        self.aggregation_thread.start()
        
        print("Metrics collector started")
    
    def stop(self):
        """Stop the metrics collection service."""
        self.is_running = False
        
        if self.collector_thread:
            self.collector_thread.join(timeout=5)
        if self.aggregation_thread:
            self.aggregation_thread.join(timeout=5)
            
        print("Metrics collector stopped")
    
    def record_metric(self, agent_id: str, metric_name: str, value: float, 
                     metric_type: str = 'gauge', unit: str = None, tags: Dict[str, str] = None):
        """
        Record a metric value.
        
        Args:
            agent_id: Agent identifier
            metric_name: Name of the metric
            value: Metric value
            metric_type: Type of metric (gauge, counter, histogram)
            unit: Unit of measurement
            tags: Additional tags for the metric
        """
        metric_key = f"{agent_id}.{metric_name}"
        
        metric_record = {
            'timestamp': datetime.utcnow(),
            'agent_id': agent_id,
            'metric_name': metric_name,
            'value': value,
            'type': metric_type,
            'unit': unit,
            'tags': tags or {}
        }
        
        self.metrics_store[metric_key].append(metric_record)
    
    def get_metrics(self, agent_id: str = None, metric_name: str = None, 
                   start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Retrieve metrics based on filters.
        
        Args:
            agent_id: Filter by agent ID
            metric_name: Filter by metric name
            start_time: Start time for filtering
            end_time: End time for filtering
            
        Returns:
            metrics: List of metric records
        """
        results = []
        
        for metric_key, metric_records in self.metrics_store.items():
            for record in metric_records:
                # Apply filters
                if agent_id and record['agent_id'] != agent_id:
                    continue
                if metric_name and record['metric_name'] != metric_name:
                    continue
                if start_time and record['timestamp'] < start_time:
                    continue
                if end_time and record['timestamp'] > end_time:
                    continue
                
                results.append(record)
        
        return sorted(results, key=lambda x: x['timestamp'])
    
    def get_aggregated_metrics(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Get aggregated metrics for an agent or all agents.
        
        Args:
            agent_id: Agent ID to filter by (optional)
            
        Returns:
            aggregated_metrics: Dictionary of aggregated metric data
        """
        if agent_id:
            return self.aggregated_metrics.get(agent_id, {})
        
        return dict(self.aggregated_metrics)
    
    def get_real_time_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the latest metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            latest_metrics: Dictionary of latest metric values
        """
        latest_metrics = {}
        
        for metric_key, metric_records in self.metrics_store.items():
            if metric_records and metric_records[-1]['agent_id'] == agent_id:
                latest_record = metric_records[-1]
                latest_metrics[latest_record['metric_name']] = {
                    'value': latest_record['value'],
                    'timestamp': latest_record['timestamp'].isoformat(),
                    'unit': latest_record['unit'],
                    'type': latest_record['type']
                }
        
        return latest_metrics
    
    def _collection_loop(self):
        """Main collection loop for periodic metric gathering."""
        while self.is_running:
            try:
                # Clean up old metrics
                self._cleanup_old_metrics()
                
                time.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                print(f"Error in metrics collection loop: {e}")
                time.sleep(5)
    
    def _aggregation_loop(self):
        """Aggregation loop for computing statistical summaries."""
        while self.is_running:
            try:
                self._compute_aggregations()
                time.sleep(30)  # Compute aggregations every 30 seconds
                
            except Exception as e:
                print(f"Error in metrics aggregation loop: {e}")
                time.sleep(5)
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for metric_key in list(self.metrics_store.keys()):
            metric_records = self.metrics_store[metric_key]
            
            # Remove old records
            while metric_records and metric_records[0]['timestamp'] < cutoff_time:
                metric_records.popleft()
            
            # Remove empty metric keys
            if not metric_records:
                del self.metrics_store[metric_key]
    
    def _compute_aggregations(self):
        """Compute aggregated statistics for metrics."""
        agent_metrics = defaultdict(lambda: defaultdict(list))
        
        # Group metrics by agent and metric name
        for metric_key, metric_records in self.metrics_store.items():
            for record in metric_records:
                agent_id = record['agent_id']
                metric_name = record['metric_name']
                agent_metrics[agent_id][metric_name].append(record['value'])
        
        # Compute aggregations
        for agent_id, metrics in agent_metrics.items():
            aggregated = {}
            
            for metric_name, values in metrics.items():
                if values:
                    aggregated[metric_name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'latest': values[-1] if values else None,
                        'trend': self._calculate_trend(values)
                    }
                    
                    if len(values) > 1:
                        aggregated[metric_name]['stddev'] = statistics.stdev(values)
            
            self.aggregated_metrics[agent_id] = aggregated
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return 'stable'
        
        # Simple trend calculation based on first and last values
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return 'stable'
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return 'increasing'
        elif change_percent < -5:
            return 'decreasing'
        else:
            return 'stable'

class AlertingSystem:
    """
    Alerting system with rule-based and anomaly detection capabilities.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.alert_callbacks: List[Callable] = []
        self.is_running = False
        self.alerting_thread = None
        
    def start(self):
        """Start the alerting system."""
        if self.is_running:
            return
            
        self.is_running = True
        self.alerting_thread = threading.Thread(target=self._alerting_loop, daemon=True)
        self.alerting_thread.start()
        
        print("Alerting system started")
    
    def stop(self):
        """Stop the alerting system."""
        self.is_running = False
        
        if self.alerting_thread:
            self.alerting_thread.join(timeout=5)
            
        print("Alerting system stopped")
    
    def add_alert_rule(self, rule: Dict[str, Any]) -> str:
        """
        Add a new alert rule.
        
        Args:
            rule: Alert rule configuration
                - name: Rule name
                - condition: Alert condition (e.g., 'metric > threshold')
                - metric_name: Metric to monitor
                - threshold: Threshold value
                - operator: Comparison operator (>, <, ==, !=)
                - agent_id: Specific agent ID (optional)
                - severity: Alert severity (low, medium, high, critical)
                - cooldown_minutes: Minimum time between alerts
                
        Returns:
            rule_id: Unique identifier for the rule
        """
        rule_id = f"rule_{int(time.time() * 1000)}"
        rule['id'] = rule_id
        rule['created_at'] = datetime.utcnow()
        rule['last_triggered'] = None
        
        self.alert_rules.append(rule)
        return rule_id
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        for i, rule in enumerate(self.alert_rules):
            if rule['id'] == rule_id:
                del self.alert_rules[i]
                return True
        return False
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback function to be called when alerts are triggered."""
        self.alert_callbacks.append(callback)
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        return sorted(self.alert_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def _alerting_loop(self):
        """Main alerting loop."""
        while self.is_running:
            try:
                self._check_alert_rules()
                time.sleep(10)  # Check alerts every 10 seconds
                
            except Exception as e:
                print(f"Error in alerting loop: {e}")
                time.sleep(5)
    
    def _check_alert_rules(self):
        """Check all alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                if self._should_check_rule(rule):
                    if self._evaluate_rule(rule):
                        self._trigger_alert(rule)
                        
            except Exception as e:
                print(f"Error checking alert rule {rule.get('name', 'unknown')}: {e}")
    
    def _should_check_rule(self, rule: Dict[str, Any]) -> bool:
        """Check if enough time has passed since last alert for this rule."""
        if not rule.get('last_triggered'):
            return True
        
        cooldown_minutes = rule.get('cooldown_minutes', 5)
        time_since_last = datetime.utcnow() - rule['last_triggered']
        
        return time_since_last.total_seconds() >= (cooldown_minutes * 60)
    
    def _evaluate_rule(self, rule: Dict[str, Any]) -> bool:
        """Evaluate if an alert rule condition is met."""
        metric_name = rule['metric_name']
        threshold = rule['threshold']
        operator = rule['operator']
        agent_id = rule.get('agent_id')
        
        # Get recent metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)  # Look at last 5 minutes
        
        metrics = self.metrics_collector.get_metrics(
            agent_id=agent_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time
        )
        
        if not metrics:
            return False
        
        # Use the latest metric value
        latest_value = metrics[-1]['value']
        
        # Evaluate condition
        if operator == '>':
            return latest_value > threshold
        elif operator == '<':
            return latest_value < threshold
        elif operator == '==':
            return latest_value == threshold
        elif operator == '!=':
            return latest_value != threshold
        elif operator == '>=':
            return latest_value >= threshold
        elif operator == '<=':
            return latest_value <= threshold
        
        return False
    
    def _trigger_alert(self, rule: Dict[str, Any]):
        """Trigger an alert."""
        alert = {
            'id': f"alert_{int(time.time() * 1000)}",
            'rule_id': rule['id'],
            'rule_name': rule['name'],
            'severity': rule.get('severity', 'medium'),
            'message': self._generate_alert_message(rule),
            'timestamp': datetime.utcnow(),
            'agent_id': rule.get('agent_id'),
            'metric_name': rule['metric_name'],
            'status': 'active'
        }
        
        # Record alert
        self.alert_history.append(alert)
        rule['last_triggered'] = datetime.utcnow()
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error calling alert callback: {e}")
        
        print(f"ALERT: {alert['message']}")
    
    def _generate_alert_message(self, rule: Dict[str, Any]) -> str:
        """Generate a human-readable alert message."""
        agent_part = f" for agent {rule['agent_id']}" if rule.get('agent_id') else ""
        return (f"{rule['name']}: {rule['metric_name']} {rule['operator']} "
                f"{rule['threshold']}{agent_part}")

class RealTimeMonitor:
    """
    Real-time monitoring service that provides live updates via WebSocket.
    """
    
    def __init__(self, metrics_collector: MetricsCollector, alerting_system: AlertingSystem):
        self.metrics_collector = metrics_collector
        self.alerting_system = alerting_system
        self.websocket_clients: List[Any] = []
        self.is_running = False
        self.broadcast_thread = None
        
    def start(self):
        """Start the real-time monitoring service."""
        if self.is_running:
            return
            
        self.is_running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        
        print("Real-time monitor started")
    
    def stop(self):
        """Stop the real-time monitoring service."""
        self.is_running = False
        
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=5)
            
        print("Real-time monitor stopped")
    
    def add_websocket_client(self, client):
        """Add a WebSocket client for real-time updates."""
        self.websocket_clients.append(client)
    
    def remove_websocket_client(self, client):
        """Remove a WebSocket client."""
        if client in self.websocket_clients:
            self.websocket_clients.remove(client)
    
    def _broadcast_loop(self):
        """Main broadcast loop for sending real-time updates."""
        while self.is_running:
            try:
                # Prepare real-time data
                data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': self._get_dashboard_metrics(),
                    'alerts': self._get_recent_alerts(),
                    'system_health': self._get_system_health()
                }
                
                # Broadcast to all connected clients
                self._broadcast_to_clients(data)
                
                time.sleep(5)  # Broadcast every 5 seconds
                
            except Exception as e:
                print(f"Error in real-time broadcast loop: {e}")
                time.sleep(5)
    
    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics formatted for dashboard display."""
        # This would be implemented to return formatted metrics
        # for the dashboard visualization
        return {
            'agent_count': len(self.metrics_collector.aggregated_metrics),
            'active_alerts': len([a for a in self.alerting_system.alert_history 
                                if a['status'] == 'active']),
            'total_tasks': 0,  # Would be retrieved from orchestration engine
            'avg_response_time': 0.0  # Would be calculated from metrics
        }
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts for real-time display."""
        return self.alerting_system.get_alert_history(limit=10)
    
    def _get_system_health(self) -> Dict[str, str]:
        """Get overall system health status."""
        return {
            'status': 'healthy',
            'metrics_collector': 'running' if self.metrics_collector.is_running else 'stopped',
            'alerting_system': 'running' if self.alerting_system.is_running else 'stopped'
        }
    
    def _broadcast_to_clients(self, data: Dict[str, Any]):
        """Broadcast data to all connected WebSocket clients."""
        # This would be implemented with actual WebSocket broadcasting
        # For now, we'll just print the data structure
        pass

