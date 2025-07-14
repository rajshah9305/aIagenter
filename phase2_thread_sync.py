# =============================================================================
# PHASE 2: THREAD SYNCHRONIZATION AND CONCURRENCY MANAGEMENT
# =============================================================================

# File: src/utils/threading.py
# Purpose: Thread synchronization utilities and patterns
# =============================================================================

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, Set
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)

class LockType(Enum):
    """Types of locks available"""
    REENTRANT = "reentrant"
    REGULAR = "regular"
    READ_WRITE = "read_write"
    SEMAPHORE = "semaphore"

class ThreadSafeCounter:
    """Thread-safe counter with atomic operations"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1) -> int:
        """Atomically increment counter"""
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount: int = 1) -> int:
        """Atomically decrement counter"""
        with self._lock:
            self._value -= amount
            return self._value
    
    def reset(self, value: int = 0) -> int:
        """Atomically reset counter"""
        with self._lock:
            old_value = self._value
            self._value = value
            return old_value
    
    @property
    def value(self) -> int:
        """Get current value"""
        with self._lock:
            return self._value

class ReadWriteLock:
    """Read-Write lock implementation for reader-writer scenarios"""
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
    
    @contextmanager
    def read_lock(self):
        """Acquire read lock"""
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()
        
        try:
            yield
        finally:
            self._read_ready.acquire()
            try:
                self._readers -= 1
                if self._readers == 0:
                    self._read_ready.notifyAll()
            finally:
                self._read_ready.release()
    
    @contextmanager
    def write_lock(self):
        """Acquire write lock"""
        self._read_ready.acquire()
        try:
            while self._readers > 0:
                self._read_ready.wait()
            yield
        finally:
            self._read_ready.release()

class ThreadSafeDict:
    """Thread-safe dictionary with atomic operations"""
    
    def __init__(self, initial_data: Dict[Any, Any] = None):
        self._data = initial_data or {}
        self._lock = threading.RLock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Thread-safe get"""
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: Any, value: Any) -> None:
        """Thread-safe set"""
        with self._lock:
            self._data[key] = value
    
    def update(self, updates: Dict[Any, Any]) -> None:
        """Thread-safe update"""
        with self._lock:
            self._data.update(updates)
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """Thread-safe pop"""
        with self._lock:
            return self._data.pop(key, default)
    
    def keys(self) -> Set[Any]:
        """Thread-safe keys"""
        with self._lock:
            return set(self._data.keys())
    
    def values(self) -> list:
        """Thread-safe values"""
        with self._lock:
            return list(self._data.values())
    
    def items(self) -> list:
        """Thread-safe items"""
        with self._lock:
            return list(self._data.items())
    
    def copy(self) -> Dict[Any, Any]:
        """Thread-safe copy"""
        with self._lock:
            return self._data.copy()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
    
    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self._data

class LockManager:
    """Centralized lock manager to prevent deadlocks"""
    
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = {}
        self._lock_order: Dict[str, int] = {}
        self._manager_lock = threading.Lock()
        self._next_order = 0
    
    def get_lock(self, name: str, lock_type: LockType = LockType.REENTRANT) -> threading.Lock:
        """Get or create a named lock"""
        with self._manager_lock:
            if name not in self._locks:
                if lock_type == LockType.REENTRANT:
                    self._locks[name] = threading.RLock()
                elif lock_type == LockType.REGULAR:
                    self._locks[name] = threading.Lock()
                elif lock_type == LockType.READ_WRITE:
                    self._locks[name] = ReadWriteLock()
                else:
                    raise ValueError(f"Unsupported lock type: {lock_type}")
                
                self._lock_order[name] = self._next_order
                self._next_order += 1
            
            return self._locks[name]
    
    @contextmanager
    def acquire_multiple(self, *lock_names: str):
        """Acquire multiple locks in consistent order to prevent deadlock"""
        # Sort locks by their order to prevent deadlock
        sorted_names = sorted(lock_names, key=lambda name: self._lock_order.get(name, 0))
        locks = [self.get_lock(name) for name in sorted_names]
        
        acquired = []
        try:
            for lock in locks:
                lock.acquire()
                acquired.append(lock)
            yield
        finally:
            # Release in reverse order
            for lock in reversed(acquired):
                lock.release()

