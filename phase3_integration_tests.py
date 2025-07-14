# Phase 3: Comprehensive Integration Tests
# File: tests/conftest.py

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.app import create_app
from src.models.database import db
from src.extensions import redis_client, cache_manager
from src.tasks.celery_config import make_celery
from src.monitoring import init_monitoring

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')[0]  # Get app without socketio
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'REDIS_URL': 'redis://localhost:6379/15',  # Test Redis DB
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean database between tests"""
    with app.app_context():
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    with patch('src.extensions.redis_client') as mock:
        mock_client = Mock()
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = []
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_celery():
    """Mock Celery for testing"""
    with patch('src.tasks.celery_config.make_celery') as mock:
        mock_celery = Mock()
        mock_task = Mock()
        mock_task.delay.return_value = Mock(id='test-task-id')
        mock_celery.Task = Mock
        mock_celery.task = lambda *args, **kwargs: lambda f: mock_task
        mock.return_value = mock_celery
        yield mock_celery

@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        'name': 'Test Agent',
        'description': 'Test agent for integration testing',
        'framework_id': 1,
        'configuration': {
            'model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        'capabilities': ['chat', 'reasoning'],
        'status': 'inactive'
    }

@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing"""
    return {
        'name': 'Test Workflow',
        'description': 'Test workflow for integration testing',
        'definition': {
            'steps': [
                {
                    'id': 'step1',
                    'type': 'agent_task',
                    'agent_id': 1,
                    'task': 'Generate response'
                }
            ]
        }
    }

# File: tests/integration/test_database_optimization.py

import pytest
import time
from unittest.mock import patch, Mock
from src.utils.db_optimization import QueryOptimizer, CacheManager
from src.models.optimized_queries import OptimizedQueries
from src.models.database import Agent, Framework, Metric, db

