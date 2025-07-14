import uuid
import json
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from collections import defaultdict
import copy

class WorkflowStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeType(Enum):
    AGENT = "agent"
    CONDITION = "condition"
    ACTION = "action"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"

class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowNode:
    """Represents a node in a workflow."""
    
    def __init__(self, node_id: str, node_type: NodeType, name: str, 
                 config: Dict[str, Any] = None, position: Dict[str, float] = None):
        self.id = node_id
        self.type = node_type
        self.name = name
        self.config = config or {}
        self.position = position or {'x': 0, 'y': 0}
        self.status = NodeStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.execution_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'config': self.config,
            'position': self.position,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': self.execution_time
        }

class WorkflowConnection:
    """Represents a connection between workflow nodes."""
    
    def __init__(self, from_node_id: str, to_node_id: str, 
                 condition: str = None, label: str = None):
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.condition = condition  # Optional condition for conditional flows
        self.label = label
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary."""
        return {
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'condition': self.condition,
            'label': self.label
        }

class WorkflowDefinition:
    """Defines a workflow structure."""
    
    def __init__(self, workflow_id: str = None, name: str = "", 
                 description: str = "", version: str = "1.0"):
        self.id = workflow_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.version = version
        self.nodes = {}  # node_id -> WorkflowNode
        self.connections = []  # List of WorkflowConnection
        self.variables = {}  # Workflow-level variables
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
    def add_node(self, node: WorkflowNode):
        """Add a node to the workflow."""
        self.nodes[node.id] = node
        self.updated_at = datetime.utcnow()
        
    def remove_node(self, node_id: str):
        """Remove a node and its connections."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Remove connections involving this node
            self.connections = [conn for conn in self.connections 
                              if conn.from_node_id != node_id and conn.to_node_id != node_id]
            self.updated_at = datetime.utcnow()
            
    def add_connection(self, connection: WorkflowConnection):
        """Add a connection between nodes."""
        # Validate that both nodes exist
        if (connection.from_node_id in self.nodes and 
            connection.to_node_id in self.nodes):
            self.connections.append(connection)
            self.updated_at = datetime.utcnow()
            return True
        return False
        
    def get_next_nodes(self, node_id: str) -> List[str]:
        """Get the next nodes to execute after the given node."""
        return [conn.to_node_id for conn in self.connections 
                if conn.from_node_id == node_id]
                
    def get_previous_nodes(self, node_id: str) -> List[str]:
        """Get the nodes that must complete before the given node."""
        return [conn.from_node_id for conn in self.connections 
                if conn.to_node_id == node_id]
                
    def get_entry_nodes(self) -> List[str]:
        """Get nodes with no incoming connections (entry points)."""
        nodes_with_incoming = {conn.to_node_id for conn in self.connections}
        return [node_id for node_id in self.nodes.keys() 
                if node_id not in nodes_with_incoming]
                
    def validate(self) -> List[str]:
        """Validate the workflow definition."""
        errors = []
        
        # Check for cycles
        if self._has_cycles():
            errors.append("Workflow contains cycles")
            
        # Check for orphaned nodes
        connected_nodes = set()
        for conn in self.connections:
            connected_nodes.add(conn.from_node_id)
            connected_nodes.add(conn.to_node_id)
            
        orphaned = set(self.nodes.keys()) - connected_nodes
        if len(orphaned) > 1:  # Allow one orphaned node as entry point
            errors.append(f"Multiple orphaned nodes: {orphaned}")
            
        # Check for missing entry points
        entry_nodes = self.get_entry_nodes()
        if not entry_nodes:
            errors.append("No entry nodes found")
            
        return errors
        
    def _has_cycles(self) -> bool:
        """Check if the workflow has cycles using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for next_node in self.get_next_nodes(node_id):
                if next_node not in visited:
                    if dfs(next_node):
                        return True
                elif next_node in rec_stack:
                    return True
                    
            rec_stack.remove(node_id)
            return False
            
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
                    
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow definition to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'connections': [conn.to_dict() for conn in self.connections],
            'variables': self.variables,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class WorkflowExecution:
    """Represents a running instance of a workflow."""
    
    def __init__(self, execution_id: str = None, workflow_def: WorkflowDefinition = None,
                 input_data: Dict[str, Any] = None):
        self.id = execution_id or str(uuid.uuid4())
        self.workflow_def = workflow_def
        self.input_data = input_data or {}
        self.status = WorkflowStatus.READY
        self.current_nodes = set()  # Currently executing nodes
        self.completed_nodes = set()  # Completed nodes
        self.failed_nodes = set()  # Failed nodes
        self.node_results = {}  # node_id -> result
        self.execution_context = {}  # Shared execution context
        self.started_at = None
        self.completed_at = None
        self.error = None
        
    def start(self):
        """Start workflow execution."""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        
        # Initialize execution context with input data
        self.execution_context.update(self.input_data)
        
        # Start with entry nodes
        entry_nodes = self.workflow_def.get_entry_nodes()
        self.current_nodes.update(entry_nodes)
        
    def complete_node(self, node_id: str, result: Any = None, error: str = None):
        """Mark a node as completed."""
        if node_id in self.current_nodes:
            self.current_nodes.remove(node_id)
            
        if error:
            self.failed_nodes.add(node_id)
            node = self.workflow_def.nodes[node_id]
            node.status = NodeStatus.FAILED
            node.error = error
            node.completed_at = datetime.utcnow()
            
            # Fail the entire workflow if any node fails
            self.status = WorkflowStatus.FAILED
            self.error = f"Node {node_id} failed: {error}"
            self.completed_at = datetime.utcnow()
        else:
            self.completed_nodes.add(node_id)
            self.node_results[node_id] = result
            
            node = self.workflow_def.nodes[node_id]
            node.status = NodeStatus.COMPLETED
            node.result = result
            node.completed_at = datetime.utcnow()
            
            if node.started_at:
                node.execution_time = (node.completed_at - node.started_at).total_seconds()
            
            # Check if we can start next nodes
            self._check_next_nodes(node_id)
            
        # Check if workflow is complete
        self._check_completion()
        
    def _check_next_nodes(self, completed_node_id: str):
        """Check if next nodes can be started."""
        next_nodes = self.workflow_def.get_next_nodes(completed_node_id)
        
        for next_node_id in next_nodes:
            # Check if all prerequisites are met
            prev_nodes = self.workflow_def.get_previous_nodes(next_node_id)
            if all(prev_id in self.completed_nodes for prev_id in prev_nodes):
                # All prerequisites completed, can start this node
                if next_node_id not in self.current_nodes and next_node_id not in self.completed_nodes:
                    self.current_nodes.add(next_node_id)
                    
                    node = self.workflow_def.nodes[next_node_id]
                    node.status = NodeStatus.RUNNING
                    node.started_at = datetime.utcnow()
                    
    def _check_completion(self):
        """Check if workflow execution is complete."""
        if self.status == WorkflowStatus.RUNNING:
            total_nodes = len(self.workflow_def.nodes)
            finished_nodes = len(self.completed_nodes) + len(self.failed_nodes)
            
            if finished_nodes == total_nodes:
                if self.failed_nodes:
                    self.status = WorkflowStatus.FAILED
                else:
                    self.status = WorkflowStatus.COMPLETED
                    
                self.completed_at = datetime.utcnow()
                
    def pause(self):
        """Pause workflow execution."""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED
            
    def resume(self):
        """Resume paused workflow execution."""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            
    def cancel(self):
        """Cancel workflow execution."""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
    def get_progress(self) -> Dict[str, Any]:
        """Get workflow execution progress."""
        total_nodes = len(self.workflow_def.nodes)
        completed = len(self.completed_nodes)
        failed = len(self.failed_nodes)
        running = len(self.current_nodes)
        
        progress_percentage = ((completed + failed) / total_nodes * 100) if total_nodes > 0 else 0
        
        return {
            'total_nodes': total_nodes,
            'completed_nodes': completed,
            'failed_nodes': failed,
            'running_nodes': running,
            'progress_percentage': progress_percentage,
            'status': self.status.value
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary."""
        return {
            'id': self.id,
            'workflow_id': self.workflow_def.id if self.workflow_def else None,
            'input_data': self.input_data,
            'status': self.status.value,
            'current_nodes': list(self.current_nodes),
            'completed_nodes': list(self.completed_nodes),
            'failed_nodes': list(self.failed_nodes),
            'node_results': self.node_results,
            'execution_context': self.execution_context,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'progress': self.get_progress()
        }

