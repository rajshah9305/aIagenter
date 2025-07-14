import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.connectors.base import FrameworkConnector, AgentStatus, TaskStatus
from src.connectors.autogen_connector import AutoGenConnector
from src.connectors.crewai_connector import CrewAIConnector

class OrchestrationEngine:
    """
    Core orchestration engine that manages multiple framework connectors
    and coordinates agent interactions across different frameworks.
    """
    
    def __init__(self):
        self.connectors: Dict[str, FrameworkConnector] = {}
        self.agent_registry: Dict[str, Dict[str, Any]] = {}  # agent_id -> agent_info
        self.task_queue: List[Dict[str, Any]] = []
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        self.message_bus: List[Dict[str, Any]] = []
        self.is_running = False
        self.worker_thread = None
        
        # Initialize default connectors
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize framework connectors."""
        self.connectors['autogen'] = AutoGenConnector()
        self.connectors['crewai'] = CrewAIConnector()
    
    def start(self):
        """Start the orchestration engine."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("Orchestration engine started")
    
    def stop(self):
        """Stop the orchestration engine."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("Orchestration engine stopped")
    
    def register_agent(self, framework: str, agent_config: Dict[str, Any]) -> str:
        """
        Register a new agent with the specified framework.
        
        Args:
            framework: Framework name (e.g., 'autogen', 'crewai')
            agent_config: Agent configuration
            
        Returns:
            agent_id: Unique identifier for the registered agent
        """
        if framework not in self.connectors:
            raise ValueError(f"Framework '{framework}' not supported")
        
        connector = self.connectors[framework]
        agent_id = connector.create_agent(agent_config)
        
        # Register in central registry
        self.agent_registry[agent_id] = {
            'framework': framework,
            'connector': connector,
            'config': agent_config,
            'registered_at': datetime.utcnow(),
            'status': AgentStatus.INACTIVE
        }
        
        return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the orchestration engine.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            success: True if agent was successfully unregistered
        """
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        # Stop and delete the agent
        connector.stop_agent(agent_id)
        connector.delete_agent(agent_id)
        
        # Remove from registry
        del self.agent_registry[agent_id]
        
        return True
    
    def start_agent(self, agent_id: str) -> bool:
        """Start an agent."""
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        success = connector.start_agent(agent_id)
        if success:
            self.agent_registry[agent_id]['status'] = AgentStatus.ACTIVE
        
        return success
    
    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        success = connector.stop_agent(agent_id)
        if success:
            self.agent_registry[agent_id]['status'] = AgentStatus.INACTIVE
        
        return success
    
    def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent."""
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        success = connector.pause_agent(agent_id)
        if success:
            self.agent_registry[agent_id]['status'] = AgentStatus.PAUSED
        
        return success
    
    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent."""
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        success = connector.resume_agent(agent_id)
        if success:
            self.agent_registry[agent_id]['status'] = AgentStatus.ACTIVE
        
        return success
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get the status of an agent."""
        if agent_id not in self.agent_registry:
            return None
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        return connector.get_agent_status(agent_id)
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for an agent."""
        if agent_id not in self.agent_registry:
            return None
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        return connector.get_agent_metrics(agent_id)
    
    def submit_task(self, agent_id: str, task_data: Dict[str, Any], priority: int = 5) -> str:
        """
        Submit a task to be executed by an agent.
        
        Args:
            agent_id: Target agent identifier
            task_data: Task data and parameters
            priority: Task priority (1-10, 1 being highest)
            
        Returns:
            task_id: Unique identifier for the submitted task
        """
        if agent_id not in self.agent_registry:
            raise ValueError(f"Agent {agent_id} not found")
        
        task_info = {
            'id': f"task_{int(time.time() * 1000)}_{agent_id[:8]}",
            'agent_id': agent_id,
            'task_data': task_data,
            'priority': priority,
            'submitted_at': datetime.utcnow(),
            'status': 'queued'
        }
        
        # Add to task queue (sorted by priority)
        self.task_queue.append(task_info)
        self.task_queue.sort(key=lambda x: x['priority'])
        
        return task_info['id']
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        # Check running tasks
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]['status']
        
        # Check queued tasks
        for task in self.task_queue:
            if task['id'] == task_id:
                return task['status']
        
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task."""
        if task_id in self.running_tasks:
            task_info = self.running_tasks[task_id]
            if task_info['status'] == 'completed':
                return task_info.get('result')
        
        return None
    
    def send_inter_agent_message(self, from_agent_id: str, to_agent_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message between agents (potentially across frameworks).
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            message: Message data
            
        Returns:
            success: True if message was sent successfully
        """
        if from_agent_id not in self.agent_registry or to_agent_id not in self.agent_registry:
            return False
        
        from_agent_info = self.agent_registry[from_agent_id]
        to_agent_info = self.agent_registry[to_agent_id]
        
        # If agents are in the same framework, use framework-specific messaging
        if from_agent_info['framework'] == to_agent_info['framework']:
            connector = from_agent_info['connector']
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
        
        self.message_bus.append(message_info)
        print(f"Cross-framework message sent: {from_agent_id} -> {to_agent_id}")
        
        return True
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        agents = []
        for agent_id, agent_info in self.agent_registry.items():
            agents.append({
                'id': agent_id,
                'framework': agent_info['framework'],
                'status': agent_info['status'].value if hasattr(agent_info['status'], 'value') else str(agent_info['status']),
                'registered_at': agent_info['registered_at'].isoformat()
            })
        return agents
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health information."""
        health_info = {
            'orchestration_engine': {
                'status': 'running' if self.is_running else 'stopped',
                'registered_agents': len(self.agent_registry),
                'queued_tasks': len(self.task_queue),
                'running_tasks': len(self.running_tasks),
                'message_bus_size': len(self.message_bus)
            },
            'frameworks': {}
        }
        
        # Get health from each connector
        for framework_name, connector in self.connectors.items():
            health_info['frameworks'][framework_name] = connector.health_check()
        
        return health_info
    
    def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update agent configuration dynamically."""
        if agent_id not in self.agent_registry:
            return False
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        success = connector.update_agent_config(agent_id, config_updates)
        if success:
            # Update local registry
            agent_info['config'].update(config_updates)
            agent_info['updated_at'] = datetime.utcnow()
        
        return success
    
    def _worker_loop(self):
        """Main worker loop for processing tasks."""
        while self.is_running:
            try:
                # Process queued tasks
                if self.task_queue:
                    task_info = self.task_queue.pop(0)
                    self._execute_task(task_info)
                
                # Check running tasks for completion
                self._check_running_tasks()
                
                # Clean up old messages
                self._cleanup_message_bus()
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Error in orchestration worker loop: {e}")
                time.sleep(1)
    
    def _execute_task(self, task_info: Dict[str, Any]):
        """Execute a task using the appropriate agent."""
        agent_id = task_info['agent_id']
        
        if agent_id not in self.agent_registry:
            print(f"Agent {agent_id} not found for task {task_info['id']}")
            return
        
        agent_info = self.agent_registry[agent_id]
        connector = agent_info['connector']
        
        try:
            # Execute the task
            framework_task_id = connector.execute_task(agent_id, task_info['task_data'])
            
            # Track the running task
            task_info['framework_task_id'] = framework_task_id
            task_info['status'] = 'running'
            task_info['started_at'] = datetime.utcnow()
            
            self.running_tasks[task_info['id']] = task_info
            
        except Exception as e:
            print(f"Error executing task {task_info['id']}: {e}")
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
    
    def _check_running_tasks(self):
        """Check running tasks for completion."""
        completed_tasks = []
        
        for task_id, task_info in self.running_tasks.items():
            agent_id = task_info['agent_id']
            framework_task_id = task_info['framework_task_id']
            
            if agent_id not in self.agent_registry:
                continue
            
            agent_info = self.agent_registry[agent_id]
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
                print(f"Error checking task {task_id}: {e}")
                task_info['status'] = 'error'
                task_info['error'] = str(e)
                completed_tasks.append(task_id)
        
        # Remove completed tasks from running tasks (keep them for result retrieval)
        # In a production system, you'd want to move these to a completed tasks store
        pass
    
    def _cleanup_message_bus(self):
        """Clean up old messages from the message bus."""
        # Keep only messages from the last hour
        cutoff_time = datetime.utcnow().timestamp() - 3600
        self.message_bus = [
            msg for msg in self.message_bus 
            if msg['timestamp'].timestamp() > cutoff_time
        ]

