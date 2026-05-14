"""
RNV Text Transformer - Export Dialog Module
Dialog for exporting text to multiple formats

Python 3.13 Optimized:
- Modern type hints
- Theme-aware styling
- Preview functionality

"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QComboBox, QCheckBox, QPushButton,
    QGroupBox, QLineEdit, QSpinBox,
    QFileDialog, QTextEdit
)
from PyQt6.QtCore import pyqtSignal

from ui.base_dialog import BaseDialog
from core.export_manager import ExportManager, ExportFormat, ExportOptions, ExportError
from utils.dialog_helper import DialogHelper
from utils.dialog_styles import DialogStyleManager

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class ExportDialog(BaseDialog):
    """
    Export dialog for saving text to multiple formats.
    
    Supports: TXT, DOCX, HTML, PDF, Markdown, RTF
    
    Signals:
        export_completed: Emitted when export is successful (path)
        export_failed: Emitted when export fails (error message)
    """
    
    # Signals
    export_completed = pyqtSignal(str)  # exported file path
    export_failed = pyqtSignal(str)  # error message
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 620
    _DIALOG_HEIGHT: ClassVar[int] = 720
    _RESIZABLE: ClassVar[bool] = True
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Export"
    
    __slots__ = (
        'text_content',
        'format_combo', 'title_input', 'line_numbers_check',
        'metadata_check', 'font_family_combo', 'font_size_spin',
        'html_dark_check', 'html_css_check',
        'pdf_page_numbers_check', 'preview_text',
        'export_btn', 'format_status_label',
        'specific_group', '_export_manager'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        text_content: str = "",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize export dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            text_content: Text to export
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self.text_content = text_content
        self._export_manager = ExportManager()
        
        self._setup_ui()
        self.apply_extended_styling('spinbox')
        self._update_format_status()
        self._update_preview()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Ensure QGroupBox headers have enough room for Montserrat-Black
        self.setStyleSheet(self.styleSheet() + """
            QGroupBox { padding-top: 32px; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 8px; }
            QCheckBox { spacing: 8px; min-height: 26px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        
        # Header
        header = QLabel("Export Document")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)
        
        # Format selection group
        format_group = QGroupBox("Output Format")
        format_group_layout = QVBoxLayout(format_group)
        format_group_layout.setSpacing(10)
        
        self.format_combo = QComboBox()
        for fmt in ExportFormat:
            self.format_combo.addItem(fmt.value, fmt)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.format_combo.setToolTip("Select output file format")
        format_group_layout.addLayout(self._create_form_row("Format:", self.format_combo))
        
        self.format_status_label = QLabel("")
        c = self.get_colors()
        self.format_status_label.setStyleSheet(f"font-size: 9pt; color: {c['text_muted']};")
        format_group_layout.addWidget(self.format_status_label)
        
        layout.addWidget(format_group)
        
        # Document options group
        doc_group = QGroupBox("Document Options")
        doc_group_layout = QVBoxLayout(doc_group)
        doc_group_layout.setSpacing(20)
        doc_group_layout.setContentsMargins(10, 10, 10, 16)
        
        # Title row - built manually to ensure label isn't clipped
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(10)
        title_label = QLabel("Title:")
        title_label.setFixedWidth(120)
        title_label.setMinimumHeight(32)
        title_row.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Document title (optional)")
        self.title_input.setMinimumHeight(32)
        self.title_input.textChanged.connect(self._update_preview)
        title_row.addWidget(self.title_input, 1)
        doc_group_layout.addLayout(title_row)
        
        doc_group_layout.addSpacing(12)
        
        self.line_numbers_check = QCheckBox("Include line numbers")
        self.line_numbers_check.setToolTip("Add line numbers to the exported output")
        self.line_numbers_check.setMinimumHeight(28)
        self.line_numbers_check.stateChanged.connect(self._update_preview)
        doc_group_layout.addWidget(self.line_numbers_check)
        
        self.metadata_check = QCheckBox("Include metadata")
        self.metadata_check.setToolTip("Include document title and date in export")
        self.metadata_check.setMinimumHeight(28)
        self.metadata_check.stateChanged.connect(self._update_preview)
        doc_group_layout.addWidget(self.metadata_check)
        
        doc_group_layout.addSpacing(8)
        
        layout.addWidget(doc_group)
        
        # Formatting options group
        fmt_group = QGroupBox("Formatting")
        fmt_group_layout = QVBoxLayout(fmt_group)
        fmt_group_layout.setSpacing(10)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Arial", "Consolas", "Courier New", "Georgia",
            "Times New Roman", "Verdana", "Tahoma"
        ])
        self.font_family_combo.currentTextChanged.connect(self._update_preview)
        self.font_family_combo.setToolTip("Select font for exported document")
        fmt_group_layout.addLayout(self._create_form_row("Font:", self.font_family_combo))
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(11)
        self.font_size_spin.setToolTip("Set font size for exported document")
        self.font_size_spin.valueChanged.connect(self._update_preview)
        fmt_group_layout.addLayout(self._create_form_row("Font size:", self.font_size_spin))
        
        layout.addWidget(fmt_group)
        
        # Format-specific options group
        self.specific_group = QGroupBox("Format-Specific Options")
        specific_layout = QVBoxLayout(self.specific_group)
        specific_layout.setSpacing(8)
        
        # HTML options
        self.html_dark_check = QCheckBox("Dark theme (HTML)")
        self.html_dark_check.setToolTip("Use dark background theme for HTML export")
        self.html_dark_check.stateChanged.connect(self._update_preview)
        specific_layout.addWidget(self.html_dark_check)
        
        self.html_css_check = QCheckBox("Inline CSS (HTML)")
        self.html_css_check.setToolTip("Embed CSS styles directly in the HTML file")
        self.html_css_check.setChecked(True)
        specific_layout.addWidget(self.html_css_check)
        
        # PDF options
        self.pdf_page_numbers_check = QCheckBox("Page numbers (PDF)")
        self.pdf_page_numbers_check.setToolTip("Add page numbers to PDF export")
        self.pdf_page_numbers_check.setChecked(True)
        specific_layout.addWidget(self.pdf_page_numbers_check)
        
        layout.addWidget(self.specific_group)
        
        # Preview group
        preview_group = QGroupBox("Preview (first 10 lines)")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setStyleSheet("font-family: Consolas; font-size: 9pt;")
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = self._create_cancel_button()
        buttons_layout.addWidget(cancel_btn)
        
        self.export_btn = QPushButton("Export...")
        self.export_btn.setToolTip("Export text to selected format")
        self.export_btn.setMinimumWidth(120)
        self.export_btn.clicked.connect(self._do_export)
        self.export_btn.setDefault(True)
        buttons_layout.addWidget(self.export_btn)
        
        layout.addLayout(buttons_layout)
        
        # Set initial visibility for format-specific options
        self._update_format_options_visibility()
    
    def _on_format_changed(self, index: int) -> None:
        """Handle format selection change."""
        self._update_format_status()
        self._update_format_options_visibility()
        self._update_preview()
    
    def _update_format_status(self) -> None:
        """Update format availability status."""
        fmt = self.format_combo.currentData()
        if fmt:
            available, message = ExportManager.check_format_dependencies(fmt)
            if available:
                self.format_status_label.setText(f"✔ {message}")
                self.format_status_label.setStyleSheet(f"font-size: 9pt; color: {self.get_colors()['success']};")
                self.export_btn.setEnabled(True)
            else:
                self.format_status_label.setText(f"✘ {message}")
                self.format_status_label.setStyleSheet(f"font-size: 9pt; color: {self.get_colors()['error']};")
                self.export_btn.setEnabled(False)
    
    def _update_format_options_visibility(self) -> None:
        """Show/hide format-specific options."""
        fmt = self.format_combo.currentData()
        
        # HTML options
        is_html = fmt == ExportFormat.HTML
        self.html_dark_check.setVisible(is_html)
        self.html_css_check.setVisible(is_html)
        
        # PDF options
        is_pdf = fmt == ExportFormat.PDF
        self.pdf_page_numbers_check.setVisible(is_pdf)
    
    def _update_preview(self) -> None:
        """Update the preview text."""
        if not self.text_content:
            self.preview_text.setPlainText("(No content to preview)")
            return
        
        lines = self.text_content.splitlines()[:10]
        
        if self.line_numbers_check.isChecked():
            total_lines = len(self.text_content.splitlines())
            width = len(str(total_lines))
            preview_lines = [
                f"{i+1:>{width}} | {line}" for i, line in enumerate(lines)
            ]
        else:
            preview_lines = lines
        
        preview = '\n'.join(preview_lines)
        if len(self.text_content.splitlines()) > 10:
            preview += "\n..."
        
        self.preview_text.setPlainText(preview)
    
    def _get_export_options(self) -> ExportOptions:
        """Get current export options from UI."""
        fmt = self.format_combo.currentData()
        
        return ExportOptions(
            format=fmt,
            include_metadata=self.metadata_check.isChecked(),
            include_line_numbers=self.line_numbers_check.isChecked(),
            page_title=self.title_input.text() or "Text Transformer Export",
            font_family=self.font_family_combo.currentText(),
            font_size=self.font_size_spin.value(),
            html_inline_css=self.html_css_check.isChecked(),
            html_dark_theme=self.html_dark_check.isChecked(),
            pdf_page_numbers=self.pdf_page_numbers_check.isChecked()
        )
    
    def _do_export(self) -> None:
        """Perform the export operation."""
        if not self.text_content:
            DialogHelper.show_warning("Warning", "No content to export", parent=self)
            return
        
        options = self._get_export_options()
        
        # Get file extension for format
        ext = ExportManager.EXTENSIONS[options.format]
        
        # Show save dialog
        default_name = f"export{ext}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Document",
            default_name,
            f"{options.format.value} (*{ext})"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            self._export_manager.export(self.text_content, file_path, options)
            
            self.export_completed.emit(file_path)
            
            DialogHelper.show_info(
                "Export Complete",
                f"Document exported successfully to:\n{file_path}",
                parent=self
            )
            
            self.accept()
            
        except ExportError as e:
            self.export_failed.emit(str(e))
            DialogHelper.show_error(
                "Export Failed",
                f"Failed to export document:\n{e}",
                parent=self
            )
    
    def set_text_content(self, text: str) -> None:
        """
        Set the text content to export.
        
        Args:
            text: Text to export
        """
        self.text_content = text
        self._update_preview()


