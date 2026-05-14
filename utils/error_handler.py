"""
RNV Text Transformer - Error Handler Module
Centralized exception handling with logging integration.

Python 3.13 Optimized:
- Modern type hints with ParamSpec and TypeVar
- Decorator pattern for clean error handling
- Context manager support
- Integration with Logger utility


Usage Examples:
    # Direct execution with fallback
    result = ErrorHandler.safe_execute(
        lambda: load_file(path),
        "loading file",
        status_callback=self._set_status,
        fallback_value=None
    )
    
    # Method decorator
    @ErrorHandler.safe_method("transforming text")
    def transform_text(self):
        # ... method code - no try/except needed ...
        pass
    
    # Context manager
    with ErrorContext("processing batch", self._set_status):
        process_files()
"""

from __future__ import annotations

import traceback
from typing import Callable, Any, TypeVar, ParamSpec
from functools import wraps

# Type variables for generic typing
T = TypeVar('T')
P = ParamSpec('P')

# Import logger with fallback
try:
    from utils.logger import Logger
    _logger = Logger("ErrorHandler")
    _use_logger = True
except ImportError:
    _use_logger = False
    _logger = None


def _log_error(context: str, error: Exception, show_traceback: bool = True) -> None:
    """Internal logging helper that uses logger if available."""
    if _use_logger and _logger:
        _logger.error(f"Error in {context}", error=error)
        if show_traceback:
            traceback.print_exc()
    else:
        print(f"ERROR: Error in {context}: {error}")
        if show_traceback:
            traceback.print_exc()


def _log_warning(message: str) -> None:
    """Internal warning helper."""
    if _use_logger and _logger:
        _logger.warning(message)
    else:
        print(f"WARNING: {message}")


def _log_info(message: str) -> None:
    """Internal info helper."""
    if _use_logger and _logger:
        _logger.info(message)
    else:
        print(f"INFO: {message}")


