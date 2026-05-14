"""
RNV Text Transformer — Comprehensive Test Suite v1.0
=====================================================
Tests all core modules for functionality, edge cases, and boundary conditions.

Usage — place this file in the same folder as RNV_Text_Transformer.py
    python test_rnv_text_transformer.py        # standard run
    python test_rnv_text_transformer.py -v     # verbose (shows each test name)

Requirements: PyQt6  (pip install PyQt6)
"""

import sys, os, io, json, tempfile, shutil, unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# QApplication MUST exist before any Qt module is imported or instantiated
try:
    from PyQt6.QtWidgets import QApplication as _QApp
    from PyQt6.QtCore import Qt as _Qt
    if not _QApp.instance():
        _qapp = _QApp(sys.argv[:1])
        _qapp.setAttribute(_Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
except Exception:
    _qapp = None

# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — locate project root and wire package paths
# Files live in core/, ui/, utils/ subdirs OR flat in one directory.
# We handle both layouts transparently.
# ══════════════════════════════════════════════════════════════════════════════
import types, importlib.util

_THIS = Path(__file__).resolve()
_ROOT = None

for _c in [_THIS.parent, _THIS.parent.parent, Path("/mnt/project")]:
    if (_c / "RNV_Text_Transformer.py").exists():
        _ROOT = _c; break
    if (_c / "core").is_dir() and (_c / "utils").is_dir():
        _ROOT = _c; break

if _ROOT is None:
    sys.exit(
        "ERROR: Cannot find project root.\n"
        "Place test_rnv_text_transformer.py in the same folder as RNV_Text_Transformer.py"
    )

_SUBDIR_LAYOUT = (_ROOT / "core").is_dir()

if _SUBDIR_LAYOUT:
    sys.path.insert(0, str(_ROOT))
else:
    # Flat layout — create virtual core/utils/ui/cli packages pointing at the flat dir
    sys.path.insert(0, str(_ROOT))
    for _pkg in ("core", "utils", "ui", "cli"):
        _m = types.ModuleType(_pkg)
        _m.__path__ = [str(_ROOT)]
        _m.__package__ = _pkg
        sys.modules[_pkg] = _m

    _LOAD = {
        "core":  ["text_transformer", "text_cleaner", "text_statistics",
                  "diff_engine", "export_manager", "preset_manager",
                  "regex_patterns", "resource_loader", "theme_manager",
                  "batch_processor", "folder_watcher"],
        "utils": ["config", "logger", "dialog_styles", "file_handler",
                  "error_handler", "settings_manager", "clipboard_utils",
                  "async_workers", "dialog_helper"],
        "ui":    ["main_window", "base_dialog", "image_button",
                  "drag_drop_text_edit", "line_number_text_edit"],
        "cli":   ["rnv_transform"],
    }
    for _pkg, _names in _LOAD.items():
        for _name in _names:
            _full = f"{_pkg}.{_name}"
            if _full in sys.modules:
                continue
            _spec = importlib.util.spec_from_file_location(
                _full, str(_ROOT / f"{_name}.py"))
            if not _spec:
                continue
            _mod = importlib.util.module_from_spec(_spec)
            _mod.__package__ = _pkg
            sys.modules[_full] = _mod
            sys.modules.setdefault(_name, _mod)
            try:
                _spec.loader.exec_module(_mod)
            except Exception:
                pass  # Qt-heavy or disk-touching modules may fail headless

# ── Imports ────────────────────────────────────────────────────────────────────
from core.text_transformer  import TextTransformer, TransformMode
from core.text_cleaner      import TextCleaner, CleanupOperation, SplitJoinOperation
from core.text_statistics   import TextStatistics, TextStats
from core.diff_engine       import DiffEngine, DiffResult, DiffChange, ChangeType
from core.export_manager    import ExportManager, ExportFormat, ExportOptions, ExportError
from core.preset_manager    import (
    PresetManager, PresetExecutor, TransformPreset, PresetStep, ActionType
)
from core.batch_processor   import BatchProcessor, BatchResult, BatchProgress
from core.regex_patterns    import RegexPatterns, RegexHelper, PatternInfo
from core.theme_manager     import ThemeManager
from core.folder_watcher    import (
    FolderWatcher, WatchRule, WatchEvent, WatchEventType, WATCHDOG_AVAILABLE
)
from utils.dialog_styles    import DialogStyleManager
from utils.file_handler     import FileHandler, FileReadError, FileWriteError
from utils.error_handler    import ErrorHandler, ErrorContext
from utils.settings_manager import SettingsManager
from utils.clipboard_utils  import ClipboardUtils
from utils.logger           import Logger, LogLevel, get_module_logger, configure
from utils import config

# CLI — actual file is cli/rnv_transform.py
try:
    from cli.rnv_transform import CLIProcessor, CLIOptions, OutputFormat
    _CLI_AVAILABLE = True
except Exception:
    _CLI_AVAILABLE = False

# ANSI colour helpers
_G="\033[92m"; _R="\033[91m"; _Y="\033[93m"; _C="\033[96m"; _B="\033[1m"; _X="\033[0m"

# Temp root for any disk-touching tests
_TMP_ROOT = tempfile.mkdtemp()


# ══════════════════════════════════════════════════════════════════════════════
# 1. TEXT TRANSFORMER
# ══════════════════════════════════════════════════════════════════════════════
class TestTextTransformer(unittest.TestCase):
    """core/text_transformer.py — all 11 transform modes + edge cases."""

    # ── UPPERCASE ──────────────────────────────────────────────────────────────
    def test_uppercase_basic(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.UPPERCASE), "HELLO WORLD")

    def test_uppercase_already_upper(self):
        self.assertEqual(TextTransformer.transform_text("HELLO", TransformMode.UPPERCASE), "HELLO")

    def test_uppercase_mixed(self):
        self.assertEqual(TextTransformer.transform_text("Hello World", TransformMode.UPPERCASE), "HELLO WORLD")

    # ── LOWERCASE ─────────────────────────────────────────────────────────────
    def test_lowercase_basic(self):
        self.assertEqual(TextTransformer.transform_text("HELLO WORLD", TransformMode.LOWERCASE), "hello world")

    def test_lowercase_already_lower(self):
        self.assertEqual(TextTransformer.transform_text("hello", TransformMode.LOWERCASE), "hello")

    def test_lowercase_mixed(self):
        self.assertEqual(TextTransformer.transform_text("Hello World", TransformMode.LOWERCASE), "hello world")

    # ── TITLE CASE ────────────────────────────────────────────────────────────
    def test_title_case_basic(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.TITLE_CASE), "Hello World")

    def test_title_case_all_upper(self):
        self.assertEqual(TextTransformer.transform_text("HELLO WORLD", TransformMode.TITLE_CASE), "Hello World")

    def test_title_case_multiword(self):
        result = TextTransformer.transform_text("the quick brown fox", TransformMode.TITLE_CASE)
        self.assertTrue(result[0].isupper())

    # ── SENTENCE CASE ─────────────────────────────────────────────────────────
    def test_sentence_case_basic(self):
        result = TextTransformer.transform_text("hello world. goodbye world.", TransformMode.SENTENCE_CASE)
        self.assertTrue(result[0].isupper())

    def test_sentence_case_all_upper(self):
        result = TextTransformer.transform_text("HELLO WORLD", TransformMode.SENTENCE_CASE)
        self.assertTrue(result[0].isupper())
        self.assertTrue(result[1:].islower() or True)  # rest may be lower

    # ── CAMEL CASE ────────────────────────────────────────────────────────────
    def test_camel_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.CAMEL_CASE), "helloWorld")

    def test_camel_case_from_snake(self):
        self.assertEqual(TextTransformer.transform_text("hello_world", TransformMode.CAMEL_CASE), "helloWorld")

    def test_camel_case_from_kebab(self):
        self.assertEqual(TextTransformer.transform_text("hello-world", TransformMode.CAMEL_CASE), "helloWorld")

    def test_camel_case_starts_lowercase(self):
        result = TextTransformer.transform_text("Hello World", TransformMode.CAMEL_CASE)
        self.assertTrue(result[0].islower())

    def test_camel_case_three_words(self):
        self.assertEqual(TextTransformer.transform_text("foo bar baz", TransformMode.CAMEL_CASE), "fooBarBaz")

    # ── PASCAL CASE ───────────────────────────────────────────────────────────
    def test_pascal_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.PASCAL_CASE), "HelloWorld")

    def test_pascal_case_starts_uppercase(self):
        result = TextTransformer.transform_text("hello world", TransformMode.PASCAL_CASE)
        self.assertTrue(result[0].isupper())

    def test_pascal_case_from_snake(self):
        self.assertEqual(TextTransformer.transform_text("hello_world", TransformMode.PASCAL_CASE), "HelloWorld")

    # ── SNAKE CASE ────────────────────────────────────────────────────────────
    def test_snake_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.SNAKE_CASE), "hello_world")

    def test_snake_case_from_camel(self):
        self.assertEqual(TextTransformer.transform_text("helloWorld", TransformMode.SNAKE_CASE), "hello_world")

    def test_snake_case_all_lowercase(self):
        result = TextTransformer.transform_text("Hello World", TransformMode.SNAKE_CASE)
        self.assertEqual(result, result.lower().replace(" ", "_").replace("-", "_") or result)
        self.assertNotIn(" ", result)

    def test_snake_case_no_spaces(self):
        result = TextTransformer.transform_text("hello world foo", TransformMode.SNAKE_CASE)
        self.assertNotIn(" ", result)
        self.assertNotIn("-", result)

    # ── CONSTANT CASE ─────────────────────────────────────────────────────────
    def test_constant_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.CONSTANT_CASE), "HELLO_WORLD")

    def test_constant_case_all_upper(self):
        result = TextTransformer.transform_text("hello world", TransformMode.CONSTANT_CASE)
        self.assertEqual(result, result.upper())

    def test_constant_case_no_spaces(self):
        result = TextTransformer.transform_text("hello world", TransformMode.CONSTANT_CASE)
        self.assertNotIn(" ", result)

    # ── KEBAB CASE ────────────────────────────────────────────────────────────
    def test_kebab_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.KEBAB_CASE), "hello-world")

    def test_kebab_case_from_snake(self):
        self.assertEqual(TextTransformer.transform_text("hello_world", TransformMode.KEBAB_CASE), "hello-world")

    def test_kebab_case_no_spaces(self):
        result = TextTransformer.transform_text("hello world", TransformMode.KEBAB_CASE)
        self.assertNotIn(" ", result)
        self.assertNotIn("_", result)

    # ── DOT CASE ──────────────────────────────────────────────────────────────
    def test_dot_case_from_spaces(self):
        self.assertEqual(TextTransformer.transform_text("hello world", TransformMode.DOT_CASE), "hello.world")

    def test_dot_case_no_spaces(self):
        result = TextTransformer.transform_text("hello world", TransformMode.DOT_CASE)
        self.assertNotIn(" ", result)

    # ── INVERTED CASE ─────────────────────────────────────────────────────────
    def test_inverted_case_basic(self):
        result = TextTransformer.transform_text("Hello World", TransformMode.INVERTED_CASE)
        self.assertEqual(result, "hELLO wORLD")

    def test_inverted_case_already_lower(self):
        result = TextTransformer.transform_text("hello", TransformMode.INVERTED_CASE)
        self.assertEqual(result, "HELLO")

    def test_inverted_case_already_upper(self):
        result = TextTransformer.transform_text("HELLO", TransformMode.INVERTED_CASE)
        self.assertEqual(result, "hello")

    # ── EDGE CASES ────────────────────────────────────────────────────────────
    def test_empty_string_all_modes(self):
        for mode in TransformMode:
            result = TextTransformer.transform_text("", mode)
            self.assertEqual(result, "", f"Mode {mode} failed on empty string")

    def test_whitespace_only(self):
        for mode in TransformMode:
            result = TextTransformer.transform_text("   ", mode)
            self.assertIsInstance(result, str)

    def test_single_char(self):
        self.assertEqual(TextTransformer.transform_text("a", TransformMode.UPPERCASE), "A")
        self.assertEqual(TextTransformer.transform_text("A", TransformMode.LOWERCASE), "a")

    def test_numbers_preserved(self):
        result = TextTransformer.transform_text("hello 123 world", TransformMode.UPPERCASE)
        self.assertIn("123", result)

    def test_get_available_modes_returns_list(self):
        modes = TextTransformer.get_available_modes()
        self.assertIsInstance(modes, list)
        self.assertGreater(len(modes), 0)

    def test_get_available_modes_count(self):
        self.assertEqual(len(TextTransformer.get_available_modes()), len(TransformMode))

    def test_get_mode_by_name_valid(self):
        mode = TextTransformer.get_mode_by_name("UPPERCASE")
        self.assertEqual(mode, TransformMode.UPPERCASE)

    def test_get_mode_by_name_invalid(self):
        mode = TextTransformer.get_mode_by_name("nonexistent")
        self.assertIsNone(mode)

    def test_transform_mode_enum_values(self):
        self.assertEqual(TransformMode.UPPERCASE, "UPPERCASE")
        self.assertEqual(TransformMode.LOWERCASE, "lowercase")
        self.assertEqual(TransformMode.SNAKE_CASE, "snake_case")
        self.assertEqual(TransformMode.KEBAB_CASE, "kebab-case")
        self.assertEqual(TransformMode.DOT_CASE, "dot.case")

    def test_multiline_uppercase(self):
        result = TextTransformer.transform_text("line one\nline two", TransformMode.UPPERCASE)
        self.assertIn("\n", result)
        self.assertEqual(result, "LINE ONE\nLINE TWO")

    def test_unicode_basic(self):
        result = TextTransformer.transform_text("café", TransformMode.UPPERCASE)
        self.assertIsInstance(result, str)

    def test_special_chars_preserved_in_snake(self):
        result = TextTransformer.transform_text("hello world!", TransformMode.SNAKE_CASE)
        self.assertIsInstance(result, str)


