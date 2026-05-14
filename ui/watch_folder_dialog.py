"""
RNV Text Transformer - Watch Folder Dialog Module
GUI for configuring folder watching and automatic transformation

Python 3.13 Optimized:
- Modern type hints
- Signal/slot architecture
- Thread-safe event handling

"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from datetime import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QCheckBox,
    QFileDialog, QTextEdit, QSplitter,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ui.base_dialog import BaseDialog
from core.folder_watcher import (
    FolderWatcher, WatchRule, WatchRuleManager,
    WatchEvent, WatchEventType, WATCHDOG_AVAILABLE
)
from core.text_transformer import TextTransformer
from core.preset_manager import PresetManager
from utils.dialog_helper import DialogHelper

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class RuleEditWidget(QWidget):
    """Widget for editing a single watch rule."""
    
    # Signals
    rule_changed = pyqtSignal(object)  # WatchRule
    rule_deleted = pyqtSignal(str)  # rule_id
    
    __slots__ = (
        'rule', 'theme_manager', 'font_family',
        'input_edit', 'output_edit', 'patterns_edit',
        'mode_combo', 'preset_combo', 'enabled_check',
        'process_existing_check', 'delete_source_check'
    )
    
    def __init__(
        self,
        rule: WatchRule,
        theme_manager: 'ThemeManager',
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """Initialize rule edit widget."""
        super().__init__(parent)
        self.rule = rule
        self.theme_manager = theme_manager
        self.font_family = font_family
        
        self._setup_ui()
        self._load_rule()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header with enabled checkbox and delete button
        header_layout = QHBoxLayout()
        
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setToolTip("Enable or disable this watch rule")
        self.enabled_check.stateChanged.connect(self._on_changed)
        header_layout.addWidget(self.enabled_check)
        
        header_layout.addStretch()
        
        delete_btn = QPushButton("Delete")
        delete_btn.setToolTip("Delete this watch rule")
        delete_btn.setFixedWidth(80)
        delete_btn.clicked.connect(self._on_delete)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Input folder
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Folder:"))
        self.input_edit = QLineEdit()
        self.input_edit.setReadOnly(True)
        self.input_edit.textChanged.connect(self._on_changed)
        input_layout.addWidget(self.input_edit, 1)
        input_browse = QPushButton("Browse...")
        input_browse.setToolTip("Select folder to watch for new files")
        input_browse.setFixedWidth(80)
        input_browse.clicked.connect(self._browse_input)
        input_layout.addWidget(input_browse)
        layout.addLayout(input_layout)
        
        # Output folder
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.textChanged.connect(self._on_changed)
        output_layout.addWidget(self.output_edit, 1)
        output_browse = QPushButton("Browse...")
        output_browse.setToolTip("Select output folder for processed files")
        output_browse.setFixedWidth(80)
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(output_browse)
        layout.addLayout(output_layout)
        
        # File patterns
        patterns_layout = QHBoxLayout()
        patterns_layout.addWidget(QLabel("File Patterns:"))
        self.patterns_edit = QLineEdit()
        self.patterns_edit.setPlaceholderText("*.txt, *.md")
        self.patterns_edit.setToolTip("Comma-separated file patterns to watch (e.g. *.txt, *.md)")
        self.patterns_edit.textChanged.connect(self._on_changed)
        patterns_layout.addWidget(self.patterns_edit, 1)
        layout.addLayout(patterns_layout)
        
        # Transform mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Transform Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("(None)")
        self.mode_combo.addItems(TextTransformer.get_available_modes())
        self.mode_combo.setToolTip("Select text transformation mode")
        self.mode_combo.currentTextChanged.connect(self._on_changed)
        mode_layout.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_layout)
        
        # Preset
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(None)")
        preset_manager = PresetManager()
        self.preset_combo.addItems(preset_manager.get_preset_names())
        self.preset_combo.setToolTip("Select a preset to apply")
        self.preset_combo.currentTextChanged.connect(self._on_changed)
        preset_layout.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.process_existing_check = QCheckBox("Process existing files on start")
        self.process_existing_check.setToolTip("Process files already in the folder when starting")
        self.process_existing_check.stateChanged.connect(self._on_changed)
        options_layout.addWidget(self.process_existing_check)
        
        self.delete_source_check = QCheckBox("Delete source after processing")
        self.delete_source_check.setToolTip("Delete original files after processing")
        self.delete_source_check.stateChanged.connect(self._on_changed)
        options_layout.addWidget(self.delete_source_check)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
    
    def _load_rule(self) -> None:
        """Load rule data into widgets.

        Signals are blocked on every input widget during load. Without this,
        the early setChecked/setText calls would fire _on_changed before
        patterns_edit is populated, and _save_rule would read the empty
        patterns_edit and overwrite self.rule.file_patterns with the default
        fallback ["*.txt"] — silently destroying the user's saved patterns.
        """
        widgets_to_block = (
            self.enabled_check, self.input_edit, self.output_edit,
            self.patterns_edit, self.mode_combo, self.preset_combo,
            self.process_existing_check, self.delete_source_check,
        )
        for w in widgets_to_block:
            w.blockSignals(True)
        try:
            self.enabled_check.setChecked(self.rule.enabled)
            self.input_edit.setText(str(self.rule.input_folder))
            self.output_edit.setText(str(self.rule.output_folder))
            self.patterns_edit.setText(", ".join(self.rule.file_patterns))

            # Mode
            if self.rule.transform_mode:
                idx = self.mode_combo.findText(self.rule.transform_mode)
                if idx >= 0:
                    self.mode_combo.setCurrentIndex(idx)

            # Preset
            if self.rule.preset_name:
                idx = self.preset_combo.findText(self.rule.preset_name)
                if idx >= 0:
                    self.preset_combo.setCurrentIndex(idx)

            self.process_existing_check.setChecked(self.rule.process_existing)
            self.delete_source_check.setChecked(self.rule.delete_source)
        finally:
            for w in widgets_to_block:
                w.blockSignals(False)
    
    def _save_rule(self) -> None:
        """Save widget data to rule."""
        self.rule.enabled = self.enabled_check.isChecked()
        self.rule.input_folder = Path(self.input_edit.text()) if self.input_edit.text() else Path()
        self.rule.output_folder = Path(self.output_edit.text()) if self.output_edit.text() else Path()
        
        patterns = self.patterns_edit.text()
        self.rule.file_patterns = [p.strip() for p in patterns.split(",") if p.strip()]
        if not self.rule.file_patterns:
            self.rule.file_patterns = ["*.txt"]
        
        mode = self.mode_combo.currentText()
        self.rule.transform_mode = mode if mode != "(None)" else None
        
        preset = self.preset_combo.currentText()
        self.rule.preset_name = preset if preset != "(None)" else None
        
        self.rule.process_existing = self.process_existing_check.isChecked()
        self.rule.delete_source = self.delete_source_check.isChecked()
    
    def _on_changed(self) -> None:
        """Handle any change."""
        self._save_rule()
        self.rule_changed.emit(self.rule)
    
    def _on_delete(self) -> None:
        """Handle delete button."""
        if DialogHelper.confirm(
            "Delete Rule",
            "Are you sure you want to delete this rule?",
            parent=self
        ):
            self.rule_deleted.emit(self.rule.id)
    
    def _browse_input(self) -> None:
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder",
            self.input_edit.text() or str(Path.home())
        )
        if folder:
            self.input_edit.setText(folder)
    
    def _browse_output(self) -> None:
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder",
            self.output_edit.text() or str(Path.home())
        )
        if folder:
            self.output_edit.setText(folder)


class WatchFolderDialog(BaseDialog):
    """
    Dialog for configuring folder watching.
    
    Features:
    - Add/edit/delete watch rules
    - Start/stop watching
    - View activity log
    - Process existing files
    """
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 800
    _DIALOG_HEIGHT: ClassVar[int] = 650
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Watch Folders"
    _MODAL: ClassVar[bool] = False
    _RESIZABLE: ClassVar[bool] = True
    
    __slots__ = (
        'watcher', 'rule_manager',
        'rules_container', 'rule_widgets',
        'log_text', 'status_label',
        'start_btn', 'stop_btn', 'add_btn',
        '_log_timer'
    )
    
    def __init__(
        self,
        theme_manager: 'ThemeManager',
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """Initialize watch folder dialog."""
        super().__init__(theme_manager, font_family, parent)
        
        self.watcher = FolderWatcher()
        self.rule_manager = WatchRuleManager()
        self.rule_widgets: dict[str, RuleEditWidget] = {}
        
        self._setup_ui()
        self.apply_base_styling()
        self._load_rules()
        
        # Setup event callback
        self.watcher.set_event_callback(self._on_watch_event)
        
        # Log timer for thread-safe updates
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._process_log_queue)
        self._log_timer.start(100)
        
        self._pending_logs: list[str] = []
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = self._create_main_layout()
        
        # Check watchdog availability
        if not WATCHDOG_AVAILABLE:
            warning = QLabel(
                "⚠️ Watch Folder feature requires the 'watchdog' library.\n"
                "Install with: pip install watchdog"
            )
            warning.setStyleSheet(f"color: {self.get_colors()['error']}; font-weight: bold; padding: 10px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        
        # Splitter for rules and log
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Rules section
        rules_group = QGroupBox("Watch Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        # Add button
        add_layout = QHBoxLayout()
        add_layout.addStretch()
        self.add_btn = QPushButton("+ Add Rule")
        self.add_btn.setToolTip("Add a new watch rule")
        self.add_btn.clicked.connect(self._add_rule)
        self.add_btn.setEnabled(WATCHDOG_AVAILABLE)
        add_layout.addWidget(self.add_btn)
        rules_layout.addLayout(add_layout)
        
        # Scrollable rules container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.rules_container = QWidget()
        self.rules_container.setLayout(QVBoxLayout())
        self.rules_container.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rules_container.layout().setSpacing(5)
        scroll.setWidget(self.rules_container)
        
        rules_layout.addWidget(scroll)
        splitter.addWidget(rules_group)
        
        # Log section
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_buttons = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setToolTip("Clear the activity log")
        clear_log_btn.clicked.connect(self._clear_log)
        log_buttons.addWidget(clear_log_btn)
        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)
        
        splitter.addWidget(log_group)
        
        # Set splitter sizes
        splitter.setSizes([400, 150])
        layout.addWidget(splitter)
        
        # Status
        self.status_label = QLabel("Status: Stopped")
        layout.addWidget(self.status_label)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        process_btn = QPushButton("Process Existing")
        process_btn.setToolTip("Process existing files in watched folders now")
        process_btn.clicked.connect(self._process_existing)
        process_btn.setEnabled(WATCHDOG_AVAILABLE)
        buttons_layout.addWidget(process_btn)
        
        buttons_layout.addStretch()
        
        self.start_btn = QPushButton("Start Watching")
        self.start_btn.setToolTip("Start monitoring folders for new files")
        self.start_btn.clicked.connect(self._start_watching)
        self.start_btn.setEnabled(WATCHDOG_AVAILABLE)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Watching")
        self.stop_btn.setToolTip("Stop folder monitoring")
        self.stop_btn.clicked.connect(self._stop_watching)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        close_btn = self._create_action_button("Close", self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_rules(self) -> None:
        """Load saved rules."""
        rules = self.rule_manager.load_rules()
        for rule in rules:
            self._add_rule_widget(rule)
            self.watcher.add_rule(rule)
    
    def _save_rules(self) -> None:
        """Save current rules."""
        rules = self.watcher.get_rules()
        self.rule_manager.save_rules(rules)
    
    def _add_rule(self) -> None:
        """Add a new rule."""
        rule = WatchRule(
            id=str(uuid.uuid4()),
            input_folder=Path.home(),
            output_folder=Path.home() / "transformed",
            file_patterns=["*.txt"],
            enabled=True
        )
        
        if self.watcher.add_rule(rule):
            self._add_rule_widget(rule)
            self._save_rules()
        else:
            DialogHelper.show_warning(
                "Error",
                "Could not add rule. Check that folders exist.",
                parent=self
            )
    
    def _add_rule_widget(self, rule: WatchRule) -> None:
        """Add a rule widget to the UI."""
        widget = RuleEditWidget(rule, self.theme_manager, self.font_family)
        widget.rule_changed.connect(self._on_rule_changed)
        widget.rule_deleted.connect(self._on_rule_deleted)
        
        self.rules_container.layout().addWidget(widget)
        self.rule_widgets[rule.id] = widget
    
    def _on_rule_changed(self, rule: WatchRule) -> None:
        """Handle rule change."""
        self.watcher.update_rule(rule)
        self._save_rules()
    
    def _on_rule_deleted(self, rule_id: str) -> None:
        """Handle rule deletion."""
        if rule_id in self.rule_widgets:
            widget = self.rule_widgets.pop(rule_id)
            widget.setParent(None)
            widget.deleteLater()
        
        self.watcher.remove_rule(rule_id)
        self._save_rules()
    
    def _start_watching(self) -> None:
        """Start watching folders."""
        rules = self.watcher.get_rules()
        enabled_rules = [r for r in rules if r.enabled]
        
        if not enabled_rules:
            DialogHelper.show_warning(
                "Warning",
                "No enabled rules to watch.",
                parent=self
            )
            return
        
        if self.watcher.start():
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"Status: Watching {len(enabled_rules)} folder(s)")
            self._log(f"Started watching {len(enabled_rules)} folder(s)")
    
    def _stop_watching(self) -> None:
        """Stop watching folders."""
        self.watcher.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self._log("Stopped watching")
    
    def _process_existing(self) -> None:
        """Process existing files in watched folders."""
        if not self.watcher.is_running():
            # Start temporarily
            self.watcher.start()
        
        count = self.watcher.process_existing_files()
        self._log(f"Queued {count} existing file(s) for processing")
    
    def _on_watch_event(self, event: WatchEvent) -> None:
        """Handle watch event (called from background thread)."""
        # Thread-safe: add to pending logs
        timestamp = event.timestamp.strftime("%H:%M:%S")
        
        if event.event_type == WatchEventType.PROCESSING_ERROR:
            msg = f"[{timestamp}] ERROR: {event.message}"
        elif event.event_type == WatchEventType.PROCESSING_COMPLETE:
            msg = f"[{timestamp}] ✔ {event.message}"
        elif event.event_type == WatchEventType.FILE_CREATED:
            msg = f"[{timestamp}] New: {event.file_path.name if event.file_path else ''}"
        else:
            msg = f"[{timestamp}] {event.message}"
        
        self._pending_logs.append(msg)
    
    def _process_log_queue(self) -> None:
        """Process pending log messages (called from main thread)."""
        while self._pending_logs:
            msg = self._pending_logs.pop(0)
            self.log_text.append(msg)
            
            # Auto-scroll
            scrollbar = self.log_text.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
    
    def _log(self, message: str) -> None:
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def _clear_log(self) -> None:
        """Clear the log."""
        self.log_text.clear()
    
    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        # Stop watcher if running
        if self.watcher.is_running():
            self.watcher.stop()
        
        # Stop timer
        self._log_timer.stop()
        
        super().closeEvent(event)