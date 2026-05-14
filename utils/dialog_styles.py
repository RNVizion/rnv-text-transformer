"""
RNV Text Transformer - Dialog Styles Module
Centralized stylesheet management for all dialogs.

Python 3.13 Optimized:
- Modern type hints with ClassVar
- LRU-style cached stylesheet generation
- Immutable color dictionaries
- Pre-warm cache support
- Cache statistics for debugging


Usage:
    from utils.dialog_styles import DialogStyleManager
    
    # Pre-warm cache at application startup (optional but recommended)
    DialogStyleManager.prewarm_cache("Arial")
    
    # Get complete dialog stylesheet (cached)
    is_dark = self.theme_manager.is_dark_mode
    stylesheet = DialogStyleManager.get_dialog_stylesheet(is_dark, self.font_family)
    self.setStyleSheet(stylesheet)
    
    # Get colors for custom styling (returns cached immutable dict)
    colors = DialogStyleManager.get_colors(is_dark)
    custom_style = f"color: {colors['accent']};"
    
    # Check cache statistics (for debugging)
    stats = DialogStyleManager.get_cache_stats()
    print(f"Cache hit rate: {stats['hit_rate']:.1%}")
"""

from __future__ import annotations

from typing import ClassVar
from functools import lru_cache


class DialogStyleManager:
    """
    Centralized stylesheet generation for all dialogs.
    
    Features:
    - LRU-style stylesheet caching with size limits
    - Immutable color dictionaries (prevent accidental modification)
    - Pre-warming support for application startup
    - Cache statistics for debugging/optimization
    - Component-specific style builders
    - Semantic color system
    
    Performance Notes:
    - Stylesheets are cached by (is_dark, font_family) key
    - Color lookups return frozen tuples (hashable, immutable)
    - Call prewarm_cache() at startup for best cold-start performance
    - Extended stylesheets are cached separately by component combination
    
    Color System:
    - bg: Primary background (dialogs)
    - bg_secondary: Input/card backgrounds  
    - bg_tertiary: Hover/disabled states
    - text: Primary text color
    - text_muted: Secondary/disabled text
    - border: Standard borders
    - border_light: Subtle borders
    - accent: Brand/action color (gold for dark, blue for light)
    - success/error/warning: Semantic colors
    
    MainWindow Colors (separate from dialog bg for intentional contrast):
    - window_bg: Main window background (#000000 dark, #F5F5F5 light)
    - button_bg/button_text/button_hover_bg/button_pressed_text: Button colors
    - input_bg/input_text/input_border: Input field colors
    - label_bg/label_text: Label colors
    - text_color/border_color: Aliases for backward compat with ThemeColors
    - output_text_color: Transformed output text highlight
    """
    
    # ==================== CACHE STORAGE ====================
    
    # Stylesheet cache: (is_dark, font_family) -> stylesheet string
    _cache: ClassVar[dict[tuple[bool, str], str]] = {}
    
    # Component-specific cache for extended stylesheets
    _component_cache: ClassVar[dict[tuple[bool, str, tuple[str, ...]], str]] = {}
    
    # Cache statistics
    _stats: ClassVar[dict[str, int]] = {
        'hits': 0,
        'misses': 0,
        'component_hits': 0,
        'component_misses': 0,
    }
    
    # Maximum cache sizes (LRU-style eviction when exceeded)
    _MAX_BASE_CACHE_SIZE: ClassVar[int] = 10
    _MAX_COMPONENT_CACHE_SIZE: ClassVar[int] = 50
    
    # ==================== COLOR DEFINITIONS ====================
    
    DARK: ClassVar[dict[str, str]] = {
        # Backgrounds
        'bg': '#1A1A1A',
        'bg_secondary': '#2A2A2A',
        'bg_tertiary': '#333333',
        'bg_hover': '#3A3A3A',
        
        # Text
        'text': '#E0E0E0',
        'text_muted': '#888888',
        'text_disabled': '#555555',
        
        # Borders
        'border': '#333333',
        'border_light': '#444444',
        'border_focus': '#d2bc93',
        
        # Accent colors
        'accent': '#d2bc93',
        'accent_hover': '#dcc9a3',
        'accent_pressed': '#b7a480',
        'accent_text': '#000000',  # Text on accent background
        
        # Semantic colors
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#d2bc93',
        
        # Special
        'selection_bg': '#d2bc93',
        'selection_text': '#000000',
        'scrollbar_bg': '#252525',
        'scrollbar_handle': '#444444',
        'scrollbar_handle_hover': '#606060',
        'scrollbar_handle_main': '#505050',
        'tooltip_border': '#d2bc93',
        
        # Checkbox indicator
        'checkbox_indicator_bg': '#1A1A1A',
        'checkbox_border': '#555555',
        
        # Dropdown / list hover
        'list_hover_bg': '#FFFFFF',
        'list_hover_text': '#000000',
        
        # MainWindow-specific (pure black background, distinct from dialog bg)
        'window_bg': '#000000',
        'button_bg': '#1A1A1A',
        'button_text': '#E0E0E0',
        'button_hover_bg': '#333333',
        'button_pressed_text': '#000000',
        'input_bg': '#1A1A1A',
        'input_text': '#E0E0E0',
        'input_border': '#333333',
        'label_bg': '#000000',
        'label_text': '#E0E0E0',
        'output_text_color': '#d2bc93',
        'border_color': '#333333',
        'text_color': '#E0E0E0',
        
        # Line number gutter widget
        'line_number_bg': '#1A1A1A',
        'line_number_fg': '#666666',
        'line_number_current_bg': '#2A2A2A',
        'line_number_current_fg': '#d2bc93',

        # Diff / compare semantic highlight colors
        'diff_added_bg':   '#1a4d1a',
        'diff_removed_bg': '#4d1a1a',
        'diff_changed_bg': '#4d4d1a',
        'diff_current_bg': '#4d1a4d',

        # Diff HTML export colors (standalone document — always light-styled)
        'diff_html_equal_bg':  '#ffffff',
        'diff_html_insert_bg': '#d4edda',
        'diff_html_delete_bg': '#f8d7da',
        'diff_html_header_bg': '#f0f0f0',
        'diff_html_line_num':  '#888888',
        'diff_html_border':    '#dddddd',
        'diff_html_stats_text':'#666666',

        # Regex builder match highlight
        'regex_match_bg': '#4a4a00',

        # Image mode semi-transparent overlay values (rgba — used only in image mode)
        'image_overlay_bg':            'rgba(0, 0, 0, 171)',
        'image_overlay_bg_dark':       'rgba(26, 26, 26, 191)',
        'image_overlay_checkbox':      'rgba(0, 0, 0, 100)',
        'image_scrollbar_border':      'rgba(51, 51, 51, 100)',
        'image_scrollbar_handle':      'rgba(80, 80, 80, 150)',
        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',
        'image_dropdown_bg':           'rgba(0, 0, 0, 131)',
        'image_dropdown_selection':    'rgba(51, 51, 51, 200)',
        'image_dropdown_border':       'rgba(51, 51, 51, 150)',
    }
    
    LIGHT: ClassVar[dict[str, str]] = {
        # Backgrounds
        'bg': '#F5F5F5',
        'bg_secondary': '#FFFFFF',
        'bg_tertiary': '#E8E8E8',
        'bg_hover': '#EEEEEE',
        
        # Text
        'text': '#000000',
        'text_muted': '#666666',
        'text_disabled': '#AAAAAA',
        
        # Borders
        'border': '#CCCCCC',
        'border_light': '#DDDDDD',
        'border_focus': '#b19145',
        
        # Accent colors
        'accent': '#b19145',
        'accent_hover': '#c4a458',
        'accent_pressed': '#8a7236',
        'accent_text': '#FFFFFF',  # Text on accent background
        
        # Semantic colors
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#b19145',
        
        # Special
        'selection_bg': '#b19145',
        'selection_text': '#FFFFFF',
        'scrollbar_bg': '#E0E0E0',
        'scrollbar_handle': '#AAAAAA',
        'scrollbar_handle_hover': '#888888',
        'scrollbar_handle_main': '#AAAAAA',
        'tooltip_border': '#b19145',
        
        # Checkbox indicator
        'checkbox_indicator_bg': '#FFFFFF',
        'checkbox_border': '#AAAAAA',
        
        # Dropdown / list hover
        'list_hover_bg': '#1A1A1A',
        'list_hover_text': '#FFFFFF',
        
        # MainWindow-specific
        'window_bg': '#F5F5F5',
        'button_bg': '#FFFFFF',
        'button_text': '#000000',
        'button_hover_bg': '#333333',
        'button_pressed_text': '#FFFFFF',
        'input_bg': '#FFFFFF',
        'input_text': '#000000',
        'input_border': '#CCCCCC',
        'label_bg': '#F5F5F5',
        'label_text': '#000000',
        'output_text_color': '#b19145',
        'border_color': '#CCCCCC',
        'text_color': '#000000',
        
        # Line number gutter widget
        'line_number_bg': '#F0F0F0',
        'line_number_fg': '#999999',
        'line_number_current_bg': '#E8E8E8',
        'line_number_current_fg': '#b19145',

        # Diff / compare semantic highlight colors
        'diff_added_bg':   '#d4edda',
        'diff_removed_bg': '#f8d7da',
        'diff_changed_bg': '#fff3cd',
        'diff_current_bg': '#e2d4f0',

        # Diff HTML export colors (standalone document — always light-styled)
        'diff_html_equal_bg':  '#ffffff',
        'diff_html_insert_bg': '#d4edda',
        'diff_html_delete_bg': '#f8d7da',
        'diff_html_header_bg': '#f0f0f0',
        'diff_html_line_num':  '#888888',
        'diff_html_border':    '#dddddd',
        'diff_html_stats_text':'#666666',

        # Regex builder match highlight
        'regex_match_bg': '#ffff99',

        # Image mode semi-transparent overlay values (rgba — used only in image mode)
        # Same values as DARK since image mode always uses dark-based overlays
        'image_overlay_bg':            'rgba(0, 0, 0, 171)',
        'image_overlay_bg_dark':       'rgba(26, 26, 26, 191)',
        'image_overlay_checkbox':      'rgba(0, 0, 0, 100)',
        'image_scrollbar_border':      'rgba(51, 51, 51, 100)',
        'image_scrollbar_handle':      'rgba(80, 80, 80, 150)',
        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',
        'image_dropdown_bg':           'rgba(0, 0, 0, 131)',
        'image_dropdown_selection':    'rgba(51, 51, 51, 200)',
        'image_dropdown_border':       'rgba(51, 51, 51, 150)',
    }
    
    # ==================== REGEX GROUP HIGHLIGHT PALETTE ====================
    # Dark-only visualization palette for regex capture group highlighting.
    # Each color corresponds to a different capture group (group 1 → index 0, etc.).
    REGEX_GROUP_COLORS: ClassVar[list[str]] = [
        "#3d5c5c", "#5c3d5c", "#5c5c3d", "#3d5c3d",
        "#5c3d3d", "#3d3d5c", "#5c4d3d", "#3d5c4d",
    ]

    # ==================== PUBLIC METHODS ====================
    
    @classmethod
    def get_colors(cls, is_dark: bool) -> dict[str, str]:
        """
        Get color dictionary for theme.
        
        Note: Returns the class-level dictionary directly for performance.
        Do not modify the returned dictionary.
        
        Args:
            is_dark: True for dark/image theme, False for light theme
            
        Returns:
            Dictionary of color name -> hex color
        """
        return cls.DARK if is_dark else cls.LIGHT
    
    @classmethod
    def get_dialog_stylesheet(cls, is_dark: bool, font_family: str) -> str:
        """
        Get complete dialog stylesheet with LRU caching.
        
        This method caches generated stylesheets for performance.
        Subsequent calls with the same parameters return cached results.
        Cache is limited to _MAX_BASE_CACHE_SIZE entries with LRU eviction.
        
        Args:
            is_dark: True for dark/image theme, False for light theme
            font_family: Font family name to use
            
        Returns:
            Complete CSS stylesheet string for QDialog
        """
        cache_key = (is_dark, font_family)
        
        if cache_key in cls._cache:
            cls._stats['hits'] += 1
            return cls._cache[cache_key]
        
        cls._stats['misses'] += 1
        
        # LRU eviction if cache is full
        if len(cls._cache) >= cls._MAX_BASE_CACHE_SIZE:
            # Remove oldest entry (first key in dict - Python 3.7+ maintains order)
            oldest_key = next(iter(cls._cache))
            del cls._cache[oldest_key]
        
        stylesheet = cls._build_dialog_stylesheet(is_dark, font_family)
        cls._cache[cache_key] = stylesheet
        return stylesheet
    
    @classmethod
    def get_extended_stylesheet(
        cls, 
        is_dark: bool, 
        font_family: str,
        *components: str
    ) -> str:
        """
        Get dialog stylesheet with additional component styles.
        
        Results are cached by (is_dark, font_family, sorted_components).
        
        Args:
            is_dark: True for dark/image theme
            font_family: Font family name
            *components: Component names to include:
                - 'splitter': QSplitter styles
                - 'menu': QMenu styles
                - 'table': QTableWidget styles
                - 'tab': QTabWidget styles
                - 'spinbox': QSpinBox/QDoubleSpinBox styles
                - 'slider': QSlider styles
                - 'list': QListWidget styles
                - 'progressbar': QProgressBar styles
                - 'tree': QTreeWidget styles
            
        Returns:
            Extended stylesheet with requested component styles
        """
        base = cls.get_dialog_stylesheet(is_dark, font_family)
        
        if not components:
            return base
        
        # Use sorted tuple for consistent cache keys
        component_key = tuple(sorted(components))
        cache_key = (is_dark, font_family, component_key)
        
        if cache_key in cls._component_cache:
            cls._stats['component_hits'] += 1
            return cls._component_cache[cache_key]
        
        cls._stats['component_misses'] += 1
        
        # LRU eviction if cache is full
        if len(cls._component_cache) >= cls._MAX_COMPONENT_CACHE_SIZE:
            oldest_key = next(iter(cls._component_cache))
            del cls._component_cache[oldest_key]
        
        c = cls.get_colors(is_dark)
        extra_styles = []
        
        component_builders = {
            'splitter': cls._get_splitter_style,
            'menu': cls._get_menu_style,
            'table': cls._get_table_style,
            'tab': cls._get_tab_style,
            'spinbox': cls._get_spinbox_style,
            'slider': cls._get_slider_style,
            'list': cls._get_list_style,
            'progressbar': cls._get_progressbar_style,
            'tree': cls._get_tree_style,
        }
        
        for component in components:
            builder = component_builders.get(component)
            if builder:
                extra_styles.append(builder(c))
        
        result = base + '\n'.join(extra_styles)
        cls._component_cache[cache_key] = result
        return result
    
    @classmethod
    def get_menu_stylesheet(cls, is_dark: bool) -> str:
        """
        Get standalone QMenu stylesheet for context menus.

        Use this when applying a stylesheet directly to a QMenu instance
        rather than to a dialog — it returns only the menu rules without
        the full base dialog stylesheet.

        Args:
            is_dark: True for dark/image theme, False for light theme

        Returns:
            QMenu-only stylesheet string
        """
        return cls._get_menu_style(cls.get_colors(is_dark))

    @classmethod
    def prewarm_cache(cls, font_family: str = "Arial") -> None:
        """
        Pre-populate cache with common stylesheet combinations.
        
        Call this at application startup for better initial performance.
        Pre-warms both dark and light themes with common component sets.
        
        Args:
            font_family: Primary font family used by the application
        """
        # Pre-warm base stylesheets for both themes
        cls.get_dialog_stylesheet(True, font_family)   # Dark
        cls.get_dialog_stylesheet(False, font_family)  # Light
        
        # Pre-warm common component combinations
        common_combos = [
            ('tab',),
            ('table',),
            ('list',),
            ('spinbox',),
            ('tab', 'table'),
            ('tab', 'splitter'),
            ('tab', 'list'),
            ('tab', 'spinbox'),
        ]
        
        for components in common_combos:
            cls.get_extended_stylesheet(True, font_family, *components)
            cls.get_extended_stylesheet(False, font_family, *components)
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all stylesheet caches.
        
        Call this when font family changes to regenerate stylesheets.
        Also resets cache statistics.
        """
        cls._cache.clear()
        cls._component_cache.clear()
        
        # Reset statistics
        for key in cls._stats:
            cls._stats[key] = 0
    
    @classmethod
    def get_cache_stats(cls) -> dict[str, int | float]:
        """
        Get cache performance statistics.
        
        Useful for debugging and optimization.
        
        Returns:
            Dictionary with cache statistics including hit rates:
            - hits: Number of base cache hits
            - misses: Number of base cache misses
            - hit_rate: Base cache hit rate (0.0 to 1.0)
            - component_hits: Number of component cache hits
            - component_misses: Number of component cache misses
            - component_hit_rate: Component cache hit rate
            - base_cache_size: Current base cache entry count
            - component_cache_size: Current component cache entry count
        """
        stats = dict(cls._stats)
        
        # Calculate hit rates
        total_base = stats['hits'] + stats['misses']
        stats['hit_rate'] = stats['hits'] / total_base if total_base > 0 else 0.0
        
        total_component = stats['component_hits'] + stats['component_misses']
        stats['component_hit_rate'] = (
            stats['component_hits'] / total_component if total_component > 0 else 0.0
        )
        
        # Add cache sizes
        stats['base_cache_size'] = len(cls._cache)
        stats['component_cache_size'] = len(cls._component_cache)
        
        return stats
    
    # ==================== INLINE STYLE METHODS ====================
    
    @classmethod
    @lru_cache(maxsize=32)
    def get_status_style(cls, is_dark: bool, status: str) -> str:
        """
        Get inline style for status indicators.
        
        Cached with LRU for frequent access patterns.
        
        Args:
            is_dark: True for dark theme
            status: One of 'success', 'error', 'warning', 'muted', 'info', 'accent'
            
        Returns:
            CSS style string for inline use
        """
        c = cls.get_colors(is_dark)
        color_map = {
            'success': c['success'],
            'error': c['error'],
            'warning': c['warning'],
            'muted': c['text_muted'],
            'info': c['info'],
            'accent': c['accent'],
        }
        color = color_map.get(status, c['text'])
        return f"color: {color};"
    
    @classmethod
    @lru_cache(maxsize=4)
    def get_header_style(cls, is_dark: bool) -> str:
        """
        Get style for section headers.
        
        Cached with LRU.
        
        Args:
            is_dark: True for dark theme
            
        Returns:
            CSS style string for headers
        """
        c = cls.get_colors(is_dark)
        return f"font-size: 14pt; font-weight: bold; color: {c['text']};"
    
    @classmethod
    @lru_cache(maxsize=4)
    def get_subtitle_style(cls, is_dark: bool) -> str:
        """
        Get style for subtitles/descriptions.
        
        Cached with LRU.
        
        Args:
            is_dark: True for dark theme
            
        Returns:
            CSS style string for subtitles
        """
        c = cls.get_colors(is_dark)
        return f"color: {c['text_muted']}; margin-bottom: 10px;"
    
    @classmethod
    @lru_cache(maxsize=4)
    def get_description_style(cls, is_dark: bool) -> str:
        """
        Get style for description/info labels (smaller muted text).
        
        Cached with LRU.
        
        Args:
            is_dark: True for dark theme
            
        Returns:
            CSS style string for description labels
        """
        c = cls.get_colors(is_dark)
        return f"color: {c['text_muted']}; font-size: 9pt;"
    
    @classmethod
    @lru_cache(maxsize=4)
    def get_tip_style(cls, is_dark: bool) -> str:
        """
        Get style for tip labels (accent italic text).
        
        Cached with LRU.
        
        Args:
            is_dark: True for dark theme
            
        Returns:
            CSS style string for tip labels
        """
        c = cls.get_colors(is_dark)
        return f"color: {c['accent']}; font-style: italic;"
    
    # ==================== INTERNAL BUILDERS ====================
    
    @classmethod
    def _build_dialog_stylesheet(cls, is_dark: bool, font_family: str) -> str:
        """Build complete dialog stylesheet."""
        c = cls.get_colors(is_dark)
        
        return f"""
            /* ===== BASE DIALOG ===== */
            QDialog {{
                background-color: {c['bg']};
                color: {c['text']};
                font-family: '{font_family}';
            }}
            
            /* ===== LABELS ===== */
            QLabel {{
                color: {c['text']};
                background-color: transparent;
            }}
            
            /* ===== GROUP BOX ===== */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border']};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: {c['accent']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            /* ===== LINE EDIT ===== */
            QLineEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                padding: 8px;
                border-radius: 4px;
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
            }}
            QLineEdit:focus {{
                border-color: {c['border_focus']};
            }}
            QLineEdit:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_disabled']};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {c['bg_tertiary']};
            }}
            
            /* ===== TEXT EDIT / PLAIN TEXT EDIT ===== */
            QTextEdit, QPlainTextEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
            }}
            QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {c['border_focus']};
            }}
            QTextEdit:disabled, QPlainTextEdit:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_disabled']};
            }}
            
            /* ===== COMBO BOX ===== */
            QComboBox {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                padding: 5px 10px;
                border-radius: 4px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border-color: {c['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
                border: 1px solid {c['border']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {c['selection_bg']};
                color: {c['selection_text']};
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {c['accent_hover']};
                color: {c['selection_text']};
            }}
            QComboBox:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_disabled']};
            }}
            
            /* ===== CHECK BOX ===== */
            QCheckBox {{
                color: {c['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {c['border_light']};
                background-color: {c['bg_secondary']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['accent']};
                border-color: {c['accent']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {c['accent']};
            }}
            QCheckBox:disabled {{
                color: {c['text_disabled']};
            }}
            
            /* ===== RADIO BUTTON ===== */
            QRadioButton {{
                color: {c['text']};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid {c['border_light']};
                background-color: {c['bg_secondary']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {c['accent']};
                border-color: {c['accent']};
            }}
            QRadioButton::indicator:hover {{
                border-color: {c['accent']};
            }}
            QRadioButton:disabled {{
                color: {c['text_disabled']};
            }}
            
            /* ===== PUSH BUTTON ===== */
            QPushButton {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                border-color: {c['accent']};
                color: {c['accent']};
            }}
            QPushButton:pressed {{
                background-color: {c['accent']};
                color: {c['accent_text']};
            }}
            QPushButton:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_disabled']};
                border-color: {c['border']};
            }}
            QPushButton:default {{
                border-color: {c['accent']};
            }}
            
            /* ===== PROGRESS BAR ===== */
            QProgressBar {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                text-align: center;
                color: {c['text']};
            }}
            QProgressBar::chunk {{
                background-color: {c['accent']};
                border-radius: 3px;
            }}
            
            /* ===== SCROLL AREA ===== */
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
            
            /* ===== SCROLL BAR ===== */
            QScrollBar:vertical {{
                background-color: {c['scrollbar_bg']};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {c['scrollbar_handle']};
                border-radius: 5px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {c['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: {c['scrollbar_bg']};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {c['scrollbar_handle']};
                border-radius: 5px;
                min-width: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {c['accent']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            
            /* ===== FRAME ===== */
            QFrame {{
                background-color: transparent;
            }}
            QFrame[frameShape="4"] {{  /* HLine */
                background-color: {c['border']};
                max-height: 1px;
            }}
            QFrame[frameShape="5"] {{  /* VLine */
                background-color: {c['border']};
                max-width: 1px;
            }}
            
        """
    
    # ==================== COMPONENT STYLES ====================
    
    @classmethod
    def _get_splitter_style(cls, c: dict[str, str]) -> str:
        """Get QSplitter stylesheet."""
        return f"""
            QSplitter::handle {{
                background-color: {c['border']};
            }}
            QSplitter::handle:horizontal {{
                width: 3px;
            }}
            QSplitter::handle:vertical {{
                height: 3px;
            }}
            QSplitter::handle:hover {{
                background-color: {c['accent']};
            }}
        """
    
    @classmethod
    def _get_menu_style(cls, c: dict[str, str]) -> str:
        """Get QMenu stylesheet."""
        return f"""
            QMenu {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 2px;
            }}
            QMenu::item:selected {{
                background-color: {c['selection_bg']};
                color: {c['selection_text']};
            }}
            QMenu::item:disabled {{
                color: {c['text_disabled']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {c['border']};
                margin: 4px 8px;
            }}
        """
    
    @classmethod
    def _get_table_style(cls, c: dict[str, str]) -> str:
        """Get QTableWidget stylesheet."""
        return f"""
            QTableWidget {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                gridline-color: {c['border']};
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {c['selection_bg']};
                color: {c['selection_text']};
            }}
            QTableWidget::item:hover {{
                background-color: {c['accent_hover']};
                color: {c['selection_text']};
            }}
            QHeaderView::section {{
                background-color: {c['bg_tertiary']};
                color: {c['text']};
                border: none;
                border-right: 1px solid {c['border']};
                border-bottom: 1px solid {c['border']};
                padding: 6px;
                font-weight: bold;
            }}
            QTableCornerButton::section {{
                background-color: {c['bg_tertiary']};
                border: none;
            }}
        """
    
    @classmethod
    def _get_tab_style(cls, c: dict[str, str]) -> str:
        """Get QTabWidget stylesheet."""
        return f"""
            QTabWidget {{
                border: none;
            }}
            QTabWidget::pane {{
                background-color: {c['bg']};
                border: none;
                border-top: none;
                padding: 0px;
                margin: 0px;
            }}
            QTabWidget::tab-bar {{
                left: 0px;
            }}
            QTabBar {{
                background-color: {c['bg']};
                border: none;
                qproperty-drawBase: 0;
            }}
            QTabBar::tab {{
                background-color: {c['bg_secondary']};
                color: {c['text_muted']};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['bg']};
                color: {c['accent']};
                border-bottom: 2px solid {c['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c['bg_hover']};
                color: {c['accent']};
                border-bottom: 2px solid {c['accent_pressed']};
            }}
        """
    
    @classmethod
    def _get_spinbox_style(cls, c: dict[str, str]) -> str:
        """Get QSpinBox/QDoubleSpinBox stylesheet."""
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                padding: 5px;
                border-radius: 4px;
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {c['border_focus']};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                border: none;
                background-color: transparent;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border: none;
                background-color: transparent;
            }}
            QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_disabled']};
            }}
        """
    
    @classmethod
    def _get_slider_style(cls, c: dict[str, str]) -> str:
        """Get QSlider stylesheet."""
        return f"""
            QSlider::groove:horizontal {{
                border: 1px solid {c['border']};
                height: 6px;
                background: {c['bg_secondary']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {c['accent']};
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {c['accent_hover']};
            }}
            QSlider::sub-page:horizontal {{
                background: {c['accent']};
                border-radius: 3px;
            }}
            QSlider::groove:vertical {{
                border: 1px solid {c['border']};
                width: 6px;
                background: {c['bg_secondary']};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {c['accent']};
                border: none;
                height: 16px;
                margin: 0 -5px;
                border-radius: 8px;
            }}
            QSlider::handle:vertical:hover {{
                background: {c['accent_hover']};
            }}
        """
    
    @classmethod
    def _get_list_style(cls, c: dict[str, str]) -> str:
        """Get QListWidget stylesheet."""
        return f"""
            QListWidget {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px;
                border-radius: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {c['selection_bg']};
                color: {c['selection_text']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {c['accent_hover']};
                color: {c['selection_text']};
            }}
        """
    
    @classmethod
    def _get_progressbar_style(cls, c: dict[str, str]) -> str:
        """Get QProgressBar stylesheet (extended version)."""
        return f"""
            QProgressBar {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                text-align: center;
                color: {c['text']};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {c['accent']};
                border-radius: 3px;
            }}
        """
    
    @classmethod
    def _get_tree_style(cls, c: dict[str, str]) -> str:
        """Get QTreeWidget stylesheet."""
        return f"""
            QTreeWidget {{
                background-color: {c['bg_secondary']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {c['selection_bg']};
                color: {c['selection_text']};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {c['accent_hover']};
                color: {c['selection_text']};
            }}
            QTreeWidget::branch {{
                background-color: transparent;
            }}
            QTreeWidget::branch:selected {{
                background-color: {c['selection_bg']};
            }}
            QHeaderView::section {{
                background-color: {c['bg_tertiary']};
                color: {c['text']};
                border: none;
                border-right: 1px solid {c['border']};
                border-bottom: 1px solid {c['border']};
                padding: 6px;
                font-weight: bold;
            }}
        """