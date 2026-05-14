"""
RNV Text Transformer - Compare & Merge Dialog Module
Enhanced side-by-side comparison with merge capabilities.

Python 3.13 Optimized:
- Modern type hints
- Synchronized scrolling
- Difference highlighting
- Accept/reject individual changes
- Navigation between differences
- Multiple export formats

"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from pathlib import Path

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QTextEdit, QPushButton, QSplitter,
    QCheckBox, QComboBox, QMenu, QFileDialog,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QTextCharFormat, QColor, QBrush, QTextCursor,
    QFont, QAction
)

from ui.base_dialog import BaseDialog
from core.diff_engine import DiffEngine, DiffResult, DiffChange, ChangeType
from utils.dialog_helper import DialogHelper
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager

class ChangeWidget(QFrame):
    """
    Widget representing a single change with accept/reject buttons.
    """
    
    accepted = pyqtSignal(int)  # index
    rejected = pyqtSignal(int)  # index
    clicked = pyqtSignal(int)   # index - for navigation
    
    __slots__ = ('index', 'change', '_accept_btn', '_reject_btn', '_status_label', '_is_dark')
    
    def __init__(
        self,
        index: int,
        change: DiffChange,
        is_dark: bool = True,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.index = index
        self.change = change
        self._is_dark = is_dark
        
        self._setup_ui()
        self._update_status()
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        
        # Change type indicator
        type_label = QLabel()
        match self.change.change_type:
            case ChangeType.INSERT:
                type_label.setText("+")
                type_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['success']}; font-weight: bold;")
            case ChangeType.DELETE:
                type_label.setText("-")
                type_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['error']}; font-weight: bold;")
            case ChangeType.REPLACE:
                type_label.setText("~")
                type_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['warning']}; font-weight: bold;")
            case _:
                type_label.setText(" ")
        type_label.setFixedWidth(16)
        layout.addWidget(type_label)
        
        # Line numbers
        left_num = str(self.change.left_line_num) if self.change.left_line_num else "-"
        right_num = str(self.change.right_line_num) if self.change.right_line_num else "-"
        line_label = QLabel(f"L{left_num}→R{right_num}")
        line_label.setFixedWidth(80)
        line_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['text_muted']}; font-size: 10px;")
        layout.addWidget(line_label)
        
        # Text preview (truncated)
        text = self.change.right_text or self.change.left_text
        preview = text[:40] + "..." if len(text) > 40 else text
        preview_label = QLabel(preview)
        preview_label.setStyleSheet("font-family: monospace;")
        preview_label.setMinimumWidth(120)
        layout.addWidget(preview_label, 1)
        
        # Status label
        self._status_label = QLabel("")
        self._status_label.setFixedWidth(78)
        layout.addWidget(self._status_label)
        
        # Accept button
        self._accept_btn = QPushButton("✔")
        self._accept_btn.setFixedSize(26, 26)
        self._accept_btn.setToolTip("Accept this change")
        self._accept_btn.clicked.connect(lambda: self.accepted.emit(self.index))
        layout.addWidget(self._accept_btn)
        
        # Reject button
        self._reject_btn = QPushButton("✘")
        self._reject_btn.setFixedSize(26, 26)
        self._reject_btn.setToolTip("Reject this change")
        self._reject_btn.clicked.connect(lambda: self.rejected.emit(self.index))
        layout.addWidget(self._reject_btn)
        
        # Apply styling
        self._apply_style()
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _apply_style(self) -> None:
        """Apply styling based on theme."""
        c = DialogStyleManager.get_colors(self._is_dark)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
            }}
            QFrame:hover {{
                border-color: {c['accent']};
            }}
            QPushButton {{
                background-color: {c['border']};
                border: 1px solid {c['border_light']};
                border-radius: 3px;
                color: {c['text']};
                padding: 0px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['border_light']};
            }}
            QPushButton:disabled {{
                background-color: {c['bg']};
                color: {c['text_disabled']};
            }}
        """)
    
    def _update_status(self) -> None:
        """Update the status display."""
        if self.change.accepted is True:
            self._status_label.setText("Accepted")
            self._status_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['success']}; font-weight: bold;")
            self._accept_btn.setEnabled(False)
            self._reject_btn.setEnabled(True)
        elif self.change.accepted is False:
            self._status_label.setText("Rejected")
            self._status_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['error']}; font-weight: bold;")
            self._accept_btn.setEnabled(True)
            self._reject_btn.setEnabled(False)
        else:
            self._status_label.setText("Pending")
            self._status_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self._is_dark)['text_muted']};")
            self._accept_btn.setEnabled(True)
            self._reject_btn.setEnabled(True)
    
    def update_change(self, change: DiffChange) -> None:
        """Update the change and refresh status."""
        self.change = change
        self._update_status()
    
    def mousePressEvent(self, event) -> None:
        """Handle click for navigation."""
        super().mousePressEvent(event)
        self.clicked.emit(self.index)

