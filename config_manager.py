import os
import json
import yaml
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from pathlib import Path

class ConfigurationManager:
    """Centralized configuration management service."""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.join(os.path.dirname(__file__), '..', 'config'))
        self.config_dir.mkdir(exist_ok=True)
        
        self.configurations = {}  # config_name -> config_data
        self.config_metadata = {}  # config_name -> metadata
        self.watchers = {}  # config_name -> list of callback functions
        self.lock = threading.RLock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load default configurations
        self._load_default_configs()
        
    def _load_default_configs(self):
        """Load default system configurations."""
        default_configs = {
            'system': {
                'name': 'AgentOrchestra',
                'version': '1.0.0',
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'max_agents': int(os.getenv('MAX_AGENTS', '100')),
                'task_timeout': int(os.getenv('TASK_TIMEOUT', '300')),
                'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
            },
            'database': {
                'url': os.getenv('DATABASE_URL', 'sqlite:///agent_orchestra.db'),
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                'echo': os.getenv('DB_ECHO', 'false').lower() == 'true'
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD'),
                'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
            },
            'security': {
                'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
                'jwt_expiration': int(os.getenv('JWT_EXPIRATION', '3600')),
                'bcrypt_rounds': int(os.getenv('BCRYPT_ROUNDS', '12')),
                'cors_origins': os.getenv('CORS_ORIGINS', '*').split(','),
                'rate_limit': os.getenv('RATE_LIMIT', '100/hour')
            },
            'monitoring': {
                'metrics_enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
                'metrics_port': int(os.getenv('METRICS_PORT', '9090')),
                'health_check_enabled': os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
                'alert_webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
                'log_retention_days': int(os.getenv('LOG_RETENTION_DAYS', '30'))
            },
            'agents': {
                'default_timeout': int(os.getenv('AGENT_DEFAULT_TIMEOUT', '300')),
                'max_retries': int(os.getenv('AGENT_MAX_RETRIES', '3')),
                'heartbeat_interval': int(os.getenv('AGENT_HEARTBEAT_INTERVAL', '60')),
                'auto_restart': os.getenv('AGENT_AUTO_RESTART', 'true').lower() == 'true',
                'resource_limits': {
                    'cpu_percent': int(os.getenv('AGENT_CPU_LIMIT', '80')),
                    'memory_mb': int(os.getenv('AGENT_MEMORY_LIMIT', '1024'))
                }
            },
            'workflows': {
                'max_concurrent': int(os.getenv('WORKFLOW_MAX_CONCURRENT', '10')),
                'default_timeout': int(os.getenv('WORKFLOW_DEFAULT_TIMEOUT', '1800')),
                'auto_cleanup': os.getenv('WORKFLOW_AUTO_CLEANUP', 'true').lower() == 'true',
                'cleanup_after_days': int(os.getenv('WORKFLOW_CLEANUP_DAYS', '7')),
                'enable_versioning': os.getenv('WORKFLOW_VERSIONING', 'true').lower() == 'true'
            }
        }
        
        for config_name, config_data in default_configs.items():
            self.set_config(config_name, config_data, save_to_file=False)
            
    def get_config(self, config_name: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value."""
        with self.lock:
            config = self.configurations.get(config_name)
            
            if config is None:
                return default
                
            if key is None:
                return config
                
            # Support nested keys with dot notation
            keys = key.split('.')
            value = config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value
            
    def set_config(self, config_name: str, config_data: Dict[str, Any], 
                   save_to_file: bool = True, notify_watchers: bool = True) -> bool:
        """Set configuration data."""
        try:
            with self.lock:
                old_config = self.configurations.get(config_name)
                self.configurations[config_name] = config_data
                
                # Update metadata
                self.config_metadata[config_name] = {
                    'last_updated': datetime.utcnow().isoformat(),
                    'version': self.config_metadata.get(config_name, {}).get('version', 0) + 1
                }
                
                # Save to file if requested
                if save_to_file:
                    self._save_config_to_file(config_name, config_data)
                    
                # Notify watchers
                if notify_watchers and config_name in self.watchers:
                    for callback in self.watchers[config_name]:
                        try:
                            callback(config_name, old_config, config_data)
                        except Exception as e:
                            self.logger.error(f"Error calling config watcher: {e}")
                            
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting config {config_name}: {e}")
            return False
            
    def update_config(self, config_name: str, updates: Dict[str, Any], 
                     save_to_file: bool = True) -> bool:
        """Update specific keys in a configuration."""
        with self.lock:
            current_config = self.configurations.get(config_name, {})
            
            # Deep merge updates
            updated_config = self._deep_merge(current_config.copy(), updates)
            
            return self.set_config(config_name, updated_config, save_to_file)
            
    def delete_config(self, config_name: str, remove_file: bool = True) -> bool:
        """Delete a configuration."""
        try:
            with self.lock:
                if config_name in self.configurations:
                    del self.configurations[config_name]
                    
                if config_name in self.config_metadata:
                    del self.config_metadata[config_name]
                    
                if config_name in self.watchers:
                    del self.watchers[config_name]
                    
                # Remove file if requested
                if remove_file:
                    config_file = self.config_dir / f"{config_name}.json"
                    if config_file.exists():
                        config_file.unlink()
                        
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting config {config_name}: {e}")
            return False
            
    def list_configs(self) -> List[Dict[str, Any]]:
        """List all configurations with metadata."""
        with self.lock:
            configs = []
            for config_name in self.configurations:
                metadata = self.config_metadata.get(config_name, {})
                configs.append({
                    'name': config_name,
                    'last_updated': metadata.get('last_updated'),
                    'version': metadata.get('version', 0),
                    'keys': list(self.configurations[config_name].keys()) if isinstance(self.configurations[config_name], dict) else []
                })
            return configs
            
    def watch_config(self, config_name: str, callback: callable):
        """Register a callback to be notified when configuration changes."""
        with self.lock:
            if config_name not in self.watchers:
                self.watchers[config_name] = []
            self.watchers[config_name].append(callback)
            
    def unwatch_config(self, config_name: str, callback: callable):
        """Unregister a configuration watcher."""
        with self.lock:
            if config_name in self.watchers:
                try:
                    self.watchers[config_name].remove(callback)
                    if not self.watchers[config_name]:
                        del self.watchers[config_name]
                except ValueError:
                    pass
                    
    def load_config_from_file(self, config_name: str, file_path: str = None) -> bool:
        """Load configuration from a file."""
        try:
            if file_path is None:
                file_path = self.config_dir / f"{config_name}.json"
            else:
                file_path = Path(file_path)
                
            if not file_path.exists():
                self.logger.warning(f"Config file not found: {file_path}")
                return False
                
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() == '.yaml' or file_path.suffix.lower() == '.yml':
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
                    
            return self.set_config(config_name, config_data, save_to_file=False)
            
        except Exception as e:
            self.logger.error(f"Error loading config from file {file_path}: {e}")
            return False
            
    def _save_config_to_file(self, config_name: str, config_data: Dict[str, Any]):
        """Save configuration to file."""
        try:
            config_file = self.config_dir / f"{config_name}.json"
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving config to file: {e}")
            
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
        
    def export_config(self, config_name: str, format: str = 'json') -> Optional[str]:
        """Export configuration as string."""
        with self.lock:
            config = self.configurations.get(config_name)
            if config is None:
                return None
                
            try:
                if format.lower() == 'yaml':
                    return yaml.dump(config, default_flow_style=False)
                else:
                    return json.dumps(config, indent=2, default=str)
                    
            except Exception as e:
                self.logger.error(f"Error exporting config: {e}")
                return None
                
    def import_config(self, config_name: str, config_string: str, format: str = 'json') -> bool:
        """Import configuration from string."""
        try:
            if format.lower() == 'yaml':
                config_data = yaml.safe_load(config_string)
            else:
                config_data = json.loads(config_string)
                
            return self.set_config(config_name, config_data)
            
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")
            return False
            
    def validate_config(self, config_name: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate configuration against a schema."""
        # Basic validation implementation
        # In production, you might use jsonschema or similar
        
        config = self.configurations.get(config_name)
        if config is None:
            return {'valid': False, 'errors': ['Configuration not found']}
            
        errors = []
        warnings = []
        
        # Basic type checking
        if schema:
            errors.extend(self._validate_against_schema(config, schema))
            
        # System-specific validations
        if config_name == 'system':
            if config.get('max_agents', 0) <= 0:
                errors.append('max_agents must be greater than 0')
                
        elif config_name == 'database':
            if not config.get('url'):
                errors.append('database.url is required')
                
        elif config_name == 'security':
            if config.get('secret_key') == 'dev-secret-key-change-in-production':
                warnings.append('Using default secret key in production is not secure')
                
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate configuration against a simple schema."""
        errors = []
        
        # Check required fields
        required = schema.get('required', [])
        for field in required:
            if field not in config:
                errors.append(f"Required field '{field}' is missing")
                
        # Check field types
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in config:
                expected_type = field_schema.get('type')
                actual_value = config[field]
                
                if expected_type == 'string' and not isinstance(actual_value, str):
                    errors.append(f"Field '{field}' must be a string")
                elif expected_type == 'integer' and not isinstance(actual_value, int):
                    errors.append(f"Field '{field}' must be an integer")
                elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                    errors.append(f"Field '{field}' must be a boolean")
                elif expected_type == 'array' and not isinstance(actual_value, list):
                    errors.append(f"Field '{field}' must be an array")
                elif expected_type == 'object' and not isinstance(actual_value, dict):
                    errors.append(f"Field '{field}' must be an object")
                    
        return errors
        
    def backup_configs(self, backup_dir: str = None) -> str:
        """Create a backup of all configurations."""
        if backup_dir is None:
            backup_dir = self.config_dir / 'backups'
            
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"config_backup_{timestamp}.json"
        
        try:
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'configurations': self.configurations,
                'metadata': self.config_metadata
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
                
            self.logger.info(f"Configuration backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            self.logger.error(f"Error creating config backup: {e}")
            raise
            
    def restore_configs(self, backup_file: str) -> bool:
        """Restore configurations from a backup file."""
        try:
            backup_file = Path(backup_file)
            
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
                
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
                
            # Restore configurations
            with self.lock:
                self.configurations = backup_data.get('configurations', {})
                self.config_metadata = backup_data.get('metadata', {})
                
            # Save all configs to files
            for config_name, config_data in self.configurations.items():
                self._save_config_to_file(config_name, config_data)
                
            self.logger.info(f"Configurations restored from: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring config backup: {e}")
            return False

# Global configuration manager instance
config_manager = ConfigurationManager()

