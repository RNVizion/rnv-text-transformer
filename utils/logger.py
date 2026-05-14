"""
RNV Text Transformer - Professional Logger Module
Provides clean, structured, color-coded console output.

Python 3.13 Optimized:
- Modern type hints with ClassVar
- Enum-based log levels
- Windows terminal color support
- Optional file logging

Usage:
    from utils.logger import Logger, get_logger
    
    # Option 1: Create module-specific logger
    logger = Logger("ModuleName")
    logger.info("Starting operation...")
    logger.success("Operation complete!")
    logger.warning("Something might be wrong")
    logger.error("Operation failed", error=exception)
    
    # Option 2: Use convenience functions
    from utils.logger import info, success, warning, error, header, separator
    info("Starting...")
    success("Done!")
"""

from __future__ import annotations

import sys
import os
from enum import Enum
from typing import Any, ClassVar
from datetime import datetime


class LogLevel(Enum):
    """Log level enumeration with priority values."""
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class ColorCodes:
    """ANSI color codes for console output."""
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Styles
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'


class Logger:
    """
    Professional logger for RNV Text Transformer with structured, color-coded output.
    
    Features:
    - Color-coded output by log level
    - Clean, structured formatting
    - Optional file logging
    - Module identification
    - Proper Unicode symbol handling
    - Windows terminal support
    """
    
    # Class-level configuration
    ENABLE_COLORS: ClassVar[bool] = True
    ENABLE_FILE_LOGGING: ClassVar[bool] = False
    LOG_FILE_PATH: ClassVar[str] = "text_transformer.log"
    MIN_LEVEL: ClassVar[LogLevel] = LogLevel.DEBUG
    SHOW_TIMESTAMP: ClassVar[bool] = False
    SHOW_MODULE: ClassVar[bool] = True
    
    # Level configuration - using Windows-compatible ASCII symbols
    LEVEL_CONFIG: ClassVar[dict[LogLevel, dict[str, Any]]] = {
        LogLevel.DEBUG: {
            'label': 'DEBUG',
            'color': ColorCodes.BRIGHT_BLACK,
            'symbol': '.'
        },
        LogLevel.INFO: {
            'label': 'INFO',
            'color': ColorCodes.CYAN,
            'symbol': '>'
        },
        LogLevel.SUCCESS: {
            'label': 'SUCCESS',
            'color': ColorCodes.GREEN,
            'symbol': '+'
        },
        LogLevel.WARNING: {
            'label': 'WARNING',
            'color': ColorCodes.YELLOW,
            'symbol': '!'
        },
        LogLevel.ERROR: {
            'label': 'ERROR',
            'color': ColorCodes.RED,
            'symbol': 'X'
        },
        LogLevel.CRITICAL: {
            'label': 'CRITICAL',
            'color': ColorCodes.BRIGHT_RED,
            'symbol': 'X'
        }
    }
    
    __slots__ = ('name', 'min_level', '_use_colors')
    
    def __init__(self, name: str, min_level: LogLevel | None = None) -> None:
        """
        Initialize logger.
        
        Args:
            name: Logger name (usually module name)
            min_level: Minimum log level to display (default: DEBUG)
        """
        self.name = name
        self.min_level = min_level or Logger.MIN_LEVEL
        self._use_colors = self._check_color_support()
    
    def _check_color_support(self) -> bool:
        """Check if terminal supports colors."""
        if not Logger.ENABLE_COLORS:
            return False
        
        # Check if stdout is a tty
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check for Windows
        if os.name == 'nt':
            # Enable ANSI colors on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                # Check for Windows Terminal or other compatible terminals
                return os.environ.get('TERM_PROGRAM') in ['vscode', 'Windows Terminal'] or \
                       os.environ.get('WT_SESSION') is not None
        
        return True
    
    def _format_message(
        self, 
        level: LogLevel, 
        message: str, 
        details: str | None = None
    ) -> str:
        """Format a log message with proper structure."""
        config = self.LEVEL_CONFIG[level]
        parts: list[str] = []
        
        # Timestamp (optional)
        if Logger.SHOW_TIMESTAMP:
            timestamp = datetime.now().strftime("%H:%M:%S")
            parts.append(f"[{timestamp}]")
        
        # Level label with color
        label = config['label'].ljust(8)
        if self._use_colors:
            parts.append(f"{config['color']}{label}{ColorCodes.RESET}")
        else:
            parts.append(label)
        
        # Module name
        if Logger.SHOW_MODULE:
            parts.append(f"| {self.name.ljust(20)}")
        
        # Symbol and message
        symbol = config['symbol']
        if level in (LogLevel.SUCCESS, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL):
            full_message = f"| {symbol} {message}"
        else:
            full_message = f"| {message}"
        
        # Add color to message if enabled
        if self._use_colors and level in (LogLevel.ERROR, LogLevel.CRITICAL, 
                                           LogLevel.SUCCESS, LogLevel.WARNING):
            full_message = f"{config['color']}{full_message}{ColorCodes.RESET}"
        
        parts.append(full_message)
        
        # Add details on same line or new line
        if details:
            if len(details) < 40:
                parts.append(f" ({details})")
            else:
                parts.append(f"\n{'':8} | {'':20} | {details}")
        
        return ' '.join(parts)
    
    def _log(
        self, 
        level: LogLevel, 
        message: str, 
        details: str | None = None, 
        error: Exception | None = None, 
        **kwargs: Any
    ) -> None:
        """Internal logging method."""
        # Check level threshold
        if level.value < self.min_level.value:
            return
        
        # Add exception info to details if provided
        if error is not None:
            error_details = f"{type(error).__name__}: {error}"
            if details:
                details = f"{details} - {error_details}"
            else:
                details = error_details
        
        # Format and print
        formatted = self._format_message(level, message, details)
        
        try:
            print(formatted, flush=True)
        except UnicodeEncodeError:
            # Fallback for terminals that don't support Unicode
            safe_formatted = formatted.encode('ascii', 'replace').decode('ascii')
            print(safe_formatted, flush=True)
        
        # File logging
        if Logger.ENABLE_FILE_LOGGING:
            self._log_to_file(level, message, details)
    
    def _log_to_file(
        self, 
        level: LogLevel, 
        message: str, 
        details: str | None = None
    ) -> None:
        """Log to file (no colors)."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config = self.LEVEL_CONFIG[level]
            
            log_line = f"[{timestamp}] {config['label'].ljust(8)} | {self.name.ljust(20)} | {message}"
            if details:
                log_line += f" ({details})"
            
            with open(Logger.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception:
            pass  # Silently fail file logging
    
    # Public logging methods
    def debug(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, details, **kwargs)
    
    def info(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, details, **kwargs)
    
    def success(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """Log success message."""
        self._log(LogLevel.SUCCESS, message, details, **kwargs)
    
    def warning(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, details, **kwargs)
    
    def error(
        self, 
        message: str, 
        error: Exception | None = None, 
        details: str | None = None, 
        **kwargs: Any
    ) -> None:
        """Log error message with optional exception."""
        self._log(LogLevel.ERROR, message, details, error=error, **kwargs)
    
    def critical(
        self, 
        message: str, 
        error: Exception | None = None,
        details: str | None = None, 
        **kwargs: Any
    ) -> None:
        """Log critical error message."""
        self._log(LogLevel.CRITICAL, message, details, error=error, **kwargs)
    
    def separator(self, char: str = "=", length: int = 60) -> None:
        """Print a separator line."""
        line = char * length
        if self._use_colors:
            print(f"{ColorCodes.DIM}{line}{ColorCodes.RESET}")
        else:
            print(line)
    
    def header(self, message: str, char: str = "=", length: int = 60) -> None:
        """Print a header with separators."""
        self.separator(char, length)
        
        # Center the message
        padding = (length - len(message) - 2) // 2
        centered = f"{char * padding} {message} {char * padding}"
        if len(centered) < length:
            centered += char
        
        if self._use_colors:
            print(f"{ColorCodes.BOLD}{ColorCodes.CYAN}{centered}{ColorCodes.RESET}")
        else:
            print(centered)
        
        self.separator(char, length)
    
    def blank(self) -> None:
        """Print a blank line."""
        print()
    
    def indent(self, message: str, level: int = 1) -> None:
        """Print an indented info message."""
        indent_str = "  " * level
        print(f"{'':8} | {'':20} | {indent_str}{message}")


# Global logger registry
_loggers: dict[str, Logger] = {}


def get_logger(name: str) -> Logger:
    """Get or create a logger by name."""
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]


def get_module_logger(name: str) -> Logger | None:
    """
    Get a logger instance with graceful fallback.
    
    This is the recommended way to get a logger in modules that may
    be imported before logging is fully configured.
    
    Args:
        name: Logger name (typically module or class name)
    
    Returns:
        Logger instance or None if unavailable
    
    Example:
        from utils.logger import get_module_logger
        _logger = get_module_logger("MyModule")
        
        # Safe logging (checks for None)
        if _logger:
            _logger.info("Message")
    """
    try:
        return get_logger(name)
    except Exception:
        return None


# Default logger for quick access
_default_logger: Logger = Logger("TextTransformer")


# Convenience functions using default logger
def debug(message: str, details: str | None = None, **kwargs: Any) -> None:
    """Quick debug log."""
    _default_logger.debug(message, details, **kwargs)


def info(message: str, details: str | None = None, **kwargs: Any) -> None:
    """Quick info log."""
    _default_logger.info(message, details, **kwargs)


def success(message: str, details: str | None = None, **kwargs: Any) -> None:
    """Quick success log."""
    _default_logger.success(message, details, **kwargs)


def warning(message: str, details: str | None = None, **kwargs: Any) -> None:
    """Quick warning log."""
    _default_logger.warning(message, details, **kwargs)


def error(
    message: str, 
    error: Exception | None = None, 
    details: str | None = None, 
    **kwargs: Any
) -> None:
    """Quick error log."""
    _default_logger.error(message, error=error, details=details, **kwargs)


def critical(
    message: str, 
    error: Exception | None = None,
    details: str | None = None, 
    **kwargs: Any
) -> None:
    """Quick critical log."""
    _default_logger.critical(message, error=error, details=details, **kwargs)


def separator(char: str = "=", length: int = 60) -> None:
    """Quick separator."""
    _default_logger.separator(char, length)


def header(message: str, char: str = "=", length: int = 60) -> None:
    """Quick header."""
    _default_logger.header(message, char, length)


def blank() -> None:
    """Quick blank line."""
    _default_logger.blank()


def configure(
    enable_colors: bool = True,
    enable_file_logging: bool = False,
    log_file_path: str = "text_transformer.log",
    min_level: LogLevel = LogLevel.DEBUG,
    show_timestamp: bool = False,
    show_module: bool = True
) -> None:
    """
    Configure global logger settings.
    
    Args:
        enable_colors: Enable colored output
        enable_file_logging: Enable logging to file
        log_file_path: Path to log file
        min_level: Minimum log level to display
        show_timestamp: Show timestamp in output
        show_module: Show module name in output
    """
    Logger.ENABLE_COLORS = enable_colors
    Logger.ENABLE_FILE_LOGGING = enable_file_logging
    Logger.LOG_FILE_PATH = log_file_path
    Logger.MIN_LEVEL = min_level
    Logger.SHOW_TIMESTAMP = show_timestamp
    Logger.SHOW_MODULE = show_module