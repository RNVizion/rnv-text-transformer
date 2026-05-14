"""
RNV Text Transformer - Utils Package
Utility modules for the application.
"""

from utils.config import (
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    RESOURCES_DIR,
    BUTTON_IMAGES_DIR,
    BACKGROUND_IMAGES_DIR,
    FONTS_DIR,
    ICONS_DIR,
    MAX_FILE_SIZE,
    SUPPORTED_EXTENSIONS,
    FontManager,
)

from utils.logger import (
    Logger,
    LogLevel,
    get_logger,
    get_module_logger,
    info,
    success,
    warning,
    error,
    header,
    separator,
    configure,
)

from utils.dialog_styles import DialogStyleManager

from utils.error_handler import ErrorHandler, ErrorContext

from utils.dialog_helper import DialogHelper

from utils.settings_manager import SettingsManager

from utils.file_handler import FileHandler, FileReadError, FileWriteError

from utils.clipboard_utils import ClipboardUtils

from utils.async_workers import (
    FileLoaderThread,
    TextTransformThread,
    should_use_thread_for_transform,
)


__all__ = [
    # Config
    'APP_NAME',
    'APP_VERSION',
    'BASE_DIR',
    'RESOURCES_DIR',
    'BUTTON_IMAGES_DIR',
    'BACKGROUND_IMAGES_DIR',
    'FONTS_DIR',
    'ICONS_DIR',
    'MAX_FILE_SIZE',
    'SUPPORTED_EXTENSIONS',
    'FontManager',
    # Logger
    'Logger',
    'LogLevel',
    'get_logger',
    'get_module_logger',
    'info',
    'success',
    'warning',
    'error',
    'header',
    'separator',
    'configure',
    # Dialog Styles
    'DialogStyleManager',
    # Error Handler
    'ErrorHandler',
    'ErrorContext',
    # Dialog Helper
    'DialogHelper',
    # Settings
    'SettingsManager',
    # File Handler
    'FileHandler',
    'FileReadError',
    'FileWriteError',
    # Clipboard
    'ClipboardUtils',
    # Async Workers
    'FileLoaderThread',
    'TextTransformThread',
    'should_use_thread_for_transform',
]
