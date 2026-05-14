"""
RNV Text Transformer - Preset Dialog Module
UI for creating, editing, and managing transformation presets

Python 3.13 Optimized:
- Modern type hints
- Dynamic step editor
- Live preview
- Drag-and-drop reordering

"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QTextEdit, QFormLayout,
    QSplitter, QFileDialog, QSpinBox,
    QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.base_dialog import BaseDialog
from core.preset_manager import (
    PresetManager, TransformPreset, PresetStep, ActionType
)
from core.text_transformer import TextTransformer
from core.text_cleaner import TextCleaner
from utils.dialog_helper import DialogHelper
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class StepEditorWidget(QWidget):
    """Widget for editing a single preset step."""
    
    step_changed = pyqtSignal()
    delete_requested = pyqtSignal()
    move_up_requested = pyqtSignal()
    move_down_requested = pyqtSignal()
    
    __slots__ = (
        'step', 'action_combo', 'params_stack', 'enabled_check',
        # Transform params
        'transform_mode_combo',
        # Cleanup params
        'cleanup_op_combo',
        # Replace params
        'replace_find_input', 'replace_with_input', 'replace_case_check',
        # Regex params
        'regex_pattern_input', 'regex_replace_input',
        # Prefix/Suffix params
        'prefix_input', 'suffix_input', 'per_line_check',
        # Wrap params
        'wrap_width_spin',
        # Split/Join params
        'delimiter_input'
    )
    
    def __init__(self, step: PresetStep, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.step = step
        self._setup_ui()
        self._load_step_data()
    
    def _setup_ui(self) -> None:
        """Setup the step editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header row with enable checkbox and action selector
        header_layout = QHBoxLayout()
        
        self.enabled_check = QCheckBox()
        self.enabled_check.setToolTip("Enable or disable this step")
        self.enabled_check.setChecked(self.step.enabled)
        self.enabled_check.stateChanged.connect(self._on_enabled_changed)
        header_layout.addWidget(self.enabled_check)
        
        self.action_combo = QComboBox()
        self.action_combo.setToolTip("Select the action type for this step")
        self.action_combo.addItems([
            "Transform", "Cleanup", "Replace", "Regex Replace",
            "Prefix", "Suffix", "Wrap Text", "Split", "Join", "Trim Lines"
        ])
        self.action_combo.setFixedWidth(120)
        self.action_combo.currentTextChanged.connect(self._on_action_changed)
        header_layout.addWidget(self.action_combo)
        
        header_layout.addStretch()
        
        # Move and delete buttons
        move_up_btn = QPushButton("↑")
        move_up_btn.setToolTip("Move step up")
        move_up_btn.setFixedWidth(30)
        move_up_btn.clicked.connect(self.move_up_requested.emit)
        header_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("↓")
        move_down_btn.setToolTip("Move step down")
        move_down_btn.setFixedWidth(30)
        move_down_btn.clicked.connect(self.move_down_requested.emit)
        header_layout.addWidget(move_down_btn)
        
        delete_btn = QPushButton("✕")
        delete_btn.setToolTip("Delete this step")
        delete_btn.setFixedWidth(30)
        delete_btn.setStyleSheet(f"color: {DialogStyleManager.DARK['error']};")
        delete_btn.clicked.connect(self.delete_requested.emit)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Stacked widget for different action parameters
        self.params_stack = QStackedWidget()
        self._create_param_widgets()
        layout.addWidget(self.params_stack)
    
    def _create_param_widgets(self) -> None:
        """Create parameter widgets for each action type."""
        # 0: Transform
        transform_widget = QWidget()
        transform_layout = QHBoxLayout(transform_widget)
        transform_layout.setContentsMargins(0, 0, 0, 0)
        transform_layout.addWidget(QLabel("Mode:"))
        self.transform_mode_combo = QComboBox()
        self.transform_mode_combo.setToolTip("Select transformation mode")
        self.transform_mode_combo.addItems(TextTransformer.get_available_modes())
        self.transform_mode_combo.currentTextChanged.connect(self._on_param_changed)
        transform_layout.addWidget(self.transform_mode_combo)
        transform_layout.addStretch()
        self.params_stack.addWidget(transform_widget)
        
        # 1: Cleanup
        cleanup_widget = QWidget()
        cleanup_layout = QHBoxLayout(cleanup_widget)
        cleanup_layout.setContentsMargins(0, 0, 0, 0)
        cleanup_layout.addWidget(QLabel("Operation:"))
        self.cleanup_op_combo = QComboBox()
        self.cleanup_op_combo.setToolTip("Select cleanup operation")
        self.cleanup_op_combo.addItems(TextCleaner.get_cleanup_operations())
        self.cleanup_op_combo.currentTextChanged.connect(self._on_param_changed)
        cleanup_layout.addWidget(self.cleanup_op_combo)
        cleanup_layout.addStretch()
        self.params_stack.addWidget(cleanup_widget)
        
        # 2: Replace
        replace_widget = QWidget()
        replace_layout = QFormLayout(replace_widget)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        self.replace_find_input = QLineEdit()
        self.replace_find_input.setPlaceholderText("Text to find")
        self.replace_find_input.textChanged.connect(self._on_param_changed)
        replace_layout.addRow("Find:", self.replace_find_input)
        self.replace_with_input = QLineEdit()
        self.replace_with_input.setPlaceholderText("Replace with")
        self.replace_with_input.textChanged.connect(self._on_param_changed)
        replace_layout.addRow("Replace:", self.replace_with_input)
        self.replace_case_check = QCheckBox("Case sensitive")
        self.replace_case_check.setToolTip("Match exact letter case when finding text")
        self.replace_case_check.setChecked(True)
        self.replace_case_check.stateChanged.connect(self._on_param_changed)
        replace_layout.addRow("", self.replace_case_check)
        self.params_stack.addWidget(replace_widget)
        
        # 3: Regex Replace
        regex_widget = QWidget()
        regex_layout = QFormLayout(regex_widget)
        regex_layout.setContentsMargins(0, 0, 0, 0)
        self.regex_pattern_input = QLineEdit()
        self.regex_pattern_input.setPlaceholderText("Regex pattern")
        self.regex_pattern_input.textChanged.connect(self._on_param_changed)
        regex_layout.addRow("Pattern:", self.regex_pattern_input)
        self.regex_replace_input = QLineEdit()
        self.regex_replace_input.setPlaceholderText("Replacement (use \\1, \\2 for groups)")
        self.regex_replace_input.textChanged.connect(self._on_param_changed)
        regex_layout.addRow("Replace:", self.regex_replace_input)
        self.params_stack.addWidget(regex_widget)
        
        # 4: Prefix
        prefix_widget = QWidget()
        prefix_layout = QFormLayout(prefix_widget)
        prefix_layout.setContentsMargins(0, 0, 0, 0)
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Prefix text")
        self.prefix_input.textChanged.connect(self._on_param_changed)
        prefix_layout.addRow("Prefix:", self.prefix_input)
        self.per_line_check = QCheckBox("Apply to each line")
        self.per_line_check.setToolTip("Apply prefix to each line individually")
        self.per_line_check.stateChanged.connect(self._on_param_changed)
        prefix_layout.addRow("", self.per_line_check)
        self.params_stack.addWidget(prefix_widget)
        
        # 5: Suffix
        suffix_widget = QWidget()
        suffix_layout = QFormLayout(suffix_widget)
        suffix_layout.setContentsMargins(0, 0, 0, 0)
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Suffix text")
        self.suffix_input.textChanged.connect(self._on_param_changed)
        suffix_layout.addRow("Suffix:", self.suffix_input)
        # Reuse per_line_check reference - create new one
        suffix_per_line = QCheckBox("Apply to each line")
        suffix_per_line.setToolTip("Apply suffix to each line individually")
        suffix_per_line.stateChanged.connect(self._on_param_changed)
        suffix_layout.addRow("", suffix_per_line)
        self.params_stack.addWidget(suffix_widget)
        
        # 6: Wrap
        wrap_widget = QWidget()
        wrap_layout = QHBoxLayout(wrap_widget)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.addWidget(QLabel("Width:"))
        self.wrap_width_spin = QSpinBox()
        self.wrap_width_spin.setToolTip("Maximum line width in characters")
        self.wrap_width_spin.setRange(10, 500)
        self.wrap_width_spin.setValue(80)
        self.wrap_width_spin.valueChanged.connect(self._on_param_changed)
        wrap_layout.addWidget(self.wrap_width_spin)
        wrap_layout.addWidget(QLabel("characters"))
        wrap_layout.addStretch()
        self.params_stack.addWidget(wrap_widget)
        
        # 7: Split
        split_widget = QWidget()
        split_layout = QHBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addWidget(QLabel("Delimiter:"))
        self.delimiter_input = QLineEdit()
        self.delimiter_input.setPlaceholderText("e.g., , or \\n or \\t")
        self.delimiter_input.textChanged.connect(self._on_param_changed)
        split_layout.addWidget(self.delimiter_input)
        self.params_stack.addWidget(split_widget)
        
        # 8: Join (reuse delimiter)
        join_widget = QWidget()
        join_layout = QHBoxLayout(join_widget)
        join_layout.setContentsMargins(0, 0, 0, 0)
        join_layout.addWidget(QLabel("Join with:"))
        join_delim = QLineEdit()
        join_delim.setPlaceholderText("e.g., , or \\n or \\t")
        join_delim.textChanged.connect(self._on_param_changed)
        join_layout.addWidget(join_delim)
        self.params_stack.addWidget(join_widget)
        
        # 9: Trim Lines (no params)
        trim_widget = QWidget()
        trim_layout = QHBoxLayout(trim_widget)
        trim_layout.setContentsMargins(0, 0, 0, 0)
        trim_layout.addWidget(QLabel("Removes leading/trailing whitespace from each line"))
        self.params_stack.addWidget(trim_widget)
    
    def _load_step_data(self) -> None:
        """Load step data into UI widgets."""
        # Set action type
        action_map = {
            ActionType.TRANSFORM: 0,
            ActionType.CLEANUP: 1,
            ActionType.REPLACE: 2,
            ActionType.REGEX_REPLACE: 3,
            ActionType.PREFIX: 4,
            ActionType.SUFFIX: 5,
            ActionType.WRAP: 6,
            ActionType.SPLIT: 7,
            ActionType.JOIN: 8,
            ActionType.TRIM_LINES: 9
        }
        
        action_index = action_map.get(self.step.action, 0)
        self.action_combo.setCurrentIndex(action_index)
        self.params_stack.setCurrentIndex(action_index)
        
        # Load action-specific params
        params = self.step.params
        
        match self.step.action:
            case ActionType.TRANSFORM:
                mode = params.get('mode', 'UPPERCASE')
                idx = self.transform_mode_combo.findText(mode)
                if idx >= 0:
                    self.transform_mode_combo.setCurrentIndex(idx)
            
            case ActionType.CLEANUP:
                op = params.get('operation', 'trim_whitespace')
                idx = self.cleanup_op_combo.findText(op)
                if idx >= 0:
                    self.cleanup_op_combo.setCurrentIndex(idx)
            
            case ActionType.REPLACE:
                self.replace_find_input.setText(params.get('find', ''))
                self.replace_with_input.setText(params.get('replace', ''))
                self.replace_case_check.setChecked(params.get('case_sensitive', True))
            
            case ActionType.REGEX_REPLACE:
                self.regex_pattern_input.setText(params.get('pattern', ''))
                self.regex_replace_input.setText(params.get('replacement', ''))
            
            case ActionType.PREFIX:
                self.prefix_input.setText(params.get('text', ''))
                self.per_line_check.setChecked(params.get('per_line', False))
            
            case ActionType.SUFFIX:
                self.suffix_input.setText(params.get('text', ''))
            
            case ActionType.WRAP:
                self.wrap_width_spin.setValue(params.get('width', 80))
            
            case ActionType.SPLIT | ActionType.JOIN:
                self.delimiter_input.setText(params.get('delimiter', ''))
    
    def _on_enabled_changed(self, state: int) -> None:
        """Handle enabled checkbox change."""
        self.step.enabled = state == Qt.CheckState.Checked.value
        self.step_changed.emit()
    
    def _on_action_changed(self, action_text: str) -> None:
        """Handle action type change."""
        action_map = {
            "Transform": (0, ActionType.TRANSFORM),
            "Cleanup": (1, ActionType.CLEANUP),
            "Replace": (2, ActionType.REPLACE),
            "Regex Replace": (3, ActionType.REGEX_REPLACE),
            "Prefix": (4, ActionType.PREFIX),
            "Suffix": (5, ActionType.SUFFIX),
            "Wrap Text": (6, ActionType.WRAP),
            "Split": (7, ActionType.SPLIT),
            "Join": (8, ActionType.JOIN),
            "Trim Lines": (9, ActionType.TRIM_LINES)
        }
        
        index, action = action_map.get(action_text, (0, ActionType.TRANSFORM))
        self.params_stack.setCurrentIndex(index)
        self.step.action = action
        self._update_step_params()
        self.step_changed.emit()
    
    def _on_param_changed(self) -> None:
        """Handle parameter change."""
        self._update_step_params()
        self.step_changed.emit()
    
    def _update_step_params(self) -> None:
        """Update step params from UI."""
        match self.step.action:
            case ActionType.TRANSFORM:
                self.step.params = {'mode': self.transform_mode_combo.currentText()}
            
            case ActionType.CLEANUP:
                self.step.params = {'operation': self.cleanup_op_combo.currentText()}
            
            case ActionType.REPLACE:
                self.step.params = {
                    'find': self.replace_find_input.text(),
                    'replace': self.replace_with_input.text(),
                    'case_sensitive': self.replace_case_check.isChecked()
                }
            
            case ActionType.REGEX_REPLACE:
                self.step.params = {
                    'pattern': self.regex_pattern_input.text(),
                    'replacement': self.regex_replace_input.text()
                }
            
            case ActionType.PREFIX:
                self.step.params = {
                    'text': self.prefix_input.text(),
                    'per_line': self.per_line_check.isChecked()
                }
            
            case ActionType.SUFFIX:
                self.step.params = {
                    'text': self.suffix_input.text(),
                    'per_line': False  # Use separate checkbox if needed
                }
            
            case ActionType.WRAP:
                self.step.params = {'width': self.wrap_width_spin.value()}
            
            case ActionType.SPLIT | ActionType.JOIN:
                self.step.params = {'delimiter': self.delimiter_input.text()}
            
            case ActionType.TRIM_LINES:
                self.step.params = {}
    
    def get_step(self) -> PresetStep:
        """Get the edited step."""
        return self.step


