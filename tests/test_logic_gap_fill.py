"""
tests/test_logic_gap_fill.py
============================
Phase 8a — pure-logic gap-fill tests.

Targets eight pure-logic modules with documented coverage gaps. No qtbot
widget driving, no thread orchestration — just direct unit tests against
the public API of each module.

Goal: push overall coverage from 59.1% to roughly 62.5% by closing the
specific uncovered branches identified in the Phase 7 mutation audit and
the Phase 1 coverage baseline, plus error-path edge cases.

Side benefit: closes all three "real gap" findings from the mutmut audit:
  - Finding 1: theme_manager image-mode branch
  - Finding 3: preset_manager duplicate_preset / rename_preset / import_preset
                return-value assertions
  - Finding 4: folder_watcher update_rule / remove_rule paths

Per-class test counts (organized as 17 test classes, 107 tests total):

  --- Sections 1-7: original Phase 8a (56 tests) ---
  TestFileHandlerGapFill ........... 12 tests
  TestDialogHelperGapFill ..........  8 tests
  TestErrorHandlerGapFill ..........  8 tests
  TestPresetManagerGapFill ......... 10 tests
  TestFolderWatcherGapFill .........  8 tests
  TestExportManagerGapFill .........  6 tests
  TestThemeManagerGapFill ..........  4 tests

  --- Section 8: extension-1 (32 tests) ---
  TestPresetExecutorActions ........ 11 tests
  TestDialogHelperExtended .........  6 tests
  TestErrorContextExtended .........  4 tests
  TestThemeManagerExtended .........  5 tests
  TestExportManagerExtended ........  3 tests
  TestPresetManagerExtended ........  3 tests

  --- Section 9: extension-2 — error paths (19 tests) ---
  TestFileHandlerErrorPaths ........  5 tests
  TestErrorHandlerEdgeCases ........  6 tests
  TestExportManagerPDFAndHelpers ...  4 tests
  TestFolderWatcherStartStop .......  4 tests
                                     ---
                                     107 tests

This file is the single source of truth for the Phase 8a test suite;
it supersedes any prior versions named test_logic_gap_fill_*.py.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ── Module imports ────────────────────────────────────────────────────────────
# All seven targets are pure-Python modules importable without Qt running.
# The dialog_helper tests need QApplication, but pytest-qt provides it via
# the qapp fixture.

from utils.file_handler import FileHandler, FileReadError, FileWriteError
from utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    safe_call,
    safe_file_operation,
    safe_text_operation,
)
from core.preset_manager import (
    PresetManager,
    TransformPreset,
    PresetStep,
    ActionType,
)
from core.folder_watcher import (
    FolderWatcher,
    WatchRule,
    WatchEvent,
    WatchEventType,
)
from core.export_manager import (
    ExportManager,
    ExportOptions,
    ExportFormat,
    ExportError,
)
from core.theme_manager import ThemeManager


# ═════════════════════════════════════════════════════════════════════════════
# 1. utils/file_handler.py — 12 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestFileHandlerGapFill:
    """Gap-fill tests for FileHandler: docx, pdf, rtf, write, format detection."""

    # ── Happy path: text files ───────────────────────────────────────────────

    def test_read_file_content_txt_returns_text(self, tmp_path):
        """`.txt` extension routes through `_read_text_file` and returns content."""
        fpath = tmp_path / "sample.txt"
        fpath.write_text("Hello\nWorld", encoding="utf-8")
        assert FileHandler.read_file_content(fpath) == "Hello\nWorld"

    def test_read_file_content_nonexistent_raises_filereaderror(self, tmp_path):
        """Missing file raises `FileReadError`, not the lower-level OSError."""
        bogus = tmp_path / "definitely_does_not_exist.txt"
        with pytest.raises(FileReadError):
            FileHandler.read_file_content(bogus)

    def test_read_file_content_unknown_extension_routes_to_text(self, tmp_path):
        """Unknown extension falls through the default arm of the match statement."""
        fpath = tmp_path / "data.xyz"
        fpath.write_text("payload", encoding="utf-8")
        assert FileHandler.read_file_content(fpath) == "payload"

    def test_read_file_content_latin1_fallback_on_unicode_error(self, tmp_path):
        """When utf-8 raises UnicodeDecodeError, latin-1 fallback succeeds."""
        # Write bytes that are not valid utf-8 but ARE valid latin-1
        fpath = tmp_path / "latin1.txt"
        fpath.write_bytes(b"caf\xe9 \xa9")  # "café ©" in latin-1
        result = FileHandler.read_file_content(fpath)
        # latin-1 reads each byte as itself; the test confirms the fallback
        # path was taken without raising
        assert result is not None
        assert "caf" in result

    # ── DOCX / PDF / RTF (optional deps) ─────────────────────────────────────

    def test_read_docx_file_extracts_paragraphs(self, tmp_path):
        """Real docx round-trip: write paragraphs with python-docx, read back."""
        docx = pytest.importorskip("docx")
        fpath = tmp_path / "sample.docx"
        doc = docx.Document()
        doc.add_paragraph("First paragraph")
        doc.add_paragraph("Second paragraph")
        doc.save(str(fpath))

        result = FileHandler.read_file_content(fpath)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_read_pdf_file_extracts_text(self, tmp_path):
        """Real pdf round-trip — generate a one-page PDF, read text back.

        Uses a pre-built minimal PDF since pypdf can't create PDFs, only read them.
        This embedded PDF contains the literal string 'PDF test content'.
        """
        pypdf = pytest.importorskip("pypdf")
        # Minimal hand-crafted PDF (~600 bytes) — single page, single string.
        # Reusing the standard pypdf test fixture pattern.
        fpath = tmp_path / "sample.pdf"
        # Generate via reportlab if available; otherwise skip
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(fpath))
            c.drawString(100, 750, "PDF test content here")
            c.save()
        except ImportError:
            pytest.skip("reportlab needed to generate test PDF")

        result = FileHandler.read_file_content(fpath)
        assert result is not None
        assert "PDF test content" in result

    def test_read_rtf_file_strips_formatting(self, tmp_path):
        """RTF source with formatting codes returns plain text via striprtf."""
        pytest.importorskip("striprtf")
        fpath = tmp_path / "sample.rtf"
        rtf_source = (
            r"{\rtf1\ansi\deff0 "
            r"{\fonttbl{\f0 Arial;}}"
            r"\f0\fs24 Plain text content here.}"
        )
        fpath.write_text(rtf_source, encoding="utf-8")

        result = FileHandler.read_file_content(fpath)
        assert result is not None
        assert "Plain text content" in result

    # ── Write path ───────────────────────────────────────────────────────────

    def test_write_text_file_creates_file_with_utf8(self, tmp_path):
        """`write_text_file` creates the file with utf-8 encoding."""
        fpath = tmp_path / "out.txt"
        FileHandler.write_text_file(fpath, "Café résumé 🎨")
        assert fpath.read_text(encoding="utf-8") == "Café résumé 🎨"

    def test_write_text_file_overwrites_existing(self, tmp_path):
        """Writing to an existing path replaces its contents."""
        fpath = tmp_path / "out.txt"
        fpath.write_text("original", encoding="utf-8")
        FileHandler.write_text_file(fpath, "replaced")
        assert fpath.read_text(encoding="utf-8") == "replaced"

    def test_write_text_file_raises_on_directory_target(self, tmp_path):
        """Passing a directory path raises `FileWriteError`, not the raw OSError."""
        with pytest.raises(FileWriteError):
            FileHandler.write_text_file(tmp_path, "content")

    # ── Format introspection helpers ─────────────────────────────────────────

    def test_get_file_extension_lowercases_result(self, tmp_path):
        """`.TXT` becomes `.txt` regardless of input casing."""
        assert FileHandler.get_file_extension("REPORT.TXT") == ".txt"
        assert FileHandler.get_file_extension("data.DocX") == ".docx"

    def test_is_supported_format_for_known_and_unknown_extensions(self):
        """`is_supported_format` returns True for known extensions, False otherwise."""
        assert FileHandler.is_supported_format("a.txt") is True
        assert FileHandler.is_supported_format("a.docx") is True
        assert FileHandler.is_supported_format("a.pdf") is True
        assert FileHandler.is_supported_format("a.rtf") is True
        assert FileHandler.is_supported_format("a.xyz") is False
        assert FileHandler.is_supported_format("noextension") is False


# ═════════════════════════════════════════════════════════════════════════════
# 2. utils/dialog_helper.py — 8 tests
# ═════════════════════════════════════════════════════════════════════════════
#
# QMessageBox.exec() is modal; tests patch it to return programmatic values
# so the test thread doesn't block waiting for user input.

class TestDialogHelperGapFill:
    """Gap-fill tests for DialogHelper. Patches QMessageBox.exec()."""

    def test_show_info_invokes_messagebox_with_information_icon(self, qapp):
        """show_info constructs an Information dialog and calls exec."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as exec_mock:
            DialogHelper.show_info("Title", "Body message")
            exec_mock.assert_called_once()

    def test_show_warning_invokes_messagebox(self, qapp):
        """show_warning produces a Warning-icon dialog and calls exec."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as exec_mock:
            DialogHelper.show_warning("Warn", "Something might be wrong")
            exec_mock.assert_called_once()

    def test_show_error_invokes_messagebox(self, qapp):
        """show_error produces a Critical-icon dialog and calls exec."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as exec_mock:
            DialogHelper.show_error("Error", "Something failed", details="Stack trace here")
            exec_mock.assert_called_once()

    def test_show_critical_invokes_messagebox(self, qapp):
        """show_critical produces a Critical-icon dialog and calls exec."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as exec_mock:
            DialogHelper.show_critical("Critical", "System failure")
            exec_mock.assert_called_once()

    def test_confirm_returns_true_when_yes_clicked(self, qapp):
        """confirm() returns True when QMessageBox.exec returns Yes."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
            assert DialogHelper.confirm("Confirm", "Continue?") is True

    def test_confirm_returns_false_when_no_clicked(self, qapp):
        """confirm() returns False when QMessageBox.exec returns No."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No):
            assert DialogHelper.confirm("Confirm", "Continue?") is False

    def test_set_app_name_updates_class_attribute(self, qapp):
        """set_app_name mutates the class-level _APP_NAME."""
        from utils.dialog_helper import DialogHelper
        original = DialogHelper._APP_NAME
        try:
            DialogHelper.set_app_name("TestApp")
            assert DialogHelper._APP_NAME == "TestApp"
        finally:
            DialogHelper.set_app_name(original)

    def test_module_level_show_info_convenience_wrapper(self, qapp):
        """Module-level `show_info` is a thin wrapper around DialogHelper.show_info."""
        from utils import dialog_helper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as exec_mock:
            dialog_helper.show_info("Title", "Body")
            exec_mock.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 3. utils/error_handler.py — 8 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestErrorHandlerGapFill:
    """Gap-fill tests for ErrorHandler decorators and convenience helpers."""

    def test_safe_method_decorator_returns_value_on_success(self):
        """`@ErrorHandler.safe_method` wraps a function; returns its real value on success."""
        @ErrorHandler.safe_method("test op", fallback_value=-1)
        def succeed(x: int) -> int:
            return x * 2

        assert succeed(5) == 10

    def test_safe_method_decorator_returns_fallback_on_exception(self):
        """`@ErrorHandler.safe_method` returns the fallback when wrapped function raises."""
        @ErrorHandler.safe_method("test op", fallback_value="DEFAULT")
        def boom() -> str:
            raise RuntimeError("intentional")

        assert boom() == "DEFAULT"

    def test_try_or_default_returns_function_result_on_success(self):
        """try_or_default returns func() when func succeeds."""
        result = ErrorHandler.try_or_default(lambda: int("42"), default=0)
        assert result == 42

    def test_try_or_default_returns_default_on_exception(self):
        """try_or_default returns `default` when func raises."""
        result = ErrorHandler.try_or_default(lambda: int("not a number"), default=99)
        assert result == 99

    def test_safe_call_wraps_function_and_logs(self):
        """Module-level `safe_call` returns the value or default."""
        assert safe_call(lambda: "value") == "value"
        assert safe_call(lambda: 1 / 0, default="fallback") == "fallback"

    def test_safe_file_operation_returns_none_on_file_not_found(self):
        """safe_file_operation maps FileNotFoundError to None with a log warning."""
        def raise_fnf():
            raise FileNotFoundError("missing")

        result = safe_file_operation(raise_fnf, "/tmp/bogus.txt", "reading")
        assert result is None

    def test_safe_file_operation_returns_none_on_permission_error(self):
        """safe_file_operation maps PermissionError to None with a log warning."""
        def raise_perm():
            raise PermissionError("no access")

        result = safe_file_operation(raise_perm, "/etc/protected", "writing")
        assert result is None

    def test_safe_text_operation_returns_empty_string_on_exception(self):
        """safe_text_operation returns "" when the inner func raises."""
        def boom():
            raise ValueError("text problem")

        assert safe_text_operation(boom, "uppercase") == ""


# ═════════════════════════════════════════════════════════════════════════════
# 4. core/preset_manager.py — 10 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestPresetManagerGapFill:
    """Gap-fill tests for PresetManager. Closes mutmut return-value gaps."""

    def _make_user_preset(self, manager: PresetManager, name: str = "My Preset") -> TransformPreset:
        """Create and register a non-builtin preset for manipulation."""
        preset = TransformPreset(
            name=name,
            description="test preset",
            steps=[PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"})],
            category="User",
            is_builtin=False,
        )
        manager._presets[name] = preset
        return preset

    def test_duplicate_preset_returns_new_preset_with_copy_suffix(self, tmp_path):
        """duplicate_preset returns a new TransformPreset with " (Copy)" suffix."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "Original")

        copy = manager.duplicate_preset("Original")
        assert copy is not None
        assert copy.name == "Original (Copy)"
        assert copy.is_builtin is False

    def test_duplicate_preset_increments_counter_on_collision(self, tmp_path):
        """When "Name (Copy)" exists, duplicate uses "Name (Copy 2)"."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "Original")
        manager.duplicate_preset("Original")  # creates "Original (Copy)"

        second_copy = manager.duplicate_preset("Original")
        assert second_copy is not None
        assert second_copy.name == "Original (Copy 2)"

    def test_duplicate_preset_with_explicit_new_name(self, tmp_path):
        """When new_name is given, it's used directly instead of auto-suffix."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "Source")

        copy = manager.duplicate_preset("Source", new_name="Custom Copy")
        assert copy is not None
        assert copy.name == "Custom Copy"

    def test_duplicate_preset_returns_none_for_unknown_name(self, tmp_path):
        """duplicate_preset returns None when the source preset doesn't exist."""
        manager = PresetManager(presets_dir=tmp_path)
        assert manager.duplicate_preset("NotARealPreset") is None

    def test_rename_preset_succeeds_for_user_preset(self, tmp_path):
        """rename_preset on a user (non-builtin) preset succeeds."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "OldName")

        result = manager.rename_preset("OldName", "NewName")
        assert result is True
        assert "NewName" in manager._presets
        assert "OldName" not in manager._presets

    def test_rename_preset_fails_for_builtin_preset(self, tmp_path):
        """Builtins cannot be renamed — rename returns False, preset unchanged."""
        manager = PresetManager(presets_dir=tmp_path)
        # Built-in presets are loaded in __init__; pick the first one we find
        builtin = next(
            (p for p in manager._presets.values() if p.is_builtin),
            None,
        )
        assert builtin is not None, "Expected at least one builtin preset"

        original_name = builtin.name
        result = manager.rename_preset(original_name, "AttemptedRename")
        assert result is False
        assert original_name in manager._presets

    def test_rename_preset_fails_on_name_collision(self, tmp_path):
        """rename_preset returns False when target name already exists."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "First")
        self._make_user_preset(manager, "Second")

        result = manager.rename_preset("First", "Second")
        assert result is False

    def test_export_import_preset_roundtrip(self, tmp_path):
        """Exporting then importing a preset produces an equivalent preset."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "RoundtripTest")

        export_path = tmp_path / "export.json"
        ok = manager.export_preset("RoundtripTest", export_path)
        assert ok is True
        assert export_path.exists()

        # Import into a fresh manager
        manager2 = PresetManager(presets_dir=tmp_path / "fresh")
        imported = manager2.import_preset(export_path)
        assert imported is not None
        assert imported.description == "test preset"
        assert imported.is_builtin is False

    def test_import_preset_handles_name_conflict_with_counter(self, tmp_path):
        """Importing a preset whose name collides appends " (1)", " (2)", etc."""
        manager = PresetManager(presets_dir=tmp_path)
        self._make_user_preset(manager, "Conflicted")

        # Export, then re-import to force a name conflict
        export_path = tmp_path / "export.json"
        manager.export_preset("Conflicted", export_path)

        re_imported = manager.import_preset(export_path)
        assert re_imported is not None
        assert re_imported.name == "Conflicted (1)"

    def test_get_categories_returns_sorted_unique(self, tmp_path):
        """get_categories returns the unique set of category names, sorted."""
        manager = PresetManager(presets_dir=tmp_path)
        # Builtin presets cover Developer / General / Writing already; just verify shape
        categories = manager.get_categories()
        assert categories == sorted(set(categories))
        assert len(categories) >= 1


# ═════════════════════════════════════════════════════════════════════════════
# 5. core/folder_watcher.py — 8 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestFolderWatcherGapFill:
    """Gap-fill tests for FolderWatcher. Closes mutmut update_rule/remove_rule gaps."""

    def _make_rule(self, tmp_path: Path, rule_id: str = "rule1", enabled: bool = False) -> WatchRule:
        """Construct a WatchRule pointed at real folders so add_rule validates them."""
        in_folder = tmp_path / f"in_{rule_id}"
        out_folder = tmp_path / f"out_{rule_id}"
        in_folder.mkdir(exist_ok=True)
        out_folder.mkdir(exist_ok=True)
        return WatchRule(
            id=rule_id,
            input_folder=in_folder,
            output_folder=out_folder,
            file_patterns=["*.txt"],
            enabled=enabled,
        )

    def test_watch_rule_matches_file_with_glob_pattern(self, tmp_path):
        """WatchRule.matches_file uses fnmatch against the patterns."""
        rule = self._make_rule(tmp_path)
        # file_patterns is ["*.txt"]
        assert rule.matches_file(Path("report.txt")) is True
        assert rule.matches_file(Path("report.md")) is False

    def test_watch_rule_to_dict_from_dict_roundtrip(self, tmp_path):
        """WatchRule survives serialization/deserialization."""
        rule = self._make_rule(tmp_path, rule_id="r1")
        as_dict = rule.to_dict()
        restored = WatchRule.from_dict(as_dict)
        assert restored.id == rule.id
        assert str(restored.input_folder) == str(rule.input_folder)
        assert restored.file_patterns == rule.file_patterns

    def test_remove_rule_returns_false_for_unknown_id(self, tmp_path):
        """remove_rule on a non-existent rule_id returns False (mutmut finding)."""
        watcher = FolderWatcher()
        assert watcher.remove_rule("never-existed") is False

    def test_remove_rule_returns_true_after_adding(self, tmp_path):
        """remove_rule returns True and removes the rule from internal storage."""
        watcher = FolderWatcher()
        rule = self._make_rule(tmp_path, rule_id="to-remove")
        assert watcher.add_rule(rule) is True
        assert watcher.remove_rule("to-remove") is True
        assert "to-remove" not in watcher._rules

    def test_update_rule_returns_false_for_unknown_id(self, tmp_path):
        """update_rule on a non-existent rule_id returns False (mutmut finding)."""
        watcher = FolderWatcher()
        ghost_rule = self._make_rule(tmp_path, rule_id="ghost")
        assert watcher.update_rule(ghost_rule) is False

    def test_update_rule_replaces_existing_rule_data(self, tmp_path):
        """update_rule replaces the stored WatchRule with the new instance."""
        watcher = FolderWatcher()
        original = self._make_rule(tmp_path, rule_id="updateme")
        watcher.add_rule(original)

        updated = self._make_rule(tmp_path, rule_id="updateme")
        updated.file_patterns = ["*.md"]
        assert watcher.update_rule(updated) is True
        assert watcher._rules["updateme"].file_patterns == ["*.md"]

    def test_get_rule_returns_none_for_unknown_id(self, tmp_path):
        """get_rule returns None when the requested rule doesn't exist."""
        watcher = FolderWatcher()
        assert watcher.get_rule("not-there") is None

    def test_get_rules_returns_list_of_all_rules(self, tmp_path):
        """get_rules returns a list copy (mutation-safe) of internal rules."""
        watcher = FolderWatcher()
        watcher.add_rule(self._make_rule(tmp_path, rule_id="a"))
        watcher.add_rule(self._make_rule(tmp_path, rule_id="b"))

        rules = watcher.get_rules()
        assert len(rules) == 2
        ids = sorted(r.id for r in rules)
        assert ids == ["a", "b"]


