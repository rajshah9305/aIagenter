# Phase 3: Background Task Processing System
# File: src/tasks/celery_config.py

from celery import Celery
from kombu import Queue
import os

def make_celery(app=None):
    """Create Celery instance with Flask app context"""
    
    # Celery configuration
    celery_config = {
        'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'UTC',
        'enable_utc': True,
        'worker_prefetch_multiplier': 4,
        'task_acks_late': True,
        'worker_disable_rate_limits': False,
        'task_default_retry_delay': 60,
        'task_max_retries': 3,
        'beat_schedule': {
            'cleanup-old-metrics': {
                'task': 'src.tasks.maintenance.cleanup_old_metrics',
                'schedule': 3600.0,  # Every hour
            },
            'agent-health-check': {
                'task': 'src.tasks.monitoring.perform_health_checks',
                'schedule': 30.0,  # Every 30 seconds
            },
            'update-performance-metrics': {
                'task': 'src.tasks.metrics.collect_system_metrics',
                'schedule': 10.0,  # Every 10 seconds
            },
            'process-workflow-queue': {
                'task': 'src.tasks.workflows.process_workflow_queue',
                'schedule': 5.0,  # Every 5 seconds
            }
        },
        'task_routes': {
            'src.tasks.maintenance.*': {'queue': 'maintenance'},
            'src.tasks.monitoring.*': {'queue': 'monitoring'},
            'src.tasks.metrics.*': {'queue': 'metrics'},
            'src.tasks.workflows.*': {'queue': 'workflows'},
            'src.tasks.agents.*': {'queue': 'agents'},
        },
        'task_default_queue': 'default',
        'task_queues': (
            Queue('default'),
            Queue('maintenance', routing_key='maintenance'),
            Queue('monitoring', routing_key='monitoring'),
            Queue('metrics', routing_key='metrics'),
            Queue('workflows', routing_key='workflows'),
            Queue('agents', routing_key='agents'),
            Queue('high_priority', routing_key='high_priority'),
        )
    }
    
    celery = Celery('agentorchestra')
    celery.conf.update(celery_config)
    
    if app:
        # Update task base classes for Flask context
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context"""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# File: src/tasks/base.py

from celery import current_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
import logging
import traceback
from typing import Any, Dict, Optional
from src.models.database import db, TaskExecution
from src.extensions import cache_manager

logger = logging.getLogger(__name__)

class BaseTask:
    """Base class for all background tasks"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.execution_id = None
        
    def __enter__(self):
        """Start task execution tracking"""
        try:
            execution = TaskExecution(
                task_name=self.task_name,
                status='running',
                started_at=datetime.utcnow(),
                celery_task_id=getattr(current_task, 'request', {}).get('id')
            )
            db.session.add(execution)
            db.session.commit()
            self.execution_id = execution.id
            
            logger.info(f"Started task: {self.task_name} (ID: {self.execution_id})")
        except Exception as e:
            logger.error(f"Failed to create task execution record: {e}")
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete task execution tracking"""
        if self.execution_id:
            try:
                execution = TaskExecution.query.get(self.execution_id)
                if execution:
                    execution.completed_at = datetime.utcnow()
                    execution.duration = (execution.completed_at - execution.started_at).total_seconds()
                    
                    if exc_type:
                        execution.status = 'failed'
                        execution.error_message = str(exc_val)
                        execution.error_traceback = traceback.format_exception(exc_type, exc_val, exc_tb)
                        logger.error(f"Task {self.task_name} failed: {exc_val}")
                    else:
                        execution.status = 'completed'
                        logger.info(f"Task {self.task_name} completed successfully in {execution.duration:.2f}s")
                    
                    db.session.commit()
            except Exception as e:
                logger.error(f"Failed to update task execution record: {e}")

def retry_on_exception(max_retries: int = 3, countdown: int = 60):
    """Decorator for automatic task retries"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if current_task.request.retries < max_retries:
                    logger.warning(f"Task {func.__name__} failed, retrying in {countdown}s: {exc}")
                    raise current_task.retry(countdown=countdown, exc=exc)
                else:
                    logger.error(f"Task {func.__name__} failed after {max_retries} retries: {exc}")
                    raise
        return wrapper
    return decorator

# File: src/tasks/agents.py

from celery import shared_task
from src.tasks.base import BaseTask, retry_on_exception
from src.models.database import Agent, Framework, Task as TaskModel
from src.services.agent_service import AgentService
from src.services.orchestration_service import OrchestrationService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='src.tasks.agents.start_agent')
@retry_on_exception(max_retries=3, countdown=30)
def start_agent(self, agent_id: int):
    """Start an agent asynchronously"""
    with BaseTask('start_agent') as task:
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent_service = AgentService()
        success = agent_service.start_agent(agent_id)
        
        if success:
            logger.info(f"Successfully started agent {agent_id}")
            return {'status': 'success', 'agent_id': agent_id}
        else:
            raise Exception(f"Failed to start agent {agent_id}")