class PresetDialog(BaseDialog):
    """
    Dialog for creating and editing transformation presets.
    
    Features:
    - Multi-step workflow editor
    - Live preview
    - Import/export presets
    - Category organization
    """
    
    # Signals
    preset_saved = pyqtSignal(str)  # preset name
    preset_applied = pyqtSignal(str)  # preset name
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 700
    _DIALOG_HEIGHT: ClassVar[int] = 600
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Preset"
    _RESIZABLE: ClassVar[bool] = True
    
    __slots__ = (
        'preset_manager',
        'current_preset', 'is_new_preset',
        'name_input', 'description_input', 'category_combo',
        'shortcut_input', 'steps_container', 'steps_layout',
        'step_widgets', 'preview_input', 'preview_output',
        'apply_btn', 'save_btn'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        preset_manager: PresetManager,
        font_family: str = "Arial",
        preset: TransformPreset | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize preset dialog.
        
        Args:
            theme_manager: Theme manager instance
            preset_manager: Preset manager instance
            font_family: Font family to use
            preset: Preset to edit (None for new preset)
            parent: Parent widget
        """
        # Set up preset data before super().__init__ (needed for _configure_window)
        self.preset_manager = preset_manager
        self.step_widgets: list[StepEditorWidget] = []
        
        # Create new or edit existing
        if preset is None:
            self.current_preset = TransformPreset(name="New Preset")
            self.is_new_preset = True
        else:
            # Make a copy for editing
            self.current_preset = TransformPreset.from_dict(preset.to_dict())
            self.is_new_preset = False
        
        super().__init__(theme_manager, font_family, parent)
        
        self._setup_ui()
        self.apply_extended_styling('tab', 'list', 'spinbox')
        self._load_preset_data()
    
    def _configure_window(self) -> None:
        """Override for dynamic title based on preset."""
        title = "New Preset" if self.is_new_preset else f"Edit Preset: {self.current_preset.name}"
        self.setWindowTitle(f"Text Transformer - {title}")
        self.setModal(self._MODAL)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)
        self.setMinimumSize(
            int(self._DIALOG_WIDTH * 0.8),
            int(self._DIALOG_HEIGHT * 0.8)
        )
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Splitter for steps and preview
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Preset info and steps
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preset info
        info_group = QGroupBox("Preset Information")
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter preset name")
        info_layout.addRow("Name:", self.name_input)
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Optional description")
        info_layout.addRow("Description:", self.description_input)
        
        category_row = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.setToolTip("Select or type a category for this preset")
        self.category_combo.setEditable(True)
        self.category_combo.addItems(["Custom", "Developer", "Writing", "General"])
        self.category_combo.setFixedWidth(150)
        category_row.addWidget(self.category_combo)
        category_row.addSpacing(20)
        category_row.addWidget(QLabel("Shortcut:"))
        self.shortcut_input = QLineEdit()
        self.shortcut_input.setPlaceholderText("e.g., Ctrl+Shift+1")
        self.shortcut_input.setFixedWidth(150)
        category_row.addWidget(self.shortcut_input)
        category_row.addStretch()
        info_layout.addRow("Category:", category_row)
        
        top_layout.addWidget(info_group)
        
        # Steps section
        steps_group = QGroupBox("Transformation Steps")
        steps_outer_layout = QVBoxLayout(steps_group)
        
        # Add step button
        add_step_layout = QHBoxLayout()
        add_step_btn = QPushButton("+ Add Step")
        add_step_btn.setToolTip("Add a new transformation step")
        add_step_btn.clicked.connect(self._add_step)
        add_step_layout.addWidget(add_step_btn)
        add_step_layout.addStretch()
        steps_outer_layout.addLayout(add_step_layout)
        
        # Scrollable steps container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(5)
        self.steps_layout.addStretch()
        
        scroll.setWidget(self.steps_container)
        steps_outer_layout.addWidget(scroll)
        
        top_layout.addWidget(steps_group)
        splitter.addWidget(top_widget)
        
        # Bottom section: Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_row = QHBoxLayout()
        
        # Input preview
        input_col = QVBoxLayout()
        input_col.addWidget(QLabel("Sample Input:"))
        self.preview_input = QTextEdit()
        self.preview_input.setPlaceholderText("Enter sample text to preview transformation...")
        self.preview_input.setMaximumHeight(80)
        self.preview_input.textChanged.connect(self._update_preview)
        input_col.addWidget(self.preview_input)
        preview_row.addLayout(input_col)
        
        # Output preview
        output_col = QVBoxLayout()
        output_col.addWidget(QLabel("Preview Output:"))
        self.preview_output = QTextEdit()
        self.preview_output.setReadOnly(True)
        self.preview_output.setMaximumHeight(80)
        output_col.addWidget(self.preview_output)
        preview_row.addLayout(output_col)
        
        preview_layout.addLayout(preview_row)
        
        splitter.addWidget(preview_group)
        
        # Set splitter sizes
        splitter.setSizes([400, 150])
        layout.addWidget(splitter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        import_btn = QPushButton("Import...")
        import_btn.setToolTip("Import preset from file")
        import_btn.clicked.connect(self._import_preset)
        buttons_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export...")
        export_btn.setToolTip("Export preset to file")
        export_btn.clicked.connect(self._export_preset)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply to Text")
        self.apply_btn.setToolTip("Apply preset to current text")
        self.apply_btn.clicked.connect(self._apply_preset)
        buttons_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save Preset")
        self.save_btn.setToolTip("Save preset")
        self.save_btn.clicked.connect(self._save_preset)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        cancel_btn = self._create_cancel_button()
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_preset_data(self) -> None:
        """Load preset data into UI."""
        self.name_input.setText(self.current_preset.name)
        self.description_input.setText(self.current_preset.description)
        
        # Set category
        cat_idx = self.category_combo.findText(self.current_preset.category)
        if cat_idx >= 0:
            self.category_combo.setCurrentIndex(cat_idx)
        else:
            self.category_combo.setCurrentText(self.current_preset.category)
        
        self.shortcut_input.setText(self.current_preset.keyboard_shortcut or "")
        
        # Load steps
        for step in self.current_preset.steps:
            self._add_step_widget(step)
        
        # Disable editing for built-in presets
        if self.current_preset.is_builtin:
            self.name_input.setEnabled(False)
            self.save_btn.setText("Save as Copy")
    
    def _add_step(self) -> None:
        """Add a new step."""
        step = PresetStep(action=ActionType.TRANSFORM, params={'mode': 'UPPERCASE'})
        self.current_preset.add_step(step)
        self._add_step_widget(step)
        self._update_preview()
    
    def _add_step_widget(self, step: PresetStep) -> None:
        """Add a step editor widget."""
        widget = StepEditorWidget(step)
        widget.step_changed.connect(self._update_preview)
        widget.delete_requested.connect(lambda: self._remove_step(widget))
        widget.move_up_requested.connect(lambda: self._move_step_up(widget))
        widget.move_down_requested.connect(lambda: self._move_step_down(widget))
        
        # Insert before the stretch
        count = self.steps_layout.count()
        self.steps_layout.insertWidget(count - 1, widget)
        self.step_widgets.append(widget)
    
    def _remove_step(self, widget: StepEditorWidget) -> None:
        """Remove a step."""
        index = self.step_widgets.index(widget)
        self.current_preset.remove_step(index)
        self.step_widgets.remove(widget)
        self.steps_layout.removeWidget(widget)
        widget.deleteLater()
        self._update_preview()
    
    def _move_step_up(self, widget: StepEditorWidget) -> None:
        """Move a step up."""
        index = self.step_widgets.index(widget)
        if index > 0:
            self.current_preset.move_step(index, index - 1)
            self._refresh_step_widgets()
    
    def _move_step_down(self, widget: StepEditorWidget) -> None:
        """Move a step down."""
        index = self.step_widgets.index(widget)
        if index < len(self.step_widgets) - 1:
            self.current_preset.move_step(index, index + 1)
            self._refresh_step_widgets()
    
    def _refresh_step_widgets(self) -> None:
        """Refresh all step widgets from preset data."""
        # Remove all widgets
        for widget in self.step_widgets:
            self.steps_layout.removeWidget(widget)
            widget.deleteLater()
        self.step_widgets.clear()
        
        # Recreate from preset
        for step in self.current_preset.steps:
            self._add_step_widget(step)
        
        self._update_preview()
    
    def _update_preview(self) -> None:
        """Update the preview output."""
        sample_text = self.preview_input.toPlainText()
        if not sample_text:
            self.preview_output.clear()
            return
        
        try:
            result = self.preset_manager.preview_preset(sample_text, self.current_preset)
            self.preview_output.setPlainText(result)
        except Exception as e:
            self.preview_output.setPlainText(f"Error: {e}")
    
    def _save_preset(self) -> None:
        """Save the preset."""
        name = self.name_input.text().strip()
        if not name:
            DialogHelper.show_warning("Warning", "Please enter a preset name.", parent=self)
            return
        
        # Check for name conflicts
        if name != self.current_preset.name:
            existing = self.preset_manager.get_preset(name)
            if existing is not None and not existing.is_builtin:
                if not DialogHelper.confirm(
                    "Confirm",
                    f"A preset named '{name}' already exists. Overwrite?",
                    parent=self
                ):
                    return
        
        # Update preset data
        self.current_preset.name = name
        self.current_preset.description = self.description_input.text().strip()
        self.current_preset.category = self.category_combo.currentText()
        self.current_preset.keyboard_shortcut = self.shortcut_input.text().strip() or None
        self.current_preset.is_builtin = False  # Saved presets are never built-in
        
        # Save
        if self.preset_manager.add_preset(self.current_preset):
            self.preset_saved.emit(name)
            self.accept()
        else:
            DialogHelper.show_error("Error", "Failed to save preset.", parent=self)
    
    def _apply_preset(self) -> None:
        """Apply preset to main text."""
        # Save first if modified
        if self.name_input.text().strip():
            self._save_preset()
            self.preset_applied.emit(self.current_preset.name)
    
    def _import_preset(self) -> None:
        """Import a preset from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Preset",
            "", "Preset Files (*.json);;All Files (*)"
        )
        if file_path:
            from pathlib import Path
            preset = self.preset_manager.import_preset(Path(file_path))
            if preset:
                DialogHelper.show_info(
                    "Success",
                    f"Imported preset: {preset.name}",
                    parent=self
                )
                # Load the imported preset for editing
                self.current_preset = preset
                self.is_new_preset = False
                self._refresh_step_widgets()
                self._load_preset_data()
            else:
                DialogHelper.show_warning("Error", "Failed to import preset.", parent=self)
    
    def _export_preset(self) -> None:
        """Export the current preset to file."""
        name = self.name_input.text().strip() or "preset"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preset",
            f"{name}.json", "Preset Files (*.json);;All Files (*)"
        )
        if file_path:
            from pathlib import Path
            # Update preset from UI first
            self.current_preset.name = self.name_input.text().strip()
            self.current_preset.description = self.description_input.text().strip()
            self.current_preset.category = self.category_combo.currentText()
            
            if self.preset_manager.export_preset(self.current_preset.name, Path(file_path)):
                DialogHelper.show_info("Success", "Preset exported successfully.", parent=self)
            else:
                # Export directly if not in manager
                try:
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_preset.to_dict(), f, indent=2)
                    DialogHelper.show_info("Success", "Preset exported successfully.", parent=self)
                except Exception as e:
                    DialogHelper.show_warning("Error", f"Failed to export: {e}", parent=self)