# ═════════════════════════════════════════════════════════════════════════════
# 6. core/export_manager.py — 6 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestExportManagerGapFill:
    """Gap-fill tests for ExportManager — DOCX path, format detection."""

    def _opts(self, fmt: ExportFormat, **overrides) -> ExportOptions:
        defaults = dict(
            format=fmt,
            font_family="Arial",
            font_size=11,
            include_metadata=False,
            include_line_numbers=False,
            page_title="Test Export",
            html_dark_theme=False,
        )
        defaults.update(overrides)
        return ExportOptions(**defaults)

    def test_export_docx_writes_valid_word_doc_and_roundtrips(self, tmp_path):
        """_export_docx generates a .docx; reading it back recovers the text."""
        docx = pytest.importorskip("docx")
        em = ExportManager()
        path = tmp_path / "out.docx"
        em.export("First line\nSecond line\nThird line", path, self._opts(ExportFormat.DOCX))

        assert path.exists()
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs]
        assert "First line" in paragraphs
        assert "Second line" in paragraphs
        assert "Third line" in paragraphs

    def test_export_docx_with_metadata_sets_doc_properties(self, tmp_path):
        """include_metadata=True populates core_properties.title and .author."""
        docx = pytest.importorskip("docx")
        em = ExportManager()
        path = tmp_path / "out.docx"
        em.export(
            "Body text",
            path,
            self._opts(ExportFormat.DOCX, include_metadata=True, page_title="Custom Title"),
        )

        doc = docx.Document(str(path))
        assert doc.core_properties.title == "Custom Title"
        assert doc.core_properties.author == "RNV Text Transformer"

    def test_export_docx_with_line_numbers_prepends_index(self, tmp_path):
        """include_line_numbers=True produces "N | text" formatted paragraphs."""
        docx = pytest.importorskip("docx")
        em = ExportManager()
        path = tmp_path / "out.docx"
        em.export(
            "alpha\nbeta\ngamma",
            path,
            self._opts(ExportFormat.DOCX, include_line_numbers=True),
        )

        doc = docx.Document(str(path))
        texts = [p.text for p in doc.paragraphs]
        # The first body paragraph should start with "1 | alpha" (padded width=1)
        body_lines = [t for t in texts if "|" in t]
        assert len(body_lines) >= 3
        assert "alpha" in body_lines[0]

    def test_get_format_from_extension_for_known_extensions(self):
        """get_format_from_extension maps .docx, .pdf, .html, etc. correctly."""
        assert ExportManager.get_format_from_extension(".docx") == ExportFormat.DOCX
        assert ExportManager.get_format_from_extension(".html") == ExportFormat.HTML
        assert ExportManager.get_format_from_extension(".md") == ExportFormat.MARKDOWN

    def test_get_format_from_extension_returns_none_for_unknown(self):
        """get_format_from_extension returns None for an unknown extension."""
        assert ExportManager.get_format_from_extension(".xyz") is None

    def test_check_format_dependencies_for_txt_returns_ok(self):
        """TXT export has no optional dependencies; should report OK."""
        ok, _msg = ExportManager.check_format_dependencies(ExportFormat.TXT)
        assert ok is True


