"""
RNV Text Transformer - Encoding Dialog Module
Dialog for detecting and converting text encodings

Python 3.13 Optimized:
- Modern type hints
- Encoding detection with chardet
- Live preview of conversion results
- Mojibake repair functionality

"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from dataclasses import dataclass
from enum import StrEnum

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QComboBox, QPushButton, QGroupBox,
    QTextEdit, QFormLayout,
    QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from utils.dialog_helper import DialogHelper

from ui.base_dialog import BaseDialog
from core.theme_manager import ThemeManager

class CommonEncoding(StrEnum):
    """Common text encodings."""
    UTF_8 = "utf-8"
    UTF_8_BOM = "utf-8-sig"
    UTF_16 = "utf-16"
    UTF_16_LE = "utf-16-le"
    UTF_16_BE = "utf-16-be"
    ASCII = "ascii"
    LATIN_1 = "iso-8859-1"
    WINDOWS_1252 = "windows-1252"
    WINDOWS_1250 = "windows-1250"
    WINDOWS_1251 = "windows-1251"
    CP437 = "cp437"
    MAC_ROMAN = "mac-roman"
    
    @classmethod
    def get_display_name(cls, encoding: str) -> str:
        """Get human-readable name for encoding."""
        display_names = {
            "utf-8": "UTF-8 (Unicode)",
            "utf-8-sig": "UTF-8 with BOM",
            "utf-16": "UTF-16 (Unicode)",
            "utf-16-le": "UTF-16 Little Endian",
            "utf-16-be": "UTF-16 Big Endian",
            "ascii": "ASCII (7-bit)",
            "iso-8859-1": "Latin-1 (ISO-8859-1)",
            "windows-1252": "Windows-1252 (Western)",
            "windows-1250": "Windows-1250 (Central European)",
            "windows-1251": "Windows-1251 (Cyrillic)",
            "cp437": "CP437 (DOS/IBM PC)",
            "mac-roman": "Mac Roman",
        }
        return display_names.get(encoding, encoding.upper())

@dataclass
class EncodingResult:
    """Result of encoding detection or conversion."""
    success: bool
    encoding: str
    confidence: float
    text: str
    message: str = ""

class EncodingDetector:
    """
    Handles encoding detection and conversion.
    
    Uses chardet for detection with fallback to common encodings.
    """
    
    # Common encodings to try as fallback
    FALLBACK_ENCODINGS: ClassVar[list[str]] = [
        'utf-8', 'windows-1252', 'iso-8859-1', 'ascii',
        'utf-16', 'windows-1251', 'windows-1250'
    ]
    
    @staticmethod
    def detect_encoding(data: bytes) -> EncodingResult:
        """
        Detect encoding of byte data.
        
        Args:
            data: Raw byte data to analyze
            
        Returns:
            EncodingResult with detected encoding info
        """
        if not data:
            return EncodingResult(
                success=False,
                encoding="",
                confidence=0.0,
                text="",
                message="No data to analyze"
            )
        
        # Try chardet first
        try:
            import chardet  # type: ignore[import-not-found]
            result = chardet.detect(data)
            
            if result and result.get('encoding'):
                encoding = result['encoding'].lower()
                confidence = result.get('confidence', 0.0)
                
                # Try to decode with detected encoding
                try:
                    text = data.decode(encoding)
                    return EncodingResult(
                        success=True,
                        encoding=encoding,
                        confidence=confidence,
                        text=text,
                        message=f"Detected {encoding} with {confidence*100:.1f}% confidence"
                    )
                except (UnicodeDecodeError, LookupError):
                    pass
                    
        except ImportError:
            # chardet not available, use fallback
            pass
        except Exception:
            pass
        
        # Fallback: try common encodings
        for encoding in EncodingDetector.FALLBACK_ENCODINGS:
            try:
                text = data.decode(encoding)
                return EncodingResult(
                    success=True,
                    encoding=encoding,
                    confidence=0.5,
                    text=text,
                    message=f"Decoded using fallback: {encoding}"
                )
            except (UnicodeDecodeError, LookupError):
                continue
        
        return EncodingResult(
            success=False,
            encoding="",
            confidence=0.0,
            text="",
            message="Could not detect encoding"
        )
    
    @staticmethod
    def convert_encoding(
        text: str,
        from_encoding: str,
        to_encoding: str,
        errors: str = 'replace'
    ) -> EncodingResult:
        """
        Convert text between encodings.
        
        Args:
            text: Text to convert
            from_encoding: Source encoding (for re-interpretation)
            to_encoding: Target encoding
            errors: Error handling ('strict', 'replace', 'ignore')
            
        Returns:
            EncodingResult with converted text
        """
        try:
            # First encode to bytes using source encoding
            # This handles cases where text was decoded incorrectly
            try:
                raw_bytes = text.encode('latin-1')
            except UnicodeEncodeError:
                # Text contains characters outside latin-1, encode directly
                raw_bytes = text.encode(from_encoding, errors=errors)
            
            # Re-decode with correct encoding
            converted = raw_bytes.decode(to_encoding, errors=errors)
            
            return EncodingResult(
                success=True,
                encoding=to_encoding,
                confidence=1.0,
                text=converted,
                message=f"Converted from {from_encoding} to {to_encoding}"
            )
            
        except Exception as e:
            return EncodingResult(
                success=False,
                encoding=to_encoding,
                confidence=0.0,
                text=text,
                message=f"Conversion failed: {e}"
            )
    
    @staticmethod
    def fix_mojibake(text: str, wrong_encoding: str, correct_encoding: str) -> EncodingResult:
        """
        Fix mojibake (garbled text from wrong encoding).
        
        Args:
            text: Garbled text
            wrong_encoding: Encoding incorrectly used to decode
            correct_encoding: Correct encoding to use
            
        Returns:
            EncodingResult with fixed text
        """
        try:
            # Re-encode with wrong encoding, then decode with correct
            raw_bytes = text.encode(wrong_encoding, errors='replace')
            fixed = raw_bytes.decode(correct_encoding, errors='replace')
            
            return EncodingResult(
                success=True,
                encoding=correct_encoding,
                confidence=0.8,
                text=fixed,
                message=f"Fixed mojibake: {wrong_encoding} → {correct_encoding}"
            )
            
        except Exception as e:
            return EncodingResult(
                success=False,
                encoding=correct_encoding,
                confidence=0.0,
                text=text,
                message=f"Mojibake fix failed: {e}"
            )

class DetectionThread(QThread):
    """Background thread for encoding detection."""
    
    finished = pyqtSignal(object)  # EncodingResult
    
    def __init__(self, data: bytes) -> None:
        super().__init__()
        self.data = data
    
    def run(self) -> None:
        """Execute detection in background."""
        result = EncodingDetector.detect_encoding(self.data)
        self.finished.emit(result)

class EncodingDialog(BaseDialog):
    """
    Encoding conversion dialog.
    
    Features:
    - Auto-detect current encoding
    - Convert between encodings
    - Preview conversion result
    - Fix mojibake (garbled text)
    - Common encoding presets
    
    Signals:
        encoding_applied: Emitted when user applies encoding change
    """
    
    encoding_applied = pyqtSignal(str)  # converted text
    
    # Dialog configuration
    _DIALOG_WIDTH: ClassVar[int] = 700
    _DIALOG_HEIGHT: ClassVar[int] = 600
    _DIALOG_TITLE: ClassVar[str] = "Text Transformer - Encoding Converter"
    _RESIZABLE: ClassVar[bool] = True
    
    __slots__ = (
        'input_text',
        'source_combo', 'target_combo', 'error_handling_combo',
        'input_preview', 'output_preview', 'status_label',
        'confidence_label', 'detect_btn', 'convert_btn',
        'mojibake_check', '_detection_thread', '_original_bytes'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        input_text: str = "",
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize encoding dialog.
        
        Args:
            theme_manager: Theme manager instance
            font_family: Font family to use
            input_text: Text to process
            parent: Parent widget
        """
        super().__init__(theme_manager, font_family, parent)
        
        self.input_text = input_text
        self._detection_thread: DetectionThread | None = None
        self._original_bytes: bytes = b""
        
        self._setup_ui()
        self.apply_extended_styling('tab', 'table')
        self._load_text()
    

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = self._create_main_layout()
        
        # Header
        header = QLabel("Encoding Converter")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)
        
        subtitle = QLabel("Detect and convert text between different character encodings")
        c = self.get_colors()
        subtitle.setStyleSheet(f"color: {c['text_muted']}; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Encoding selection group
        encoding_group = QGroupBox("Encoding Settings")
        encoding_layout = QFormLayout(encoding_group)
        encoding_layout.setSpacing(10)
        encoding_layout.setHorizontalSpacing(15)
        
        # Source encoding
        source_layout = QHBoxLayout()
        self.source_combo = QComboBox()
        self.source_combo.setToolTip("Select the current encoding of the text")
        self._populate_encoding_combo(self.source_combo)
        self.source_combo.setCurrentText(CommonEncoding.get_display_name("utf-8"))
        source_layout.addWidget(self.source_combo)
        
        self.detect_btn = QPushButton("Auto-Detect")
        self.detect_btn.setToolTip("Automatically detect the source encoding")
        self.detect_btn.clicked.connect(self._detect_encoding)
        self.detect_btn.setFixedWidth(130)
        source_layout.addWidget(self.detect_btn)
        
        source_label = QLabel("Source Encoding:")
        source_label.setMinimumWidth(140)
        encoding_layout.addRow(source_label, source_layout)
        
        # Confidence indicator
        self.confidence_label = QLabel("Confidence: --")
        self.confidence_label.setStyleSheet(f"color: {c['text_muted']};")
        encoding_layout.addRow("", self.confidence_label)
        
        # Target encoding
        self.target_combo = QComboBox()
        self.target_combo.setToolTip("Select the target encoding to convert to")
        self._populate_encoding_combo(self.target_combo)
        self.target_combo.setCurrentText(CommonEncoding.get_display_name("utf-8"))
        target_label = QLabel("Target Encoding:")
        target_label.setMinimumWidth(140)
        encoding_layout.addRow(target_label, self.target_combo)
        
        # Error handling
        self.error_handling_combo = QComboBox()
        self.error_handling_combo.setToolTip("How to handle characters that can't be converted")
        self.error_handling_combo.addItems([
            "Replace invalid characters with ?",
            "Ignore invalid characters",
            "Strict (fail on invalid)"
        ])
        error_label = QLabel("Error Handling:")
        error_label.setMinimumWidth(140)
        encoding_layout.addRow(error_label, self.error_handling_combo)
        
        # Mojibake fix option
        self.mojibake_check = QCheckBox("Fix mojibake (garbled text repair)")
        self.mojibake_check.setToolTip(
            "Use this if text was decoded with wrong encoding and appears garbled"
        )
        encoding_layout.addRow("", self.mojibake_check)
        
        layout.addWidget(encoding_group)
        
        # Preview splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Input preview
        input_group = QGroupBox("Input Preview")
        input_layout = QVBoxLayout(input_group)
        self.input_preview = QTextEdit()
        self.input_preview.setReadOnly(True)
        self.input_preview.setMaximumHeight(150)
        input_layout.addWidget(self.input_preview)
        splitter.addWidget(input_group)
        
        # Output preview
        output_group = QGroupBox("Output Preview")
        output_layout = QVBoxLayout(output_group)
        self.output_preview = QTextEdit()
        self.output_preview.setReadOnly(True)
        self.output_preview.setMaximumHeight(150)
        output_layout.addWidget(self.output_preview)
        splitter.addWidget(output_group)
        
        layout.addWidget(splitter)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {c['text_muted']};")
        layout.addWidget(self.status_label)
        
        # Buttons
        self.convert_btn = QPushButton("Preview Conversion")
        self.convert_btn.setToolTip("Preview the encoding conversion result")
        self.convert_btn.clicked.connect(self._preview_conversion)
        
        apply_btn = QPushButton("Apply to Document")
        apply_btn.setToolTip("Apply the encoding conversion to the document")
        apply_btn.clicked.connect(self._apply_encoding)
        
        close_btn = self._create_action_button("Close", self.close)
        
        layout.addLayout(self._create_button_row(self.convert_btn, apply_btn, close_btn))
    
    def _populate_encoding_combo(self, combo: QComboBox) -> None:
        """Populate encoding combo with common encodings."""
        encodings = [
            ("utf-8", "UTF-8 (Unicode)"),
            ("utf-8-sig", "UTF-8 with BOM"),
            ("utf-16", "UTF-16 (Unicode)"),
            ("utf-16-le", "UTF-16 Little Endian"),
            ("utf-16-be", "UTF-16 Big Endian"),
            ("ascii", "ASCII (7-bit)"),
            ("iso-8859-1", "Latin-1 (ISO-8859-1)"),
            ("windows-1252", "Windows-1252 (Western)"),
            ("windows-1250", "Windows-1250 (Central European)"),
            ("windows-1251", "Windows-1251 (Cyrillic)"),
            ("cp437", "CP437 (DOS/IBM PC)"),
            ("mac-roman", "Mac Roman"),
        ]
        
        for encoding, display in encodings:
            combo.addItem(display, encoding)
    
    def _get_selected_encoding(self, combo: QComboBox) -> str:
        """Get the encoding value from combo selection."""
        return combo.currentData() or "utf-8"
    
    def _get_error_mode(self) -> str:
        """Get error handling mode from combo."""
        index = self.error_handling_combo.currentIndex()
        return ['replace', 'ignore', 'strict'][index]
    

    def _load_text(self) -> None:
        """Load input text into preview."""
        # Store as bytes for detection
        try:
            self._original_bytes = self.input_text.encode('utf-8')
        except Exception:
            self._original_bytes = self.input_text.encode('latin-1', errors='replace')
        
        # Show preview (first 500 chars)
        preview = self.input_text[:500]
        if len(self.input_text) > 500:
            preview += "\n\n... (truncated)"
        self.input_preview.setPlainText(preview)
    
    def _detect_encoding(self) -> None:
        """Auto-detect encoding of input text."""
        if not self._original_bytes:
            self.status_label.setText("No text to analyze")
            return
        
        self.status_label.setText("Detecting encoding...")
        self.detect_btn.setEnabled(False)
        
        # Run detection in background
        self._detection_thread = DetectionThread(self._original_bytes)
        self._detection_thread.finished.connect(self._on_detection_complete)
        self._detection_thread.start()
    
    def _on_detection_complete(self, result: EncodingResult) -> None:
        """Handle encoding detection completion."""
        self.detect_btn.setEnabled(True)
        
        if result.success:
            # Find and select the detected encoding
            encoding = result.encoding.lower()
            for i in range(self.source_combo.count()):
                if self.source_combo.itemData(i) == encoding:
                    self.source_combo.setCurrentIndex(i)
                    break
            
            confidence_pct = result.confidence * 100
            self.confidence_label.setText(f"Confidence: {confidence_pct:.1f}%")
            
            if confidence_pct >= 90:
                self.confidence_label.setStyleSheet(f"color: {self.get_colors()['success']};")
            elif confidence_pct >= 70:
                self.confidence_label.setStyleSheet(f"color: {self.get_colors()['warning']};")
            else:
                self.confidence_label.setStyleSheet(f"color: {self.get_colors()['error']};")
            
            self.status_label.setText(result.message)
        else:
            self.status_label.setText(f"Detection failed: {result.message}")
            self.confidence_label.setText("Confidence: --")
            self.confidence_label.setStyleSheet(f"color: {self.get_colors()['text_muted']};")
    
    def _preview_conversion(self) -> None:
        """Preview encoding conversion."""
        source_encoding = self._get_selected_encoding(self.source_combo)
        target_encoding = self._get_selected_encoding(self.target_combo)
        error_mode = self._get_error_mode()
        
        if self.mojibake_check.isChecked():
            # Mojibake fix mode
            result = EncodingDetector.fix_mojibake(
                self.input_text,
                source_encoding,
                target_encoding
            )
        else:
            # Normal conversion
            result = EncodingDetector.convert_encoding(
                self.input_text,
                source_encoding,
                target_encoding,
                error_mode
            )
        
        if result.success:
            # Show preview (first 500 chars)
            preview = result.text[:500]
            if len(result.text) > 500:
                preview += "\n\n... (truncated)"
            self.output_preview.setPlainText(preview)
            self.status_label.setText(result.message)
        else:
            self.output_preview.setPlainText(f"Error: {result.message}")
            self.status_label.setText(f"Conversion failed: {result.message}")
    
    def _apply_encoding(self) -> None:
        """Apply encoding conversion and emit result."""
        source_encoding = self._get_selected_encoding(self.source_combo)
        target_encoding = self._get_selected_encoding(self.target_combo)
        error_mode = self._get_error_mode()
        
        if self.mojibake_check.isChecked():
            result = EncodingDetector.fix_mojibake(
                self.input_text,
                source_encoding,
                target_encoding
            )
        else:
            result = EncodingDetector.convert_encoding(
                self.input_text,
                source_encoding,
                target_encoding,
                error_mode
            )
        
        if result.success:
            self.encoding_applied.emit(result.text)
            self.accept()
        else:
            DialogHelper.show_warning(
                "Conversion Failed",
                f"Could not convert encoding: {result.message}",
                parent=self
            )
    
    def set_text(self, text: str) -> None:
        """
        Set input text.
        
        Args:
            text: Text to process
        """
        self.input_text = text
        self._load_text()
    
    def closeEvent(self, event) -> None:
        """Handle dialog close - clean up threads."""
        if self._detection_thread is not None and self._detection_thread.isRunning():
            self._detection_thread.wait(1000)
        super().closeEvent(event)

class EncodingWidget(QWidget):
    """
    Standalone encoding widget for embedding in other dialogs.
    
    Provides the same functionality as EncodingDialog but as a widget.
    """
    
    encoding_changed = pyqtSignal(str)  # converted text
    
    __slots__ = (
        'theme_manager', 'font_family', 'input_text',
        'source_combo', 'target_combo', '_detector'
    )
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        font_family: str = "Arial",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.font_family = font_family
        self.input_text = ""
        self._detector = EncodingDetector()
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("From:"))
        self.source_combo = QComboBox()
        self.source_combo.setToolTip("Source encoding")
        self._populate_combo(self.source_combo)
        layout.addWidget(self.source_combo)
        
        layout.addWidget(QLabel("To:"))
        self.target_combo = QComboBox()
        self.target_combo.setToolTip("Target encoding")
        self._populate_combo(self.target_combo)
        layout.addWidget(self.target_combo)
        
        convert_btn = QPushButton("Convert")
        convert_btn.setToolTip("Convert text encoding")
        convert_btn.clicked.connect(self._convert)
        layout.addWidget(convert_btn)
        
        layout.addStretch()
    
    def _populate_combo(self, combo: QComboBox) -> None:
        """Populate encoding combo."""
        encodings = [
            ("utf-8", "UTF-8"),
            ("windows-1252", "Windows-1252"),
            ("iso-8859-1", "Latin-1"),
            ("ascii", "ASCII"),
        ]
        for encoding, display in encodings:
            combo.addItem(display, encoding)
    
    def set_text(self, text: str) -> None:
        """Set text to convert."""
        self.input_text = text
    
    def _convert(self) -> None:
        """Execute conversion."""
        source = self.source_combo.currentData()
        target = self.target_combo.currentData()
        
        result = EncodingDetector.convert_encoding(
            self.input_text, source, target
        )
        
        if result.success:
            self.encoding_changed.emit(result.text)