class PresetManagerDialog(BaseDialog):
    """
    Dialog for managing all presets - list, delete, organize.
    """
    
    # Signals
    preset_selected = pyqtSignal(str)  # preset name to apply
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 700
    _DIALOG_HEIGHT: ClassVar[int] = 550
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Manage Presets"
    
    __slots__ = (
        'preset_manager',
        'preset_list', 'info_label'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        preset_manager: PresetManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(theme_manager, font_family, parent)
        
        self.preset_manager = preset_manager
        
        self._setup_ui()
        self.apply_extended_styling('list')
        self._populate_list()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.setAlternatingRowColors(False)
        self.preset_list.itemDoubleClicked.connect(self._on_preset_double_clicked)
        self.preset_list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.preset_list)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        new_btn = QPushButton("New Preset")
        new_btn.setToolTip("Create a new preset")
        new_btn.clicked.connect(self._new_preset)
        buttons_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setToolTip("Edit selected preset")
        edit_btn.clicked.connect(self._edit_preset)
        buttons_layout.addWidget(edit_btn)
        
        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.setToolTip("Duplicate selected preset")
        duplicate_btn.clicked.connect(self._duplicate_preset)
        buttons_layout.addWidget(duplicate_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setToolTip("Delete selected preset")
        delete_btn.clicked.connect(self._delete_preset)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.setToolTip("Apply selected preset to text")
        apply_btn.clicked.connect(self._apply_preset)
        buttons_layout.addWidget(apply_btn)
        
        close_btn = self._create_close_button()
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_list(self) -> None:
        """Populate the preset list."""
        self.preset_list.clear()
        
        categories = self.preset_manager.get_presets_by_category()
        
        for category, presets in sorted(categories.items()):
            # Add category header
            header_item = QListWidgetItem(f"━━ {category} ━━━━")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.preset_list.addItem(header_item)
            
            for preset in presets:
                icon = "🔒 " if preset.is_builtin else ""
                text = f"{icon}{preset.name}"
                if preset.keyboard_shortcut:
                    text += f"  [{preset.keyboard_shortcut}]"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, preset.name)
                self.preset_list.addItem(item)
    
    def _on_selection_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle selection change."""
        if current is None:
            self.info_label.setText("")
            return
        
        name = current.data(Qt.ItemDataRole.UserRole)
        if name:
            preset = self.preset_manager.get_preset(name)
            if preset:
                info = f"{preset.description}" if preset.description else "No description"
                info += f"\n{preset.get_step_count()} step(s)"
                self.info_label.setText(info)
    
    def _on_preset_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on preset."""
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.preset_selected.emit(name)
            self.accept()
    
    def _get_selected_preset_name(self) -> str | None:
        """Get currently selected preset name."""
        item = self.preset_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def _new_preset(self) -> None:
        """Create new preset."""
        dialog = PresetDialog(
            self.theme_manager,
            self.preset_manager,
            self.font_family,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._populate_list()
    
    def _edit_preset(self) -> None:
        """Edit selected preset."""
        name = self._get_selected_preset_name()
        if not name:
            return
        
        preset = self.preset_manager.get_preset(name)
        if preset:
            dialog = PresetDialog(
                self.theme_manager,
                self.preset_manager,
                self.font_family,
                preset=preset,
                parent=self
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._populate_list()
    
    def _duplicate_preset(self) -> None:
        """Duplicate selected preset."""
        name = self._get_selected_preset_name()
        if not name:
            return
        
        new_preset = self.preset_manager.duplicate_preset(name)
        if new_preset:
            self._populate_list()
    
    def _delete_preset(self) -> None:
        """Delete selected preset."""
        name = self._get_selected_preset_name()
        if not name:
            return
        
        preset = self.preset_manager.get_preset(name)
        if preset and preset.is_builtin:
            DialogHelper.show_warning("Warning", "Cannot delete built-in presets.", parent=self)
            return
        
        if DialogHelper.confirm(
            "Confirm Delete",
            f"Delete preset '{name}'?",
            parent=self
        ):
            self.preset_manager.delete_preset(name)
            self._populate_list()
    
    def _apply_preset(self) -> None:
        """Apply selected preset."""
        name = self._get_selected_preset_name()
        if name:
            self.preset_selected.emit(name)
            self.accept()