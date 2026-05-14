"""
RNV Text Transformer - Theme Manager Module
Handles Dark Mode, Light Mode, and Image Mode theming

Python 3.13 Optimized:
- Modern type hints with TypedDict for theme structure
- Match statement for theme cycling
- Pillow 10.x compatibility (Image.Resampling)
- ClassVar for theme dictionaries
- Professional logging via Logger utility

- DialogStyleManager is the single source of truth for all colors
- ThemeManager.colors property provides unified access
- Removed DARK_THEME/LIGHT_THEME dicts and get_current_theme() (migrated to .colors)
- Removed ThemeColors TypedDict (no longer needed)
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import ClassVar

from PyQt6.QtGui import QPixmap
from PIL import Image

from utils.config import BUTTON_IMAGES_DIR, BACKGROUND_IMAGES_DIR
from utils.logger import get_module_logger

_logger = get_module_logger("ThemeManager")


class ThemeManager:
    """
    Manages application themes with Dark Mode, Light Mode, and Image Mode.
    
    Python 3.13 optimized with proper type hints and modern Pillow API.
    Color definitions are centralized in DialogStyleManager — access via self.colors.
    """
    
    # Button names for image mode detection
    _BUTTON_NAMES: ClassVar[tuple[str, ...]] = ('transform', 'copy', 'load', 'save')
    
    # Maximum background image dimension (4K)
    _MAX_DIMENSION: ClassVar[int] = 3840
    
    __slots__ = ('current_theme', 'image_mode_available', 'image_mode_active', 'background_pixmap')
    
    def __init__(self) -> None:
        """Initialize theme manager with default dark theme."""
        self.current_theme: str = 'dark'
        self.image_mode_available: bool = False
        self.image_mode_active: bool = False
        self.background_pixmap: QPixmap | None = None
    
    def detect_image_resources(self) -> bool:
        """
        Check if custom images are available for Image Mode.
        
        Loads and caches background image with automatic resizing.
        Uses Pillow 10.x compatible resampling.
        
        Returns:
            True if image mode is available
        """
        bg_path = BACKGROUND_IMAGES_DIR / "background.png"
        logger = _logger
        
        # Load and cache background pixmap with resizing
        has_background = self._load_background_image(bg_path)
        
        # Check for button images
        button_count = sum(
            1 for name in self._BUTTON_NAMES
            if (BUTTON_IMAGES_DIR / f"{name}_base.png").exists()
        )
        
        self.image_mode_available = has_background or button_count >= 2
        
        if self.image_mode_available:
            self.image_mode_active = True
            self.current_theme = 'image'
            if logger:
                logger.success(
                    "Image Mode available",
                    details=f"background: {has_background}, buttons: {button_count}/4"
                )
        
        return self.image_mode_available
    
    def _load_background_image(self, bg_path: Path) -> bool:
        """
        Load and cache background image with automatic resizing.
        
        Args:
            bg_path: Path to background image
            
        Returns:
            True if successfully loaded
        """
        if not bg_path.exists():
            return False
        
        logger = _logger
        
        try:
            # Load with PIL and resize if needed
            with Image.open(bg_path) as img:
                # Resize if image is too large (over 4K resolution)
                if img.width > self._MAX_DIMENSION or img.height > self._MAX_DIMENSION:
                    ratio = min(
                        self._MAX_DIMENSION / img.width,
                        self._MAX_DIMENSION / img.height
                    )
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    # Use Image.Resampling.LANCZOS (Pillow 10.x compatible)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    if logger:
                        logger.info(
                            "Resized background image",
                            details=f"{new_size[0]}x{new_size[1]}"
                        )
                
                # Convert to QPixmap via bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                self.background_pixmap = QPixmap()
                if self.background_pixmap.loadFromData(buffer.getvalue()):
                    if logger:
                        logger.success(
                            "Loaded background image",
                            details=f"{img.width}x{img.height}"
                        )
                    return True
                else:
                    self.background_pixmap = None
                    if logger:
                        logger.error("Failed to load background image into QPixmap")
                    return False
                    
        except Exception as e:
            if logger:
                logger.error("Error loading background image", error=e)
            self.background_pixmap = None
            return False
    
    def cycle_theme(self) -> str:
        """
        Cycle through available themes.
        
        Uses match statement for cleaner state transitions.
        
        Returns:
            Name of new theme
        """
        if self.image_mode_available:
            match self.current_theme:
                case 'image':
                    self.current_theme = 'dark'
                    self.image_mode_active = False
                case 'dark':
                    self.current_theme = 'light'
                case 'light' | _:
                    self.current_theme = 'image'
                    self.image_mode_active = True
        else:
            # Only toggle between dark and light if no image mode
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        
        return self.current_theme
    
    def get_theme_display_name(self) -> str:
        """
        Get display name for current theme.
        
        Returns:
            Human-readable theme name
        """
        match self.current_theme:
            case 'image':
                return "Image Mode"
            case 'dark':
                return "Dark Mode"
            case 'light':
                return "Light Mode"
            case _:
                return "Unknown Mode"
    
    @property
    def is_dark_mode(self) -> bool:
        """
        Check if current theme uses dark colors (dark or image mode).
        
        Returns:
            True if dark or image theme is active
        """
        return self.current_theme in ('dark', 'image')
    
    @property
    def colors(self) -> dict[str, str]:
        """
        Get current theme colors from the centralized DialogStyleManager.
        
        This is the preferred way to access theme colors. Returns the full
        color dictionary including both dialog-specific and MainWindow-specific
        keys (window_bg, button_bg, input_bg, output_text_color, etc.).
        
        Returns:
            Immutable color dictionary — do not modify.
        """
        from utils.dialog_styles import DialogStyleManager
        return DialogStyleManager.get_colors(self.is_dark_mode)
    
    def is_image_mode(self) -> bool:
        """
        Check if image mode is active.
        
        Returns:
            True if in image mode
        """
        return self.image_mode_active
    
    def get_background_pixmap(self) -> QPixmap | None:
        """
        Get cached background pixmap.
        
        Returns:
            Background QPixmap or None
        """
        return self.background_pixmap
    
    def set_theme(self, theme: str) -> bool:
        """
        Directly set theme by name.
        
        Args:
            theme: 'dark', 'light', or 'image'
            
        Returns:
            True if theme was set successfully
        """
        if theme == 'image' and not self.image_mode_available:
            return False
        
        if theme in ('dark', 'light', 'image'):
            self.current_theme = theme
            self.image_mode_active = (theme == 'image')
            return True
        
        return False