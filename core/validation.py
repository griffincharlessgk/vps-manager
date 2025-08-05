import re
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format"""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 64:
        return False, "Username must be less than 64 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    return True, ""

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    if not ip:
        return True  # IP is optional
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """Validate date format"""
    if not date_str:
        return True  # Date is optional
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_integer_range(value: Any, min_val: int = None, max_val: int = None) -> Tuple[bool, str]:
    """Validate integer value within range"""
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            return False, f"Value must be at least {min_val}"
        if max_val is not None and int_val > max_val:
            return False, f"Value must be at most {max_val}"
        return True, ""
    except (ValueError, TypeError):
        return False, "Value must be a valid integer"

def validate_float_range(value: Any, min_val: float = None, max_val: float = None) -> Tuple[bool, str]:
    """Validate float value within range"""
    try:
        float_val = float(value)
        if min_val is not None and float_val < min_val:
            return False, f"Value must be at least {min_val}"
        if max_val is not None and float_val > max_val:
            return False, f"Value must be at most {max_val}"
        return True, ""
    except (ValueError, TypeError):
        return False, "Value must be a valid number"

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input"""
    if not value:
        return ""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(value))
    # Limit length
    return sanitized[:max_length]

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """Validate API key format"""
    if not api_key:
        return False, "API key is required"
    if len(api_key) < 10:
        return False, "API key seems too short"
    if len(api_key) > 512:
        return False, "API key is too long"
    return True, ""

def validate_telegram_chat_id(chat_id: str) -> bool:
    """Validate Telegram chat ID format"""
    if not chat_id:
        return True  # Optional field
    # Telegram chat IDs are typically numbers, can be negative
    try:
        int(chat_id)
        return True
    except ValueError:
        return False

def validate_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize JSON data"""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a JSON object")
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = [sanitize_string(str(item)) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = str(value)
    
    return sanitized

def validate_vps_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate VPS data"""
    required_fields = ['id', 'service', 'name']
    validate_required_fields(data, required_fields)
    
    # Validate individual fields
    if not validate_ip_address(data.get('ip', '')):
        raise ValidationError("Invalid IP address format")
    
    if data.get('expiry') and not validate_date_format(data['expiry']):
        raise ValidationError("Invalid expiry date format (use YYYY-MM-DD)")
    
    return validate_json_data(data)

def validate_account_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Account data"""
    required_fields = ['id', 'service', 'username']
    validate_required_fields(data, required_fields)
    
    if data.get('expiry') and not validate_date_format(data['expiry']):
        raise ValidationError("Invalid expiry date format (use YYYY-MM-DD)")
    
    return validate_json_data(data)

def validate_bitlaunch_api_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate BitLaunch API data"""
    required_fields = ['email', 'api_key']
    validate_required_fields(data, required_fields)
    
    if not validate_email(data['email']):
        raise ValidationError("Invalid email format")
    
    is_valid, error_msg = validate_api_key(data['api_key'])
    if not is_valid:
        raise ValidationError(error_msg)
    
    # Validate update_frequency
    if 'update_frequency' in data:
        is_valid, error_msg = validate_integer_range(data['update_frequency'], 1, 30)
        if not is_valid:
            raise ValidationError(error_msg)
    
    return validate_json_data(data)

def validate_zingproxy_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ZingProxy data"""
    required_fields = ['email', 'password']
    validate_required_fields(data, required_fields)
    
    if not validate_email(data['email']):
        raise ValidationError("Invalid email format")
    
    is_valid, error_msg = validate_password(data['password'])
    if not is_valid:
        raise ValidationError(error_msg)
    
    return validate_json_data(data) 