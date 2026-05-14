"""
RNV Text Transformer - Folder Watcher Module
File system monitoring for automatic text transformation

Python 3.13 Optimized:
- watchdog for file system events
- Threading for background monitoring
- Queue-based event processing
- Configurable watch rules

"""

from __future__ import annotations

import time
import threading
import queue
from pathlib import Path
from typing import Callable, NamedTuple, ClassVar, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from enum import StrEnum
from datetime import datetime

from utils.logger import get_module_logger

_logger = get_module_logger("FolderWatcher")

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from watchdog.observers import Observer  # type: ignore[import-not-found]
    from watchdog.events import FileSystemEventHandler as FSEventHandler  # type: ignore[import-not-found]

# Try to import watchdog, provide fallback if not available
try:
    from watchdog.observers import Observer as _Observer  # type: ignore[import-not-found]
    from watchdog.events import (  # type: ignore[import-not-found]
        FileSystemEventHandler,
        FileCreatedEvent,
        FileModifiedEvent,
        FileMovedEvent,
        DirCreatedEvent,
    )
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    _Observer = None  # type: ignore[misc, assignment]
    FileSystemEventHandler = object  # type: ignore[misc, assignment]


class WatchEventType(StrEnum):
    """Types of watch events."""
    FILE_CREATED = "created"
    FILE_MODIFIED = "modified"
    FILE_MOVED = "moved"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_ERROR = "processing_error"
    WATCHER_STARTED = "watcher_started"
    WATCHER_STOPPED = "watcher_stopped"


@dataclass
class WatchEvent:
    """Event from folder watcher."""
    event_type: WatchEventType
    file_path: Path | None = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    error: Exception | None = None


@dataclass
class WatchRule:
    """Configuration for a watch folder rule."""
    id: str
    input_folder: Path
    output_folder: Path
    file_patterns: list[str] = field(default_factory=lambda: ["*.txt"])
    transform_mode: str | None = None
    preset_name: str | None = None
    cleanup_ops: list[str] = field(default_factory=list)
    enabled: bool = True
    process_existing: bool = False
    delete_source: bool = False
    
    def matches_file(self, file_path: Path) -> bool:
        """Check if file matches this rule's patterns."""
        import fnmatch
        name = file_path.name
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.file_patterns)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'input_folder': str(self.input_folder),
            'output_folder': str(self.output_folder),
            'file_patterns': self.file_patterns,
            'transform_mode': self.transform_mode,
            'preset_name': self.preset_name,
            'cleanup_ops': self.cleanup_ops,
            'enabled': self.enabled,
            'process_existing': self.process_existing,
            'delete_source': self.delete_source,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WatchRule':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            input_folder=Path(data.get('input_folder', '')),
            output_folder=Path(data.get('output_folder', '')),
            file_patterns=data.get('file_patterns', ['*.txt']),
            transform_mode=data.get('transform_mode'),
            preset_name=data.get('preset_name'),
            cleanup_ops=data.get('cleanup_ops', []),
            enabled=data.get('enabled', True),
            process_existing=data.get('process_existing', False),
            delete_source=data.get('delete_source', False),
        )


class WatchEventHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Handler for file system events."""
    
    __slots__ = ('rule', 'event_queue', '_debounce_dict', '_debounce_delay')
    
    def __init__(
        self, 
        rule: WatchRule, 
        event_queue: queue.Queue,
        debounce_delay: float = 1.0
    ) -> None:
        """
        Initialize event handler.
        
        Args:
            rule: Watch rule for this handler
            event_queue: Queue to put events into
            debounce_delay: Seconds to wait before processing (debounce)
        """
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.rule = rule
        self.event_queue = event_queue
        self._debounce_dict: dict[str, float] = {}
        self._debounce_delay = debounce_delay
    
    def _should_process(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        # Skip if rule disabled
        if not self.rule.enabled:
            return False
        
        # Skip if doesn't match patterns
        if not self.rule.matches_file(file_path):
            return False
        
        # Skip if it's in the output folder (avoid loops)
        try:
            file_path.relative_to(self.rule.output_folder)
            return False  # File is in output folder
        except ValueError:
            pass  # Not in output folder, OK to process
        
        # Debounce check
        key = str(file_path)
        current_time = time.time()
        last_time = self._debounce_dict.get(key, 0)
        
        if current_time - last_time < self._debounce_delay:
            return False
        
        self._debounce_dict[key] = current_time
        return True
    
    def on_created(self, event) -> None:
        """Handle file created event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if self._should_process(file_path):
            self.event_queue.put(WatchEvent(
                event_type=WatchEventType.FILE_CREATED,
                file_path=file_path,
                message=f"New file: {file_path.name}"
            ))
    
    def on_modified(self, event) -> None:
        """Handle file modified event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if self._should_process(file_path):
            self.event_queue.put(WatchEvent(
                event_type=WatchEventType.FILE_MODIFIED,
                file_path=file_path,
                message=f"Modified: {file_path.name}"
            ))
    
    def on_moved(self, event) -> None:
        """Handle file moved event."""
        if event.is_directory:
            return
        
        file_path = Path(event.dest_path)
        if self._should_process(file_path):
            self.event_queue.put(WatchEvent(
                event_type=WatchEventType.FILE_MOVED,
                file_path=file_path,
                message=f"Moved to: {file_path.name}"
            ))


class FolderWatcher:
    """
    Watches folders for file changes and triggers transformations.
    
    Features:
    - Multiple folder rules
    - Pattern matching
    - Debouncing
    - Event callbacks
    - Background processing
    """
    
    # Processing thread check interval
    _QUEUE_TIMEOUT: ClassVar[float] = 0.5
    
    __slots__ = (
        '_rules', '_observers', '_handlers', '_event_queue',
        '_processing_thread', '_running', '_event_callback',
        '_lock'
    )
    
    def __init__(self) -> None:
        """Initialize folder watcher."""
        self._rules: dict[str, WatchRule] = {}
        self._observers: dict[str, Any] = {}  # Observer instances when watchdog available
        self._handlers: dict[str, WatchEventHandler] = {}
        self._event_queue: queue.Queue[WatchEvent] = queue.Queue()
        self._processing_thread: threading.Thread | None = None
        self._running = False
        self._event_callback: Callable[[WatchEvent], None] | None = None
        self._lock = threading.Lock()
    
    @staticmethod
    def is_available() -> bool:
        """Check if watchdog is available."""
        return WATCHDOG_AVAILABLE
    
    def set_event_callback(self, callback: Callable[[WatchEvent], None]) -> None:
        """
        Set callback for watch events.
        
        Args:
            callback: Function to call with WatchEvent
        """
        self._event_callback = callback
    
    def add_rule(self, rule: WatchRule) -> bool:
        """
        Add a watch rule.
        
        Args:
            rule: Watch rule to add
            
        Returns:
            True if added successfully
        """
        if not WATCHDOG_AVAILABLE:
            return False
        
        with self._lock:
            # Validate folders
            if not rule.input_folder.exists():
                return False
            
            # Create output folder if needed
            rule.output_folder.mkdir(parents=True, exist_ok=True)
            
            self._rules[rule.id] = rule
            
            # If running, start watching this folder
            if self._running:
                self._start_rule_watcher(rule)
            
            return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a watch rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            True if removed successfully
        """
        with self._lock:
            if rule_id not in self._rules:
                return False
            
            # Stop observer for this rule
            self._stop_rule_watcher(rule_id)
            
            del self._rules[rule_id]
            return True
    
    def update_rule(self, rule: WatchRule) -> bool:
        """
        Update an existing rule.
        
        Args:
            rule: Updated rule
            
        Returns:
            True if updated successfully
        """
        with self._lock:
            if rule.id not in self._rules:
                return False
            
            # Stop and restart watcher
            was_running = rule.id in self._observers
            if was_running:
                self._stop_rule_watcher(rule.id)
            
            self._rules[rule.id] = rule
            
            if was_running and rule.enabled:
                self._start_rule_watcher(rule)
            
            return True
    
    def get_rules(self) -> list[WatchRule]:
        """Get all rules."""
        with self._lock:
            return list(self._rules.values())
    
    def get_rule(self, rule_id: str) -> WatchRule | None:
        """Get a specific rule."""
        return self._rules.get(rule_id)
    
    def start(self) -> bool:
        """
        Start watching all enabled rules.
        
        Returns:
            True if started successfully
        """
        if not WATCHDOG_AVAILABLE:
            self._emit_event(WatchEvent(
                event_type=WatchEventType.PROCESSING_ERROR,
                message="watchdog library not installed"
            ))
            return False
        
        if self._running:
            return True
        
        with self._lock:
            self._running = True
            
            # Start observers for all enabled rules
            for rule in self._rules.values():
                if rule.enabled:
                    self._start_rule_watcher(rule)
            
            # Start processing thread
            self._processing_thread = threading.Thread(
                target=self._process_events,
                daemon=True,
                name="FolderWatcher-Processor"
            )
            self._processing_thread.start()
            
            self._emit_event(WatchEvent(
                event_type=WatchEventType.WATCHER_STARTED,
                message=f"Watching {len(self._observers)} folder(s)"
            ))
            
            return True
    
    def stop(self) -> None:
        """Stop all watchers."""
        with self._lock:
            self._running = False
            
            # Stop all observers
            for rule_id in list(self._observers.keys()):
                self._stop_rule_watcher(rule_id)
            
            # Wait for processing thread
            if self._processing_thread is not None:
                self._processing_thread.join(timeout=2.0)
                self._processing_thread = None
            
            self._emit_event(WatchEvent(
                event_type=WatchEventType.WATCHER_STOPPED,
                message="Watcher stopped"
            ))
    
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
    
    def process_existing_files(self, rule_id: str | None = None) -> int:
        """
        Process existing files in watched folders.
        
        Args:
            rule_id: Specific rule to process, or None for all
            
        Returns:
            Number of files queued for processing
        """
        count = 0
        
        with self._lock:
            rules_to_process = (
                [self._rules[rule_id]] if rule_id and rule_id in self._rules
                else self._rules.values()
            )
            
            for rule in rules_to_process:
                if not rule.enabled:
                    continue
                
                for pattern in rule.file_patterns:
                    for file_path in rule.input_folder.glob(pattern):
                        if file_path.is_file():
                            self._event_queue.put(WatchEvent(
                                event_type=WatchEventType.FILE_CREATED,
                                file_path=file_path,
                                message=f"Existing file: {file_path.name}"
                            ))
                            count += 1
        
        return count
    
    def _start_rule_watcher(self, rule: WatchRule) -> None:
        """Start watcher for a specific rule."""
        if not WATCHDOG_AVAILABLE:
            return
        
        if rule.id in self._observers:
            return  # Already watching
        
        handler = WatchEventHandler(rule, self._event_queue)
        observer = _Observer()
        observer.schedule(handler, str(rule.input_folder), recursive=False)
        observer.start()
        
        self._observers[rule.id] = observer
        self._handlers[rule.id] = handler
        
        # Process existing files if configured
        if rule.process_existing:
            self.process_existing_files(rule.id)
    
    def _stop_rule_watcher(self, rule_id: str) -> None:
        """Stop watcher for a specific rule."""
        if rule_id in self._observers:
            observer = self._observers[rule_id]
            observer.stop()
            observer.join(timeout=2.0)
            del self._observers[rule_id]
        
        if rule_id in self._handlers:
            del self._handlers[rule_id]
    
    def _process_events(self) -> None:
        """Process events from queue (runs in background thread)."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=self._QUEUE_TIMEOUT)
                self._handle_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                if _logger:
                    _logger.error("Event processing error", error=e)
                self._emit_event(WatchEvent(
                    event_type=WatchEventType.PROCESSING_ERROR,
                    message=f"Processing error: {e}",
                    error=e
                ))
    
    def _handle_event(self, event: WatchEvent) -> None:
        """Handle a single watch event."""
        if event.file_path is None:
            self._emit_event(event)
            return
        
        # Find matching rule
        rule = self._find_rule_for_file(event.file_path)
        if rule is None:
            return
        
        # Emit processing started
        self._emit_event(WatchEvent(
            event_type=WatchEventType.PROCESSING_STARTED,
            file_path=event.file_path,
            message=f"Processing: {event.file_path.name}"
        ))
        
        try:
            # Process the file
            self._process_file(event.file_path, rule)
            
            # Emit success
            self._emit_event(WatchEvent(
                event_type=WatchEventType.PROCESSING_COMPLETE,
                file_path=event.file_path,
                message=f"Complete: {event.file_path.name}"
            ))
            
        except Exception as e:
            if _logger:
                _logger.error(f"File processing failed: {event.file_path.name}", error=e)
            self._emit_event(WatchEvent(
                event_type=WatchEventType.PROCESSING_ERROR,
                file_path=event.file_path,
                message=f"Error: {e}",
                error=e
            ))
    
    def _find_rule_for_file(self, file_path: Path) -> WatchRule | None:
        """Find the rule that matches a file."""
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            # Check if file is in the input folder
            try:
                file_path.relative_to(rule.input_folder)
            except ValueError:
                continue
            
            # Check if file matches patterns
            if rule.matches_file(file_path):
                return rule
        
        return None
    
    def _process_file(self, file_path: Path, rule: WatchRule) -> None:
        """Process a file according to its rule."""
        # Import here to avoid circular imports
        from core.text_transformer import TextTransformer
        from core.text_cleaner import TextCleaner, CleanupOperation
        from core.preset_manager import PresetManager, PresetExecutor
        from utils.file_handler import FileHandler
        
        # Read file
        content = FileHandler.read_file_content(file_path)
        if content is None:
            raise ValueError(f"Could not read file: {file_path}")
        
        result = content
        
        # Apply cleanup operations
        if rule.cleanup_ops:
            for op_name in rule.cleanup_ops:
                op = CleanupOperation(op_name)
                result = TextCleaner.apply_operation(result, op)
        
        # Apply preset
        if rule.preset_name:
            preset_manager = PresetManager()
            preset = preset_manager.get_preset(rule.preset_name)
            if preset:
                executor = PresetExecutor(preset_manager)
                result = executor.execute(preset, result)
        
        # Apply transform mode
        if rule.transform_mode:
            result = TextTransformer.transform_text(result, rule.transform_mode)
        
        # Write output
        output_path = rule.output_folder / file_path.name
        output_path.write_text(result, encoding='utf-8')
        
        # Delete source if configured
        if rule.delete_source and output_path.exists():
            file_path.unlink()
    
    def _emit_event(self, event: WatchEvent) -> None:
        """Emit event to callback."""
        if self._event_callback is not None:
            try:
                self._event_callback(event)
            except Exception as e:
                if _logger:
                    _logger.warning("Event callback error", details=str(e))


class WatchRuleManager:
    """
    Manages persistence of watch rules.
    
    Rules are stored in QSettings alongside other app settings.
    """
    
    _SETTINGS_KEY: ClassVar[str] = "watch_folders/rules"
    
    __slots__ = ('_settings',)
    
    def __init__(self) -> None:
        """Initialize rule manager."""
        from PyQt6.QtCore import QSettings
        self._settings = QSettings("RNV", "RNV Text Transformer")
    
    def save_rules(self, rules: list[WatchRule]) -> None:
        """Save rules to settings."""
        import json
        data = [rule.to_dict() for rule in rules]
        self._settings.setValue(self._SETTINGS_KEY, json.dumps(data))
    
    def load_rules(self) -> list[WatchRule]:
        """Load rules from settings."""
        import json
        data_str = self._settings.value(self._SETTINGS_KEY, "[]")
        
        try:
            data = json.loads(data_str) if isinstance(data_str, str) else []
            return [WatchRule.from_dict(d) for d in data]
        except Exception as e:
            if _logger:
                _logger.warning("Failed to load watch rules, using defaults", details=str(e))
            return []
    
    def clear_rules(self) -> None:
        """Clear all saved rules."""
        self._settings.remove(self._SETTINGS_KEY)