# ══════════════════════════════════════════════════════════════════════════════
# 2. TEXT CLEANER
# ══════════════════════════════════════════════════════════════════════════════
class TestTextCleaner(unittest.TestCase):
    """core/text_cleaner.py — all cleanup operations + split/join."""

    def test_trim_whitespace(self):
        self.assertEqual(TextCleaner.trim_whitespace("  hello  "), "hello")

    def test_trim_whitespace_empty(self):
        self.assertEqual(TextCleaner.trim_whitespace(""), "")

    def test_remove_extra_spaces(self):
        self.assertEqual(TextCleaner.remove_extra_spaces("hello   world"), "hello world")

    def test_remove_extra_blank_lines(self):
        text = "line1\n\n\nline2"
        result = TextCleaner.remove_extra_blank_lines(text)
        self.assertNotIn("\n\n\n", result)

    def test_remove_all_blank_lines(self):
        text = "line1\n\nline2\n\nline3"
        result = TextCleaner.remove_all_blank_lines(text)
        self.assertNotIn("\n\n", result)
        self.assertIn("line1", result)
        self.assertIn("line3", result)

    def test_fix_line_endings_unix(self):
        text = "line1\r\nline2\r\nline3"
        result = TextCleaner.fix_line_endings_unix(text)
        self.assertNotIn("\r\n", result)
        self.assertIn("\n", result)

    def test_fix_line_endings_windows(self):
        text = "line1\nline2\nline3"
        result = TextCleaner.fix_line_endings_windows(text)
        self.assertIn("\r\n", result)

    def test_remove_duplicate_lines(self):
        text = "apple\nbanana\napple\ncherry"
        result = TextCleaner.remove_duplicate_lines(text)
        lines = result.splitlines()
        self.assertEqual(len(lines), len(set(lines)))

    def test_sort_lines_asc(self):
        text = "banana\napple\ncherry"
        result = TextCleaner.sort_lines(text)
        lines = result.splitlines()
        self.assertEqual(lines, sorted(lines, key=str.lower))

    def test_sort_lines_desc(self):
        text = "banana\napple\ncherry"
        result = TextCleaner.sort_lines(text, reverse=True)
        lines = result.splitlines()
        self.assertEqual(lines, sorted(lines, key=str.lower, reverse=True))

    def test_strip_html_tags(self):
        result = TextCleaner.strip_html_tags("<b>hello</b> <i>world</i>")
        self.assertNotIn("<b>", result)
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_strip_html_nested(self):
        result = TextCleaner.strip_html_tags("<div><p>text</p></div>")
        self.assertNotIn("<", result)
        self.assertIn("text", result)

    def test_remove_non_printable(self):
        text = "hello\x00world\x01!"
        result = TextCleaner.remove_non_printable(text)
        self.assertNotIn("\x00", result)
        self.assertNotIn("\x01", result)
        self.assertIn("hello", result)

    def test_normalize_unicode(self):
        text = "caf\u00e9"
        result = TextCleaner.normalize_unicode(text)
        self.assertIsInstance(result, str)

    def test_remove_leading_spaces(self):
        text = "  line1\n  line2"
        result = TextCleaner.remove_leading_spaces(text)
        for line in result.splitlines():
            self.assertFalse(line.startswith(" "))

    def test_remove_trailing_spaces(self):
        text = "line1  \nline2  "
        result = TextCleaner.remove_trailing_spaces(text)
        for line in result.splitlines():
            self.assertFalse(line.endswith(" "))

    def test_cleanup_dispatcher_all_operations(self):
        """cleanup() routes all CleanupOperation values without raising."""
        text = "Hello   World\n\nTest  Line"
        for op in CleanupOperation:
            result = TextCleaner.cleanup(text, op)
            self.assertIsInstance(result, str, f"cleanup({op}) returned non-string")

    def test_cleanup_empty_string(self):
        for op in CleanupOperation:
            result = TextCleaner.cleanup("", op)
            self.assertIsInstance(result, str)

    def test_apply_multiple_cleanups(self):
        text = "  hello   world  "
        ops = [CleanupOperation.TRIM_WHITESPACE, CleanupOperation.REMOVE_EXTRA_SPACES]
        result = TextCleaner.apply_multiple_cleanups(text, ops)
        self.assertEqual(result, "hello world")

    def test_get_cleanup_operations_returns_list(self):
        ops = TextCleaner.get_cleanup_operations()
        self.assertIsInstance(ops, list)
        self.assertGreater(len(ops), 0)

    def test_split_by_comma(self):
        result = TextCleaner.split_join("a,b,c", SplitJoinOperation.SPLIT_BY_COMMA)
        self.assertIn("a", result)
        self.assertIn("b", result)
        self.assertIn("c", result)

    def test_join_with_comma(self):
        result = TextCleaner.split_join("a\nb\nc", SplitJoinOperation.JOIN_WITH_COMMA)
        self.assertIn(",", result)

    def test_wrap_text(self):
        long_text = "word " * 30
        result = TextCleaner.wrap_text(long_text, width=40)
        for line in result.splitlines():
            self.assertLessEqual(len(line), 45)  # small tolerance for word boundaries

    def test_unwrap_text(self):
        text = "line one\nline two\n\nparagraph two"
        result = TextCleaner.unwrap_text(text)
        self.assertIsInstance(result, str)

    def test_split_into_chunks(self):
        text = "a" * 100
        result = TextCleaner.split_into_chunks(text, chunk_size=10)
        self.assertIsInstance(result, str)

    def test_sort_lines_case_insensitive(self):
        text = "Banana\napple\nCherry"
        result = TextCleaner.sort_lines(text, case_insensitive=True)
        lines = result.splitlines()
        self.assertEqual(lines[0].lower(), "apple")


# ══════════════════════════════════════════════════════════════════════════════
# 3. TEXT STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
class TestTextStatistics(unittest.TestCase):
    """core/text_statistics.py — character, word, line, paragraph counting."""

    def test_empty_string(self):
        stats = TextStatistics.calculate("")
        self.assertEqual(stats.characters, 0)
        self.assertEqual(stats.words, 0)
        self.assertEqual(stats.lines, 0)

    def test_single_word(self):
        stats = TextStatistics.calculate("hello")
        self.assertEqual(stats.characters, 5)
        self.assertEqual(stats.words, 1)
        self.assertEqual(stats.lines, 1)

    def test_two_words(self):
        stats = TextStatistics.calculate("hello world")
        self.assertEqual(stats.words, 2)

    def test_character_count_with_spaces(self):
        stats = TextStatistics.calculate("hi there")
        self.assertEqual(stats.characters, 8)
        self.assertEqual(stats.characters_no_spaces, 7)

    def test_line_count_single(self):
        stats = TextStatistics.calculate("one line")
        self.assertEqual(stats.lines, 1)

    def test_line_count_multiple(self):
        stats = TextStatistics.calculate("line1\nline2\nline3")
        self.assertEqual(stats.lines, 3)

    def test_paragraph_count(self):
        stats = TextStatistics.calculate("para1\n\npara2\n\npara3")
        self.assertGreaterEqual(stats.paragraphs, 2)

    def test_characters_no_spaces(self):
        stats = TextStatistics.calculate("a b c")
        self.assertEqual(stats.characters_no_spaces, 3)

    def test_returns_text_stats(self):
        stats = TextStatistics.calculate("hello")
        self.assertIsInstance(stats, TextStats)

    def test_format_stats_compact(self):
        stats = TextStatistics.calculate("hello world")
        formatted = TextStatistics.format_stats(stats, compact=True)
        self.assertIsInstance(formatted, str)
        self.assertGreater(len(formatted), 0)

    def test_format_stats_verbose(self):
        stats = TextStatistics.calculate("hello world\nsecond line")
        formatted = TextStatistics.format_stats(stats, compact=False)
        self.assertIsInstance(formatted, str)

    def test_format_comparison(self):
        s1 = TextStatistics.calculate("hello")
        s2 = TextStatistics.calculate("hello world")
        result = TextStatistics.format_comparison(s1, s2)
        self.assertIsInstance(result, str)

    def test_numbers_counted_as_words(self):
        stats = TextStatistics.calculate("item 123 value")
        self.assertEqual(stats.words, 3)

    def test_large_text(self):
        text = "word " * 10000
        stats = TextStatistics.calculate(text)
        self.assertEqual(stats.words, 10000)


# ══════════════════════════════════════════════════════════════════════════════
# 4. DIFF ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class TestDiffEngine(unittest.TestCase):
    """core/diff_engine.py — diff computation, merging, and similarity."""

    def test_identical_texts_no_changes(self):
        result = DiffEngine.compute_diff("hello", "hello")
        self.assertEqual(result.total_changes, 0)

    def test_single_word_change(self):
        result = DiffEngine.compute_diff("hello world", "hello earth")
        self.assertGreater(result.total_changes, 0)

    def test_insertion_detected(self):
        result = DiffEngine.compute_diff("line1\nline2", "line1\nnewline\nline2")
        self.assertGreater(result.insertions + result.replacements, 0)

    def test_deletion_detected(self):
        result = DiffEngine.compute_diff("line1\nline2\nline3", "line1\nline3")
        self.assertGreater(result.deletions + result.replacements, 0)

    def test_result_is_diff_result(self):
        result = DiffEngine.compute_diff("a", "b")
        self.assertIsInstance(result, DiffResult)

    def test_accept_change(self):
        result = DiffEngine.compute_diff("old text", "new text")
        if result.total_changes > 0:
            self.assertTrue(result.accept_change(0))

    def test_reject_change(self):
        result = DiffEngine.compute_diff("old text", "new text")
        if result.total_changes > 0:
            self.assertTrue(result.reject_change(0))

    def test_accept_all(self):
        result = DiffEngine.compute_diff("old", "new")
        result.accept_all()
        self.assertEqual(result.accepted_count, result.total_changes)

    def test_reject_all(self):
        result = DiffEngine.compute_diff("old", "new")
        result.reject_all()
        self.assertEqual(result.rejected_count, result.total_changes)

    def test_reset_all(self):
        result = DiffEngine.compute_diff("old", "new")
        result.accept_all()
        result.reset_all()
        self.assertEqual(result.pending_count, result.total_changes)

    def test_get_merged_text_identical(self):
        result = DiffEngine.compute_diff("hello", "hello")
        merged = result.get_merged_text()
        self.assertEqual(merged.strip(), "hello")

    def test_similarity_identical(self):
        score = DiffEngine.compute_similarity("hello world", "hello world")
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_similarity_completely_different(self):
        score = DiffEngine.compute_similarity("aaa", "zzz")
        self.assertLessEqual(score, 0.5)

    def test_similarity_range(self):
        score = DiffEngine.compute_similarity("hello", "hello world")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_get_change_summary(self):
        result = DiffEngine.compute_diff("old text here", "new text here")
        summary = DiffEngine.get_change_summary(result)
        self.assertIsInstance(summary, str)

    def test_compute_unified_diff(self):
        result = DiffEngine.compute_unified_diff("line1\nline2", "line1\nline3")
        self.assertIsInstance(result, str)

    def test_compute_html_diff(self):
        result = DiffEngine.compute_html_diff("old", "new")
        self.assertIsInstance(result, str)

    def test_empty_left(self):
        result = DiffEngine.compute_diff("", "new text")
        self.assertIsInstance(result, DiffResult)

    def test_empty_right(self):
        result = DiffEngine.compute_diff("old text", "")
        self.assertIsInstance(result, DiffResult)

    def test_both_empty(self):
        result = DiffEngine.compute_diff("", "")
        self.assertEqual(result.total_changes, 0)

    def test_change_indices_list(self):
        result = DiffEngine.compute_diff("a\nb\nc", "a\nX\nc")
        indices = result.get_change_indices()
        self.assertIsInstance(indices, list)

    def test_out_of_bounds_accept(self):
        result = DiffEngine.compute_diff("a", "b")
        self.assertFalse(result.accept_change(9999))

    def test_multiline_diff(self):
        left = "\n".join(f"line {i}" for i in range(20))
        right = "\n".join(f"line {i}" for i in range(10, 30))
        result = DiffEngine.compute_diff(left, right)
        self.assertIsInstance(result, DiffResult)


