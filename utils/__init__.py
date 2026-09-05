"""
RNV Text Transformer - Utils Package
Utility modules for the application.
"""

from utils.colors import (
    TRUE_BLACK,
    WHITE,
    BRAND_BLACK,
    APP_CARD,
    APP_BORDER,
    APP_TEXT,
    APP_TEXT_DIM,
    STATUS_SUCCESS,
    STATUS_WARNING,
    STATUS_ERROR,
    STATUS_SUCCESS_TEXT,
    STATUS_WARNING_TEXT,
    STATUS_ERROR_TEXT,
    STATUS_SUCCESS_TEXT_LIGHT,
    STATUS_WARNING_TEXT_LIGHT,
    STATUS_ERROR_TEXT_LIGHT,
    BRAND_GOLD_HOVER,
    BRAND_GOLD_PRESSED,
    GREY_44,
    GREY_55,
    GREY_60,
    GREY_66,
    GREY_88,
    GREY_CC,
    GREY_DD,
    GREY_E0,
    GREY_EE,
    APP_PANEL_HOVER,
    APP_HOVER_LIGHT,
    GOLD_TEXT_GROUND_FLOOR,
    GREY_F5,
    SEMANTIC_DIFF_ADDED,
    SEMANTIC_DIFF_REMOVED,
    SEMANTIC_DIFF_CHANGED,
    SEMANTIC_DIFF_CURRENT,
    SEMANTIC_DIFF_ADDED_LIGHT,
    SEMANTIC_DIFF_REMOVED_LIGHT,
    SEMANTIC_DIFF_CHANGED_LIGHT,
    SEMANTIC_DIFF_CURRENT_LIGHT,
    SEMANTIC_REGEX_MATCH,
    SEMANTIC_REGEX_MATCH_LIGHT,
    SEMANTIC_REGEX_GROUPS,
    BRAND_GOLD,
    BRAND_DARK_GOLD,
    BRAND_DARK_GOLD_DEEP,
    BRAND_DARK_GOLD_PRESSED,
    lighten,
    with_alpha,
)

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
    # Brand Colors
    'TRUE_BLACK',
    'WHITE',
    'BRAND_BLACK',
    'APP_CARD',
    'APP_BORDER',
    'APP_TEXT',
    'APP_TEXT_DIM',
    'STATUS_SUCCESS',
    'STATUS_WARNING',
    'STATUS_ERROR',
    'STATUS_SUCCESS_TEXT',
    'STATUS_WARNING_TEXT',
    'STATUS_ERROR_TEXT',
    'STATUS_SUCCESS_TEXT_LIGHT',
    'STATUS_WARNING_TEXT_LIGHT',
    'STATUS_ERROR_TEXT_LIGHT',
    'BRAND_GOLD_HOVER',
    'BRAND_GOLD_PRESSED',
    'GREY_44',
    'GREY_55',
    'GREY_60',
    'GREY_66',
    'GREY_88',
    'GREY_CC',
    'GREY_DD',
    'GREY_E0',
    'GREY_EE',
    'APP_PANEL_HOVER',
    'APP_HOVER_LIGHT',
    'GOLD_TEXT_GROUND_FLOOR',
    'GREY_F5',
    'SEMANTIC_DIFF_ADDED',
    'SEMANTIC_DIFF_REMOVED',
    'SEMANTIC_DIFF_CHANGED',
    'SEMANTIC_DIFF_CURRENT',
    'SEMANTIC_DIFF_ADDED_LIGHT',
    'SEMANTIC_DIFF_REMOVED_LIGHT',
    'SEMANTIC_DIFF_CHANGED_LIGHT',
    'SEMANTIC_DIFF_CURRENT_LIGHT',
    'SEMANTIC_REGEX_MATCH',
    'SEMANTIC_REGEX_MATCH_LIGHT',
    'SEMANTIC_REGEX_GROUPS',
    'BRAND_GOLD',
    'BRAND_DARK_GOLD',
    'BRAND_DARK_GOLD_DEEP',
    'BRAND_DARK_GOLD_PRESSED',
    'lighten',
    'with_alpha',
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