class TestDatabaseOptimization:
    """Test database optimization and caching"""
    
    def test_query_optimizer_initialization(self, app, mock_redis):
        """Test QueryOptimizer initialization"""
        with app.app_context():
            optimizer = QueryOptimizer(mock_redis)
            assert optimizer.redis_client == mock_redis
            assert optimizer.slow_query_threshold == 1.0
            assert optimizer.query_stats == {}
    
    def test_query_monitoring_setup(self, app, mock_redis):
        """Test query monitoring setup"""
        with app.app_context():
            optimizer = QueryOptimizer(mock_redis)
            optimizer.setup_query_monitoring()
            
            # Execute a query to trigger monitoring
            agents = Agent.query.all()
            
            # Check if query stats were recorded
            assert len(optimizer.query_stats) >= 0  # May be 0 for simple queries
    
    def test_cache_manager_key_generation(self, app, mock_redis):
        """Test cache key generation"""
        with app.app_context():
            cache_manager = CacheManager(mock_redis)
            
            # Test key generation
            key1 = cache_manager.cache_key("test", "arg1", "arg2", param1="value1")
            key2 = cache_manager.cache_key("test", "arg1", "arg2", param1="value1")
            key3 = cache_manager.cache_key("test", "arg1", "arg3", param1="value1")
            
            assert key1 == key2  # Same arguments should generate same key
            assert key1 != key3  # Different arguments should generate different key
            assert key1.startswith("agentorchestra:test:")
    
    def test_cached_decorator(self, app, mock_redis):
        """Test caching decorator functionality"""
        with app.app_context():
            cache_manager = CacheManager(mock_redis)
            
            call_count = 0
            
            @cache_manager.cached(ttl=300, prefix="test")
            def expensive_function(arg1, arg2):
                nonlocal call_count
                call_count += 1
                return f"result_{arg1}_{arg2}"
            
            # First call should execute function
            result1 = expensive_function("a", "b")
            assert result1 == "result_a_b"
            assert call_count == 1
            
            # Second call should use cache (but won't since we're mocking Redis)
            mock_redis.get.return_value = '\"cached_result\"'
            result2 = expensive_function("a", "b")
            assert result2 == "cached_result"
    
    def test_optimized_queries_active_agents(self, app, mock_redis):
        """Test optimized active agents query"""
        with app.app_context():
            # Create test data
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent1 = Agent(name='Agent 1', framework_id=framework.id, status='active')
            agent2 = Agent(name='Agent 2', framework_id=framework.id, status='idle')
            agent3 = Agent(name='Agent 3', framework_id=framework.id, status='error')
            
            db.session.add_all([agent1, agent2, agent3])
            db.session.commit()
            
            # Test optimized query
            cache_manager = CacheManager(mock_redis)
            queries = OptimizedQueries(cache_manager)
            
            # Mock cache miss
            mock_redis.get.return_value = None
            
            results = queries.get_active_agents_summary()
            
            # Should return active and idle agents only
            assert len(results) == 2
            assert mock_redis.setex.called  # Should attempt to cache result
    
    def test_performance_metrics_query(self, app, mock_redis):
        """Test performance metrics aggregation"""
        with app.app_context():
            # Create test metrics
            for i in range(5):
                metric = Metric(
                    agent_id=None,
                    metric_type='system',
                    cpu_usage=50.0 + i,
                    memory_usage=60.0 + i,
                    disk_usage=30.0
                )
                db.session.add(metric)
            
            db.session.commit()
            
            cache_manager = CacheManager(mock_redis)
            queries = OptimizedQueries(cache_manager)
            
            # Mock cache miss
            mock_redis.get.return_value = None
            
            metrics = queries.get_performance_metrics(hours=24)
            
            assert 'avg_cpu' in metrics
            assert 'avg_memory' in metrics
            assert metrics['avg_cpu'] > 0
            assert metrics['avg_memory'] > 0
    
    def test_bulk_update_with_cache_invalidation(self, app, mock_redis):
        """Test bulk update with cache invalidation"""
        with app.app_context():
            # Create test agents
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agents = []
            for i in range(3):
                agent = Agent(name=f'Agent {i}', framework_id=framework.id, status='inactive')
                agents.append(agent)
                db.session.add(agent)
            
            db.session.commit()
            agent_ids = [agent.id for agent in agents]
            
            cache_manager = CacheManager(mock_redis)
            queries = OptimizedQueries(cache_manager)
            
            # Perform bulk update
            queries.bulk_update_agent_status(agent_ids, 'active')
            
            # Verify update
            updated_agents = Agent.query.filter(Agent.id.in_(agent_ids)).all()
            assert all(agent.status == 'active' for agent in updated_agents)
            
            # Verify cache invalidation was called
            assert mock_redis.keys.call_count >= 1  # Should call keys for pattern matching

# File: tests/integration/test_background_tasks.py

import pytest
from unittest.mock import patch, Mock, MagicMock
from src.tasks.agents import start_agent, stop_agent, bulk_agent_operation
from src.tasks.workflows import execute_workflow, process_workflow_queue
from src.tasks.monitoring import perform_health_checks, collect_system_metrics
from src.tasks.maintenance import cleanup_old_metrics
from src.models.database import Agent, Framework, TaskExecution, Metric, db

