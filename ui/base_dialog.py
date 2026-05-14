"""
RNV Text Transformer - Base Dialog Module
Base class for all application dialogs with common functionality.

Python 3.13 Optimized:
- Modern type hints
- Consistent window configuration
- Theme-aware styling via DialogStyleManager
- Common button and layout helpers


Usage:
    from ui.base_dialog import BaseDialog
    
    class MyDialog(BaseDialog):
        _DIALOG_WIDTH = 600
        _DIALOG_HEIGHT = 400
        _DIALOG_TITLE = "My Dialog"
        
        def __init__(self, theme_manager, font_family="Arial", parent=None):
            super().__init__(theme_manager, font_family, parent)
            self._setup_ui()
            self.apply_base_styling()
        
        def _setup_ui(self):
            # ... build UI ...
            close_btn = self._create_close_button()
            layout.addLayout(self._create_button_row(close_btn))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QDialog, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class BaseDialog(QDialog):
    """
    Base class for all application dialogs.
    
    Provides:
    - Standard window configuration (title, size, modality, flags)
    - Theme detection and styling via DialogStyleManager
    - Common button creation helpers
    - Standard layout helpers
    
    Subclasses should:
    1. Override class variables for dialog configuration
    2. Call super().__init__() in their __init__
    3. Build UI in _setup_ui() or similar method
    4. Call self.apply_base_styling() after UI is built
    
    Class Variables:
        _DIALOG_WIDTH: Dialog width in pixels (default: 500)
        _DIALOG_HEIGHT: Dialog height in pixels (default: 400)
        _DIALOG_TITLE: Window title (default: "Dialog")
        _MODAL: Whether dialog is modal (default: True)
        _RESIZABLE: Whether dialog can be resized (default: False)
    """
    
    # ==================== CLASS CONFIGURATION ====================
    
    _DIALOG_WIDTH: ClassVar[int] = 500
    _DIALOG_HEIGHT: ClassVar[int] = 400
    _DIALOG_TITLE: ClassVar[str] = "Dialog"
    _MODAL: ClassVar[bool] = True
    _RESIZABLE: ClassVar[bool] = False
    
    # Standard button sizes
    _BUTTON_HEIGHT: ClassVar[int] = 35
    _BUTTON_WIDTH_SMALL: ClassVar[int] = 80
    _BUTTON_WIDTH_MEDIUM: ClassVar[int] = 100
    _BUTTON_WIDTH_LARGE: ClassVar[int] = 120
    
    # Standard margins and spacing
    _CONTENT_MARGINS: ClassVar[tuple[int, int, int, int]] = (15, 15, 15, 15)
    _SPACING: ClassVar[int] = 12
    
    __slots__ = ('theme_manager', 'font_family', '_is_dark')
    
    # ==================== INITIALIZATION ====================
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize base dialog.
        
        Args:
            theme_manager: Theme manager instance for styling
            font_family: Font family name to use
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.font_family = font_family
        self._is_dark = self._detect_dark_theme()
        
        self._configure_window()
    
    def _detect_dark_theme(self) -> bool:
        """
        Detect if dark theme is active.
        
        Returns:
            True if current theme uses dark colors (dark or image mode)
        """
        # Use property if available, otherwise check directly
        if hasattr(self.theme_manager, 'is_dark_mode'):
            return self.theme_manager.is_dark_mode
        return self.theme_manager.current_theme in ('dark', 'image')
    
    def _configure_window(self) -> None:
        """Configure standard window properties."""
        # Set title
        self.setWindowTitle(self._DIALOG_TITLE)
        
        # Set window icon (same as main window)
        from core.resource_loader import ResourceLoader
        app_icon = ResourceLoader.load_app_icon()
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        
        # Set modality
        self.setModal(self._MODAL)
        
        # Remove help button from title bar (Windows)
        flags = self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        
        # Prevent window resizing for fixed-size dialogs
        if not self._RESIZABLE:
            flags |= Qt.WindowType.MSWindowsFixedSizeDialogHint
        
        self.setWindowFlags(flags)
        
        # Set size (min and max locked to same dimensions prevents drag resize glitch)
        if self._RESIZABLE:
            self.resize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)
            self.setMinimumSize(
                int(self._DIALOG_WIDTH * 0.8),
                int(self._DIALOG_HEIGHT * 0.8)
            )
        else:
            self.setMinimumSize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)
            self.setMaximumSize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)
    
    # ==================== STYLING ====================
    
    def apply_base_styling(self) -> None:
        """
        Apply theme-appropriate base styling using DialogStyleManager.
        
        Call this after building UI to apply consistent styling.
        For dialogs with additional components, override and call super().
        """
        from utils.dialog_styles import DialogStyleManager
        stylesheet = DialogStyleManager.get_dialog_stylesheet(
            self._is_dark, 
            self.font_family
        )
        self.setStyleSheet(stylesheet)
    
    def apply_extended_styling(self, *components: str) -> None:
        """
        Apply styling with additional component styles.
        
        Args:
            *components: Component names to include
                - 'splitter': QSplitter styles
                - 'menu': QMenu styles
                - 'table': QTableWidget styles
                - 'tab': QTabWidget styles
                - 'spinbox': QSpinBox styles
                - 'slider': QSlider styles
                - 'list': QListWidget styles
        """
        from utils.dialog_styles import DialogStyleManager
        stylesheet = DialogStyleManager.get_extended_stylesheet(
            self._is_dark,
            self.font_family,
            *components
        )
        self.setStyleSheet(stylesheet)
    
    def refresh_theme(self) -> None:
        """
        Refresh dialog styling after theme change.
        
        Call this when the application theme changes to update the dialog.
        """
        self._is_dark = self._detect_dark_theme()
        self.apply_base_styling()
    
    def get_status_style(self, status: str) -> str:
        """
        Get inline style for status indicators.
        
        Args:
            status: One of 'success', 'error', 'warning', 'muted', 'info', 'accent'
            
        Returns:
            CSS style string
        """
        from utils.dialog_styles import DialogStyleManager
        return DialogStyleManager.get_status_style(self._is_dark, status)
    
    # ==================== BUTTON HELPERS ====================
    
    def _create_close_button(
        self, 
        text: str = "Close",
        width: int | None = None,
        is_default: bool = True
    ) -> QPushButton:
        """
        Create standard close button.
        
        Args:
            text: Button text (default: "Close")
            width: Button width (default: _BUTTON_WIDTH_MEDIUM)
            is_default: Whether this is the default button
            
        Returns:
            Configured QPushButton that closes the dialog
        """
        btn = QPushButton(text)
        btn.setFixedSize(width or self._BUTTON_WIDTH_MEDIUM, self._BUTTON_HEIGHT)
        btn.clicked.connect(self.accept)
        if is_default:
            btn.setDefault(True)
        return btn
    
    def _create_cancel_button(
        self, 
        text: str = "Cancel",
        width: int | None = None
    ) -> QPushButton:
        """
        Create standard cancel button.
        
        Args:
            text: Button text (default: "Cancel")
            width: Button width (default: _BUTTON_WIDTH_MEDIUM)
            
        Returns:
            Configured QPushButton that rejects the dialog
        """
        btn = QPushButton(text)
        btn.setFixedSize(width or self._BUTTON_WIDTH_MEDIUM, self._BUTTON_HEIGHT)
        btn.clicked.connect(self.reject)
        return btn
    
    def _create_action_button(
        self,
        text: str,
        callback: callable,
        width: int | None = None,
        enabled: bool = True,
        tooltip: str | None = None
    ) -> QPushButton:
        """
        Create action button with callback.
        
        Args:
            text: Button text
            callback: Function to call on click
            width: Button width (default: _BUTTON_WIDTH_MEDIUM)
            enabled: Whether button is initially enabled
            tooltip: Optional tooltip text
            
        Returns:
            Configured QPushButton
        """
        btn = QPushButton(text)
        btn.setFixedSize(width or self._BUTTON_WIDTH_MEDIUM, self._BUTTON_HEIGHT)
        btn.clicked.connect(callback)
        btn.setEnabled(enabled)
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def _create_small_button(
        self,
        text: str,
        callback: callable,
        tooltip: str | None = None
    ) -> QPushButton:
        """
        Create small action button (e.g., for toolbars).
        
        Args:
            text: Button text (usually short, like "+" or "...")
            callback: Function to call on click
            tooltip: Optional tooltip text
            
        Returns:
            Small configured QPushButton
        """
        btn = QPushButton(text)
        btn.setFixedSize(self._BUTTON_WIDTH_SMALL, self._BUTTON_HEIGHT)
        btn.clicked.connect(callback)
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    # ==================== LAYOUT HELPERS ====================
    
    def _create_button_row(
        self, 
        *buttons: QPushButton, 
        stretch_before: bool = True,
        stretch_after: bool = False,
        spacing: int | None = None
    ) -> QHBoxLayout:
        """
        Create horizontal button layout.
        
        Args:
            *buttons: Buttons to add to the row
            stretch_before: Add stretch before buttons (right-align)
            stretch_after: Add stretch after buttons
            spacing: Space between buttons (default: 10)
            
        Returns:
            Configured QHBoxLayout
        """
        layout = QHBoxLayout()
        layout.setSpacing(spacing if spacing is not None else 10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if stretch_before:
            layout.addStretch()
        
        for btn in buttons:
            layout.addWidget(btn)
        
        if stretch_after:
            layout.addStretch()
        
        return layout
    
    def _create_main_layout(
        self,
        margins: tuple[int, int, int, int] | None = None,
        spacing: int | None = None
    ) -> QVBoxLayout:
        """
        Create standard main vertical layout.
        
        Args:
            margins: Content margins (left, top, right, bottom)
            spacing: Spacing between items
            
        Returns:
            Configured QVBoxLayout set on the dialog
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*(margins or self._CONTENT_MARGINS))
        layout.setSpacing(spacing if spacing is not None else self._SPACING)
        return layout
    
    def _create_form_row(
        self,
        label_text: str,
        widget: QWidget,
        label_width: int = 120
    ) -> QHBoxLayout:
        """
        Create a form row with label and widget.
        
        Args:
            label_text: Label text
            widget: Widget to place next to label
            label_width: Fixed width for label alignment
            
        Returns:
            QHBoxLayout containing label and widget
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        label = QLabel(label_text)
        label.setFixedWidth(label_width)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        
        return layout
    
    # ==================== WIDGET HELPERS ====================
    
    def _create_header_label(self, text: str) -> QLabel:
        """
        Create a section header label.
        
        Args:
            text: Header text
            
        Returns:
            Styled QLabel for use as section header
        """
        from utils.dialog_styles import DialogStyleManager
        
        label = QLabel(text)
        label.setStyleSheet(DialogStyleManager.get_header_style(self._is_dark))
        return label
    
    def _create_subtitle_label(self, text: str) -> QLabel:
        """
        Create a subtitle/description label.
        
        Args:
            text: Subtitle text
            
        Returns:
            Styled QLabel for use as subtitle
        """
        from utils.dialog_styles import DialogStyleManager
        
        label = QLabel(text)
        label.setStyleSheet(DialogStyleManager.get_subtitle_style(self._is_dark))
        label.setWordWrap(True)
        return label
    
    def _create_description_label(self, text: str) -> QLabel:
        """
        Create a description/info label (smaller muted text).
        
        Args:
            text: Description text
            
        Returns:
            Styled QLabel for use as description within groups
        """
        from utils.dialog_styles import DialogStyleManager
        
        label = QLabel(text)
        label.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))
        label.setWordWrap(True)
        return label
    
    def _create_tip_label(self, text: str, center: bool = True) -> QLabel:
        """
        Create a tip label (accent-colored italic text).
        
        Args:
            text: Tip text
            center: Whether to center-align the text
            
        Returns:
            Styled QLabel for use as a tip/hint
        """
        from utils.dialog_styles import DialogStyleManager
        
        label = QLabel(text)
        label.setStyleSheet(DialogStyleManager.get_tip_style(self._is_dark))
        if center:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
    
    def _create_separator(self, horizontal: bool = True) -> QFrame:
        """
        Create a separator line.
        
        Args:
            horizontal: True for horizontal line, False for vertical
            
        Returns:
            QFrame configured as separator
        """
        separator = QFrame()
        if horizontal:
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
        else:
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator
    
    # ==================== UTILITY METHODS ====================
    
    @property
    def is_dark_theme(self) -> bool:
        """Check if dialog is using dark theme colors."""
        return self._is_dark
    
    def get_colors(self) -> dict[str, str]:
        """
        Get current theme colors.
        
        Returns:
            Dictionary of color name -> hex color
        """
        from utils.dialog_styles import DialogStyleManager
        return DialogStyleManager.get_colors(self._is_dark)