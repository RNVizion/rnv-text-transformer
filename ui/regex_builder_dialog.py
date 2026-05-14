"""
RNV Text Transformer - Regex Builder Dialog Module
Visual regex pattern builder with live preview and match highlighting

Python 3.13 Optimized:
- Modern type hints
- Live pattern testing
- Common patterns library integration
- Capture group visualization

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QTextEdit, QComboBox, QCheckBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QTextCharFormat, QColor, QBrush, QTextCursor, QFont
)

from ui.base_dialog import BaseDialog
from core.regex_patterns import RegexPatterns, RegexHelper, PatternInfo
from utils.dialog_helper import DialogHelper
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager

class RegexBuilderDialog(BaseDialog):
    """
    Visual regex pattern builder with live preview.
    
    Features:
    - Pattern input with syntax validation
    - Common patterns library dropdown
    - Regex flags (case-insensitive, multiline, etc.)
    - Live match highlighting in test area
    - Capture groups display
    - Replace functionality with backreferences
    - Pattern explanation
    """
    
    # Signal emitted when pattern is applied
    pattern_applied = pyqtSignal(str, str, int)  # pattern, replacement, flags
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 800
    _DIALOG_HEIGHT: ClassVar[int] = 650
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Regex Builder"
    _MODAL: ClassVar[bool] = False
    _RESIZABLE: ClassVar[bool] = True
    
    # Highlight colors
    _MATCH_COLOR_DARK:  ClassVar[str]       = DialogStyleManager.DARK['regex_match_bg']
    _MATCH_COLOR_LIGHT: ClassVar[str]       = DialogStyleManager.LIGHT['regex_match_bg']
    _GROUP_COLORS:      ClassVar[list[str]] = DialogStyleManager.REGEX_GROUP_COLORS
    
    __slots__ = (
        'input_text',
        'pattern_input', 'replacement_input', 'test_text',
        'matches_table', 'groups_table', 'result_preview',
        'case_check', 'multiline_check', 'dotall_check',
        'pattern_combo', 'status_label', 'match_count_label',
        '_update_timer', '_current_matches'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        input_text: str = "",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize regex builder dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            input_text: Initial test text
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self.input_text = input_text
        self._current_matches: list = []
        
        # Setup debounced update timer BEFORE UI setup (signals may trigger it)
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update_matches)
        
        self._setup_ui()
        self.apply_extended_styling('tab', 'list', 'table')
        self._populate_patterns()
        self._load_text()
    

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Pattern section
        pattern_group = QGroupBox("Pattern")
        pattern_layout = QVBoxLayout(pattern_group)
        
        # Common patterns dropdown
        patterns_row = QHBoxLayout()
        patterns_row.addWidget(QLabel("Common Patterns:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.setToolTip("Select a common regex pattern template")
        self.pattern_combo.setMinimumWidth(250)
        self.pattern_combo.currentIndexChanged.connect(self._on_pattern_selected)
        patterns_row.addWidget(self.pattern_combo)
        patterns_row.addStretch()
        pattern_layout.addLayout(patterns_row)
        
        # Pattern input
        pattern_input_row = QHBoxLayout()
        pattern_input_row.addWidget(QLabel("Pattern:"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter regex pattern...")
        self.pattern_input.setFont(QFont("Consolas", 10))
        self.pattern_input.textChanged.connect(self._on_pattern_changed)
        pattern_input_row.addWidget(self.pattern_input)
        pattern_layout.addLayout(pattern_input_row)
        
        # Replacement input
        replacement_row = QHBoxLayout()
        replacement_row.addWidget(QLabel("Replace:"))
        self.replacement_input = QLineEdit()
        self.replacement_input.setPlaceholderText("Replacement text (use \\1, \\2 for groups)...")
        self.replacement_input.setFont(QFont("Consolas", 10))
        self.replacement_input.textChanged.connect(self._on_replacement_changed)
        replacement_row.addWidget(self.replacement_input)
        pattern_layout.addLayout(replacement_row)
        
        # Flags row
        flags_row = QHBoxLayout()
        flags_row.addWidget(QLabel("Flags:"))
        
        self.case_check = QCheckBox("Case Insensitive (i)")
        self.case_check.setToolTip("Ignore letter case when matching")
        self.case_check.stateChanged.connect(self._trigger_update)
        flags_row.addWidget(self.case_check)
        
        self.multiline_check = QCheckBox("Multiline (m)")
        self.multiline_check.setToolTip("Allow ^ and $ to match line boundaries")
        self.multiline_check.stateChanged.connect(self._trigger_update)
        flags_row.addWidget(self.multiline_check)
        
        self.dotall_check = QCheckBox("Dot All (s)")
        self.dotall_check.setToolTip("Allow . to match newline characters")
        self.dotall_check.stateChanged.connect(self._trigger_update)
        flags_row.addWidget(self.dotall_check)
        
        flags_row.addStretch()
        pattern_layout.addLayout(flags_row)
        
        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        c = self.get_colors()
        self.status_label.setStyleSheet(f"color: {c['text_muted']};")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        self.match_count_label = QLabel("Matches: 0")
        status_row.addWidget(self.match_count_label)
        pattern_layout.addLayout(status_row)
        
        layout.addWidget(pattern_group)
        
        # Main splitter for test area and results
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Test text area
        test_group = QGroupBox("Test Text")
        test_layout = QVBoxLayout(test_group)
        self.test_text = QTextEdit()
        self.test_text.setFont(QFont("Consolas", 10))
        self.test_text.setMinimumHeight(150)
        self.test_text.textChanged.connect(self._on_test_text_changed)
        test_layout.addWidget(self.test_text)
        splitter.addWidget(test_group)
        
        # Results tabs
        results_tabs = QTabWidget()
        
        # Matches tab
        matches_widget = QWidget()
        matches_layout = QVBoxLayout(matches_widget)
        matches_layout.setContentsMargins(5, 5, 5, 5)
        
        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(4)
        self.matches_table.setHorizontalHeaderLabels(["#", "Match", "Start", "End"])
        self.matches_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.matches_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.matches_table.itemClicked.connect(self._on_match_clicked)
        matches_layout.addWidget(self.matches_table)
        results_tabs.addTab(matches_widget, "Matches")
        
        # Groups tab
        groups_widget = QWidget()
        groups_layout = QVBoxLayout(groups_widget)
        groups_layout.setContentsMargins(5, 5, 5, 5)
        
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(3)
        self.groups_table.setHorizontalHeaderLabels(["Group", "Name", "Value"])
        self.groups_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        groups_layout.addWidget(self.groups_table)
        results_tabs.addTab(groups_widget, "Groups")
        
        # Replace preview tab
        replace_widget = QWidget()
        replace_layout = QVBoxLayout(replace_widget)
        replace_layout.setContentsMargins(5, 5, 5, 5)
        
        self.result_preview = QTextEdit()
        self.result_preview.setFont(QFont("Consolas", 10))
        self.result_preview.setReadOnly(True)
        replace_layout.addWidget(self.result_preview)
        results_tabs.addTab(replace_widget, "Replace Preview")
        
        splitter.addWidget(results_tabs)
        splitter.setSizes([300, 250])
        
        layout.addWidget(splitter, 1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Pattern")
        test_btn.setToolTip("Test the current pattern against sample text")
        test_btn.clicked.connect(self._update_matches)
        buttons_layout.addWidget(test_btn)
        
        copy_pattern_btn = QPushButton("Copy Pattern")
        copy_pattern_btn.setToolTip("Copy regex pattern to clipboard")
        copy_pattern_btn.clicked.connect(self._copy_pattern)
        buttons_layout.addWidget(copy_pattern_btn)
        
        buttons_layout.addStretch()
        
        apply_find_btn = QPushButton("Apply Find")
        apply_find_btn.setToolTip("Send pattern to Find dialog")
        apply_find_btn.clicked.connect(self._apply_find)
        buttons_layout.addWidget(apply_find_btn)
        
        apply_replace_btn = QPushButton("Apply Replace All")
        apply_replace_btn.setToolTip("Apply regex replacement to all matches")
        apply_replace_btn.clicked.connect(self._apply_replace)
        buttons_layout.addWidget(apply_replace_btn)
        
        close_btn = self._create_action_button("Close", self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_patterns(self) -> None:
        """Populate common patterns dropdown."""
        self.pattern_combo.addItem("-- Select Pattern --", None)
        
        patterns_by_category = RegexPatterns.get_patterns_by_category()
        
        for category in sorted(patterns_by_category.keys()):
            # Add category separator
            self.pattern_combo.addItem(f"── {category} ──", None)
            
            for pattern_info in patterns_by_category[category]:
                display = f"  {pattern_info.name}"
                self.pattern_combo.addItem(display, pattern_info)
    
    def _on_pattern_selected(self, index: int) -> None:
        """Handle pattern selection from dropdown."""
        pattern_info = self.pattern_combo.itemData(index)
        
        if pattern_info is None:
            return
        
        if isinstance(pattern_info, PatternInfo):
            self.pattern_input.setText(pattern_info.pattern)
            
            # Set flags based on pattern
            self.case_check.setChecked(bool(pattern_info.flags & re.IGNORECASE))
            self.multiline_check.setChecked(bool(pattern_info.flags & re.MULTILINE))
            self.dotall_check.setChecked(bool(pattern_info.flags & re.DOTALL))
            
            self.status_label.setText(pattern_info.description)
    
    def _on_pattern_changed(self, text: str) -> None:
        """Handle pattern text change."""
        self._trigger_update()
        
        # Validate pattern
        if text:
            is_valid, error = RegexHelper.validate_pattern(text, self._get_flags())
            if is_valid:
                self.status_label.setText("Pattern is valid")
                self.status_label.setStyleSheet(f"color: {self.get_colors()['success']};")
            else:
                self.status_label.setText(f"Error: {error}")
                self.status_label.setStyleSheet(f"color: {self.get_colors()['error']};")
        else:
            self.status_label.setText("Enter a pattern")
            self.status_label.setStyleSheet(f"color: {self.get_colors()['text_muted']};")
    
    def _on_replacement_changed(self, text: str) -> None:
        """Handle replacement text change."""
        self._trigger_update()
    
    def _on_test_text_changed(self) -> None:
        """Handle test text change."""
        self._trigger_update()
    
    def _trigger_update(self) -> None:
        """Trigger debounced update."""
        self._update_timer.start(300)  # 300ms debounce
    
    def _get_flags(self) -> int:
        """Get current regex flags."""
        return RegexHelper.get_flags_from_options(
            case_insensitive=self.case_check.isChecked(),
            multiline=self.multiline_check.isChecked(),
            dotall=self.dotall_check.isChecked()
        )
    
    def _update_matches(self) -> None:
        """Update matches and highlighting."""
        pattern = self.pattern_input.text()
        test_text = self.test_text.toPlainText()
        
        if not pattern or not test_text:
            self._clear_results()
            return
        
        flags = self._get_flags()
        
        # Validate pattern first
        is_valid, error = RegexHelper.validate_pattern(pattern, flags)
        if not is_valid:
            self._clear_results()
            self.status_label.setText(f"Error: {error}")
            self.status_label.setStyleSheet(f"color: {self.get_colors()['error']};")
            return
        
        # Find matches
        self._current_matches = RegexHelper.find_all_matches(test_text, pattern, flags)
        
        # Update UI
        self._update_matches_table()
        self._update_groups_table()
        self._highlight_matches()
        self._update_replace_preview()
        
        # Update count
        count = len(self._current_matches)
        self.match_count_label.setText(f"Matches: {count}")
        self.status_label.setText(f"Found {count} match{'es' if count != 1 else ''}")
        c = self.get_colors()
        self.status_label.setStyleSheet(f"color: {c['success']};" if count > 0 else f"color: {c['text_muted']};")
    
    def _clear_results(self) -> None:
        """Clear all results."""
        self._current_matches = []
        self.matches_table.setRowCount(0)
        self.groups_table.setRowCount(0)
        self.result_preview.clear()
        self.match_count_label.setText("Matches: 0")
        
        # Clear highlighting
        cursor = self.test_text.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()
        self.test_text.setTextCursor(cursor)
    
    def _update_matches_table(self) -> None:
        """Update matches table with current matches."""
        self.matches_table.setRowCount(len(self._current_matches))
        
        for i, match in enumerate(self._current_matches):
            # Match number
            item_num = QTableWidgetItem(str(i + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.matches_table.setItem(i, 0, item_num)
            
            # Match text (truncate if too long)
            match_text = match.text
            if len(match_text) > 50:
                match_text = match_text[:47] + "..."
            self.matches_table.setItem(i, 1, QTableWidgetItem(match_text))
            
            # Start position
            item_start = QTableWidgetItem(str(match.start))
            item_start.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.matches_table.setItem(i, 2, item_start)
            
            # End position
            item_end = QTableWidgetItem(str(match.end))
            item_end.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.matches_table.setItem(i, 3, item_end)
    
    def _update_groups_table(self) -> None:
        """Update groups table with first match's groups."""
        if not self._current_matches:
            self.groups_table.setRowCount(0)
            return
        
        # Use first match for groups display
        match = self._current_matches[0]
        groups = match.groups
        group_dict = match.group_dict
        
        row_count = len(groups) + len(group_dict)
        self.groups_table.setRowCount(row_count)
        
        row = 0
        
        # Numbered groups
        for i, group_value in enumerate(groups):
            item_num = QTableWidgetItem(str(i + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.groups_table.setItem(row, 0, item_num)
            
            self.groups_table.setItem(row, 1, QTableWidgetItem(""))
            self.groups_table.setItem(row, 2, QTableWidgetItem(group_value or ""))
            row += 1
        
        # Named groups
        for name, value in group_dict.items():
            item_num = QTableWidgetItem("-")
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.groups_table.setItem(row, 0, item_num)
            
            self.groups_table.setItem(row, 1, QTableWidgetItem(name))
            self.groups_table.setItem(row, 2, QTableWidgetItem(value or ""))
            row += 1
    
    def _highlight_matches(self) -> None:
        """Highlight matches in test text area."""
        # First, clear existing formatting
        cursor = self.test_text.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        if not self._current_matches:
            return
        
        is_dark = self.theme_manager.current_theme in ('dark', 'image')
        highlight_color = QColor(self._MATCH_COLOR_DARK if is_dark else self._MATCH_COLOR_LIGHT)
        
        # Highlight each match
        for match in self._current_matches:
            cursor.setPosition(match.start)
            cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)
            
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(highlight_color))
            cursor.mergeCharFormat(fmt)
    
    def _update_replace_preview(self) -> None:
        """Update replace preview with replacement applied."""
        pattern = self.pattern_input.text()
        replacement = self.replacement_input.text()
        test_text = self.test_text.toPlainText()
        
        if not pattern or not test_text:
            self.result_preview.clear()
            return
        
        if not replacement:
            self.result_preview.setPlainText("(Enter replacement text to preview)")
            return
        
        flags = self._get_flags()
        result, count = RegexHelper.replace_all(test_text, pattern, replacement, flags)
        self.result_preview.setPlainText(result)
    
    def _on_match_clicked(self, item: QTableWidgetItem) -> None:
        """Handle click on match in table - scroll to match in text."""
        row = item.row()
        if row < len(self._current_matches):
            match = self._current_matches[row]
            
            # Select the match in test text
            cursor = self.test_text.textCursor()
            cursor.setPosition(match.start)
            cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)
            self.test_text.setTextCursor(cursor)
            self.test_text.ensureCursorVisible()
    
    def _copy_pattern(self) -> None:
        """Copy pattern to clipboard."""
        from PyQt6.QtWidgets import QApplication
        
        pattern = self.pattern_input.text()
        if pattern:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(pattern)
                self.status_label.setText("Pattern copied to clipboard")
    
    def _apply_find(self) -> None:
        """Apply pattern for find operation."""
        pattern = self.pattern_input.text()
        if not pattern:
            DialogHelper.show_warning("Warning", "Please enter a pattern", parent=self)
            return
        
        flags = self._get_flags()
        is_valid, error = RegexHelper.validate_pattern(pattern, flags)
        
        if not is_valid:
            DialogHelper.show_warning("Invalid Pattern", f"Pattern error: {error}", parent=self)
            return
        
        self.pattern_applied.emit(pattern, "", flags)
        self.accept()
    
    def _apply_replace(self) -> None:
        """Apply pattern and replacement."""
        pattern = self.pattern_input.text()
        replacement = self.replacement_input.text()
        
        if not pattern:
            DialogHelper.show_warning("Warning", "Please enter a pattern", parent=self)
            return
        
        flags = self._get_flags()
        is_valid, error = RegexHelper.validate_pattern(pattern, flags)
        
        if not is_valid:
            DialogHelper.show_warning("Invalid Pattern", f"Pattern error: {error}", parent=self)
            return
        
        self.pattern_applied.emit(pattern, replacement, flags)
        self.accept()
    
    def _load_text(self) -> None:
        """Load input text into test area."""
        if self.input_text:
            self.test_text.setPlainText(self.input_text)
    
    def set_text(self, text: str) -> None:
        """
        Set test text.
        
        Args:
            text: Text to test patterns against
        """
        self.input_text = text
        self._load_text()
    
    def set_pattern(self, pattern: str) -> None:
        """
        Set initial pattern.
        
        Args:
            pattern: Regex pattern to set
        """
        self.pattern_input.setText(pattern)
    

    def closeEvent(self, event) -> None:
        """Handle dialog close - stop update timer."""
        self._update_timer.stop()
        super().closeEvent(event)