"""
RNV Text Transformer - Async Workers Module
Background thread workers for file loading and text transformation

Python 3.13 Optimized:
- QThread-based workers for non-blocking operations
- Signal-based communication with main thread
- Proper cleanup and cancellation support
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

from utils.file_handler import FileHandler, FileReadError
from core.text_transformer import TextTransformer
from utils.logger import get_module_logger

_logger = get_module_logger("AsyncWorkers")

if TYPE_CHECKING:
    pass


# Threshold for using background thread (100KB)
LARGE_TEXT_THRESHOLD: int = 100_000


class FileLoaderThread(QThread):
    """
    Background thread for loading files without blocking the UI.
    
    Signals:
        finished: Emitted with (content, filename) on success
        error: Emitted with error message on failure
        progress: Emitted with percentage (0-100) for progress updates
    """
    
    finished = pyqtSignal(str, str)  # content, filename
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    __slots__ = ('file_path', '_cancelled')
    
    def __init__(self, file_path: str) -> None:
        """
        Initialize file loader thread.
        
        Args:
            file_path: Path to file to load
        """
        super().__init__()
        self.file_path = file_path
        self._cancelled = False
    
    def run(self) -> None:
        """Execute file loading in background thread."""
        if self._cancelled:
            return
        
        try:
            self.progress.emit(10)  # Started
            
            content = FileHandler.read_file_content(self.file_path)
            
            if self._cancelled:
                return
            
            self.progress.emit(90)  # Almost done
            
            if content is not None:
                filename = FileHandler.get_file_name(self.file_path)
                self.progress.emit(100)
                self.finished.emit(content, filename)
            else:
                self.error.emit("Could not read file content")
                
        except FileReadError as e:
            if not self._cancelled:
                if _logger:
                    _logger.warning(f"File load failed: {self.file_path}", details=str(e))
                self.error.emit(str(e))
        except Exception as e:
            if not self._cancelled:
                if _logger:
                    _logger.error(f"Unexpected file load error: {self.file_path}", error=e)
                self.error.emit(f"Unexpected error: {e}")
    
    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled = True


class TextTransformThread(QThread):
    """
    Background thread for text transformation without blocking the UI.
    
    Used for large text blocks that would cause noticeable UI lag.
    
    Signals:
        finished: Emitted with transformed text on success
        error: Emitted with error message on failure
        progress: Emitted with percentage (0-100) for progress updates
    """
    
    finished = pyqtSignal(str)  # transformed text
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    __slots__ = ('text', 'mode', '_cancelled')
    
    def __init__(self, text: str, mode: str) -> None:
        """
        Initialize text transform thread.
        
        Args:
            text: Text to transform
            mode: Transformation mode
        """
        super().__init__()
        self.text = text
        self.mode = mode
        self._cancelled = False
    
    def run(self) -> None:
        """Execute text transformation in background thread."""
        if self._cancelled:
            return
        
        try:
            self.progress.emit(20)  # Started
            
            result = TextTransformer.transform_text(self.text, self.mode)
            
            if self._cancelled:
                return
            
            self.progress.emit(100)
            self.finished.emit(result)
            
        except Exception as e:
            if not self._cancelled:
                if _logger:
                    _logger.error(f"Transform error in mode '{self.mode}'", error=e)
                self.error.emit(f"Transform error: {e}")
    
    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled = True


def should_use_thread_for_transform(text: str) -> bool:
    """
    Determine if text transformation should use a background thread.
    
    Args:
        text: Text to be transformed
        
    Returns:
        True if text is large enough to warrant background processing
    """
    return len(text) > LARGE_TEXT_THRESHOLD