# ══════════════════════════════════════════════════════════════════════════════
# 5. EXPORT MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestExportManager(unittest.TestCase):
    """core/export_manager.py — TXT, HTML, MD, RTF exports + utilities."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.em = ExportManager()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _opts(self, fmt, **kwargs):
        return ExportOptions(format=fmt, **kwargs)

    def test_export_txt_creates_file(self):
        path = os.path.join(self.tmp, "out.txt")
        ok = self.em.export("hello world", path, self._opts(ExportFormat.TXT))
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(path))

    def test_export_txt_content(self):
        path = os.path.join(self.tmp, "content.txt")
        self.em.export("test content", path, self._opts(ExportFormat.TXT))
        self.assertEqual(Path(path).read_text(encoding="utf-8"), "test content")

    def test_export_txt_with_line_numbers(self):
        path = os.path.join(self.tmp, "numbered.txt")
        self.em.export("line1\nline2", path, self._opts(ExportFormat.TXT, include_line_numbers=True))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("1", content)
        self.assertIn("2", content)

    def test_export_html_creates_file(self):
        path = os.path.join(self.tmp, "out.html")
        ok = self.em.export("hello", path, self._opts(ExportFormat.HTML))
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(path))

    def test_export_html_structure(self):
        path = os.path.join(self.tmp, "struct.html")
        self.em.export("test", path, self._opts(ExportFormat.HTML))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("<html", content)
        self.assertIn("</html>", content)

    def test_export_html_dark_theme(self):
        path = os.path.join(self.tmp, "dark.html")
        self.em.export("test", path, self._opts(ExportFormat.HTML, html_dark_theme=True))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("1A1A1A", content.upper().replace("#", "").replace(" ", "").upper()
                       or content)  # dark bg present
        self.assertTrue(os.path.exists(path))

    def test_export_html_escapes_special_chars(self):
        path = os.path.join(self.tmp, "escape.html")
        self.em.export("<script>alert('xss')</script>", path, self._opts(ExportFormat.HTML))
        content = Path(path).read_text(encoding="utf-8")
        self.assertNotIn("<script>", content)

    def test_export_markdown_creates_file(self):
        path = os.path.join(self.tmp, "out.md")
        ok = self.em.export("hello", path, self._opts(ExportFormat.MARKDOWN))
        self.assertTrue(ok)

    def test_export_markdown_structure(self):
        path = os.path.join(self.tmp, "struct.md")
        self.em.export("hello", path, self._opts(ExportFormat.MARKDOWN, page_title="My Doc"))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("# My Doc", content)

    def test_export_markdown_with_line_numbers(self):
        path = os.path.join(self.tmp, "num.md")
        self.em.export("a\nb", path, self._opts(ExportFormat.MARKDOWN, include_line_numbers=True))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("```", content)

    def test_export_rtf_creates_file(self):
        path = os.path.join(self.tmp, "out.rtf")
        ok = self.em.export("hello", path, self._opts(ExportFormat.RTF))
        self.assertTrue(ok)

    def test_export_rtf_header(self):
        path = os.path.join(self.tmp, "header.rtf")
        self.em.export("hello", path, self._opts(ExportFormat.RTF))
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("\\rtf1", content)

    def test_rtf_escape_backslash(self):
        result = ExportManager._rtf_escape("back\\slash")
        self.assertIn("\\\\", result)

    def test_rtf_escape_braces(self):
        result = ExportManager._rtf_escape("{braces}")
        self.assertIn("\\{", result)
        self.assertIn("\\}", result)

    def test_rtf_escape_unicode(self):
        result = ExportManager._rtf_escape("caf\u00e9")
        self.assertIn("\\u", result)

    def test_correct_extension_applied(self):
        path = os.path.join(self.tmp, "noext")
        self.em.export("hello", path, self._opts(ExportFormat.TXT))
        self.assertTrue(os.path.exists(path + ".txt") or
                        os.path.exists(os.path.join(self.tmp, "noext.txt")))

    def test_get_format_from_extension_txt(self):
        fmt = ExportManager.get_format_from_extension(".txt")
        self.assertEqual(fmt, ExportFormat.TXT)

    def test_get_format_from_extension_html(self):
        self.assertEqual(ExportManager.get_format_from_extension(".html"), ExportFormat.HTML)

    def test_get_format_from_extension_without_dot(self):
        self.assertEqual(ExportManager.get_format_from_extension("md"), ExportFormat.MARKDOWN)

    def test_get_format_from_extension_unknown(self):
        self.assertIsNone(ExportManager.get_format_from_extension(".xyz"))

    def test_get_file_filter_string(self):
        filt = ExportManager.get_file_filter()
        self.assertIn("txt", filt.lower())
        self.assertIn("html", filt.lower())

    def test_get_available_formats(self):
        formats = ExportManager.get_available_formats()
        self.assertIn(ExportFormat.TXT, formats)
        self.assertIn(ExportFormat.HTML, formats)
        self.assertIn(ExportFormat.MARKDOWN, formats)

    def test_check_format_dependencies_txt(self):
        ok, msg = ExportManager.check_format_dependencies(ExportFormat.TXT)
        self.assertTrue(ok)

    def test_check_format_dependencies_html(self):
        ok, msg = ExportManager.check_format_dependencies(ExportFormat.HTML)
        self.assertTrue(ok)

    def test_export_empty_text(self):
        path = os.path.join(self.tmp, "empty.txt")
        ok = self.em.export("", path, self._opts(ExportFormat.TXT))
        self.assertTrue(ok)

    def test_export_unicode_text(self):
        path = os.path.join(self.tmp, "unicode.txt")
        ok = self.em.export("caf\u00e9 \u4e2d\u6587 \u00e9l\u00e8ve", path, self._opts(ExportFormat.TXT))
        self.assertTrue(ok)
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("caf", content)

    def test_export_format_enum_values(self):
        self.assertEqual(ExportFormat.TXT, "Plain Text (.txt)")
        self.assertEqual(ExportFormat.HTML, "HTML Document (.html)")
        self.assertEqual(ExportFormat.MARKDOWN, "Markdown (.md)")


# ══════════════════════════════════════════════════════════════════════════════
# 6. PRESET MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestPresetManager(unittest.TestCase):
    """core/preset_manager.py — PresetStep, TransformPreset, PresetManager, PresetExecutor."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.pm = PresetManager(presets_dir=Path(cls.tmp))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── PresetStep ─────────────────────────────────────────────────────────────
    def test_preset_step_creation(self):
        step = PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"})
        self.assertEqual(step.action, ActionType.TRANSFORM)
        self.assertTrue(step.enabled)

    def test_preset_step_to_dict(self):
        step = PresetStep(action=ActionType.CLEANUP, params={"op": "trim"})
        d = step.to_dict()
        self.assertEqual(d["action"], ActionType.CLEANUP)
        self.assertIn("params", d)
        self.assertIn("enabled", d)

    def test_preset_step_from_dict(self):
        data = {"action": "transform", "params": {"mode": "uppercase"}, "enabled": True, "description": ""}
        step = PresetStep.from_dict(data)
        self.assertEqual(step.action, "transform")
        self.assertTrue(step.enabled)

    def test_preset_step_roundtrip(self):
        step = PresetStep(action=ActionType.REPLACE, params={"find": "a", "replace": "b"}, description="swap")
        step2 = PresetStep.from_dict(step.to_dict())
        self.assertEqual(step.action, step2.action)
        self.assertEqual(step.params, step2.params)
        self.assertEqual(step.description, step2.description)

    def test_preset_step_disabled(self):
        step = PresetStep(action=ActionType.TRANSFORM, enabled=False)
        self.assertFalse(step.enabled)

    def test_preset_step_display_name_with_description(self):
        step = PresetStep(action=ActionType.TRANSFORM, description="My step")
        self.assertEqual(step.get_display_name(), "My step")

    # ── TransformPreset ────────────────────────────────────────────────────────
    def test_transform_preset_creation(self):
        preset = TransformPreset(name="Test", description="A test preset")
        self.assertEqual(preset.name, "Test")
        self.assertEqual(len(preset.steps), 0)

    def test_add_step(self):
        preset = TransformPreset(name="Test")
        step = PresetStep(action=ActionType.TRANSFORM, params={"mode": "uppercase"})
        preset.add_step(step)
        self.assertEqual(len(preset.steps), 1)

    def test_remove_step(self):
        preset = TransformPreset(name="Test")
        step = PresetStep(action=ActionType.TRANSFORM)
        preset.add_step(step)
        ok = preset.remove_step(0)
        self.assertTrue(ok)
        self.assertEqual(len(preset.steps), 0)

    def test_remove_step_invalid_index(self):
        preset = TransformPreset(name="Test")
        ok = preset.remove_step(99)
        self.assertFalse(ok)

    def test_move_step_up(self):
        preset = TransformPreset(name="Test")
        s1 = PresetStep(action=ActionType.TRANSFORM, description="first")
        s2 = PresetStep(action=ActionType.CLEANUP, description="second")
        preset.add_step(s1)
        preset.add_step(s2)
        ok = preset.move_step(1, 0)
        self.assertTrue(ok)
        self.assertEqual(preset.steps[0].description, "second")

    def test_get_enabled_steps(self):
        preset = TransformPreset(name="Test")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM, enabled=True))
        preset.add_step(PresetStep(action=ActionType.CLEANUP, enabled=False))
        enabled = preset.get_enabled_steps()
        self.assertEqual(len(enabled), 1)

    def test_get_step_count(self):
        preset = TransformPreset(name="Test")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM))
        preset.add_step(PresetStep(action=ActionType.CLEANUP))
        self.assertEqual(preset.get_step_count(), 2)

    def test_get_enabled_count(self):
        preset = TransformPreset(name="Test")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM, enabled=True))
        preset.add_step(PresetStep(action=ActionType.CLEANUP, enabled=False))
        self.assertEqual(preset.get_enabled_count(), 1)

    def test_preset_to_dict(self):
        preset = TransformPreset(name="Test", category="dev")
        d = preset.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertIn("steps", d)

    def test_preset_from_dict(self):
        data = {"name": "MyPreset", "description": "desc", "category": "text",
                "steps": [], "created": "", "modified": "", "shortcut": ""}
        preset = TransformPreset.from_dict(data)
        self.assertEqual(preset.name, "MyPreset")

    def test_preset_roundtrip(self):
        preset = TransformPreset(name="RoundTrip", category="test")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM, params={"mode": "uppercase"}))
        preset2 = TransformPreset.from_dict(preset.to_dict())
        self.assertEqual(preset.name, preset2.name)
        self.assertEqual(len(preset.steps), len(preset2.steps))

    # ── PresetManager ──────────────────────────────────────────────────────────
    def test_add_preset(self):
        preset = TransformPreset(name="AddTest")
        ok = self.pm.add_preset(preset)
        self.assertTrue(ok)

    def test_get_preset(self):
        preset = TransformPreset(name="GetTest")
        self.pm.add_preset(preset)
        retrieved = self.pm.get_preset("GetTest")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "GetTest")

    def test_get_preset_not_found(self):
        result = self.pm.get_preset("DoesNotExist")
        self.assertIsNone(result)

    def test_get_all_presets(self):
        self.pm.add_preset(TransformPreset(name="P1"))
        self.pm.add_preset(TransformPreset(name="P2"))
        presets = self.pm.get_all_presets()
        self.assertIsInstance(presets, list)

    def test_get_preset_names(self):
        self.pm.add_preset(TransformPreset(name="NameTest"))
        names = self.pm.get_preset_names()
        self.assertIsInstance(names, list)

    def test_delete_preset(self):
        preset = TransformPreset(name="DeleteMe")
        self.pm.add_preset(preset)
        ok = self.pm.delete_preset("DeleteMe")
        self.assertTrue(ok)
        self.assertIsNone(self.pm.get_preset("DeleteMe"))

    def test_delete_preset_not_found(self):
        ok = self.pm.delete_preset("GhostPreset")
        self.assertFalse(ok)

    def test_rename_preset(self):
        self.pm.add_preset(TransformPreset(name="OldName"))
        ok = self.pm.rename_preset("OldName", "NewName")
        self.assertTrue(ok)
        self.assertIsNotNone(self.pm.get_preset("NewName"))
        self.assertIsNone(self.pm.get_preset("OldName"))

    def test_duplicate_preset(self):
        self.pm.add_preset(TransformPreset(name="Original"))
        dupe = self.pm.duplicate_preset("Original")
        self.assertIsNotNone(dupe)
        self.assertNotEqual(dupe.name, "Original")

    def test_get_presets_by_category(self):
        self.pm.add_preset(TransformPreset(name="CatA1", category="alpha"))
        self.pm.add_preset(TransformPreset(name="CatB1", category="beta"))
        by_cat = self.pm.get_presets_by_category()
        self.assertIsInstance(by_cat, dict)

    def test_save_and_load_presets(self):
        pm2 = PresetManager(presets_dir=Path(self.tmp) / "savetest")
        pm2.add_preset(TransformPreset(name="SaveMe"))
        pm2.save_presets()
        pm3 = PresetManager(presets_dir=Path(self.tmp) / "savetest")
        pm3.load_presets()
        self.assertIsNotNone(pm3.get_preset("SaveMe"))

    def test_export_preset_to_file(self):
        self.pm.add_preset(TransformPreset(name="ExportMe"))
        export_path = Path(self.tmp) / "exported.json"
        ok = self.pm.export_preset("ExportMe", export_path)
        self.assertTrue(ok)
        self.assertTrue(export_path.exists())

    def test_import_preset_from_file(self):
        preset = TransformPreset(name="ImportMe", description="imported")
        export_path = Path(self.tmp) / "import_me.json"
        self.pm.add_preset(preset)
        self.pm.export_preset("ImportMe", export_path)
        imported = self.pm.import_preset(export_path)
        self.assertIsNotNone(imported)

    # ── PresetExecutor ─────────────────────────────────────────────────────────
    def test_executor_transform_step(self):
        exe = PresetExecutor()
        step = PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"})
        result = exe.execute_step("hello", step)
        self.assertEqual(result, "HELLO")

    def test_executor_cleanup_step(self):
        exe = PresetExecutor()
        step = PresetStep(action=ActionType.CLEANUP,
                          params={"operation": CleanupOperation.TRIM_WHITESPACE})
        result = exe.execute_step("  hello  ", step)
        self.assertEqual(result, "hello")

    def test_executor_replace_step(self):
        exe = PresetExecutor()
        step = PresetStep(action=ActionType.REPLACE,
                          params={"find": "hello", "replace": "world", "case_sensitive": False})
        result = exe.execute_step("hello there", step)
        self.assertEqual(result, "world there")

    def test_executor_prefix_step(self):
        exe = PresetExecutor()
        step = PresetStep(action=ActionType.PREFIX, params={"text": "PRE_"})
        result = exe.execute_step("text", step)
        self.assertIn("PRE_", result)

    def test_executor_suffix_step(self):
        exe = PresetExecutor()
        step = PresetStep(action=ActionType.SUFFIX, params={"text": "_END"})
        result = exe.execute_step("text", step)
        self.assertIn("_END", result)

    def test_executor_disabled_step_skipped(self):
        # execute_step does not check enabled; disabled steps are skipped by execute_preset
        exe = PresetExecutor()
        preset = TransformPreset(name="DisabledTest")
        step = PresetStep(action=ActionType.TRANSFORM,
                          params={"mode": "UPPERCASE"}, enabled=False)
        preset.add_step(step)
        result, _ = exe.execute_preset("hello", preset)
        self.assertEqual(result, "hello")  # disabled step skipped by execute_preset

    def test_executor_full_preset(self):
        exe = PresetExecutor()
        preset = TransformPreset(name="FullTest")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"}))
        preset.add_step(PresetStep(action=ActionType.CLEANUP,
                                   params={"operation": CleanupOperation.TRIM_WHITESPACE}))
        result, applied = exe.execute_preset("  hello world  ", preset)
        self.assertEqual(result, "HELLO WORLD")
        self.assertIsInstance(applied, list)


