"""
RNV Text Transformer - Batch Processing Dialog Module
Dialog for batch processing multiple files

Python 3.13 Optimized:
- Modern type hints
- QThread for background processing
- Progress reporting

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QCheckBox, QProgressBar, QTextEdit,
    QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ui.base_dialog import BaseDialog
from core.batch_processor import BatchProcessor, BatchResult, BatchProgress
from core.text_transformer import TextTransformer
from utils.dialog_helper import DialogHelper

if TYPE_CHECKING:
    from core.theme_manager import ThemeManager


class BatchWorkerThread(QThread):
    """Background thread for batch processing."""
    
    progress_update = pyqtSignal(int, int, str)  # current, total, filename
    file_processed = pyqtSignal(object)  # BatchResult
    finished_processing = pyqtSignal(list)  # List of BatchResult
    
    __slots__ = ('processor', 'folder')
    
    def __init__(self, processor: BatchProcessor, folder: Path) -> None:
        super().__init__()
        self.processor = processor
        self.folder = folder
    
    def run(self) -> None:
        """Execute batch processing."""
        results: list[BatchResult] = []
        
        generator = self.processor.process_folder(self.folder)
        
        try:
            while True:
                progress, result = next(generator)
                self.progress_update.emit(
                    progress.current,
                    progress.total,
                    progress.current_file
                )
                if result is not None:
                    results.append(result)
                    self.file_processed.emit(result)
        except StopIteration as e:
            # Generator finished, get final results
            if e.value:
                results = e.value
        
        self.finished_processing.emit(results)
    
    def cancel(self) -> None:
        """Request cancellation."""
        self.processor.cancel()


class BatchDialog(BaseDialog):
    """
    Batch processing dialog for transforming multiple files.
    
    Features:
    - Select source folder
    - Optional output folder
    - Recursive processing option
    - Progress display
    - Results log
    """
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 600
    _DIALOG_HEIGHT: ClassVar[int] = 550
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Batch Processing"
    
    __slots__ = (
        'source_input', 'output_input', 'mode_combo',
        'recursive_check', 'same_location_check',
        'progress_bar', 'progress_label', 'log_text',
        'start_btn', 'cancel_btn', 'close_btn',
        '_worker_thread', '_results'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize batch dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self._worker_thread: BatchWorkerThread | None = None
        self._results: list[BatchResult] = []
        
        self._setup_ui()
        self.apply_extended_styling('progressbar')
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Source folder
        source_group = QGroupBox("Source Folder")
        source_layout = QHBoxLayout(source_group)
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select folder containing files to process...")
        self.source_input.setReadOnly(True)
        source_layout.addWidget(self.source_input)
        
        browse_source_btn = QPushButton("Browse...")
        browse_source_btn.setToolTip("Select folder containing files to process")
        browse_source_btn.clicked.connect(self._browse_source)
        source_layout.addWidget(browse_source_btn)
        
        layout.addWidget(source_group)
        
        # Output folder
        output_group = QGroupBox("Output Location")
        output_layout = QVBoxLayout(output_group)
        
        self.same_location_check = QCheckBox("Save to same location (add '_transformed' suffix)")
        self.same_location_check.setToolTip("Save transformed files alongside originals with '_transformed' suffix")
        self.same_location_check.setChecked(True)
        self.same_location_check.stateChanged.connect(self._on_same_location_changed)
        output_layout.addWidget(self.same_location_check)
        
        output_row = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Select output folder...")
        self.output_input.setReadOnly(True)
        self.output_input.setEnabled(False)
        output_row.addWidget(self.output_input)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.setToolTip("Select a different output folder")
        self.browse_output_btn.clicked.connect(self._browse_output)
        self.browse_output_btn.setEnabled(False)
        output_row.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(output_row)
        layout.addWidget(output_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout(options_group)
        
        mode_label = QLabel("Transform Mode:")
        options_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(TextTransformer.get_available_modes())
        self.mode_combo.setToolTip("Select text transformation mode")
        self.mode_combo.setFixedWidth(150)
        options_layout.addWidget(self.mode_combo)
        
        options_layout.addSpacing(20)
        
        self.recursive_check = QCheckBox("Include subfolders")
        self.recursive_check.setToolTip("Also process files in subfolders")
        options_layout.addWidget(self.recursive_check)
        
        options_layout.addStretch()
        layout.addWidget(options_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setToolTip("Begin batch processing all files in source folder")
        self.start_btn.clicked.connect(self._start_processing)
        buttons_layout.addWidget(self.start_btn)
        
        self.cancel_btn = self._create_action_button("Cancel", self._cancel_processing, enabled=False)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.close_btn = self._create_action_button("Close", self.close)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _browse_source(self) -> None:
        """Browse for source folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Source Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.source_input.setText(folder)
            self._update_file_count()
    
    def _browse_output(self) -> None:
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_input.setText(folder)
    
    def _on_same_location_changed(self, state: int) -> None:
        """Handle same location checkbox change."""
        is_same = state == Qt.CheckState.Checked.value
        self.output_input.setEnabled(not is_same)
        self.browse_output_btn.setEnabled(not is_same)
        if is_same:
            self.output_input.clear()
    
    def _update_file_count(self) -> None:
        """Update file count display."""
        source = self.source_input.text()
        if not source:
            return
        
        folder = Path(source)
        if not folder.exists():
            return
        
        # Create temp processor to count files
        processor = BatchProcessor(
            transform_mode="",
            recursive=self.recursive_check.isChecked()
        )
        files = processor.get_supported_files(folder)
        self.progress_label.setText(f"Found {len(files)} supported file(s)")
    
    def _start_processing(self) -> None:
        """Start batch processing."""
        source = self.source_input.text()
        if not source:
            DialogHelper.show_warning("Warning", "Please select a source folder", parent=self)
            return
        
        folder = Path(source)
        if not folder.exists():
            DialogHelper.show_warning("Warning", "Source folder does not exist", parent=self)
            return
        
        # Determine output folder
        output_folder: Path | None = None
        if not self.same_location_check.isChecked():
            output = self.output_input.text()
            if not output:
                DialogHelper.show_warning("Warning", "Please select an output folder", parent=self)
                return
            output_folder = Path(output)
        
        # Create processor
        processor = BatchProcessor(
            transform_mode=self.mode_combo.currentText(),
            recursive=self.recursive_check.isChecked(),
            output_folder=output_folder
        )
        
        # Check file count
        files = processor.get_supported_files(folder)
        if not files:
            DialogHelper.show_info("Info", "No supported files found in folder", parent=self)
            return
        
        # Confirm
        if not DialogHelper.confirm(
            "Confirm",
            f"Process {len(files)} file(s) with '{self.mode_combo.currentText()}' transform?",
            parent=self
        ):
            return
        
        # Setup UI for processing
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(files))
        self.log_text.clear()
        self._results.clear()
        
        # Start worker thread
        self._worker_thread = BatchWorkerThread(processor, folder)
        self._worker_thread.progress_update.connect(self._on_progress)
        self._worker_thread.file_processed.connect(self._on_file_processed)
        self._worker_thread.finished_processing.connect(self._on_finished)
        self._worker_thread.start()
    
    def _cancel_processing(self) -> None:
        """Cancel batch processing."""
        if self._worker_thread is not None:
            self._worker_thread.cancel()
            self.progress_label.setText("Cancelling...")
    
    def _on_progress(self, current: int, total: int, filename: str) -> None:
        """Handle progress update."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Processing {current}/{total}: {filename}")
    
    def _on_file_processed(self, result: BatchResult) -> None:
        """Handle file processed result."""
        status = "✔" if result.success else "✘"
        self.log_text.append(f"{status} {result.file_path.name}: {result.message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def _on_finished(self, results: list[BatchResult]) -> None:
        """Handle processing finished."""
        self._results = results
        
        # Get summary
        summary = BatchProcessor.get_summary(results)
        
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_label.setText(
            f"Complete: {summary['successful']}/{summary['total_files']} successful"
        )
        
        self.log_text.append("")
        self.log_text.append(f"{'='*40}")
        self.log_text.append(f"Total files: {summary['total_files']}")
        self.log_text.append(f"Successful: {summary['successful']}")
        self.log_text.append(f"Failed: {summary['failed']}")
        
        # Reset UI
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        self._worker_thread = None
    
    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        if self._worker_thread is not None and self._worker_thread.isRunning():
            if DialogHelper.confirm(
                "Confirm",
                "Processing is in progress. Cancel and close?",
                parent=self
            ):
                self._worker_thread.cancel()
                self._worker_thread.wait(2000)
            else:
                event.ignore()
                return
        
        super().closeEvent(event)