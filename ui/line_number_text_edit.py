"""
RNV Text Transformer - Line Number Text Edit Module
Custom QPlainTextEdit widget with line number gutter

Python 3.13 Optimized:
- Modern type hints
- Efficient line number rendering
- Theme-aware styling
- Current line highlighting
- Toggle visibility

"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QPaintEvent, QResizeEvent,
    QFont, QTextCursor
)

if TYPE_CHECKING:
    from PyQt6.QtCore import QRectF

from utils.dialog_styles import DialogStyleManager


class LineNumberArea(QWidget):
    """
    Widget that displays line numbers in a gutter alongside QPlainTextEdit.
    
    Designed to be used as a child widget of LineNumberTextEdit.
    """
    
    __slots__ = ('editor',)
    
    def __init__(self, editor: 'LineNumberTextEdit') -> None:
        """
        Initialize line number area.
        
        Args:
            editor: Parent LineNumberTextEdit
        """
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self) -> QSize:
        """Return size hint for the line number area."""
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint line numbers."""
        self.editor.line_number_area_paint_event(event)


class LineNumberTextEdit(QPlainTextEdit):
    """
    QPlainTextEdit with line number gutter and current line highlighting.
    
    Features:
    - Line numbers gutter (toggleable)
    - Current line highlighting
    - Theme-aware colors
    - Synchronized scrolling
    - Compatible with DragDropTextEdit functionality
    """
    
    # Theme colors sourced from DialogStyleManager — no hardcoded hex
    # Keys used: line_number_bg, line_number_fg, line_number_current_bg, line_number_current_fg
    
    # Padding for line number area
    _LINE_NUMBER_PADDING: ClassVar[int] = 10
    
    # Signal emitted when text changes
    textModified = pyqtSignal()
    
    __slots__ = (
        '_line_number_area', '_show_line_numbers', '_highlight_current_line',
        '_line_number_bg', '_line_number_fg', '_current_line_bg',
        '_current_line_number_fg', '_is_dark_theme'
    )
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize LineNumberTextEdit.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize state
        self._show_line_numbers: bool = True
        self._highlight_current_line: bool = True
        self._is_dark_theme: bool = True
        
        # Set colors for dark theme by default — sourced from DialogStyleManager
        _dark = DialogStyleManager.DARK
        self._line_number_bg = QColor(_dark['line_number_bg'])
        self._line_number_fg = QColor(_dark['line_number_fg'])
        self._current_line_bg = QColor(_dark['line_number_current_bg'])
        self._current_line_number_fg = QColor(_dark['line_number_current_fg'])
        
        # Create line number area
        self._line_number_area = LineNumberArea(self)
        
        # Connect signals
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line_slot)
        
        # Initialize
        self._update_line_number_area_width(0)
        self._highlight_current_line_slot()
    
    def set_show_line_numbers(self, show: bool) -> None:
        """
        Toggle line number visibility.
        
        Args:
            show: True to show line numbers, False to hide
        """
        self._show_line_numbers = show
        self._update_line_number_area_width(0)
        self._line_number_area.setVisible(show)
        self.update()
    
    def get_show_line_numbers(self) -> bool:
        """Get current line number visibility state."""
        return self._show_line_numbers
    
    def set_highlight_current_line(self, highlight: bool) -> None:
        """
        Toggle current line highlighting.
        
        Args:
            highlight: True to highlight current line
        """
        self._highlight_current_line = highlight
        self._highlight_current_line_slot()
    
    def get_highlight_current_line(self) -> bool:
        """Get current line highlighting state."""
        return self._highlight_current_line
    
    def set_theme_colors(self, is_dark: bool) -> None:
        """
        Set colors based on theme.
        
        Args:
            is_dark: True for dark theme, False for light theme
        """
        self._is_dark_theme = is_dark
        
        _c = DialogStyleManager.get_colors(is_dark)
        self._line_number_bg = QColor(_c['line_number_bg'])
        self._line_number_fg = QColor(_c['line_number_fg'])
        self._current_line_bg = QColor(_c['line_number_current_bg'])
        self._current_line_number_fg = QColor(_c['line_number_current_fg'])
        
        self._line_number_area.update()
        self._highlight_current_line_slot()
    
    def line_number_area_width(self) -> int:
        """
        Calculate the width needed for the line number area.
        
        Returns:
            Width in pixels
        """
        if not self._show_line_numbers:
            return 0
        
        digits = 1
        max_lines = max(1, self.blockCount())
        while max_lines >= 10:
            max_lines //= 10
            digits += 1
        
        # Ensure minimum width for small documents
        digits = max(digits, 2)
        
        # Calculate width based on font metrics
        space = self._LINE_NUMBER_PADDING + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def _update_line_number_area_width(self, new_block_count: int) -> None:
        """Update viewport margins to accommodate line number area."""
        if self._show_line_numbers:
            self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        else:
            self.setViewportMargins(0, 0, 0, 0)
    
    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """
        Update line number area when text scrolls or changes.
        
        Args:
            rect: Update rectangle
            dy: Vertical scroll amount
        """
        if not self._show_line_numbers:
            return
        
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), 
                self._line_number_area.width(), 
                rect.height()
            )
        
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize to update line number area geometry."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def _highlight_current_line_slot(self) -> None:
        """Highlight the current line."""
        extra_selections: list = []
        
        if not self.isReadOnly() and self._highlight_current_line:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self._current_line_bg)
            selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        """
        Paint the line numbers in the gutter.
        
        Args:
            event: QPaintEvent
        """
        if not self._show_line_numbers:
            return
        
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self._line_number_bg)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(
            self.contentOffset()
        ).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        # Get current line number
        current_line = self.textCursor().blockNumber()
        
        # Get font for line numbers (slightly smaller than editor font)
        font = self.font()
        font.setPointSize(max(font.pointSize() - 1, 8))
        painter.setFont(font)
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # Use different color for current line
                if block_number == current_line:
                    painter.setPen(self._current_line_number_fg)
                else:
                    painter.setPen(self._line_number_fg)
                
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 5, 
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
        
        painter.end()
    
    def get_current_line_number(self) -> int:
        """
        Get the current line number (1-indexed).
        
        Returns:
            Current line number
        """
        return self.textCursor().blockNumber() + 1
    
    def get_total_lines(self) -> int:
        """
        Get total number of lines.
        
        Returns:
            Total line count
        """
        return self.blockCount()
    
    def go_to_line(self, line_number: int) -> bool:
        """
        Move cursor to specified line.
        
        Args:
            line_number: Line number (1-indexed)
            
        Returns:
            True if successful
        """
        if line_number < 1 or line_number > self.blockCount():
            return False
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.Down,
            QTextCursor.MoveMode.MoveAnchor,
            line_number - 1
        )
        self.setTextCursor(cursor)
        self.centerCursor()
        return True
    
    def setPlainText(self, text: str) -> None:
        """Override to emit textModified signal."""
        super().setPlainText(text)
        self.textModified.emit()
    
    def clear(self) -> None:
        """Override to emit textModified signal."""
        super().clear()
        self.textModified.emit()


class LineNumberQTextEdit(QTextEdit):
    """
    QTextEdit wrapper that provides line number functionality.
    
    Since QTextEdit doesn't support line numbers as easily as QPlainTextEdit,
    this provides a simpler interface for read-only output display with
    line count information, but without the gutter.
    
    For full line number gutter support, use LineNumberTextEdit (QPlainTextEdit).
    """
    
    __slots__ = ('_line_count_label',)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize LineNumberQTextEdit.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._line_count_label: str = ""
    
    def get_current_line_number(self) -> int:
        """
        Get the current line number (1-indexed).
        
        Returns:
            Current line number
        """
        cursor = self.textCursor()
        return cursor.blockNumber() + 1
    
    def get_total_lines(self) -> int:
        """
        Get total number of lines.
        
        Returns:
            Total line count
        """
        return self.document().blockCount()
    
    def get_line_info(self) -> str:
        """
        Get formatted line info string.
        
        Returns:
            String like "Line 5/120"
        """
        current = self.get_current_line_number()
        total = self.get_total_lines()
        return f"Line {current}/{total}"