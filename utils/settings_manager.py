"""
RNV Text Transformer - Settings Manager Module
Handles persistent application settings using QSettings

Python 3.13 Optimized:
- Modern type hints
- ClassVar for default values
- Clean API for settings access
- Automatic type conversion
"""

from __future__ import annotations

from typing import ClassVar

from PyQt6.QtCore import QSettings, QByteArray

from utils.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_X,
    DEFAULT_WINDOW_Y,
)


class SettingsManager:
    """
    Manages persistent application settings using QSettings.
    
    Settings are stored in the user's application data directory:
    - Windows: Registry or %APPDATA%
    - macOS: ~/Library/Preferences/
    - Linux: ~/.config/
    
    Uses organization name 'RNV' and application name from config.
    """
    
    # Organization name for settings storage
    _ORGANIZATION: ClassVar[str] = "RNV"
    
    # Settings keys
    class Keys:
        """Settings key constants to prevent typos."""
        # Window settings
        WINDOW_GEOMETRY = "window/geometry"
        WINDOW_MAXIMIZED = "window/maximized"
        WINDOW_X = "window/x"
        WINDOW_Y = "window/y"
        WINDOW_WIDTH = "window/width"
        WINDOW_HEIGHT = "window/height"
        
        # Theme settings
        THEME_CURRENT = "theme/current"
        
        # Transform settings
        TRANSFORM_LAST_MODE = "transform/last_mode"
        
        # Feature settings
        AUTO_TRANSFORM = "features/auto_transform"
        SHOW_TOOLTIPS = "features/show_tooltips"
        STATS_POSITION = "features/stats_position"
        
        # Recent files
        RECENT_FILES = "recent/files"
        RECENT_FILES_MAX = "recent/max_count"
    
    __slots__ = ('_settings',)
    
    def __init__(self) -> None:
        """Initialize settings manager with QSettings backend."""
        self._settings = QSettings(self._ORGANIZATION, APP_NAME)
    
    # ==================== WINDOW SETTINGS ====================
    
    def save_window_geometry(self, geometry: QByteArray) -> None:
        """
        Save window geometry (position, size, state).
        
        Args:
            geometry: QByteArray from window.saveGeometry()
        """
        self._settings.setValue(self.Keys.WINDOW_GEOMETRY, geometry)
    
    def load_window_geometry(self) -> QByteArray | None:
        """
        Load saved window geometry.
        
        Returns:
            QByteArray for window.restoreGeometry() or None if not saved
        """
        value = self._settings.value(self.Keys.WINDOW_GEOMETRY)
        if isinstance(value, QByteArray):
            return value
        return None
    
    def save_window_maximized(self, maximized: bool) -> None:
        """
        Save window maximized state.
        
        Args:
            maximized: Whether window is maximized
        """
        self._settings.setValue(self.Keys.WINDOW_MAXIMIZED, maximized)
    
    def load_window_maximized(self) -> bool:
        """
        Load window maximized state.
        
        Returns:
            True if window was maximized, False otherwise
        """
        return self._settings.value(self.Keys.WINDOW_MAXIMIZED, False, type=bool)
    
    def save_window_position(self, x: int, y: int, width: int, height: int) -> None:
        """
        Save window position and size individually.
        
        Args:
            x: Window X position
            y: Window Y position
            width: Window width
            height: Window height
        """
        self._settings.setValue(self.Keys.WINDOW_X, x)
        self._settings.setValue(self.Keys.WINDOW_Y, y)
        self._settings.setValue(self.Keys.WINDOW_WIDTH, width)
        self._settings.setValue(self.Keys.WINDOW_HEIGHT, height)
    
    def load_window_position(self) -> tuple[int, int, int, int]:
        """
        Load window position and size.
        
        Returns:
            Tuple of (x, y, width, height) with defaults if not saved
        """
        x = self._settings.value(self.Keys.WINDOW_X, DEFAULT_WINDOW_X, type=int)
        y = self._settings.value(self.Keys.WINDOW_Y, DEFAULT_WINDOW_Y, type=int)
        width = self._settings.value(self.Keys.WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH, type=int)
        height = self._settings.value(self.Keys.WINDOW_HEIGHT, DEFAULT_WINDOW_HEIGHT, type=int)
        return (x, y, width, height)
    
    # ==================== THEME SETTINGS ====================
    
    def save_theme(self, theme: str) -> None:
        """
        Save current theme preference.
        
        Args:
            theme: Theme name ('dark', 'light', or 'image')
        """
        self._settings.setValue(self.Keys.THEME_CURRENT, theme)
    
    def load_theme(self) -> str:
        """
        Load saved theme preference.
        
        Returns:
            Theme name, defaults to 'dark' if not saved
        """
        return self._settings.value(self.Keys.THEME_CURRENT, "dark", type=str)
    
    # ==================== TRANSFORM SETTINGS ====================
    
    def save_transform_mode(self, mode: str) -> None:
        """
        Save last used transform mode.
        
        Args:
            mode: Transform mode name (e.g., 'UPPERCASE', 'lowercase')
        """
        self._settings.setValue(self.Keys.TRANSFORM_LAST_MODE, mode)
    
    def load_transform_mode(self) -> str:
        """
        Load last used transform mode.
        
        Returns:
            Transform mode name, defaults to 'UPPERCASE' if not saved
        """
        return self._settings.value(self.Keys.TRANSFORM_LAST_MODE, "UPPERCASE", type=str)
    
    # ==================== FEATURE SETTINGS ====================
    
    def save_auto_transform(self, enabled: bool) -> None:
        """
        Save auto-transform preference.
        
        Args:
            enabled: Whether auto-transform is enabled
        """
        self._settings.setValue(self.Keys.AUTO_TRANSFORM, enabled)
    
    def load_auto_transform(self) -> bool:
        """
        Load auto-transform preference.
        
        Returns:
            True if auto-transform enabled, False by default
        """
        return self._settings.value(self.Keys.AUTO_TRANSFORM, False, type=bool)
    
    def save_show_tooltips(self, enabled: bool) -> None:
        """
        Save show tooltips preference.
        
        Args:
            enabled: Whether tooltips are shown
        """
        self._settings.setValue(self.Keys.SHOW_TOOLTIPS, enabled)
    
    def load_show_tooltips(self) -> bool:
        """
        Load show tooltips preference.
        
        Returns:
            True if tooltips enabled, True by default
        """
        return self._settings.value(self.Keys.SHOW_TOOLTIPS, True, type=bool)
    
    def save_stats_position(self, position: str) -> None:
        """
        Save statistics display position.
        
        Args:
            position: Position string ("Below Output", "Above Output", "Hidden")
        """
        self._settings.setValue(self.Keys.STATS_POSITION, position)
    
    def load_stats_position(self) -> str:
        """
        Load statistics display position.
        
        Returns:
            Position string, "Below Output" by default
        """
        return self._settings.value(self.Keys.STATS_POSITION, "Below Output", type=str)
    
    # ==================== RECENT FILES ====================
    
    def save_recent_files(self, files: list[str]) -> None:
        """
        Save recent files list.
        
        Args:
            files: List of file paths
        """
        self._settings.setValue(self.Keys.RECENT_FILES, files)
    
    def load_recent_files(self) -> list[str]:
        """
        Load recent files list.
        
        Returns:
            List of file paths, empty list if none saved
        """
        value = self._settings.value(self.Keys.RECENT_FILES, [])
        if isinstance(value, list):
            return [str(f) for f in value if f]
        return []
    
    def add_recent_file(self, file_path: str, max_files: int = 10) -> None:
        """
        Add a file to the recent files list.
        
        Args:
            file_path: Path to add
            max_files: Maximum number of recent files to keep
        """
        files = self.load_recent_files()
        
        # Remove if already exists (will be re-added at top)
        if file_path in files:
            files.remove(file_path)
        
        # Add to beginning
        files.insert(0, file_path)
        
        # Trim to max
        files = files[:max_files]
        
        self.save_recent_files(files)
    
    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._settings.setValue(self.Keys.RECENT_FILES, [])
    
    def save_recent_files_max(self, max_count: int) -> None:
        """
        Save maximum recent files count.
        
        Args:
            max_count: Maximum number of recent files to keep (0 = disabled)
        """
        self._settings.setValue(self.Keys.RECENT_FILES_MAX, max_count)
    
    def load_recent_files_max(self) -> int:
        """
        Load maximum recent files count.
        
        Returns:
            Maximum count, 10 by default
        """
        return self._settings.value(self.Keys.RECENT_FILES_MAX, 10, type=int)
    
    # ==================== UTILITY METHODS ====================
    
    def clear_all(self) -> None:
        """Clear all settings (useful for reset to defaults)."""
        self._settings.clear()
    
    def sync(self) -> None:
        """Force write settings to storage."""
        self._settings.sync()
    
    def contains(self, key: str) -> bool:
        """
        Check if a setting exists.
        
        Args:
            key: Settings key to check
            
        Returns:
            True if key exists
        """
        return self._settings.contains(key)
    
    def get_settings_path(self) -> str:
        """
        Get the path where settings are stored.
        
        Returns:
            Settings file/registry path
        """
        return self._settings.fileName()