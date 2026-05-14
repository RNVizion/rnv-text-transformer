"""
RNV Text Transformer - Configuration Module
Contains all application constants, paths, and font management

Python 3.13 Optimized:
- Modern type hints (native list, dict, tuple)
- @classmethod for class-level cache access
- Improved path handling with pathlib
- Professional logging via Logger utility
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QByteArray

from utils.logger import get_module_logger

_logger = get_module_logger("FontManager")


# ==================== PATH CONFIGURATION ====================
# Using pathlib for more robust path handling
BASE_DIR: Path = Path(__file__).resolve().parent.parent
RESOURCES_DIR: Path = BASE_DIR / "resources"
BUTTON_IMAGES_DIR: Path = RESOURCES_DIR / "button_images"
BACKGROUND_IMAGES_DIR: Path = RESOURCES_DIR / "background_images"
FONTS_DIR: Path = RESOURCES_DIR / "fonts"
ICONS_DIR: Path = RESOURCES_DIR / "icons"

# ==================== APPLICATION CONSTANTS ====================
APP_NAME: str = "RNV Text Transformer"
APP_VERSION: str = "3.0.3"
DEFAULT_WINDOW_WIDTH: int = 900
DEFAULT_WINDOW_HEIGHT: int = 600
DEFAULT_WINDOW_X: int = 100
DEFAULT_WINDOW_Y: int = 100
MIN_WINDOW_WIDTH: int = 800
MIN_WINDOW_HEIGHT: int = 600

# Button dimensions
BUTTON_MIN_WIDTH: int = 100
BUTTON_MIN_HEIGHT: int = 35
BUTTON_SPACING: int = 10
BUTTON_MARGINS: tuple[int, int, int, int] = (0, 10, 0, 10)

# Text area dimensions
INPUT_TEXT_MIN_HEIGHT: int = 100
INPUT_TEXT_MAX_HEIGHT: int = 150
STATUS_LABEL_MIN_HEIGHT: int = 40

# Theme button dimensions
THEME_BUTTON_WIDTH: int = 90
THEME_BUTTON_HEIGHT: int = 30
THEME_BUTTON_MARGIN: int = 20

# Timer settings
STATUS_CLEAR_TIMEOUT: int = 3000  # 3 seconds
DRAG_TRACK_INTERVAL: int = 33  # ~30fps (sufficient for drag tracking)

# File size limits
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB limit for file loading


# ==================== EMBEDDED FONT DATA ====================
MONT_FONT_BASE64: str = """
<BASE64 FONT STRING HERE>
"""


# ==================== FONT MANAGER ====================
class FontManager:
    """
    Manages custom font loading and fallback.
    
    Uses class-level caching for performance optimization.
    Python 3.13 optimized with proper type hints and ClassVar.
    """
    
    _cached_font: ClassVar[QFont | None] = None
    _font_family: ClassVar[str | None] = None
    
    @classmethod
    def load_embedded_font(cls) -> QFont:
        """
        Load Montserrat-Black font from embedded base64 or file.
        
        Returns:
            QFont: The loaded custom font or Arial fallback
        """
        if cls._cached_font is not None:
            return cls._cached_font
        
        logger = _logger
        
        # Try embedded font first
        if MONT_FONT_BASE64.strip() and "<BASE64 FONT STRING" not in MONT_FONT_BASE64:
            font_id = QFontDatabase.addApplicationFontFromData(
                QByteArray.fromBase64(MONT_FONT_BASE64.encode("utf-8"))
            )
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    if logger:
                        logger.success("Loaded Montserrat-Black", details="embedded")
                    cls._cached_font = QFont(families[0], 10)
                    cls._font_family = families[0]
                    return cls._cached_font
        
        # Try loading from file
        font_path = FONTS_DIR / "Montserrat-Black.ttf"
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    if logger:
                        logger.success("Loaded Montserrat-Black", details="file")
                    cls._cached_font = QFont(families[0], 10)
                    cls._font_family = families[0]
                    return cls._cached_font
        
        # Fallback to Arial
        if logger:
            logger.warning("Using fallback font", details="Arial")
        cls._cached_font = QFont("Arial", 10)
        cls._font_family = "Arial"
        return cls._cached_font
    
    @classmethod
    def get_font_family(cls) -> str:
        """
        Get the loaded font family name.
        
        Returns:
            str: Font family name
        """
        if cls._font_family is None:
            cls.load_embedded_font()
        return cls._font_family or "Arial"
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the font cache (useful for testing)."""
        cls._cached_font = None
        cls._font_family = None


# ==================== SUPPORTED FILE FORMATS ====================
SUPPORTED_FORMATS: dict[str, list[str]] = {
    'text': ['.txt', '.md', '.py', '.js', '.html', '.log'],
    'document': ['.docx', '.pdf', '.rtf'],
    'all': ['.txt', '.md', '.docx', '.pdf', '.rtf', '.py', '.js', '.html', '.log']
}

# Frozenset for O(1) extension lookup
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(SUPPORTED_FORMATS['all'])

FILE_DIALOG_FILTER: str = (
    "All Supported Files (*.txt *.md *.docx *.pdf *.rtf *.py *.js *.html *.log);;"
    "Text Files (*.txt);;"
    "Markdown Files (*.md);;"
    "Word Documents (*.docx);;"
    "PDF Files (*.pdf);;"
    "Rich Text Format (*.rtf);;"
    "Python Files (*.py);;"
    "JavaScript Files (*.js);;"
    "HTML Files (*.html);;"
    "Log Files (*.log);;"
    "All Files (*)"
)

SAVE_FILE_FILTER: str = "Text Files (*.txt);;All Files (*)"