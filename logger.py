import logging
import os
import traceback
from datetime import datetime
from config import Config

class Logger:
    def __init__(self):
        self.log_file = Config.LOG_FILE
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('GymChatbot')
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def error_with_trace(self, exception, context=""):
        """Log error with full traceback"""
        error_msg = f"{context}: {str(exception)}" if context else str(exception)
        self.logger.error(error_msg)
        self.logger.error(traceback.format_exc())
    
    def log_data_scan(self, total_files, new_files):
        """Log data scan results"""
        if new_files:
            self.info(f"Data scan: Found {len(new_files)} new file(s) out of {total_files} total")
            for file in new_files:
                self.info(f"  New file detected: {file}")
        else:
            self.info(f"Data scan: No new files detected ({total_files} files total)")
    
    def get_log_path(self):
        """Get the log file path"""
        return self.log_file

logger = Logger()