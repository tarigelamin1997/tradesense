"""
Data Validation and Input Sanitization

Provides comprehensive validation utilities for API inputs, trade data, and user inputs.
"""
import re
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, field_validator, ValidationError
import html

logger = logging.getLogger(__name__)

class CustomValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS and injection attacks"""
    if not isinstance(value, str):
        return str(value)
    
    # Remove HTML tags and entities
    sanitized = html.escape(value.strip())
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    return sanitized

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    if not symbol:
        return False
    
    # Basic symbol validation (alphanumeric, dots, hyphens)
    pattern = r'^[A-Za-z0-9.-]{1,10}$'
    return bool(re.match(pattern, symbol))

def validate_price(price: Union[str, float, Decimal]) -> bool:
    """Validate price format and range"""
    try:
        if isinstance(price, str):
            price = Decimal(price)
        elif isinstance(price, float):
            price = Decimal(str(price))
        
        return price > 0 and price <= 1000000  # Reasonable price range
    except (InvalidOperation, ValueError):
        return False

def validate_quantity(quantity: Union[str, float, int]) -> bool:
    """Validate trade quantity"""
    try:
        if isinstance(quantity, str):
            quantity = float(quantity)
        
        return quantity > 0 and quantity <= 1000000  # Reasonable quantity range
    except (ValueError, TypeError):
        return False

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate date range"""
    if not start_date or not end_date:
        return False
    
    if start_date >= end_date:
        return False
    
    # Check if range is reasonable (not more than 10 years)
    max_range = timedelta(days=3650)
    if end_date - start_date > max_range:
        return False
    
    return True

class TradeDataValidator(BaseModel):
    """Validate trade data structure"""
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    strategy_tag: Optional[str] = None
    confidence_score: Optional[float] = None
    notes: Optional[str] = None
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not validate_symbol(v):
            raise ValueError('Invalid symbol format')
        return v.upper()
    
    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v):
        if v not in ['long', 'short', 'buy', 'sell']:
            raise ValueError('Direction must be long, short, buy, or sell')
        return v.lower()
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if not validate_quantity(v):
            raise ValueError('Invalid quantity')
        return v
    
    @field_validator('entry_price')
    @classmethod
    def validate_entry_price(cls, v):
        if not validate_price(v):
            raise ValueError('Invalid entry price')
        return v
    
    @field_validator('exit_price')
    @classmethod
    def validate_exit_price(cls, v):
        if v is not None and not validate_price(v):
            raise ValueError('Invalid exit price')
        return v
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Confidence score must be between 0 and 100')
        return v
    
    @field_validator('notes')
    @classmethod
    def sanitize_notes(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class UserDataValidator(BaseModel):
    """Validate user data structure"""
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 30:
            raise ValueError('Username must be between 3 and 30 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError(f'Password validation failed: {", ".join(errors)}')
        return v
    
    @field_validator('first_name')
    @classmethod
    def sanitize_first_name(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v
    
    @field_validator('last_name')
    @classmethod
    def sanitize_last_name(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

def validate_trade_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate trade data and return validation result"""
    try:
        TradeDataValidator(**data)
        return True, []
    except CustomValidationError as e:
        errors = [f"{field}: {error}" for field, error in e.errors()]
        return False, errors

def validate_user_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate user data and return validation result"""
    try:
        UserDataValidator(**data)
        return True, []
    except CustomValidationError as e:
        errors = [f"{field}: {error}" for field, error in e.errors()]
        return False, errors

def sanitize_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all string inputs in a dictionary"""
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_input_data(item) if isinstance(item, dict) else 
                            sanitize_string(item) if isinstance(item, str) else item 
                            for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

def validate_pagination_params(page: int, per_page: int) -> Tuple[bool, List[str]]:
    """Validate pagination parameters"""
    errors = []
    
    if page < 1:
        errors.append("Page must be greater than 0")
    
    if per_page < 1 or per_page > 100:
        errors.append("Per page must be between 1 and 100")
    
    return len(errors) == 0, errors

def validate_date_format(date_str: str) -> bool:
    """Validate date string format"""
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower())) 