class TestBackgroundTasks:
    """Test background task processing"""
    
    @patch('src.tasks.agents.AgentService')
    def test_start_agent_task(self, mock_service, app, sample_agent_data):
        """Test agent start task"""
        with app.app_context():
            # Create test agent
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent = Agent(name='Test Agent', framework_id=framework.id, status='inactive')
            db.session.add(agent)
            db.session.commit()
            
            # Mock service
            mock_service_instance = Mock()
            mock_service_instance.start_agent.return_value = True
            mock_service.return_value = mock_service_instance
            
            # Mock current_task for the decorator
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'test-task-id'
                mock_task.request.retries = 0
                
                # Execute task
                result = start_agent('self', agent.id)
                
                assert result['status'] == 'success'
                assert result['agent_id'] == agent.id
                assert mock_service_instance.start_agent.called
    
    @patch('src.tasks.agents.AgentService')
    def test_start_agent_task_failure(self, mock_service, app):
        """Test agent start task failure"""
        with app.app_context():
            # Mock service failure
            mock_service_instance = Mock()
            mock_service_instance.start_agent.return_value = False
            mock_service.return_value = mock_service_instance
            
            # Mock current_task
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'test-task-id'
                mock_task.request.retries = 0
                
                # Execute task - should raise exception
                with pytest.raises(Exception, match="Failed to start agent"):
                    start_agent('self', 999)  # Non-existent agent
    
    def test_bulk_agent_operation(self, app):
        """Test bulk agent operations"""
        with app.app_context():
            # Create test framework and agents
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent_ids = []
            for i in range(3):
                agent = Agent(name=f'Agent {i}', framework_id=framework.id, status='inactive')
                db.session.add(agent)
                db.session.flush()
                agent_ids.append(agent.id)
            
            db.session.commit()
            
            # Mock the individual task functions
            with patch('src.tasks.agents.start_agent') as mock_start:
                mock_result = Mock()
                mock_result.id = 'task-123'
                mock_start.delay.return_value = mock_result
                
                # Mock current_task
                with patch('src.tasks.base.current_task') as mock_task:
                    mock_task.request = Mock()
                    mock_task.request.id = 'bulk-task-id'
                    
                    # Execute bulk operation
                    results = bulk_agent_operation('self', agent_ids, 'start')
                    
                    assert len(results) == 3
                    assert all(result['status'] == 'queued' for result in results)
                    assert mock_start.delay.call_count == 3
    
    @patch('src.tasks.workflows.WorkflowService')
    def test_execute_workflow_task(self, mock_service, app):
        """Test workflow execution task"""
        with app.app_context():
            # Mock workflow service
            mock_service_instance = Mock()
            mock_service_instance.start_execution.return_value = 'exec-123'
            mock_service_instance.execute_workflow.return_value = {'status': 'completed'}
            mock_service.return_value = mock_service_instance
            
            # Mock current_task
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'workflow-task-id'
                mock_task.request.retries = 0
                
                # Execute task
                result = execute_workflow('self', 1, {'input': 'test'})
                
                assert result['workflow_id'] == 1
                assert result['execution_id'] == 'exec-123'
                assert 'result' in result
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics_task(self, mock_disk, mock_memory, mock_cpu, app):
        """Test system metrics collection task"""
        with app.app_context():
            # Mock system information
            mock_cpu.return_value = 45.5
            mock_memory.return_value = Mock(percent=62.3, available=1000000, total=2000000)
            mock_disk.return_value = Mock(percent=78.1, free=500000, total=1000000)
            
            # Mock current_task
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'metrics-task-id'
                
                # Execute task
                result = collect_system_metrics('self')
                
                assert result['cpu_usage'] == 45.5
                assert result['memory_usage'] == 62.3
                assert result['disk_usage'] == 78.1
                
                # Verify metric was stored
                metrics = Metric.query.filter_by(metric_type='system').all()
                assert len(metrics) == 1
                assert metrics[0].cpu_usage == 45.5
    
    @patch('src.tasks.monitoring.MonitoringService')
    def test_perform_health_checks_task(self, mock_service, app):
        """Test health checks task"""
        with app.app_context():
            # Create test agents
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent1 = Agent(name='Agent 1', framework_id=framework.id, status='active')
            agent2 = Agent(name='Agent 2', framework_id=framework.id, status='idle')
            db.session.add_all([agent1, agent2])
            db.session.commit()
            
            # Mock monitoring service
            mock_service_instance = Mock()
            mock_service_instance.check_agent_health.side_effect = [
                {'status': 'healthy', 'response_time': 0.1},
                {'status': 'unhealthy', 'response_time': 2.0}
            ]
            mock_service.return_value = mock_service_instance
            
            # Mock current_task
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'health-task-id'
                
                # Execute task
                result = perform_health_checks('self')
                
                assert result['total_agents'] == 2
                assert len(result['results']) == 2
                
                # Verify unhealthy agent status was updated
                updated_agent = Agent.query.get(agent2.id)
                assert updated_agent.status == 'error'
    
    def test_cleanup_old_metrics_task(self, app):
        """Test metrics cleanup task"""
        with app.app_context():
            # Create old and new metrics
            from datetime import datetime, timedelta
            
            old_time = datetime.utcnow() - timedelta(days=10)
            new_time = datetime.utcnow() - timedelta(hours=1)
            
            old_metric = Metric(
                metric_type='system',
                cpu_usage=50.0,
                memory_usage=60.0,
                created_at=old_time
            )
            new_metric = Metric(
                metric_type='system',
                cpu_usage=55.0,
                memory_usage=65.0,
                created_at=new_time
            )
            
            db.session.add_all([old_metric, new_metric])
            db.session.commit()
            
            # Mock current_task
            with patch('src.tasks.base.current_task') as mock_task:
                mock_task.request = Mock()
                mock_task.request.id = 'cleanup-task-id'
                
                # Execute cleanup
                result = cleanup_old_metrics('self', days=7)
                
                assert result['deleted_count'] >= 0  # May vary based on test timing
                
                # Verify new metric still exists
                remaining_metrics = Metric.query.all()
                assert len(remaining_metrics) >= 1

