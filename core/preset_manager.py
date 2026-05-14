"""
RNV Text Transformer - Preset Manager Module
Manages custom transformation presets with multi-step workflows

Python 3.13 Optimized:
- Dataclass-based preset structures
- JSON persistence
- Step execution pipeline

"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Callable
from enum import StrEnum

from utils.logger import get_module_logger
from utils.error_handler import ErrorHandler

_logger = get_module_logger("PresetManager")


class ActionType(StrEnum):
    """Available preset action types."""
    TRANSFORM = "transform"
    CLEANUP = "cleanup"
    REPLACE = "replace"
    REGEX_REPLACE = "regex_replace"
    SPLIT = "split"
    JOIN = "join"
    WRAP = "wrap"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    TRIM_LINES = "trim_lines"


@dataclass
class PresetStep:
    """
    Single step in a transformation preset.
    
    Attributes:
        action: Type of action (transform, cleanup, replace, etc.)
        params: Action-specific parameters
        enabled: Whether this step is active
        description: Optional human-readable description
    """
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'action': self.action,
            'params': self.params,
            'enabled': self.enabled,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresetStep:
        """Create PresetStep from dictionary."""
        return cls(
            action=data.get('action', ''),
            params=data.get('params', {}),
            enabled=data.get('enabled', True),
            description=data.get('description', '')
        )
    
    def get_display_name(self) -> str:
        """Get human-readable description of this step."""
        if self.description:
            return self.description
        
        action = self.action
        params = self.params
        
        match action:
            case ActionType.TRANSFORM:
                mode = params.get('mode', 'Unknown')
                return f"Transform: {mode}"
            case ActionType.CLEANUP:
                op = params.get('operation', 'Unknown')
                return f"Cleanup: {op}"
            case ActionType.REPLACE:
                find = params.get('find', '')[:20]
                return f"Replace: '{find}...'"
            case ActionType.REGEX_REPLACE:
                pattern = params.get('pattern', '')[:20]
                return f"Regex: '{pattern}...'"
            case ActionType.SPLIT:
                delim = params.get('delimiter', '')
                return f"Split by: '{delim}'"
            case ActionType.JOIN:
                delim = params.get('delimiter', '')
                return f"Join with: '{delim}'"
            case ActionType.WRAP:
                width = params.get('width', 80)
                return f"Wrap at {width} chars"
            case ActionType.PREFIX:
                prefix = params.get('text', '')[:15]
                return f"Add prefix: '{prefix}'"
            case ActionType.SUFFIX:
                suffix = params.get('text', '')[:15]
                return f"Add suffix: '{suffix}'"
            case ActionType.TRIM_LINES:
                return "Trim each line"
            case _:
                return f"{action}: {params}"


@dataclass
class TransformPreset:
    """
    Complete transformation preset with multiple steps.
    
    Attributes:
        name: Unique preset name
        description: User description
        steps: Ordered list of transformation steps
        created: Creation timestamp
        modified: Last modification timestamp
        keyboard_shortcut: Optional shortcut (e.g., "Ctrl+Shift+1")
        category: Optional category for organization
        is_builtin: Whether this is a built-in preset (read-only)
    """
    name: str
    description: str = ""
    steps: list[PresetStep] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    keyboard_shortcut: str | None = None
    category: str = "Custom"
    is_builtin: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'created': self.created,
            'modified': self.modified,
            'keyboard_shortcut': self.keyboard_shortcut,
            'category': self.category,
            'is_builtin': self.is_builtin
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransformPreset:
        """Create TransformPreset from dictionary."""
        steps = [PresetStep.from_dict(s) for s in data.get('steps', [])]
        return cls(
            name=data.get('name', 'Unnamed'),
            description=data.get('description', ''),
            steps=steps,
            created=data.get('created', datetime.now().isoformat()),
            modified=data.get('modified', datetime.now().isoformat()),
            keyboard_shortcut=data.get('keyboard_shortcut'),
            category=data.get('category', 'Custom'),
            is_builtin=data.get('is_builtin', False)
        )
    
    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified = datetime.now().isoformat()
    
    def add_step(self, step: PresetStep) -> None:
        """Add a step to the preset."""
        self.steps.append(step)
        self.update_modified()
    
    def remove_step(self, index: int) -> bool:
        """Remove a step by index."""
        if 0 <= index < len(self.steps):
            del self.steps[index]
            self.update_modified()
            return True
        return False
    
    def move_step(self, from_index: int, to_index: int) -> bool:
        """Move a step from one position to another."""
        if 0 <= from_index < len(self.steps) and 0 <= to_index < len(self.steps):
            step = self.steps.pop(from_index)
            self.steps.insert(to_index, step)
            self.update_modified()
            return True
        return False
    
    def get_enabled_steps(self) -> list[PresetStep]:
        """Get only enabled steps."""
        return [s for s in self.steps if s.enabled]
    
    def get_step_count(self) -> int:
        """Get total number of steps."""
        return len(self.steps)
    
    def get_enabled_count(self) -> int:
        """Get number of enabled steps."""
        return len(self.get_enabled_steps())


class PresetExecutor:
    """
    Executes preset steps on text.
    
    Integrates with TextTransformer and TextCleaner for actual operations.
    """
    
    __slots__ = ('_transform_func', '_cleanup_func')
    
    def __init__(self) -> None:
        """Initialize executor with lazy imports."""
        self._transform_func: Callable | None = None
        self._cleanup_func: Callable | None = None
    
    def _get_transformer(self) -> Callable:
        """Lazy load TextTransformer."""
        if self._transform_func is None:
            from core.text_transformer import TextTransformer
            self._transform_func = TextTransformer.transform_text
        return self._transform_func
    
    def _get_cleaner(self) -> Callable:
        """Lazy load TextCleaner."""
        if self._cleanup_func is None:
            from core.text_cleaner import TextCleaner
            self._cleanup_func = TextCleaner.cleanup
        return self._cleanup_func
    
    def execute_preset(
        self,
        text: str,
        preset: TransformPreset,
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> tuple[str, list[str]]:
        """
        Execute all enabled steps in a preset.
        
        Args:
            text: Input text to transform
            preset: Preset to execute
            progress_callback: Optional callback(current, total, step_name)
            
        Returns:
            Tuple of (result_text, list of step descriptions that were applied)
        """
        result = text
        applied_steps: list[str] = []
        enabled_steps = preset.get_enabled_steps()
        total = len(enabled_steps)
        
        for i, step in enumerate(enabled_steps):
            if progress_callback:
                progress_callback(i, total, step.get_display_name())
            
            try:
                result = self.execute_step(result, step)
                applied_steps.append(step.get_display_name())
            except Exception as e:
                # Log error but continue with remaining steps
                if _logger:
                    _logger.warning(f"Preset step failed: {step.get_display_name()}", details=str(e))
                applied_steps.append(f"[ERROR] {step.get_display_name()}: {e}")
        
        if progress_callback:
            progress_callback(total, total, "Complete")
        
        return result, applied_steps
    
    def execute_step(self, text: str, step: PresetStep) -> str:
        """
        Execute a single preset step.
        
        Args:
            text: Input text
            step: Step to execute
            
        Returns:
            Transformed text
        """
        action = step.action
        params = step.params
        
        match action:
            case ActionType.TRANSFORM:
                transformer = self._get_transformer()
                mode = params.get('mode', 'UPPERCASE')
                return transformer(text, mode)
            
            case ActionType.CLEANUP:
                cleaner = self._get_cleaner()
                operation = params.get('operation', 'trim_whitespace')
                return cleaner(text, operation)
            
            case ActionType.REPLACE:
                find = params.get('find', '')
                replace = params.get('replace', '')
                case_sensitive = params.get('case_sensitive', True)
                if case_sensitive:
                    return text.replace(find, replace)
                else:
                    pattern = re.compile(re.escape(find), re.IGNORECASE)
                    return pattern.sub(replace, text)
            
            case ActionType.REGEX_REPLACE:
                pattern = params.get('pattern', '')
                replacement = params.get('replacement', '')
                flags = params.get('flags', 0)
                try:
                    return re.sub(pattern, replacement, text, flags=flags)
                except re.error as e:
                    if _logger:
                        _logger.warning(f"Regex replace failed: {pattern}", details=str(e))
                    return text
            
            case ActionType.SPLIT:
                delimiter = params.get('delimiter', '\n')
                # Convert escaped sequences
                delimiter = delimiter.replace('\\n', '\n').replace('\\t', '\t')
                parts = text.split(delimiter)
                return '\n'.join(parts)
            
            case ActionType.JOIN:
                delimiter = params.get('delimiter', ' ')
                delimiter = delimiter.replace('\\n', '\n').replace('\\t', '\t')
                lines = text.splitlines()
                return delimiter.join(lines)
            
            case ActionType.WRAP:
                width = params.get('width', 80)
                import textwrap
                return textwrap.fill(text, width=width)
            
            case ActionType.PREFIX:
                prefix = params.get('text', '')
                per_line = params.get('per_line', False)
                if per_line:
                    lines = text.splitlines()
                    return '\n'.join(prefix + line for line in lines)
                return prefix + text
            
            case ActionType.SUFFIX:
                suffix = params.get('text', '')
                per_line = params.get('per_line', False)
                if per_line:
                    lines = text.splitlines()
                    return '\n'.join(line + suffix for line in lines)
                return text + suffix
            
            case ActionType.TRIM_LINES:
                lines = text.splitlines()
                return '\n'.join(line.strip() for line in lines)
            
            case _:
                return text


class PresetManager:
    """
    Manages preset storage, loading, and organization.
    
    Presets are stored in JSON format in the user's config directory.
    """
    
    # Default presets file name
    _PRESETS_FILE: ClassVar[str] = "presets.json"
    
    # Built-in presets
    _BUILTIN_PRESETS: ClassVar[list[dict]] = [
        {
            "name": "Code Variable Cleanup",
            "description": "Clean whitespace and convert to snake_case",
            "category": "Developer",
            "is_builtin": True,
            "steps": [
                {"action": "cleanup", "params": {"operation": "trim_whitespace"}},
                {"action": "cleanup", "params": {"operation": "collapse_whitespace"}},
                {"action": "transform", "params": {"mode": "snake_case"}}
            ]
        },
        {
            "name": "Markdown Cleanup",
            "description": "Clean up Markdown text formatting",
            "category": "Writing",
            "is_builtin": True,
            "steps": [
                {"action": "cleanup", "params": {"operation": "normalize_line_endings"}},
                {"action": "cleanup", "params": {"operation": "remove_trailing_whitespace"}},
                {"action": "cleanup", "params": {"operation": "collapse_blank_lines"}}
            ]
        },
        {
            "name": "Plain Text Export",
            "description": "Strip formatting and normalize text",
            "category": "General",
            "is_builtin": True,
            "steps": [
                {"action": "cleanup", "params": {"operation": "strip_html"}},
                {"action": "cleanup", "params": {"operation": "normalize_unicode"}},
                {"action": "cleanup", "params": {"operation": "trim_whitespace"}}
            ]
        },
        {
            "name": "Title Case Headlines",
            "description": "Convert to title case and trim",
            "category": "Writing",
            "is_builtin": True,
            "steps": [
                {"action": "trim_lines", "params": {}},
                {"action": "transform", "params": {"mode": "Title Case"}}
            ]
        },
        {
            "name": "Constant Name Generator",
            "description": "Convert to CONSTANT_CASE for code constants",
            "category": "Developer",
            "is_builtin": True,
            "steps": [
                {"action": "cleanup", "params": {"operation": "collapse_whitespace"}},
                {"action": "transform", "params": {"mode": "CONSTANT_CASE"}}
            ]
        },
        {
            "name": "URL Slug Generator",
            "description": "Create URL-friendly slugs from text",
            "category": "Developer",
            "is_builtin": True,
            "steps": [
                {"action": "cleanup", "params": {"operation": "remove_non_printable"}},
                {"action": "transform", "params": {"mode": "kebab-case"}}
            ]
        }
    ]
    
    __slots__ = ('_presets', '_presets_path', '_executor')
    
    def __init__(self, presets_dir: Path | None = None) -> None:
        """
        Initialize preset manager.
        
        Args:
            presets_dir: Directory to store presets (uses default if None)
        """
        self._presets: dict[str, TransformPreset] = {}
        self._executor = PresetExecutor()
        
        # Determine presets path
        if presets_dir is None:
            # Use app data directory
            from PyQt6.QtCore import QStandardPaths
            app_data = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
            presets_dir = Path(app_data) / "RNV" / "TextTransformer"
        
        self._presets_path = presets_dir / self._PRESETS_FILE
        
        # Load built-in presets
        self._load_builtin_presets()
        
        # Load user presets
        self.load_presets()
    
    def _load_builtin_presets(self) -> None:
        """Load built-in presets."""
        for preset_data in self._BUILTIN_PRESETS:
            preset = TransformPreset.from_dict(preset_data)
            self._presets[preset.name] = preset
    
    def load_presets(self) -> bool:
        """
        Load presets from file.
        
        Returns:
            True if loaded successfully
        """
        if not self._presets_path.exists():
            return False
        
        def _do_load() -> bool:
            with open(self._presets_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for preset_data in data.get('presets', []):
                preset = TransformPreset.from_dict(preset_data)
                # Don't overwrite built-in presets
                if preset.name not in self._presets or not self._presets[preset.name].is_builtin:
                    self._presets[preset.name] = preset
            
            return True
        
        return ErrorHandler.safe_execute(
            _do_load, "loading presets", fallback_value=False
        ) or False
    
    def save_presets(self) -> bool:
        """
        Save user presets to file.
        
        Returns:
            True if saved successfully
        """
        def _do_save() -> bool:
            # Ensure directory exists
            self._presets_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Only save non-builtin presets
            user_presets = [
                p.to_dict() for p in self._presets.values()
                if not p.is_builtin
            ]
            
            data = {'presets': user_presets}
            
            with open(self._presets_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        
        return ErrorHandler.safe_execute(
            _do_save, "saving presets", fallback_value=False
        ) or False
    
    def get_preset(self, name: str) -> TransformPreset | None:
        """Get preset by name."""
        return self._presets.get(name)
    
    def get_all_presets(self) -> list[TransformPreset]:
        """Get all presets sorted by name."""
        return sorted(self._presets.values(), key=lambda p: p.name.lower())
    
    def get_presets_by_category(self) -> dict[str, list[TransformPreset]]:
        """Get presets organized by category."""
        categories: dict[str, list[TransformPreset]] = {}
        for preset in self._presets.values():
            cat = preset.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(preset)
        
        # Sort presets within each category
        for cat in categories:
            categories[cat].sort(key=lambda p: p.name.lower())
        
        return categories
    
    def get_preset_names(self) -> list[str]:
        """Get sorted list of preset names."""
        return sorted(self._presets.keys(), key=str.lower)
    
    def add_preset(self, preset: TransformPreset) -> bool:
        """
        Add or update a preset.
        
        Args:
            preset: Preset to add
            
        Returns:
            True if added successfully
        """
        if preset.is_builtin:
            return False  # Can't add built-in presets
        
        preset.update_modified()
        self._presets[preset.name] = preset
        return self.save_presets()
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset by name.
        
        Args:
            name: Preset name to delete
            
        Returns:
            True if deleted successfully
        """
        preset = self._presets.get(name)
        if preset is None or preset.is_builtin:
            return False
        
        del self._presets[name]
        return self.save_presets()
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset.
        
        Args:
            old_name: Current preset name
            new_name: New preset name
            
        Returns:
            True if renamed successfully
        """
        preset = self._presets.get(old_name)
        if preset is None or preset.is_builtin:
            return False
        
        if new_name in self._presets:
            return False  # Name already exists
        
        del self._presets[old_name]
        preset.name = new_name
        preset.update_modified()
        self._presets[new_name] = preset
        return self.save_presets()
    
    def duplicate_preset(self, name: str, new_name: str | None = None) -> TransformPreset | None:
        """
        Duplicate a preset.
        
        Args:
            name: Preset to duplicate
            new_name: Name for the copy (auto-generated if None)
            
        Returns:
            New preset or None if failed
        """
        original = self._presets.get(name)
        if original is None:
            return None
        
        # Generate new name
        if new_name is None:
            new_name = f"{original.name} (Copy)"
            counter = 1
            while new_name in self._presets:
                counter += 1
                new_name = f"{original.name} (Copy {counter})"
        
        # Create copy
        new_preset = TransformPreset(
            name=new_name,
            description=original.description,
            steps=[PresetStep.from_dict(s.to_dict()) for s in original.steps],
            category=original.category,
            is_builtin=False
        )
        
        self._presets[new_name] = new_preset
        self.save_presets()
        return new_preset
    
    def execute_preset(
        self,
        text: str,
        preset_name: str,
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> tuple[str, list[str]] | None:
        """
        Execute a preset by name.
        
        Args:
            text: Input text
            preset_name: Name of preset to execute
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (result, applied_steps) or None if preset not found
        """
        preset = self.get_preset(preset_name)
        if preset is None:
            return None
        
        return self._executor.execute_preset(text, preset, progress_callback)
    
    def preview_preset(self, text: str, preset: TransformPreset) -> str:
        """
        Preview preset result without saving.
        
        Args:
            text: Sample text
            preset: Preset to preview
            
        Returns:
            Transformed text
        """
        result, _ = self._executor.execute_preset(text, preset)
        return result
    
    def export_preset(self, name: str, file_path: Path) -> bool:
        """
        Export a single preset to file.
        
        Args:
            name: Preset name
            file_path: Export file path
            
        Returns:
            True if exported successfully
        """
        preset = self._presets.get(name)
        if preset is None:
            return False
        
        def _do_export() -> bool:
            data = preset.to_dict()
            data['is_builtin'] = False  # Exported presets are user presets
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        
        return ErrorHandler.safe_execute(
            _do_export, f"exporting preset '{name}'", fallback_value=False
        ) or False
    
    def import_preset(self, file_path: Path) -> TransformPreset | None:
        """
        Import a preset from file.
        
        Args:
            file_path: Import file path
            
        Returns:
            Imported preset or None if failed
        """
        def _do_import() -> TransformPreset:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preset = TransformPreset.from_dict(data)
            preset.is_builtin = False
            
            # Handle name conflicts
            original_name = preset.name
            counter = 1
            while preset.name in self._presets:
                preset.name = f"{original_name} ({counter})"
                counter += 1
            
            self._presets[preset.name] = preset
            self.save_presets()
            return preset
        
        return ErrorHandler.safe_execute(
            _do_import, f"importing preset from '{file_path.name}'"
        )
    
    def get_categories(self) -> list[str]:
        """Get sorted list of all categories."""
        categories = set(p.category for p in self._presets.values())
        return sorted(categories)
    
    def get_shortcuts(self) -> dict[str, str]:
        """Get mapping of keyboard shortcuts to preset names."""
        return {
            p.keyboard_shortcut: p.name
            for p in self._presets.values()
            if p.keyboard_shortcut
        }


# Helper functions for creating common steps
def create_transform_step(mode: str, description: str = "") -> PresetStep:
    """Create a transformation step."""
    return PresetStep(
        action=ActionType.TRANSFORM,
        params={'mode': mode},
        description=description or f"Transform: {mode}"
    )


def create_cleanup_step(operation: str, description: str = "") -> PresetStep:
    """Create a cleanup step."""
    return PresetStep(
        action=ActionType.CLEANUP,
        params={'operation': operation},
        description=description or f"Cleanup: {operation}"
    )


def create_replace_step(
    find: str,
    replace: str,
    case_sensitive: bool = True,
    description: str = ""
) -> PresetStep:
    """Create a find/replace step."""
    return PresetStep(
        action=ActionType.REPLACE,
        params={
            'find': find,
            'replace': replace,
            'case_sensitive': case_sensitive
        },
        description=description or f"Replace '{find[:20]}'"
    )


def create_regex_step(
    pattern: str,
    replacement: str,
    flags: int = 0,
    description: str = ""
) -> PresetStep:
    """Create a regex replacement step."""
    return PresetStep(
        action=ActionType.REGEX_REPLACE,
        params={
            'pattern': pattern,
            'replacement': replacement,
            'flags': flags
        },
        description=description or f"Regex: {pattern[:20]}"
    )