# Phase 3: Comprehensive Logging & Monitoring System
# File: src/monitoring/logger_config.py

import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from flask import request, g, current_app
import os
import sys

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if hasattr(g, 'request_id'):
            log_data['request_id'] = g.request_id
            
        if request:
            log_data['request'] = {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)

class AgentOrchestraLogger:
    """Enhanced logging system for AgentOrchestra"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logging with Flask app"""
        
        # Create logs directory
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        
        # Remove default handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Setup structured file logging
        self._setup_file_logging(app, logs_dir)
        
        # Setup console logging for development
        if app.config.get('DEBUG'):
            self._setup_console_logging()
        
        # Setup error logging
        self._setup_error_logging(logs_dir)
        
        # Setup audit logging
        self._setup_audit_logging(logs_dir)
        
        # Configure third-party loggers
        self._configure_third_party_loggers()
    
    def _setup_file_logging(self, app, logs_dir):
        """Setup rotating file handler for general logs"""
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, 'agentorchestra.log'),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(StructuredFormatter())
        
        logging.getLogger().addHandler(file_handler)
    
    def _setup_console_logging(self):
        """Setup console logging for development"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Use simple format for console
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        logging.getLogger().addHandler(console_handler)
    
    def _setup_error_logging(self, logs_dir):
        """Setup dedicated error logging"""
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, 'errors.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        # Create error-only logger
        error_logger = logging.getLogger('agentorchestra.errors')
        error_logger.addHandler(error_handler)
        error_logger.propagate = False
    
    def _setup_audit_logging(self, logs_dir):
        """Setup audit trail logging"""
        audit_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, 'audit.log'),
            maxBytes=100*1024*1024,  # 100MB
            backupCount=20,
            encoding='utf-8'
        )
        
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredFormatter())
        
        # Create audit-only logger
        audit_logger = logging.getLogger('agentorchestra.audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
    
    def _configure_third_party_loggers(self):
        """Configure third-party library loggers"""
        # Reduce SQLAlchemy verbosity
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
        
        # Reduce Celery verbosity
        logging.getLogger('celery').setLevel(logging.WARNING)
        
        # Reduce Flask verbosity
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

# File: src/monitoring/metrics_collector.py

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from src.models.database import db, Agent, Metric
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available: int
    memory_total: int
    disk_usage: float
    disk_free: int
    disk_total: int
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: datetime
    active_agents: int
    total_agents: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_response_time: float
    error_rate: float
    throughput: float

class MetricsCollector:
    """Real-time metrics collection and aggregation"""
    
    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval
        self.running = False
        self.collection_thread = None
        
        # In-memory storage for real-time metrics
        self.system_metrics_buffer = deque(maxlen=360)  # 1 hour at 10s intervals
        self.app_metrics_buffer = deque(maxlen=360)
        self.agent_metrics_buffer = defaultdict(lambda: deque(maxlen=360))
        
        # Performance counters
        self.last_network_stats = None
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=100)
        
        self.lock = threading.Lock()
    
    def start_collection(self):
        """Start metrics collection in background thread"""
        if not self.running:
            self.running = True
            self.collection_thread = threading.Thread(target=self._collection_loop)
            self.collection_thread.daemon = True
            self.collection_thread.start()
            logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                with self.lock:
                    self.system_metrics_buffer.append(system_metrics)
                
                # Collect application metrics
                app_metrics = self._collect_application_metrics()
                with self.lock:
                    self.app_metrics_buffer.append(app_metrics)
                
                # Collect agent-specific metrics
                self._collect_agent_metrics()
                
                # Persist metrics to database periodically
                if len(self.system_metrics_buffer) % 6 == 0:  # Every minute
                    self._persist_metrics()
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Load average (Unix only)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]
        
        # Connection count
        try:
            connections = len(psutil.net_connections())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            connections = 0
        
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_available=memory.available,
            memory_total=memory.total,
            disk_usage=disk.percent,
            disk_free=disk.free,
            disk_total=disk.total,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_connections=connections,
            load_average=load_avg
        )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            # Agent metrics
            agent_counts = db.session.query(
                Agent.status, 
                db.func.count(Agent.id)
            ).group_by(Agent.status).all()
            
            active_agents = sum(count for status, count in agent_counts if status in ['active', 'idle'])
            total_agents = sum(count for status, count in agent_counts)
            
            # Task metrics (placeholder - adjust based on your Task model)
            # running_tasks = Task.query.filter_by(status='running').count()
            # completed_tasks = Task.query.filter_by(status='completed').count()
            # failed_tasks = Task.query.filter_by(status='failed').count()
            
            # Performance metrics
            with self.lock:
                avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
                error_rate = (self.error_count / max(self.request_count, 1)) * 100
                throughput = self.request_count / self.collection_interval if self.request_count > 0 else 0
                
                # Reset counters
                self.request_count = 0
                self.error_count = 0
                self.response_times.clear()
            
            return ApplicationMetrics(
                timestamp=datetime.utcnow(),
                active_agents=active_agents,
                total_agents=total_agents,
                running_tasks=0,  # running_tasks,
                completed_tasks=0,  # completed_tasks,
                failed_tasks=0,  # failed_tasks,
                average_response_time=avg_response_time,
                error_rate=error_rate,
                throughput=throughput
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return ApplicationMetrics(
                timestamp=datetime.utcnow(),
                active_agents=0, total_agents=0, running_tasks=0,
                completed_tasks=0, failed_tasks=0, average_response_time=0,
                error_rate=0, throughput=0
            )
    
    def _collect_agent_metrics(self):
        """Collect metrics for individual agents"""
        try:
            active_agents = Agent.query.filter(Agent.status.in_(['active', 'idle'])).all()
            
            for agent in active_agents:
                # Collect agent-specific metrics (placeholder)
                agent_metric = {
                    'timestamp': datetime.utcnow(),
                    'agent_id': agent.id,
                    'status': agent.status,
                    'cpu_usage': 0.0,  # Would come from agent's process
                    'memory_usage': 0.0,
                    'task_count': 0,
                    'error_count': 0
                }
                
                with self.lock:
                    self.agent_metrics_buffer[agent.id].append(agent_metric)
                    
        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")
    
    def _persist_metrics(self):
        """Persist metrics to database"""
        try:
            # Get latest system metrics
            with self.lock:
                if not self.system_metrics_buffer:
                    return
                
                latest_system = self.system_metrics_buffer[-1]
                latest_app = self.app_metrics_buffer[-1] if self.app_metrics_buffer else None
            
            # Create database metric entry
            metric = Metric(
                agent_id=None,  # System metric
                metric_type='system',
                cpu_usage=latest_system.cpu_usage,
                memory_usage=latest_system.memory_usage,
                disk_usage=latest_system.disk_usage,
                custom_metrics={
                    'memory_available': latest_system.memory_available,
                    'memory_total': latest_system.memory_total,
                    'disk_free': latest_system.disk_free,
                    'disk_total': latest_system.disk_total,
                    'network_bytes_sent': latest_system.network_bytes_sent,
                    'network_bytes_recv': latest_system.network_bytes_recv,
                    'active_connections': latest_system.active_connections,
                    'load_average': latest_system.load_average,
                    'application_metrics': asdict(latest_app) if latest_app else {}
                }
            )
            
            db.session.add(metric)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error persisting metrics: {e}")
            db.session.rollback()
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record request metrics"""
        with self.lock:
            self.request_count += 1
            if is_error:
                self.error_count += 1
            self.response_times.append(response_time)
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        with self.lock:
            system_metrics = list(self.system_metrics_buffer)
            app_metrics = list(self.app_metrics_buffer)
        
        if not system_metrics:
            return {}
        
        latest_system = system_metrics[-1]
        latest_app = app_metrics[-1] if app_metrics else None
        
        return {
            'system': asdict(latest_system),
            'application': asdict(latest_app) if latest_app else {},
            'timestamp': datetime.utcnow().isoformat(),
            'collection_interval': self.collection_interval
        }