@shared_task(bind=True, name='src.tasks.agents.stop_agent')
@retry_on_exception(max_retries=2, countdown=10)
def stop_agent(self, agent_id: int):
    """Stop an agent asynchronously"""
    with BaseTask('stop_agent') as task:
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent_service = AgentService()
        success = agent_service.stop_agent(agent_id)
        
        if success:
            logger.info(f"Successfully stopped agent {agent_id}")
            return {'status': 'success', 'agent_id': agent_id}
        else:
            raise Exception(f"Failed to stop agent {agent_id}")

@shared_task(bind=True, name='src.tasks.agents.restart_agent')
def restart_agent(self, agent_id: int):
    """Restart an agent asynchronously"""
    with BaseTask('restart_agent') as task:
        # Stop then start
        stop_result = stop_agent.delay(agent_id)
        stop_result.get(timeout=60)  # Wait for stop to complete
        
        start_result = start_agent.delay(agent_id)
        return start_result.get(timeout=120)  # Wait for start to complete

@shared_task(bind=True, name='src.tasks.agents.bulk_agent_operation')
def bulk_agent_operation(self, agent_ids: list, operation: str):
    """Perform bulk operations on multiple agents"""
    with BaseTask('bulk_agent_operation') as task:
        results = []
        
        for agent_id in agent_ids:
            try:
                if operation == 'start':
                    result = start_agent.delay(agent_id)
                elif operation == 'stop':
                    result = stop_agent.delay(agent_id)
                elif operation == 'restart':
                    result = restart_agent.delay(agent_id)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                results.append({
                    'agent_id': agent_id,
                    'task_id': result.id,
                    'status': 'queued'
                })
            except Exception as e:
                results.append({
                    'agent_id': agent_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results

# File: src/tasks/workflows.py

from celery import shared_task, group, chain
from src.tasks.base import BaseTask, retry_on_exception
from src.models.database import Workflow, WorkflowExecution, Task as TaskModel
from src.services.workflow_service import WorkflowService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='src.tasks.workflows.execute_workflow')
@retry_on_exception(max_retries=2, countdown=60)
def execute_workflow(self, workflow_id: int, input_data: dict = None):
    """Execute a complete workflow"""
    with BaseTask('execute_workflow') as task:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_service = WorkflowService()
        execution_id = workflow_service.start_execution(workflow_id, input_data or {})
        
        # Execute workflow steps
        result = workflow_service.execute_workflow(execution_id)
        
        logger.info(f"Workflow {workflow_id} execution {execution_id} completed")
        return {
            'workflow_id': workflow_id,
            'execution_id': execution_id,
            'result': result
        }

@shared_task(bind=True, name='src.tasks.workflows.process_workflow_queue')
def process_workflow_queue(self):
    """Process queued workflows"""
    with BaseTask('process_workflow_queue') as task:
        workflow_service = WorkflowService()
        
        # Get pending workflows
        pending_workflows = workflow_service.get_pending_workflows(limit=10)
        
        processed_count = 0
        for workflow_exec in pending_workflows:
            try:
                # Execute workflow asynchronously
                execute_workflow.delay(workflow_exec.workflow_id, workflow_exec.input_data)
                workflow_exec.status = 'running'
                db.session.commit()
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to queue workflow {workflow_exec.id}: {e}")
        
        logger.info(f"Processed {processed_count} workflows from queue")
        return {'processed_count': processed_count}

@shared_task(bind=True, name='src.tasks.workflows.parallel_task_execution')
def parallel_task_execution(self, task_ids: list):
    """Execute multiple tasks in parallel"""
    with BaseTask('parallel_task_execution') as task:
        from src.tasks.agents import start_agent
        
        # Create parallel task group
        task_group = group(start_agent.s(task_id) for task_id in task_ids)
        result = task_group.apply_async()
        
        # Wait for all tasks to complete
        results = result.get()
        
        return {
            'total_tasks': len(task_ids),
            'results': results
        }

# File: src/tasks/monitoring.py

from celery import shared_task
from src.tasks.base import BaseTask
from src.models.database import Agent, Metric
from src.services.monitoring_service import MonitoringService
from src.extensions import cache_manager
import psutil
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='src.tasks.monitoring.perform_health_checks')
def perform_health_checks(self):
    """Perform health checks on all active agents"""
    with BaseTask('perform_health_checks') as task:
        monitoring_service = MonitoringService()
        
        # Get all active agents
        active_agents = Agent.query.filter(Agent.status.in_(['active', 'idle'])).all()
        
        health_results = []
        for agent in active_agents:
            try:
                health_status = monitoring_service.check_agent_health(agent.id)
                health_results.append({
                    'agent_id': agent.id,
                    'status': health_status['status'],
                    'response_time': health_status.get('response_time', 0)
                })
                
                # Update agent status if unhealthy
                if health_status['status'] != 'healthy':
                    agent.status = 'error'
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Health check failed for agent {agent.id}: {e}")
                health_results.append({
                    'agent_id': agent.id,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Invalidate health cache
        cache_manager.invalidate_pattern("health")
        
        logger.info(f"Completed health checks for {len(active_agents)} agents")
        return {
            'total_agents': len(active_agents),
            'results': health_results
        }

@shared_task(bind=True, name='src.tasks.monitoring.collect_system_metrics')
def collect_system_metrics(self):
    """Collect system performance metrics"""
    with BaseTask('collect_system_metrics') as task:
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Store metrics in database
            metric = Metric(
                agent_id=None,  # System-wide metric
                metric_type='system',
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                custom_metrics={
                    'memory_available': memory.available,
                    'memory_total': memory.total,
                    'disk_free': disk.free,
                    'disk_total': disk.total
                }
            )
            
            db.session.add(metric)
            db.session.commit()
            
            # Invalidate metrics cache
            cache_manager.invalidate_pattern("metrics")
            
            logger.debug(f"Collected system metrics: CPU {cpu_percent}%, Memory {memory.percent}%")
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise

# File: src/tasks/maintenance.py

from celery import shared_task
from src.tasks.base import BaseTask
from src.models.database import Metric, TaskExecution, WorkflowExecution
from src.models.optimized_queries import OptimizedQueries
from src.extensions import cache_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='src.tasks.maintenance.cleanup_old_metrics')
def cleanup_old_metrics(self, days: int = 7):
    """Clean up old metrics from database"""
    with BaseTask('cleanup_old_metrics') as task:
        optimized_queries = OptimizedQueries(cache_manager)
        deleted_count = optimized_queries.cleanup_old_metrics(days)
        
        logger.info(f"Cleaned up {deleted_count} metrics older than {days} days")
        return {'deleted_count': deleted_count, 'days': days}

@shared_task(bind=True, name='src.tasks.maintenance.cleanup_old_executions')
def cleanup_old_executions(self, days: int = 30):
    """Clean up old task and workflow executions"""
    with BaseTask('cleanup_old_executions') as task:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Clean up task executions
        task_deleted = TaskExecution.query.filter(
            TaskExecution.completed_at < cutoff_date
        ).delete(synchronize_session=False)
        
        # Clean up workflow executions
        workflow_deleted = WorkflowExecution.query.filter(
            WorkflowExecution.completed_at < cutoff_date
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        total_deleted = task_deleted + workflow_deleted
        logger.info(f"Cleaned up {total_deleted} executions older than {days} days")
        
        return {
            'task_executions_deleted': task_deleted,
            'workflow_executions_deleted': workflow_deleted,
            'total_deleted': total_deleted
        }

@shared_task(bind=True, name='src.tasks.maintenance.cache_warmup')
def cache_warmup(self):
    """Warm up frequently accessed cache entries"""
    with BaseTask('cache_warmup') as task:
        optimized_queries = OptimizedQueries(cache_manager)
        
        warmup_tasks = [
            ('dashboard_data', optimized_queries.get_dashboard_data),
            ('active_agents', optimized_queries.get_active_agents_summary),
            ('performance_metrics', lambda: optimized_queries.get_performance_metrics(24))
        ]
        
        warmed_count = 0
        for cache_key, func in warmup_tasks:
            try:
                result = func()
                warmed_count += 1
                logger.debug(f"Warmed up cache for {cache_key}")
            except Exception as e:
                logger.error(f"Failed to warm up cache for {cache_key}: {e}")
        
        logger.info(f"Cache warmup completed: {warmed_count}/{len(warmup_tasks)} entries")
        return {'warmed_count': warmed_count, 'total_tasks': len(warmup_tasks)}

# File: src/tasks/__init__.py

from src.tasks.celery_config import make_celery
from src.tasks import agents, workflows, monitoring, maintenance

__all__ = ['make_celery', 'agents', 'workflows', 'monitoring', 'maintenance']

# File: src/models/database.py (Add new model)

class TaskExecution(db.Model):
    """Track background task executions"""
    __tablename__ = 'task_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    celery_task_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # seconds
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_name': self.task_name,
            'celery_task_id': self.celery_task_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'error_message': self.error_message
        }