# ═════════════════════════════════════════════════════════════════════════════
# 7. core/theme_manager.py — 4 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestThemeManagerGapFill:
    """Gap-fill tests for ThemeManager — closes mutmut image-mode branch finding."""

    def test_cycle_theme_image_to_dark_when_image_mode_available(self, qapp):
        """When image mode is active and image-mode is available, cycle goes image→dark."""
        tm = ThemeManager()
        tm.image_mode_available = True  # force the branch
        tm.image_mode_active = True
        tm.current_theme = "image"

        new = tm.cycle_theme()
        assert new == "dark"
        assert tm.image_mode_active is False

    def test_cycle_theme_light_to_image_when_image_mode_available(self, qapp):
        """When image mode is available, cycle from light goes to image (not dark)."""
        tm = ThemeManager()
        tm.image_mode_available = True
        tm.image_mode_active = False
        tm.current_theme = "light"

        new = tm.cycle_theme()
        assert new == "image"
        assert tm.image_mode_active is True

    def test_get_theme_display_name_returns_image_mode_label(self, qapp):
        """get_theme_display_name maps 'image' to 'Image Mode' (mutmut finding)."""
        tm = ThemeManager()
        tm.current_theme = "image"
        assert tm.get_theme_display_name() == "Image Mode"

    def test_set_theme_to_explicit_value_updates_current(self, qapp):
        """set_theme directly sets the current theme to the given value."""
        tm = ThemeManager()
        result = tm.set_theme("dark")
        # set_theme returns a bool indicating success; the theme state matters more
        assert tm.current_theme == "dark"
        # call it again with the other value to confirm it toggles
        tm.set_theme("light")
        assert tm.current_theme == "light"


