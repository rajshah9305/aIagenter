import uuid
import time
import threading
import heapq
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json

class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Task:
    """Represents a task in the system."""
    
    def __init__(self, task_id: str = None, agent_id: str = None, task_data: Dict[str, Any] = None,
                 priority: TaskPriority = TaskPriority.NORMAL, timeout_seconds: int = 300,
                 retry_count: int = 0, max_retries: int = 3, dependencies: List[str] = None):
        self.id = task_id or str(uuid.uuid4())
        self.agent_id = agent_id
        self.task_data = task_data or {}
        self.priority = priority
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.dependencies = dependencies or []
        
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.queued_at = None
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.execution_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'task_data': self.task_data,
            'priority': self.priority.value,
            'timeout_seconds': self.timeout_seconds,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'queued_at': self.queued_at.isoformat() if self.queued_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time
        }
    
    def is_ready_to_execute(self, completed_tasks: set) -> bool:
        """Check if task dependencies are satisfied."""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def is_expired(self) -> bool:
        """Check if task has exceeded its timeout."""
        if self.started_at and self.timeout_seconds > 0:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            return elapsed > self.timeout_seconds
        return False

class TaskQueue:
    """Priority-based task queue with dependency management."""
    
    def __init__(self):
        self.queue = []  # Priority queue (heap)
        self.tasks = {}  # task_id -> Task
        self.agent_queues = defaultdict(deque)  # agent_id -> deque of task_ids
        self.completed_tasks = set()  # Set of completed task IDs
        self.lock = threading.RLock()
        
    def add_task(self, task: Task) -> bool:
        """Add a task to the queue."""
        with self.lock:
            if task.id in self.tasks:
                return False
            
            self.tasks[task.id] = task
            task.status = TaskStatus.QUEUED
            task.queued_at = datetime.utcnow()
            
            # Add to priority queue (negative priority for max-heap behavior)
            priority_score = -task.priority.value
            heapq.heappush(self.queue, (priority_score, task.created_at.timestamp(), task.id))
            
            # Add to agent-specific queue if agent is specified
            if task.agent_id:
                self.agent_queues[task.agent_id].append(task.id)
            
            return True
    
    def get_next_task(self, agent_id: str = None) -> Optional[Task]:
        """Get the next available task for execution."""
        with self.lock:
            if agent_id:
                # Get next task for specific agent
                agent_queue = self.agent_queues.get(agent_id, deque())
                
                while agent_queue:
                    task_id = agent_queue.popleft()
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        if (task.status == TaskStatus.QUEUED and 
                            task.is_ready_to_execute(self.completed_tasks)):
                            return task
            else:
                # Get next task from global priority queue
                while self.queue:
                    _, _, task_id = heapq.heappop(self.queue)
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        if (task.status == TaskStatus.QUEUED and 
                            task.is_ready_to_execute(self.completed_tasks)):
                            return task
            
            return None
    
    def mark_task_running(self, task_id: str) -> bool:
        """Mark a task as running."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
                return True
            return False
    
    def mark_task_completed(self, task_id: str, result: Any = None) -> bool:
        """Mark a task as completed."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                
                if task.started_at:
                    task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
                self.completed_tasks.add(task_id)
                return True
            return False
    
    def mark_task_failed(self, task_id: str, error: str = None) -> bool:
        """Mark a task as failed."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error = error
                
                if task.started_at:
                    task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
                return True
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        with self.lock:
            return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks for a specific agent."""
        with self.lock:
            return [task for task in self.tasks.values() if task.agent_id == agent_id]
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self.lock:
            status_counts = defaultdict(int)
            for task in self.tasks.values():
                status_counts[task.status.value] += 1
            
            return {
                'total_tasks': len(self.tasks),
                'queued_tasks': len(self.queue),
                'completed_tasks': len(self.completed_tasks),
                'status_breakdown': dict(status_counts),
                'agent_queues': {agent_id: len(queue) for agent_id, queue in self.agent_queues.items()}
            }