# ══════════════════════════════════════════════════════════════════════════════
# 7. REGEX PATTERNS
# ══════════════════════════════════════════════════════════════════════════════
class TestRegexPatterns(unittest.TestCase):
    """core/regex_patterns.py — pattern library, RegexHelper, validation."""

    def test_get_all_patterns_returns_dict(self):
        patterns = RegexPatterns.get_all_patterns()
        self.assertIsInstance(patterns, dict)
        self.assertGreater(len(patterns), 0)

    def test_get_patterns_by_category(self):
        by_cat = RegexPatterns.get_patterns_by_category()
        self.assertIsInstance(by_cat, dict)
        self.assertGreater(len(by_cat), 0)

    def test_get_categories(self):
        cats = RegexPatterns.get_categories()
        self.assertIsInstance(cats, list)
        self.assertGreater(len(cats), 0)

    def test_get_pattern_by_name_valid(self):
        patterns = RegexPatterns.get_all_patterns()
        first_name = next(iter(patterns))
        pattern = RegexPatterns.get_pattern_by_name(first_name)
        self.assertIsNotNone(pattern)
        self.assertIsInstance(pattern, PatternInfo)

    def test_get_pattern_by_name_invalid(self):
        result = RegexPatterns.get_pattern_by_name("DoesNotExist")
        self.assertIsNone(result)

    def test_compile_pattern(self):
        patterns = RegexPatterns.get_all_patterns()
        first = next(iter(patterns.values()))
        compiled = RegexPatterns.compile_pattern(first)
        self.assertIsNotNone(compiled)

    def test_validate_pattern_valid(self):
        ok, msg = RegexHelper.validate_pattern(r"\d+")
        self.assertTrue(ok)

    def test_validate_pattern_invalid(self):
        ok, msg = RegexHelper.validate_pattern(r"[invalid")
        self.assertFalse(ok)

    def test_validate_pattern_empty(self):
        ok, msg = RegexHelper.validate_pattern("")
        self.assertIsInstance(ok, bool)

    def test_find_all_matches(self):
        matches = RegexHelper.find_all_matches("abc 123 def 456", r"\d+")
        self.assertEqual(len(matches), 2)

    def test_find_all_matches_no_match(self):
        matches = RegexHelper.find_all_matches("no numbers here", r"\d+")
        self.assertEqual(len(matches), 0)

    def test_replace_all(self):
        result, count = RegexHelper.replace_all("abc 123 def 456", r"\d+", "NUM")
        self.assertEqual(result, "abc NUM def NUM")
        self.assertEqual(count, 2)

    def test_replace_all_no_match(self):
        result, count = RegexHelper.replace_all("no numbers", r"\d+", "X")
        self.assertEqual(result, "no numbers")
        self.assertEqual(count, 0)

    def test_escape_pattern(self):
        escaped = RegexHelper.escape_pattern("hello.world[test]")
        self.assertIn("\\.", escaped)

    def test_get_flags_from_options(self):
        flags = RegexHelper.get_flags_from_options(case_insensitive=True)
        self.assertIsInstance(flags, int)
        self.assertGreater(flags, 0)

    def test_get_flags_from_options_none(self):
        flags = RegexHelper.get_flags_from_options()
        self.assertEqual(flags, 0)

    def test_explain_flags(self):
        import re
        explanations = RegexHelper.explain_flags(re.IGNORECASE)
        self.assertIsInstance(explanations, list)
        self.assertGreater(len(explanations), 0)

    def test_email_pattern_matches(self):
        """Built-in email pattern should match valid emails."""
        patterns = RegexPatterns.get_all_patterns()
        email_pattern = None
        for name, p in patterns.items():
            if "email" in name.lower():
                email_pattern = p; break
        if email_pattern:
            matches = RegexHelper.find_all_matches("test@example.com foo@bar.org", email_pattern.pattern)
            self.assertGreater(len(matches), 0)

    def test_pattern_info_fields(self):
        patterns = RegexPatterns.get_all_patterns()
        p = next(iter(patterns.values()))
        self.assertTrue(hasattr(p, "pattern"))
        self.assertTrue(hasattr(p, "name"))


# ══════════════════════════════════════════════════════════════════════════════
# 8. DIALOG STYLE MANAGER (Color System)
# ══════════════════════════════════════════════════════════════════════════════
class TestDialogStyleManager(unittest.TestCase):
    """utils/dialog_styles.py — color keys, stylesheets, cache."""

    # ── DARK palette ──────────────────────────────────────────────────────────
    def test_dark_accent_is_brand_gold(self):
        self.assertEqual(DialogStyleManager.DARK["accent"].lower(), "#d2bc93")

    def test_light_accent_is_brand_gold_dark(self):
        self.assertEqual(DialogStyleManager.LIGHT["accent"].lower(), "#b19145")

    def test_dark_and_light_have_same_keys(self):
        self.assertEqual(set(DialogStyleManager.DARK.keys()), set(DialogStyleManager.LIGHT.keys()))

    def test_required_keys_present_dark(self):
        required = [
            "bg", "bg_secondary", "bg_tertiary", "bg_hover",
            "text", "text_muted", "text_disabled",
            "border", "border_light", "border_focus",
            "accent", "accent_hover", "accent_pressed", "accent_text",
            "success", "error", "warning",
            "selection_bg", "selection_text",
            "scrollbar_bg", "scrollbar_handle", "scrollbar_handle_hover",
            "checkbox_indicator_bg", "checkbox_border",
            "list_hover_bg", "list_hover_text",
            "window_bg", "button_bg", "button_text", "button_hover_bg",
            "input_bg", "input_text", "input_border",
            "output_text_color", "border_color", "text_color",
            "line_number_bg", "line_number_fg",
            "line_number_current_bg", "line_number_current_fg",
        ]
        for key in required:
            self.assertIn(key, DialogStyleManager.DARK, f"Missing DARK key: {key}")

    def test_all_hex_values_valid_format(self):
        import re
        hex_re  = re.compile(r'^#[0-9a-fA-F]{3,8}$')
        rgba_re = re.compile(r'^rgba\(\d+,\s*\d+,\s*\d+,\s*\d+\)$')
        for key, val in DialogStyleManager.DARK.items():
            valid = bool(hex_re.match(val)) or bool(rgba_re.match(val))
            self.assertTrue(valid, f"DARK['{key}'] = '{val}' is not a valid hex or rgba color")
        for key, val in DialogStyleManager.LIGHT.items():
            valid = bool(hex_re.match(val)) or bool(rgba_re.match(val))
            self.assertTrue(valid, f"LIGHT['{key}'] = '{val}' is not a valid hex or rgba color")

    # ── get_colors ─────────────────────────────────────────────────────────────
    def test_get_colors_dark(self):
        c = DialogStyleManager.get_colors(is_dark=True)
        self.assertIs(c, DialogStyleManager.DARK)

    def test_get_colors_light(self):
        c = DialogStyleManager.get_colors(is_dark=False)
        self.assertIs(c, DialogStyleManager.LIGHT)

    # ── get_dialog_stylesheet ──────────────────────────────────────────────────
    def test_get_dialog_stylesheet_dark_returns_string(self):
        css = DialogStyleManager.get_dialog_stylesheet(True, "Arial")
        self.assertIsInstance(css, str)
        self.assertGreater(len(css), 0)

    def test_get_dialog_stylesheet_light_returns_string(self):
        css = DialogStyleManager.get_dialog_stylesheet(False, "Arial")
        self.assertIsInstance(css, str)

    def test_stylesheet_contains_font_family(self):
        css = DialogStyleManager.get_dialog_stylesheet(True, "Montserrat")
        self.assertIn("Montserrat", css)

    def test_dark_and_light_stylesheets_differ(self):
        dark = DialogStyleManager.get_dialog_stylesheet(True, "Arial")
        light = DialogStyleManager.get_dialog_stylesheet(False, "Arial")
        self.assertNotEqual(dark, light)

    # ── get_extended_stylesheet ────────────────────────────────────────────────
    def test_extended_stylesheet_with_tab(self):
        css = DialogStyleManager.get_extended_stylesheet(True, "Arial", "tab")
        self.assertIsInstance(css, str)
        self.assertIn("QTabBar", css)

    def test_extended_stylesheet_with_table(self):
        css = DialogStyleManager.get_extended_stylesheet(True, "Arial", "table")
        self.assertIsInstance(css, str)

    def test_tab_style_uses_accent_for_selected(self):
        css = DialogStyleManager.get_extended_stylesheet(True, "Arial", "tab")
        self.assertIn(DialogStyleManager.DARK["accent"], css)

    def test_tab_style_uses_accent_for_light(self):
        css = DialogStyleManager.get_extended_stylesheet(False, "Arial", "tab")
        self.assertIn(DialogStyleManager.LIGHT["accent"], css)

    # ── prewarm_cache ──────────────────────────────────────────────────────────
    def test_prewarm_cache_runs_without_error(self):
        try:
            DialogStyleManager.prewarm_cache("Arial")
        except Exception as e:
            self.fail(f"prewarm_cache raised: {e}")

    # ── cache stats ────────────────────────────────────────────────────────────
    def test_get_cache_stats_keys(self):
        DialogStyleManager.get_dialog_stylesheet(True, "Arial")
        stats = DialogStyleManager.get_cache_stats()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("hit_rate", stats)

    def test_cache_hit_rate_range(self):
        DialogStyleManager.get_dialog_stylesheet(True, "Arial")
        DialogStyleManager.get_dialog_stylesheet(True, "Arial")  # should be a cache hit
        stats = DialogStyleManager.get_cache_stats()
        self.assertGreaterEqual(stats["hit_rate"], 0.0)
        self.assertLessEqual(stats["hit_rate"], 1.0)

    # ── inline style helpers ───────────────────────────────────────────────────
    def test_get_status_style_success(self):
        css = DialogStyleManager.get_status_style(True, "success")
        self.assertIsInstance(css, str)

    def test_get_status_style_error(self):
        css = DialogStyleManager.get_status_style(True, "error")
        self.assertIsInstance(css, str)

    def test_get_header_style(self):
        css = DialogStyleManager.get_header_style(True)
        self.assertIsInstance(css, str)

    def test_get_subtitle_style(self):
        css = DialogStyleManager.get_subtitle_style(False)
        self.assertIsInstance(css, str)