# ═════════════════════════════════════════════════════════════════════════════
# 8. Extension tests — additional coverage for under-tested surfaces
# ═════════════════════════════════════════════════════════════════════════════
#
# These tests close the gaps identified after Phase 8a's first validation:
#   - PresetExecutor action types (REPLACE, REGEX_REPLACE, SPLIT, JOIN,
#     WRAP, PREFIX, SUFFIX, TRIM_LINES) — biggest single uncovered block
#   - dialog_helper.ask_yes_no_cancel / ask_retry_cancel / show_about
#   - error_handler.ErrorContext entry/exit, exception suppression
#   - theme_manager._load_background_image, colors, detect_image_resources
#   - export_manager dependency / filter helpers
#   - preset_manager.get_shortcuts and edge cases


class TestPresetExecutorActions:
    """Cover all PresetExecutor.execute_step action types."""

    def _executor(self):
        from core.preset_manager import PresetExecutor
        return PresetExecutor()

    def test_execute_step_replace_case_sensitive(self):
        """REPLACE action substitutes literal string (case sensitive)."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.REPLACE,
            params={"find": "world", "replace": "earth", "case_sensitive": True},
        )
        assert executor.execute_step("hello world", step) == "hello earth"
        # case-sensitive: "World" should NOT match
        assert executor.execute_step("hello World", step) == "hello World"

    def test_execute_step_replace_case_insensitive(self):
        """REPLACE action with case_sensitive=False matches all case variants."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.REPLACE,
            params={"find": "world", "replace": "earth", "case_sensitive": False},
        )
        result = executor.execute_step("Hello World, hello WORLD", step)
        assert result == "Hello earth, hello earth"

    def test_execute_step_regex_replace_pattern_substitution(self):
        """REGEX_REPLACE applies re.sub with the given pattern."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.REGEX_REPLACE,
            params={"pattern": r"\d+", "replacement": "N"},
        )
        assert executor.execute_step("foo 123 bar 456", step) == "foo N bar N"

    def test_execute_step_regex_replace_invalid_pattern_returns_unchanged(self):
        """REGEX_REPLACE with invalid pattern returns text unchanged (logs warning)."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.REGEX_REPLACE,
            params={"pattern": r"[invalid(", "replacement": "X"},
        )
        # Invalid regex shouldn't raise — should return original text
        assert executor.execute_step("input text", step) == "input text"

    def test_execute_step_split_joins_with_newlines(self):
        """SPLIT splits on the delimiter and joins with newlines."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.SPLIT,
            params={"delimiter": ","},
        )
        assert executor.execute_step("a,b,c", step) == "a\nb\nc"

    def test_execute_step_join_concatenates_lines_with_delimiter(self):
        """JOIN reverses split, joining lines with the given delimiter."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.JOIN,
            params={"delimiter": " | "},
        )
        assert executor.execute_step("a\nb\nc", step) == "a | b | c"

    def test_execute_step_wrap_at_specified_width(self):
        """WRAP uses textwrap.fill to wrap at the given width."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.WRAP,
            params={"width": 10},
        )
        result = executor.execute_step("this is a longer sentence that needs wrapping", step)
        # Every line should be <= 10 chars
        assert all(len(line) <= 10 for line in result.splitlines())

    def test_execute_step_prefix_adds_text_to_start(self):
        """PREFIX with per_line=False adds the prefix once to the start."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.PREFIX,
            params={"text": ">> ", "per_line": False},
        )
        assert executor.execute_step("a\nb\nc", step) == ">> a\nb\nc"

    def test_execute_step_prefix_per_line(self):
        """PREFIX with per_line=True prepends to every line."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.PREFIX,
            params={"text": "> ", "per_line": True},
        )
        assert executor.execute_step("alpha\nbeta\ngamma", step) == "> alpha\n> beta\n> gamma"

    def test_execute_step_suffix_per_line(self):
        """SUFFIX with per_line=True appends to every line."""
        executor = self._executor()
        step = PresetStep(
            action=ActionType.SUFFIX,
            params={"text": ".", "per_line": True},
        )
        assert executor.execute_step("alpha\nbeta", step) == "alpha.\nbeta."

    def test_execute_step_trim_lines_strips_each_line(self):
        """TRIM_LINES strips whitespace from each line individually."""
        executor = self._executor()
        step = PresetStep(action=ActionType.TRIM_LINES, params={})
        assert executor.execute_step("  hello  \n  world  ", step) == "hello\nworld"


class TestDialogHelperExtended:
    """Cover ask_yes_no_cancel, ask_retry_cancel, show_about."""

    def test_ask_yes_no_cancel_returns_yes_on_yes_button(self, qapp):
        """ask_yes_no_cancel maps QMessageBox.Yes to DialogResult.YES."""
        from utils.dialog_helper import DialogHelper, DialogResult
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
            assert DialogHelper.ask_yes_no_cancel("T", "M") == DialogResult.YES

    def test_ask_yes_no_cancel_returns_no_on_no_button(self, qapp):
        """ask_yes_no_cancel maps QMessageBox.No to DialogResult.NO."""
        from utils.dialog_helper import DialogHelper, DialogResult
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No):
            assert DialogHelper.ask_yes_no_cancel("T", "M") == DialogResult.NO

    def test_ask_yes_no_cancel_returns_cancel_on_cancel_button(self, qapp):
        """ask_yes_no_cancel maps QMessageBox.Cancel to DialogResult.CANCEL."""
        from utils.dialog_helper import DialogHelper, DialogResult
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Cancel):
            assert DialogHelper.ask_yes_no_cancel("T", "M") == DialogResult.CANCEL

    def test_ask_retry_cancel_returns_retry(self, qapp):
        """ask_retry_cancel maps QMessageBox.Retry to DialogResult.RETRY."""
        from utils.dialog_helper import DialogHelper, DialogResult
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Retry):
            assert DialogHelper.ask_retry_cancel("Conn", "Try again?") == DialogResult.RETRY

    def test_ask_retry_cancel_returns_cancel(self, qapp):
        """ask_retry_cancel maps non-Retry exec result to DialogResult.CANCEL."""
        from utils.dialog_helper import DialogHelper, DialogResult
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Cancel):
            assert DialogHelper.ask_retry_cancel("Conn", "Try again?") == DialogResult.CANCEL

    def test_show_about_invokes_messagebox_about(self, qapp):
        """show_about delegates to QMessageBox.about (static)."""
        from utils.dialog_helper import DialogHelper
        from PyQt6.QtWidgets import QMessageBox
        with patch.object(QMessageBox, "about") as about_mock:
            DialogHelper.show_about("About App", "<h3>App</h3><p>Version 1.0</p>")
            about_mock.assert_called_once()
            # Confirm message arg was passed through
            args = about_mock.call_args[0]
            assert "App" in args[1] or "App" in args[2]


class TestErrorContextExtended:
    """Cover ErrorContext entry, exit, exception suppression."""

    def test_error_context_no_exception_marks_success(self):
        """When the with block completes without raising, context.success stays True."""
        with ErrorContext("doing thing") as ctx:
            value = 1 + 1
        assert ctx.success is True
        assert ctx.error is None

    def test_error_context_exception_marks_failure_and_suppresses(self):
        """By default (reraise=False), ErrorContext swallows the exception."""
        with ErrorContext("doing risky thing") as ctx:
            raise ValueError("intentional")
        # No exception escapes
        assert ctx.success is False
        assert isinstance(ctx.error, ValueError)

    def test_error_context_reraise_propagates_exception(self):
        """With reraise=True, the exception escapes the with block."""
        with pytest.raises(RuntimeError, match="must propagate"):
            with ErrorContext("doing thing", reraise=True) as ctx:
                raise RuntimeError("must propagate")

    def test_error_context_invokes_status_callback_on_exception(self):
        """status_callback is invoked when an exception is handled."""
        captured = []
        def status_callback(msg: str) -> None:
            captured.append(msg)

        with ErrorContext("doing thing", status_callback=status_callback) as ctx:
            raise ValueError("test")

        # handle_exception calls the status_callback at least once
        assert len(captured) >= 1
        assert ctx.success is False


class TestThemeManagerExtended:
    """Cover image loading, colors property, detect_image_resources."""

    def test_colors_property_returns_dict_from_dialog_style_manager(self, qapp):
        """ThemeManager.colors delegates to DialogStyleManager.get_colors."""
        tm = ThemeManager()
        tm.current_theme = "dark"
        colors = tm.colors
        assert isinstance(colors, dict)
        # All themes should expose at least these keys
        assert "accent" in colors or "background" in colors or len(colors) > 5

    def test_detect_image_resources_returns_false_with_no_images(self, qapp, tmp_path, monkeypatch):
        """detect_image_resources returns False when no background or buttons present."""
        # Point image directories at a clean tmp_path
        from core import theme_manager as tm_module
        monkeypatch.setattr(tm_module, "BACKGROUND_IMAGES_DIR", tmp_path / "bg")
        monkeypatch.setattr(tm_module, "BUTTON_IMAGES_DIR", tmp_path / "btn")
        (tmp_path / "bg").mkdir()
        (tmp_path / "btn").mkdir()

        tm = ThemeManager()
        result = tm.detect_image_resources()
        assert result is False
        assert tm.image_mode_available is False

    def test_load_background_image_returns_false_for_missing_file(self, qapp, tmp_path):
        """_load_background_image returns False when the path doesn't exist."""
        tm = ThemeManager()
        result = tm._load_background_image(tmp_path / "does_not_exist.png")
        assert result is False

    def test_set_theme_rejects_image_when_not_available(self, qapp):
        """set_theme('image') returns False if image_mode_available is False."""
        tm = ThemeManager()
        tm.image_mode_available = False
        assert tm.set_theme("image") is False

    def test_set_theme_rejects_unknown_value(self, qapp):
        """set_theme with an unknown theme name returns False, doesn't mutate state."""
        tm = ThemeManager()
        tm.current_theme = "dark"
        assert tm.set_theme("rainbow") is False
        assert tm.current_theme == "dark"


