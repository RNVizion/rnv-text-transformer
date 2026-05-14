"""
RNV Text Transformer - Core Package
Core business logic modules.
"""

from core.theme_manager import ThemeManager

from core.resource_loader import ResourceLoader

from core.text_transformer import TextTransformer, TransformMode

from core.text_statistics import TextStatistics, TextStats

from core.text_cleaner import TextCleaner, CleanupOperation, SplitJoinOperation

from core.batch_processor import BatchProcessor, BatchResult, BatchProgress

from core.diff_engine import DiffEngine, DiffResult, DiffChange, ChangeType

from core.export_manager import ExportManager, ExportFormat, ExportOptions, ExportError

from core.preset_manager import (
    PresetManager,
    PresetExecutor,
    TransformPreset,
    PresetStep,
    ActionType,
)

from core.regex_patterns import RegexPatterns, RegexHelper, PatternInfo

from core.folder_watcher import FolderWatcher, WatchRule, WatchRuleManager, WatchEvent


__all__ = [
    # Theme
    'ThemeManager',
    # Resources
    'ResourceLoader',
    # Text Processing
    'TextTransformer',
    'TransformMode',
    'TextStatistics',
    'TextStats',
    'TextCleaner',
    'CleanupOperation',
    'SplitJoinOperation',
    # Batch Processing
    'BatchProcessor',
    'BatchResult',
    'BatchProgress',
    # Diff
    'DiffEngine',
    'DiffResult',
    'DiffChange',
    'ChangeType',
    # Export
    'ExportManager',
    'ExportFormat',
    'ExportOptions',
    'ExportError',
    # Presets
    'PresetManager',
    'PresetExecutor',
    'TransformPreset',
    'PresetStep',
    'ActionType',
    # Regex
    'RegexPatterns',
    'RegexHelper',
    'PatternInfo',
    # Folder Watcher
    'FolderWatcher',
    'WatchRule',
    'WatchRuleManager',
    'WatchEvent',
]
