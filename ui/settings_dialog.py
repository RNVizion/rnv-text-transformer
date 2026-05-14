"""
RNV Text Transformer - Settings Dialog Module
Tabbed settings panel for application configuration

Python 3.13 Optimized:
- Modern type hints
- Match statements
- Clean separation of concerns

- Removed About tab (moved to standalone AboutDialog)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QSpinBox, QPushButton,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QListWidget, QListWidgetItem,
    QScrollArea, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.base_dialog import BaseDialog
from core.text_cleaner import TextCleaner
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager
    from core.theme_manager import ThemeManager

class SettingsDialog(BaseDialog):
    """
    Tabbed settings dialog for application configuration.
    
    Tabs:
    - Settings: General preferences
    - Adjustments: Text manipulation actions (Clear, Swap, Undo, Redo)
    - Export: Multi-format export options
    - History: Recent files list
    - Quick Actions: Keyboard shortcuts
    
    Note: About information moved to standalone AboutDialog (Ctrl+/)
    
    Signals:
        settings_changed: Emitted when settings are modified
        theme_change_requested: Emitted when theme change is requested
    """
    
    # Signals
    settings_changed = pyqtSignal()
    theme_change_requested = pyqtSignal(str)  # theme name
    stats_position_changed = pyqtSignal(str)  # position string
    undo_requested = pyqtSignal()  # undo output
    redo_requested = pyqtSignal()  # redo output
    open_recent_file_requested = pyqtSignal(str)  # open recent file
    cleanup_requested = pyqtSignal(str)  # cleanup operation
    split_join_requested = pyqtSignal(str)  # split/join operation
    export_requested = pyqtSignal()  # open export dialog
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 622
    _DIALOG_HEIGHT: ClassVar[int] = 620  # Increased for new content
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Features & Settings"
    
    __slots__ = (
        'settings_manager', 'tab_widget', 
        # Settings tab widgets
        'theme_combo', 'auto_transform_check', 'auto_load_check',
        'show_tooltips_check', 'recent_files_spin', 'stats_position_combo',
        # Adjustments tab widgets
        'cleanup_combo', 'split_join_combo',
        # History tab widgets
        'recent_files_list',
        # Tracking
        '_original_theme', '_changes_made'
    )
    
    def __init__(
        self, 
        settings_manager: SettingsManager,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize settings dialog.
        
        Args:
            settings_manager: Application settings manager
            theme_manager: Theme manager instance
            font_family: Font family to use
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self.settings_manager = settings_manager
        self._changes_made = False
        
        # Store original theme for cancel/revert
        self._original_theme = theme_manager.current_theme
        
        self._setup_ui()
        self._load_current_settings()
        self.apply_extended_styling('tab', 'spinbox', 'slider', 'list', 'table')
    

    def _setup_ui(self) -> None:
        """Setup the dialog UI with tabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setUsesScrollButtons(False)
        self.tab_widget.tabBar().setDrawBase(False)
        
        # Add tabs (About moved to standalone dialog Ctrl+/)
        self.tab_widget.addTab(self._create_settings_tab(), "⚙ Settings")
        self.tab_widget.addTab(self._create_adjustments_tab(), "🔧 Adjustments")
        self.tab_widget.addTab(self._create_export_tab(), "📤 Export")
        self.tab_widget.addTab(self._create_history_tab(), "📜 History")
        self.tab_widget.addTab(self._create_quick_actions_tab(), "⚡ Quick Actions")
        
        layout.addWidget(self.tab_widget)
        
        # Bottom button bar
        reset_btn = self._create_action_button(
            "Reset to Defaults", self._reset_to_defaults, width=170
        )
        close_btn = self._create_close_button()
        button_row = self._create_button_row(reset_btn, close_btn)
        button_row.setContentsMargins(10, 10, 10, 0)
        layout.addLayout(button_row)
    
    def _create_settings_tab(self) -> QWidget:
        """Create the Settings tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        
        # Header
        layout.addWidget(self._create_header_label("Application Settings"))
        layout.addWidget(self._create_subtitle_label("Customize your Text Transformer experience"))
        
        # General Preferences Group
        general_group = QGroupBox("General Preferences")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)
        
        # Default Theme
        self.theme_combo = QComboBox()
        self.theme_combo.setItemDelegate(QStyledItemDelegate())
        theme_options = ["Dark Mode", "Light Mode"]
        if self.theme_manager.image_mode_available:
            theme_options.append("Image Mode")
        self.theme_combo.addItems(theme_options)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.theme_combo.setToolTip("Select the default application theme")
        general_layout.addRow("Default Theme:", self.theme_combo)
        
        # Auto-transform
        self.auto_transform_check = QCheckBox("Auto-transform on input change")
        self.auto_transform_check.setToolTip("Automatically transform text when input changes")
        self.auto_transform_check.stateChanged.connect(self._on_setting_changed)
        general_layout.addRow("", self.auto_transform_check)
        
        # Show tooltips
        self.show_tooltips_check = QCheckBox("Show button tooltips")
        self.show_tooltips_check.setToolTip("Show or hide tooltips on main window buttons")
        self.show_tooltips_check.setChecked(True)  # Default on
        self.show_tooltips_check.stateChanged.connect(self._on_setting_changed)
        general_layout.addRow("", self.show_tooltips_check)
        
        layout.addWidget(general_group)
        
        # History Settings Group
        history_group = QGroupBox("Recent Files")
        history_layout = QFormLayout(history_group)
        history_layout.setSpacing(10)
        
        # Recent files limit
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setRange(0, 20)
        self.recent_files_spin.setValue(10)
        self.recent_files_spin.setSpecialValueText("Disabled")
        self.recent_files_spin.setToolTip("Maximum number of recent files to remember (0 to disable)")
        self.recent_files_spin.valueChanged.connect(self._on_setting_changed)
        history_layout.addRow("Maximum recent files:", self.recent_files_spin)
        
        # Clear recent files button
        clear_recent_btn = QPushButton("Clear Recent Files")
        clear_recent_btn.setToolTip("Remove all entries from recent files list")
        clear_recent_btn.clicked.connect(self._clear_recent_files)
        history_layout.addRow("", clear_recent_btn)
        
        layout.addWidget(history_group)
        
        # Statistics Display Group
        stats_group = QGroupBox("Statistics Display")
        stats_layout = QFormLayout(stats_group)
        stats_layout.setSpacing(10)
        
        self.stats_position_combo = QComboBox()
        self.stats_position_combo.setItemDelegate(QStyledItemDelegate())
        self.stats_position_combo.addItems(["Below Output", "Above Output", "Hidden"])
        self.stats_position_combo.setToolTip("Choose where text statistics are displayed")
        self.stats_position_combo.currentTextChanged.connect(self._on_setting_changed)
        stats_layout.addRow("Statistics position:", self.stats_position_combo)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return tab
    
    def _create_adjustments_tab(self) -> QWidget:
        """Create the Adjustments tab with text manipulation actions."""
        # Create scroll area for the tab content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        layout.addWidget(self._create_header_label("Text Adjustments"))
        layout.addWidget(self._create_subtitle_label("Quick text manipulation and cleanup actions"))
        
        # ==================== TEXT CLEANUP GROUP ====================
        cleanup_group = QGroupBox("Text Cleanup")
        cleanup_layout = QVBoxLayout(cleanup_group)
        cleanup_layout.setSpacing(10)
        
        cleanup_layout.addWidget(self._create_description_label("Apply cleanup operations to your text"))
        
        cleanup_row = QHBoxLayout()
        self.cleanup_combo = QComboBox()
        self.cleanup_combo.setItemDelegate(QStyledItemDelegate())
        self.cleanup_combo.addItems(TextCleaner.get_cleanup_operations())
        self.cleanup_combo.setToolTip("Select a cleanup operation to apply")
        self.cleanup_combo.setMinimumWidth(200)
        cleanup_row.addWidget(self.cleanup_combo)
        cleanup_row.addStretch()
        
        cleanup_btn = self._create_action_button("Apply", self._action_cleanup)
        cleanup_row.addWidget(cleanup_btn)
        
        cleanup_layout.addLayout(cleanup_row)
        layout.addWidget(cleanup_group)
        
        # ==================== SPLIT/JOIN GROUP ====================
        split_group = QGroupBox("Split / Join")
        split_layout = QVBoxLayout(split_group)
        split_layout.setSpacing(10)
        
        split_layout.addWidget(self._create_description_label("Split text into lines or join lines together"))
        
        split_row = QHBoxLayout()
        self.split_join_combo = QComboBox()
        self.split_join_combo.setItemDelegate(QStyledItemDelegate())
        self.split_join_combo.addItems(TextCleaner.get_split_join_operations())
        self.split_join_combo.setToolTip("Select a split or join operation")
        self.split_join_combo.setMinimumWidth(200)
        split_row.addWidget(self.split_join_combo)
        split_row.addStretch()
        
        split_btn = self._create_action_button("Apply", self._action_split_join)
        split_row.addWidget(split_btn)
        
        split_layout.addLayout(split_row)
        layout.addWidget(split_group)
        
        # ==================== TEXT ACTIONS GROUP ====================
        actions_group = QGroupBox("Text Actions")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(12)
        
        # Clear All section
        clear_layout = QHBoxLayout()
        clear_info = QVBoxLayout()
        clear_label = QLabel("Clear All Text")
        clear_label.setStyleSheet("font-weight: bold;")
        clear_info.addWidget(clear_label)
        clear_info.addWidget(self._create_description_label("Remove all text from input and output areas"))
        clear_layout.addLayout(clear_info)
        clear_layout.addStretch()
        
        clear_btn = self._create_action_button("Clear All", self._action_clear_all)
        clear_layout.addWidget(clear_btn)
        
        actions_layout.addLayout(clear_layout)
        
        # Separator
        actions_layout.addWidget(self._create_separator())
        
        # Swap section
        swap_layout = QHBoxLayout()
        swap_info = QVBoxLayout()
        swap_label = QLabel("Swap Input/Output")
        swap_label.setStyleSheet("font-weight: bold;")
        swap_info.addWidget(swap_label)
        swap_info.addWidget(self._create_description_label("Move output text to input for chained transformations"))
        swap_layout.addLayout(swap_info)
        swap_layout.addStretch()
        
        swap_btn = self._create_action_button("Swap", self._action_swap)
        swap_layout.addWidget(swap_btn)
        
        actions_layout.addLayout(swap_layout)
        
        layout.addWidget(actions_group)
        
        # ==================== UNDO/REDO GROUP ====================
        undo_group = QGroupBox("Output History")
        undo_layout = QVBoxLayout(undo_group)
        undo_layout.setSpacing(12)
        
        # Undo section
        undo_row = QHBoxLayout()
        undo_info = QVBoxLayout()
        undo_label = QLabel("Undo Output")
        undo_label.setStyleSheet("font-weight: bold;")
        undo_info.addWidget(undo_label)
        undo_info.addWidget(self._create_description_label("Revert to previous transformation result"))
        undo_row.addLayout(undo_info)
        undo_row.addStretch()
        
        undo_btn = self._create_action_button("Undo", self._action_undo)
        undo_row.addWidget(undo_btn)
        
        undo_layout.addLayout(undo_row)
        
        # Separator
        undo_layout.addWidget(self._create_separator())
        
        # Redo section
        redo_row = QHBoxLayout()
        redo_info = QVBoxLayout()
        redo_label = QLabel("Redo Output")
        redo_label.setStyleSheet("font-weight: bold;")
        redo_info.addWidget(redo_label)
        redo_info.addWidget(self._create_description_label("Restore previously undone transformation"))
        redo_row.addLayout(redo_info)
        redo_row.addStretch()
        
        redo_btn = self._create_action_button("Redo", self._action_redo)
        redo_row.addWidget(redo_btn)
        
        undo_layout.addLayout(redo_row)
        
        layout.addWidget(undo_group)
        
        # ==================== KEYBOARD SHORTCUTS ====================
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        
        shortcut_info = QLabel(
            "• Clear All: Ctrl+Shift+X\n"
            "• Swap Input/Output: Ctrl+Shift+S\n"
            "• Undo Output: Ctrl+Z\n"
            "• Redo Output: Ctrl+Y"
        )
        shortcut_info.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))
        shortcuts_layout.addWidget(shortcut_info)
        
        layout.addWidget(shortcuts_group)
        
        layout.addStretch()
        
        scroll.setWidget(tab)
        return scroll
    
    def _action_clear_all(self) -> None:
        """Execute Clear All action on parent window."""
        parent = self.parent()
        if parent is not None and hasattr(parent, '_clear_all'):
            parent._clear_all()
    
    def _action_swap(self) -> None:
        """Execute Swap action on parent window."""
        parent = self.parent()
        if parent is not None and hasattr(parent, '_swap_input_output'):
            parent._swap_input_output()
    
    def _action_undo(self) -> None:
        """Execute Undo action."""
        self.undo_requested.emit()
    
    def _action_redo(self) -> None:
        """Execute Redo action."""
        self.redo_requested.emit()
    
    def _action_cleanup(self) -> None:
        """Execute selected cleanup operation."""
        operation = self.cleanup_combo.currentText()
        self.cleanup_requested.emit(operation)
    
    def _action_split_join(self) -> None:
        """Execute selected split/join operation."""
        operation = self.split_join_combo.currentText()
        self.split_join_requested.emit(operation)
    
    def _create_export_tab(self) -> QWidget:
        """Create the Export tab for multi-format export."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        
        # Header
        layout.addWidget(self._create_header_label("Export Output"))
        layout.addWidget(self._create_subtitle_label("Export your transformed text to various formats"))
        
        # Export Formats Group
        formats_group = QGroupBox("Available Formats")
        formats_layout = QVBoxLayout(formats_group)
        formats_layout.setSpacing(12)
        
        # Format descriptions
        formats_info = [
            ("📄 Plain Text (.txt)", "Simple text file, UTF-8 encoded"),
            ("📝 Word Document (.docx)", "Microsoft Word format with formatting"),
            ("🌐 HTML Document (.html)", "Web page with styling options"),
            ("📕 PDF Document (.pdf)", "Portable document with page layout"),
            ("📋 Markdown (.md)", "Lightweight markup for documentation"),
            ("📃 Rich Text (.rtf)", "Cross-platform formatted text"),
        ]
        
        for format_name, description in formats_info:
            format_row = QHBoxLayout()
            
            format_label = QLabel(format_name)
            format_label.setStyleSheet("font-weight: bold;")
            format_label.setFixedWidth(200)
            format_row.addWidget(format_label)
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))
            format_row.addWidget(desc_label)
            
            format_row.addStretch()
            formats_layout.addLayout(format_row)
        
        layout.addWidget(formats_group)
        
        # Export Options Group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)
        
        options_info = QLabel(
            "The Export dialog provides options for:\n\n"
            "• Line Numbers - Add line numbers to output\n"
            "• Metadata - Include document information\n"
            "• Font Settings - Choose font family and size\n"
            "• Format-specific options (PDF pages, HTML theme)"
        )
        options_info.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))
        options_layout.addWidget(options_info)
        
        layout.addWidget(options_group)
        
        # Export Button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        export_btn = self._create_action_button(
            "Open Export Dialog...", self._action_export, width=200
        )
        export_layout.addWidget(export_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        # Tip
        layout.addWidget(self._create_tip_label(
            "💡 Tip: Use Ctrl+E to quickly open the Export dialog from the main window"
        ))
        
        layout.addStretch()
        return tab
    
    def _action_export(self) -> None:
        """Open export dialog."""
        self.export_requested.emit()
        self.accept()  # Close settings dialog to show export dialog
    
    def _create_history_tab(self) -> QWidget:
        """Create the History tab with recent files list."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(18)
        
        # Header
        layout.addWidget(self._create_header_label("Recent Files"))
        layout.addWidget(self._create_subtitle_label("Recently opened files - double-click to open"))
        
        # Recent files list
        self.recent_files_list = QListWidget()
        self.recent_files_list.setAlternatingRowColors(False)
        self.recent_files_list.itemDoubleClicked.connect(self._on_recent_file_double_clicked)
        layout.addWidget(self.recent_files_list)
        
        # Populate the list
        self._populate_recent_files()
        
        # Buttons row
        refresh_btn = self._create_action_button("Refresh", self._populate_recent_files)
        clear_btn = self._create_action_button("Clear All", self._clear_recent_files_and_refresh)
        layout.addLayout(self._create_button_row(refresh_btn, clear_btn))
        
        # Info label
        layout.addWidget(self._create_tip_label(
            "Tip: Use Ctrl+Shift+O to quickly access recent files from the main window"
        ))
        
        return tab
    
    def _populate_recent_files(self) -> None:
        """Populate the recent files list."""
        self.recent_files_list.clear()
        
        recent_files = self.settings_manager.load_recent_files()
        
        if not recent_files:
            item = QListWidgetItem("No recent files")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.recent_files_list.addItem(item)
            return
        
        from pathlib import Path
        for file_path in recent_files:
            path = Path(file_path)
            # Show filename and parent directory
            if path.parent.name:
                display_text = f"{path.name}  ({path.parent.name})"
            else:
                display_text = path.name
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, file_path)  # Store full path
            item.setToolTip(file_path)  # Show full path on hover
            self.recent_files_list.addItem(item)
    
    def _on_recent_file_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on recent file item."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.open_recent_file_requested.emit(file_path)
            self.accept()  # Close dialog after opening file
    
    def _clear_recent_files_and_refresh(self) -> None:
        """Clear recent files and refresh the list."""
        self._clear_recent_files()
        self._populate_recent_files()
    
    def _create_quick_actions_tab(self) -> QWidget:
        """Create the Quick Actions tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        
        # Header
        layout.addWidget(self._create_header_label("Quick Actions & Shortcuts"))
        layout.addWidget(self._create_subtitle_label("Fast productivity tools and keyboard shortcuts"))
        
        # Keyboard Shortcuts Group
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        
        # Create shortcuts table
        shortcuts_table = QTableWidget()
        shortcuts_table.setColumnCount(2)
        shortcuts_table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        shortcuts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        shortcuts_table.verticalHeader().setVisible(False)
        shortcuts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        shortcuts_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        shortcuts_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Define shortcuts
        shortcuts = [
            ("Ctrl+T", "Transform Text"),
            ("Ctrl+Shift+C", "Copy Output to Clipboard"),
            ("Ctrl+O", "Load File"),
            ("Ctrl+S", "Save Output to File"),
            ("Ctrl+E", "Export Output"),
            ("Ctrl+Shift+X", "Clear All Text"),
            ("Ctrl+Shift+S", "Swap Input/Output"),
            ("Ctrl+Shift+T", "Cycle Theme"),
            ("Ctrl+,", "Open Settings"),
            ("Ctrl+Z", "Undo Output"),
            ("Ctrl+Y", "Redo Output"),
            ("Ctrl+Shift+O", "Recent Files Menu"),
            ("Ctrl+F", "Find"),
            ("Ctrl+H", "Find & Replace"),
            ("Ctrl+B", "Batch Processing"),
            ("Ctrl+D", "Compare View"),
            ("Ctrl+R", "Regex Builder"),
            ("Ctrl+Shift+E", "Encoding Converter"),
            ("Ctrl+P", "Presets Manager"),
            ("Ctrl+W", "Watch Folders"),
            ("F11", "Toggle Tooltips"),
            ("Ctrl+/", "About"),
            ("Ctrl+Q", "Quit Application"),
        ]
        
        shortcuts_table.setRowCount(len(shortcuts))
        for row, (shortcut, action) in enumerate(shortcuts):
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            shortcuts_table.setItem(row, 0, shortcut_item)
            
            action_item = QTableWidgetItem(action)
            shortcuts_table.setItem(row, 1, action_item)
        
        shortcuts_layout.addWidget(shortcuts_table)
        
        # Let shortcuts group expand to fill available space
        layout.addWidget(shortcuts_group, 1)
        
        # Quick Actions Group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        actions_layout.addWidget(self._create_tip_label(
            "💡 Tip: Use keyboard shortcuts for fastest workflow!"
        ))
        
        layout.addWidget(actions_group)
        
        return tab
    
    def _load_current_settings(self) -> None:
        """Load current settings into UI widgets."""
        # Theme
        current_theme = self.theme_manager.current_theme
        theme_map = {
            'dark': "Dark Mode",
            'light': "Light Mode",
            'image': "Image Mode"
        }
        theme_text = theme_map.get(current_theme, "Dark Mode")
        index = self.theme_combo.findText(theme_text)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Auto-transform
        self.auto_transform_check.setChecked(
            self.settings_manager.load_auto_transform()
        )
        
        # Show tooltips
        self.show_tooltips_check.setChecked(
            self.settings_manager.load_show_tooltips()
        )
        
        # Stats position
        stats_position = self.settings_manager.load_stats_position()
        stats_index = self.stats_position_combo.findText(stats_position)
        if stats_index >= 0:
            self.stats_position_combo.setCurrentIndex(stats_index)
        
        # Recent files max
        max_recent = self.settings_manager.load_recent_files_max()
        self.recent_files_spin.setValue(max_recent)
    

    def _on_theme_changed(self, theme_text: str) -> None:
        """Handle theme selection change."""
        theme_map = {
            "Dark Mode": 'dark',
            "Light Mode": 'light',
            "Image Mode": 'image'
        }
        theme = theme_map.get(theme_text, 'dark')
        
        # Save and emit signal
        self.settings_manager.save_theme(theme)
        self.theme_change_requested.emit(theme)
        self._changes_made = True
        
        # Update dialog styling for new theme
        self.theme_manager.set_theme(theme)
        self._is_dark = self._detect_dark_theme()
        self.apply_extended_styling('tab', 'spinbox', 'slider', 'list', 'table')
    
    def _on_setting_changed(self) -> None:
        """Handle any setting change - auto-apply all settings immediately."""
        self._changes_made = True
        
        # Save all settings immediately
        self.settings_manager.save_auto_transform(
            self.auto_transform_check.isChecked()
        )
        self.settings_manager.save_show_tooltips(
            self.show_tooltips_check.isChecked()
        )
        self.settings_manager.save_recent_files_max(
            self.recent_files_spin.value()
        )
        
        # Save and emit stats position change
        position = self.stats_position_combo.currentText()
        self.settings_manager.save_stats_position(position)
        self.stats_position_changed.emit(position)
        
        self.settings_changed.emit()
    
    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.settings_manager.clear_recent_files()
        self._changes_made = True
    
    def _reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        # Reset UI to defaults
        self.theme_combo.setCurrentText("Dark Mode")
        self.auto_transform_check.setChecked(False)
        self.show_tooltips_check.setChecked(True)
        self.recent_files_spin.setValue(10)
        self.stats_position_combo.setCurrentText("Below Output")
        
        # Save defaults
        self.settings_manager.save_theme('dark')
        self.settings_manager.save_auto_transform(False)
        
        self._changes_made = True
        self.settings_changed.emit()
        self.theme_change_requested.emit('dark')
    
    def has_changes(self) -> bool:
        """Check if any settings were changed."""
        return self._changes_made