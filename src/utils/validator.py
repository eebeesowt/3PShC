"""
Утилиты для валидации данных.
"""
import re
from typing import Tuple, Optional


class Validator:
    """Валидация входных данных"""
    
    # Regex для IPv4
    IP_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    
    @staticmethod
    def validate_ip(ip: str) -> Tuple[bool, Optional[str]]:
        """
        Валидировать IP адрес.
        
        Returns:
            (is_valid, error_message)
        """
        if not ip:
            return False, "IP address is required"
        
        if not Validator.IP_PATTERN.match(ip):
            return False, "Invalid IP address format"
        
        return True, None
    
    @staticmethod
    def validate_port(port_str: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Валидировать порт.
        
        Returns:
            (is_valid, error_message, port_value)
        """
        if not port_str:
            return False, "Port is required", None
        
        try:
            port = int(port_str)
        except ValueError:
            return False, "Port must be a number", None
        
        if not (1 <= port <= 65535):
            return False, "Port must be between 1 and 65535", None
        
        return True, None, port
    
    @staticmethod
    def validate_required(value: str, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Проверить обязательное поле.
        
        Returns:
            (is_valid, error_message)
        """
        if not value or not value.strip():
            return False, f"{field_name} is required"
        
        return True, None