# File: src/monitoring/alerting.py

import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """Definition of an alert rule"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    level: AlertLevel
    message_template: str
    cooldown_minutes: int = 15
    enabled: bool = True

@dataclass
class Alert:
    """An active alert"""
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """Comprehensive alerting system"""
    
    def __init__(self, smtp_config: Optional[Dict[str, str]] = None):
        self.smtp_config = smtp_config or {}
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_triggered: Dict[str, datetime] = {}
        
        # Setup default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alerting rules"""
        
        # High CPU usage
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda data: data.get('system', {}).get('cpu_usage', 0) > 80,
            level=AlertLevel.WARNING,
            message_template="High CPU usage detected: {cpu_usage:.1f}%",
            cooldown_minutes=10
        ))
        
        # High memory usage
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda data: data.get('system', {}).get('memory_usage', 0) > 85,
            level=AlertLevel.WARNING,
            message_template="High memory usage detected: {memory_usage:.1f}%",
            cooldown_minutes=10
        ))
        
        # Critical memory usage
        self.add_rule(AlertRule(
            name="critical_memory_usage",
            condition=lambda data: data.get('system', {}).get('memory_usage', 0) > 95,
            level=AlertLevel.CRITICAL,
            message_template="Critical memory usage: {memory_usage:.1f}%",
            cooldown_minutes=5
        ))
        
        # Agent failures
        self.add_rule(AlertRule(
            name="agent_failures",
            condition=lambda data: data.get('application', {}).get('error_rate', 0) > 10,
            level=AlertLevel.WARNING,
            message_template="High agent error rate: {error_rate:.1f}%",
            cooldown_minutes=15
        ))
        
        # No active agents
        self.add_rule(AlertRule(
            name="no_active_agents",
            condition=lambda data: data.get('application', {}).get('active_agents', 0) == 0,
            level=AlertLevel.CRITICAL,
            message_template="No active agents detected",
            cooldown_minutes=5
        ))
        
        # High disk usage
        self.add_rule(AlertRule(
            name="high_disk_usage",
            condition=lambda data: data.get('system', {}).get('disk_usage', 0) > 90,
            level=AlertLevel.CRITICAL,
            message_template="Critical disk usage: {disk_usage:.1f}%",
            cooldown_minutes=30
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def check_alerts(self, metrics_data: Dict[str, Any]):
        """Check all rules against current metrics"""
        current_time = datetime.utcnow()
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if (rule_name in self.last_triggered and 
                current_time - self.last_triggered[rule_name] < timedelta(minutes=rule.cooldown_minutes)):
                continue
            
            try:
                # Evaluate rule condition
                if rule.condition(metrics_data):
                    self._trigger_alert(rule, metrics_data, current_time)
                else:
                    # Check if we should resolve an existing alert
                    if rule_name in self.active_alerts:
                        self._resolve_alert(rule_name, current_time)
                        
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule_name}: {e}")
    
    def _trigger_alert(self, rule: AlertRule, data: Dict[str, Any], timestamp: datetime):
        """Trigger an alert"""
        # Format message
        try:
            # Flatten data for message formatting
            flat_data = self._flatten_dict(data)
            message = rule.message_template.format(**flat_data)
        except (KeyError, ValueError) as e:
            message = f"{rule.message_template} (formatting error: {e})"
        
        # Create alert
        alert = Alert(
            rule_name=rule.name,
            level=rule.level,
            message=message,
            timestamp=timestamp,
            data=data
        )
        
        # Store alert
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        self.last_triggered[rule.name] = timestamp
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"Alert triggered: {rule.name} - {message}")
    
    def _resolve_alert(self, rule_name: str, timestamp: datetime):
        """Resolve an active alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = timestamp
            
            del self.active_alerts[rule_name]
            
            logger.info(f"Alert resolved: {rule_name}")
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        # Email notification
        if self.smtp_config and alert.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self._send_email_notification(alert)
        
        # Log notification
        log_level = logging.WARNING if alert.level == AlertLevel.WARNING else logging.CRITICAL
        logger.log(log_level, f"ALERT: {alert.message}")
    
    def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            if not all(k in self.smtp_config for k in ['host', 'port', 'username', 'password', 'to_email']):
                logger.warning("SMTP configuration incomplete, skipping email notification")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = self.smtp_config['to_email']
            msg['Subject'] = f"AgentOrchestra Alert: {alert.rule_name}"
            
            # Create email body
            body = f"""
