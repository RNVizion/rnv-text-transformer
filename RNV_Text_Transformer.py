#!/usr/bin/env python3
"""
RNV Text Transformer - Main Application Entry Point

A professional text transformation application with support for:
- 11 transformation modes (UPPERCASE, lowercase, Title Case, Sentence case,
  camelCase, PascalCase, snake_case, kebab-case, CONSTANT_CASE, Alternating, Reverse)
- Multiple file formats (TXT, MD, DOCX, PDF, RTF, PY, JS, HTML, LOG)
- Multi-format export (TXT, DOCX, HTML, PDF, MD, RTF)
- Drag & drop file loading with async support for large files
- Three theme modes (Dark, Light, Image with custom graphics)
- Find & Replace with regex support
- Batch processing for multiple files
- Compare view with difference highlighting
- Text cleanup and split/join operations
- Line numbers toggle and clipboard history
- Text statistics, auto-transform, undo/redo
- Settings persistence and keyboard shortcuts
- Professional logging system

Requires: Python 3.10+, PyQt6, Pillow, python-docx, pypdf, striprtf
Optional: reportlab (for PDF export)
"""

from __future__ import annotations

import sys

# Python version check - requires 3.10+ for match statements and modern type hints
MIN_PYTHON_VERSION = (3, 10)
if sys.version_info < MIN_PYTHON_VERSION:
    sys.exit(
        f"Error: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required "
        f"(found {sys.version_info.major}.{sys.version_info.minor}). "
        f"Python 3.13+ recommended for best performance."
    )

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.config import FontManager, APP_NAME, APP_VERSION
from utils.logger import Logger, header, separator
from utils.dialog_styles import DialogStyleManager
from core.resource_loader import ResourceLoader


def main() -> None:
    """Main application entry point."""
    # Initialize logger
    logger = Logger("Application")
    
    # Display startup header
    header(f"{APP_NAME} v{APP_VERSION}")
    logger.info("Starting application...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Use Fusion style for consistent cross-platform rendering
    # Prevents Windows native tooltip frames from overriding Qt CSS styling
    app.setStyle("Fusion")
    
    # Load and set custom font globally
    logger.info("Loading custom font...")
    custom_font = FontManager.load_embedded_font()
    app.setFont(custom_font)
    logger.success("Font applied to application")
    
    # Pre-warm stylesheet cache for faster dialog opening
    font_family = custom_font.family() if custom_font else "Arial"
    DialogStyleManager.prewarm_cache(font_family)
    logger.info("Stylesheet cache pre-warmed")
    
    # Pre-load button images for image mode (eliminates first-click delay)
    preloaded = ResourceLoader.preload_button_images(['transform', 'copy', 'load', 'save'])
    if preloaded > 0:
        logger.info(f"Button images preloaded", details=f"{preloaded} images")
    
    # Create and show main window
    logger.info("Creating main window...")
    window = MainWindow()
    window.show()
    
    separator()
    logger.success("Application ready!")
    separator()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()