class CompareDialog(BaseDialog):
    """
    Enhanced Compare & Merge dialog with full merge capabilities.
    
    Features:
    - Side-by-side diff view with synchronized scrolling
    - Accept/reject individual changes
    - Navigate between differences
    - Accept all / Reject all buttons
    - Export diff as unified diff, HTML, or side-by-side text
    - Apply merged result to output
    
    Signals:
        merge_applied: Emitted with merged text when Apply Merge is clicked
    """
    
    # Signals
    merge_applied = pyqtSignal(str)  # merged text
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 1000
    _DIALOG_HEIGHT: ClassVar[int] = 700
    _DIALOG_MIN_WIDTH: ClassVar[int] = 880
    _DIALOG_MIN_HEIGHT: ClassVar[int] = 600
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Compare & Merge"
    _MODAL: ClassVar[bool] = False
    _RESIZABLE: ClassVar[bool] = True
    
    # Highlight colors — sourced from DialogStyleManager for single source of truth
    _ADDED_COLOR_DARK:   ClassVar[str] = DialogStyleManager.DARK['diff_added_bg']
    _REMOVED_COLOR_DARK: ClassVar[str] = DialogStyleManager.DARK['diff_removed_bg']
    _CHANGED_COLOR_DARK: ClassVar[str] = DialogStyleManager.DARK['diff_changed_bg']
    _CURRENT_COLOR_DARK: ClassVar[str] = DialogStyleManager.DARK['diff_current_bg']

    _ADDED_COLOR_LIGHT:   ClassVar[str] = DialogStyleManager.LIGHT['diff_added_bg']
    _REMOVED_COLOR_LIGHT: ClassVar[str] = DialogStyleManager.LIGHT['diff_removed_bg']
    _CHANGED_COLOR_LIGHT: ClassVar[str] = DialogStyleManager.LIGHT['diff_changed_bg']
    _CURRENT_COLOR_LIGHT: ClassVar[str] = DialogStyleManager.LIGHT['diff_current_bg']
    
    __slots__ = (
        'input_text', 'output_text',
        'input_edit', 'output_edit',
        'sync_scroll_check', 'highlight_diff_check',
        'view_mode_combo', 'changes_list_widget', 'changes_list_layout',
        'stats_label', 'nav_label',
        'prev_btn', 'next_btn',
        'accept_all_btn', 'reject_all_btn', 'reset_btn',
        'export_btn', 'apply_btn',
        '_syncing_scroll', '_diff_result', '_current_change_idx',
        '_change_widgets'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        input_text: str = "",
        output_text: str = "",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize compare dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            input_text: Original input text
            output_text: Transformed output text
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self.input_text = input_text
        self.output_text = output_text
        self._syncing_scroll = False
        self._diff_result: DiffResult | None = None
        self._current_change_idx: int = -1
        self._change_widgets: list[ChangeWidget] = []
        
        self._setup_ui()
        self.setMinimumSize(self._DIALOG_MIN_WIDTH, self._DIALOG_MIN_HEIGHT)
        self.apply_extended_styling('splitter', 'menu')
        self._compute_diff()
        self._load_text()
    
    def refresh_theme(self) -> None:
        """
        Refresh dialog appearance after the application theme changes.
        
        Overrides BaseDialog.refresh_theme to also handle the dialog-specific
        elements: the splitter/menu stylesheet, the ChangeWidget instances
        (whose _is_dark is fixed at construction), and diff highlight colors.
        Called by MainWindow when the user cycles theme while this non-modal
        dialog is open.
        """
        # Update self._is_dark and re-apply base stylesheet
        super().refresh_theme()
        
        # Re-apply extended styling so splitter handles and export menu
        # follow the new theme (super only applies base styling).
        self.apply_extended_styling('splitter', 'menu')
        
        # ChangeWidget bakes _is_dark into its label/button styles at
        # construction time. Rebuild the list so widgets pick up new colors.
        # Accepted/Rejected/Pending state is preserved because it lives in
        # _diff_result.changes, not in the widgets themselves.
        self._populate_changes_list()
        
        # Re-render diff highlights with the new theme palette.
        if self.highlight_diff_check.isChecked():
            self._highlight_differences()
    

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout(margins=(10, 10, 10, 10), spacing=8)
        
        # Top options bar
        self._setup_options_bar(layout)
        
        # Main content area (splitter)
        self._setup_content_area(layout)
        
        # Statistics and navigation bar
        self._setup_stats_bar(layout)
        
        # Action buttons bar
        self._setup_action_bar(layout)
        
        # Bottom buttons
        self._setup_bottom_buttons(layout)
    
    def _setup_options_bar(self, layout: QVBoxLayout) -> None:
        """Setup the top options bar."""
        options_layout = QHBoxLayout()
        
        # View mode selector
        view_label = QLabel("View:")
        options_layout.addWidget(view_label)
        
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Side-by-Side", "Inline (Unified)"])
        self.view_mode_combo.setToolTip("Switch between side-by-side and inline diff view")
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        self.view_mode_combo.setFixedWidth(140)
        options_layout.addWidget(self.view_mode_combo)
        
        options_layout.addSpacing(20)
        
        self.sync_scroll_check = QCheckBox("Synchronized scrolling")
        self.sync_scroll_check.setToolTip("Scroll both panels together")
        self.sync_scroll_check.setChecked(True)
        options_layout.addWidget(self.sync_scroll_check)
        
        self.highlight_diff_check = QCheckBox("Highlight differences")
        self.highlight_diff_check.setToolTip("Highlight text differences with color")
        self.highlight_diff_check.setChecked(True)
        self.highlight_diff_check.stateChanged.connect(self._on_highlight_changed)
        options_layout.addWidget(self.highlight_diff_check)
        
        options_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Refresh the comparison")
        refresh_btn.setMinimumWidth(100)
        refresh_btn.clicked.connect(self._refresh_comparison)
        options_layout.addWidget(refresh_btn)
        
        layout.addLayout(options_layout)
    
    def _setup_content_area(self, layout: QVBoxLayout) -> None:
        """Setup the main content splitter."""
        # Horizontal splitter for diff view and changes list
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Diff view
        diff_widget = QWidget()
        diff_layout = QVBoxLayout(diff_widget)
        diff_layout.setContentsMargins(0, 0, 0, 0)
        
        # Vertical splitter for side-by-side
        self.diff_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Original
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        self.input_label = QLabel("Original (Input)")
        self.input_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.input_label)
        
        self.input_edit = QTextEdit()
        self.input_edit.setReadOnly(True)
        self.input_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.input_edit.setFont(QFont("Consolas", 10))
        left_layout.addWidget(self.input_edit)
        
        self.diff_splitter.addWidget(left_widget)
        
        # Right side - Modified
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        self.output_label = QLabel("Modified (Output)")
        self.output_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(self.output_label)
        
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output_edit.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.output_edit)
        
        self.diff_splitter.addWidget(right_widget)
        self.diff_splitter.setSizes([400, 400])
        
        diff_layout.addWidget(self.diff_splitter)
        main_splitter.addWidget(diff_widget)
        
        # Right: Changes list
        changes_widget = QWidget()
        changes_widget.setMinimumWidth(420)
        changes_layout = QVBoxLayout(changes_widget)
        changes_layout.setContentsMargins(5, 0, 0, 0)
        
        changes_label = QLabel("Changes")
        changes_label.setStyleSheet("font-weight: bold;")
        changes_layout.addWidget(changes_label)
        
        # Scrollable changes list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.changes_list_widget = QWidget()
        self.changes_list_layout = QVBoxLayout(self.changes_list_widget)
        self.changes_list_layout.setContentsMargins(0, 0, 0, 0)
        self.changes_list_layout.setSpacing(4)
        self.changes_list_layout.addStretch()
        
        scroll_area.setWidget(self.changes_list_widget)
        changes_layout.addWidget(scroll_area)
        
        main_splitter.addWidget(changes_widget)
        main_splitter.setSizes([580, 420])
        
        layout.addWidget(main_splitter, 1)
        
        # Connect scroll synchronization
        self._connect_scroll_sync()
    
    def _setup_stats_bar(self, layout: QVBoxLayout) -> None:
        """Setup statistics and navigation bar."""
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Changes: 0 | Accepted: 0 | Rejected: 0 | Pending: 0")
        self.stats_label.setMinimumWidth(380)
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Navigation
        self.nav_label = QLabel("Change: -/-")
        stats_layout.addWidget(self.nav_label)
        
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setToolTip("Navigate to previous change")
        self.prev_btn.setFixedWidth(90)
        self.prev_btn.clicked.connect(self._navigate_prev)
        stats_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setToolTip("Navigate to next change")
        self.next_btn.setFixedWidth(90)
        self.next_btn.clicked.connect(self._navigate_next)
        stats_layout.addWidget(self.next_btn)
        
        layout.addLayout(stats_layout)
    
    def _setup_action_bar(self, layout: QVBoxLayout) -> None:
        """Setup action buttons bar."""
        action_layout = QHBoxLayout()
        
        self.accept_all_btn = QPushButton("Accept All")
        self.accept_all_btn.setToolTip("Accept all pending changes")
        self.accept_all_btn.setMinimumWidth(110)
        self.accept_all_btn.clicked.connect(self._accept_all)
        action_layout.addWidget(self.accept_all_btn)
        
        self.reject_all_btn = QPushButton("Reject All")
        self.reject_all_btn.setToolTip("Reject all pending changes")
        self.reject_all_btn.setMinimumWidth(110)
        self.reject_all_btn.clicked.connect(self._reject_all)
        action_layout.addWidget(self.reject_all_btn)
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.setToolTip("Reset all changes to pending")
        self.reset_btn.setMinimumWidth(110)
        self.reset_btn.clicked.connect(self._reset_all)
        action_layout.addWidget(self.reset_btn)
        
        action_layout.addStretch()
        
        # Export button with menu
        self.export_btn = QPushButton("Export ▼")
        self.export_btn.setToolTip("Export diff in various formats")
        self.export_btn.setMinimumWidth(110)
        export_menu = QMenu(self)
        
        export_unified = QAction("Unified Diff (.diff)", self)
        export_unified.triggered.connect(lambda: self._export_diff("unified"))
        export_menu.addAction(export_unified)
        
        export_html = QAction("HTML Report (.html)", self)
        export_html.triggered.connect(lambda: self._export_diff("html"))
        export_menu.addAction(export_html)
        
        export_side = QAction("Side-by-Side Text (.txt)", self)
        export_side.triggered.connect(lambda: self._export_diff("side"))
        export_menu.addAction(export_side)
        
        export_conflict = QAction("Conflict Markers (.txt)", self)
        export_conflict.triggered.connect(lambda: self._export_diff("conflict"))
        export_menu.addAction(export_conflict)
        
        self.export_btn.setMenu(export_menu)
        action_layout.addWidget(self.export_btn)
        
        layout.addLayout(action_layout)
    
    def _setup_bottom_buttons(self, layout: QVBoxLayout) -> None:
        """Setup bottom buttons."""
        cancel_btn = self._create_cancel_button()
        
        self.apply_btn = QPushButton("Apply Merge")
        self.apply_btn.setToolTip("Apply accepted changes to output")
        self.apply_btn.setMinimumWidth(130)
        self.apply_btn.clicked.connect(self._apply_merge)
        self.apply_btn.setDefault(True)
        
        layout.addLayout(self._create_button_row(cancel_btn, self.apply_btn))
    
    def _connect_scroll_sync(self) -> None:
        """Connect scroll bars for synchronized scrolling."""
        input_vbar = self.input_edit.verticalScrollBar()
        output_vbar = self.output_edit.verticalScrollBar()
        input_hbar = self.input_edit.horizontalScrollBar()
        output_hbar = self.output_edit.horizontalScrollBar()
        
        if input_vbar and output_vbar:
            input_vbar.valueChanged.connect(self._sync_vertical_scroll_input)
            output_vbar.valueChanged.connect(self._sync_vertical_scroll_output)
        
        if input_hbar and output_hbar:
            input_hbar.valueChanged.connect(self._sync_horizontal_scroll_input)
            output_hbar.valueChanged.connect(self._sync_horizontal_scroll_output)
    
    def _sync_vertical_scroll_input(self, value: int) -> None:
        """Sync output vertical scroll to input."""
        if self._syncing_scroll or not self.sync_scroll_check.isChecked():
            return
        self._syncing_scroll = True
        output_vbar = self.output_edit.verticalScrollBar()
        if output_vbar:
            output_vbar.setValue(value)
        self._syncing_scroll = False
    
    def _sync_vertical_scroll_output(self, value: int) -> None:
        """Sync input vertical scroll to output."""
        if self._syncing_scroll or not self.sync_scroll_check.isChecked():
            return
        self._syncing_scroll = True
        input_vbar = self.input_edit.verticalScrollBar()
        if input_vbar:
            input_vbar.setValue(value)
        self._syncing_scroll = False
    
    def _sync_horizontal_scroll_input(self, value: int) -> None:
        """Sync output horizontal scroll to input."""
        if self._syncing_scroll or not self.sync_scroll_check.isChecked():
            return
        self._syncing_scroll = True
        output_hbar = self.output_edit.horizontalScrollBar()
        if output_hbar:
            output_hbar.setValue(value)
        self._syncing_scroll = False
    
    def _sync_horizontal_scroll_output(self, value: int) -> None:
        """Sync input horizontal scroll to output."""
        if self._syncing_scroll or not self.sync_scroll_check.isChecked():
            return
        self._syncing_scroll = True
        input_hbar = self.input_edit.horizontalScrollBar()
        if input_hbar:
            input_hbar.setValue(value)
        self._syncing_scroll = False
    

    def _compute_diff(self) -> None:
        """Compute diff between input and output."""
        self._diff_result = DiffEngine.compute_diff(self.input_text, self.output_text)
        self._current_change_idx = -1
        self._populate_changes_list()
        self._update_stats()
        self._update_navigation()
    
    def _populate_changes_list(self) -> None:
        """Populate the changes list with change widgets."""
        # Clear existing widgets
        for widget in self._change_widgets:
            widget.deleteLater()
        self._change_widgets.clear()
        
        # Remove all items from layout
        while self.changes_list_layout.count() > 0:
            item = self.changes_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self._diff_result is None:
            self.changes_list_layout.addStretch()
            return
        
        is_dark = self.theme_manager.current_theme in ('dark', 'image')
        
        # Add widgets for each change
        for i, change in enumerate(self._diff_result.changes):
            if change.is_change():
                widget = ChangeWidget(i, change, is_dark)
                widget.accepted.connect(self._on_change_accepted)
                widget.rejected.connect(self._on_change_rejected)
                widget.clicked.connect(self._on_change_clicked)
                self.changes_list_layout.addWidget(widget)
                self._change_widgets.append(widget)
        
        self.changes_list_layout.addStretch()
    
    def _load_text(self) -> None:
        """Load input and output text into editors."""
        if self.view_mode_combo.currentIndex() == 0:
            # Side-by-side view
            self.input_edit.setPlainText(self.input_text)
            self.output_edit.setPlainText(self.output_text)
            self.input_edit.show()
            self.input_label.show()
            self.output_label.setText("Modified (Output)")
            # Show both panels in splitter
            self.diff_splitter.widget(0).show()
        else:
            # Inline/unified view
            self._show_inline_diff()
        
        if self.highlight_diff_check.isChecked():
            self._highlight_differences()
    
    def _show_inline_diff(self) -> None:
        """Show inline unified diff view."""
        if self._diff_result is None:
            return
        
        # Hide left panel
        self.diff_splitter.widget(0).hide()
        self.output_label.setText("Unified Diff")
        
        unified = DiffEngine.compute_unified_diff(
            self.input_text, self.output_text,
            "original", "modified"
        )
        self.output_edit.setPlainText(unified)
    
    def _on_view_mode_changed(self, index: int) -> None:
        """Handle view mode change."""
        self._load_text()
    
    def _on_highlight_changed(self, state: int) -> None:
        """Handle highlight checkbox change."""
        if state == Qt.CheckState.Checked.value:
            self._highlight_differences()
        else:
            self._clear_highlights()
    
    def _refresh_comparison(self) -> None:
        """Refresh the comparison with current text."""
        parent = self.parent()
        if parent is not None:
            if hasattr(parent, 'text_input'):
                self.input_text = parent.text_input.toPlainText()
            if hasattr(parent, 'output_text'):
                self.output_text = parent.output_text.toPlainText()
        
        self._compute_diff()
        self._load_text()
    
    def _highlight_differences(self) -> None:
        """Highlight differences between input and output."""
        if self._diff_result is None or self.view_mode_combo.currentIndex() != 0:
            return
        
        is_dark = self.theme_manager.current_theme in ('dark', 'image')
        
        if is_dark:
            added_color = QColor(self._ADDED_COLOR_DARK)
            removed_color = QColor(self._REMOVED_COLOR_DARK)
            changed_color = QColor(self._CHANGED_COLOR_DARK)
        else:
            added_color = QColor(self._ADDED_COLOR_LIGHT)
            removed_color = QColor(self._REMOVED_COLOR_LIGHT)
            changed_color = QColor(self._CHANGED_COLOR_LIGHT)
        
        # Reset text first
        self._clear_highlights()
        
        # Track positions for highlighting
        input_lines = self.input_text.split('\n')
        output_lines = self.output_text.split('\n')
        
        # Build position maps
        input_positions = []
        pos = 0
        for line in input_lines:
            input_positions.append((pos, pos + len(line)))
            pos += len(line) + 1  # +1 for newline
        
        output_positions = []
        pos = 0
        for line in output_lines:
            output_positions.append((pos, pos + len(line)))
            pos += len(line) + 1
        
        # Apply highlighting based on changes
        for change in self._diff_result.changes:
            match change.change_type:
                case ChangeType.DELETE:
                    if change.left_line_num and change.left_line_num <= len(input_positions):
                        start, end = input_positions[change.left_line_num - 1]
                        self._highlight_range(self.input_edit, start, end - start, removed_color)
                
                case ChangeType.INSERT:
                    if change.right_line_num and change.right_line_num <= len(output_positions):
                        start, end = output_positions[change.right_line_num - 1]
                        self._highlight_range(self.output_edit, start, end - start, added_color)
                
                case ChangeType.REPLACE:
                    if change.left_line_num and change.left_line_num <= len(input_positions):
                        start, end = input_positions[change.left_line_num - 1]
                        self._highlight_range(self.input_edit, start, end - start, changed_color)
                    if change.right_line_num and change.right_line_num <= len(output_positions):
                        start, end = output_positions[change.right_line_num - 1]
                        self._highlight_range(self.output_edit, start, end - start, changed_color)
    
    def _highlight_range(
        self,
        text_edit: QTextEdit,
        start: int,
        length: int,
        color: QColor
    ) -> None:
        """Highlight a range of text."""
        text_length = len(text_edit.toPlainText())
        if start >= text_length:
            return
        
        cursor = text_edit.textCursor()
        cursor.setPosition(min(start, text_length))
        cursor.setPosition(
            min(start + length, text_length),
            QTextCursor.MoveMode.KeepAnchor
        )
        
        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QBrush(color))
        cursor.mergeCharFormat(format_highlight)
    
    def _clear_highlights(self) -> None:
        """Clear all highlights by reloading text."""
        self.input_edit.setPlainText(self.input_text)
        self.output_edit.setPlainText(self.output_text)
    
    def _update_stats(self) -> None:
        """Update statistics display."""
        if self._diff_result is None:
            self.stats_label.setText("No differences")
            return
        
        total = self._diff_result.total_changes
        accepted = self._diff_result.accepted_count
        rejected = self._diff_result.rejected_count
        pending = self._diff_result.pending_count
        
        similarity = DiffEngine.compute_similarity(self.input_text, self.output_text)
        
        self.stats_label.setText(
            f"Changes: {total} | Accepted: {accepted} | "
            f"Rejected: {rejected} | Pending: {pending} | "
            f"Similarity: {similarity * 100:.1f}%"
        )
    
    def _update_navigation(self) -> None:
        """Update navigation controls."""
        if self._diff_result is None:
            self.nav_label.setText("Change: -/-")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        
        change_indices = self._diff_result.get_change_indices()
        total = len(change_indices)
        
        if total == 0:
            self.nav_label.setText("No changes")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        
        current = 0
        if self._current_change_idx >= 0:
            try:
                current = change_indices.index(self._current_change_idx) + 1
            except ValueError:
                current = 0
        
        self.nav_label.setText(f"Change: {current}/{total}")
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total)
    
    def _navigate_prev(self) -> None:
        """Navigate to previous change."""
        if self._diff_result is None:
            return
        
        change_indices = self._diff_result.get_change_indices()
        if not change_indices:
            return
        
        current_pos = -1
        if self._current_change_idx >= 0:
            try:
                current_pos = change_indices.index(self._current_change_idx)
            except ValueError:
                current_pos = len(change_indices)
        
        if current_pos > 0:
            self._current_change_idx = change_indices[current_pos - 1]
            self._scroll_to_change(self._current_change_idx)
            self._update_navigation()
    
    def _navigate_next(self) -> None:
        """Navigate to next change."""
        if self._diff_result is None:
            return
        
        change_indices = self._diff_result.get_change_indices()
        if not change_indices:
            return
        
        current_pos = -1
        if self._current_change_idx >= 0:
            try:
                current_pos = change_indices.index(self._current_change_idx)
            except ValueError:
                current_pos = -1
        
        if current_pos < len(change_indices) - 1:
            self._current_change_idx = change_indices[current_pos + 1]
            self._scroll_to_change(self._current_change_idx)
            self._update_navigation()
    
    def _on_change_clicked(self, index: int) -> None:
        """Handle click on a change widget."""
        self._current_change_idx = index
        self._scroll_to_change(index)
        self._update_navigation()
    
    def _scroll_to_change(self, index: int) -> None:
        """Scroll text views to show a specific change."""
        if self._diff_result is None or index < 0 or index >= len(self._diff_result.changes):
            return
        
        change = self._diff_result.changes[index]
        
        # Calculate line position
        line_num = change.left_line_num or change.right_line_num
        if line_num is None:
            return
        
        # Scroll input editor
        cursor = self.input_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(min(line_num - 1, self.input_text.count('\n'))):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        self.input_edit.setTextCursor(cursor)
        self.input_edit.ensureCursorVisible()
        
        # Scroll output editor (synced if enabled)
        if not self.sync_scroll_check.isChecked():
            cursor = self.output_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            right_line = change.right_line_num or line_num
            for _ in range(min(right_line - 1, self.output_text.count('\n'))):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.output_edit.setTextCursor(cursor)
            self.output_edit.ensureCursorVisible()
    
    def _on_change_accepted(self, index: int) -> None:
        """Handle change accepted."""
        if self._diff_result is None:
            return
        
        self._diff_result.accept_change(index)
        self._update_change_widget(index)
        self._update_stats()
    
    def _on_change_rejected(self, index: int) -> None:
        """Handle change rejected."""
        if self._diff_result is None:
            return
        
        self._diff_result.reject_change(index)
        self._update_change_widget(index)
        self._update_stats()
    
    def _update_change_widget(self, index: int) -> None:
        """Update a specific change widget."""
        if self._diff_result is None:
            return
        
        for widget in self._change_widgets:
            if widget.index == index:
                widget.update_change(self._diff_result.changes[index])
                break
    
    def _accept_all(self) -> None:
        """Accept all changes."""
        if self._diff_result is None:
            return
        
        self._diff_result.accept_all()
        for widget in self._change_widgets:
            widget.update_change(self._diff_result.changes[widget.index])
        self._update_stats()
    
    def _reject_all(self) -> None:
        """Reject all changes."""
        if self._diff_result is None:
            return
        
        self._diff_result.reject_all()
        for widget in self._change_widgets:
            widget.update_change(self._diff_result.changes[widget.index])
        self._update_stats()
    
    def _reset_all(self) -> None:
        """Reset all changes to undecided."""
        if self._diff_result is None:
            return
        
        self._diff_result.reset_all()
        for widget in self._change_widgets:
            widget.update_change(self._diff_result.changes[widget.index])
        self._update_stats()
    
    def _export_diff(self, format_type: str) -> None:
        """Export diff in specified format."""
        if self._diff_result is None:
            DialogHelper.show_info("Export", "No differences to export.", parent=self)
            return
        
        # Determine file filter and content
        match format_type:
            case "unified":
                filter_str = "Diff Files (*.diff);;All Files (*)"
                default_ext = ".diff"
                content = DiffEngine.compute_unified_diff(
                    self.input_text, self.output_text
                )
            case "html":
                filter_str = "HTML Files (*.html);;All Files (*)"
                default_ext = ".html"
                content = DiffEngine.compute_html_diff(
                    self.input_text, self.output_text,
                    "Text Transformer - Diff Report"
                )
            case "side":
                filter_str = "Text Files (*.txt);;All Files (*)"
                default_ext = ".txt"
                content = DiffEngine.compute_side_by_side(
                    self.input_text, self.output_text
                )
            case "conflict":
                filter_str = "Text Files (*.txt);;All Files (*)"
                default_ext = ".txt"
                content = DiffEngine.generate_conflict_markers(
                    self.input_text, self.output_text
                )
            case _:
                return
        
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Diff", f"diff{default_ext}", filter_str
        )
        
        if file_path:
            try:
                Path(file_path).write_text(content, encoding='utf-8')
                DialogHelper.show_info(
                    "Export Complete",
                    f"Diff exported to:\n{file_path}",
                    parent=self
                )
            except Exception as e:
                DialogHelper.show_error(
                    "Export Error",
                    f"Failed to export diff:\n{e}",
                    parent=self
                )
    
    def _apply_merge(self) -> None:
        """Apply the merged result."""
        if self._diff_result is None:
            self.accept()
            return
        
        # Check for pending changes
        if self._diff_result.pending_count > 0:
            if not DialogHelper.confirm(
                "Pending Changes",
                f"There are {self._diff_result.pending_count} undecided changes.\n\n"
                "Pending changes will use the modified (output) version.\n\n"
                "Continue with merge?",
                parent=self
            ):
                return
        
        # Generate merged text
        merged = self._diff_result.get_merged_text(use_modified_for_pending=True)
        
        # Emit signal with merged text
        self.merge_applied.emit(merged)
        self.accept()
    
    def set_texts(self, input_text: str, output_text: str) -> None:
        """
        Set input and output texts.
        
        Args:
            input_text: Original input text
            output_text: Transformed output text
        """
        self.input_text = input_text
        self.output_text = output_text
        self._compute_diff()
        self._load_text()