AgentOrchestra Alert

Level: {alert.level.value.upper()}
Rule: {alert.rule_name}
Message: {alert.message}
Time: {alert.timestamp.isoformat()}

System Information:
{json.dumps(alert.data, indent=2, default=str)}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert: {alert.rule_name}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for string formatting"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp > cutoff_time]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        # Count by level
        level_counts = {}
        for level in AlertLevel:
            level_counts[level.value] = sum(1 for alert in self.alert_history if alert.level == level)
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'alerts_by_level': level_counts,
            'rules_count': len(self.rules),
            'enabled_rules': sum(1 for rule in self.rules.values() if rule.enabled)
        }

# File: src/monitoring/__init__.py

from src.monitoring.logger_config import AgentOrchestraLogger
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.alerting import AlertManager, AlertLevel, AlertRule, Alert

# Global instances
logger_manager = AgentOrchestraLogger()
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

def init_monitoring(app):
    """Initialize monitoring system"""
    
    # Initialize logging
    logger_manager.init_app(app)
    
    # Initialize metrics collection
    metrics_collector.start_collection()
    
    # Initialize alerting with SMTP config if available
    smtp_config = {
        'host': app.config.get('SMTP_HOST'),
        'port': app.config.get('SMTP_PORT', 587),
        'username': app.config.get('SMTP_USERNAME'),
        'password': app.config.get('SMTP_PASSWORD'),
        'to_email': app.config.get('ALERT_EMAIL')
    }
    
    if all(smtp_config.values()):
        global alert_manager
        alert_manager = AlertManager(smtp_config)
    
    # Setup periodic alert checking
    @app.before_request
    def check_alerts_on_request():
        """Check alerts on each request"""
        try:
            metrics_data = metrics_collector.get_real_time_metrics()
            if metrics_data:
                alert_manager.check_alerts(metrics_data)
        except Exception as e:
            app.logger.error(f"Error checking alerts: {e}")
    
    return {
        'logger_manager': logger_manager,
        'metrics_collector': metrics_collector,
        'alert_manager': alert_manager
    }

__all__ = [
    'AgentOrchestraLogger',
    'MetricsCollector', 
    'AlertManager',
    'AlertLevel',
    'AlertRule',
    'Alert',
    'init_monitoring',
    'logger_manager',
    'metrics_collector', 
    'alert_manager'
]