class TestExportManagerExtended:
    """Cover format/filter helpers and dependency check edge cases."""

    def test_check_format_dependencies_for_docx_returns_ok_when_installed(self):
        """When python-docx is installed (it is in requirements-dev), DOCX is OK."""
        docx = pytest.importorskip("docx")
        ok, _msg = ExportManager.check_format_dependencies(ExportFormat.DOCX)
        assert ok is True

    def test_get_file_filter_returns_string_with_all_formats(self):
        """get_file_filter returns a non-empty string covering at least TXT and HTML."""
        result = ExportManager.get_file_filter()
        assert isinstance(result, str)
        assert "txt" in result.lower() or "TXT" in result
        assert "html" in result.lower() or "HTML" in result

    def test_get_available_formats_returns_non_empty_list(self):
        """get_available_formats lists at least the always-on formats."""
        result = ExportManager.get_available_formats()
        assert isinstance(result, list)
        # TXT and HTML never depend on optional packages
        assert ExportFormat.TXT in result
        assert ExportFormat.HTML in result


class TestPresetManagerExtended:
    """Cover get_shortcuts and remaining helper paths."""

    def test_get_shortcuts_returns_mapping_for_user_presets(self, tmp_path):
        """get_shortcuts returns {shortcut: name} for presets with keyboard_shortcut set."""
        manager = PresetManager(presets_dir=tmp_path)
        preset = TransformPreset(
            name="Shortcut Preset",
            description="has shortcut",
            steps=[PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"})],
            category="User",
            is_builtin=False,
            keyboard_shortcut="Ctrl+Shift+U",
        )
        manager._presets["Shortcut Preset"] = preset

        shortcuts = manager.get_shortcuts()
        assert "Ctrl+Shift+U" in shortcuts
        assert shortcuts["Ctrl+Shift+U"] == "Shortcut Preset"

    def test_get_shortcuts_skips_presets_without_shortcut(self, tmp_path):
        """Presets with empty keyboard_shortcut are excluded from the mapping."""
        manager = PresetManager(presets_dir=tmp_path)
        # Builtins typically have empty keyboard_shortcut
        shortcuts = manager.get_shortcuts()
        for name in shortcuts.values():
            preset = manager._presets[name]
            assert preset.keyboard_shortcut  # non-empty

    def test_preview_preset_returns_transformed_text(self, tmp_path):
        """preview_preset runs the preset's transformation and returns result."""
        manager = PresetManager(presets_dir=tmp_path)
        preset = TransformPreset(
            name="Upper Preview",
            description="",
            steps=[PresetStep(action=ActionType.TRANSFORM, params={"mode": "UPPERCASE"})],
            category="User",
            is_builtin=False,
        )
        result = manager.preview_preset("hello", preset)
        assert result == "HELLO"


# ═════════════════════════════════════════════════════════════════════════════
# 9. Extension-2 — error paths and remaining uncovered branches
# ═════════════════════════════════════════════════════════════════════════════
#
# These tests target the highest-leverage remaining gaps after extension-1:
#   - file_handler error paths (directory, oversized, corrupt docx, encrypted pdf,
#     empty pdf, rtf with bad bytes, write logger error)
#   - error_handler.handle_exception with status_callback, safe_execute reraise/silent,
#     try_or_default with log_error=True
#   - export_manager._export_pdf real round-trip (closes the 75-line gap at 307-383)
#   - folder_watcher.start/stop, is_running, get_rules thread-safety


class TestFileHandlerErrorPaths:
    """Cover the error / fallback paths in FileHandler."""

    def test_read_file_content_directory_raises_not_regular_file(self, tmp_path):
        """Pointing at a directory raises FileReadError with 'not a regular file'."""
        # tmp_path is itself a directory
        with pytest.raises(FileReadError, match="(?i)not a regular file|directory"):
            FileHandler.read_file_content(tmp_path)

    def test_read_file_content_oversized_raises(self, tmp_path, monkeypatch):
        """File above MAX_FILE_SIZE raises FileReadError with 'too large'."""
        from utils import file_handler as fh_module
        # Drop the limit to 100 bytes for the test
        monkeypatch.setattr(fh_module, "MAX_FILE_SIZE", 100)

        big = tmp_path / "big.txt"
        big.write_bytes(b"x" * 500)
        with pytest.raises(FileReadError, match="(?i)too large"):
            FileHandler.read_file_content(big)

    def test_read_docx_corrupted_raises_filereaderror(self, tmp_path):
        """A .docx that isn't actually a zip raises a friendly FileReadError."""
        pytest.importorskip("docx")
        bogus = tmp_path / "bogus.docx"
        bogus.write_text("This is plain text, not a real docx", encoding="utf-8")
        with pytest.raises(FileReadError):
            FileHandler.read_file_content(bogus)

    def test_read_pdf_empty_or_text_less_raises(self, tmp_path):
        """A PDF with no extractable text raises FileReadError with the right hint."""
        pytest.importorskip("pypdf")
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not available to generate empty PDF")

        empty_pdf = tmp_path / "empty.pdf"
        c = canvas.Canvas(str(empty_pdf))
        # No drawString call — page is empty
        c.showPage()
        c.save()

        with pytest.raises(FileReadError, match="(?i)no extractable text|scanned"):
            FileHandler.read_file_content(empty_pdf)

    def test_read_pdf_corrupted_raises_filereaderror(self, tmp_path):
        """A file with .pdf extension but garbage bytes raises FileReadError."""
        pytest.importorskip("pypdf")
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"not a real pdf, just text bytes")
        with pytest.raises(FileReadError):
            FileHandler.read_file_content(fake_pdf)


