import uuid
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.connectors.base import FrameworkConnector, AgentStatus, TaskStatus

class CrewAIConnector(FrameworkConnector):
    """
    Connector for CrewAI framework.
    This is a mock implementation for demonstration purposes.
    In a real implementation, this would integrate with the actual CrewAI library.
    """
    
    def __init__(self):
        super().__init__("CrewAI", "0.1.0")
        self.tasks = {}  # task_id -> task_info mapping
        self.crews = {}  # crew_id -> crew_info mapping
        
    def create_agent(self, agent_config: Dict[str, Any]) -> str:
        """Create a new CrewAI agent."""
        agent_id = str(uuid.uuid4())
        
        # Mock CrewAI agent creation
        agent_instance = {
            'id': agent_id,
            'name': agent_config.get('name', f'crewai_agent_{agent_id[:8]}'),
            'role': agent_config.get('role', 'crew_member'),
            'goal': agent_config.get('goal', ''),
            'backstory': agent_config.get('backstory', ''),
            'tools': agent_config.get('tools', []),
            'max_iter': agent_config.get('max_iter', 10),
            'status': AgentStatus.INACTIVE,
            'created_at': datetime.utcnow(),
            'crew_id': agent_config.get('crew_id'),
            'metrics': {
                'tasks_completed': 0,
                'total_iterations': 0,
                'avg_iterations_per_task': 0.0,
                'tool_usage_count': 0,
                'error_count': 0
            }
        }
        
        self.agents[agent_id] = agent_instance
        return agent_id
    
    def start_agent(self, agent_id: str) -> bool:
        """Start a CrewAI agent."""
        if agent_id not in self.agents:
            return False
            
        self.agents[agent_id]['status'] = AgentStatus.ACTIVE
        self.agents[agent_id]['started_at'] = datetime.utcnow()
        return True
    
    def stop_agent(self, agent_id: str) -> bool:
        """Stop a CrewAI agent."""
        if agent_id not in self.agents:
            return False
            
        self.agents[agent_id]['status'] = AgentStatus.INACTIVE
        self.agents[agent_id]['stopped_at'] = datetime.utcnow()
        return True
    
    def pause_agent(self, agent_id: str) -> bool:
        """Pause a CrewAI agent."""
        if agent_id not in self.agents:
            return False
            
        self.agents[agent_id]['status'] = AgentStatus.PAUSED
        return True
    
    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused CrewAI agent."""
        if agent_id not in self.agents:
            return False
            
        self.agents[agent_id]['status'] = AgentStatus.ACTIVE
        return True
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete a CrewAI agent."""
        if agent_id not in self.agents:
            return False
            
        del self.agents[agent_id]
        return True
    
    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """Get the current status of a CrewAI agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        return self.agents[agent_id]['status']
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for a CrewAI agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        return {
            'agent_id': agent_id,
            'framework': self.framework_name,
            'status': agent['status'].value,
            'role': agent['role'],
            'crew_id': agent.get('crew_id'),
            'uptime': self._calculate_uptime(agent),
            'tasks_completed': agent['metrics']['tasks_completed'],
            'total_iterations': agent['metrics']['total_iterations'],
            'avg_iterations_per_task': agent['metrics']['avg_iterations_per_task'],
            'tool_usage_count': agent['metrics']['tool_usage_count'],
            'error_count': agent['metrics']['error_count'],
            'max_iter': agent['max_iter'],
            'available_tools': len(agent['tools'])
        }
    
    def execute_task(self, agent_id: str, task_data: Dict[str, Any]) -> str:
        """Execute a task using the specified CrewAI agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        if self.agents[agent_id]['status'] != AgentStatus.ACTIVE:
            raise ValueError(f"Agent {agent_id} is not active")
            
        task_id = str(uuid.uuid4())
        
        # Mock task execution
        task_info = {
            'id': task_id,
            'agent_id': agent_id,
            'status': TaskStatus.RUNNING,
            'input_data': task_data,
            'started_at': datetime.utcnow(),
            'current_iteration': 0,
            'max_iterations': self.agents[agent_id]['max_iter'],
            'tools_used': []
        }
        
        self.tasks[task_id] = task_info
        
        # Simulate task execution
        self._simulate_crewai_task_execution(task_id)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get the status of a task execution."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        return self.tasks[task_id]['status']
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task."""
        if task_id not in self.tasks:
            return None
            
        task = self.tasks[task_id]
        if task['status'] != TaskStatus.COMPLETED:
            return None
            
        return task.get('result')
    
    def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update CrewAI agent configuration dynamically."""
        if agent_id not in self.agents:
            return False
            
        agent = self.agents[agent_id]
        
        # Update supported configuration fields
        if 'max_iter' in config_updates:
            agent['max_iter'] = config_updates['max_iter']
        if 'goal' in config_updates:
            agent['goal'] = config_updates['goal']
        if 'backstory' in config_updates:
            agent['backstory'] = config_updates['backstory']
        if 'tools' in config_updates:
            agent['tools'] = config_updates['tools']
        if 'role' in config_updates:
            agent['role'] = config_updates['role']
            
        agent['updated_at'] = datetime.utcnow()
        return True
    
    def send_message(self, from_agent_id: str, to_agent_id: str, message: Dict[str, Any]) -> bool:
        """Send a message from one CrewAI agent to another."""
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return False
            
        # Check if agents are in the same crew
        from_agent = self.agents[from_agent_id]
        to_agent = self.agents[to_agent_id]
        
        if from_agent.get('crew_id') != to_agent.get('crew_id'):
            print(f"Warning: Agents {from_agent_id} and {to_agent_id} are not in the same crew")
            return False
            
        # Mock message sending within crew
        message_id = str(uuid.uuid4())
        print(f"Crew message {message_id} sent from {from_agent_id} to {to_agent_id}: {message}")
        
        return True
    
    def create_crew(self, crew_config: Dict[str, Any]) -> str:
        """Create a new crew with multiple agents."""
        crew_id = str(uuid.uuid4())
        
        crew_info = {
            'id': crew_id,
            'name': crew_config.get('name', f'crew_{crew_id[:8]}'),
            'agents': crew_config.get('agents', []),
            'process': crew_config.get('process', 'sequential'),
            'created_at': datetime.utcnow(),
            'status': 'inactive'
        }
        
        self.crews[crew_id] = crew_info
        
        # Update agent crew assignments
        for agent_id in crew_info['agents']:
            if agent_id in self.agents:
                self.agents[agent_id]['crew_id'] = crew_id
                
        return crew_id
    
    def execute_crew_task(self, crew_id: str, task_data: Dict[str, Any]) -> str:
        """Execute a task using an entire crew."""
        if crew_id not in self.crews:
            raise ValueError(f"Crew {crew_id} not found")
            
        crew = self.crews[crew_id]
        task_id = str(uuid.uuid4())
        
        # Mock crew task execution
        task_info = {
            'id': task_id,
            'crew_id': crew_id,
            'status': TaskStatus.RUNNING,
            'input_data': task_data,
            'started_at': datetime.utcnow(),
            'agent_results': {}
        }
        
        self.tasks[task_id] = task_info
        
        # Simulate crew collaboration
        self._simulate_crew_execution(task_id)
        
        return task_id
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the CrewAI connector."""
        base_health = super().health_check()
        base_health.update({
            'timestamp': datetime.utcnow().isoformat(),
            'active_tasks': len([t for t in self.tasks.values() if t['status'] == TaskStatus.RUNNING]),
            'total_tasks': len(self.tasks),
            'active_crews': len(self.crews),
            'framework_specific': {
                'supports_crews': True,
                'supports_tools': True,
                'supports_iterative_execution': True,
                'default_max_iter': 10
            }
        })
        return base_health
    
    def _calculate_uptime(self, agent: Dict[str, Any]) -> float:
        """Calculate agent uptime in seconds."""
        if 'started_at' not in agent:
            return 0.0
            
        start_time = agent['started_at']
        if agent['status'] == AgentStatus.ACTIVE:
            return (datetime.utcnow() - start_time).total_seconds()
        elif 'stopped_at' in agent:
            return (agent['stopped_at'] - start_time).total_seconds()
        else:
            return 0.0
    
    def _simulate_crewai_task_execution(self, task_id: str):
        """Simulate CrewAI task execution with iterations."""
        task = self.tasks[task_id]
        agent_id = task['agent_id']
        agent = self.agents[agent_id]
        
        # Simulate iterative execution
        max_iterations = task['max_iterations']
        for i in range(1, max_iterations + 1):
            time.sleep(0.02)  # Simulate processing time per iteration
            task['current_iteration'] = i
            
            # Simulate tool usage
            if agent['tools'] and i % 2 == 0:
                tool_used = agent['tools'][i % len(agent['tools'])] if agent['tools'] else 'default_tool'
                task['tools_used'].append(tool_used)
                agent['metrics']['tool_usage_count'] += 1
            
            # Simulate completion after some iterations
            if i >= 3:  # Complete after at least 3 iterations
                break
        
        # Complete the task
        task['status'] = TaskStatus.COMPLETED
        task['completed_at'] = datetime.utcnow()
        task['result'] = {
            'output': f"CrewAI task {task_id} completed after {task['current_iteration']} iterations",
            'iterations_used': task['current_iteration'],
            'tools_used': task['tools_used'],
            'execution_time': (task['completed_at'] - task['started_at']).total_seconds()
        }
        
        # Update agent metrics
        agent['metrics']['tasks_completed'] += 1
        agent['metrics']['total_iterations'] += task['current_iteration']
        if agent['metrics']['tasks_completed'] > 0:
            agent['metrics']['avg_iterations_per_task'] = (
                agent['metrics']['total_iterations'] / agent['metrics']['tasks_completed']
            )
    
    def _simulate_crew_execution(self, task_id: str):
        """Simulate crew-based task execution."""
        task = self.tasks[task_id]
        crew_id = task['crew_id']
        crew = self.crews[crew_id]
        
        # Simulate each agent in the crew working on the task
        for agent_id in crew['agents']:
            if agent_id in self.agents:
                agent_task_id = self.execute_task(agent_id, task['input_data'])
                # Wait for agent task to complete (in real implementation, this would be async)
                time.sleep(0.1)
                agent_result = self.get_task_result(agent_task_id)
                task['agent_results'][agent_id] = agent_result
        
        # Complete the crew task
        task['status'] = TaskStatus.COMPLETED
        task['completed_at'] = datetime.utcnow()
        task['result'] = {
            'output': f"Crew task {task_id} completed with {len(task['agent_results'])} agent contributions",
            'agent_results': task['agent_results'],
            'execution_time': (task['completed_at'] - task['started_at']).total_seconds()
        }