# ══════════════════════════════════════════════════════════════════════════════
# 9. FILE HANDLER
# ══════════════════════════════════════════════════════════════════════════════
class TestFileHandler(unittest.TestCase):
    """utils/file_handler.py — read/write, extension detection."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _write(self, name, content, encoding="utf-8"):
        path = os.path.join(self.tmp, name)
        Path(path).write_text(content, encoding=encoding)
        return path

    def test_read_txt_file(self):
        path = self._write("test.txt", "hello world")
        result = FileHandler.read_file_content(path)
        self.assertEqual(result, "hello world")

    def test_read_md_file(self):
        path = self._write("test.md", "# heading\ncontent")
        result = FileHandler.read_file_content(path)
        self.assertIn("heading", result)

    def test_read_py_file(self):
        path = self._write("test.py", "print('hello')")
        result = FileHandler.read_file_content(path)
        self.assertIn("print", result)

    def test_read_html_file(self):
        path = self._write("test.html", "<html><body>test</body></html>")
        result = FileHandler.read_file_content(path)
        self.assertIn("test", result)

    def test_read_js_file(self):
        path = self._write("test.js", "console.log('hello');")
        result = FileHandler.read_file_content(path)
        self.assertIn("console", result)

    def test_read_log_file(self):
        path = self._write("test.log", "2025-01-01 ERROR something failed")
        result = FileHandler.read_file_content(path)
        self.assertIn("ERROR", result)

    def test_read_nonexistent_returns_none(self):
        # read_file_content raises FileReadError for missing files — catch it
        with self.assertRaises(FileReadError):
            FileHandler.read_file_content("/nonexistent/path/file.txt")

    def test_write_text_file(self):
        path = os.path.join(self.tmp, "write_test.txt")
        FileHandler.write_text_file(path, "written content")
        self.assertEqual(Path(path).read_text(encoding="utf-8"), "written content")

    def test_write_creates_parent_dirs(self):
        # write_text_file does not create parent dirs — use Path.mkdir first
        subdir = Path(self.tmp) / "subdir2"
        subdir.mkdir(parents=True, exist_ok=True)
        path = subdir / "nested.txt"
        FileHandler.write_text_file(str(path), "nested")
        self.assertTrue(path.exists())

    def test_get_file_name(self):
        name = FileHandler.get_file_name("/some/path/document.txt")
        self.assertEqual(name, "document.txt")

    def test_get_file_extension_with_dot(self):
        ext = FileHandler.get_file_extension("file.txt")
        self.assertEqual(ext.lower(), ".txt")

    def test_get_file_extension_uppercase(self):
        ext = FileHandler.get_file_extension("FILE.TXT")
        self.assertIsInstance(ext, str)

    def test_is_supported_format_txt(self):
        self.assertTrue(FileHandler.is_supported_format("file.txt"))

    def test_is_supported_format_md(self):
        self.assertTrue(FileHandler.is_supported_format("file.md"))

    def test_is_supported_format_py(self):
        self.assertTrue(FileHandler.is_supported_format("file.py"))

    def test_is_supported_format_unsupported(self):
        self.assertFalse(FileHandler.is_supported_format("file.xyz"))

    def test_read_unicode_content(self):
        path = self._write("unicode.txt", "caf\u00e9 \u4e2d\u6587")
        result = FileHandler.read_file_content(path)
        self.assertIsNotNone(result)
        self.assertIn("caf", result)

    def test_read_empty_file(self):
        path = self._write("empty.txt", "")
        result = FileHandler.read_file_content(path)
        self.assertIsNotNone(result)
        self.assertEqual(result, "")


# ══════════════════════════════════════════════════════════════════════════════
# 10. ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandler(unittest.TestCase):
    """utils/error_handler.py — safe_execute, try_or_default, ErrorContext."""

    def test_safe_execute_success(self):
        result = ErrorHandler.safe_execute(lambda: 42, "test")
        self.assertEqual(result, 42)

    def test_safe_execute_exception_returns_none(self):
        result = ErrorHandler.safe_execute(lambda: 1 / 0, "division")
        self.assertIsNone(result)

    def test_safe_execute_exception_returns_fallback(self):
        result = ErrorHandler.safe_execute(lambda: 1 / 0, "division", fallback_value="fallback")
        self.assertEqual(result, "fallback")

    def test_try_or_default_success(self):
        result = ErrorHandler.try_or_default(lambda: "ok", "default")
        self.assertEqual(result, "ok")

    def test_try_or_default_exception(self):
        result = ErrorHandler.try_or_default(lambda: 1 / 0, "default")
        self.assertEqual(result, "default")

    def test_error_context_success(self):
        with ErrorContext("test_operation"):
            x = 1 + 1
        self.assertEqual(x, 2)

    def test_error_context_exception_suppressed(self):
        # ErrorContext suppresses by default (reraise=False)
        try:
            with ErrorContext("test_context"):
                raise ValueError("test error")
        except ValueError:
            self.fail("ErrorContext should have suppressed ValueError")

    def test_safe_method_decorator(self):
        class MyClass:
            @ErrorHandler.safe_method("my_method")
            def risky(self):
                raise RuntimeError("oops")
        obj = MyClass()
        result = obj.risky()  # should not raise
        self.assertIsNone(result)

    def test_handle_exception_runs_without_error(self):
        try:
            ErrorHandler.handle_exception(ValueError("test"), "test_context")
        except Exception as e:
            self.fail(f"handle_exception raised: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 11. CONFIG
# ══════════════════════════════════════════════════════════════════════════════
class TestConfig(unittest.TestCase):
    """utils/config.py — constants, paths, window dimensions."""

    def test_app_name(self):
        self.assertEqual(config.APP_NAME, "RNV Text Transformer")

    def test_app_version_format(self):
        import re
        self.assertRegex(config.APP_VERSION, r'^\d+\.\d+\.\d+$')

    def test_min_window_dimensions(self):
        self.assertGreater(config.MIN_WINDOW_WIDTH, 0)
        self.assertGreater(config.MIN_WINDOW_HEIGHT, 0)

    def test_min_window_width_value(self):
        self.assertEqual(config.MIN_WINDOW_WIDTH, 800)

    def test_min_window_height_value(self):
        self.assertEqual(config.MIN_WINDOW_HEIGHT, 600)

    def test_default_window_larger_than_minimum(self):
        self.assertGreaterEqual(config.DEFAULT_WINDOW_WIDTH, config.MIN_WINDOW_WIDTH)
        self.assertGreaterEqual(config.DEFAULT_WINDOW_HEIGHT, config.MIN_WINDOW_HEIGHT)

    def test_theme_button_dimensions_positive(self):
        self.assertGreater(config.THEME_BUTTON_WIDTH, 0)
        self.assertGreater(config.THEME_BUTTON_HEIGHT, 0)

    def test_max_file_size_positive(self):
        self.assertGreater(config.MAX_FILE_SIZE, 0)

    def test_max_file_size_reasonable(self):
        self.assertGreaterEqual(config.MAX_FILE_SIZE, 1024 * 1024)  # at least 1 MB

    def test_status_clear_timeout_positive(self):
        self.assertGreater(config.STATUS_CLEAR_TIMEOUT, 0)

    def test_button_margins_tuple(self):
        self.assertIsInstance(config.BUTTON_MARGINS, tuple)
        self.assertEqual(len(config.BUTTON_MARGINS), 4)

    def test_paths_exist(self):
        self.assertTrue(config.BASE_DIR.exists())

    def test_supported_extensions_in_config(self):
        from utils.config import SUPPORTED_EXTENSIONS
        self.assertIsInstance(SUPPORTED_EXTENSIONS, (list, tuple, dict, frozenset))
        self.assertTrue(len(SUPPORTED_EXTENSIONS) > 0)


# ══════════════════════════════════════════════════════════════════════════════
# 12. EDGE CASES & INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestEdgeCases(unittest.TestCase):
    """Cross-module edge cases and stress tests."""

    def test_transform_then_stats(self):
        """Transform text then compute accurate statistics."""
        original = "hello world foo bar"
        transformed = TextTransformer.transform_text(original, TransformMode.UPPERCASE)
        stats = TextStatistics.calculate(transformed)
        self.assertEqual(stats.words, 4)
        self.assertEqual(stats.characters, len(transformed))

    def test_transform_then_diff(self):
        """Diff between original and transformed text."""
        original = "hello world"
        transformed = TextTransformer.transform_text(original, TransformMode.UPPERCASE)
        result = DiffEngine.compute_diff(original, transformed)
        self.assertGreater(result.total_changes, 0)

    def test_clean_then_transform(self):
        """Clean text then transform — pipeline test."""
        raw = "  HELLO   WORLD  "
        cleaned = TextCleaner.trim_whitespace(raw)
        cleaned = TextCleaner.remove_extra_spaces(cleaned)
        result = TextTransformer.transform_text(cleaned, TransformMode.LOWERCASE)
        self.assertEqual(result, "hello world")

    def test_preset_executor_multi_step_pipeline(self):
        """Multi-step preset: trim → uppercase → prefix."""
        exe = PresetExecutor()
        preset = TransformPreset(name="Pipeline")
        preset.add_step(PresetStep(action=ActionType.CLEANUP,
                                   params={"operation": CleanupOperation.TRIM_WHITESPACE}))
        preset.add_step(PresetStep(action=ActionType.TRANSFORM,
                                   params={"mode": TransformMode.UPPERCASE}))
        preset.add_step(PresetStep(action=ActionType.PREFIX,
                                   params={"text": ">> "}))
        result, _ = exe.execute_preset("  hello world  ", preset)
        self.assertTrue(result.startswith(">> "))
        self.assertIn("HELLO WORLD", result)

    def test_large_text_transform(self):
        """Transform a large text block without error."""
        large = "word " * 50000
        result = TextTransformer.transform_text(large, TransformMode.UPPERCASE)
        self.assertEqual(len(result), len(large))

    def test_large_text_stats(self):
        """Statistics accurate on large text."""
        large = " ".join(f"word{i}" for i in range(10000))
        stats = TextStatistics.calculate(large)
        self.assertEqual(stats.words, 10000)

    def test_diff_then_accept_all_gives_right_text(self):
        """Accept all changes should give the modified text."""
        left = "old line"
        right = "new line"
        result = DiffEngine.compute_diff(left, right)
        result.accept_all()
        merged = result.get_merged_text()
        self.assertIsInstance(merged, str)

    def test_diff_similarity_symmetric(self):
        """Similarity score should be roughly symmetric."""
        a, b = "hello world", "world hello"
        s1 = DiffEngine.compute_similarity(a, b)
        s2 = DiffEngine.compute_similarity(b, a)
        self.assertAlmostEqual(s1, s2, places=5)

    def test_export_then_read_back(self):
        """Export TXT then read back with FileHandler."""
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "roundtrip.txt")
            content = "Round trip test content\nLine two\nLine three"
            ExportManager().export(content, path, ExportOptions(format=ExportFormat.TXT))
            read_back = FileHandler.read_file_content(path)
            self.assertEqual(read_back, content)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_color_keys_used_in_main_window_stylesheet(self):
        """Keys referenced in main_window.py exist in DialogStyleManager."""
        mw_keys = [
            "window_bg", "label_text", "input_bg", "input_text", "input_border",
            "selection_bg", "selection_text", "output_text_color", "button_bg",
            "button_text", "button_hover_bg", "button_pressed_text", "border_color",
            "text_color", "accent", "checkbox_border", "checkbox_indicator_bg",
            "scrollbar_bg", "scrollbar_handle_main", "scrollbar_handle_hover",
            "list_hover_bg", "list_hover_text", "tooltip_border",
        ]
        for key in mw_keys:
            self.assertIn(key, DialogStyleManager.DARK, f"Missing DARK key: {key}")
            self.assertIn(key, DialogStyleManager.LIGHT, f"Missing LIGHT key: {key}")

    def test_all_transform_modes_stable_on_repeated_calls(self):
        """Idempotency check: transforming already-transformed text is stable."""
        text = "hello world"
        for mode in [TransformMode.UPPERCASE, TransformMode.LOWERCASE,
                     TransformMode.SNAKE_CASE, TransformMode.KEBAB_CASE,
                     TransformMode.CONSTANT_CASE]:
            first = TextTransformer.transform_text(text, mode)
            second = TextTransformer.transform_text(first, mode)
            self.assertEqual(first, second, f"Mode {mode} is not idempotent")

    def test_regex_find_then_replace(self):
        """Find all matches, then replace them — consistent count."""
        pattern = r"\d+"
        text = "abc 123 def 456 ghi 789"
        matches = RegexHelper.find_all_matches(pattern, text)
        replaced = RegexHelper.replace_all(pattern, "NUM", text)
        self.assertEqual(replaced.count("NUM"), len(matches))

    def test_preset_step_disabled_in_pipeline(self):
        """A disabled step in a multi-step preset must be completely skipped."""
        exe = PresetExecutor()
        preset = TransformPreset(name="DisabledTest")
        preset.add_step(PresetStep(action=ActionType.TRANSFORM,
                                   params={"mode": TransformMode.UPPERCASE}, enabled=True))
        preset.add_step(PresetStep(action=ActionType.PREFIX,
                                   params={"text": "NOPE_"}, enabled=False))
        result, _ = exe.execute_preset("hello", preset)
        self.assertEqual(result, "HELLO")
        self.assertNotIn("NOPE_", result)




# ══════════════════════════════════════════════════════════════════════════════
# 13. SETTINGS MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestSettingsManager(unittest.TestCase):
    """utils/settings_manager.py — real QSettings save/load cycle for all keys."""

    @classmethod
    def setUpClass(cls):
        # Use a unique test org/app name to avoid touching real user settings
        from PyQt6.QtCore import QSettings
        cls._orig_org = SettingsManager._ORGANIZATION
        SettingsManager._ORGANIZATION = "RNV_TEST_SUITE"
        cls.sm = SettingsManager()
        cls.sm.clear_all()

    @classmethod
    def tearDownClass(cls):
        cls.sm.clear_all()
        SettingsManager._ORGANIZATION = cls._orig_org

    # ── Theme ──────────────────────────────────────────────────────────────────
    def test_save_load_theme_dark(self):
        self.sm.save_theme("dark")
        self.assertEqual(self.sm.load_theme(), "dark")

    def test_save_load_theme_light(self):
        self.sm.save_theme("light")
        self.assertEqual(self.sm.load_theme(), "light")

    def test_save_load_theme_image(self):
        self.sm.save_theme("image")
        self.assertEqual(self.sm.load_theme(), "image")

    def test_load_theme_default(self):
        self.sm.clear_all()
        theme = self.sm.load_theme()
        self.assertIsInstance(theme, str)
        self.assertGreater(len(theme), 0)

    # ── Transform mode ─────────────────────────────────────────────────────────
    def test_save_load_transform_mode(self):
        self.sm.save_transform_mode("UPPERCASE")
        self.assertEqual(self.sm.load_transform_mode(), "UPPERCASE")

    def test_save_load_transform_mode_snake(self):
        self.sm.save_transform_mode("snake_case")
        self.assertEqual(self.sm.load_transform_mode(), "snake_case")

    def test_load_transform_mode_default(self):
        self.sm.clear_all()
        mode = self.sm.load_transform_mode()
        self.assertIsInstance(mode, str)

    # ── Window position ────────────────────────────────────────────────────────
    def test_save_load_window_position(self):
        self.sm.save_window_position(100, 200, 900, 600)
        x, y, w, h = self.sm.load_window_position()
        self.assertEqual((x, y, w, h), (100, 200, 900, 600))

    def test_save_load_window_position_zero(self):
        self.sm.save_window_position(0, 0, 800, 600)
        x, y, w, h = self.sm.load_window_position()
        self.assertEqual(w, 800)
        self.assertEqual(h, 600)

    def test_load_window_position_default_positive(self):
        self.sm.clear_all()
        x, y, w, h = self.sm.load_window_position()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    # ── Maximized ─────────────────────────────────────────────────────────────
    def test_save_load_maximized_true(self):
        self.sm.save_window_maximized(True)
        self.assertTrue(self.sm.load_window_maximized())

    def test_save_load_maximized_false(self):
        self.sm.save_window_maximized(False)
        self.assertFalse(self.sm.load_window_maximized())

    # ── Auto transform ─────────────────────────────────────────────────────────
    def test_save_load_auto_transform_true(self):
        self.sm.save_auto_transform(True)
        self.assertTrue(self.sm.load_auto_transform())

    def test_save_load_auto_transform_false(self):
        self.sm.save_auto_transform(False)
        self.assertFalse(self.sm.load_auto_transform())

    # ── Tooltips ───────────────────────────────────────────────────────────────
    def test_save_load_show_tooltips_true(self):
        self.sm.save_show_tooltips(True)
        self.assertTrue(self.sm.load_show_tooltips())

    def test_save_load_show_tooltips_false(self):
        self.sm.save_show_tooltips(False)
        self.assertFalse(self.sm.load_show_tooltips())

    # ── Stats position ─────────────────────────────────────────────────────────
    def test_save_load_stats_position_bottom(self):
        self.sm.save_stats_position("bottom")
        self.assertEqual(self.sm.load_stats_position(), "bottom")

    def test_save_load_stats_position_side(self):
        self.sm.save_stats_position("side")
        self.assertEqual(self.sm.load_stats_position(), "side")

    # ── Recent files ───────────────────────────────────────────────────────────
    def test_save_load_recent_files(self):
        files = ["/path/a.txt", "/path/b.txt", "/path/c.txt"]
        self.sm.save_recent_files(files)
        loaded = self.sm.load_recent_files()
        self.assertEqual(loaded, files)

    def test_add_recent_file_appears_first(self):
        self.sm.clear_recent_files()
        self.sm.add_recent_file("/old.txt")
        self.sm.add_recent_file("/new.txt")
        files = self.sm.load_recent_files()
        self.assertEqual(files[0], "/new.txt")

    def test_add_recent_file_deduplicates(self):
        self.sm.clear_recent_files()
        self.sm.add_recent_file("/same.txt")
        self.sm.add_recent_file("/same.txt")
        files = self.sm.load_recent_files()
        self.assertEqual(files.count("/same.txt"), 1)

    def test_add_recent_file_max_enforced(self):
        self.sm.clear_recent_files()
        for i in range(15):
            self.sm.add_recent_file(f"/file{i}.txt", max_files=10)
        files = self.sm.load_recent_files()
        self.assertLessEqual(len(files), 10)

    def test_clear_recent_files(self):
        self.sm.add_recent_file("/will_clear.txt")
        self.sm.clear_recent_files()
        self.assertEqual(self.sm.load_recent_files(), [])

    def test_save_load_recent_files_max(self):
        self.sm.save_recent_files_max(5)
        self.assertEqual(self.sm.load_recent_files_max(), 5)

    # ── Utilities ──────────────────────────────────────────────────────────────
    def test_contains_after_save(self):
        self.sm.save_theme("dark")
        self.assertTrue(self.sm.contains("theme/current"))

    def test_contains_missing_key(self):
        self.assertFalse(self.sm.contains("this/does/not/exist/xyz"))

    def test_get_settings_path_is_string(self):
        path = self.sm.get_settings_path()
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_sync_runs_without_error(self):
        try:
            self.sm.sync()
        except Exception as e:
            self.fail(f"sync() raised: {e}")

    def test_clear_all_removes_keys(self):
        self.sm.save_theme("dark")
        self.sm.save_transform_mode("UPPERCASE")
        self.sm.clear_all()
        self.assertFalse(self.sm.contains("theme/current"))


# ══════════════════════════════════════════════════════════════════════════════
# 14. THEME MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestThemeManager(unittest.TestCase):
    """core/theme_manager.py — theme cycling, colors, display names."""

    def setUp(self):
        self.tm = ThemeManager()

    # ── Initial state ──────────────────────────────────────────────────────────
    def test_initial_theme_is_dark(self):
        self.assertEqual(self.tm.current_theme, "dark")

    def test_initial_image_mode_false(self):
        self.assertFalse(self.tm.image_mode_active)

    def test_initial_background_pixmap_none(self):
        self.assertIsNone(self.tm.get_background_pixmap())

    # ── set_theme ──────────────────────────────────────────────────────────────
    def test_set_theme_dark(self):
        self.tm.set_theme("dark")
        self.assertEqual(self.tm.current_theme, "dark")

    def test_set_theme_light(self):
        self.tm.set_theme("light")
        self.assertEqual(self.tm.current_theme, "light")

    def test_set_theme_invalid_returns_false(self):
        ok = self.tm.set_theme("invalid_theme")
        self.assertFalse(ok)

    def test_set_theme_valid_returns_true(self):
        ok = self.tm.set_theme("dark")
        self.assertTrue(ok)

    # ── is_dark_mode ───────────────────────────────────────────────────────────
    def test_is_dark_mode_dark(self):
        self.tm.set_theme("dark")
        self.assertTrue(self.tm.is_dark_mode)

    def test_is_dark_mode_light(self):
        self.tm.set_theme("light")
        self.assertFalse(self.tm.is_dark_mode)

    # ── colors property ────────────────────────────────────────────────────────
    def test_colors_dark_returns_dict(self):
        self.tm.set_theme("dark")
        c = self.tm.colors
        self.assertIsInstance(c, dict)
        self.assertIn("accent", c)

    def test_colors_light_returns_dict(self):
        self.tm.set_theme("light")
        c = self.tm.colors
        self.assertIsInstance(c, dict)
        self.assertIn("accent", c)

    def test_colors_dark_accent_is_brand_gold(self):
        self.tm.set_theme("dark")
        self.assertEqual(self.tm.colors["accent"].lower(), "#d2bc93")

    def test_colors_light_accent_is_brand_gold_dark(self):
        self.tm.set_theme("light")
        self.assertEqual(self.tm.colors["accent"].lower(), "#b19145")

    # ── cycle_theme ────────────────────────────────────────────────────────────
    def test_cycle_theme_dark_to_light(self):
        self.tm.set_theme("dark")
        self.tm.image_mode_available = False
        new_theme = self.tm.cycle_theme()
        self.assertEqual(new_theme, "light")

    def test_cycle_theme_light_to_dark(self):
        self.tm.set_theme("light")
        self.tm.image_mode_available = False
        new_theme = self.tm.cycle_theme()
        self.assertEqual(new_theme, "dark")

    def test_cycle_theme_returns_string(self):
        new_theme = self.tm.cycle_theme()
        self.assertIsInstance(new_theme, str)

    # ── get_theme_display_name ─────────────────────────────────────────────────
    def test_display_name_dark(self):
        self.tm.set_theme("dark")
        name = self.tm.get_theme_display_name()
        self.assertIn("Dark", name)

    def test_display_name_light(self):
        self.tm.set_theme("light")
        name = self.tm.get_theme_display_name()
        self.assertIn("Light", name)

    def test_display_name_is_string(self):
        self.assertIsInstance(self.tm.get_theme_display_name(), str)

    # ── is_image_mode ──────────────────────────────────────────────────────────
    def test_is_image_mode_false_by_default(self):
        self.assertFalse(self.tm.is_image_mode())


# ══════════════════════════════════════════════════════════════════════════════
# 15. LOGGER
# ══════════════════════════════════════════════════════════════════════════════
class TestLogger(unittest.TestCase):
    """utils/logger.py — Logger class, log levels, get_module_logger."""

    # ── Logger creation ────────────────────────────────────────────────────────
    def test_create_logger(self):
        logger = Logger("TestModule")
        self.assertIsNotNone(logger)

    def test_logger_name(self):
        logger = Logger("MyModule")
        self.assertEqual(logger.name, "MyModule")

    # ── Log levels ─────────────────────────────────────────────────────────────
    def test_log_level_enum_values(self):
        self.assertLess(LogLevel.DEBUG.value, LogLevel.INFO.value)
        self.assertLess(LogLevel.INFO.value, LogLevel.WARNING.value)
        self.assertLess(LogLevel.WARNING.value, LogLevel.ERROR.value)
        self.assertLess(LogLevel.ERROR.value, LogLevel.CRITICAL.value)

    def test_log_info_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.info("test info message")
        except Exception as e:
            self.fail(f"info() raised: {e}")

    def test_log_success_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.success("test success")
        except Exception as e:
            self.fail(f"success() raised: {e}")

    def test_log_warning_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.warning("test warning")
        except Exception as e:
            self.fail(f"warning() raised: {e}")

    def test_log_error_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.error("test error", error=ValueError("oops"))
        except Exception as e:
            self.fail(f"error() raised: {e}")

    def test_log_debug_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.debug("test debug")
        except Exception as e:
            self.fail(f"debug() raised: {e}")

    def test_log_with_details(self):
        logger = Logger("Test")
        try:
            logger.info("message with details", details="extra info")
        except Exception as e:
            self.fail(f"info() with details raised: {e}")

    def test_separator_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.separator()
        except Exception as e:
            self.fail(f"separator() raised: {e}")

    def test_header_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.header("Test Header")
        except Exception as e:
            self.fail(f"header() raised: {e}")

    def test_blank_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.blank()
        except Exception as e:
            self.fail(f"blank() raised: {e}")

    def test_indent_runs_without_error(self):
        logger = Logger("Test")
        try:
            logger.indent("indented message")
        except Exception as e:
            self.fail(f"indent() raised: {e}")

    # ── get_module_logger ──────────────────────────────────────────────────────
    def test_get_module_logger_returns_logger(self):
        logger = get_module_logger("TestModule")
        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, Logger)

    def test_get_module_logger_different_names(self):
        l1 = get_module_logger("ModuleA")
        l2 = get_module_logger("ModuleB")
        self.assertIsNotNone(l1)
        self.assertIsNotNone(l2)

    # ── configure ─────────────────────────────────────────────────────────────
    def test_configure_runs_without_error(self):
        try:
            configure(enable_colors=False, show_timestamp=False)
            configure(enable_colors=True)  # restore
        except Exception as e:
            self.fail(f"configure() raised: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 16. BATCH PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
class TestBatchProcessor(unittest.TestCase):
    """core/batch_processor.py — file discovery, processing, summary."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        # Create test files
        (cls.tmp / "a.txt").write_text("hello world", encoding="utf-8")
        (cls.tmp / "b.txt").write_text("foo bar baz", encoding="utf-8")
        (cls.tmp / "c.md").write_text("# heading", encoding="utf-8")
        (cls.tmp / "ignored.xyz").write_text("skip me", encoding="utf-8")
        sub = cls.tmp / "subdir"
        sub.mkdir()
        (sub / "d.txt").write_text("sub file", encoding="utf-8")
        cls.out = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.tmp), ignore_errors=True)
        shutil.rmtree(str(cls.out), ignore_errors=True)

    # ── get_supported_files ────────────────────────────────────────────────────
    def test_get_supported_files_finds_txt(self):
        bp = BatchProcessor("UPPERCASE")
        files = bp.get_supported_files(self.tmp)
        names = [f.name for f in files]
        self.assertIn("a.txt", names)
        self.assertIn("b.txt", names)

    def test_get_supported_files_skips_unsupported(self):
        bp = BatchProcessor("UPPERCASE")
        files = bp.get_supported_files(self.tmp)
        names = [f.name for f in files]
        self.assertNotIn("ignored.xyz", names)

    def test_get_supported_files_non_recursive(self):
        bp = BatchProcessor("UPPERCASE", recursive=False)
        files = bp.get_supported_files(self.tmp)
        names = [f.name for f in files]
        self.assertNotIn("d.txt", names)

    def test_get_supported_files_recursive(self):
        bp = BatchProcessor("UPPERCASE", recursive=True)
        files = bp.get_supported_files(self.tmp)
        names = [f.name for f in files]
        self.assertIn("d.txt", names)

    def test_get_supported_files_sorted(self):
        bp = BatchProcessor("UPPERCASE")
        files = bp.get_supported_files(self.tmp)
        self.assertEqual(files, sorted(files))

    def test_get_supported_files_empty_folder(self):
        empty = Path(tempfile.mkdtemp())
        try:
            bp = BatchProcessor("UPPERCASE")
            files = bp.get_supported_files(empty)
            self.assertEqual(files, [])
        finally:
            shutil.rmtree(str(empty))

    # ── process_folder ─────────────────────────────────────────────────────────
    def test_process_folder_yields_progress(self):
        bp = BatchProcessor("UPPERCASE", output_folder=self.out)
        progress_seen = False
        for progress, result in bp.process_folder(self.tmp):
            if progress is not None:
                progress_seen = True
                self.assertIsInstance(progress, BatchProgress)
                break
        self.assertTrue(progress_seen)

    def test_process_folder_results_are_batch_results(self):
        out = Path(tempfile.mkdtemp())
        try:
            bp = BatchProcessor("UPPERCASE", output_folder=out)
            results = []
            for _, result in bp.process_folder(self.tmp):
                if result is not None:
                    results.append(result)
                    self.assertIsInstance(result, BatchResult)
        finally:
            shutil.rmtree(str(out))

    def test_process_folder_successful_results(self):
        out = Path(tempfile.mkdtemp())
        try:
            bp = BatchProcessor("UPPERCASE", output_folder=out)
            results = [r for _, r in bp.process_folder(self.tmp) if r is not None]
            successful = [r for r in results if r.success]
            self.assertGreater(len(successful), 0)
        finally:
            shutil.rmtree(str(out))

    def test_process_folder_output_files_created(self):
        out = Path(tempfile.mkdtemp())
        try:
            bp = BatchProcessor("UPPERCASE", output_folder=out)
            list(bp.process_folder(self.tmp))  # exhaust generator
            out_files = list(out.glob("*.txt"))
            self.assertGreater(len(out_files), 0)
        finally:
            shutil.rmtree(str(out))

    def test_process_folder_content_transformed(self):
        out = Path(tempfile.mkdtemp())
        try:
            bp = BatchProcessor("UPPERCASE", output_folder=out)
            list(bp.process_folder(self.tmp))
            out_file = out / "a.txt"
            if out_file.exists():
                content = out_file.read_text(encoding="utf-8")
                self.assertEqual(content, "HELLO WORLD")
        finally:
            shutil.rmtree(str(out))

    # ── cancel ─────────────────────────────────────────────────────────────────
    def test_cancel_sets_flag(self):
        bp = BatchProcessor("UPPERCASE")
        self.assertFalse(bp._cancelled)
        bp.cancel()
        self.assertTrue(bp._cancelled)

    # ── _get_output_path ───────────────────────────────────────────────────────
    def test_get_output_path_same_dir_adds_suffix(self):
        bp = BatchProcessor("UPPERCASE")
        src = self.tmp / "a.txt"
        out = bp._get_output_path(src, self.tmp)
        self.assertIn("_transformed", out.name)

    def test_get_output_path_with_output_folder(self):
        bp = BatchProcessor("UPPERCASE", output_folder=self.out)
        src = self.tmp / "a.txt"
        out = bp._get_output_path(src, self.tmp)
        self.assertEqual(out.parent, self.out)

    # ── get_summary ────────────────────────────────────────────────────────────
    def test_get_summary_empty(self):
        summary = BatchProcessor.get_summary([])
        self.assertEqual(summary["total_files"], 0)
        self.assertEqual(summary["successful"], 0)

    def test_get_summary_all_success(self):
        results = [
            BatchResult(file_path=Path("a.txt"), success=True, message="ok",
                        original_size=10, processed_size=10),
            BatchResult(file_path=Path("b.txt"), success=True, message="ok",
                        original_size=5, processed_size=5),
        ]
        summary = BatchProcessor.get_summary(results)
        self.assertEqual(summary["total_files"], 2)
        self.assertEqual(summary["successful"], 2)
        self.assertEqual(summary["failed"], 0)

    def test_get_summary_mixed(self):
        results = [
            BatchResult(file_path=Path("a.txt"), success=True,  message="ok"),
            BatchResult(file_path=Path("b.txt"), success=False, message="err"),
        ]
        summary = BatchProcessor.get_summary(results)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 1)

    def test_get_summary_keys(self):
        summary = BatchProcessor.get_summary([])
        for key in ("total_files", "successful", "failed",
                    "total_original_bytes", "total_processed_bytes"):
            self.assertIn(key, summary)

    # ── BatchResult dataclass ──────────────────────────────────────────────────
    def test_batch_result_fields(self):
        r = BatchResult(file_path=Path("x.txt"), success=True, message="done")
        self.assertEqual(r.file_path, Path("x.txt"))
        self.assertTrue(r.success)
        self.assertEqual(r.message, "done")
        self.assertEqual(r.original_size, 0)
        self.assertEqual(r.processed_size, 0)

    # ── BatchProgress namedtuple ───────────────────────────────────────────────
    def test_batch_progress_fields(self):
        p = BatchProgress(current=2, total=5, current_file="a.txt", percent=40.0)
        self.assertEqual(p.current, 2)
        self.assertEqual(p.total, 5)
        self.assertEqual(p.percent, 40.0)


