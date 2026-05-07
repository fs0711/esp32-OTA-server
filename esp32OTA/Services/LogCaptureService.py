"""
Log Capture Service - Captures terminal/stdout logs in memory
"""
import sys
import io
import logging
from datetime import datetime
from threading import Lock
from collections import deque


class LogCaptureService:
    """Service to capture and manage application logs"""
    
    _logs = deque(maxlen=2000)  # Keep last 2000 log entries
    _lock = Lock()
    _original_stdout = None
    _original_stderr = None
    _log_handler = None
    
    class MemoryLogHandler(logging.Handler):
        """Custom logging handler to capture logs from logging module"""
        def emit(self, record):
            try:
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                    "level": record.levelname,
                    "message": self.format(record)
                }
                
                with LogCaptureService._lock:
                    LogCaptureService._logs.append(log_entry)
            except Exception:
                pass
    
    class LogWriter:
        """Custom writer to capture logs"""
        def __init__(self, original_stream, is_stderr=False):
            self.original_stream = original_stream
            self.is_stderr = is_stderr
            self.buffer = ""
        
        def write(self, message):
            if message and message.strip():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_level = "ERROR" if self.is_stderr else "INFO"
                log_entry = {
                    "timestamp": timestamp,
                    "level": log_level,
                    "message": message.strip()
                }
                
                with LogCaptureService._lock:
                    LogCaptureService._logs.append(log_entry)
            
            # Also write to original stream to maintain visibility
            return self.original_stream.write(message)
        
        def flush(self):
            return self.original_stream.flush()
        
        def isatty(self):
            return self.original_stream.isatty() if hasattr(self.original_stream, 'isatty') else False
        
        def __getattr__(self, name):
            """Delegate any other attributes to the original stream"""
            return getattr(self.original_stream, name)
    
    @classmethod
    def start_capture(cls):
        """Start capturing logs"""
        # Capture stdout/stderr
        if cls._original_stdout is None:
            cls._original_stdout = sys.stdout
            cls._original_stderr = sys.stderr
            sys.stdout = cls.LogWriter(sys.stdout)
            sys.stderr = cls.LogWriter(sys.stderr, is_stderr=True)
        
        # Add logging handler to capture logging module logs
        if cls._log_handler is None:
            cls._log_handler = cls.MemoryLogHandler()
            cls._log_handler.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            
            # Add handler to root logger and common loggers
            root_logger = logging.getLogger()
            root_logger.addHandler(cls._log_handler)
            
            # Also add to commonly used loggers
            for logger_name in ['apscheduler', 'esp32OTA', 'flask', 'werkzeug']:
                logging.getLogger(logger_name).addHandler(cls._log_handler)
    
    @classmethod
    def stop_capture(cls):
        """Stop capturing logs"""
        if cls._original_stdout is not None:
            sys.stdout = cls._original_stdout
            sys.stderr = cls._original_stderr
            cls._original_stdout = None
            cls._original_stderr = None
        
        if cls._log_handler is not None:
            root_logger = logging.getLogger()
            root_logger.removeHandler(cls._log_handler)
            
            for logger_name in ['apscheduler', 'esp32OTA', 'flask', 'werkzeug']:
                logging.getLogger(logger_name).removeHandler(cls._log_handler)
            
            cls._log_handler = None
    
    @classmethod
    def get_logs(cls, limit=None, offset=0):
        """Get captured logs"""
        with cls._lock:
            all_logs = list(cls._logs)
        
        if limit:
            return all_logs[offset:offset+limit]
        return all_logs[offset:]
    
    @classmethod
    def clear_logs(cls):
        """Clear all captured logs"""
        with cls._lock:
            cls._logs.clear()
    
    @classmethod
    def add_log(cls, message, level="INFO"):
        """Manually add a log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        with cls._lock:
            cls._logs.append(log_entry)