class TaskDistributionEngine:
    """Main engine for task distribution and management."""
    
    def __init__(self):
        self.task_queue = TaskQueue()
        self.agent_capabilities = {}  # agent_id -> set of capabilities
        self.agent_load = defaultdict(int)  # agent_id -> current task count
        self.task_callbacks = {}  # task_id -> callback function
        self.is_running = False
        self.distribution_thread = None
        self.monitoring_thread = None
        
    def start(self):
        """Start the task distribution engine."""
        if self.is_running:
            return
            
        self.is_running = True
        self.distribution_thread = threading.Thread(target=self._distribution_loop, daemon=True)
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        
        self.distribution_thread.start()
        self.monitoring_thread.start()
        
        print("Task distribution engine started")
    
    def stop(self):
        """Stop the task distribution engine."""
        self.is_running = False
        
        if self.distribution_thread:
            self.distribution_thread.join(timeout=5)
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
        print("Task distribution engine stopped")
    
    def register_agent_capabilities(self, agent_id: str, capabilities: List[str]):
        """Register agent capabilities for task matching."""
        self.agent_capabilities[agent_id] = set(capabilities)
    
    def submit_task(self, task_data: Dict[str, Any], agent_id: str = None, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   timeout_seconds: int = 300, dependencies: List[str] = None,
                   callback: Callable = None) -> str:
        """Submit a new task for execution."""
        task = Task(
            agent_id=agent_id,
            task_data=task_data,
            priority=priority,
            timeout_seconds=timeout_seconds,
            dependencies=dependencies or []
        )
        
        if self.task_queue.add_task(task):
            if callback:
                self.task_callbacks[task.id] = callback
            return task.id
        else:
            raise ValueError(f"Failed to add task {task.id}")
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        task = self.task_queue.get_task(task_id)
        return task.status.value if task else None
    
    def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task."""
        task = self.task_queue.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or queued task."""
        task = self.task_queue.get_task(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            return True
        return False
    
    def get_agent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific agent."""
        tasks = self.task_queue.get_tasks_by_agent(agent_id)
        return [task.to_dict() for task in tasks]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide task statistics."""
        queue_stats = self.task_queue.get_queue_stats()
        
        return {
            **queue_stats,
            'registered_agents': len(self.agent_capabilities),
            'agent_load': dict(self.agent_load),
            'active_callbacks': len(self.task_callbacks)
        }
    
    def find_suitable_agent(self, required_capabilities: List[str]) -> Optional[str]:
        """Find the most suitable agent for a task based on capabilities and load."""
        suitable_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if all(cap in capabilities for cap in required_capabilities):
                load = self.agent_load[agent_id]
                suitable_agents.append((agent_id, load))
        
        if suitable_agents:
            # Return agent with lowest load
            return min(suitable_agents, key=lambda x: x[1])[0]
        
        return None
    
    def _distribution_loop(self):
        """Main distribution loop."""
        while self.is_running:
            try:
                # Process tasks without specific agents
                task = self.task_queue.get_next_task()
                if task:
                    # Find suitable agent based on task requirements
                    required_capabilities = task.task_data.get('required_capabilities', [])
                    suitable_agent = self.find_suitable_agent(required_capabilities)
                    
                    if suitable_agent:
                        task.agent_id = suitable_agent
                        self._execute_task(task)
                    else:
                        # No suitable agent found, re-queue for later
                        time.sleep(1)
                
                # Process agent-specific tasks
                for agent_id in list(self.agent_capabilities.keys()):
                    agent_task = self.task_queue.get_next_task(agent_id)
                    if agent_task:
                        self._execute_task(agent_task)
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Error in task distribution loop: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: Task):
        """Execute a task (simulate execution for now)."""
        try:
            self.task_queue.mark_task_running(task.id)
            self.agent_load[task.agent_id] += 1
            
            # Simulate task execution
            # In a real implementation, this would delegate to the actual agent
            print(f"Executing task {task.id} on agent {task.agent_id}")
            
            # Simulate some processing time
            time.sleep(0.1)
            
            # Mark as completed with mock result
            result = {
                'status': 'success',
                'output': f"Task {task.id} completed successfully",
                'execution_time': 0.1
            }
            
            self.task_queue.mark_task_completed(task.id, result)
            self.agent_load[task.agent_id] -= 1
            
            # Call callback if registered
            if task.id in self.task_callbacks:
                callback = self.task_callbacks[task.id]
                try:
                    callback(task)
                except Exception as e:
                    print(f"Error calling task callback: {e}")
                finally:
                    del self.task_callbacks[task.id]
                    
        except Exception as e:
            print(f"Error executing task {task.id}: {e}")
            self.task_queue.mark_task_failed(task.id, str(e))
            if task.agent_id:
                self.agent_load[task.agent_id] -= 1
    
    def _monitoring_loop(self):
        """Monitor tasks for timeouts and retries."""
        while self.is_running:
            try:
                # Check for timed out tasks
                running_tasks = self.task_queue.get_tasks_by_status(TaskStatus.RUNNING)
                
                for task in running_tasks:
                    if task.is_expired():
                        print(f"Task {task.id} timed out")
                        task.status = TaskStatus.TIMEOUT
                        task.completed_at = datetime.utcnow()
                        
                        if task.agent_id:
                            self.agent_load[task.agent_id] -= 1
                        
                        # Retry if possible
                        if task.retry_count < task.max_retries:
                            retry_task = Task(
                                agent_id=task.agent_id,
                                task_data=task.task_data,
                                priority=task.priority,
                                timeout_seconds=task.timeout_seconds,
                                retry_count=task.retry_count + 1,
                                max_retries=task.max_retries,
                                dependencies=task.dependencies
                            )
                            self.task_queue.add_task(retry_task)
                            print(f"Retrying task {task.id} as {retry_task.id}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error in task monitoring loop: {e}")
                time.sleep(5)

