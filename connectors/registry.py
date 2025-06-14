
from typing import Dict, List, Type, Any
import importlib
import inspect
from .base import ConnectorBase

class ConnectorRegistry:
    """Registry for managing and discovering connectors."""
    
    def __init__(self):
        self._connectors: Dict[str, Type[ConnectorBase]] = {}
        self._instances: Dict[str, ConnectorBase] = {}
    
    def register(self, connector_class: Type[ConnectorBase], name: str = None):
        """Register a connector class."""
        if not issubclass(connector_class, ConnectorBase):
            raise ValueError(f"Connector {connector_class} must inherit from ConnectorBase")
        
        name = name or connector_class.__name__
        self._connectors[name] = connector_class
        
    def unregister(self, name: str):
        """Unregister a connector."""
        if name in self._connectors:
            del self._connectors[name]
        if name in self._instances:
            del self._instances[name]
    
    def get_connector_class(self, name: str) -> Type[ConnectorBase]:
        """Get connector class by name."""
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' not found in registry")
        return self._connectors[name]
    
    def create_instance(self, name: str, config: Dict[str, Any] = None) -> ConnectorBase:
        """Create and cache connector instance."""
        if name not in self._instances:
            connector_class = self.get_connector_class(name)
            self._instances[name] = connector_class(config)
        return self._instances[name]
    
    def list_connectors(self) -> List[str]:
        """List all registered connector names."""
        return list(self._connectors.keys())
    
    def get_connector_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a connector."""
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' not found")
        
        connector_class = self._connectors[name]
        
        # Get class docstring and methods
        info = {
            'name': name,
            'class_name': connector_class.__name__,
            'module': connector_class.__module__,
            'docstring': connector_class.__doc__,
            'methods': []
        }
        
        # Get method signatures
        for method_name, method in inspect.getmembers(connector_class, predicate=inspect.ismethod):
            if not method_name.startswith('_'):
                try:
                    signature = inspect.signature(method)
                    info['methods'].append({
                        'name': method_name,
                        'signature': str(signature),
                        'docstring': method.__doc__
                    })
                except:
                    pass
        
        return info
    
    def filter_by_type(self, connector_type: str) -> List[str]:
        """Filter connectors by type."""
        matching = []
        for name in self._connectors:
            try:
                # Create temporary instance to check type
                instance = self.create_instance(name)
                if instance.connector_type == connector_type:
                    matching.append(name)
            except:
                pass
        return matching
    
    def auto_discover(self, package_path: str = "connectors"):
        """Auto-discover connectors in specified package."""
        try:
            package = importlib.import_module(package_path)
            
            # Look for connector modules
            for module_name in dir(package):
                if module_name.startswith('_'):
                    continue
                
                try:
                    module = importlib.import_module(f"{package_path}.{module_name}")
                    
                    # Find connector classes in module
                    for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(class_obj, ConnectorBase) and 
                            class_obj != ConnectorBase and
                            class_obj.__module__ == module.__name__):
                            self.register(class_obj)
                            
                except ImportError:
                    continue
                    
        except ImportError:
            pass

# Global registry instance
registry = ConnectorRegistry()