class TestErrorHandlerEdgeCases:
    """Cover handle_exception status_callback, safe_execute reraise/silent."""

    def test_handle_exception_invokes_status_callback(self):
        """handle_exception calls status_callback with the user-facing message."""
        captured = []
        def cb(msg: str) -> None:
            captured.append(msg)

        ErrorHandler.handle_exception(
            RuntimeError("oh no"),
            "loading thing",
            status_callback=cb,
        )
        # status_callback fires with the auto-generated message
        assert len(captured) == 1
        assert "loading thing" in captured[0].lower() or "failed" in captured[0].lower()

    def test_handle_exception_uses_custom_user_message(self):
        """user_message overrides the auto-generated message."""
        captured = []
        ErrorHandler.handle_exception(
            ValueError("bad input"),
            "parsing",
            status_callback=captured.append,
            user_message="The file appears damaged.",
        )
        assert captured == ["The file appears damaged."]

    def test_handle_exception_survives_callback_failure(self):
        """If status_callback raises, handle_exception still returns cleanly."""
        def bad_cb(msg: str) -> None:
            raise RuntimeError("callback broken")

        # Should NOT propagate the callback's exception
        ErrorHandler.handle_exception(
            ValueError("input"),
            "test",
            status_callback=bad_cb,
        )  # No exception expected

    def test_safe_execute_silent_skips_logging(self):
        """silent=True skips the error log but still returns fallback."""
        result = ErrorHandler.safe_execute(
            lambda: 1 / 0,
            "division",
            fallback_value="quiet fallback",
            silent=True,
        )
        assert result == "quiet fallback"

    def test_safe_execute_reraise_propagates(self):
        """reraise=True propagates the exception after handling."""
        with pytest.raises(ValueError, match="must propagate"):
            ErrorHandler.safe_execute(
                lambda: (_ for _ in ()).throw(ValueError("must propagate")),
                "test",
                reraise=True,
            )

    def test_try_or_default_with_log_error_path(self):
        """try_or_default(log_error=True) takes the warning-log branch on failure."""
        result = ErrorHandler.try_or_default(
            lambda: int("not a number"),
            default=42,
            log_error=True,
        )
        assert result == 42


