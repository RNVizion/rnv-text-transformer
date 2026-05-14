"""
RNV Text Transformer - About Dialog Module
Standalone application information and help dialog

Accessible via Ctrl+/ keyboard shortcut

Displays:
- Application name, version, description
- Feature list
- Keyboard shortcuts reference
- System information
- Credits

Python 3.13 Optimized:
- Modern type hints
- Clean separation of concerns
- Theme-aware styling

"""

from __future__ import annotations

import sys
import os
from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("AboutDialog")
except ImportError:
    logger = None

# Import config for app info
try:
    from utils.config import APP_NAME, APP_VERSION, BASE_DIR
except ImportError:
    APP_NAME = "RNV Text Transformer"
    APP_VERSION = ""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.dialog_styles import DialogStyleManager
except ImportError:
    DialogStyleManager = None  # type: ignore[assignment]


class AboutDialog(QDialog):
    """
    About dialog with application information, features, and keyboard shortcuts.
    
    Features:
    - Tabbed interface: About, Features, Shortcuts, Credits
    - App icon and version display
    - System information
    - Full keyboard shortcuts reference
    - Theme-aware styling (dark/light)
    """
    
    # Dialog dimensions
    _DIALOG_WIDTH: ClassVar[int] = 520
    _DIALOG_HEIGHT: ClassVar[int] = 680
    
    __slots__ = ('_is_dark', 'tabs', 'font_family', 'theme_manager')
    
    def __init__(
        self, 
        theme_manager: ThemeManager | None = None,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize About dialog.
        
        Args:
            theme_manager: Theme manager for styling
            font_family: Font family to use
            parent: Parent widget (not passed to super to avoid stylesheet inheritance)
        """
        # Don't pass parent to avoid stylesheet inheritance issues
        super().__init__(None)
        
        self.theme_manager = theme_manager
        self.font_family = font_family
        self._is_dark = self._detect_theme()
        
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        
        # Set window icon
        icon_path = os.path.join(BASE_DIR, "resources", "icons", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.MSWindowsFixedSizeDialogHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setFixedSize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)
        
        self._build_ui()
        self._apply_theme()
        
        if logger:
            logger.success("About dialog initialized")
    
    def _detect_theme(self) -> bool:
        """Detect if dark theme is active."""
        if self.theme_manager:
            return self.theme_manager.current_theme in ('dark', 'image')
        return True  # Default to dark
    
    def _build_ui(self) -> None:
        """Build the about dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header section with app name and version
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab widget for organized content
        self.tabs = QTabWidget()
        
        # Create tabs
        about_tab = self._create_about_tab()
        features_tab = self._create_features_tab()
        shortcuts_tab = self._create_shortcuts_tab()
        credits_tab = self._create_credits_tab()
        
        self.tabs.addTab(about_tab, "About")
        self.tabs.addTab(features_tab, "Features")
        self.tabs.addTab(shortcuts_tab, "Shortcuts")
        self.tabs.addTab(credits_tab, "Credits")
        
        layout.addWidget(self.tabs, 1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 35)
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header(self) -> QWidget:
        """Create the header section with app name and logo."""
        header = QFrame()
        header.setObjectName("header_frame")
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        # App icon (if available)
        icon_label = QLabel()
        icon_label.setStyleSheet("border: none; background: transparent;")
        icon_path = os.path.join(BASE_DIR, "resources", "icons", "icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    64, 64, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
        icon_label.setFixedSize(70, 70)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # App name and version
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        name_label = QLabel(APP_NAME)
        name_label.setStyleSheet("font-size: 24px; font-weight: bold; border: none; background: transparent;")
        text_layout.addWidget(name_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        _accent = DialogStyleManager.get_colors(self._is_dark)['accent']
        version_label.setStyleSheet(f"font-size: 14px; color: {_accent}; border: none; background: transparent;")
        text_layout.addWidget(version_label)
        
        desc_label = QLabel("Professional Text Transformation Application")
        desc_label.setStyleSheet("font-size: 12px; border: none; background: transparent;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        text_layout.addStretch()
        header_layout.addLayout(text_layout, 1)
        
        return header
    
    def _create_about_tab(self) -> QWidget:
        """Create the About tab with application description."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Get system info
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            qt_version = QT_VERSION_STR
            pyqt_version = PYQT_VERSION_STR
        except ImportError:
            qt_version = "Unknown"
            pyqt_version = "Unknown"
        
        desc_text = f"""
<h3>Professional Text Transformation Application</h3>

<p>RNV Text Transformer is a desktop application for transforming text between 
different case formats and styles. Built with Python and PyQt6, it provides 
a professional interface for text manipulation, file processing, and batch 
operations.</p>

<h4>Core Capabilities:</h4>
<ul>
<li><b>Multiple Transform Modes</b> - 15+ text transformation styles</li>
<li><b>File Support</b> - TXT, DOCX, PDF, RTF, MD, and code files</li>
<li><b>Batch Processing</b> - Transform multiple files at once</li>
<li><b>Regex Builder</b> - Visual regex pattern construction</li>
<li><b>Text Cleanup</b> - Remove whitespace, normalize, deduplicate</li>
<li><b>Export Options</b> - Multiple formats including clipboard</li>
<li><b>Watch Folders</b> - Auto-transform files in monitored directories</li>
</ul>

<h4>System Information:</h4>
<table>
<tr><td><b>Python:</b></td><td>{python_version}</td></tr>
<tr><td><b>PyQt6:</b></td><td>{pyqt_version}</td></tr>
<tr><td><b>Qt:</b></td><td>{qt_version}</td></tr>
<tr><td><b>Platform:</b></td><td>{sys.platform}</td></tr>
</table>
"""
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.TextFormat.RichText)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(desc_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_features_tab(self) -> QWidget:
        """Create the Features tab with feature list."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        features_text = """
<h3>Feature Overview</h3>

<h4>📝 Text Transformation</h4>
<ul>
<li><b>Case Modes</b> - UPPERCASE, lowercase, Title Case, Sentence case</li>
<li><b>Developer Modes</b> - camelCase, PascalCase, snake_case, kebab-case</li>
<li><b>Special Modes</b> - CONSTANT_CASE, dot.case, Alternating Case, Reverse</li>
<li><b>Real-time Preview</b> - See transformation results instantly</li>
<li><b>Auto-transform</b> - Automatic transformation on input change</li>
</ul>

<h4>📁 File Operations</h4>
<ul>
<li><b>Multi-format Support</b> - TXT, MD, DOCX, PDF, RTF, PY, JS, HTML, LOG</li>
<li><b>Drag & Drop</b> - Load files by dropping them on the input area</li>
<li><b>Recent Files</b> - Quick access to recently opened files</li>
<li><b>Batch Processing</b> - Transform entire folders of files</li>
<li><b>Watch Folders</b> - Monitor directories for automatic processing</li>
</ul>

<h4>🔧 Text Cleanup</h4>
<ul>
<li><b>Whitespace Tools</b> - Trim, normalize spaces, remove blank lines</li>
<li><b>Line Operations</b> - Sort, reverse, deduplicate, number lines</li>
<li><b>Character Cleanup</b> - Remove special chars, fix encoding</li>
<li><b>Split/Join</b> - Split text or join lines with custom separators</li>
</ul>

<h4>🔍 Find & Replace</h4>
<ul>
<li><b>Basic Search</b> - Find text with highlighting</li>
<li><b>Regex Support</b> - Full regular expression patterns</li>
<li><b>Replace Options</b> - Single or replace all occurrences</li>
<li><b>Case Sensitivity</b> - Optional case-sensitive matching</li>
</ul>

<h4>📊 Advanced Features</h4>
<ul>
<li><b>Regex Builder</b> - Visual pattern construction with testing</li>
<li><b>Transform Presets</b> - Save and reuse custom configurations</li>
<li><b>Compare View</b> - Side-by-side diff with highlighting</li>
<li><b>Multi-format Export</b> - Export to various formats</li>
<li><b>Encoding Detection</b> - Handle different text encodings</li>
</ul>

<h4>🎨 Themes</h4>
<ul>
<li><b>Dark Mode</b> - Easy on the eyes for long sessions</li>
<li><b>Light Mode</b> - High contrast for bright environments</li>
<li><b>Image Mode</b> - Custom button graphics and backgrounds</li>
</ul>
"""
        
        features_label = QLabel(features_text)
        features_label.setWordWrap(True)
        features_label.setTextFormat(Qt.TextFormat.RichText)
        features_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(features_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_shortcuts_tab(self) -> QWidget:
        """Create the Shortcuts tab with keyboard shortcuts reference."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>

<h4>File Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+O</b></td><td>Open/Load File</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save Output to File</td></tr>
<tr><td><b>Ctrl+Shift+O</b></td><td>Recent Files Menu</td></tr>
<tr><td><b>Ctrl+E</b></td><td>Export Dialog</td></tr>
</table>

<h4>Text Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+T</b></td><td>Transform Text</td></tr>
<tr><td><b>Ctrl+Shift+C</b></td><td>Copy Output to Clipboard</td></tr>
<tr><td><b>Ctrl+Shift+X</b></td><td>Clear All Text</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Swap Input/Output</td></tr>
<tr><td><b>Ctrl+Z</b></td><td>Undo Output</td></tr>
<tr><td><b>Ctrl+Y</b></td><td>Redo Output</td></tr>
</table>

<h4>Search & Replace</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+F</b></td><td>Find Dialog</td></tr>
<tr><td><b>Ctrl+H</b></td><td>Find & Replace Dialog</td></tr>
<tr><td><b>Ctrl+R</b></td><td>Regex Builder</td></tr>
</table>

<h4>Advanced Features</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+B</b></td><td>Batch Processing</td></tr>
<tr><td><b>Ctrl+D</b></td><td>Compare View</td></tr>
<tr><td><b>Ctrl+P</b></td><td>Preset Manager</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Watch Folder Dialog</td></tr>
<tr><td><b>Ctrl+Shift+E</b></td><td>Encoding Dialog</td></tr>
</table>

<h4>Application</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+,</b></td><td>Open Settings & Features Panel</td></tr>
<tr><td><b>Ctrl+/</b></td><td>Open About Dialog (This Window)</td></tr>
<tr><td><b>Ctrl+Shift+T</b></td><td>Cycle Theme</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit Application</td></tr>
</table>

<h4>Debug & Display</h4>
<table width="100%">
<tr><td width="40%"><b>F11</b></td><td>Toggle Tooltips On/Off</td></tr>
<tr><td><b>F12</b></td><td>Toggle Debug Mode</td></tr>
</table>
"""
        
        shortcuts_label = QLabel(shortcuts_text)
        shortcuts_label.setWordWrap(True)
        shortcuts_label.setTextFormat(Qt.TextFormat.RichText)
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(shortcuts_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_credits_tab(self) -> QWidget:
        """Create the Credits tab with acknowledgments."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        _accent = DialogStyleManager.get_colors(self._is_dark)['accent']
        credits_text = f"""
<h3>Credits & Acknowledgments</h3>

<h4>Development</h4>
<p>RNV Text Transformer was created with passion for productivity tools 
and efficient text processing workflows.</p>

<h4>Technologies</h4>
<table width="100%">
<tr><td width="40%"><b>Framework</b></td><td>PyQt6</td></tr>
<tr><td><b>Language</b></td><td>Python 3.13</td></tr>
<tr><td><b>Image Processing</b></td><td>Pillow (PIL)</td></tr>
<tr><td><b>Document Support</b></td><td>python-docx, pypdf, striprtf</td></tr>
</table>

<h4>Design Philosophy</h4>
<ul>
<li><b>Modular Architecture</b> - Clean separation of core, UI, and utilities</li>
<li><b>Type Safety</b> - Modern Python type hints throughout</li>
<li><b>Performance</b> - Async operations for large files</li>
<li><b>Extensibility</b> - Plugin-ready transform modes</li>
</ul>

<h4>Special Thanks</h4>
<ul>
<li>The PyQt community for excellent documentation</li>
<li>Python Software Foundation</li>
<li>Open source contributors and maintainers</li>
<li>Beta testers and early adopters</li>
<li>Everyone who provided feedback and suggestions</li>
</ul>

<hr>

<p style="text-align: center; color: {_accent};">
<b>RNV Text Transformer</b><br>
One developer, one tool, built for anyone who spends their day wrangling text.<br><br>
\u00a9 2026 RNV Software
</p>
"""
        
        credits_label = QLabel(credits_text)
        credits_label.setWordWrap(True)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(credits_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def set_theme(self, is_dark: bool) -> None:
        """
        Set the dialog theme (dark or light).
        
        Args:
            is_dark: True for dark theme, False for light
        """
        self._is_dark = is_dark
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply the current theme to the dialog using DialogStyleManager colors."""
        c = DialogStyleManager.get_colors(self._is_dark)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['bg']};
                color: {c['text']};
                font-family: '{self.font_family}';
            }}
            QFrame {{
                background-color: {c['scrollbar_bg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QFrame#header_frame {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QTabWidget::pane {{
                background-color: {c['bg']};
                border: 1px solid {c['border']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {c['scrollbar_bg']};
                color: {c['text_muted']};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['bg']};
                color: {c['accent']};
                border-bottom: 2px solid {c['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c['bg_tertiary']};
                color: {c['accent']};
                border-bottom: 2px solid {c['accent_pressed']};
            }}
            QLabel {{
                color: {c['text']};
                background-color: transparent;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {c['scrollbar_bg']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {c['scrollbar_handle']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {c['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QPushButton {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border_light']};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                border-color: {c['accent']};
            }}
            QPushButton:pressed {{
                background-color: {c['accent']};
                color: {c['accent_text']};
            }}
        """)
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Clears pixmaps to free memory.
        """
        try:
            # Clear any pixmaps to free memory
            for child in self.findChildren(QLabel):
                pixmap = child.pixmap()
                if pixmap and not pixmap.isNull():
                    child.clear()
            
            if logger:
                logger.debug("AboutDialog cleanup complete")
                
        except Exception as e:
            if logger:
                logger.error(f"Error during AboutDialog cleanup: {e}")
    
    def closeEvent(self, event) -> None:
        """Handle dialog close - ensure cleanup runs."""
        self.cleanup()
        super().closeEvent(event)