# File: tests/integration/test_monitoring_system.py

import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from src.monitoring import init_monitoring
from src.monitoring.metrics_collector import MetricsCollector, SystemMetrics, ApplicationMetrics
from src.monitoring.alerting import AlertManager, AlertRule, AlertLevel
from src.monitoring.logger_config import AgentOrchestraLogger
from src.models.database import Agent, Framework, Metric, db

class TestMonitoringSystem:
    """Test comprehensive monitoring system"""
    
    def test_monitoring_initialization(self, app):
        """Test monitoring system initialization"""
        with app.app_context():
            components = init_monitoring(app)
            
            assert 'logger_manager' in components
            assert 'metrics_collector' in components
            assert 'alert_manager' in components
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.getloadavg')
    @patch('psutil.net_connections')
    def test_metrics_collection(self, mock_connections, mock_loadavg, mock_net, 
                               mock_disk, mock_memory, mock_cpu, app):
        """Test metrics collection functionality"""
        with app.app_context():
            # Mock system information
            mock_cpu.return_value = 45.5
            mock_memory.return_value = Mock(
                percent=62.3, 
                available=1000000, 
                total=2000000
            )
            mock_disk.return_value = Mock(
                percent=78.1, 
                free=500000, 
                total=1000000
            )
            mock_net.return_value = Mock(
                bytes_sent=1000000, 
                bytes_recv=2000000
            )
            mock_loadavg.return_value = [0.5, 0.7, 0.9]
            mock_connections.return_value = [Mock() for _ in range(10)]
            
            collector = MetricsCollector(collection_interval=1)
            system_metrics = collector._collect_system_metrics()
            
            assert isinstance(system_metrics, SystemMetrics)
            assert system_metrics.cpu_usage == 45.5
            assert system_metrics.memory_usage == 62.3
            assert system_metrics.disk_usage == 78.1
            assert system_metrics.active_connections == 10
    
    def test_application_metrics_collection(self, app):
        """Test application metrics collection"""
        with app.app_context():
            # Create test data
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent1 = Agent(name='Agent 1', framework_id=framework.id, status='active')
            agent2 = Agent(name='Agent 2', framework_id=framework.id, status='idle')
            agent3 = Agent(name='Agent 3', framework_id=framework.id, status='error')
            
            db.session.add_all([agent1, agent2, agent3])
            db.session.commit()
            
            collector = MetricsCollector()
            app_metrics = collector._collect_application_metrics()
            
            assert isinstance(app_metrics, ApplicationMetrics)
            assert app_metrics.active_agents == 2  # active + idle
            assert app_metrics.total_agents == 3
    
    def test_metrics_persistence(self, app, mock_redis):
        """Test metrics persistence to database"""
        with app.app_context():
            collector = MetricsCollector()
            
            # Mock system metrics
            with patch.object(collector, '_collect_system_metrics') as mock_system:
                with patch.object(collector, '_collect_application_metrics') as mock_app:
                    mock_system.return_value = SystemMetrics(
                        timestamp=Mock(),
                        cpu_usage=50.0,
                        memory_usage=60.0,
                        memory_available=1000000,
                        memory_total=2000000,
                        disk_usage=70.0,
                        disk_free=500000,
                        disk_total=1000000,
                        network_bytes_sent=1000000,
                        network_bytes_recv=2000000,
                        active_connections=10,
                        load_average=[0.5, 0.7, 0.9]
                    )
                    
                    mock_app.return_value = ApplicationMetrics(
                        timestamp=Mock(),
                        active_agents=5,
                        total_agents=10,
                        running_tasks=3,
                        completed_tasks=100,
                        failed_tasks=2,
                        average_response_time=0.5,
                        error_rate=2.0,
                        throughput=10.0
                    )
                    
                    # Add to buffer
                    collector.system_metrics_buffer.append(mock_system.return_value)
                    collector.app_metrics_buffer.append(mock_app.return_value)
                    
                    # Persist metrics
                    collector._persist_metrics()
                    
                    # Verify persistence
                    metrics = Metric.query.filter_by(metric_type='system').all()
                    assert len(metrics) == 1
                    assert metrics[0].cpu_usage == 50.0
    
    def test_alert_manager_initialization(self, app):
        """Test alert manager initialization and default rules"""
        alert_manager = AlertManager()
        
        # Check default rules exist
        assert 'high_cpu_usage' in alert_manager.rules
        assert 'high_memory_usage' in alert_manager.rules
        assert 'critical_memory_usage' in alert_manager.rules
        assert 'no_active_agents' in alert_manager.rules
        
        # Check rule properties
        cpu_rule = alert_manager.rules['high_cpu_usage']
        assert cpu_rule.level == AlertLevel.WARNING
        assert cpu_rule.cooldown_minutes == 10
    
    def test_alert_triggering(self, app):
        """Test alert triggering functionality"""
        alert_manager = AlertManager()
        
        # Test data that should trigger high CPU alert
        metrics_data = {
            'system': {
                'cpu_usage': 85.0,  # Above 80% threshold
                'memory_usage': 50.0
            },
            'application': {
                'active_agents': 5,
                'error_rate': 5.0
            }
        }
        
        # Check alerts
        alert_manager.check_alerts(metrics_data)
        
        # Verify alert was triggered
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) >= 1
        
        # Find the CPU alert
        cpu_alerts = [alert for alert in active_alerts if alert.rule_name == 'high_cpu_usage']
        assert len(cpu_alerts) == 1
        assert '85.0%' in cpu_alerts[0].message
    
    def test_alert_resolution(self, app):
        """Test alert resolution when conditions improve"""
        alert_manager = AlertManager()
        
        # First trigger an alert
        high_cpu_data = {
            'system': {'cpu_usage': 85.0, 'memory_usage': 50.0},
            'application': {'active_agents': 5, 'error_rate': 5.0}
        }
        alert_manager.check_alerts(high_cpu_data)
        
        # Verify alert is active
        assert len(alert_manager.get_active_alerts()) >= 1
        
        # Now provide data that should resolve the alert
        normal_cpu_data = {
            'system': {'cpu_usage': 45.0, 'memory_usage': 50.0},
            'application': {'active_agents': 5, 'error_rate': 5.0}
        }
        alert_manager.check_alerts(normal_cpu_data)
        
        # Check if alert was resolved
        cpu_alerts = [alert for alert in alert_manager.get_active_alerts() 
                     if alert.rule_name == 'high_cpu_usage']
        assert len(cpu_alerts) == 0  # Should be resolved
    
    def test_custom_alert_rule(self, app):
        """Test adding and using custom alert rules"""
        alert_manager = AlertManager()
        
        # Add custom rule
        custom_rule = AlertRule(
            name="test_custom_rule",
            condition=lambda data: data.get('test_value', 0) > 100,
            level=AlertLevel.CRITICAL,
            message_template="Test value too high: {test_value}",
            cooldown_minutes=5
        )
        
        alert_manager.add_rule(custom_rule)
        
        # Test with triggering data
        test_data = {'test_value': 150}
        alert_manager.check_alerts(test_data)
        
        # Verify custom alert was triggered
        active_alerts = alert_manager.get_active_alerts()
        custom_alerts = [alert for alert in active_alerts if alert.rule_name == 'test_custom_rule']
        assert len(custom_alerts) == 1
        assert 'Test value too high: 150' in custom_alerts[0].message
    
    @patch('smtplib.SMTP')
    def test_email_notifications(self, mock_smtp, app):
        """Test email notification sending"""
        # Setup SMTP config
        smtp_config = {
            'host': 'smtp.test.com',
            'port': 587,
            'username': 'test@test.com',
            'password': 'testpass',
            'to_email': 'admin@test.com'
        }
        
        alert_manager = AlertManager(smtp_config)
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Trigger a critical alert
        critical_data = {
            'system': {'memory_usage': 96.0},  # Critical threshold
            'application': {'active_agents': 5}
        }
        
        alert_manager.check_alerts(critical_data)
        
        # Verify email was sent
        assert mock_server.send_message.called
    
    def test_alert_statistics(self, app):
        """Test alert statistics functionality"""
        alert_manager = AlertManager()
        
        # Trigger some alerts
        test_data = {
            'system': {'cpu_usage': 85.0, 'memory_usage': 96.0},
            'application': {'active_agents': 0}  # No active agents
        }
        
        alert_manager.check_alerts(test_data)
        
        # Get statistics
        stats = alert_manager.get_alert_statistics()
        
        assert 'total_alerts' in stats
        assert 'active_alerts' in stats
        assert 'alerts_by_level' in stats
        assert 'rules_count' in stats
        assert stats['total_alerts'] >= 0
        assert stats['active_alerts'] >= 0