class ThreadPool:
    """Simple thread pool for executing tasks"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self._workers = []
        self._task_queue = []
        self._queue_lock = threading.Lock()
        self._queue_condition = threading.Condition(self._queue_lock)
        self._shutdown = False
        self._active_tasks = ThreadSafeCounter()
        
        # Start worker threads
        for i in range(max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"ThreadPoolWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
    
    def submit(self, func: Callable, *args, **kwargs) -> None:
        """Submit a task to the thread pool"""
        if self._shutdown:
            raise RuntimeError("Cannot submit task to shutdown thread pool")
        
        task = (func, args, kwargs)
        
        with self._queue_condition:
            self._task_queue.append(task)
            self._queue_condition.notify()
    
    def shutdown(self, timeout: float = 5.0) -> bool:
        """Shutdown the thread pool"""
        self._shutdown = True
        
        # Wake up all workers
        with self._queue_condition:
            self._queue_condition.notify_all()
        
        # Wait for workers to finish
        start_time = time.time()
        for worker in self._workers:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                worker.join(timeout=remaining_time)
        
        return all(not worker.is_alive() for worker in self._workers)
    
    def _worker_loop(self):
        """Worker thread main loop"""
        while not self._shutdown:
            task = None
            
            with self._queue_condition:
                while not self._task_queue and not self._shutdown:
                    self._queue_condition.wait()
                
                if self._task_queue:
                    task = self._task_queue.pop(0)
            
            if task:
                func, args, kwargs = task
                self._active_tasks.increment()
                
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in thread pool task: {e}")
                finally:
                    self._active_tasks.decrement()
    
    @property
    def active_tasks(self) -> int:
        """Get number of active tasks"""
        return self._active_tasks.value

# =============================================================================
# File: src/utils/concurrency.py
# Purpose: Concurrency patterns and utilities
# =============================================================================

import asyncio
import concurrent.futures
from typing import List, Callable, Any, Optional
from functools import wraps

class AsyncBatchProcessor:
    """Process items in batches asynchronously"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 5):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    async def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        """Process a batch of items asynchronously"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for item in items:
                task = loop.run_in_executor(executor, processor, item)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    async def process_all(self, items: List[Any], processor: Callable) -> List[Any]:
        """Process all items in batches"""
        all_results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await self.process_batch(batch, processor)
            all_results.extend(batch_results)
        
        return all_results

