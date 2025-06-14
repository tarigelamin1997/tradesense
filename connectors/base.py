
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

class ConnectorBase(ABC):
    """Base class for all trading data connectors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize connector with configuration."""
        self.config = config or {}
        self.name = self.__class__.__name__
        self.authenticated = False
        
    @property
    @abstractmethod
    def connector_type(self) -> str:
        """Return the type of connector (e.g., 'broker', 'csv', 'api')."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported data formats (e.g., ['csv', 'json', 'api'])."""
        pass
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the data source.
        
        Args:
            credentials: Dictionary containing authentication data
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from the source.
        
        Args:
            start_date: Start date for trade data
            end_date: End date for trade data
            symbol: Optional symbol filter
            **kwargs: Additional connector-specific parameters
            
        Returns:
            List of raw trade dictionaries
        """
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize raw trade data to standard format.
        
        Args:
            raw_data: Raw trade data from fetch_trades()
            
        Returns:
            DataFrame with standardized columns matching universal schema
        """
        pass
    
    def to_universal_model(self, raw_data: List[Dict[str, Any]]) -> 'UniversalTradeDataModel':
        """Convert raw data to universal trade model."""
        from models.trade_model import UniversalTradeDataModel
        
        # First normalize to DataFrame
        df = self.normalize_data(raw_data)
        
        # Then convert to universal model
        model = UniversalTradeDataModel()
        return model.from_dataframe(df, self.connector_type)
    
    def validate_connection(self) -> bool:
        """Test connection to data source."""
        try:
            # Attempt to fetch a small amount of data
            test_data = self.fetch_trades()
            return len(test_data) >= 0  # Even empty results indicate successful connection
        except Exception:
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return connector metadata and capabilities."""
        return {
            'name': self.name,
            'type': self.connector_type,
            'supported_formats': self.supported_formats,
            'authenticated': self.authenticated,
            'config_required': self.get_required_config(),
            'optional_params': self.get_optional_params()
        }
    
    def get_required_config(self) -> List[str]:
        """Return list of required configuration keys."""
        return []
    
    def get_optional_params(self) -> List[str]:
        """Return list of optional parameters for fetch_trades."""
        return []
    
    def test_data_quality(self, sample_size: int = 10) -> Dict[str, Any]:
        """Test data quality by fetching a small sample."""
        try:
            raw_data = self.fetch_trades()[:sample_size]
            if not raw_data:
                return {'status': 'no_data', 'message': 'No trade data available'}
            
            normalized_df = self.normalize_data(raw_data)
            
            # Basic quality checks
            quality_report = {
                'status': 'success',
                'sample_size': len(normalized_df),
                'columns': list(normalized_df.columns),
                'missing_required': [],
                'data_types': normalized_df.dtypes.to_dict()
            }
            
            # Check for required columns using universal model
            from models.trade_model import UniversalTradeDataModel
            required_cols = UniversalTradeDataModel().get_required_columns()
            for col in required_cols:
                if col not in normalized_df.columns:
                    quality_report['missing_required'].append(col)
            
            return quality_report
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