class TestExportManagerPDFAndHelpers:
    """PDF round-trip + format helper edge cases (largest remaining gap)."""

    def _opts(self, fmt: ExportFormat, **overrides) -> ExportOptions:
        defaults = dict(
            format=fmt,
            font_family="Arial",
            font_size=11,
            include_metadata=False,
            include_line_numbers=False,
            page_title="Test Export",
            html_dark_theme=False,
        )
        defaults.update(overrides)
        return ExportOptions(**defaults)

    def test_export_pdf_writes_valid_pdf_with_content(self, tmp_path):
        """_export_pdf produces a real PDF; pypdf reads it back with content present."""
        pytest.importorskip("reportlab")
        pypdf = pytest.importorskip("pypdf")

        em = ExportManager()
        path = tmp_path / "out.pdf"
        em.export(
            "Sample line one\nSample line two\nSample line three",
            path,
            self._opts(ExportFormat.PDF, page_title="My Report"),
        )

        assert path.exists()
        reader = pypdf.PdfReader(str(path))
        extracted = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert "Sample line" in extracted

    def test_export_pdf_with_line_numbers(self, tmp_path):
        """_export_pdf with include_line_numbers=True prepends the line index."""
        pytest.importorskip("reportlab")
        pypdf = pytest.importorskip("pypdf")

        em = ExportManager()
        path = tmp_path / "out_nums.pdf"
        em.export(
            "alpha\nbeta\ngamma",
            path,
            self._opts(ExportFormat.PDF, include_line_numbers=True),
        )

        reader = pypdf.PdfReader(str(path))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        # Line-number prefix format is "N | text"
        assert "|" in text

    def test_export_pdf_with_metadata_footer(self, tmp_path):
        """_export_pdf with include_metadata=True appends the generator footer."""
        pytest.importorskip("reportlab")
        pypdf = pytest.importorskip("pypdf")

        em = ExportManager()
        path = tmp_path / "out_meta.pdf"
        em.export(
            "Body content here",
            path,
            self._opts(ExportFormat.PDF, include_metadata=True),
        )

        reader = pypdf.PdfReader(str(path))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert "RNV Text Transformer" in text

    def test_export_pdf_long_content_multi_page(self, tmp_path):
        """Long content forces a multi-page PDF; we just verify it doesn't crash."""
        pytest.importorskip("reportlab")
        pypdf = pytest.importorskip("pypdf")

        em = ExportManager()
        path = tmp_path / "out_long.pdf"
        # 500 lines of text — definitely multi-page at 11pt
        long_text = "\n".join(f"Line {i} of the long document" for i in range(500))
        em.export(long_text, path, self._opts(ExportFormat.PDF))

        reader = pypdf.PdfReader(str(path))
        assert len(reader.pages) >= 2


