"""
RNV Text Transformer - Clipboard Utils Module
Handles clipboard operations

Python 3.13 Optimized:
- Modern type hints
- Cleaner exception handling
- Professional logging via Logger utility
"""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from utils.logger import get_module_logger

_logger = get_module_logger("Clipboard")


class ClipboardUtils:
    """Utility class for clipboard operations."""
    
    __slots__ = ()  # No instance attributes needed
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        Copy text to system clipboard.
        
        Args:
            text: Text to copy
        
        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False
        
        try:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)
                return True
            return False
        except Exception as e:
            logger = _logger
            if logger:
                logger.error("Error copying to clipboard", error=e)
            return False
    
    @staticmethod
    def get_clipboard_text() -> str:
        """
        Get text from system clipboard.
        
        Returns:
            Clipboard text or empty string if unavailable
        """
        try:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                return clipboard.text() or ""
            return ""
        except Exception as e:
            logger = _logger
            if logger:
                logger.error("Error reading clipboard", error=e)
            return ""
    
    @staticmethod
    def has_text() -> bool:
        """
        Check if clipboard contains text.
        
        Returns:
            True if clipboard has text
        """
        try:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                mime_data = clipboard.mimeData()
                return mime_data is not None and mime_data.hasText()
            return False
        except Exception as e:
            if _logger:
                _logger.warning("Clipboard check failed", details=str(e))
            return False