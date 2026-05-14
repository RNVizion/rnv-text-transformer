"""
RNV Text Transformer - Find & Replace Dialog Module
Provides find and find/replace functionality for text areas

Python 3.13 Optimized:
- Modern type hints
- Match statements
- Clean separation of concerns

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QCheckBox, QPushButton,
    QGroupBox, QRadioButton, QButtonGroup, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QBrush

from ui.base_dialog import BaseDialog
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class FindReplaceDialog(BaseDialog):
    """
    Find and Replace dialog for text searching and replacement.
    
    Features:
    - Find text with highlighting
    - Replace single or all occurrences
    - Case sensitive option
    - Whole word option
    - Regular expression support
    - Search in input or output area
    
    Signals:
        find_requested: Emitted when find is requested
        replace_requested: Emitted when replace is requested
        replace_all_requested: Emitted when replace all is requested
    """
    
    # Signals
    find_requested = pyqtSignal(str, dict)  # search_text, options
    replace_requested = pyqtSignal(str, str, dict)  # search, replace, options
    replace_all_requested = pyqtSignal(str, str, dict)  # search, replace, options
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 450
    _DIALOG_HEIGHT: ClassVar[int] = 320
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Find"
    _MODAL: ClassVar[bool] = False
    
    # Highlight colors — sourced from DialogStyleManager (no hardcoded hex)
    
    __slots__ = (
        'target_text_edit',
        'find_input', 'replace_input',
        'case_sensitive_check', 'whole_word_check', 'regex_check',
        'search_input_radio', 'search_output_radio', 'search_group',
        'find_btn', 'find_next_btn', 'replace_btn', 'replace_all_btn',
        'status_label', '_current_matches', '_current_match_index',
        '_is_replace_mode'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        target_text_edit: QTextEdit | None = None,
        replace_mode: bool = False,
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize Find/Replace dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            target_text_edit: Text edit widget to search in
            replace_mode: If True, show replace options
            parent: Parent widget
        """
        self._is_replace_mode = replace_mode
        super().__init__(theme_manager, font_family, parent)
        
        self.target_text_edit = target_text_edit
        self._current_matches: list[tuple[int, int]] = []  # (start, end) positions
        self._current_match_index: int = -1
        
        self._setup_ui()
        self.apply_base_styling()
    
    def _configure_window(self) -> None:
        """Override to set fixed width only (height adjusts to content)."""
        title = "Find and Replace" if self._is_replace_mode else "Find"
        self.setWindowTitle(f"Text Transformer - {title}")
        self.setModal(self._MODAL)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setFixedWidth(self._DIALOG_WIDTH)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Find input
        find_group = QGroupBox("Find")
        find_layout = QVBoxLayout(find_group)
        
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Enter text to find...")
        self.find_input.textChanged.connect(self._on_find_text_changed)
        self.find_input.returnPressed.connect(self._on_find_next)
        find_layout.addWidget(self.find_input)
        
        layout.addWidget(find_group)
        
        # Replace input (only in replace mode)
        if self._is_replace_mode:
            replace_group = QGroupBox("Replace with")
            replace_layout = QVBoxLayout(replace_group)
            
            self.replace_input = QLineEdit()
            self.replace_input.setPlaceholderText("Enter replacement text...")
            replace_layout.addWidget(self.replace_input)
            
            layout.addWidget(replace_group)
        else:
            self.replace_input = None
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        # First row of options
        options_row1 = QHBoxLayout()
        
        self.case_sensitive_check = QCheckBox("Case sensitive")
        self.case_sensitive_check.setToolTip("Match exact letter case")
        options_row1.addWidget(self.case_sensitive_check)
        
        self.whole_word_check = QCheckBox("Whole word")
        self.whole_word_check.setToolTip("Match whole words only")
        options_row1.addWidget(self.whole_word_check)
        
        self.regex_check = QCheckBox("Regular expression")
        self.regex_check.setToolTip("Use regular expression patterns")
        self.regex_check.stateChanged.connect(self._on_regex_changed)
        options_row1.addWidget(self.regex_check)
        
        options_row1.addStretch()
        options_layout.addLayout(options_row1)
        
        # Search area selection
        search_area_layout = QHBoxLayout()
        search_area_label = QLabel("Search in:")
        search_area_layout.addWidget(search_area_label)
        
        self.search_group = QButtonGroup(self)
        self.search_input_radio = QRadioButton("Input")
        self.search_output_radio = QRadioButton("Output")
        self.search_input_radio.setChecked(True)
        
        self.search_group.addButton(self.search_input_radio, 0)
        self.search_group.addButton(self.search_output_radio, 1)
        
        search_area_layout.addWidget(self.search_input_radio)
        search_area_layout.addWidget(self.search_output_radio)
        search_area_layout.addStretch()
        
        options_layout.addLayout(search_area_layout)
        
        layout.addWidget(options_group)
        
        # Status label
        self.status_label = QLabel("")
        c = self.get_colors()
        self.status_label.setStyleSheet(f"color: {c['text_muted']};")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.find_btn = QPushButton("Find")
        self.find_btn.setToolTip("Find first occurrence")
        self.find_btn.clicked.connect(self._on_find)
        buttons_layout.addWidget(self.find_btn)
        
        self.find_next_btn = QPushButton("Find Next")
        self.find_next_btn.setToolTip("Find next occurrence")
        self.find_next_btn.clicked.connect(self._on_find_next)
        self.find_next_btn.setEnabled(False)
        buttons_layout.addWidget(self.find_next_btn)
        
        if self._is_replace_mode:
            self.replace_btn = QPushButton("Replace")
            self.replace_btn.setToolTip("Replace current match")
            self.replace_btn.clicked.connect(self._on_replace)
            self.replace_btn.setEnabled(False)
            buttons_layout.addWidget(self.replace_btn)
            
            self.replace_all_btn = QPushButton("Replace All")
            self.replace_all_btn.setToolTip("Replace all occurrences")
            self.replace_all_btn.clicked.connect(self._on_replace_all)
            buttons_layout.addWidget(self.replace_all_btn)
        else:
            self.replace_btn = None
            self.replace_all_btn = None
        
        close_btn = self._create_action_button("Close", self._on_close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def set_target_text_edit(self, text_edit: QTextEdit, is_output: bool = False) -> None:
        """
        Set the target text edit widget to search in.
        
        Args:
            text_edit: QTextEdit widget
            is_output: If True, select output radio button
        """
        self.target_text_edit = text_edit
        if is_output:
            self.search_output_radio.setChecked(True)
        else:
            self.search_input_radio.setChecked(True)
    
    def get_search_options(self) -> dict:
        """
        Get current search options.
        
        Returns:
            Dictionary with search options
        """
        return {
            'case_sensitive': self.case_sensitive_check.isChecked(),
            'whole_word': self.whole_word_check.isChecked(),
            'regex': self.regex_check.isChecked(),
            'search_output': self.search_output_radio.isChecked()
        }
    
    def _on_find_text_changed(self, text: str) -> None:
        """Handle find text change - reset matches."""
        self._current_matches.clear()
        self._current_match_index = -1
        self.find_next_btn.setEnabled(False)
        if self.replace_btn:
            self.replace_btn.setEnabled(False)
        self.status_label.setText("")
        self._clear_highlights()
    
    def _on_regex_changed(self, state: int) -> None:
        """Handle regex checkbox change."""
        if state == Qt.CheckState.Checked.value:
            # Disable whole word when regex is enabled
            self.whole_word_check.setChecked(False)
            self.whole_word_check.setEnabled(False)
        else:
            self.whole_word_check.setEnabled(True)
    
    def _on_find(self) -> None:
        """Execute find operation."""
        search_text = self.find_input.text()
        if not search_text:
            self.status_label.setText("Please enter text to find")
            return
        
        options = self.get_search_options()
        self._perform_find(search_text, options)
    
    def _on_find_next(self) -> None:
        """Find next match."""
        if not self._current_matches:
            self._on_find()
            return
        
        # Move to next match
        self._current_match_index = (self._current_match_index + 1) % len(self._current_matches)
        self._highlight_current_match()
    
    def _on_replace(self) -> None:
        """Replace current match."""
        if not self._current_matches or self._current_match_index < 0:
            self.status_label.setText("No match selected")
            return
        
        if self.target_text_edit is None or self.replace_input is None:
            return
        
        replace_text = self.replace_input.text()
        start, end = self._current_matches[self._current_match_index]
        
        # Replace the current match
        cursor = self.target_text_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(replace_text)
        
        # Re-find to update matches
        self._on_find()
        self.status_label.setText("Replaced 1 occurrence")
    
    def _on_replace_all(self) -> None:
        """Replace all matches."""
        search_text = self.find_input.text()
        if not search_text:
            self.status_label.setText("Please enter text to find")
            return
        
        if self.target_text_edit is None or self.replace_input is None:
            return
        
        replace_text = self.replace_input.text()
        options = self.get_search_options()
        
        text = self.target_text_edit.toPlainText()
        count = 0
        
        try:
            if options['regex']:
                flags = 0 if options['case_sensitive'] else re.IGNORECASE
                pattern = re.compile(search_text, flags)
                new_text, count = pattern.subn(replace_text, text)
            else:
                if options['whole_word']:
                    flags = 0 if options['case_sensitive'] else re.IGNORECASE
                    pattern = re.compile(r'\b' + re.escape(search_text) + r'\b', flags)
                    new_text, count = pattern.subn(replace_text, text)
                elif options['case_sensitive']:
                    count = text.count(search_text)
                    new_text = text.replace(search_text, replace_text)
                else:
                    # Case insensitive replace
                    pattern = re.compile(re.escape(search_text), re.IGNORECASE)
                    new_text, count = pattern.subn(replace_text, text)
            
            if count > 0:
                self.target_text_edit.setPlainText(new_text)
                self.status_label.setText(f"Replaced {count} occurrence(s)")
            else:
                self.status_label.setText("No matches found")
                
        except re.error as e:
            self.status_label.setText(f"Regex error: {e}")
        
        self._current_matches.clear()
        self._current_match_index = -1
    
    def _on_close(self) -> None:
        """Close dialog and clear highlights."""
        self._clear_highlights()
        self.close()
    
    def _perform_find(self, search_text: str, options: dict) -> None:
        """
        Perform the find operation.
        
        Args:
            search_text: Text to search for
            options: Search options dictionary
        """
        if self.target_text_edit is None:
            self.status_label.setText("No text area selected")
            return
        
        text = self.target_text_edit.toPlainText()
        self._current_matches.clear()
        self._current_match_index = -1
        
        try:
            if options['regex']:
                flags = 0 if options['case_sensitive'] else re.IGNORECASE
                pattern = re.compile(search_text, flags)
                for match in pattern.finditer(text):
                    self._current_matches.append((match.start(), match.end()))
            else:
                if options['whole_word']:
                    flags = 0 if options['case_sensitive'] else re.IGNORECASE
                    pattern = re.compile(r'\b' + re.escape(search_text) + r'\b', flags)
                    for match in pattern.finditer(text):
                        self._current_matches.append((match.start(), match.end()))
                else:
                    # Simple text search
                    search_in = text if options['case_sensitive'] else text.lower()
                    find_text = search_text if options['case_sensitive'] else search_text.lower()
                    
                    start = 0
                    while True:
                        pos = search_in.find(find_text, start)
                        if pos == -1:
                            break
                        self._current_matches.append((pos, pos + len(search_text)))
                        start = pos + 1
            
            if self._current_matches:
                self._current_match_index = 0
                self._highlight_all_matches()
                self._highlight_current_match()
                self.find_next_btn.setEnabled(True)
                if self.replace_btn:
                    self.replace_btn.setEnabled(True)
                self.status_label.setText(
                    f"Found {len(self._current_matches)} match(es)"
                )
            else:
                self.status_label.setText("No matches found")
                self._clear_highlights()
                
        except re.error as e:
            self.status_label.setText(f"Regex error: {e}")
    
    def _highlight_all_matches(self) -> None:
        """Highlight all matches in the text edit."""
        if self.target_text_edit is None:
            return
        
        self._clear_highlights()
        
        is_dark = self.theme_manager.current_theme in ('dark', 'image')
        highlight_color = QColor(DialogStyleManager.get_colors(is_dark)['accent'])
        highlight_color.setAlpha(80)  # Semi-transparent
        
        cursor = self.target_text_edit.textCursor()
        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QBrush(highlight_color))
        
        # Apply highlighting to all matches
        for start, end in self._current_matches:
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(format_highlight)
    
    def _highlight_current_match(self) -> None:
        """Highlight and scroll to current match."""
        if self.target_text_edit is None or self._current_match_index < 0:
            return
        
        if self._current_match_index >= len(self._current_matches):
            return
        
        start, end = self._current_matches[self._current_match_index]
        
        # Move cursor to current match and select it
        cursor = self.target_text_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.target_text_edit.setTextCursor(cursor)
        
        # Ensure the match is visible
        self.target_text_edit.ensureCursorVisible()
        
        # Update status
        self.status_label.setText(
            f"Match {self._current_match_index + 1} of {len(self._current_matches)}"
        )
    
    def _clear_highlights(self) -> None:
        """Clear all highlights from the text edit."""
        if self.target_text_edit is None:
            return
        
        # Reset formatting by getting plain text and setting it back
        # This preserves the text but removes formatting
        cursor = self.target_text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        format_clear = QTextCharFormat()
        cursor.setCharFormat(format_clear)
        cursor.clearSelection()
        self.target_text_edit.setTextCursor(cursor)
    
    def closeEvent(self, event) -> None:
        """Handle dialog close - clear highlights."""
        self._clear_highlights()
        super().closeEvent(event)