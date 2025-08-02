"""Configuration management system with layered approach."""
from typing import Dict, Any, List, Optional, Callable, cast, TypeVar
import os
import json
import yaml
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Type variable for type-safe conversions
T = TypeVar('T')

class ConfigSource(ABC):
    """Interface for configuration sources."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get config value by key.
        
        Args:
            key: Config key to get
            
        Returns:
            Config value or None if not found
        """
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        Get all config values.
        
        Returns:
            Dictionary of all config values
        """
        pass


class EnvConfigSource(ConfigSource):
    """Environment variable configuration source."""
    
    def __init__(self, prefix: str = ""):
        """
        Initialize environment config source.
        
        Args:
            prefix: Environment variable prefix
        """
        self.prefix = prefix
        logger.debug(f"Created environment config source with prefix '{prefix}'")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get config value from environment.
        
        Args:
            key: Config key to get
            
        Returns:
            Config value or None if not found
        """
        env_key = f"{self.prefix}{key.upper()}"
        value = os.environ.get(env_key)
        logger.debug(f"Environment config get: {env_key} = {value}")
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all config values from environment.
        
        Returns:
            Dictionary of all config values
        """
        result = {}
        for key, value in os.environ.items():
            if not self.prefix or key.startswith(self.prefix):
                # Remove prefix if present
                config_key = key
                if self.prefix and key.startswith(self.prefix):
                    config_key = key[len(self.prefix):]
                    
                result[config_key.lower()] = value
                
        return result


class JsonConfigSource(ConfigSource):
    """JSON file configuration source."""
    
    def __init__(self, file_path: str):
        """
        Initialize JSON config source.
        
        Args:
            file_path: Path to JSON file
        """
        self.file_path = file_path
        self._config = self._load_config()
        logger.debug(f"Created JSON config source from {file_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load config from JSON file.
        
        Returns:
            Config dictionary
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON config file {self.file_path}: {e}")
            return {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get config value from JSON.
        
        Args:
            key: Config key to get
            
        Returns:
            Config value or None if not found
        """
        # Support dot notation for nested keys
        parts = key.split('.')
        result = self._config
        
        for part in parts:
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return None
                
        return result
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all config values from JSON.
        
        Returns:
            Dictionary of all config values
        """
        return self._config


class YamlConfigSource(ConfigSource):
    """YAML file configuration source."""
    
    def __init__(self, file_path: str):
        """
        Initialize YAML config source.
        
        Args:
            file_path: Path to YAML file
        """
        self.file_path = file_path
        self._config = self._load_config()
        logger.debug(f"Created YAML config source from {file_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load config from YAML file.
        
        Returns:
            Config dictionary
        """
        try:
            with open(self.file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.file_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config file {self.file_path}: {e}")
            return {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get config value from YAML.
        
        Args:
            key: Config key to get
            
        Returns:
            Config value or None if not found
        """
        # Support dot notation for nested keys
        parts = key.split('.')
        result = self._config
        
        for part in parts:
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return None
                
        return result
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all config values from YAML.
        
        Returns:
            Dictionary of all config values
        """
        return self._config


class InMemoryConfigSource(ConfigSource):
    """In-memory configuration source."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize in-memory config source.
        
        Args:
            config: Initial config dictionary
        """
        self._config = config or {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get config value from memory.
        
        Args:
            key: Config key to get
            
        Returns:
            Config value or None if not found
        """
        # Support dot notation for nested keys
        parts = key.split('.')
        result = self._config
        
        for part in parts:
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return None
                
        return result
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all config values from memory.
        
        Returns:
            Dictionary of all config values
        """
        return self._config
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Config key to set
            value: Config value to set
        """
        # Support dot notation for nested keys
        parts = key.split('.')
        
        # Navigate to the deepest level
        config = self._config
        for i, part in enumerate(parts[:-1]):
            if part not in config or not isinstance(config[part], dict):
                config[part] = {}
            config = config[part]
        
        # Set the value
        config[parts[-1]] = value


class ConfigManager:
    """
    Manages configuration from multiple sources with layered priority.
    """
    
    def __init__(self, sources: List[ConfigSource] = None):
        """
        Initialize config manager.
        
        Args:
            sources: Configuration sources in priority order (highest priority first)
        """
        self._sources = sources or []
        logger.info(f"Created config manager with {len(self._sources)} sources")
    
    def add_source(self, source: ConfigSource, priority: int = 0) -> None:
        """
        Add a configuration source.
        
        Args:
            source: Configuration source
            priority: Priority level (0 is highest)
        """
        if priority >= len(self._sources):
            self._sources.append(source)
        else:
            self._sources.insert(priority, source)
        logger.debug(f"Added config source at priority {priority}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        for source in self._sources:
            value = source.get(key)
            if value is not None:
                return value
                
        return default
    
    def get_typed(self, key: str, type_converter: Callable[[Any], T], default: T = None) -> T:
        """
        Get a configuration value with type conversion.
        
        Args:
            key: Configuration key
            type_converter: Function to convert value to desired type
            default: Default value if not found
            
        Returns:
            Converted configuration value or default
        """
        value = self.get(key)
        if value is None:
            return default
            
        try:
            return type_converter(value)
        except Exception as e:
            logger.warning(f"Error converting config value for {key}: {e}")
            return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Integer configuration value or default
        """
        return self.get_typed(key, int, default)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a float configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Float configuration value or default
        """
        return self.get_typed(key, float, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Boolean configuration value or default
        """
        value = self.get(key)
        if value is None:
            return default
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y", "on")
            
        return bool(value)
    
    def get_list(self, key: str, item_type: Callable[[Any], T] = None, default: List = None) -> List:
        """
        Get a list configuration value.
        
        Args:
            key: Configuration key
            item_type: Function to convert list items
            default: Default value if not found
            
        Returns:
            List configuration value or default
        """
        value = self.get(key)
        if not value:
            return default or []
            
        if not isinstance(value, list):
            try:
                value = json.loads(value)
                if not isinstance(value, list):
                    value = [value]
            except (json.JSONDecodeError, TypeError):
                value = [value]
                
        if item_type:
            try:
                return [item_type(item) for item in value]
            except Exception as e:
                logger.warning(f"Error converting list items for {key}: {e}")
                return default or []
                
        return value
    
    def get_dict(self, key: str, default: Dict = None) -> Dict:
        """
        Get a dictionary configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Dictionary configuration value or default
        """
        value = self.get(key)
        if not value:
            return default or {}
            
        if not isinstance(value, dict):
            try:
                value = json.loads(value)
                if not isinstance(value, dict):
                    return default or {}
            except (json.JSONDecodeError, TypeError):
                return default or {}
                
        return value
    
    @staticmethod
    def create_default() -> 'ConfigManager':
        """
        Create a default config manager with standard sources.
        
        Returns:
            Configured config manager
        """
        manager = ConfigManager()
        
        # Add sources in priority order (higher priority first)
        manager.add_source(EnvConfigSource())
        
        # Try to load local config files if they exist
        if os.path.exists('config.local.yaml'):
            manager.add_source(YamlConfigSource('config.local.yaml'))
            
        if os.path.exists('config.yaml'):
            manager.add_source(YamlConfigSource('config.yaml'))
            
        if os.path.exists('config.local.json'):
            manager.add_source(JsonConfigSource('config.local.json'))
            
        if os.path.exists('config.json'):
            manager.add_source(JsonConfigSource('config.json'))
            
        return manager 