class ErrorHandler:
    """
    Centralized error handling with consistent logging and user feedback.
    
    Provides three main patterns:
    1. safe_execute() - Wrap function calls with error handling
    2. @safe_method - Decorator for class methods
    3. ErrorContext - Context manager for code blocks
    """
    
    __slots__ = ()  # Static methods only, no instance attributes
    
    # Global configuration
    SHOW_TRACEBACK: bool = True  # Set to False in production
    LOG_TO_FILE: bool = False    # Enable for debugging
    LOG_FILE_PATH: str = "text_transformer_errors.log"
    
    @staticmethod
    def handle_exception(
        error: Exception,
        context: str,
        status_callback: Callable[[str], None] | None = None,
        show_traceback: bool = True,
        user_message: str | None = None
    ) -> None:
        """
        Handle exception with consistent logging and user feedback.
        
        Args:
            error: The exception that occurred
            context: Description of what was being done (e.g., "loading file")
            status_callback: Optional callback for status updates (e.g., self._set_status)
            show_traceback: Whether to print full traceback to console
            user_message: Custom message for user (auto-generated if None)
        """
        # Console logging
        _log_error(context, error, show_traceback=False)
        
        if show_traceback and ErrorHandler.SHOW_TRACEBACK:
            traceback.print_exc()
        
        # File logging (optional)
        if ErrorHandler.LOG_TO_FILE:
            ErrorHandler._log_to_file(error, context)
        
        # User feedback via status callback
        if status_callback:
            user_msg = user_message or f"{context.capitalize()} failed"
            try:
                status_callback(user_msg)
            except Exception as callback_error:
                _log_warning(f"Status callback failed: {callback_error}")
    
    @staticmethod
    def _log_to_file(error: Exception, context: str) -> None:
        """Log error to file for debugging."""
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            with open(ErrorHandler.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Context: {context}\n")
                f.write(f"Error: {error}\n")
                f.write(f"Traceback:\n")
                traceback.print_exc(file=f)
                f.write(f"{'='*80}\n")
        except Exception as log_error:
            _log_warning(f"Failed to log error to file: {log_error}")
    
    @staticmethod
    def safe_execute(
        func: Callable[[], T],
        context: str,
        status_callback: Callable[[str], None] | None = None,
        fallback_value: T | None = None,
        reraise: bool = False,
        user_message: str | None = None,
        silent: bool = False
    ) -> T | None:
        """
        Execute function with error handling.
        
        Args:
            func: Function to execute (typically a lambda)
            context: Description for error messages (e.g., "loading settings")
            status_callback: Optional status update callback
            fallback_value: Value to return if exception occurs
            reraise: Whether to re-raise exception after handling
            user_message: Custom user message
            silent: If True, don't log errors
        
        Returns:
            Function result or fallback_value if exception occurs
            
        Example:
            content = ErrorHandler.safe_execute(
                lambda: file.read(),
                "reading file",
                self._set_status,
                fallback_value=""
            )
        """
        try:
            return func()
        except Exception as e:
            if not silent:
                ErrorHandler.handle_exception(
                    e, 
                    context, 
                    status_callback,
                    user_message=user_message
                )
            if reraise:
                raise
            return fallback_value
    
    @staticmethod
    def safe_method(
        context: str,
        fallback_value: Any = None,
        user_message: str | None = None
    ) -> Callable[[Callable[P, T]], Callable[P, T | None]]:
        """
        Decorator for safe method execution.
        
        Args:
            context: Description of what method does
            fallback_value: Value to return if exception occurs
            user_message: Custom user message
        
        Returns:
            Decorated function
        
        Example:
            @ErrorHandler.safe_method("saving file", fallback_value=False)
            def save_file(self, path: str) -> bool:
                with open(path, 'w') as f:
                    f.write(self.content)
                return True
        """
        def decorator(func: Callable[P, T]) -> Callable[P, T | None]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
                # Try to find status callback from self (first arg)
                status_callback = None
                if args and hasattr(args[0], '_set_status'):
                    status_callback = args[0]._set_status
                elif args and hasattr(args[0], 'status_updated'):
                    status_callback = args[0].status_updated.emit
                
                return ErrorHandler.safe_execute(
                    lambda: func(*args, **kwargs),
                    context,
                    status_callback,
                    fallback_value,
                    user_message=user_message
                )
            return wrapper
        return decorator
    
    @staticmethod
    def try_or_default(
        func: Callable[[], T],
        default: T,
        log_error: bool = False
    ) -> T:
        """
        Simple try/except wrapper returning default on any error.
        
        Args:
            func: Function to execute
            default: Default value on error
            log_error: Whether to log the error
            
        Returns:
            Function result or default
            
        Example:
            value = ErrorHandler.try_or_default(
                lambda: int(text),
                default=0
            )
        """
        try:
            return func()
        except Exception as e:
            if log_error:
                _log_warning(f"Using default value due to: {e}")
            return default


class ErrorContext:
    """
    Context manager for error handling in code blocks.
    
    Usage:
        with ErrorContext("processing batch", self._set_status):
            for file in files:
                process(file)
        
        # Check if error occurred:
        with ErrorContext("loading config") as ctx:
            config = load_config()
        if ctx.error:
            use_defaults()
    """
    
    __slots__ = (
        'context', 'status_callback', 'reraise',
        'user_message', 'error', 'success'
    )
    
    def __init__(
        self,
        context: str,
        status_callback: Callable[[str], None] | None = None,
        reraise: bool = False,
        user_message: str | None = None
    ) -> None:
        """
        Initialize error context.
        
        Args:
            context: Description for error messages
            status_callback: Optional status update callback
            reraise: Whether to re-raise exceptions
            user_message: Custom user message
        """
        self.context = context
        self.status_callback = status_callback
        self.reraise = reraise
        self.user_message = user_message
        self.error: Exception | None = None
        self.success: bool = True
    
    def __enter__(self) -> 'ErrorContext':
        """Enter the context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context, handling any exception.
        
        Returns:
            True to suppress exception, False to propagate
        """
        if exc_type is not None:
            self.error = exc_val
            self.success = False
            
            ErrorHandler.handle_exception(
                exc_val,
                self.context,
                self.status_callback,
                user_message=self.user_message
            )
            return not self.reraise  # Suppress if not reraising
        return False


# ==================== FILE-SPECIFIC HELPERS ====================

def safe_file_operation(
    func: Callable[[], T],
    filepath: str,
    operation: str = "file operation"
) -> T | None:
    """
    Safely execute file operations with helpful error messages.
    
    Args:
        func: File operation to execute
        filepath: Path to file (for error messages)
        operation: Description (e.g., "reading", "writing")
    
    Returns:
        Function result or None on error
        
    Example:
        content = safe_file_operation(
            lambda: Path(filepath).read_text(),
            filepath,
            "reading"
        )
    """
    try:
        return func()
    except FileNotFoundError:
        _log_warning(f"File not found: {filepath}")
        return None
    except PermissionError:
        _log_warning(f"Permission denied: {filepath}")
        return None
    except UnicodeDecodeError as e:
        _log_warning(f"Encoding error in file {filepath}: {e}")
        return None
    except Exception as e:
        _log_error(f"{operation} file {filepath}", e)
        return None


def safe_text_operation(
    func: Callable[[], str],
    context: str = "text operation"
) -> str:
    """
    Safely execute text operations, returning empty string on error.
    
    Args:
        func: Text operation to execute
        context: Description for error messages
    
    Returns:
        Function result or empty string on error
        
    Example:
        result = safe_text_operation(
            lambda: text.upper(),
            "converting to uppercase"
        )
    """
    try:
        return func()
    except Exception as e:
        _log_error(context, e, show_traceback=False)
        return ""


# ==================== CONVENIENCE FUNCTION ====================

def safe_call(
    func: Callable[[], T],
    context: str = "operation",
    default: T | None = None
) -> T | None:
    """
    Quick wrapper for safe function execution.
    
    Args:
        func: Function to execute
        context: Operation description for logging
        default: Default value on error
        
    Returns:
        Function result or default value
        
    Example:
        result = safe_call(lambda: parse_data(raw), "parsing data", default={})
    """
    return ErrorHandler.safe_execute(func, context, fallback_value=default)