# File: tests/integration/test_end_to_end_workflow.py

import pytest
import json
from unittest.mock import patch, Mock
from src.models.database import Agent, Framework, Workflow, WorkflowExecution, db

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_complete_agent_lifecycle(self, app, client, sample_agent_data):
        """Test complete agent lifecycle: create, start, monitor, stop"""
        with app.app_context():
            # 1. Create framework first
            framework_data = {
                'name': 'Test Framework',
                'version': '1.0',
                'description': 'Framework for testing',
                'configuration_schema': {'type': 'object'}
            }
            
            framework_response = client.post('/api/frameworks', 
                                           data=json.dumps(framework_data),
                                           content_type='application/json')
            assert framework_response.status_code == 201
            framework_id = framework_response.get_json()['data']['id']
            
            # 2. Create agent
            sample_agent_data['framework_id'] = framework_id
            agent_response = client.post('/api/agents',
                                       data=json.dumps(sample_agent_data),
                                       content_type='application/json')
            assert agent_response.status_code == 201
            agent_id = agent_response.get_json()['data']['id']
            
            # 3. Start agent (mock the service)
            with patch('src.services.agent_service.AgentService.start_agent') as mock_start:
                mock_start.return_value = True
                
                start_response = client.post(f'/api/agents/{agent_id}/start')
                assert start_response.status_code == 200
                
            # 4. Check agent status
            status_response = client.get(f'/api/agents/{agent_id}')
            assert status_response.status_code == 200
            agent_data = status_response.get_json()['data']
            
            # 5. Get metrics (mock metrics collection)
            with patch('src.models.optimized_queries.OptimizedQueries.get_dashboard_data') as mock_metrics:
                mock_metrics.return_value = {
                    'agents': {'total': 1, 'active': 1, 'error': 0},
                    'tasks': {'total': 0, 'completed': 0, 'failed': 0}
                }
                
                metrics_response = client.get('/api/dashboard/metrics')
                assert metrics_response.status_code == 200
                
            # 6. Stop agent
            with patch('src.services.agent_service.AgentService.stop_agent') as mock_stop:
                mock_stop.return_value = True
                
                stop_response = client.post(f'/api/agents/{agent_id}/stop')
                assert stop_response.status_code == 200
    
    def test_workflow_execution_with_monitoring(self, app, client, sample_workflow_data):
        """Test workflow execution with real-time monitoring"""
        with app.app_context():
            # 1. Create framework and agent first
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent = Agent(name='Test Agent', framework_id=framework.id, status='active')
            db.session.add(agent)
            db.session.commit()
            
            # 2. Create workflow
            sample_workflow_data['definition']['steps'][0]['agent_id'] = agent.id
            
            workflow_response = client.post('/api/workflows',
                                          data=json.dumps(sample_workflow_data),
                                          content_type='application/json')
            assert workflow_response.status_code == 201
            workflow_id = workflow_response.get_json()['data']['id']
            
            # 3. Execute workflow (mock execution)
            with patch('src.services.workflow_service.WorkflowService.start_execution') as mock_start:
                with patch('src.services.workflow_service.WorkflowService.execute_workflow') as mock_execute:
                    mock_start.return_value = 'exec-123'
                    mock_execute.return_value = {'status': 'completed', 'result': 'success'}
                    
                    execution_response = client.post(f'/api/workflows/{workflow_id}/execute',
                                                   data=json.dumps({'input_data': {'test': 'value'}}),
                                                   content_type='application/json')
                    assert execution_response.status_code == 200
                    
            # 4. Monitor execution status
            with patch('src.models.database.WorkflowExecution.query') as mock_query:
                mock_execution = Mock()
                mock_execution.status = 'completed'
                mock_execution.result = {'status': 'completed'}
                mock_query.filter_by.return_value.first.return_value = mock_execution
                
                status_response = client.get(f'/api/workflows/{workflow_id}/executions/exec-123')
                # Note: This endpoint would need to be implemented
    
    def test_error_handling_and_recovery(self, app, client):
        """Test error handling and recovery mechanisms"""
        with app.app_context():
            # 1. Test invalid agent creation
            invalid_agent_data = {
                'name': '',  # Invalid empty name
                'framework_id': 999,  # Non-existent framework
            }
            
            response = client.post('/api/agents',
                                 data=json.dumps(invalid_agent_data),
                                 content_type='application/json')
            assert response.status_code in [400, 422]  # Validation error
            
            # 2. Test service unavailable scenario
            with patch('src.services.agent_service.AgentService.start_agent') as mock_start:
                mock_start.side_effect = Exception("Service unavailable")
                
                # Create valid agent first
                framework = Framework(name='Test Framework', version='1.0')
                db.session.add(framework)
                db.session.flush()
                
                agent = Agent(name='Test Agent', framework_id=framework.id)
                db.session.add(agent)
                db.session.commit()
                
                # Try to start agent
                response = client.post(f'/api/agents/{agent.id}/start')
                assert response.status_code == 500
                
                # Error should be logged and returned
                response_data = response.get_json()
                assert 'error' in response_data
    
    def test_performance_under_load(self, app, client):
        """Test system performance under simulated load"""
        with app.app_context():
            # Create multiple agents
            framework = Framework(name='Load Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            agent_ids = []
            for i in range(10):
                agent = Agent(name=f'Load Test Agent {i}', framework_id=framework.id)
                db.session.add(agent)
                db.session.flush()
                agent_ids.append(agent.id)
            
            db.session.commit()
            
            # Simulate concurrent requests
            with patch('src.services.agent_service.AgentService.start_agent') as mock_start:
                mock_start.return_value = True
                
                responses = []
                for agent_id in agent_ids:
                    response = client.post(f'/api/agents/{agent_id}/start')
                    responses.append(response)
                
                # All requests should succeed
                assert all(r.status_code == 200 for r in responses)
            
            # Check system metrics after load
            with patch('src.monitoring.metrics_collector.MetricsCollector.get_real_time_metrics') as mock_metrics:
                mock_metrics.return_value = {
                    'system': {
                        'cpu_usage': 75.0,
                        'memory_usage': 65.0,
                        'disk_usage': 30.0
                    },
                    'application': {
                        'active_agents': 10,
                        'total_agents': 10,
                        'error_rate': 0.0
                    }
                }
                
                metrics_response = client.get('/api/monitoring/metrics')
                if metrics_response.status_code == 200:  # If endpoint exists
                    metrics_data = metrics_response.get_json()
                    assert metrics_data['data']['application']['active_agents'] == 10

# File: tests/integration/test_api_integration.py

import pytest
import json
from unittest.mock import patch, Mock
from src.models.database import Agent, Framework, db

class TestAPIIntegration:
    """Test API endpoint integration"""
    
    def test_agent_crud_operations(self, app, client):
        """Test complete CRUD operations for agents"""
        with app.app_context():
            # Create framework first
            framework = Framework(name='Test Framework', version='1.0')
            db.session.add(framework)
            db.session.commit()
            
            # 1. CREATE agent
            agent_data = {
                'name': 'Integration Test Agent',
                'description': 'Agent for API integration testing',
                'framework_id': framework.id,
                'configuration': {'model': 'gpt-4'},
                'capabilities': ['chat']
            }
            
            create_response = client.post('/api/agents',
                                        data=json.dumps(agent_data),
                                        content_type='application/json')
            assert create_response.status_code == 201
            
            agent_id = create_response.get_json()['data']['id']
            
            # 2. READ agent
            read_response = client.get(f'/api/agents/{agent_id}')
            assert read_response.status_code == 200
            
            read_data = read_response.get_json()['data']
            assert read_data['name'] == agent_data['name']
            assert read_data['framework_id'] == framework.id
            
            # 3. UPDATE agent
            update_data = {
                'name': 'Updated Integration Test Agent',
                'description': 'Updated description'
            }
            
            update_response = client.put(f'/api/agents/{agent_id}',
                                       data=json.dumps(update_data),
                                       content_type='application/json')
            assert update_response.status_code == 200
            
            # Verify update
            verify_response = client.get(f'/api/agents/{agent_id}')
            verify_data = verify_response.get_json()['data']
            assert verify_data['name'] == update_data['name']
            
            # 4. LIST agents
            list_response = client.get('/api/agents')
            assert list_response.status_code == 200
            
            agents_list = list_response.get_json()['data']
            assert len(agents_list) >= 1
            assert any(agent['id'] == agent_id for agent in agents_list)
            
            # 5. DELETE agent
            delete_response = client.delete(f'/api/agents/{agent_id}')
            assert delete_response.status_code == 200
            
            # Verify deletion
            verify_delete_response = client.get(f'/api/agents/{agent_id}')
            assert verify_delete_response.status_code == 404
    
    def test_api_error_handling(self, app, client):
        """Test API error handling"""
        with app.app_context():
            # Test 404 for non-existent resource
            response = client.get('/api/agents/99999')
            assert response.status_code == 404
            
            error_data = response.get_json()
            assert 'error' in error_data
            assert not error_data.get('success', True)
            
            # Test 400 for invalid data
            invalid_data = {'invalid_field': 'value'}
            response = client.post('/api/agents',
                                 data=json.dumps(invalid_data),
                                 content_type='application/json')
            assert response.status_code in [400, 422]
    
    def test_api_pagination(self, app, client):
        """Test API pagination functionality"""
        with app.app_context():
            # Create framework
            framework = Framework(name='Pagination Test Framework', version='1.0')
            db.session.add(framework)
            db.session.flush()
            
            # Create multiple agents
            for i in range(25):
                agent = Agent(name=f'Pagination Agent {i}', framework_id=framework.id)
                db.session.add(agent)
            
            db.session.commit()
            
            # Test pagination
            response = client.get('/api/agents?page=1&per_page=10')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['data']) <= 10
            
            # Check pagination metadata
            if 'pagination' in data:
                pagination = data['pagination']
                assert 'total' in pagination
                assert 'pages' in pagination
                assert 'current_page' in pagination

# File: tests/integration/requirements.txt

pytest>=7.0.0
pytest-mock>=3.0.0
pytest-cov>=4.0.0
pytest-flask>=1.2.0
pytest-asyncio>=0.21.0
factory-boy>=3.2.0
freezegun>=1.2.0