"""
RNV Text Transformer - Dialog Helper Module
Standardized QMessageBox dialogs for consistent user interaction.

Python 3.13 Optimized:
- Modern type hints
- Enum for dialog results
- Static methods for easy access
- Theme-aware styling

Usage:
    from utils.dialog_helper import DialogHelper, DialogResult
    
    # Information dialog
    DialogHelper.show_info("Operation Complete", "Files processed successfully.")
    
    # Warning dialog
    DialogHelper.show_warning("Warning", "Some files could not be processed.")
    
    # Error dialog
    DialogHelper.show_error("Error", "Failed to save file.", details=str(exception))
    
    # Confirmation dialog
    if DialogHelper.confirm("Confirm Delete", "Are you sure?"):
        delete_file()
    
    # Yes/No/Cancel dialog
    result = DialogHelper.ask_yes_no_cancel("Save Changes", "Save before closing?")
    if result == DialogResult.YES:
        save()
    elif result == DialogResult.NO:
        discard()
    else:
        cancel_close()
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    pass


class DialogResult(Enum):
    """Result values for dialog interactions."""
    YES = auto()
    NO = auto()
    CANCEL = auto()
    OK = auto()
    RETRY = auto()
    IGNORE = auto()


class DialogHelper:
    """
    Standardized dialog helper for consistent user interactions.
    
    Provides static methods for common dialog patterns:
    - Information messages
    - Warning messages
    - Error messages
    - Confirmation dialogs
    - Yes/No/Cancel dialogs
    - Input dialogs (future)
    
    All dialogs support optional detailed text for exceptions.
    """
    
    # Default window title prefix
    _APP_NAME: str = "Text Transformer"
    
    @classmethod
    def set_app_name(cls, name: str) -> None:
        """
        Set the application name used in dialog titles.
        
        Args:
            name: Application name
        """
        cls._APP_NAME = name
    
    @staticmethod
    def show_info(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text (shown in expandable section)
            parent: Parent widget
            
        Example:
            DialogHelper.show_info("Success", "File saved successfully.")
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
    
    @staticmethod
    def show_warning(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text
            parent: Parent widget
            
        Example:
            DialogHelper.show_warning("Warning", "Some files were skipped.")
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
    
    @staticmethod
    def show_error(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text (useful for exception info)
            parent: Parent widget
            
        Example:
            try:
                risky_operation()
            except Exception as e:
                DialogHelper.show_error("Error", "Operation failed.", details=str(e))
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
    
    @staticmethod
    def confirm(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> bool:
        """
        Show a confirmation dialog (Yes/No).
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text
            parent: Parent widget
            
        Returns:
            True if user clicked Yes, False otherwise
            
        Example:
            if DialogHelper.confirm("Delete", "Delete selected files?"):
                delete_files()
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
        return dialog.exec() == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def ask_yes_no_cancel(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> DialogResult:
        """
        Show a Yes/No/Cancel dialog.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text
            parent: Parent widget
            
        Returns:
            DialogResult.YES, DialogResult.NO, or DialogResult.CANCEL
            
        Example:
            result = DialogHelper.ask_yes_no_cancel("Save", "Save changes?")
            if result == DialogResult.YES:
                save_document()
            elif result == DialogResult.NO:
                discard_changes()
            else:
                return  # Cancel the operation
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        result = dialog.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            return DialogResult.YES
        elif result == QMessageBox.StandardButton.No:
            return DialogResult.NO
        else:
            return DialogResult.CANCEL
    
    @staticmethod
    def ask_retry_cancel(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> DialogResult:
        """
        Show a Retry/Cancel dialog for recoverable errors.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text
            parent: Parent widget
            
        Returns:
            DialogResult.RETRY or DialogResult.CANCEL
            
        Example:
            while True:
                try:
                    connect_to_server()
                    break
                except ConnectionError as e:
                    result = DialogHelper.ask_retry_cancel(
                        "Connection Failed",
                        "Could not connect to server.",
                        details=str(e)
                    )
                    if result == DialogResult.CANCEL:
                        return
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Retry | 
            QMessageBox.StandardButton.Cancel
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Retry)
        
        result = dialog.exec()
        
        if result == QMessageBox.StandardButton.Retry:
            return DialogResult.RETRY
        else:
            return DialogResult.CANCEL
    
    @staticmethod
    def show_about(
        title: str,
        message: str,
        parent: QWidget | None = None
    ) -> None:
        """
        Show an About dialog.
        
        Args:
            title: Dialog title
            message: About text (can include HTML)
            parent: Parent widget
            
        Example:
            DialogHelper.show_about(
                "About Text Transformer",
                "<h3>RNV Text Transformer</h3>"
                f"<p>Version {APP_VERSION}</p>"  # from utils.config
                "<p>A professional text transformation tool.</p>"
            )
        """
        QMessageBox.about(parent, title, message)
    
    @staticmethod
    def show_critical(
        title: str,
        message: str,
        details: str | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Show a critical error dialog.
        
        Same as show_error but semantically indicates a severe issue.
        
        Args:
            title: Dialog title
            message: Main message
            details: Optional detailed text
            parent: Parent widget
        """
        DialogHelper.show_error(title, message, details, parent)


# Convenience functions for quick access (renamed to avoid shadowing logger functions)
def show_info(title: str, message: str, details: str | None = None, parent: QWidget | None = None) -> None:
    """Show info dialog."""
    DialogHelper.show_info(title, message, details, parent)


def show_warning(title: str, message: str, details: str | None = None, parent: QWidget | None = None) -> None:
    """Show warning dialog."""
    DialogHelper.show_warning(title, message, details, parent)


def show_error(title: str, message: str, details: str | None = None, parent: QWidget | None = None) -> None:
    """Show error dialog."""
    DialogHelper.show_error(title, message, details, parent)


def confirm(title: str, message: str, details: str | None = None, parent: QWidget | None = None) -> bool:
    """Show confirmation dialog."""
    return DialogHelper.confirm(title, message, details, parent)


def ask_save(parent: QWidget | None = None) -> DialogResult:
    """
    Convenience function for "Save changes?" dialog.
    
    Returns:
        DialogResult.YES (save), DialogResult.NO (don't save), or DialogResult.CANCEL
    """
    return DialogHelper.ask_yes_no_cancel(
        "Save Changes",
        "Do you want to save your changes?",
        parent=parent
    )