class ExportWidget(QWidget):
    """
    Embeddable export widget for use in Settings dialog.
    
    Provides export functionality without being a standalone dialog.
    
    Signals:
        export_requested: Emitted when export is requested
    """
    
    # Signal emitted when export button clicked
    export_requested = pyqtSignal()
    
    __slots__ = (
        'theme_manager', 'font_family',
        'format_combo', 'line_numbers_check', 'metadata_check',
        'export_btn', 'status_label'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize export widget.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.font_family = font_family
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Export Output")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)
        
        subtitle = QLabel("Save your transformed text to various formats")
        subtitle.setStyleSheet(f"color: {DialogStyleManager.get_colors(self.theme_manager.is_dark_mode)['text_muted']}; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Quick export section
        export_group = QGroupBox("Quick Export")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(12)
        
        # Format row
        format_row = QHBoxLayout()
        format_label = QLabel("Format:")
        format_row.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.setToolTip("Select output file format")
        for fmt in ExportFormat:
            available, _ = ExportManager.check_format_dependencies(fmt)
            display = fmt.value
            if not available:
                display += " (unavailable)"
            self.format_combo.addItem(display, fmt)
        self.format_combo.setMinimumWidth(200)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        
        export_layout.addLayout(format_row)
        
        # Options
        self.line_numbers_check = QCheckBox("Include line numbers")
        self.line_numbers_check.setToolTip("Add line numbers to the exported output")
        export_layout.addWidget(self.line_numbers_check)
        
        self.metadata_check = QCheckBox("Include metadata")
        self.metadata_check.setToolTip("Include document title and date in export")
        export_layout.addWidget(self.metadata_check)
        
        # Export button
        button_row = QHBoxLayout()
        button_row.addStretch()
        
        self.export_btn = QPushButton("Export Output...")
        self.export_btn.setToolTip("Export text to selected format")
        self.export_btn.setFixedWidth(150)
        self.export_btn.clicked.connect(self.export_requested.emit)
        button_row.addWidget(self.export_btn)
        
        export_layout.addLayout(button_row)
        
        layout.addWidget(export_group)
        
        # Supported formats info
        info_group = QGroupBox("Supported Formats")
        info_layout = QVBoxLayout(info_group)
        
        formats_info = [
            "• TXT - Plain text (UTF-8 encoding)",
            "• DOCX - Microsoft Word document",
            "• HTML - Web page with styling",
            "• PDF - Portable Document Format",
            "• MD - Markdown document",
            "• RTF - Rich Text Format"
        ]
        
        for info in formats_info:
            label = QLabel(info)
            label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self.theme_manager.is_dark_mode)['text_disabled']};")
            info_layout.addWidget(label)
        
        layout.addWidget(info_group)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {DialogStyleManager.get_colors(self.theme_manager.is_dark_mode)['text_muted']}; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def get_selected_format(self) -> ExportFormat:
        """Get the currently selected export format."""
        return self.format_combo.currentData()
    
    def get_include_line_numbers(self) -> bool:
        """Get whether to include line numbers."""
        return self.line_numbers_check.isChecked()
    
    def get_include_metadata(self) -> bool:
        """Get whether to include metadata."""
        return self.metadata_check.isChecked()
    
    def set_status(self, message: str) -> None:
        """Set status message."""
        self.status_label.setText(message)