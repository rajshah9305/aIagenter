from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class AgentRegistry:
    """
    Agent discovery and registry service that maintains a catalog of all agents
    and their capabilities across different frameworks.
    """
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self.framework_index: Dict[str, List[str]] = {}    # framework -> [agent_ids]
        self.tags_index: Dict[str, List[str]] = {}         # tag -> [agent_ids]
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """
        Register an agent in the discovery service.
        
        Args:
            agent_id: Unique agent identifier
            agent_info: Agent metadata and capabilities
            
        Returns:
            success: True if agent was registered successfully
        """
        try:
            # Validate required fields
            required_fields = ['name', 'framework', 'capabilities']
            for field in required_fields:
                if field not in agent_info:
                    raise ValueError(f"Missing required field: {field}")
            
            # Prepare agent record
            agent_record = {
                'id': agent_id,
                'name': agent_info['name'],
                'framework': agent_info['framework'],
                'version': agent_info.get('version', '1.0'),
                'description': agent_info.get('description', ''),
                'capabilities': agent_info['capabilities'],
                'tags': agent_info.get('tags', []),
                'status': agent_info.get('status', 'inactive'),
                'endpoint': agent_info.get('endpoint'),
                'metadata': agent_info.get('metadata', {}),
                'registered_at': datetime.utcnow(),
                'last_seen': datetime.utcnow(),
                'health_status': 'unknown'
            }
            
            # Store agent record
            self.agents[agent_id] = agent_record
            
            # Update indexes
            self._update_indexes(agent_id, agent_record)
            
            return True
            
        except Exception as e:
            print(f"Error registering agent {agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the discovery service.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            success: True if agent was unregistered successfully
        """
        if agent_id not in self.agents:
            return False
        
        agent_record = self.agents[agent_id]
        
        # Remove from indexes
        self._remove_from_indexes(agent_id, agent_record)
        
        # Remove agent record
        del self.agents[agent_id]
        
        return True
    
    def update_agent_status(self, agent_id: str, status: str, health_status: str = None) -> bool:
        """
        Update agent status and health information.
        
        Args:
            agent_id: Agent identifier
            status: New status (active, inactive, paused, error)
            health_status: Health status (healthy, degraded, unhealthy)
            
        Returns:
            success: True if status was updated successfully
        """
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id]['status'] = status
        self.agents[agent_id]['last_seen'] = datetime.utcnow()
        
        if health_status:
            self.agents[agent_id]['health_status'] = health_status
        
        return True
    
    def find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            agents: List of agent records with the specified capability
        """
        if capability not in self.capabilities_index:
            return []
        
        agent_ids = self.capabilities_index[capability]
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def find_agents_by_framework(self, framework: str) -> List[Dict[str, Any]]:
        """
        Find agents by framework.
        
        Args:
            framework: Framework name
            
        Returns:
            agents: List of agent records for the specified framework
        """
        if framework not in self.framework_index:
            return []
        
        agent_ids = self.framework_index[framework]
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def find_agents_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Find agents by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            agents: List of agent records with the specified tag
        """
        if tag not in self.tags_index:
            return []
        
        agent_ids = self.tags_index[tag]
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def search_agents(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for agents using multiple criteria.
        
        Args:
            query: Search criteria dictionary
                - capabilities: List of required capabilities
                - framework: Framework name
                - tags: List of required tags
                - status: Agent status
                - health_status: Health status
                
        Returns:
            agents: List of matching agent records
        """
        matching_agents = list(self.agents.values())
        
        # Filter by capabilities
        if 'capabilities' in query:
            required_capabilities = query['capabilities']
            matching_agents = [
                agent for agent in matching_agents
                if all(cap in agent['capabilities'] for cap in required_capabilities)
            ]
        
        # Filter by framework
        if 'framework' in query:
            framework = query['framework']
            matching_agents = [
                agent for agent in matching_agents
                if agent['framework'] == framework
            ]
        
        # Filter by tags
        if 'tags' in query:
            required_tags = query['tags']
            matching_agents = [
                agent for agent in matching_agents
                if all(tag in agent['tags'] for tag in required_tags)
            ]
        
        # Filter by status
        if 'status' in query:
            status = query['status']
            matching_agents = [
                agent for agent in matching_agents
                if agent['status'] == status
            ]
        
        # Filter by health status
        if 'health_status' in query:
            health_status = query['health_status']
            matching_agents = [
                agent for agent in matching_agents
                if agent['health_status'] == health_status
            ]
        
        return matching_agents
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            agent_info: Agent record or None if not found
        """
        return self.agents.get(agent_id)
    
    def list_all_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents.
        
        Returns:
            agents: List of all agent records
        """
        return list(self.agents.values())
    
    def get_capabilities_catalog(self) -> Dict[str, List[str]]:
        """
        Get a catalog of all available capabilities and the agents that provide them.
        
        Returns:
            catalog: Dictionary mapping capabilities to agent IDs
        """
        return dict(self.capabilities_index)
    
    def get_framework_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of agents by framework.
        
        Returns:
            summary: Framework statistics and agent counts
        """
        summary = {}
        
        for framework, agent_ids in self.framework_index.items():
            agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
            
            status_counts = {}
            health_counts = {}
            
            for agent in agents:
                status = agent['status']
                health = agent['health_status']
                
                status_counts[status] = status_counts.get(status, 0) + 1
                health_counts[health] = health_counts.get(health, 0) + 1
            
            summary[framework] = {
                'total_agents': len(agents),
                'status_breakdown': status_counts,
                'health_breakdown': health_counts,
                'agent_ids': agent_ids
            }
        
        return summary
    
    def update_agent_metadata(self, agent_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """
        Update agent metadata.
        
        Args:
            agent_id: Agent identifier
            metadata_updates: Metadata updates to apply
            
        Returns:
            success: True if metadata was updated successfully
        """
        if agent_id not in self.agents:
            return False
        
        agent_record = self.agents[agent_id]
        
        # Update basic fields
        for field in ['name', 'description', 'version', 'endpoint']:
            if field in metadata_updates:
                agent_record[field] = metadata_updates[field]
        
        # Update metadata
        if 'metadata' in metadata_updates:
            agent_record['metadata'].update(metadata_updates['metadata'])
        
        # Update capabilities and rebuild indexes if changed
        if 'capabilities' in metadata_updates:
            # Remove from old indexes
            self._remove_from_indexes(agent_id, agent_record)
            
            # Update capabilities
            agent_record['capabilities'] = metadata_updates['capabilities']
            
            # Rebuild indexes
            self._update_indexes(agent_id, agent_record)
        
        # Update tags and rebuild indexes if changed
        if 'tags' in metadata_updates:
            # Remove from old indexes
            self._remove_from_indexes(agent_id, agent_record)
            
            # Update tags
            agent_record['tags'] = metadata_updates['tags']
            
            # Rebuild indexes
            self._update_indexes(agent_id, agent_record)
        
        agent_record['updated_at'] = datetime.utcnow()
        return True
    
    def export_registry(self) -> str:
        """
        Export the entire registry as JSON.
        
        Returns:
            json_data: JSON string representation of the registry
        """
        export_data = {
            'agents': {
                agent_id: {
                    **agent_record,
                    'registered_at': agent_record['registered_at'].isoformat(),
                    'last_seen': agent_record['last_seen'].isoformat(),
                    'updated_at': agent_record.get('updated_at', agent_record['registered_at']).isoformat()
                }
                for agent_id, agent_record in self.agents.items()
            },
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_registry(self, json_data: str) -> bool:
        """
        Import registry data from JSON.
        
        Args:
            json_data: JSON string representation of registry data
            
        Returns:
            success: True if import was successful
        """
        try:
            import_data = json.loads(json_data)
            
            for agent_id, agent_record in import_data['agents'].items():
                # Convert timestamp strings back to datetime objects
                agent_record['registered_at'] = datetime.fromisoformat(agent_record['registered_at'])
                agent_record['last_seen'] = datetime.fromisoformat(agent_record['last_seen'])
                if 'updated_at' in agent_record:
                    agent_record['updated_at'] = datetime.fromisoformat(agent_record['updated_at'])
                
                # Register the agent
                self.agents[agent_id] = agent_record
                self._update_indexes(agent_id, agent_record)
            
            return True
            
        except Exception as e:
            print(f"Error importing registry: {e}")
            return False
    
    def _update_indexes(self, agent_id: str, agent_record: Dict[str, Any]):
        """Update search indexes for an agent."""
        # Update capabilities index
        for capability in agent_record['capabilities']:
            if capability not in self.capabilities_index:
                self.capabilities_index[capability] = []
            if agent_id not in self.capabilities_index[capability]:
                self.capabilities_index[capability].append(agent_id)
        
        # Update framework index
        framework = agent_record['framework']
        if framework not in self.framework_index:
            self.framework_index[framework] = []
        if agent_id not in self.framework_index[framework]:
            self.framework_index[framework].append(agent_id)
        
        # Update tags index
        for tag in agent_record['tags']:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            if agent_id not in self.tags_index[tag]:
                self.tags_index[tag].append(agent_id)
    
    def _remove_from_indexes(self, agent_id: str, agent_record: Dict[str, Any]):
        """Remove an agent from search indexes."""
        # Remove from capabilities index
        for capability in agent_record['capabilities']:
            if capability in self.capabilities_index:
                if agent_id in self.capabilities_index[capability]:
                    self.capabilities_index[capability].remove(agent_id)
                if not self.capabilities_index[capability]:
                    del self.capabilities_index[capability]
        
        # Remove from framework index
        framework = agent_record['framework']
        if framework in self.framework_index:
            if agent_id in self.framework_index[framework]:
                self.framework_index[framework].remove(agent_id)
            if not self.framework_index[framework]:
                del self.framework_index[framework]
        
        # Remove from tags index
        for tag in agent_record['tags']:
            if tag in self.tags_index:
                if agent_id in self.tags_index[tag]:
                    self.tags_index[tag].remove(agent_id)
                if not self.tags_index[tag]:
                    del self.tags_index[tag]

