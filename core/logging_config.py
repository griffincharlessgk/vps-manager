import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """Setup logging configuration for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    raw_level = os.getenv('LOG_LEVEL', 'INFO')
    log_level = (raw_level or 'INFO').strip().upper()
    if not hasattr(logging, log_level):
        log_level = 'INFO'
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler - chỉ hiển thị WARNING và ERROR trên terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(detailed_formatter)
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    # Suppress noisy loggers - tắt hoàn toàn các log không cần thiết
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('apscheduler').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
    
    # Log application startup - chỉ log khi cần thiết
    logger = logging.getLogger(__name__)
    if log_level == 'DEBUG':
        logger.info(f"Application started with log level: {log_level}")
        logger.info(f"Log files directory: {log_dir}")

def log_security_event(event_type: str, user_id: str = None, details: str = None):
    """Log security events"""
    security_logger = logging.getLogger('security')
    message = f"SECURITY_EVENT: {event_type}"
    if user_id:
        message += f" | User: {user_id}"
    if details:
        message += f" | Details: {details}"
    security_logger.info(message)

def log_api_request(method: str, endpoint: str, user_id: str = None, status_code: int = None):
    """Log API requests"""
    logger = logging.getLogger('api')
    message = f"API_REQUEST: {method} {endpoint}"
    if user_id:
        message += f" | User: {user_id}"
    if status_code:
        message += f" | Status: {status_code}"
    logger.info(message)

def log_database_operation(operation: str, table: str, record_id: str = None):
    """Log database operations"""
    logger = logging.getLogger('database')
    message = f"DB_OPERATION: {operation} on {table}"
    if record_id:
        message += f" | ID: {record_id}"
    logger.info(message) 