class TestFolderWatcherStartStop:
    """Cover start/stop/is_running and unavailable-watchdog paths."""

    def _make_rule(self, tmp_path: Path, rule_id: str = "r1", enabled: bool = True) -> WatchRule:
        in_folder = tmp_path / f"in_{rule_id}"
        out_folder = tmp_path / f"out_{rule_id}"
        in_folder.mkdir(exist_ok=True)
        out_folder.mkdir(exist_ok=True)
        return WatchRule(
            id=rule_id,
            input_folder=in_folder,
            output_folder=out_folder,
            file_patterns=["*.txt"],
            enabled=enabled,
        )

    def test_is_running_false_before_start(self):
        """is_running returns False on a fresh watcher."""
        watcher = FolderWatcher()
        assert watcher.is_running() is False

    def test_start_then_stop_toggles_is_running(self, tmp_path):
        """start() flips is_running to True; stop() flips it back to False."""
        pytest.importorskip("watchdog")
        watcher = FolderWatcher()
        rule = self._make_rule(tmp_path)
        watcher.add_rule(rule)

        assert watcher.start() is True
        assert watcher.is_running() is True

        watcher.stop()
        assert watcher.is_running() is False

    def test_start_twice_returns_true_idempotent(self, tmp_path):
        """Calling start() twice is idempotent — second call returns True without crash."""
        pytest.importorskip("watchdog")
        watcher = FolderWatcher()
        watcher.add_rule(self._make_rule(tmp_path))

        try:
            assert watcher.start() is True
            assert watcher.start() is True  # idempotent
        finally:
            watcher.stop()

    def test_add_rule_with_nonexistent_input_folder_returns_false(self, tmp_path):
        """add_rule rejects rules whose input_folder does not exist."""
        pytest.importorskip("watchdog")
        watcher = FolderWatcher()
        # Make a rule, then DELETE the input folder before adding
        rule = self._make_rule(tmp_path, rule_id="ghost")
        import shutil
        shutil.rmtree(rule.input_folder)

        assert watcher.add_rule(rule) is False
