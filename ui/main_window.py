"""
RNV Text Transformer - Main Window Module
Main application window with UI setup and event handling

Python 3.13 Optimized:
- Modern type hints with TYPE_CHECKING
- Match statements for theme handling
- Improved organization with helper methods
- Better type safety throughout

- Standalone About dialog (Ctrl+/)
- Removed About tab from settings panel
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QFileDialog, QSizePolicy, QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPoint
from PyQt6.QtGui import (
    QPalette, QColor, QShortcut, QKeySequence, QAction, QCursor,
    QPainter, QPen, QPainterPath
)

from core.theme_manager import ThemeManager
from core.text_transformer import TextTransformer
from core.resource_loader import ResourceLoader
from core.text_statistics import TextStatistics
from core.preset_manager import PresetManager, PresetExecutor, TransformPreset
from ui.drag_drop_text_edit import DragDropTextEdit
from ui.image_button import ImageButton
from ui.settings_dialog import SettingsDialog
from ui.find_replace_dialog import FindReplaceDialog
from ui.batch_dialog import BatchDialog
from ui.compare_dialog import CompareDialog
from ui.export_dialog import ExportDialog
from ui.encoding_dialog import EncodingDialog
from ui.regex_builder_dialog import RegexBuilderDialog
from ui.preset_dialog import PresetDialog, PresetManagerDialog
from ui.watch_folder_dialog import WatchFolderDialog
from ui.about_dialog import AboutDialog
from utils.config import (
    FontManager, APP_NAME, THEME_BUTTON_WIDTH, THEME_BUTTON_HEIGHT,
    THEME_BUTTON_MARGIN, STATUS_CLEAR_TIMEOUT, FILE_DIALOG_FILTER, SAVE_FILE_FILTER,
    BUTTON_SPACING, BUTTON_MARGINS, INPUT_TEXT_MIN_HEIGHT, INPUT_TEXT_MAX_HEIGHT,
    STATUS_LABEL_MIN_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
)
from utils.file_handler import FileHandler
from utils.clipboard_utils import ClipboardUtils
from utils.async_workers import (
    FileLoaderThread, TextTransformThread, should_use_thread_for_transform
)
from utils.settings_manager import SettingsManager
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from PyQt6.QtGui import QResizeEvent, QCloseEvent


# Auto-transform debounce delay (milliseconds)
AUTO_TRANSFORM_DELAY: int = 500

# Settings button height (in mode row)
SETTINGS_BUTTON_HEIGHT: int = 30

# Maximum output history states for undo/redo
MAX_OUTPUT_HISTORY: int = 10


class _ThemedToolTip(QLabel):
    """
    Custom tooltip that bypasses native Windows tooltip rendering.
    
    Native QToolTip on Windows creates an OS-level popup window with its own
    frame that cannot be styled via CSS. This class creates a frameless Qt
    widget with WA_TranslucentBackground and paints its own rounded-rect
    background, giving pixel-perfect themed tooltips in all modes.
    """
    
    _instance: '_ThemedToolTip | None' = None
    _OFFSET_X: int = 16
    _OFFSET_Y: int = 20
    _HIDE_DELAY_MS: int = 5000
    _MAX_WIDTH: int = 400
    _BORDER_RADIUS: int = 4
    
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(self._MAX_WIDTH)
        self.hide()
        
        # Colors for paintEvent (updated on each show via show_tip)
        self._bg_color = QColor(DialogStyleManager.DARK['bg_secondary'])
        self._border_color = QColor(DialogStyleManager.DARK['tooltip_border'])
        
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
    
    @classmethod
    def instance(cls) -> '_ThemedToolTip':
        """Get or create the singleton tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def paintEvent(self, event) -> None:
        """Paint rounded-rect background and border manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw filled rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                           float(rect.width()), float(rect.height()),
                           self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.fillPath(path, self._bg_color)
        
        # Draw border
        painter.setPen(QPen(self._border_color, 1.0))
        painter.drawPath(path)
        painter.end()
        
        # Let QLabel paint the text on top
        super().paintEvent(event)
    
    def show_tip(self, global_pos: QPoint, text: str,
                 colors: dict, font_family: str) -> None:
        """Show themed tooltip at the given global position."""
        # Store colors for paintEvent
        self._bg_color = QColor(colors['bg_secondary'])
        self._border_color = QColor(colors['tooltip_border'])
        
        # Title case the tooltip text
        self.setText(text.title())
        
        # Stylesheet for text only (background/border painted in paintEvent)
        self.setStyleSheet(
            f"color: {colors['text']};"
            f"padding: 4px 8px;"
            f"font-family: '{font_family}';"
            f"background: transparent;"
        )
        self.adjustSize()
        
        # Position below-right of cursor
        x = global_pos.x() + self._OFFSET_X
        y = global_pos.y() + self._OFFSET_Y
        
        # Keep tooltip on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            rect = screen.availableGeometry()
            if x + self.width() > rect.right():
                x = global_pos.x() - self.width() - 4
            if y + self.height() > rect.bottom():
                y = global_pos.y() - self.height() - 4
        
        self.move(x, y)
        self.show()
        self._hide_timer.start(self._HIDE_DELAY_MS)
    
    def hide_tip(self) -> None:
        """Hide the tooltip and cancel auto-hide timer."""
        self._hide_timer.stop()
        self.hide()


class MainWindow(QMainWindow):
    """Main application window."""
    
    __slots__ = (
        'theme_manager', 'settings_manager', 'custom_font', 'font_family', 
        'background_label', 'input_label', 'input_label_container', 'text_input', 
        'mode_label', 'mode_combo', 'mode_combo_view', 'buttons_layout', 'transform_btn', 
        'copy_btn', 'load_btn', 'save_btn',
        'all_buttons', 'output_label', 'output_text', 'output_layout', 'status_label',
        'stats_label', 'theme_button', 'settings_button', 
        'status_timer', 'auto_transform_timer',
        # Async worker threads
        '_file_loader_thread', '_transform_thread', '_is_loading',
        # Recent files and undo/redo
        'recent_files_menu', '_output_history', '_output_history_index',
        # Preset system
        'preset_manager', 'preset_executor'
    )
    
    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()
        
        # Initialize settings manager (must be first for loading preferences)
        self.settings_manager = SettingsManager()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.detect_image_resources()
        
        # Load saved theme preference
        self._load_theme_from_settings()
        
        # Load custom font
        self.custom_font = FontManager.load_embedded_font()
        self.font_family = FontManager.get_font_family()
        
        # Setup window with saved geometry or defaults
        self.setWindowTitle(APP_NAME)
        self._restore_window_geometry()
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Load and set application icon
        app_icon = ResourceLoader.load_app_icon()
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        
        # Disable drag and drop on main window
        self.setAcceptDrops(False)
        
        # Create background label for image mode
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)
        self.background_label.lower()
        self.background_label.hide()
        
        # Initialize async worker threads
        self._file_loader_thread: FileLoaderThread | None = None
        self._transform_thread: TextTransformThread | None = None
        self._is_loading: bool = False
        
        # Initialize output history for undo/redo
        self._output_history: list[str] = []
        self._output_history_index: int = -1
        
        # Initialize preset system
        self.preset_manager = PresetManager()
        self.preset_executor = PresetExecutor()
        
        # Setup UI
        self._setup_ui()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Restore last used transform mode
        self._restore_transform_mode()
        
        # Apply saved settings
        self._apply_stats_position_from_settings()
        
        # Apply theme
        self.apply_theme()
        
        # Schedule initial button update after window is shown
        QTimer.singleShot(0, self._initial_button_update)
        
        # Install application-level event filter for custom themed tooltips
        # (bypasses native Windows tooltip rendering that ignores CSS border-radius)
        QApplication.instance().installEventFilter(self)
    
    def _load_theme_from_settings(self) -> None:
        """Load and apply saved theme preference."""
        saved_theme = self.settings_manager.load_theme()
        
        # Handle image mode availability
        if saved_theme == 'image' and not self.theme_manager.image_mode_available:
            saved_theme = 'dark'  # Fallback if image resources not available
        
        # Set the theme
        self.theme_manager.set_theme(saved_theme)
    
    def _restore_window_geometry(self) -> None:
        """
        Restore window position and size from settings.
        
        Uses individual saved values (not QByteArray restoreGeometry) so we can
        explicitly clamp width/height to the minimum before applying. restoreGeometry
        encodes the raw saved dimensions and bypasses setMinimumSize entirely.
        """
        x, y, width, height = self.settings_manager.load_window_position()
        
        # Clamp to minimum size before applying
        width = max(width, MIN_WINDOW_WIDTH)
        height = max(height, MIN_WINDOW_HEIGHT)
        
        self.setGeometry(x, y, width, height)
        
        # Restore maximized state
        if self.settings_manager.load_window_maximized():
            self.showMaximized()
    
    def _restore_transform_mode(self) -> None:
        """Restore last used transform mode from settings."""
        saved_mode = self.settings_manager.load_transform_mode()
        index = self.mode_combo.findText(saved_mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for all primary actions."""
        # Transform: Ctrl+T
        shortcut_transform = QShortcut(QKeySequence("Ctrl+T"), self)
        shortcut_transform.activated.connect(self._transform_text)
        
        # Copy output: Ctrl+Shift+C
        shortcut_copy = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        shortcut_copy.activated.connect(self._copy_to_clipboard)
        
        # Load file: Ctrl+O
        shortcut_load = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_load.activated.connect(self._load_file)
        
        # Save file: Ctrl+S
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self._save_file)
        
        # Clear all: Ctrl+Shift+X
        shortcut_clear = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        shortcut_clear.activated.connect(self._clear_all)
        
        # Swap input/output: Ctrl+Shift+S
        shortcut_swap = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        shortcut_swap.activated.connect(self._swap_input_output)
        
        # Cycle theme: Ctrl+Shift+T
        shortcut_theme = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut_theme.activated.connect(self._cycle_theme)
        
        # Open settings: Ctrl+, (standard settings shortcut)
        shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        shortcut_settings.activated.connect(self._open_settings)
        
        # Quit: Ctrl+Q
        shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_quit.activated.connect(self.close)
        
        # Undo output: Ctrl+Z
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self._undo_output)
        
        # Redo output: Ctrl+Y
        shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        shortcut_redo.activated.connect(self._redo_output)
        
        # Recent files: Ctrl+Shift+O
        shortcut_recent = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        shortcut_recent.activated.connect(self._show_recent_files_menu)
        
        # Find: Ctrl+F
        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self._open_find_dialog)
        
        # Find & Replace: Ctrl+H
        shortcut_replace = QShortcut(QKeySequence("Ctrl+H"), self)
        shortcut_replace.activated.connect(self._open_replace_dialog)
        
        # Batch Processing: Ctrl+B
        shortcut_batch = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut_batch.activated.connect(self._open_batch_dialog)
        
        # Compare View: Ctrl+D
        shortcut_compare = QShortcut(QKeySequence("Ctrl+D"), self)
        shortcut_compare.activated.connect(self._open_compare_dialog)
        
        # Export: Ctrl+E
        shortcut_export = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_export.activated.connect(self._open_export_dialog)
        
        # Encoding Converter: Ctrl+Shift+E
        shortcut_encoding = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        shortcut_encoding.activated.connect(self._open_encoding_dialog)
        
        # Regex Builder: Ctrl+R
        shortcut_regex = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_regex.activated.connect(self._open_regex_builder_dialog)
        
        # Preset Manager: Ctrl+P
        shortcut_presets = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_presets.activated.connect(self._open_preset_manager_dialog)
        
        # Watch Folders: Ctrl+W
        shortcut_watch = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut_watch.activated.connect(self._open_watch_folder_dialog)
        
        # About: Ctrl+/
        shortcut_about = QShortcut(QKeySequence("Ctrl+/"), self)
        shortcut_about.activated.connect(self._open_about_dialog)
        
        # Toggle tooltips: F11
        shortcut_tooltips = QShortcut(QKeySequence("F11"), self)
        shortcut_tooltips.activated.connect(self._toggle_tooltips)
    
    def _setup_button_tooltips(self) -> None:
        """Add tooltips with keyboard shortcut hints to buttons."""
        self.transform_btn.setToolTip("Transform text (Ctrl+T)")
        self.copy_btn.setToolTip("Copy output to clipboard (Ctrl+Shift+C)")
        self.load_btn.setToolTip("Load file (Ctrl+O) | Recent files (Ctrl+Shift+O)")
        self.save_btn.setToolTip("Save output to file (Ctrl+S)")
        self.theme_button.setToolTip("Cycle theme (Ctrl+Shift+T)")
        self.settings_button.setToolTip("Open settings (Ctrl+,)")
        self.mode_combo.setToolTip("Select text transformation mode")
    
    def _initial_button_update(self) -> None:
        """Update buttons after initial layout is complete."""
        if not self.theme_manager.is_image_mode():
            for btn in self.all_buttons:
                btn.update_text_font_size()
            self.settings_button.update_text_font_size()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top section with input
        self._setup_input_section(main_layout)
        
        # Middle section with output and buttons
        self._setup_middle_section(main_layout)
        
        # Theme button (floating in corner)
        self._setup_theme_button()
        
        # Add tooltips to buttons
        self._setup_button_tooltips()
        
        # Status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._clear_status)
        
        # Auto-transform debounce timer
        self.auto_transform_timer = QTimer()
        self.auto_transform_timer.setSingleShot(True)
        self.auto_transform_timer.timeout.connect(self._do_auto_transform)
    
    def _setup_input_section(self, main_layout: QVBoxLayout) -> None:
        """Setup input text area and mode selector."""
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(5)
        
        # Top row container with styled background (stretches full width)
        self.input_label_container = QWidget()
        input_label_row = QHBoxLayout(self.input_label_container)
        input_label_row.setContentsMargins(5, 0, 0, 2)  # Slim margins: left, top, right, bottom
        input_label_row.setSpacing(10)
        
        self.input_label = QLabel("Enter or paste your text:")
        self.input_label.setStyleSheet("")  # Clear any individual styling - will be styled via container
        input_label_row.addWidget(self.input_label)
        
        input_label_row.addStretch()
        
        # Settings button on the right side of top row (always shows gear image)
        self.settings_button = ImageButton("settings_gear", "Settings", self._open_settings)
        self.settings_button.set_font_family(self.font_family)
        self.settings_button.set_force_image_mode(True)  # Always show gear image in all modes
        self.settings_button.set_theme_manager(self.theme_manager)
        self.settings_button.setFixedSize(SETTINGS_BUTTON_HEIGHT, SETTINGS_BUTTON_HEIGHT)  # Square button
        input_label_row.addWidget(self.settings_button)
        
        top_layout.addWidget(self.input_label_container)
        
        self.text_input = DragDropTextEdit()
        self.text_input.setMinimumHeight(INPUT_TEXT_MIN_HEIGHT)
        self.text_input.setMaximumHeight(INPUT_TEXT_MAX_HEIGHT)
        self.text_input.fileDropped.connect(self._handle_dropped_file)
        self.text_input.textChanged.connect(self._on_input_text_changed)
        self.text_input.set_theme_manager(self.theme_manager)
        # Connect context menu signals
        self.text_input.loadFileRequested.connect(self._load_file)
        self.text_input.clearRequested.connect(self._clear_input)
        top_layout.addWidget(self.text_input)
        
        # Mode row
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        self.mode_label = QLabel("Mode:")
        mode_layout.addWidget(self.mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(TextTransformer.get_available_modes())
        self.mode_combo.setFixedWidth(175)  # Wider to fit new mode names
        
        # Connect mode change to save preference and auto-transform
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Set view to allow transparency in dropdown
        view = self.mode_combo.view()
        if view is not None:
            window = view.window()
            if window is not None:
                window.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
                window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Store view reference for palette updates
        self.mode_combo_view = view
        
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        
        top_layout.addLayout(mode_layout)
        main_layout.addWidget(top_widget)
    
    def _on_input_text_changed(self) -> None:
        """Handle input text changes - trigger auto-transform if enabled."""
        # Update statistics
        self._update_statistics()
        
        # Trigger auto-transform with debounce (if enabled in settings)
        if self.settings_manager.load_auto_transform() and not self._is_loading:
            self.auto_transform_timer.start(AUTO_TRANSFORM_DELAY)
    
    def _do_auto_transform(self) -> None:
        """Execute auto-transform after debounce delay."""
        if self.settings_manager.load_auto_transform() and not self._is_loading:
            self._transform_text()
    
    def _on_mode_changed(self, mode: str) -> None:
        """Handle transform mode change - save preference and auto-transform."""
        self.settings_manager.save_transform_mode(mode)
        
        # Auto-transform if enabled and there's text
        if self.settings_manager.load_auto_transform() and self.text_input.toPlainText():
            self._transform_text()
    
    def _setup_middle_section(self, main_layout: QVBoxLayout) -> None:
        """Setup output area and action buttons."""
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(0)
        middle_layout.setContentsMargins(10, 0, 10, 0)
        
        # Buttons container
        buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(buttons_container)
        self.buttons_layout.setSpacing(BUTTON_SPACING)
        self.buttons_layout.setContentsMargins(*BUTTON_MARGINS)
        self.buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create buttons - set font family explicitly before theme manager
        # to ensure correct font is used even before window hierarchy is established
        self.transform_btn = ImageButton("transform", "Transform", self._transform_text)
        self.transform_btn.set_font_family(self.font_family)
        self.transform_btn.set_theme_manager(self.theme_manager)
        self.transform_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.transform_btn.setMinimumHeight(80)
        self.buttons_layout.addWidget(self.transform_btn)
        
        self.copy_btn = ImageButton("copy", "Copy", self._copy_to_clipboard)
        self.copy_btn.set_font_family(self.font_family)
        self.copy_btn.set_theme_manager(self.theme_manager)
        self.copy_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.copy_btn.setMinimumHeight(80)
        self.buttons_layout.addWidget(self.copy_btn)
        
        self.load_btn = ImageButton("load", "Load", self._load_file)
        self.load_btn.set_font_family(self.font_family)
        self.load_btn.set_theme_manager(self.theme_manager)
        self.load_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.load_btn.setMinimumHeight(80)
        self.buttons_layout.addWidget(self.load_btn)
        
        self.save_btn = ImageButton("save", "Save", self._save_file)
        self.save_btn.set_font_family(self.font_family)
        self.save_btn.set_theme_manager(self.theme_manager)
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.save_btn.setMinimumHeight(80)
        self.buttons_layout.addWidget(self.save_btn)
        
        # Store button list for easy access (only main action buttons)
        self.all_buttons = [
            self.transform_btn, self.copy_btn, self.load_btn, self.save_btn
        ]
        
        middle_layout.addWidget(buttons_container, 1)
        
        # Output on right
        self._setup_output_section(middle_layout)
        
        main_layout.addLayout(middle_layout, 1)
    
    def _setup_output_section(self, middle_layout: QHBoxLayout) -> None:
        """Setup output text area."""
        output_container = QWidget()
        self.output_layout = QVBoxLayout(output_container)
        self.output_layout.setSpacing(10)
        self.output_layout.setContentsMargins(10, 10, 10, 10)
        
        self.output_label = QLabel("Output:")
        self.output_layout.addWidget(self.output_label)
        
        self.output_text = DragDropTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setAcceptDrops(False)
        self.output_text.set_output_mode(True)  # Set as output area
        self.output_text.set_theme_manager(self.theme_manager)
        # Connect context menu signals
        self.output_text.saveFileRequested.connect(self._save_file)
        self.output_layout.addWidget(self.output_text)
        
        # Statistics label - default position is below output
        self.stats_label = QLabel("Input: 0 chars | 0 words | 0 lines")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.output_layout.addWidget(self.stats_label)
        
        self.status_label = QLabel("")
        self.status_label.setMinimumHeight(STATUS_LABEL_MIN_HEIGHT)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_layout.addWidget(self.status_label)
        
        middle_layout.addWidget(output_container, 3)
    
    def _update_statistics(self) -> None:
        """Update the statistics display for input and output text."""
        input_text = self.text_input.toPlainText()
        output_text = self.output_text.toPlainText()
        
        input_stats = TextStatistics.calculate(input_text)
        output_stats = TextStatistics.calculate(output_text)
        
        stats_text = TextStatistics.format_comparison(input_stats, output_stats)
        self.stats_label.setText(stats_text)
    
    def _setup_theme_button(self) -> None:
        """Setup theme toggle button."""
        self.theme_button = QPushButton(self.theme_manager.get_theme_display_name(), self)
        self.theme_button.clicked.connect(self._cycle_theme)
        self.theme_button.setFixedSize(THEME_BUTTON_WIDTH, THEME_BUTTON_HEIGHT)
        
        # Position immediately at bottom-right. If the window was already shown
        # via showMaximized() in _restore_window_geometry, resizeEvent fired
        # before this button existed, so it was never positioned. Set it now.
        self.theme_button.move(
            self.width() - THEME_BUTTON_WIDTH - THEME_BUTTON_MARGIN,
            self.height() - THEME_BUTTON_HEIGHT - THEME_BUTTON_MARGIN
        )
        
        self.theme_button.raise_()
        self.theme_button.show()
        
        # Connect pressed/released signals for theme button
        self.theme_button.pressed.connect(self._on_theme_button_press)
        self.theme_button.released.connect(self._on_theme_button_release)
    
    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(
            settings_manager=self.settings_manager,
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            parent=self
        )
        
        # Connect theme change signal
        dialog.theme_change_requested.connect(self._apply_theme_from_settings)
        
        # Connect settings changed signal
        dialog.settings_changed.connect(self._on_settings_changed)
        
        # Connect stats position change signal
        dialog.stats_position_changed.connect(self._update_stats_position)
        
        # Connect undo/redo signals
        dialog.undo_requested.connect(self._undo_output)
        dialog.redo_requested.connect(self._redo_output)
        
        # Connect recent file open signal
        dialog.open_recent_file_requested.connect(self._open_recent_file)
        
        # Connect cleanup and split/join signals
        dialog.cleanup_requested.connect(self._apply_cleanup)
        dialog.split_join_requested.connect(self._apply_split_join)
        
        # Connect export signal
        dialog.export_requested.connect(self._open_export_dialog)
        
        dialog.exec()
    
    def _update_stats_position(self, position: str) -> None:
        """
        Update statistics label position based on settings.
        
        Args:
            position: "Below Output", "Above Output", or "Hidden"
        
        Layout indices:
        - 0: output_label ("Output:")
        - 1: output_text (or stats if "Above Output")
        - 2: stats_label (default) or output_text
        - 3: status_label
        """
        if position == "Hidden":
            self.stats_label.hide()
        else:
            self.stats_label.show()
            
            # Remove stats_label from current position
            self.output_layout.removeWidget(self.stats_label)
            
            if position == "Above Output":
                # Insert after output_label (index 1), before output_text
                self.output_layout.insertWidget(1, self.stats_label)
            else:  # "Below Output" (default)
                # Insert after output_text (index 2), before status_label
                # Find current index of status_label and insert before it
                status_index = self.output_layout.indexOf(self.status_label)
                self.output_layout.insertWidget(status_index, self.stats_label)
    
    def _apply_stats_position_from_settings(self) -> None:
        """Apply the saved stats position setting on startup."""
        position = self.settings_manager.load_stats_position()
        self._update_stats_position(position)
    
    def _apply_theme_from_settings(self, theme: str) -> None:
        """
        Apply theme change requested from settings dialog.
        
        Args:
            theme: Theme name ('dark', 'light', or 'image')
        """
        # Set the theme
        self.theme_manager.set_theme(theme)
        self.theme_button.setText(self.theme_manager.get_theme_display_name())
        
        # Clear scaled caches when switching themes
        for btn in self.all_buttons:
            btn.clear_scaled_cache()
        self.settings_button.clear_scaled_cache()
        
        # Apply the new theme
        self.apply_theme()
        
        # If switching to image mode, update icon sizes immediately
        if self.theme_manager.is_image_mode():
            for btn in self.all_buttons:
                btn.force_update_image_mode()
            self.settings_button.force_update_image_mode()
        
        # Propagate theme change to any open non-modal dialog
        self._refresh_open_dialogs_theme()
        
        self.update()
    
    def _on_settings_changed(self) -> None:
        """Handle settings changed from dialog - apply all settings immediately."""
        # Update tooltips visibility based on setting
        show_tooltips = self.settings_manager.load_show_tooltips()
        self._update_tooltips_visibility(show_tooltips)
    
    def _update_tooltips_visibility(self, show: bool) -> None:
        """
        Enable or disable tooltips on buttons.
        
        Args:
            show: Whether to show tooltips
        """
        if show:
            self._setup_button_tooltips()
        else:
            # Clear tooltips
            self.transform_btn.setToolTip("")
            self.copy_btn.setToolTip("")
            self.load_btn.setToolTip("")
            self.save_btn.setToolTip("")
            self.theme_button.setToolTip("")
            self.settings_button.setToolTip("")
            self.mode_combo.setToolTip("")
            # Hide any currently visible custom tooltip
            _ThemedToolTip.instance().hide_tip()
    
    def _toggle_tooltips(self) -> None:
        """Toggle tooltip visibility (F11 shortcut)."""
        current = self.settings_manager.load_show_tooltips()
        new_state = not current
        self.settings_manager.save_show_tooltips(new_state)
        self._update_tooltips_visibility(new_state)
        state_text = "enabled" if new_state else "disabled"
        self._set_status(f"Tooltips {state_text}")
    
    # ==================== THEME MANAGEMENT ====================
    
    def _cycle_theme(self) -> None:
        """Cycle through available themes."""
        self.theme_manager.cycle_theme()
        self.theme_button.setText(self.theme_manager.get_theme_display_name())
        
        # Save theme preference
        self.settings_manager.save_theme(self.theme_manager.current_theme)
        
        # Clear scaled caches when switching themes
        for btn in self.all_buttons:
            btn.clear_scaled_cache()
        self.settings_button.clear_scaled_cache()
        
        # Apply the new theme
        self.apply_theme()
        
        # If switching to image mode, update icon sizes immediately
        if self.theme_manager.is_image_mode():
            for btn in self.all_buttons:
                btn.force_update_image_mode()
            self.settings_button.force_update_image_mode()
        
        # Propagate theme change to any open non-modal dialog
        self._refresh_open_dialogs_theme()
        
        self.update()
    
    def _on_theme_button_press(self) -> None:
        """Handle theme button press."""
        stylesheet = self._build_theme_button_stylesheet(pressed=True)
        self.theme_button.setStyleSheet(stylesheet)
    
    def _on_theme_button_release(self) -> None:
        """Handle theme button release."""
        stylesheet = self._build_theme_button_stylesheet(pressed=False)
        self.theme_button.setStyleSheet(stylesheet)
    
    def _build_theme_button_stylesheet(self, pressed: bool = False) -> str:
        """
        Build stylesheet for theme toggle button.
        
        Args:
            pressed: Whether button is in pressed state
            
        Returns:
            Complete stylesheet string
        """
        if self.theme_manager.is_image_mode():
            # Image mode — use DARK palette (image mode is dark-based)
            _d = DialogStyleManager.DARK
            if pressed:
                bg, color, hover_bg = _d['bg_tertiary'], _d['accent_text'], _d['bg_tertiary']
            else:
                bg, color, hover_bg = _d['button_bg'], _d['text'], _d['button_hover_bg']
            border = _d['border']
            hover_color = color
        else:
            # Dark/Light mode colors from theme
            theme = self.theme_manager.colors
            bg = theme['button_bg']
            border = theme['border_color']
            hover_bg = theme['button_hover_bg']
            if pressed:
                color = theme['button_pressed_text']
                hover_color = theme['button_pressed_text']
            else:
                color = theme['button_text']
                hover_color = theme['button_text']
        
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid {border};
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-family: '{self.font_family}';
                font-size: 7.5pt;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_color};
            }}
        """
    
    def apply_theme(self) -> None:
        """Apply current theme to all UI components."""
        self.setUpdatesEnabled(False)
        try:
            # colors returns dark palette for both dark & image modes
            active_theme = self.theme_manager.colors
            
            # Apply button layout spacing
            self.buttons_layout.setSpacing(BUTTON_SPACING)
            self.buttons_layout.setContentsMargins(*BUTTON_MARGINS)
            
            # Set palette
            palette = QPalette()
            window_color = QColor(active_theme['window_bg'])
            text_color = QColor(active_theme['text_color'])
            
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, window_color)
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, text_color)
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, window_color)
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, text_color)
            
            # Selection highlight colors (brand gold)
            highlight_color = QColor(active_theme['selection_bg'])
            highlight_text = QColor(active_theme['selection_text'])
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, highlight_color)
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, highlight_text)
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, highlight_color)
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, highlight_text)
            
            app = QApplication.instance()
            if app is not None:
                app.setPalette(palette)
            
            # Handle background image using QLabel
            if self.theme_manager.is_image_mode():
                bg_pixmap = self.theme_manager.get_background_pixmap()
                if bg_pixmap is not None and not bg_pixmap.isNull():
                    self.background_label.setPixmap(bg_pixmap)
                    self.background_label.setGeometry(0, 0, self.width(), self.height())
                    self.background_label.show()
                    self.theme_button.raise_()  # Keep theme button above background image
                else:
                    self.background_label.hide()
            else:
                self.background_label.hide()
            
            # Apply stylesheets
            self._apply_stylesheets(active_theme)
            
            # Update all buttons
            for btn in self.all_buttons:
                btn.apply_style()
            
            self.theme_button.repaint()
            
        except Exception as e:
            from utils.logger import get_module_logger
            _log = get_module_logger("MainWindow")
            if _log:
                _log.error(f"apply_theme failed: {e}")
        finally:
            self.setUpdatesEnabled(True)
            self.update()
    
    def _apply_stylesheets(self, active_theme: dict) -> None:
        """Apply stylesheets to UI components."""
        # Get mode and determine special colors for image mode
        mode = self.theme_manager.current_theme
        if mode not in ('image', 'dark', 'light'):
            mode = 'light'  # Fallback
        
        # Image mode uses semi-transparent backgrounds
        if mode == 'image':
            input_bg = DialogStyleManager.DARK['image_overlay_bg']
            label_bg = DialogStyleManager.DARK['image_overlay_bg']
        else:
            input_bg = active_theme['input_bg']
            label_bg = active_theme['label_bg']
        
        scrollbar_style = self._get_scrollbar_style(mode)
        dropdown_style = self._get_dropdown_style(mode, active_theme)
        checkbox_style = self._get_checkbox_style(mode, active_theme)
        
        # Set main stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {active_theme['window_bg']};
            }}
            QLabel {{
                color: {active_theme['label_text']};
                background-color: {label_bg};
                padding: 5px;
                font-family: '{self.font_family}';
            }}
            QTextEdit {{
                background-color: {input_bg};
                color: {active_theme['input_text']};
                border: 1px solid {active_theme['input_border']};
                padding: 4px;
                font-family: '{self.font_family}';
                selection-background-color: {active_theme['selection_bg']};
                selection-color: {active_theme['selection_text']};
            }}
            QComboBox {{
                background-color: {input_bg};
                color: {active_theme['input_text']};
                border: 1px solid {active_theme['input_border']};
                padding: 4px;
                font-family: '{self.font_family}';
                selection-background-color: {active_theme['selection_bg']};
                selection-color: {active_theme['selection_text']};
            }}
            {dropdown_style}
            {scrollbar_style}
            {checkbox_style}
        """)
        
        # Style output text
        output_palette = self.output_text.palette()
        output_palette.setColor(
            self.output_text.foregroundRole(),
            QColor(active_theme['output_text_color'])
        )
        self.output_text.setPalette(output_palette)
        
        # Update dropdown view styling
        if self.mode_combo_view is not None:
            self._update_dropdown_view_style()
        
        # Style theme button
        self._style_theme_button(active_theme)
        
        # Style settings button (ImageButton)
        self.settings_button.apply_style()
        
        # Style info labels (status, output, and stats)
        self._style_info_label(self.status_label, mode, active_theme)
        self._style_info_label(self.output_label, mode, active_theme)
        self._style_info_label(self.stats_label, mode, active_theme)
        
        # Style input label container (full-width background bar with settings button)
        self._style_input_label_container(mode, active_theme)
    
    def _get_checkbox_style(self, mode: str, active_theme: dict) -> str:
        """Get checkbox stylesheet for given mode."""
        match mode:
            case 'image':
                # Image mode uses DARK palette
                return f"""
                    QCheckBox {{
                        color: {active_theme['text']};
                        background-color: transparent;
                        font-family: '{self.font_family}';
                        spacing: 5px;
                    }}
                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 1px solid {active_theme['checkbox_border']};
                        border-radius: 3px;
                        background-color: {DialogStyleManager.DARK['image_overlay_checkbox']};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {active_theme['accent']};
                        border-color: {active_theme['accent']};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {active_theme['accent']};
                    }}
                """
            case 'dark':
                return f"""
                    QCheckBox {{
                        color: {active_theme['text_color']};
                        background-color: transparent;
                        font-family: '{self.font_family}';
                        spacing: 5px;
                    }}
                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 1px solid {active_theme['checkbox_border']};
                        border-radius: 3px;
                        background-color: {active_theme['checkbox_indicator_bg']};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {active_theme['accent']};
                        border-color: {active_theme['accent']};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {active_theme['accent']};
                    }}
                """
            case _:  # light
                return f"""
                    QCheckBox {{
                        color: {active_theme['text_color']};
                        background-color: transparent;
                        font-family: '{self.font_family}';
                        spacing: 5px;
                    }}
                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 1px solid {active_theme['checkbox_border']};
                        border-radius: 3px;
                        background-color: {active_theme['checkbox_indicator_bg']};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {active_theme['accent']};
                        border-color: {active_theme['accent']};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {active_theme['accent']};
                    }}
                """
    
    def _style_info_label(self, label: QLabel, mode: str, theme: dict) -> None:
        """
        Apply styling to info labels (status_label, output_label, stats_label).
        
        Args:
            label: The QLabel to style
            mode: Current theme mode ('image', 'dark', 'light')
            theme: Active theme dictionary
        """
        bg = DialogStyleManager.DARK['image_overlay_bg_dark'] if mode == 'image' else theme['input_bg']
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {theme['input_text']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                font-family: '{self.font_family}';
            }}
        """)
    
    def _style_input_label_container(self, mode: str, theme: dict) -> None:
        """
        Apply styling to input label container (full-width bar with settings button).
        
        Args:
            mode: Current theme mode ('image', 'dark', 'light')
            theme: Active theme dictionary
        """
        bg = DialogStyleManager.DARK['image_overlay_bg'] if mode == 'image' else theme['input_bg']
        self.input_label_container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border: 1px solid {theme['input_border']};
            }}
            QLabel {{
                background-color: transparent;
                border: none;
                color: {theme['input_text']};
                padding: 0px;
                font-family: '{self.font_family}';
            }}
        """)
    
    def _get_scrollbar_style(self, mode: str) -> str:
        """Get scrollbar stylesheet for given mode."""
        match mode:
            case 'image':
                _i = DialogStyleManager.DARK
                return f"""
                    QScrollBar:vertical {{
                        background: transparent;
                        width: 12px;
                        margin: 0px;
                        border: 1px solid {_i['image_scrollbar_border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: {_i['image_scrollbar_handle']};
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background: {_i['accent']};
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        background: transparent;
                        height: 12px;
                        margin: 0px;
                        border: 1px solid {_i['image_scrollbar_border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: {_i['image_scrollbar_handle']};
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:horizontal:hover {{
                        background: {_i['accent']};
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """
            case 'dark':
                _c = DialogStyleManager.DARK
                return f"""
                    QScrollBar:vertical {{
                        background: {_c['scrollbar_bg']};
                        width: 12px;
                        margin: 0px;
                        border: 1px solid {_c['border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: {_c['scrollbar_handle_main']};
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background: {_c['accent']};
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        background: {_c['scrollbar_bg']};
                        height: 12px;
                        margin: 0px;
                        border: 1px solid {_c['border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: {_c['scrollbar_handle_main']};
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:horizontal:hover {{
                        background: {_c['accent']};
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """
            case _:  # light
                _c = DialogStyleManager.LIGHT
                return f"""
                    QScrollBar:vertical {{
                        background: {_c['scrollbar_bg']};
                        width: 12px;
                        margin: 0px;
                        border: 1px solid {_c['border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: {_c['scrollbar_handle_main']};
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background: {_c['accent']};
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        background: {_c['scrollbar_bg']};
                        height: 12px;
                        margin: 0px;
                        border: 1px solid {_c['border']};
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: {_c['scrollbar_handle_main']};
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::handle:horizontal:hover {{
                        background: {_c['accent']};
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """
    
    def _get_dropdown_style(self, mode: str, active_theme: dict) -> str:
        """Get dropdown stylesheet for given mode."""
        match mode:
            case 'image':
                _d = DialogStyleManager.DARK
                return f"""
                    QComboBox::drop-down {{
                        border: none;
                        background-color: {active_theme['button_bg']};
                    }}
                    QComboBox QAbstractItemView {{
                        background-color: {_d['image_dropdown_bg']};
                        color: {_d['text']};
                        selection-background-color: {_d['image_dropdown_selection']};
                        selection-color: {_d['list_hover_bg']};
                        border: 1px solid {_d['image_dropdown_border']};
                    }}
                    QComboBox QAbstractItemView::item {{
                        background-color: {_d['image_dropdown_bg']};
                        color: {_d['text']};
                        padding: 4px;
                    }}
                    QComboBox QAbstractItemView::item:selected {{
                        background-color: {_d['image_dropdown_selection']};
                        color: {_d['list_hover_bg']};
                    }}
                """
            case 'dark':
                _c = DialogStyleManager.DARK
                return f"""
                    QComboBox::drop-down {{
                        border: none;
                        background-color: {active_theme['button_bg']};
                    }}
                    QComboBox QAbstractItemView {{
                        background-color: {_c['bg']};
                        color: {_c['text']};
                        selection-background-color: {_c['list_hover_bg']};
                        selection-color: {_c['list_hover_text']};
                        border: 1px solid {_c['border']};
                    }}
                """
            case _:  # light
                _c = DialogStyleManager.LIGHT
                return f"""
                    QComboBox::drop-down {{
                        border: none;
                        background-color: {active_theme['button_bg']};
                    }}
                    QComboBox QAbstractItemView {{
                        background-color: {_c['bg_secondary']};
                        color: {_c['text']};
                        selection-background-color: {_c['list_hover_bg']};
                        selection-color: {_c['list_hover_text']};
                        border: 1px solid {_c['border']};
                    }}
                """
    
    def _update_dropdown_view_style(self) -> None:
        """Update dropdown view styling."""
        if self.mode_combo_view is None:
            return
            
        match self.theme_manager.current_theme:
            case 'dark':
                _c = DialogStyleManager.DARK
                self.mode_combo_view.setStyleSheet(f"""
                    QListView {{
                        background-color: {_c['bg']};
                        color: {_c['text']};
                        border: 1px solid {_c['border']};
                    }}
                    QListView::item:hover {{
                        background-color: {_c['list_hover_bg']};
                        color: {_c['list_hover_text']};
                    }}
                    QListView::item:selected {{
                        background-color: {_c['list_hover_bg']};
                        color: {_c['list_hover_text']};
                    }}
                """)
            case 'light':
                _c = DialogStyleManager.LIGHT
                self.mode_combo_view.setStyleSheet(f"""
                    QListView {{
                        background-color: {_c['bg_secondary']};
                        color: {_c['text']};
                        border: 1px solid {_c['border']};
                    }}
                    QListView::item:hover {{
                        background-color: {_c['list_hover_bg']};
                        color: {_c['list_hover_text']};
                    }}
                    QListView::item:selected {{
                        background-color: {_c['list_hover_bg']};
                        color: {_c['list_hover_text']};
                    }}
                """)
            case _:  # image mode — rgba backgrounds intentional (image shows through)
                _d = DialogStyleManager.DARK
                self.mode_combo_view.setStyleSheet(f"""
                    QListView {{
                        background-color: {_d['image_dropdown_bg']};
                        color: {_d['text']};
                        border: 1px solid {_d['image_dropdown_border']};
                    }}
                    QListView::item {{
                        background-color: {_d['image_dropdown_bg']};
                        color: {_d['text']};
                        padding: 4px;
                    }}
                    QListView::item:hover {{
                        background-color: {_d['image_dropdown_selection']};
                        color: {_d['list_hover_bg']};
                    }}
                    QListView::item:selected {{
                        background-color: {_d['image_dropdown_selection']};
                        color: {_d['list_hover_bg']};
                    }}
                """)
    
    def _style_theme_button(self, active_theme: dict) -> None:
        """Apply styling to theme button."""
        stylesheet = self._build_theme_button_stylesheet(pressed=False)
        self.theme_button.setStyleSheet(stylesheet)
    
    # ==================== EVENT HANDLING ====================
    
    def eventFilter(self, obj, event) -> bool:
        """
        Application-level event filter for custom themed tooltips.
        
        Intercepts QEvent.ToolTip to show our custom _ThemedToolTip
        instead of the native OS tooltip (which ignores CSS border-radius
        on Windows Light/Image modes).
        """
        event_type = event.type()
        
        if event_type == QEvent.Type.ToolTip:
            if isinstance(obj, QWidget) and obj.toolTip():
                _ThemedToolTip.instance().show_tip(
                    QCursor.pos(),
                    obj.toolTip(),
                    self.theme_manager.colors,
                    self.font_family
                )
                return True  # Consume event — prevent native tooltip
        elif event_type in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                            QEvent.Type.WindowDeactivate, QEvent.Type.Wheel):
            _ThemedToolTip.instance().hide_tip()
        
        return super().eventFilter(obj, event)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Position theme button and background on resize."""
        super().resizeEvent(event)
        
        w, h = self.width(), self.height()
        
        # Update background label size if visible
        if hasattr(self, 'background_label') and self.background_label.isVisible():
            self.background_label.setGeometry(0, 0, w, h)
        
        # Position theme button (bottom right)
        if hasattr(self, 'theme_button'):
            self.theme_button.move(
                w - self.theme_button.width() - THEME_BUTTON_MARGIN,
                h - self.theme_button.height() - THEME_BUTTON_MARGIN
            )
            self.theme_button.raise_()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Save settings and clean up threads when window is closed."""
        # Remove event filter and hide tooltip
        QApplication.instance().removeEventFilter(self)
        _ThemedToolTip.instance().hide_tip()
        
        # Save window geometry
        self.settings_manager.save_window_geometry(self.saveGeometry())
        self.settings_manager.save_window_maximized(self.isMaximized())
        
        # Save individual position values — clamp to minimum before saving
        # to prevent undersized values from persisting across sessions
        if not self.isMaximized():
            geo = self.geometry()
            self.settings_manager.save_window_position(
                geo.x(),
                geo.y(),
                max(geo.width(), MIN_WINDOW_WIDTH),
                max(geo.height(), MIN_WINDOW_HEIGHT)
            )
        
        # Ensure settings are written to disk
        self.settings_manager.sync()
        
        # Cancel and wait for any running threads
        if self._file_loader_thread is not None:
            self._file_loader_thread.cancel()
            self._file_loader_thread.wait(1000)  # Wait up to 1 second
        
        if self._transform_thread is not None:
            self._transform_thread.cancel()
            self._transform_thread.wait(1000)
        
        super().closeEvent(event)
    
    # ==================== APPLICATION FUNCTIONS ====================
    
    def _set_buttons_enabled(self, enabled: bool) -> None:
        """
        Enable or disable action buttons during async operations.
        
        In image mode, we only use the _is_loading flag to prevent clicks
        (avoids Qt's disabled icon graying effect that causes visual flash).
        In text modes, we also call setEnabled() for visual feedback.
        """
        self._is_loading = not enabled
        
        # In image mode, skip setEnabled to avoid icon graying flash
        # The _is_loading flag will still block operations
        if not self.theme_manager.is_image_mode():
            for btn in self.all_buttons:
                btn.setEnabled(enabled)
    
    def _handle_dropped_file(self, file_path: str) -> None:
        """Handle file dropped on input text area (async)."""
        if self._is_loading:
            return  # Ignore if already loading
        
        self._set_status("Loading file...")
        self._set_buttons_enabled(False)
        
        # Clean up any previous thread
        if self._file_loader_thread is not None:
            self._file_loader_thread.cancel()
            self._file_loader_thread.wait()
        
        self._file_loader_thread = FileLoaderThread(file_path)
        self._file_loader_thread.finished.connect(self._on_file_loaded_dragdrop)
        self._file_loader_thread.error.connect(self._on_file_error)
        self._file_loader_thread.start()
        
        # Add to recent files
        self.settings_manager.add_recent_file(file_path)
    
    def _on_file_loaded_dragdrop(self, content: str, filename: str) -> None:
        """Handle successful drag-drop file load."""
        self.text_input.setPlainText(content)
        self._set_status(f"Loaded via drag & drop: {filename}")
        self.text_input.restore_original_style()
        self._set_buttons_enabled(True)
        self._transform_text()
    
    def _transform_text(self) -> None:
        """Transform the input text based on selected mode (async for large text)."""
        # Skip if already loading (image mode buttons aren't disabled)
        if self._is_loading:
            return
        
        text = self.text_input.toPlainText()
        mode = self.mode_combo.currentText()
        
        # Use background thread for large text
        if should_use_thread_for_transform(text):
            self._set_status("Transforming large text...")
            self._set_buttons_enabled(False)
            
            # Clean up any previous thread
            if self._transform_thread is not None:
                self._transform_thread.cancel()
                self._transform_thread.wait()
            
            self._transform_thread = TextTransformThread(text, mode)
            self._transform_thread.finished.connect(self._on_transform_complete)
            self._transform_thread.error.connect(self._on_transform_error)
            self._transform_thread.start()
        else:
            # Small text - transform synchronously
            result = TextTransformer.transform_text(text, mode)
            self.output_text.setPlainText(result)
            self._add_to_output_history(result)  # Track for undo/redo
            self._update_statistics()
            self._set_status("Text transformed!")
    
    def _on_transform_complete(self, result: str) -> None:
        """Handle successful text transformation."""
        self.output_text.setPlainText(result)
        self._add_to_output_history(result)  # Track for undo/redo
        self._update_statistics()
        self._set_status("Text transformed!")
        self._set_buttons_enabled(True)
    
    def _on_transform_error(self, error_msg: str) -> None:
        """Handle text transformation error."""
        self._set_status(f"Transform error: {error_msg}")
        self._set_buttons_enabled(True)
    
    def _copy_to_clipboard(self) -> None:
        """Copy output text to clipboard."""
        # Skip if loading in progress (image mode buttons aren't disabled)
        if self._is_loading:
            return
        
        text = self.output_text.toPlainText()
        if ClipboardUtils.copy_to_clipboard(text):
            self._set_status("Copied to clipboard!")
        else:
            self._set_status("Nothing to copy!")
    
    def _load_file(self) -> None:
        """Load text from file - supports multiple formats (async)."""
        if self._is_loading:
            return  # Ignore if already loading
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Text File", "", FILE_DIALOG_FILTER
        )
        if file_path:
            self._set_status("Loading file...")
            self._set_buttons_enabled(False)
            
            # Clean up any previous thread
            if self._file_loader_thread is not None:
                self._file_loader_thread.cancel()
                self._file_loader_thread.wait()
            
            self._file_loader_thread = FileLoaderThread(file_path)
            self._file_loader_thread.finished.connect(self._on_file_loaded)
            self._file_loader_thread.error.connect(self._on_file_error)
            self._file_loader_thread.start()
            
            # Add to recent files
            self.settings_manager.add_recent_file(file_path)
    
    def _on_file_loaded(self, content: str, filename: str) -> None:
        """Handle successful file load."""
        self.text_input.setPlainText(content)
        self._set_status(f"File loaded: {filename}")
        self._set_buttons_enabled(True)
        self._transform_text()
    
    def _on_file_error(self, error_msg: str) -> None:
        """Handle file loading error."""
        self._set_status(f"Error: {error_msg}")
        self._set_buttons_enabled(True)
    
    def _save_file(self) -> None:
        """Save output text to file."""
        # Skip if loading in progress (image mode buttons aren't disabled)
        if self._is_loading:
            return
        
        text = self.output_text.toPlainText()
        if not text:
            self._set_status("Nothing to save!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Text File", "", SAVE_FILE_FILTER
        )
        if file_path:
            try:
                FileHandler.write_text_file(file_path, text)
                self._set_status("File saved")
            except Exception as e:
                self._set_status(f"Error: {e}")
    
    def _clear_all(self) -> None:
        """Clear both input and output text areas."""
        if self._is_loading:
            return
        
        self.text_input.clear()
        self.output_text.clear()
        self._clear_output_history()
        self._update_statistics()
        self._set_status("Cleared all text")
    
    def _clear_input(self) -> None:
        """Clear only the input text area (from context menu)."""
        if self._is_loading:
            return
        
        self.text_input.clear()
        self._update_statistics()
        self._set_status("Cleared input")
    
    def _swap_input_output(self) -> None:
        """Swap input and output text for chained transformations."""
        if self._is_loading:
            return
        
        output_text = self.output_text.toPlainText()
        
        if not output_text:
            self._set_status("Nothing to swap!")
            return
        
        self.text_input.setPlainText(output_text)
        self.output_text.clear()
        self._clear_output_history()
        self._update_statistics()
        self._set_status("Swapped input and output")
    
    # ==================== OUTPUT HISTORY (UNDO/REDO) ====================
    
    def _add_to_output_history(self, text: str) -> None:
        """
        Add current output state to history for undo/redo.
        
        Args:
            text: Output text to save in history
        """
        # If we're not at the end of history, truncate future states
        if self._output_history_index < len(self._output_history) - 1:
            self._output_history = self._output_history[:self._output_history_index + 1]
        
        # Don't add duplicate consecutive states
        if self._output_history and self._output_history[-1] == text:
            return
        
        # Add new state
        self._output_history.append(text)
        
        # Trim to max size
        if len(self._output_history) > MAX_OUTPUT_HISTORY:
            self._output_history = self._output_history[-MAX_OUTPUT_HISTORY:]
        
        # Update index to point to current state
        self._output_history_index = len(self._output_history) - 1
    
    def _clear_output_history(self) -> None:
        """Clear the output history."""
        self._output_history.clear()
        self._output_history_index = -1
    
    def _undo_output(self) -> None:
        """Undo last output transformation."""
        if self._output_history_index > 0:
            self._output_history_index -= 1
            text = self._output_history[self._output_history_index]
            self.output_text.setPlainText(text)
            self._update_statistics()
            self._set_status(f"Undo ({self._output_history_index + 1}/{len(self._output_history)})")
        elif self._output_history_index == 0 and self._output_history:
            # At first state, undo to empty
            self._output_history_index = -1
            self.output_text.clear()
            self._update_statistics()
            self._set_status("Undo (cleared)")
        else:
            self._set_status("Nothing to undo")
    
    def _redo_output(self) -> None:
        """Redo output transformation."""
        if self._output_history_index < len(self._output_history) - 1:
            self._output_history_index += 1
            text = self._output_history[self._output_history_index]
            self.output_text.setPlainText(text)
            self._update_statistics()
            self._set_status(f"Redo ({self._output_history_index + 1}/{len(self._output_history)})")
        else:
            self._set_status("Nothing to redo")
    
    # ==================== RECENT FILES ====================
    
    def _add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.
        
        Args:
            file_path: Path to the file that was opened
        """
        max_files = self.settings_manager.load_recent_files_max()
        if max_files > 0:
            self.settings_manager.add_recent_file(file_path, max_files)
    
    def _open_recent_file(self, file_path: str) -> None:
        """
        Open a file from the recent files list.
        
        Args:
            file_path: Path to the file to open
        """
        if self._is_loading:
            return
        
        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            self._set_status(f"File not found: {path.name}")
            # Remove from recent files
            files = self.settings_manager.load_recent_files()
            if file_path in files:
                files.remove(file_path)
                self.settings_manager.save_recent_files(files)
            return
        
        # Load the file
        self._set_status("Loading file...")
        self._set_buttons_enabled(False)
        
        # Clean up any previous thread
        if self._file_loader_thread is not None:
            self._file_loader_thread.cancel()
            self._file_loader_thread.wait()
        
        self._file_loader_thread = FileLoaderThread(file_path)
        self._file_loader_thread.finished.connect(self._on_file_loaded)
        self._file_loader_thread.error.connect(self._on_file_error)
        self._file_loader_thread.start()
    
    # ==================== TEXT CLEANUP & SPLIT/JOIN ====================
    
    def _apply_cleanup(self, operation: str) -> None:
        """
        Apply a text cleanup operation to the input text.
        
        Args:
            operation: Name of the cleanup operation to apply
        """
        from core.text_cleaner import TextCleaner
        
        text = self.text_input.toPlainText()
        if not text:
            self._set_status("No text to clean!")
            return
        
        # Apply cleanup operation
        result = TextCleaner.cleanup(text, operation)
        
        # Update input text with cleaned result
        self.text_input.setPlainText(result)
        
        # Auto-transform if enabled
        if self.settings_manager.load_auto_transform():
            self._transform_text()
        
        self._set_status(f"Applied: {operation}")
    
    def _apply_split_join(self, operation: str) -> None:
        """
        Apply a split/join operation to the input text.
        
        Args:
            operation: Name of the split/join operation to apply
        """
        from core.text_cleaner import TextCleaner
        
        text = self.text_input.toPlainText()
        if not text:
            self._set_status("No text to process!")
            return
        
        # Apply split/join operation
        result = TextCleaner.split_join(text, operation)
        
        # Update input text with result
        self.text_input.setPlainText(result)
        
        # Auto-transform if enabled
        if self.settings_manager.load_auto_transform():
            self._transform_text()
        
        self._set_status(f"Applied: {operation}")
    
    def _show_recent_files_menu(self) -> None:
        """Show recent files popup menu."""
        recent_files = self.settings_manager.load_recent_files()
        
        if not recent_files:
            self._set_status("No recent files")
            return
        
        menu = QMenu(self)
        is_dark = self.theme_manager.is_dark_mode
        menu.setStyleSheet(DialogStyleManager.get_menu_stylesheet(is_dark))
        
        for file_path in recent_files:
            path = Path(file_path)
            # Show just filename, full path in tooltip
            action = QAction(path.name, self)
            action.setToolTip(file_path)
            action.triggered.connect(lambda checked, fp=file_path: self._open_recent_file(fp))
            menu.addAction(action)
        
        menu.addSeparator()
        
        # Clear recent files option
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        menu.addAction(clear_action)
        
        # Show menu at load button position
        menu.exec(self.load_btn.mapToGlobal(self.load_btn.rect().bottomLeft()))
    
    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.settings_manager.clear_recent_files()
        self._set_status("Recent files cleared")
    
    # ==================== ADVANCED FEATURES ====================
    
    def _open_find_dialog(self) -> None:
        """Open Find dialog."""
        dialog = FindReplaceDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            target_text_edit=self.text_input,
            replace_mode=False,
            parent=self
        )
        dialog.show()
    
    def _open_replace_dialog(self) -> None:
        """Open Find & Replace dialog."""
        dialog = FindReplaceDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            target_text_edit=self.text_input,
            replace_mode=True,
            parent=self
        )
        dialog.show()
    
    def _open_batch_dialog(self) -> None:
        """Open Batch Processing dialog."""
        dialog = BatchDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            parent=self
        )
        dialog.exec()
    
    def _open_compare_dialog(self) -> None:
        """Open Compare & Merge dialog."""
        input_text = self.text_input.toPlainText()
        output_text = self.output_text.toPlainText()
        
        if not input_text and not output_text:
            self._set_status("Nothing to compare")
            return
        
        dialog = CompareDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            input_text=input_text,
            output_text=output_text,
            parent=self
        )
        
        # Connect merge_applied signal to update output
        dialog.merge_applied.connect(self._on_merge_applied)
        
        # Track the open non-modal dialog so theme changes can be propagated
        # to it. Clear the reference when the dialog closes (X button calls
        # reject() → finished; Apply Merge calls accept() → finished).
        self._compare_dialog = dialog
        dialog.finished.connect(self._on_compare_dialog_closed)
        
        dialog.show()
    
    def _on_compare_dialog_closed(self, _result: int = 0) -> None:
        """Clear the compare dialog reference when it closes."""
        self._compare_dialog = None
    
    def _refresh_open_dialogs_theme(self) -> None:
        """
        Propagate the current theme to any open non-modal dialog.
        
        Called whenever the application theme changes (via Ctrl+Shift+T or
        from the settings dialog). The compare dialog is the only non-modal
        one — modal dialogs cannot be open during a theme cycle so they
        don't need this. Wrapped defensively in case the Qt object was
        destroyed without the finished signal firing.
        """
        compare_dialog = getattr(self, '_compare_dialog', None)
        if compare_dialog is not None:
            try:
                compare_dialog.refresh_theme()
            except RuntimeError:
                self._compare_dialog = None
    
    def _on_merge_applied(self, merged_text: str) -> None:
        """Handle merged text from Compare & Merge dialog."""
        self.output_text.setPlainText(merged_text)
        self._add_to_output_history(merged_text)
        self._update_statistics()
        self._set_status("Merge applied to output")
    
    def _open_export_dialog(self) -> None:
        """Open Export dialog for multi-format export."""
        output_text = self.output_text.toPlainText()
        
        if not output_text:
            self._set_status("Nothing to export")
            return
        
        dialog = ExportDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            text_content=output_text,
            parent=self
        )
        
        # Connect signals
        dialog.export_completed.connect(self._on_export_completed)
        dialog.export_failed.connect(self._on_export_failed)
        
        dialog.exec()
    
    def _on_export_completed(self, file_path: str) -> None:
        """Handle successful export."""
        from pathlib import Path
        filename = Path(file_path).name
        self._set_status(f"Exported: {filename}")
    
    def _on_export_failed(self, error_msg: str) -> None:
        """Handle export failure."""
        self._set_status(f"Export failed: {error_msg}")
    
    def _open_encoding_dialog(self) -> None:
        """Open Encoding Converter dialog."""
        input_text = self.text_input.toPlainText()
        
        dialog = EncodingDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            input_text=input_text,
            parent=self
        )
        
        # Connect conversion signal
        dialog.encoding_applied.connect(self._on_encoding_conversion_applied)
        
        dialog.exec()
    
    def _on_encoding_conversion_applied(self, converted_text: str) -> None:
        """Handle encoding conversion applied."""
        self.text_input.setPlainText(converted_text)
        self._set_status("Encoding conversion applied")
        self._transform_text()
    
    def _open_regex_builder_dialog(self) -> None:
        """Open Regex Builder dialog."""
        input_text = self.text_input.toPlainText()
        
        dialog = RegexBuilderDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            input_text=input_text,
            parent=self
        )
        
        # Connect pattern applied signal
        dialog.pattern_applied.connect(self._on_regex_pattern_applied)
        
        dialog.show()
    
    def _on_regex_pattern_applied(self, pattern: str, replacement: str, flags: int) -> None:
        """Handle regex pattern applied from builder."""
        import re
        
        text = self.text_input.toPlainText()
        
        if replacement:
            # Replace all matches
            try:
                result = re.sub(pattern, replacement, text, flags=flags)
                self.text_input.setPlainText(result)
                self._set_status("Regex replacement applied")
                self._transform_text()
            except re.error as e:
                self._set_status(f"Regex error: {e}")
        else:
            # Just highlight - open find dialog with pattern
            dialog = FindReplaceDialog(
                theme_manager=self.theme_manager,
                font_family=self.font_family,
                target_text_edit=self.text_input,
                replace_mode=False,
                parent=self
            )
            dialog.find_input.setText(pattern)
            dialog.regex_check.setChecked(True)
            dialog.show()
    
    # ==================== PRESET SYSTEM ====================
    
    def _open_preset_manager_dialog(self) -> None:
        """Open Preset Manager dialog."""
        dialog = PresetManagerDialog(
            theme_manager=self.theme_manager,
            preset_manager=self.preset_manager,
            font_family=self.font_family,
            parent=self
        )
        
        # Connect preset selection signal (emits preset name)
        dialog.preset_selected.connect(self._apply_preset_by_name)
        
        dialog.exec()
    
    def _open_preset_editor_dialog(self, preset: TransformPreset | None = None) -> None:
        """
        Open Preset Editor dialog to create or edit a preset.
        
        Args:
            preset: Existing preset to edit, or None for new preset
        """
        dialog = PresetDialog(
            theme_manager=self.theme_manager,
            preset_manager=self.preset_manager,
            font_family=self.font_family,
            preset=preset,
            parent=self
        )
        
        # Connect apply signal (emits preset name)
        dialog.preset_applied.connect(self._apply_preset_by_name)
        
        dialog.exec()
    
    def _apply_preset(self, preset: TransformPreset) -> None:
        """
        Apply a preset to the current input text.
        
        Args:
            preset: The preset to apply
        """
        if self._is_loading:
            return
        
        text = self.text_input.toPlainText()
        
        if not text:
            self._set_status("No text to transform")
            return
        
        try:
            # Execute the preset (text first, then preset)
            result, applied_steps = self.preset_executor.execute_preset(text, preset)
            
            # Update output
            self.output_text.setPlainText(result)
            self._add_to_output_history(result)
            self._update_statistics()
            
            # Show status
            step_count = len(applied_steps)
            self._set_status(f"Preset '{preset.name}' applied ({step_count} steps)")
            
        except Exception as e:
            self._set_status(f"Preset error: {e}")
    
    def _apply_preset_by_name(self, preset_name: str) -> None:
        """
        Apply a preset by its name.
        
        Args:
            preset_name: Name of the preset to apply
        """
        preset = self.preset_manager.get_preset(preset_name)
        if preset:
            self._apply_preset(preset)
        else:
            self._set_status(f"Preset not found: {preset_name}")
    
    # ==================== WATCH FOLDER ====================
    
    def _open_watch_folder_dialog(self) -> None:
        """Open Watch Folder dialog for automatic file transformation."""
        dialog = WatchFolderDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            parent=self
        )
        dialog.show()
    
    # ==================== ABOUT DIALOG ====================
    
    def _open_about_dialog(self) -> None:
        """Open standalone About dialog."""
        dialog = AboutDialog(
            theme_manager=self.theme_manager,
            font_family=self.font_family,
            parent=self
        )
        dialog.exec()

    def _set_status(self, msg: str) -> None:
        """Set status message that auto-clears after timeout."""
        self.status_label.setText(msg)
        self.status_timer.start(STATUS_CLEAR_TIMEOUT)
    
    def _clear_status(self) -> None:
        """Clear status message."""
        self.status_label.setText("")
        self.status_timer.stop()