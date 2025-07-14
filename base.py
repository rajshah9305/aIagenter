from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FrameworkConnector(ABC):
    """
    Abstract base class for all framework connectors.
    Each framework (AutoGen, CrewAI, etc.) must implement this interface.
    """
    
    def __init__(self, framework_name: str, version: str):
        self.framework_name = framework_name
        self.version = version
        self.agents = {}  # agent_id -> agent_instance mapping
        
    @abstractmethod
    def create_agent(self, agent_config: Dict[str, Any]) -> str:
        """
        Create a new agent instance.
        
        Args:
            agent_config: Configuration dictionary for the agent
            
        Returns:
            agent_id: Unique identifier for the created agent
        """
        pass
    
    @abstractmethod
    def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            success: True if agent started successfully
        """
        pass
    
    @abstractmethod
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            success: True if agent stopped successfully
        """
        pass
    
    @abstractmethod
    def pause_agent(self, agent_id: str) -> bool:
        """
        Pause an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            success: True if agent paused successfully
        """
        pass
    
    @abstractmethod
    def resume_agent(self, agent_id: str) -> bool:
        """
        Resume a paused agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            success: True if agent resumed successfully
        """
        pass
    
    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            success: True if agent deleted successfully
        """
        pass
    
    @abstractmethod
    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """
        Get the current status of an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            status: Current status of the agent
        """
        pass
    
    @abstractmethod
    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for an agent.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            metrics: Dictionary containing various performance metrics
        """
        pass
    
    @abstractmethod
    def execute_task(self, agent_id: str, task_data: Dict[str, Any]) -> str:
        """
        Execute a task using the specified agent.
        
        Args:
            agent_id: Unique identifier of the agent
            task_data: Task data and parameters
            
        Returns:
            task_id: Unique identifier for the task execution
        """
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> TaskStatus:
        """
        Get the status of a task execution.
        
        Args:
            task_id: Unique identifier of the task
            
        Returns:
            status: Current status of the task
        """
        pass
    
    @abstractmethod
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: Unique identifier of the task
            
        Returns:
            result: Task result data, or None if not completed
        """
        pass
    
    @abstractmethod
    def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update agent configuration dynamically.
        
        Args:
            agent_id: Unique identifier of the agent
            config_updates: Configuration updates to apply
            
        Returns:
            success: True if configuration updated successfully
        """
        pass
    
    @abstractmethod
    def send_message(self, from_agent_id: str, to_agent_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message from one agent to another (if supported by framework).
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            message: Message data
            
        Returns:
            success: True if message sent successfully
        """
        pass
    
    def list_agents(self) -> List[str]:
        """
        List all agent IDs managed by this connector.
        
        Returns:
            agent_ids: List of agent identifiers
        """
        return list(self.agents.keys())
    
    def get_framework_info(self) -> Dict[str, str]:
        """
        Get information about this framework connector.
        
        Returns:
            info: Framework name, version, and other metadata
        """
        return {
            'name': self.framework_name,
            'version': self.version,
            'connector_class': self.__class__.__name__
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the framework connector.
        
        Returns:
            health_status: Health information and diagnostics
        """
        return {
            'status': 'healthy',
            'framework': self.framework_name,
            'version': self.version,
            'active_agents': len(self.agents),
            'timestamp': None  # Should be set by implementation
        }

