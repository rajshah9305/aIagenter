# Phase 3: Database Query Optimization & Caching
# File: src/utils/db_optimization.py

import functools
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Union
from flask import current_app
from sqlalchemy import event, text
from sqlalchemy.pool import Pool
from redis import Redis
from src.models.database import db

class QueryOptimizer:
    """Advanced database query optimization and caching"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds
        
    def setup_query_monitoring(self):
        """Setup query performance monitoring"""
        
        @event.listens_for(db.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            
        @event.listens_for(db.engine, "after_cursor_execute") 
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Log slow queries
            if total > self.slow_query_threshold:
                current_app.logger.warning(
                    f"Slow query detected: {total:.3f}s\n{statement[:200]}..."
                )
            
            # Update query statistics
            query_hash = hashlib.md5(statement.encode()).hexdigest()[:8]
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'statement': statement[:100] + '...' if len(statement) > 100 else statement
                }
            
            stats = self.query_stats[query_hash]
            stats['count'] += 1
            stats['total_time'] += total
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], total)

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        return {
            'total_queries': sum(stat['count'] for stat in self.query_stats.values()),
            'slow_queries': len([s for s in self.query_stats.values() if s['max_time'] > self.slow_query_threshold]),
            'queries': sorted(
                self.query_stats.values(), 
                key=lambda x: x['avg_time'], 
                reverse=True
            )[:10]  # Top 10 slowest queries
        }

class CacheManager:
    """Advanced caching with Redis backend"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
        
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"agentorchestra:{prefix}:{key_hash}"
    
    def cached(self, ttl: Optional[int] = None, prefix: str = "default"):
        """Decorator for caching function results"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
                
                # Try to get from cache
                try:
                    cached_result = self.redis.get(cache_key)
                    if cached_result:
                        return json.loads(cached_result)
                except Exception as e:
                    current_app.logger.warning(f"Cache get error: {e}")
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                
                try:
                    self.redis.setex(
                        cache_key,
                        ttl or self.default_ttl,
                        json.dumps(result, default=str)
                    )
                except Exception as e:
                    current_app.logger.warning(f"Cache set error: {e}")
                
                return result
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            keys = self.redis.keys(f"agentorchestra:{pattern}*")
            if keys:
                self.redis.delete(*keys)
                return len(keys)
        except Exception as e:
            current_app.logger.error(f"Cache invalidation error: {e}")
        return 0

# File: src/models/optimized_queries.py

from sqlalchemy import func, and_, or_
from src.models.database import Agent, Framework, Task, Metric
from src.utils.db_optimization import CacheManager

class OptimizedQueries:
    """Optimized database queries with caching"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    @property 
    def cached(self):
        return self.cache.cached
    
    @cached(ttl=600, prefix="agents")
    def get_active_agents_summary(self) -> List[Dict[str, Any]]:
        """Get summary of active agents with optimized query"""
        return db.session.query(
            Agent.id,
            Agent.name,
            Agent.status,
            Agent.framework_id,
            Framework.name.label('framework_name'),
            func.count(Task.id).label('task_count')
        ).join(
            Framework, Agent.framework_id == Framework.id
        ).outerjoin(
            Task, and_(Agent.id == Task.agent_id, Task.status == 'running')
        ).filter(
            Agent.status.in_(['active', 'idle'])
        ).group_by(
            Agent.id, Agent.name, Agent.status, Agent.framework_id, Framework.name
        ).all()
    
    @cached(ttl=300, prefix="metrics")
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics with caching"""
        cutoff_time = func.datetime('now', f'-{hours} hours')
        
        # Optimized query using window functions
        metrics_query = db.session.query(
            func.avg(Metric.cpu_usage).label('avg_cpu'),
            func.max(Metric.cpu_usage).label('max_cpu'),
            func.avg(Metric.memory_usage).label('avg_memory'),
            func.max(Metric.memory_usage).label('max_memory'),
            func.count(Metric.id).label('total_metrics')
        ).filter(
            Metric.created_at >= cutoff_time
        ).first()
        
        return {
            'avg_cpu': float(metrics_query.avg_cpu or 0),
            'max_cpu': float(metrics_query.max_cpu or 0),
            'avg_memory': float(metrics_query.avg_memory or 0),
            'max_memory': float(metrics_query.max_memory or 0),
            'total_metrics': metrics_query.total_metrics
        }
    
    @cached(ttl=180, prefix="dashboard")
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data in single optimized query"""
        # Use CTE for complex dashboard queries
        agent_stats = db.session.query(
            func.count(Agent.id).label('total_agents'),
            func.sum(func.case([(Agent.status == 'active', 1)], else_=0)).label('active_agents'),
            func.sum(func.case([(Agent.status == 'error', 1)], else_=0)).label('error_agents')
        ).first()
        
        task_stats = db.session.query(
            func.count(Task.id).label('total_tasks'),
            func.sum(func.case([(Task.status == 'completed', 1)], else_=0)).label('completed_tasks'),
            func.sum(func.case([(Task.status == 'failed', 1)], else_=0)).label('failed_tasks')
        ).first()
        
        return {
            'agents': {
                'total': agent_stats.total_agents,
                'active': agent_stats.active_agents,
                'error': agent_stats.error_agents
            },
            'tasks': {
                'total': task_stats.total_tasks,
                'completed': task_stats.completed_tasks,
                'failed': task_stats.failed_tasks
            }
        }
    
    def bulk_update_agent_status(self, agent_ids: List[int], status: str):
        """Optimized bulk update with cache invalidation"""
        # Bulk update
        db.session.query(Agent).filter(
            Agent.id.in_(agent_ids)
        ).update(
            {Agent.status: status}, 
            synchronize_session=False
        )
        
        # Invalidate related caches
        self.cache.invalidate_pattern("agents")
        self.cache.invalidate_pattern("dashboard")
        
        db.session.commit()
    
    def cleanup_old_metrics(self, days: int = 7):
        """Cleanup old metrics with optimized query"""
        cutoff_date = func.datetime('now', f'-{days} days')
        
        deleted_count = db.session.query(Metric).filter(
            Metric.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        db.session.commit()
        current_app.logger.info(f"Cleaned up {deleted_count} old metrics")
        return deleted_count

# File: src/utils/connection_pool.py

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool, StaticPool
import redis.connection
from redis.connection import ConnectionPool

class DatabasePoolManager:
    """Manage database connection pools for optimal performance"""
    
    @staticmethod
    def create_optimized_engine(database_uri: str, **kwargs):
        """Create optimized SQLAlchemy engine"""
        
        # Default optimizations
        default_options = {
            'poolclass': QueuePool,
            'pool_size': 20,
            'max_overflow': 30,
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # 1 hour
            'echo': False,
            'connect_args': {
                'check_same_thread': False if 'sqlite' in database_uri else {},
                'timeout': 30,
            }
        }
        
        # Merge with provided options
        engine_options = {**default_options, **kwargs}
        
        # Create engine
        engine = create_engine(database_uri, **engine_options)
        
        # Setup engine events for monitoring
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if 'sqlite' in database_uri:
                cursor = dbapi_connection.cursor()
                # SQLite optimizations
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL") 
                cursor.execute("PRAGMA cache_size=1000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        return engine
    
    @staticmethod
    def create_redis_pool(redis_url: str) -> ConnectionPool:
        """Create optimized Redis connection pool"""
        return ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )

# File: src/extensions.py (Updated)

from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from src.utils.db_optimization import QueryOptimizer, CacheManager
from src.utils.connection_pool import DatabasePoolManager

# Global instances
db = SQLAlchemy()
redis_client = None
query_optimizer = None
cache_manager = None

def init_extensions(app):
    """Initialize all extensions with optimizations"""
    global redis_client, query_optimizer, cache_manager
    
    # Initialize database with optimized engine
    if not app.config.get('TESTING'):
        # Replace default engine with optimized one
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
        db.init_app(app)
        
        # Setup optimized engine
        optimized_engine = DatabasePoolManager.create_optimized_engine(
            app.config['SQLALCHEMY_DATABASE_URI']
        )
        db.engine = optimized_engine
    else:
        db.init_app(app)
    
    # Initialize Redis with connection pool
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_pool = DatabasePoolManager.create_redis_pool(redis_url)
    redis_client = Redis(connection_pool=redis_pool)
    
    # Initialize optimization tools
    query_optimizer = QueryOptimizer(redis_client)
    cache_manager = CacheManager(redis_client)
    
    # Setup query monitoring in non-testing environments
    if not app.config.get('TESTING'):
        query_optimizer.setup_query_monitoring()
    
    return {
        'db': db,
        'redis': redis_client,
        'query_optimizer': query_optimizer,
        'cache_manager': cache_manager
    }