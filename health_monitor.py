import threading
import time
import requests
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class HealthCheck:
    """Represents a health check configuration."""
    
    def __init__(self, check_id: str, name: str, check_type: str, 
                 config: Dict[str, Any], interval_seconds: int = 30,
                 timeout_seconds: int = 10, retries: int = 3):
        self.id = check_id
        self.name = name
        self.type = check_type
        self.config = config
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.last_check = None
        self.last_status = HealthStatus.UNKNOWN
        self.last_error = None
        self.consecutive_failures = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert health check to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'config': self.config,
            'interval_seconds': self.interval_seconds,
            'timeout_seconds': self.timeout_seconds,
            'retries': self.retries,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_status': self.last_status.value,
            'last_error': self.last_error,
            'consecutive_failures': self.consecutive_failures
        }

class AgentHealth:
    """Tracks health status for an agent."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.overall_status = HealthStatus.UNKNOWN
        self.health_checks = {}  # check_id -> HealthCheck
        self.status_history = deque(maxlen=100)  # Recent status history
        self.last_seen = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
    def add_health_check(self, health_check: HealthCheck):
        """Add a health check for this agent."""
        self.health_checks[health_check.id] = health_check
        
    def update_check_status(self, check_id: str, status: HealthStatus, error: str = None):
        """Update the status of a specific health check."""
        if check_id in self.health_checks:
            check = self.health_checks[check_id]
            check.last_check = datetime.utcnow()
            check.last_status = status
            check.last_error = error
            
            if status != HealthStatus.HEALTHY:
                check.consecutive_failures += 1
            else:
                check.consecutive_failures = 0
                
            self._update_overall_status()
            
    def _update_overall_status(self):
        """Update overall agent health status based on individual checks."""
        if not self.health_checks:
            self.overall_status = HealthStatus.UNKNOWN
            return
            
        statuses = [check.last_status for check in self.health_checks.values()]
        
        # If any check is critical, overall status is critical
        if HealthStatus.CRITICAL in statuses:
            new_status = HealthStatus.CRITICAL
        # If any check is warning, overall status is warning
        elif HealthStatus.WARNING in statuses:
            new_status = HealthStatus.WARNING
        # If all checks are healthy, overall status is healthy
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            new_status = HealthStatus.HEALTHY
        else:
            new_status = HealthStatus.UNKNOWN
            
        # Record status change
        if new_status != self.overall_status:
            self.status_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'old_status': self.overall_status.value,
                'new_status': new_status.value
            })
            self.overall_status = new_status
            
    def needs_recovery(self) -> bool:
        """Check if agent needs recovery action."""
        return (self.overall_status == HealthStatus.CRITICAL and 
                self.recovery_attempts < self.max_recovery_attempts)
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent health to dictionary."""
        return {
            'agent_id': self.agent_id,
            'overall_status': self.overall_status.value,
            'health_checks': {check_id: check.to_dict() 
                            for check_id, check in self.health_checks.items()},
            'status_history': list(self.status_history),
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'recovery_attempts': self.recovery_attempts,
            'max_recovery_attempts': self.max_recovery_attempts
        }

