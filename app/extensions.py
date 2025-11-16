import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path

class UserContextFilter(logging.Filter):
    """ filter to add user context to log errors to avoid raising exceptions"""
    def __init__(self):
        super().__init__()
        self.user_id = "SYSTEM"
        
    def filter(self, record):
        record.user_id = getattr(record, "user_id", self.user_id)
        return True


def ensure_log_directory(log_path):
    """
    ensure that the directory for a log file exists

    Args:
        log_path (str): path to the log file
    """
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
def setup_logging(log_level='INFO', log_dir='logs', log_file='app.log', error_log_file='errors.log') -> logging.Logger:
    """
    setup logging configurstion for the application

    Args:
        log_level (str):  log level(DEBUG, INFO, WARNING, ERROR, CRITICAL)  Defaults to 'INFO'.
        log_dir (str): directory for the log fiiles
        log_file (str): name of the main log file Defaults to 'app.log'.
        error_log_file (str): name of the main error log file Defaults to 'errors.log'.
    """
    log_level = log_level.upper()
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        log_level = 'INFO'
        numeric_level = logging.INFO
        
    log_dir_path = Path(log_dir)
    app_log_path = str(log_dir_path / log_file)
    error_log_path = str(log_dir_path / error_log_file)
    
    ensure_log_directory(app_log_path)
    ensure_log_directory(error_log_path)
    
    logger = logging.getLogger()
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)-8s - User:%(user_id)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M'
    )
    user_filter = UserContextFilter()
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    console_handler.addFilter(user_filter)
    logger.addHandler(console_handler)
    
    file_handler = TimedRotatingFileHandler(
        filename=app_log_path, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    file_handler.addFilter(user_filter)
    logger.addHandler(file_handler)
    
    error_handler = TimedRotatingFileHandler(
        filename=error_log_path, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(user_filter)
    logger.addHandler(error_handler)
    
    return logger


logger = setup_logging()
    
    