"""
RNV Text Transformer - Image Button Module
Custom QPushButton with base/hover/pressed image states

Python 3.13 Optimized:
- Modern type hints with TYPE_CHECKING
- Match statements for state handling
- Improved slot usage
- Better event handling
- LRU-style cache with size limit

- Fixed font family initialization for text modes
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, ClassVar

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QCursor, QPixmap, QEnterEvent, QFont, QFontMetrics

from core.resource_loader import ResourceLoader
from utils.config import DRAG_TRACK_INTERVAL

if TYPE_CHECKING:
    from PyQt6.QtGui import QResizeEvent
    from core.theme_manager import ThemeManager


class ImageButton(QPushButton):
    """
    Button with custom base/hover/pressed image states.
    
    Optimized for performance with pixmap caching and LRU-style eviction.
    """
    
    # Maximum cached scaled pixmaps per button (3 states × 3 recent sizes)
    _MAX_SCALED_CACHE_SIZE: ClassVar[int] = 9
    
    __slots__ = (
        'button_name', 'label_text', 'base_pixmap', 'hover_pixmap',
        'pressed_pixmap', 'scaled_cache', 'theme_manager',
        'is_pressed_state', 'is_hover_state', 'drag_track_timer',
        '_cached_font_family', '_force_image_mode'
    )
    
    def __init__(
        self,
        button_name: str,
        label_text: str,
        command: Callable[[], None] | None = None,
        parent: QPushButton | None = None
    ) -> None:
        """
        Initialize ImageButton.
        
        Args:
            button_name: Name of button for loading images
            label_text: Text to display in text mode
            command: Function to call on click
            parent: Parent widget
        """
        super().__init__(parent)
        self.button_name = button_name
        self.label_text = label_text

        # Load all three states (uses ResourceLoader cache)
        self.base_pixmap: QPixmap | None = ResourceLoader.load_button_image(button_name, 'base')
        self.hover_pixmap: QPixmap | None = ResourceLoader.load_button_image(button_name, 'hover')
        self.pressed_pixmap: QPixmap | None = ResourceLoader.load_button_image(button_name, 'pressed')

        # Cache for scaled pixmaps to avoid redundant scaling
        self.scaled_cache: dict[str, QPixmap] = {}
        
        # Cache for font family (avoid repeated lookups)
        self._cached_font_family: str | None = None

        self.theme_manager: ThemeManager | None = None
        self.is_pressed_state: bool = False
        self.is_hover_state: bool = False
        self._force_image_mode: bool = False  # When True, always show images regardless of theme

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(label_text)

        if command is not None:
            self.clicked.connect(command)

        self.pressed.connect(self._on_press)
        self.released.connect(self._on_release)

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
        # Timer to track mouse position during drag
        self.drag_track_timer = QTimer(self)
        self.drag_track_timer.timeout.connect(self._check_mouse_position)
        self.drag_track_timer.setInterval(DRAG_TRACK_INTERVAL)
    
    def _check_mouse_position(self) -> None:
        """Check if mouse is over button while pressed (for drag tracking)."""
        if not self.is_pressed_state:
            return
    
        # Get global cursor position and convert to local
        global_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(global_pos)
    
        # Check if inside button
        is_inside = self.rect().contains(local_pos)
    
        if is_inside != self.is_hover_state:
            self.is_hover_state = is_inside
            self._update_button_state('pressed' if is_inside else 'base')

    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """
        Set theme manager for this button.
        
        Args:
            theme_manager: ThemeManager instance
        """
        self.theme_manager = theme_manager
        self.apply_style()
    
    def set_font_family(self, font_family: str) -> None:
        """
        Explicitly set the font family for this button.
        
        This ensures correct font is used even before window hierarchy is established.
        
        Args:
            font_family: Font family name to use
        """
        self._cached_font_family = font_family
    
    def set_force_image_mode(self, force: bool = True) -> None:
        """
        Set whether to always show images regardless of theme mode.
        
        Useful for buttons like Settings that should always show their icon.
        
        Args:
            force: If True, always show images; if False, follow theme mode
        """
        self._force_image_mode = force
        self.apply_style()
    
    def clear_scaled_cache(self) -> None:
        """Clear the scaled pixmap cache (called on resize or theme change)."""
        self.scaled_cache.clear()
    
    def clear_font_cache(self) -> None:
        """Clear the font family cache to force fresh lookup."""
        self._cached_font_family = None
    
    def _get_scaled_pixmap(self, pixmap: QPixmap, state: str) -> QPixmap | None:
        """
        Get scaled pixmap from cache or create and cache it.
        
        Uses LRU-style eviction when cache exceeds maximum size.
        
        Args:
            pixmap: QPixmap to scale
            state: Current button state
        
        Returns:
            Scaled pixmap or None
        """
        if pixmap.isNull():
            return None
        
        # Create cache key based on size and state
        size = self.size()
        cache_key = f"{state}_{size.width()}_{size.height()}"
        
        # Return cached version if available (move to end for LRU)
        if cache_key in self.scaled_cache:
            # Move to end (most recently used)
            value = self.scaled_cache.pop(cache_key)
            self.scaled_cache[cache_key] = value
            return value
        
        # Evict oldest entries if cache is full (LRU eviction)
        while len(self.scaled_cache) >= self._MAX_SCALED_CACHE_SIZE:
            oldest_key = next(iter(self.scaled_cache))
            del self.scaled_cache[oldest_key]
        
        # Scale and cache
        scaled = pixmap.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.scaled_cache[cache_key] = scaled
        return scaled

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter (hover)."""
        super().enterEvent(event)
        if self._is_in_image_mode() and not self.is_pressed_state:
            self.is_hover_state = True
            self._update_button_state('hover')

    def leaveEvent(self, event) -> None:
        """Handle mouse leave."""
        super().leaveEvent(event)
        if self._is_in_image_mode() and not self.is_pressed_state:
            self.is_hover_state = False
            self._update_button_state('base')

    def _on_press(self) -> None:
        """Handle press event."""
        self.is_pressed_state = True
        if self._is_in_image_mode():
            self.drag_track_timer.start()
            self._update_button_state('pressed')
        else:
            self._update_text_mode_pressed(True)

    def _on_release(self) -> None:
        """Handle release event."""
        self.is_pressed_state = False
        if self._is_in_image_mode():
            self.drag_track_timer.stop()
    
            # Check final position
            global_pos = QCursor.pos()
            local_pos = self.mapFromGlobal(global_pos)
            is_inside = self.rect().contains(local_pos)
    
            self.is_hover_state = is_inside
            self._update_button_state('hover' if is_inside else 'base')
        else:
            self._update_text_mode_pressed(False)
    
    def _is_in_image_mode(self) -> bool:
        """Check if currently in image mode or force image mode is enabled."""
        if self._force_image_mode and self.base_pixmap is not None and not self.base_pixmap.isNull():
            return True
        return self.theme_manager is not None and self.theme_manager.is_image_mode()
    
    def _update_button_state(self, state: str) -> None:
        """
        Update button to show specified state (base, hover, pressed).
        
        Args:
            state: 'base', 'hover', or 'pressed'
        """
        if not self._is_in_image_mode():
            return
        
        # Select the appropriate pixmap using match statement
        match state:
            case 'base':
                pixmap = self.base_pixmap
            case 'hover':
                pixmap = self.hover_pixmap or self.base_pixmap
            case 'pressed':
                pixmap = self.pressed_pixmap or self.base_pixmap
            case _:
                pixmap = self.base_pixmap
        
        if pixmap is not None and not pixmap.isNull():
            scaled_pixmap = self._get_scaled_pixmap(pixmap, state)
            if scaled_pixmap is not None:
                self.setIcon(QIcon(scaled_pixmap))
                self.setIconSize(self.size())
    
    def _update_text_mode_pressed(self, is_pressed: bool) -> None:
        """
        Update text color for pressed state in text mode.
        
        Args:
            is_pressed: Whether button is pressed
        """
        if self._is_in_image_mode() or self.theme_manager is None:
            return
        
        theme = self.theme_manager.colors
        
        text_color = theme['button_pressed_text'] if is_pressed else theme['button_text']
        stylesheet = self._build_text_mode_stylesheet(text_color)
        if stylesheet:
            self.setStyleSheet(stylesheet)
    
    def _build_text_mode_stylesheet(
        self, 
        text_color: str | None = None,
        use_minimum_height: bool = False
    ) -> str:
        """
        Build stylesheet for text mode buttons.
        
        Args:
            text_color: Override text color (for pressed state)
            use_minimum_height: Use minimum height for font calculation (for initial styling)
            
        Returns:
            Complete stylesheet string or empty string if theme unavailable
        """
        if self.theme_manager is None:
            return ""
        
        theme = self.theme_manager.colors
        font_family = self._get_font_family()
        
        # Calculate font size based on button height
        if use_minimum_height:
            button_height = max(self.height(), self.minimumHeight())
        else:
            button_height = self.height()
        
        if button_height <= 0:
            font_size = 10
        else:
            # Primary: natural size from button height (original behaviour)
            font_size = max(8, int(button_height * 0.28))
            
            # Secondary: only reduce if the text would actually clip at this size.
            # Use QFontMetrics to measure the real rendered text width — no magic
            # constants, no premature reduction. Kicks in only when needed.
            button_width = self.width() if self.width() > 0 else self.minimumWidth()
            available_w = button_width - 32  # 16px padding each side
            if available_w > 0:
                ref_font = QFont(font_family)
                ref_font.setBold(True)
                ref_font.setPointSize(font_size)
                text_w = QFontMetrics(ref_font).horizontalAdvance(self.label_text)
                if text_w > available_w:
                    # Text clips at natural size — scale down just enough to fit
                    ref_font.setPointSize(12)
                    text_w_at_12 = QFontMetrics(ref_font).horizontalAdvance(self.label_text)
                    if text_w_at_12 > 0:
                        font_size = max(8, int(12 * available_w / text_w_at_12))
        
        color = text_color or theme['button_text']
        
        return f"""
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {color};
                border: 1px solid {theme['border_color']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: '{font_family}';
                font-size: {font_size}pt;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
            }}
        """
    
    def _get_font_family(self) -> str:
        """
        Get font family from parent window or default.
        
        Uses caching to avoid repeated lookups on resize events.
        Only caches if we successfully get the font from parent window.
        """
        # Return cached value if we have a valid one
        if self._cached_font_family is not None:
            return self._cached_font_family
        
        # Try to get font from parent window
        parent_window = self.window()
        if parent_window is not None and hasattr(parent_window, 'font_family'):
            font_family = parent_window.font_family
            if font_family:
                # Cache only if we got a valid font from parent
                self._cached_font_family = font_family
                return font_family
        
        # Return fallback without caching - allows retry on next call
        return 'Arial'
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize to update icon size."""
        super().resizeEvent(event)
        
        # Clear cache on resize since sizes changed
        self.clear_scaled_cache()
        
        if self._is_in_image_mode():
            # Determine current state and update
            state = 'base'
            if self.is_pressed_state:
                state = 'pressed'
            elif self.is_hover_state:
                state = 'hover'
            self._update_button_state(state)
        else:
            self.update_text_font_size()
    
    def update_text_font_size(self) -> None:
        """Update font size based on button height for text mode."""
        if self._is_in_image_mode() or self.theme_manager is None:
            return
        
        stylesheet = self._build_text_mode_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
    
    def apply_style(self) -> None:
        """Apply theme-based styling."""
        if self.theme_manager is None:
            return
        
        # Only set size constraints if not in force_image_mode (which uses fixed size)
        if not self._force_image_mode:
            self.setMinimumSize(100, 35)
            self.setMaximumSize(16777215, 16777215)
        
        if self._is_in_image_mode() and self.base_pixmap is not None and not self.base_pixmap.isNull():
            # Image mode styling - include disabled state to prevent flash on enable/disable
            self.setText("")
            self.setIcon(QIcon(self.base_pixmap))
            self.setFlat(True)
            self.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                }
                QPushButton:disabled {
                    border: none;
                    background: transparent;
                }
            """)
        else:
            # Text mode styling - clear font cache to get fresh lookup
            self.clear_font_cache()
            
            self.setText(self.label_text)
            self.setIcon(QIcon())
            self.setFlat(False)
            
            stylesheet = self._build_text_mode_stylesheet(use_minimum_height=True)
            if stylesheet:
                self.setStyleSheet(stylesheet)
    
    def force_update_image_mode(self) -> None:
        """Force immediate update for image mode."""
        if self._is_in_image_mode():
            size = self.size()
            if size.width() > 0 and size.height() > 0:
                state = 'base'
                if self.is_pressed_state:
                    state = 'pressed'
                elif self.is_hover_state:
                    state = 'hover'
                self._update_button_state(state)