def synchronized(lock_name: str = None):
    """Decorator to synchronize method access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Use instance-specific lock or named lock
            if lock_name:
                lock = getattr(self, f'_{lock_name}_lock', None)
                if not lock:
                    lock = threading.RLock()
                    setattr(self, f'_{lock_name}_lock', lock)
            else:
                # Default instance lock
                if not hasattr(self, '_sync_lock'):
                    self._sync_lock = threading.RLock()
                lock = self._sync_lock
            
            with lock:
                return func(self, *args, **kwargs)
        return wrapper
    return decorator

def thread_safe_property(func: Callable) -> property:
    """Create a thread-safe property"""
    attr_name = f'_{func.__name__}_value'
    lock_name = f'_{func.__name__}_lock'
    
    def getter(self):
        if not hasattr(self, lock_name):
            setattr(self, lock_name, threading.RLock())
        
        lock = getattr(self, lock_name)
        with lock:
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)
    
    def setter(self, value):
        if not hasattr(self, lock_name):
            setattr(self, lock_name, threading.RLock())
        
        lock = getattr(self, lock_name)
        with lock:
            setattr(self, attr_name, value)
    
    return property(getter, setter)

class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls = []
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed under rate limit"""
        now = time.time()
        
        with self._lock:
            # Remove old calls outside the time window
            self._calls = [call_time for call_time in self._calls 
                          if now - call_time < self.time_window]
            
            # Check if we can make another call
            if len(self._calls) < self.max_calls:
                self._calls.append(now)
                return True
            
            return False
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded"""
        while not self.is_allowed():
            time.sleep(0.1)

# =============================================================================
# File: src/services/thread_safe_orchestration.py
# Purpose: Thread-safe orchestration engine implementation
# =============================================================================

import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.connectors.base import FrameworkConnector, AgentStatus, TaskStatus
from src.connectors.autogen_connector import AutoGenConnector
from src.connectors.crewai_connector import CrewAIConnector
from src.services.base import BaseService
from src.utils.threading import ThreadSafeDict, ThreadSafeCounter, LockManager, synchronized

class ThreadSafeOrchestrationEngine(BaseService):
    """Thread-safe orchestration engine with proper synchronization"""
    
    def __init__(self):
        super().__init__("OrchestrationEngine")
        
        # Thread-safe data structures
        self.connectors: Dict[str, FrameworkConnector] = {}
        self.agent_registry = ThreadSafeDict()
        self.task_queue = []
        self.running_tasks = ThreadSafeDict()
        self.message_bus = []
        self.task_counter = ThreadSafeCounter()
        
        # Synchronization
        self.lock_manager = LockManager()
        self._task_queue_lock = threading.RLock()
        self._message_bus_lock = threading.RLock()
        self._worker_threads = []
        
        # Initialize connectors
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize framework connectors with thread safety"""
        with self.lock_manager.get_lock("connectors"):
            self.connectors['autogen'] = AutoGenConnector()
            self.connectors['crewai'] = CrewAIConnector()
    
    def _start_implementation(self):
        """Start the orchestration engine"""
        # Start worker threads
        for i in range(3):  # 3 worker threads
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"OrchestrationWorker-{i}",
                daemon=True
            )
            self._worker_threads.append(worker)
            worker.start()
        
        logger.info("Thread-safe orchestration engine started with worker threads")
    
    def _stop_implementation(self):
        """Stop the orchestration engine"""
        # Worker threads will stop when is_running becomes False
        for worker in self._worker_threads:
            if worker.is_alive():
                worker.join(timeout=5)
        
        self._worker_threads.clear()
        logger.info("Thread-safe orchestration engine stopped")
    
    @synchronized("agent_operations")
    def register_agent(self, framework: str, agent_config: Dict[str, Any]) -> str:
        """Thread-safe agent registration"""
        if framework not in self.connectors:
            raise ValueError(f"Framework '{framework}' not supported")
        
        connector = self.connectors[framework]
        agent_id = connector.create_agent(agent_config)
        
        # Register in central registry
        agent_info = {
            'framework': framework,
            'connector': connector,
            'config': agent_config,
            'registered_at': datetime.utcnow(),
            'status': AgentStatus.INACTIVE
        }
        
        self.agent_registry.set(agent_id, agent_info)
        
        logger.info(f"Agent {agent_id} registered successfully")
        return agent_id
    
    @synchronized("agent_operations")
    def unregister_agent(self, agent_id: str) -> bool:
        """Thread-safe agent unregistration"""
        agent_info = self.agent_registry.get(agent_id)
        if not agent_info:
            return False
        
        connector = agent_info['connector']
        
        # Stop and delete the agent
        connector.stop_agent(agent_id)
        connector.delete_agent(agent_id)
        
        # Remove from registry
        self.agent_registry.pop(agent_id)
        
        logger.info(f"Agent {agent_id} unregistered successfully")
        return True
    
    @synchronized("agent_operations")
    def start_agent(self, agent_id: str) -> bool:
        """Thread-safe agent start"""
        agent_info = self.agent_registry.get(agent_id)
        if not agent_info:
            return False
        
        connector = agent_info['connector']
        success = connector.start_agent(agent_id)
        
        if success:
            agent_info['status'] = AgentStatus.ACTIVE
            self.agent_registry.set(agent_id, agent_info)
        
        return success
    
    def submit_task(self, agent_id: str, task_data: Dict[str, Any], priority: int = 5) -> str:
        """Thread-safe task submission"""
        agent_info = self.agent_registry.get(agent_id)
        if not agent_info:
            raise ValueError(f"Agent {agent_id} not found")
        
        task_id = f"task_{self.task_counter.increment()}_{agent_id[:8]}"
        
        task_info = {
            'id': task_id,
            'agent_id': agent_id,
            'task_data': task_data,
            'priority': priority,
            'submitted_at': datetime.utcnow(),
            'status': 'queued'
        }
        
        # Add to task queue with proper synchronization
        with self._task_queue_lock:
            self.task_queue.append(task_info)
            self.task_queue.sort(key=lambda x: x['priority'])
        
        logger.info(f"Task {task_id} submitted for agent {agent_id}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Thread-safe task status retrieval"""
        # Check running tasks
        task_info = self.running_tasks.get(task_id)
        if task_info:
            return task_info['status']
        
        # Check queued tasks
        with self._task_queue_lock:
            for task in self.task_queue:
                if task['id'] == task_id:
                    return task['status']
        
        return None
    
    def send_inter_agent_message(self, from_agent_id: str, to_agent_id: str, message: Dict[str, Any]) -> bool:
        """Thread-safe inter-agent messaging"""
        from_agent = self.agent_registry.get(from_agent_id)
        to_agent = self.agent_registry.get(to_agent_id)
        
        if not from_agent or not to_agent:
            return False
        
        # If agents are in the same framework, use framework-specific messaging
        if from_agent['framework'] == to_agent['framework']:
            connector = from_agent['connector']
            return connector.send_message(from_agent_id, to_agent_id, message)
        
        # Cross-framework messaging via message bus
        message_info = {
            'id': f"msg_{int(time.time() * 1000)}",
            'from_agent_id': from_agent_id,
            'to_agent_id': to_agent_id,
            'message': message,
            'timestamp': datetime.utcnow(),
            'status': 'delivered'
        }
        
        with self._message_bus_lock:
            self.message_bus.append(message_info)
        
        logger.info(f"Cross-framework message sent: {from_agent_id} -> {to_agent_id}")
        return True
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """Thread-safe agent listing"""
        agents = []
        for agent_id, agent_info in self.agent_registry.items():
            agents.append({
                'id': agent_id,
                'framework': agent_info['framework'],
                'status': agent_info['status'].value if hasattr(agent_info['status'], 'value') else str(agent_info['status']),
                'registered_at': agent_info['registered_at'].isoformat()
            })
        return agents
    
    def _health_check_implementation(self) -> Dict[str, Any]:
        """Thread-safe health check"""
        return {
            'registered_agents': len(self.agent_registry),
            'queued_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'message_bus_size': len(self.message_bus),
            'worker_threads': len([t for t in self._worker_threads if t.is_alive()])
        }
    
    def _worker_loop(self):
        """Thread-safe worker loop for processing tasks"""
        while self.is_running:
            try:
                # Process queued tasks
                task_info = None
                
                with self._task_queue_lock:
                    if self.task_queue:
                        task_info = self.task_queue.pop(0)
                
                if task_info:
                    self._execute_task(task_info)
                
                # Check running tasks for completion
                self._check_running_tasks()
                
                # Clean up old messages
                self._cleanup_message_bus()
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error in orchestration worker loop: {e}")
                time.sleep(1)
    
    def _execute_task(self, task_info: Dict[str, Any]):
        """Execute a task with proper thread safety"""
        agent_id = task_info['agent_id']
        agent_info = self.agent_registry.get(agent_id)
        
        if not agent_info:
            logger.error(f"Agent {agent_id} not found for task {task_info['id']}")
            return
        
        connector = agent_info['connector']
        
        try:
            # Execute the task
            framework_task_id = connector.execute_task(agent_id, task_info['task_data'])
            
            # Track the running task
            task_info['framework_task_id'] = framework_task_id
            task_info['status'] = 'running'
            task_info['started_at'] = datetime.utcnow()
            
            self.running_tasks.set(task_info['id'], task_info)
            
            logger.info(f"Task {task_info['id']} started execution")
            
        except Exception as e:
            logger.error(f"Error executing task {task_info['id']}: {e}")
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
    
    def _check_running_tasks(self):
        """Check running tasks for completion"""
        completed_tasks = []
        
        for task_id, task_info in self.running_tasks.items():
            agent_id = task_info['agent_id']
            framework_task_id = task_info['framework_task_id']
            
            agent_info = self.agent_registry.get(agent_id)
            if not agent_info:
                continue
            
            connector = agent_info['connector']
            
            try:
                # Check task status
                status = connector.get_task_status(framework_task_id)
                
                if status == TaskStatus.COMPLETED:
                    result = connector.get_task_result(framework_task_id)
                    task_info['status'] = 'completed'
                    task_info['result'] = result
                    task_info['completed_at'] = datetime.utcnow()
                    completed_tasks.append(task_id)
                    
                elif status == TaskStatus.FAILED:
                    task_info['status'] = 'failed'
                    task_info['completed_at'] = datetime.utcnow()
                    completed_tasks.append(task_id)
                    
            except Exception as e:
                logger.error(f"Error checking task {task_id}: {e}")
                task_info['status'] = 'error'
                task_info['error'] = str(e)
                completed_tasks.append(task_id)
        
        # Keep completed tasks for result retrieval
        # In production, move to a completed tasks store
    
    def _cleanup_message_bus(self):
        """Clean up old messages from the message bus"""
        cutoff_time = datetime.utcnow().timestamp() - 3600  # 1 hour
        
        with self._message_bus_lock:
            self.message_bus = [
                msg for msg in self.message_bus 
                if msg['timestamp'].timestamp() > cutoff_time
            ]

# Global thread-safe lock manager instance
lock_manager = LockManager()