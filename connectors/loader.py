
import os
import importlib.util
import inspect
from typing import List, Dict, Any
from .base import ConnectorBase
from .registry import registry

def load_connectors(connector_dirs: List[str] = None) -> Dict[str, Any]:
    """Dynamically load connectors from specified directories.
    
    Args:
        connector_dirs: List of directories to scan for connectors
        
    Returns:
        Dict with loading results and errors
    """
    if connector_dirs is None:
        connector_dirs = [
            "connectors",
            "connectors/brokers", 
            "connectors/csv",
            "connectors/api"
        ]
    
    # Initialize registry with built-in connectors
    from .brokers.interactive_brokers import InteractiveBrokersConnector
    from .brokers.td_ameritrade import TDAmeritudeConnector  
    from .brokers.apex_trader import ApexTraderConnector
    
    # Register built-in connectors
    registry.register(InteractiveBrokersConnector, 'interactive_brokers')
    registry.register(TDAmeritudeConnector, 'td_ameritrade')
    registry.register(ApexTraderConnector, 'apex_trader')
    
    results = {
        'loaded': [],
        'errors': [],
        'total_found': 0
    }
    
    for connector_dir in connector_dirs:
        if not os.path.exists(connector_dir):
            continue
            
        for filename in os.listdir(connector_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_path = os.path.join(connector_dir, filename)
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Load module dynamically
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find connector classes
                    connector_classes = []
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, ConnectorBase) and 
                            obj != ConnectorBase):
                            connector_classes.append(obj)
                    
                    # Register found connectors
                    for connector_class in connector_classes:
                        registry.register(connector_class)
                        results['loaded'].append({
                            'name': connector_class.__name__,
                            'module': module_name,
                            'path': module_path
                        })
                        results['total_found'] += 1
                        
                except Exception as e:
                    results['errors'].append({
                        'file': filename,
                        'error': str(e)
                    })
    
    return results

def get_available_connectors() -> List[Dict[str, Any]]:
    """Get list of all available connectors with metadata."""
    connectors = []
    
    for name in registry.list_connectors():
        try:
            instance = registry.create_instance(name)
            metadata = instance.get_metadata()
            connectors.append(metadata)
        except Exception as e:
            connectors.append({
                'name': name,
                'error': str(e),
                'status': 'error'
            })
    
    return connectors

def test_connector(name: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a specific connector."""
    try:
        instance = registry.create_instance(name, config)
        
        # Test connection
        connection_ok = instance.validate_connection()
        
        # Test data quality
        quality_report = instance.test_data_quality()
        
        return {
            'name': name,
            'connection_status': 'ok' if connection_ok else 'failed',
            'quality_report': quality_report,
            'metadata': instance.get_metadata()
        }
        
    except Exception as e:
        return {
            'name': name,
            'error': str(e),
            'status': 'error'
        }
