"""
RNV Text Transformer - Drag Drop Text Edit Module
Custom QTextEdit widget with drag-and-drop file support and context menus

Python 3.13 Optimized:
- Modern type hints
- TYPE_CHECKING for forward references
- Improved event handling
- frozenset for O(1) extension lookup
- Custom context menus for input/output text areas
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QTextEdit, QApplication, QMenu
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

from utils.config import SUPPORTED_FORMATS
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QContextMenuEvent
    from core.theme_manager import ThemeManager


class DragDropTextEdit(QTextEdit):
    """
    Custom QTextEdit with drag-and-drop support for document files.
    
    Emits fileDropped signal when a supported file is dropped.
    Uses frozenset for O(1) extension checking.
    Provides custom context menus for input/output modes.
    """
    
    # Signal emitted when file is dropped
    fileDropped = pyqtSignal(str)
    
    # Signals for context menu actions
    loadFileRequested = pyqtSignal()
    saveFileRequested = pyqtSignal()
    clearRequested = pyqtSignal()
    
    # Drag highlight style
    _DRAG_HIGHLIGHT_STYLE: str = """
        QTextEdit {
            border: 2px dashed #BFd2bc93;
            background-color: #BFd2bc93;
            color: #000000;
            padding: 4px;
        }
    """
    
    __slots__ = ('_accepted_extensions', '_is_output_mode', '_theme_manager')
    
    def __init__(self, parent: QTextEdit | None = None) -> None:
        """
        Initialize DragDropTextEdit.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Use frozenset for O(1) lookup instead of list with O(n) any()
        self._accepted_extensions: frozenset[str] = frozenset(SUPPORTED_FORMATS['all'])
        self._is_output_mode: bool = False  # False = input, True = output
        self._theme_manager: ThemeManager | None = None

    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """
        Set the theme manager so context menus can be styled correctly.

        Args:
            theme_manager: Application ThemeManager instance
        """
        self._theme_manager = theme_manager
    
    def set_output_mode(self, is_output: bool) -> None:
        """
        Set whether this is an output text area (affects context menu).
        
        Args:
            is_output: True for output mode, False for input mode
        """
        self._is_output_mode = is_output
    
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """
        Show custom context menu.
        
        Args:
            event: QContextMenuEvent
        """
        menu = QMenu(self)

        # Apply themed stylesheet so menu respects dark/light mode
        if self._theme_manager is not None:
            is_dark = self._theme_manager.is_dark_mode
            menu.setStyleSheet(DialogStyleManager.get_menu_stylesheet(is_dark))
        
        # Get clipboard for paste availability check
        clipboard = QApplication.clipboard()
        has_clipboard = clipboard is not None and bool(clipboard.text())
        has_selection = self.textCursor().hasSelection()
        has_text = bool(self.toPlainText())
        
        if self._is_output_mode:
            # Output text area menu
            self._create_output_context_menu(menu, has_selection, has_text)
        else:
            # Input text area menu
            self._create_input_context_menu(menu, has_selection, has_text, has_clipboard)
        
        menu.exec(event.globalPos())
    
    def _create_input_context_menu(
        self, 
        menu: QMenu, 
        has_selection: bool, 
        has_text: bool,
        has_clipboard: bool
    ) -> None:
        """
        Create context menu for input text area.
        
        Args:
            menu: QMenu to populate
            has_selection: Whether text is selected
            has_text: Whether text area has content
            has_clipboard: Whether clipboard has text
        """
        # Cut
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(has_selection)
        menu.addAction(cut_action)
        
        # Copy
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(has_selection)
        menu.addAction(copy_action)
        
        # Paste
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        paste_action.setEnabled(has_clipboard)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # Select All
        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.selectAll)
        select_all_action.setEnabled(has_text)
        menu.addAction(select_all_action)
        
        # Clear
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._on_clear)
        clear_action.setEnabled(has_text)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        # Load File
        load_action = QAction("Load File...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.loadFileRequested.emit)
        menu.addAction(load_action)
    
    def _create_output_context_menu(
        self, 
        menu: QMenu, 
        has_selection: bool, 
        has_text: bool
    ) -> None:
        """
        Create context menu for output text area.
        
        Args:
            menu: QMenu to populate
            has_selection: Whether text is selected
            has_text: Whether text area has content
        """
        # Copy (selection)
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(has_selection)
        menu.addAction(copy_action)
        
        # Copy All
        copy_all_action = QAction("Copy All", self)
        copy_all_action.setShortcut("Ctrl+Shift+C")
        copy_all_action.triggered.connect(self._copy_all)
        copy_all_action.setEnabled(has_text)
        menu.addAction(copy_all_action)
        
        menu.addSeparator()
        
        # Select All
        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.selectAll)
        select_all_action.setEnabled(has_text)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # Save As
        save_action = QAction("Save As...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.saveFileRequested.emit)
        save_action.setEnabled(has_text)
        menu.addAction(save_action)
    
    def _on_clear(self) -> None:
        """Handle clear action - emit signal for parent to handle."""
        self.clearRequested.emit()
    
    def _copy_all(self) -> None:
        """Copy all text to clipboard."""
        text = self.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handle drag enter event.
        
        Accepts drag if file has supported extension.
        
        Args:
            event: QDragEnterEvent
        """
        mime_data = event.mimeData()
        if mime_data is not None and mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_supported_file(file_path):
                    event.acceptProposedAction()
                    # Visual feedback - highlight this text area
                    self.setStyleSheet(self._DRAG_HIGHLIGHT_STYLE)
                    return
        
        event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """
        Handle drag leave event.
        
        Restores original styling.
        
        Args:
            event: QDragLeaveEvent
        """
        self.restore_original_style()
        self.update()
        QApplication.processEvents()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handle drop event.
        
        Emits fileDropped signal if file is supported.
        
        Args:
            event: QDropEvent
        """
        mime_data = event.mimeData()
        if mime_data is not None and mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                
                if self._is_supported_file(file_path):
                    event.acceptProposedAction()
                    self.restore_original_style()
                    self.update()
                    QApplication.processEvents()
                    self.fileDropped.emit(file_path)
                    return
        
        self.restore_original_style()
        self.update()
        QApplication.processEvents()
        event.ignore()
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        Check if file has supported extension using O(1) set lookup.
        
        Args:
            file_path: File path (case insensitive)
            
        Returns:
            True if file extension is supported
        """
        # Extract extension using pathlib (handles edge cases)
        ext = Path(file_path).suffix.lower()
        return ext in self._accepted_extensions
    
    def restore_original_style(self) -> None:
        """Restore the original stylesheet - force reapply from theme."""
        # Clear inline stylesheet
        self.setStyleSheet("")
        # Force Qt to reprocess and reapply parent stylesheet
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()