class WorkflowEngine:
    """Main workflow execution engine."""
    
    def __init__(self, task_distribution_engine=None):
        self.workflow_definitions = {}  # workflow_id -> WorkflowDefinition
        self.executions = {}  # execution_id -> WorkflowExecution
        self.execution_callbacks = {}  # execution_id -> callback
        self.node_handlers = {}  # node_type -> handler function
        self.task_distribution_engine = task_distribution_engine
        self.is_running = False
        self.execution_thread = None
        
        # Register default node handlers
        self._register_default_handlers()
        
    def start(self):
        """Start the workflow engine."""
        if self.is_running:
            return
            
        self.is_running = True
        self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()
        
        print("Workflow engine started")
        
    def stop(self):
        """Stop the workflow engine."""
        self.is_running = False
        
        if self.execution_thread:
            self.execution_thread.join(timeout=5)
            
        print("Workflow engine stopped")
        
    def register_workflow(self, workflow_def: WorkflowDefinition) -> bool:
        """Register a workflow definition."""
        errors = workflow_def.validate()
        if errors:
            print(f"Workflow validation failed: {errors}")
            return False
            
        self.workflow_definitions[workflow_def.id] = workflow_def
        return True
        
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None,
                        callback: Callable = None) -> str:
        """Start executing a workflow."""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        workflow_def = self.workflow_definitions[workflow_id]
        execution = WorkflowExecution(
            workflow_def=workflow_def,
            input_data=input_data or {}
        )
        
        execution.start()
        self.executions[execution.id] = execution
        
        if callback:
            self.execution_callbacks[execution.id] = callback
            
        return execution.id
        
    def get_execution_status(self, execution_id: str) -> Optional[str]:
        """Get the status of a workflow execution."""
        execution = self.executions.get(execution_id)
        return execution.status.value if execution else None
        
    def get_execution_progress(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the progress of a workflow execution."""
        execution = self.executions.get(execution_id)
        return execution.get_progress() if execution else None
        
    def pause_execution(self, execution_id: str) -> bool:
        """Pause a workflow execution."""
        execution = self.executions.get(execution_id)
        if execution:
            execution.pause()
            return True
        return False
        
    def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused workflow execution."""
        execution = self.executions.get(execution_id)
        if execution:
            execution.resume()
            return True
        return False
        
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution."""
        execution = self.executions.get(execution_id)
        if execution:
            execution.cancel()
            return True
        return False
        
    def register_node_handler(self, node_type: NodeType, handler: Callable):
        """Register a handler for a specific node type."""
        self.node_handlers[node_type] = handler
        
    def _register_default_handlers(self):
        """Register default node handlers."""
        self.node_handlers[NodeType.AGENT] = self._handle_agent_node
        self.node_handlers[NodeType.CONDITION] = self._handle_condition_node
        self.node_handlers[NodeType.ACTION] = self._handle_action_node
        
    def _execution_loop(self):
        """Main execution loop."""
        while self.is_running:
            try:
                # Process all running executions
                for execution_id, execution in list(self.executions.items()):
                    if execution.status == WorkflowStatus.RUNNING:
                        self._process_execution(execution)
                        
                    # Clean up completed executions
                    elif execution.status in [WorkflowStatus.COMPLETED, 
                                            WorkflowStatus.FAILED, 
                                            WorkflowStatus.CANCELLED]:
                        if execution_id in self.execution_callbacks:
                            callback = self.execution_callbacks[execution_id]
                            try:
                                callback(execution)
                            except Exception as e:
                                print(f"Error calling execution callback: {e}")
                            finally:
                                del self.execution_callbacks[execution_id]
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                print(f"Error in workflow execution loop: {e}")
                time.sleep(1)
                
    def _process_execution(self, execution: WorkflowExecution):
        """Process a running workflow execution."""
        # Execute current nodes
        for node_id in list(execution.current_nodes):
            node = execution.workflow_def.nodes[node_id]
            
            if node.status == NodeStatus.RUNNING:
                # Execute the node
                self._execute_node(execution, node)
                
    def _execute_node(self, execution: WorkflowExecution, node: WorkflowNode):
        """Execute a workflow node."""
        try:
            handler = self.node_handlers.get(node.type)
            if handler:
                result = handler(execution, node)
                execution.complete_node(node.id, result)
            else:
                execution.complete_node(node.id, error=f"No handler for node type {node.type}")
                
        except Exception as e:
            execution.complete_node(node.id, error=str(e))
            
    def _handle_agent_node(self, execution: WorkflowExecution, node: WorkflowNode) -> Any:
        """Handle agent node execution."""
        # Submit task to agent via task distribution engine
        if self.task_distribution_engine:
            task_data = {
                'node_id': node.id,
                'execution_id': execution.id,
                'agent_config': node.config,
                'context': execution.execution_context
            }
            
            agent_id = node.config.get('agent_id')
            task_id = self.task_distribution_engine.submit_task(
                task_data=task_data,
                agent_id=agent_id
            )
            
            # For now, simulate completion
            return {'task_id': task_id, 'status': 'submitted'}
        else:
            # Simulate agent execution
            time.sleep(0.1)
            return {'status': 'completed', 'output': f'Agent {node.name} executed'}
            
    def _handle_condition_node(self, execution: WorkflowExecution, node: WorkflowNode) -> Any:
        """Handle condition node execution."""
        # Evaluate condition based on execution context
        condition = node.config.get('condition', 'true')
        
        # Simple condition evaluation (in practice, this would be more sophisticated)
        try:
            # Create a safe evaluation context
            eval_context = {
                'context': execution.execution_context,
                'results': execution.node_results
            }
            
            # For safety, use a simple condition format
            if condition == 'true':
                result = True
            elif condition == 'false':
                result = False
            else:
                # Simple variable checks
                result = eval_context.get(condition, False)
                
            return {'condition_result': result}
            
        except Exception as e:
            return {'condition_result': False, 'error': str(e)}
            
    def _handle_action_node(self, execution: WorkflowExecution, node: WorkflowNode) -> Any:
        """Handle action node execution."""
        action_type = node.config.get('action_type', 'log')
        
        if action_type == 'log':
            message = node.config.get('message', f'Action {node.name} executed')
            print(f"Workflow {execution.id}: {message}")
            return {'action': 'log', 'message': message}
            
        elif action_type == 'set_variable':
            var_name = node.config.get('variable_name')
            var_value = node.config.get('variable_value')
            if var_name:
                execution.execution_context[var_name] = var_value
                return {'action': 'set_variable', 'variable': var_name, 'value': var_value}
                
        return {'action': action_type, 'status': 'completed'}

