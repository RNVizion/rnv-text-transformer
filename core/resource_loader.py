"""
RNV Text Transformer - Resource Loader Module
Handles loading of image resources with caching for performance

Python 3.13 Optimized:
- ClassVar for proper class-level type hints
- @classmethod for cache management
- Pathlib integration
- Modern type hints
- Professional logging via Logger utility
"""

from __future__ import annotations

from typing import ClassVar

from PyQt6.QtGui import QPixmap, QIcon

from utils.config import BUTTON_IMAGES_DIR, ICONS_DIR
from utils.logger import get_module_logger

_logger = get_module_logger("ResourceLoader")


class ResourceLoader:
    """
    Handles loading of image resources with caching.
    
    Uses class-level cache for performance optimization across all instances.
    Cache is bounded to prevent unbounded memory growth.
    """
    
    # Class-level cache shared across all instances
    _pixmap_cache: ClassVar[dict[str, QPixmap]] = {}
    _MAX_CACHE_SIZE: ClassVar[int] = 50  # Max cached pixmaps (LRU eviction)
    
    __slots__ = ()  # No instance attributes needed
    
    @classmethod
    def load_button_image(cls, button_name: str, state: str = 'base') -> QPixmap | None:
        """
        Load button image for given state (base, hover, pressed) with caching.
        
        Args:
            button_name: Name of the button (e.g., 'transform', 'copy')
            state: Image state - 'base', 'hover', or 'pressed'
        
        Returns:
            Loaded pixmap or None if not found
        """
        cache_key = f"{button_name}_{state}"
        
        # Return cached pixmap if available (move to end for LRU)
        if cache_key in cls._pixmap_cache:
            # Move to end (most recently used)
            pixmap = cls._pixmap_cache.pop(cache_key)
            cls._pixmap_cache[cache_key] = pixmap
            return pixmap
        
        img_path = BUTTON_IMAGES_DIR / f"{button_name}_{state}.png"
        logger = _logger
        
        if img_path.exists():
            try:
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    # Evict oldest entry if cache is full
                    if len(cls._pixmap_cache) >= cls._MAX_CACHE_SIZE:
                        oldest_key = next(iter(cls._pixmap_cache))
                        del cls._pixmap_cache[oldest_key]
                    # Cache the loaded pixmap
                    cls._pixmap_cache[cache_key] = pixmap
                    if logger:
                        logger.success(f"Loaded button image: {button_name}_{state}.png")
                    return pixmap
            except Exception as e:
                if logger:
                    logger.error(f"Error loading button image {button_name}_{state}", error=e)
        
        return None
    
    @classmethod
    def load_app_icon(cls) -> QIcon | None:
        """
        Load application icon.
        
        Returns:
            Application icon or None if not found
        """
        icon_path = ICONS_DIR / "icon.png"
        logger = _logger
        
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if logger:
                    logger.success("Loaded application icon")
                return icon
            except Exception as e:
                if logger:
                    logger.error("Error loading application icon", error=e)
        
        return None
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the pixmap cache."""
        cls._pixmap_cache.clear()
        logger = _logger
        if logger:
            logger.info("Cleared resource cache")
    
    @classmethod
    def get_cache_size(cls) -> int:
        """
        Get number of cached items.
        
        Returns:
            Number of cached pixmaps
        """
        return len(cls._pixmap_cache)
    
    @classmethod
    def is_cached(cls, button_name: str, state: str = 'base') -> bool:
        """
        Check if a button image is cached.
        
        Args:
            button_name: Name of the button
            state: Image state
            
        Returns:
            True if cached
        """
        cache_key = f"{button_name}_{state}"
        return cache_key in cls._pixmap_cache
    
    @classmethod
    def preload_button_images(cls, button_names: list[str]) -> int:
        """
        Preload all states for given button names.
        
        Args:
            button_names: List of button names to preload
            
        Returns:
            Number of images successfully loaded
        """
        states = ('base', 'hover', 'pressed')
        loaded = 0
        
        for name in button_names:
            for state in states:
                if cls.load_button_image(name, state) is not None:
                    loaded += 1
        
        return loaded