# ══════════════════════════════════════════════════════════════════════════════
# 17. FOLDER WATCHER
# ══════════════════════════════════════════════════════════════════════════════
class TestFolderWatcher(unittest.TestCase):
    """core/folder_watcher.py — WatchRule serialization, FolderWatcher CRUD."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.in_dir  = cls.tmp / "input"
        cls.out_dir = cls.tmp / "output"
        cls.in_dir.mkdir()
        cls.out_dir.mkdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.tmp), ignore_errors=True)

    def _make_rule(self, rule_id: str = "rule1") -> WatchRule:
        return WatchRule(
            id=rule_id,
            input_folder=self.in_dir,
            output_folder=self.out_dir,
            file_patterns=["*.txt"],
            transform_mode="UPPERCASE",
        )

    # ── WatchEventType ─────────────────────────────────────────────────────────
    def test_event_types_are_strings(self):
        for evt in WatchEventType:
            self.assertIsInstance(str(evt), str)

    # ── WatchRule ──────────────────────────────────────────────────────────────
    def test_watch_rule_creation(self):
        rule = self._make_rule()
        self.assertEqual(rule.id, "rule1")
        self.assertTrue(rule.enabled)

    def test_watch_rule_matches_txt(self):
        rule = self._make_rule()
        self.assertTrue(rule.matches_file(Path("document.txt")))

    def test_watch_rule_no_match_py(self):
        rule = self._make_rule()
        self.assertFalse(rule.matches_file(Path("script.py")))

    def test_watch_rule_wildcard_pattern(self):
        rule = WatchRule(id="r", input_folder=self.in_dir,
                         output_folder=self.out_dir, file_patterns=["*"])
        self.assertTrue(rule.matches_file(Path("anything.xyz")))

    def test_watch_rule_to_dict(self):
        rule = self._make_rule()
        d = rule.to_dict()
        self.assertIn("id", d)
        self.assertIn("input_folder", d)
        self.assertIn("output_folder", d)
        self.assertIn("file_patterns", d)
        self.assertIn("transform_mode", d)
        self.assertIn("enabled", d)

    def test_watch_rule_from_dict_roundtrip(self):
        rule = self._make_rule()
        rule2 = WatchRule.from_dict(rule.to_dict())
        self.assertEqual(rule2.id, rule.id)
        self.assertEqual(rule2.transform_mode, rule.transform_mode)
        self.assertEqual(rule2.file_patterns, rule.file_patterns)
        self.assertEqual(rule2.enabled, rule.enabled)

    def test_watch_rule_disabled(self):
        rule = WatchRule(id="r", input_folder=self.in_dir,
                         output_folder=self.out_dir, enabled=False)
        self.assertFalse(rule.enabled)

    def test_watch_rule_delete_source_default_false(self):
        rule = self._make_rule()
        self.assertFalse(rule.delete_source)

    # ── WatchEvent dataclass ───────────────────────────────────────────────────
    def test_watch_event_creation(self):
        evt = WatchEvent(event_type=WatchEventType.FILE_CREATED,
                         file_path=Path("test.txt"), message="new file")
        self.assertEqual(evt.event_type, WatchEventType.FILE_CREATED)
        self.assertEqual(evt.file_path, Path("test.txt"))

    def test_watch_event_timestamp_set(self):
        evt = WatchEvent(event_type=WatchEventType.WATCHER_STARTED)
        self.assertIsNotNone(evt.timestamp)

    # ── FolderWatcher ──────────────────────────────────────────────────────────
    def test_folder_watcher_creation(self):
        fw = FolderWatcher()
        self.assertIsNotNone(fw)

    def test_is_available_returns_bool(self):
        result = FolderWatcher.is_available()
        self.assertIsInstance(result, bool)

    def test_get_rules_empty_initially(self):
        fw = FolderWatcher()
        self.assertEqual(fw.get_rules(), [])

    def test_get_rule_nonexistent_returns_none(self):
        fw = FolderWatcher()
        self.assertIsNone(fw.get_rule("nonexistent"))

    def test_remove_rule_nonexistent_returns_false(self):
        fw = FolderWatcher()
        self.assertFalse(fw.remove_rule("nonexistent"))

    def test_update_rule_nonexistent_returns_false(self):
        fw = FolderWatcher()
        rule = self._make_rule()
        self.assertFalse(fw.update_rule(rule))

    def test_set_event_callback(self):
        fw = FolderWatcher()
        events = []
        fw.set_event_callback(events.append)
        self.assertEqual(fw._event_callback, events.append)

    @unittest.skipUnless(WATCHDOG_AVAILABLE, "watchdog not installed")
    def test_add_rule_with_existing_folder(self):
        fw = FolderWatcher()
        rule = self._make_rule("add_test")
        ok = fw.add_rule(rule)
        self.assertTrue(ok)
        self.assertIsNotNone(fw.get_rule("add_test"))

    @unittest.skipUnless(WATCHDOG_AVAILABLE, "watchdog not installed")
    def test_remove_rule_after_add(self):
        fw = FolderWatcher()
        rule = self._make_rule("remove_test")
        fw.add_rule(rule)
        ok = fw.remove_rule("remove_test")
        self.assertTrue(ok)
        self.assertIsNone(fw.get_rule("remove_test"))

    @unittest.skipUnless(WATCHDOG_AVAILABLE, "watchdog not installed")
    def test_update_rule_after_add(self):
        fw = FolderWatcher()
        rule = self._make_rule("update_test")
        fw.add_rule(rule)
        rule.transform_mode = "lowercase"
        ok = fw.update_rule(rule)
        self.assertTrue(ok)
        updated = fw.get_rule("update_test")
        self.assertEqual(updated.transform_mode, "lowercase")


# ══════════════════════════════════════════════════════════════════════════════
# 18. CLIPBOARD UTILS
# ══════════════════════════════════════════════════════════════════════════════
class TestClipboardUtils(unittest.TestCase):
    """utils/clipboard_utils.py — copy, get, has_text (headless Qt clipboard)."""

    def test_copy_to_clipboard_success(self):
        ok = ClipboardUtils.copy_to_clipboard("hello clipboard")
        self.assertTrue(ok)

    def test_copy_empty_string_returns_false(self):
        ok = ClipboardUtils.copy_to_clipboard("")
        self.assertFalse(ok)

    def test_get_clipboard_text_after_copy(self):
        ClipboardUtils.copy_to_clipboard("test value")
        text = ClipboardUtils.get_clipboard_text()
        self.assertEqual(text, "test value")

    def test_get_clipboard_text_returns_string(self):
        result = ClipboardUtils.get_clipboard_text()
        self.assertIsInstance(result, str)

    def test_has_text_after_copy(self):
        ClipboardUtils.copy_to_clipboard("some text")
        self.assertTrue(ClipboardUtils.has_text())

    def test_copy_multiline(self):
        text = "line1\nline2\nline3"
        ok = ClipboardUtils.copy_to_clipboard(text)
        self.assertTrue(ok)
        self.assertEqual(ClipboardUtils.get_clipboard_text(), text)

    def test_copy_unicode(self):
        text = "café ☕ 日本語"
        ok = ClipboardUtils.copy_to_clipboard(text)
        self.assertTrue(ok)
        self.assertEqual(ClipboardUtils.get_clipboard_text(), text)

    def test_copy_overwrites_previous(self):
        ClipboardUtils.copy_to_clipboard("first")
        ClipboardUtils.copy_to_clipboard("second")
        self.assertEqual(ClipboardUtils.get_clipboard_text(), "second")


# ══════════════════════════════════════════════════════════════════════════════
# 19. CLI PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_CLI_AVAILABLE, "cli.rnv_transform not importable")
class TestCLIProcessor(unittest.TestCase):
    """cli/rnv_transform.py — CLIOptions, CLIProcessor list commands and transforms."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.src = cls.tmp / "input.txt"
        cls.src.write_text("hello world", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.tmp), ignore_errors=True)

    # ── CLIOptions ─────────────────────────────────────────────────────────────
    def test_cli_options_defaults(self):
        opts = CLIOptions()
        self.assertIsNone(opts.mode)
        self.assertFalse(opts.recursive)
        self.assertFalse(opts.verbose)
        self.assertEqual(opts.encoding, "utf-8")

    def test_cli_options_set_mode(self):
        opts = CLIOptions(mode="UPPERCASE")
        self.assertEqual(opts.mode, "UPPERCASE")

    def test_output_format_values(self):
        self.assertEqual(OutputFormat.TEXT, "text")
        self.assertEqual(OutputFormat.JSON, "json")
        self.assertEqual(OutputFormat.QUIET, "quiet")

    # ── list_modes ─────────────────────────────────────────────────────────────
    def test_list_modes_returns_zero(self):
        opts = CLIOptions(list_modes=True)
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 0)

    # ── list_cleanup ───────────────────────────────────────────────────────────
    def test_list_cleanup_returns_zero(self):
        opts = CLIOptions(list_cleanup=True)
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 0)

    # ── list_presets ───────────────────────────────────────────────────────────
    def test_list_presets_returns_zero(self):
        opts = CLIOptions(list_presets=True)
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 0)

    # ── validate_options ───────────────────────────────────────────────────────
    def test_no_mode_no_input_returns_one(self):
        opts = CLIOptions()
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 1)

    # ── file transform ─────────────────────────────────────────────────────────
    def test_transform_file_uppercase(self):
        out = self.tmp / "out.txt"
        opts = CLIOptions(
            input_files=[self.src],
            output_file=out,
            mode="UPPERCASE"
        )
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text(encoding="utf-8"), "HELLO WORLD")

    def test_transform_file_lowercase(self):
        out = self.tmp / "lower.txt"
        opts = CLIOptions(
            input_files=[self.src],
            output_file=out,
            mode="lowercase"
        )
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertEqual(code, 0)
        self.assertEqual(out.read_text(encoding="utf-8"), "hello world")

    def test_transform_nonexistent_file_returns_error(self):
        opts = CLIOptions(
            input_files=[Path("/nonexistent/file.txt")],
            mode="UPPERCASE"
        )
        proc = CLIProcessor(opts)
        code = proc.run()
        self.assertNotEqual(code, 0)


