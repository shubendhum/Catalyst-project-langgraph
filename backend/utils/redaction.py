"""
Log Redaction Utility
Masks sensitive information in logs
"""
import re
from typing import Any, Dict, List


# Patterns for sensitive data
PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'api_key': re.compile(r'\b(sk-[a-zA-Z0-9]{20,}|[a-zA-Z0-9_-]{32,})\b'),
    'bearer_token': re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE),
    'password': re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
}


def redact_sensitive(data: Any, mask: str = "***REDACTED***") -> Any:
    """
    Redact sensitive information from data
    
    Args:
        data: Data to redact (str, dict, list, etc.)
        mask: Replacement string for sensitive data
        
    Returns:
        Redacted data
    """
    if isinstance(data, str):
        return redact_string(data, mask)
    elif isinstance(data, dict):
        return redact_dict(data, mask)
    elif isinstance(data, list):
        return [redact_sensitive(item, mask) for item in data]
    else:
        return data


def redact_string(text: str, mask: str = "***REDACTED***") -> str:
    """Redact sensitive patterns in a string"""
    result = text
    
    for pattern_name, pattern in PATTERNS.items():
        if pattern_name == 'email':
            # Keep domain for emails, redact local part
            result = pattern.sub(lambda m: f"***@{m.group().split('@')[1]}", result)
        elif pattern_name == 'password':
            # Redact password values
            result = pattern.sub(lambda m: f"{m.group(1)}={mask}", result)
        else:
            # Redact entire match
            result = pattern.sub(mask, result)
    
    return result


def redact_dict(data: Dict[str, Any], mask: str = "***REDACTED***") -> Dict[str, Any]:
    """Redact sensitive keys and values in a dictionary"""
    sensitive_keys = [
        'password', 'passwd', 'pwd', 'api_key', 'apikey', 'secret', 
        'token', 'authorization', 'auth', 'credential', 'private_key',
        'access_token', 'refresh_token', 'session_id', 'cookie'
    ]
    
    result = {}
    for key, value in data.items():
        # Check if key is sensitive
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            result[key] = mask
        elif isinstance(value, str):
            result[key] = redact_string(value, mask)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, mask)
        elif isinstance(value, list):
            result[key] = [redact_sensitive(item, mask) for item in value]
        else:
            result[key] = value
    
    return result


def safe_log_data(data: Any) -> Any:
    """
    Prepare data for safe logging by redacting sensitive information
    
    This is the main function to use when logging request/response data
    """
    return redact_sensitive(data)