class HealthMonitor:
    """Main health monitoring service."""
    
    def __init__(self):
        self.agent_health = {}  # agent_id -> AgentHealth
        self.check_handlers = {}  # check_type -> handler function
        self.recovery_handlers = {}  # agent_type -> recovery function
        self.alert_callbacks = []  # List of alert callback functions
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 10  # Check every 10 seconds
        
        # Register default check handlers
        self._register_default_handlers()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the health monitoring service."""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Health monitoring service started")
        
    def stop(self):
        """Stop the health monitoring service."""
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        self.logger.info("Health monitoring service stopped")
        
    def register_agent(self, agent_id: str, health_checks: List[HealthCheck]):
        """Register an agent for health monitoring."""
        if agent_id not in self.agent_health:
            self.agent_health[agent_id] = AgentHealth(agent_id)
            
        agent_health = self.agent_health[agent_id]
        for check in health_checks:
            agent_health.add_health_check(check)
            
        self.logger.info(f"Registered agent {agent_id} with {len(health_checks)} health checks")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from health monitoring."""
        if agent_id in self.agent_health:
            del self.agent_health[agent_id]
            self.logger.info(f"Unregistered agent {agent_id}")
            
    def get_agent_health(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific agent."""
        agent_health = self.agent_health.get(agent_id)
        return agent_health.to_dict() if agent_health else None
        
    def get_all_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all agents."""
        return {agent_id: health.to_dict() 
                for agent_id, health in self.agent_health.items()}
                
    def get_unhealthy_agents(self) -> List[str]:
        """Get list of agents that are not healthy."""
        unhealthy = []
        for agent_id, health in self.agent_health.items():
            if health.overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                unhealthy.append(agent_id)
        return unhealthy
        
    def register_check_handler(self, check_type: str, handler: Callable):
        """Register a handler for a specific check type."""
        self.check_handlers[check_type] = handler
        
    def register_recovery_handler(self, agent_type: str, handler: Callable):
        """Register a recovery handler for a specific agent type."""
        self.recovery_handlers[agent_type] = handler
        
    def add_alert_callback(self, callback: Callable):
        """Add a callback function for health alerts."""
        self.alert_callbacks.append(callback)
        
    def _register_default_handlers(self):
        """Register default health check handlers."""
        self.check_handlers['http'] = self._http_health_check
        self.check_handlers['tcp'] = self._tcp_health_check
        self.check_handlers['ping'] = self._ping_health_check
        self.check_handlers['custom'] = self._custom_health_check
        
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check each agent's health
                for agent_id, agent_health in self.agent_health.items():
                    self._check_agent_health(agent_health, current_time)
                    
                    # Attempt recovery if needed
                    if agent_health.needs_recovery():
                        self._attempt_recovery(agent_health)
                        
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(5)
                
    def _check_agent_health(self, agent_health: AgentHealth, current_time: datetime):
        """Check health for a specific agent."""
        for check_id, health_check in agent_health.health_checks.items():
            # Check if it's time to run this health check
            if (health_check.last_check is None or 
                (current_time - health_check.last_check).total_seconds() >= health_check.interval_seconds):
                
                self._run_health_check(agent_health, health_check)
                
    def _run_health_check(self, agent_health: AgentHealth, health_check: HealthCheck):
        """Run a specific health check."""
        try:
            handler = self.check_handlers.get(health_check.type)
            if not handler:
                agent_health.update_check_status(
                    health_check.id, 
                    HealthStatus.CRITICAL, 
                    f"No handler for check type: {health_check.type}"
                )
                return
                
            # Run the health check with retries
            for attempt in range(health_check.retries + 1):
                try:
                    result = handler(health_check)
                    
                    if result.get('healthy', False):
                        agent_health.update_check_status(health_check.id, HealthStatus.HEALTHY)
                        agent_health.last_seen = datetime.utcnow()
                        break
                    else:
                        error_msg = result.get('error', 'Health check failed')
                        if attempt == health_check.retries:
                            # Final attempt failed
                            status = HealthStatus.CRITICAL if health_check.consecutive_failures >= 3 else HealthStatus.WARNING
                            agent_health.update_check_status(health_check.id, status, error_msg)
                            self._send_alert(agent_health.agent_id, health_check, status, error_msg)
                        else:
                            # Retry
                            time.sleep(1)
                            
                except Exception as e:
                    if attempt == health_check.retries:
                        agent_health.update_check_status(
                            health_check.id, 
                            HealthStatus.CRITICAL, 
                            f"Health check exception: {str(e)}"
                        )
                        self._send_alert(agent_health.agent_id, health_check, HealthStatus.CRITICAL, str(e))
                    else:
                        time.sleep(1)
                        
        except Exception as e:
            self.logger.error(f"Error running health check {health_check.id}: {e}")
            
    def _attempt_recovery(self, agent_health: AgentHealth):
        """Attempt to recover an unhealthy agent."""
        try:
            agent_id = agent_health.agent_id
            
            # Get agent type from configuration (simplified)
            agent_type = "generic"  # In practice, this would be determined from agent metadata
            
            recovery_handler = self.recovery_handlers.get(agent_type)
            if recovery_handler:
                self.logger.info(f"Attempting recovery for agent {agent_id}")
                
                success = recovery_handler(agent_id, agent_health)
                agent_health.recovery_attempts += 1
                
                if success:
                    self.logger.info(f"Recovery successful for agent {agent_id}")
                    agent_health.recovery_attempts = 0  # Reset on success
                else:
                    self.logger.warning(f"Recovery failed for agent {agent_id}")
                    
            else:
                self.logger.warning(f"No recovery handler for agent type {agent_type}")
                
        except Exception as e:
            self.logger.error(f"Error during recovery attempt for agent {agent_health.agent_id}: {e}")
            
    def _send_alert(self, agent_id: str, health_check: HealthCheck, status: HealthStatus, error: str):
        """Send health alert to registered callbacks."""
        alert_data = {
            'agent_id': agent_id,
            'check_id': health_check.id,
            'check_name': health_check.name,
            'status': status.value,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Error calling alert callback: {e}")
                
    def _http_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """HTTP health check handler."""
        config = health_check.config
        url = config.get('url')
        expected_status = config.get('expected_status', 200)
        expected_content = config.get('expected_content')
        
        if not url:
            return {'healthy': False, 'error': 'No URL specified'}
            
        try:
            response = requests.get(
                url, 
                timeout=health_check.timeout_seconds,
                headers=config.get('headers', {})
            )
            
            # Check status code
            if response.status_code != expected_status:
                return {
                    'healthy': False, 
                    'error': f'Expected status {expected_status}, got {response.status_code}'
                }
                
            # Check content if specified
            if expected_content and expected_content not in response.text:
                return {
                    'healthy': False, 
                    'error': f'Expected content "{expected_content}" not found'
                }
                
            return {
                'healthy': True, 
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {'healthy': False, 'error': f'HTTP request failed: {str(e)}'}
            
    def _tcp_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """TCP health check handler."""
        config = health_check.config
        host = config.get('host')
        port = config.get('port')
        
        if not host or not port:
            return {'healthy': False, 'error': 'Host and port must be specified'}
            
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(health_check.timeout_seconds)
            
            start_time = time.time()
            result = sock.connect_ex((host, port))
            end_time = time.time()
            
            sock.close()
            
            if result == 0:
                return {
                    'healthy': True, 
                    'response_time': end_time - start_time
                }
            else:
                return {'healthy': False, 'error': f'Connection failed to {host}:{port}'}
                
        except Exception as e:
            return {'healthy': False, 'error': f'TCP check failed: {str(e)}'}
            
    def _ping_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Ping health check handler."""
        config = health_check.config
        host = config.get('host')
        
        if not host:
            return {'healthy': False, 'error': 'Host must be specified'}
            
        try:
            import subprocess
            
            # Use ping command
            cmd = ['ping', '-c', '1', '-W', str(health_check.timeout_seconds * 1000), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=health_check.timeout_seconds)
            
            if result.returncode == 0:
                return {'healthy': True}
            else:
                return {'healthy': False, 'error': f'Ping failed: {result.stderr}'}
                
        except Exception as e:
            return {'healthy': False, 'error': f'Ping check failed: {str(e)}'}
            
    def _custom_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Custom health check handler."""
        # This would execute custom health check logic
        # For now, just return a placeholder
        return {'healthy': True, 'message': 'Custom health check not implemented'}