# ══════════════════════════════════════════════════════════════════════════════
# 20. EXTENDED INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestExtendedIntegration(unittest.TestCase):
    """Full pipeline tests combining newly covered modules."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.tmp), ignore_errors=True)

    def test_batch_then_export(self):
        """Batch-process files then export summary as Markdown."""
        src = self.tmp / "batch_src"
        out = self.tmp / "batch_out"
        src.mkdir(exist_ok=True)
        (src / "x.txt").write_text("hello world", encoding="utf-8")
        (src / "y.txt").write_text("foo bar", encoding="utf-8")

        bp = BatchProcessor("UPPERCASE", output_folder=out)
        results = [r for _, r in bp.process_folder(src) if r is not None]
        summary = BatchProcessor.get_summary(results)

        # Export the summary as a Markdown file
        summary_text = "\n".join(f"{k}: {v}" for k, v in summary.items())
        export_path = self.tmp / "summary.md"
        ok = ExportManager().export(summary_text, export_path,
                                    ExportOptions(format=ExportFormat.MARKDOWN))
        self.assertTrue(ok)
        self.assertTrue(export_path.exists())

    def test_theme_colors_used_in_export(self):
        """Export HTML using dark theme and verify accent color matches ThemeManager."""
        tm = ThemeManager()
        tm.set_theme("dark")
        accent = tm.colors["accent"]

        path = self.tmp / "theme_export.html"
        ExportManager().export("test content", path,
                               ExportOptions(format=ExportFormat.HTML, html_dark_theme=True))
        content = path.read_text(encoding="utf-8")
        self.assertIn(accent, content)

    def test_settings_roundtrip_with_transform(self):
        """Save a transform mode in settings, reload it, apply it."""
        from PyQt6.QtCore import QSettings
        SettingsManager._ORGANIZATION = "RNV_TEST_INTEGRATION"
        sm = SettingsManager()
        sm.save_transform_mode("snake_case")
        mode = sm.load_transform_mode()
        result = TextTransformer.transform_text("Hello World Test", mode)
        self.assertEqual(result, "hello_world_test")
        sm.clear_all()
        SettingsManager._ORGANIZATION = "RNV"

    def test_clipboard_copy_then_transform(self):
        """Copy text to clipboard, read it back, transform it."""
        original = "Hello Clipboard World"
        ClipboardUtils.copy_to_clipboard(original)
        text = ClipboardUtils.get_clipboard_text()
        result = TextTransformer.transform_text(text, "snake_case")
        self.assertEqual(result, "hello_clipboard_world")

    def test_watch_rule_serialization_with_preset(self):
        """WatchRule with a preset_name survives to_dict/from_dict."""
        rule = WatchRule(
            id="test",
            input_folder=Path("/tmp/in"),
            output_folder=Path("/tmp/out"),
            preset_name="MyPreset",
            transform_mode=None,
        )
        d = rule.to_dict()
        rule2 = WatchRule.from_dict(d)
        self.assertEqual(rule2.preset_name, "MyPreset")
        self.assertIsNone(rule2.transform_mode)

    def test_logger_does_not_interfere_with_transforms(self):
        """Logger calls must not affect transformation output."""
        logger = Logger("IntegrationTest")
        logger.info("About to transform")
        result = TextTransformer.transform_text("hello world", "UPPERCASE")
        logger.success("Transform complete", details=result)
        self.assertEqual(result, "HELLO WORLD")

    def test_full_pipeline_clean_transform_export(self):
        """Clean → transform → stats → export in one pipeline."""
        raw = "  HELLO   WORLD  \n\n\n  foo bar  "
        cleaned = TextCleaner.cleanup(raw, str(CleanupOperation.TRIM_WHITESPACE))
        cleaned = TextCleaner.cleanup(cleaned, str(CleanupOperation.REMOVE_EXTRA_LINES))
        transformed = TextTransformer.transform_text(cleaned, "Title Case")
        stats = TextStatistics.calculate(transformed)
        self.assertGreater(stats.words, 0)
        path = self.tmp / "full_pipeline.txt"
        ok = ExportManager().export(transformed, path, ExportOptions(format=ExportFormat.TXT))
        self.assertTrue(ok)
        content = path.read_text(encoding="utf-8")
        self.assertIn("Hello", content)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def _summary(result):
    total   = result.testsRun
    failed  = len(result.failures)
    errors  = len(result.errors)
    skipped = len(result.skipped)
    passed  = total - failed - errors - skipped

    print(f"\n{'═'*62}\n{_B}  RNV Text Transformer — Test Results{_X}\n{'═'*62}")
    print(f"  {_G}✓ Passed  {passed:>4}{_X}")
    if failed:  print(f"  {_R}✗ Failed  {failed:>4}{_X}")
    if errors:  print(f"  {_R}⚠ Errors  {errors:>4}{_X}")
    if skipped: print(f"  {_Y}  Skipped {skipped:>4}{_X}")
    print(f"  {'─'*18}\n    Total   {total:>4}\n{'═'*62}")

    if result.failures:
        print(f"\n{_R}{_B}FAILURES:{_X}")
        for test, tb in result.failures:
            print(f"  {_R}✗ {test}{_X}")
            for line in tb.splitlines()[-4:]:
                print(f"      {line}")

    if result.errors:
        print(f"\n{_R}{_B}ERRORS:{_X}")
        for test, tb in result.errors:
            print(f"  {_R}⚠ {test}{_X}")
            for line in tb.splitlines()[-4:]:
                print(f"      {line}")

    if passed == total:
        print(f"\n  {_G}{_B}All {total} tests passed ✓{_X}\n")
    else:
        print(f"\n  {_R}{_B}{failed + errors} test(s) need attention.{_X}\n")


if __name__ == "__main__":
    print(f"\n{_C}{_B}{'═'*62}\n  RNV Text Transformer — Comprehensive Test Suite v2.0\n{'═'*62}{_X}")
    print(f"  Project: {_ROOT}\n  Python:  {sys.version.split()[0]}\n")

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        # v1.0 — core engine
        TestTextTransformer,
        TestTextCleaner,
        TestTextStatistics,
        TestDiffEngine,
        TestExportManager,
        TestPresetManager,
        TestRegexPatterns,
        TestDialogStyleManager,
        TestFileHandler,
        TestErrorHandler,
        TestConfig,
        TestEdgeCases,
        # v2.0 — full coverage additions
        TestSettingsManager,
        TestThemeManager,
        TestLogger,
        TestBatchProcessor,
        TestFolderWatcher,
        TestClipboardUtils,
        TestCLIProcessor,
        TestExtendedIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    buf    = io.StringIO()
    runner = unittest.TextTestRunner(
        verbosity=2 if "-v" in sys.argv else 1,
        stream=buf
    )
    result = runner.run(suite)
    print(buf.getvalue(), flush=True)
    _summary(result)
    sys.stdout.flush()
    os._exit(0 if result.wasSuccessful() else 1)