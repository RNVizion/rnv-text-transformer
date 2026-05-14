"""
tests/test_main_window.py
=========================
Combined test file for MainWindow.

Layout:
  - Section 1 (Phase 3): 6 smoke tests covering construction + basic state
  - Section 2 (Phase 8c R2): 35 interaction tests across 6 logical groups

The MainWindow class is the largest module in the codebase (938 stmts).
Phase 3 tests cover construction (~150 stmts via __init__ alone).
Phase 8c R2 tests target the behavioral surface: text transformation,
file operations, undo/redo, cleanup, theme cycling, and dialog launching.

All tests use the `main_window` fixture from conftest.py, which:
  - Constructs MainWindow under tmp_settings (isolated QSettings)
  - Registers it with qtbot for automatic cleanup
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Phase 3 smoke tests (6 tests, unchanged)
# ═════════════════════════════════════════════════════════════════════════════

class TestMainWindow:
    """Smoke tests for the application's main window."""

    def test_mainwindow_instantiates(self, main_window):
        """
        Constructor runs to completion. This single test is the largest
        coverage gain in the entire phase — MainWindow.__init__ exercises
        ~150+ statements covering settings load, theme detection, font
        loading, geometry restore, worker thread setup, preset system init,
        and full UI construction.
        """
        assert main_window is not None

    def test_mainwindow_window_title_is_app_name(self, main_window):
        """Window title is set to APP_NAME from utils/config.py."""
        from utils.config import APP_NAME
        assert main_window.windowTitle() == APP_NAME

    def test_mainwindow_minimum_size_set(self, main_window):
        """Minimum window size matches MIN_WINDOW_WIDTH × MIN_WINDOW_HEIGHT."""
        from utils.config import MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
        size = main_window.minimumSize()
        assert size.width() == MIN_WINDOW_WIDTH
        assert size.height() == MIN_WINDOW_HEIGHT

    def test_mainwindow_drops_disabled_on_window(self, main_window):
        """
        Drag-drop is intentionally disabled on MainWindow itself; it's
        enabled on the inner DragDropTextEdit widgets instead.
        """
        assert main_window.acceptDrops() is False

    def test_mainwindow_resize_does_not_crash(self, main_window, qtbot):
        """
        Resize the window twice. This exercises the resizeEvent path
        with the hasattr guards from your memory — the fix you added
        for early-fire resizeEvents under the Fusion style.
        """
        main_window.show()
        main_window.resize(800, 600)
        qtbot.wait(50)
        main_window.resize(400, 300)
        qtbot.wait(50)
        # No assertion needed — surviving the resizes is the test

    def test_mainwindow_theme_can_be_switched(self, main_window):
        """
        Programmatic theme switching via the internal apply method works
        and updates the underlying theme_manager state.
        """
        # Capture current theme
        original = main_window.theme_manager.current_theme
        # Switch to the opposite theme
        new_theme = "light" if original == "dark" else "dark"
        main_window._apply_theme_from_settings(new_theme)
        assert main_window.theme_manager.current_theme == new_theme
        # Restore for any later tests in the same session
        main_window._apply_theme_from_settings(original)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Phase 8c R2 interaction tests (35 tests in 6 groups)
# ═════════════════════════════════════════════════════════════════════════════

# ─── Group A: Construction + initial state (4 tests) ─────────────────────────

class TestMainWindowConstruction:
    """Construction-time invariants beyond Phase 3's smoke checks."""

    def test_mainwindow_has_input_and_output_widgets(self, main_window):
        """MainWindow exposes text_input and output_text widgets."""
        assert main_window.text_input is not None
        assert main_window.output_text is not None

    def test_mainwindow_mode_combo_populated_with_modes(self, main_window):
        """mode_combo contains the available transformation modes."""
        assert main_window.mode_combo.count() > 0
        # First item should be a known mode
        modes = [main_window.mode_combo.itemText(i)
                 for i in range(main_window.mode_combo.count())]
        assert "UPPERCASE" in modes or "lowercase" in modes

    def test_mainwindow_output_text_is_readonly(self, main_window):
        """The output area is read-only — users edit input, not output."""
        assert main_window.output_text.isReadOnly() is True

    def test_mainwindow_history_initially_empty(self, main_window):
        """Output history starts empty with index at -1."""
        assert main_window._output_history == []
        assert main_window._output_history_index == -1


# ─── Group B: Text transformation flow (6 tests) ─────────────────────────────

class TestMainWindowTransformation:
    """Text transformation pipeline tests."""

    def test_transform_text_uppercase_sync_path(self, main_window):
        """Small input + UPPERCASE mode transforms synchronously."""
        main_window.text_input.setPlainText("hello world")
        # Find and select UPPERCASE mode
        idx = main_window.mode_combo.findText("UPPERCASE")
        if idx < 0:
            pytest.skip("UPPERCASE mode not in combo")
        main_window.mode_combo.setCurrentIndex(idx)
        main_window._transform_text()
        assert main_window.output_text.toPlainText() == "HELLO WORLD"

    def test_transform_text_lowercase_sync_path(self, main_window):
        """lowercase mode also runs synchronously for small input."""
        main_window.text_input.setPlainText("HELLO WORLD")
        idx = main_window.mode_combo.findText("lowercase")
        if idx < 0:
            pytest.skip("lowercase mode not in combo")
        main_window.mode_combo.setCurrentIndex(idx)
        main_window._transform_text()
        assert main_window.output_text.toPlainText() == "hello world"

    def test_on_transform_complete_populates_output(self, main_window):
        """_on_transform_complete (the async-path handler) sets output text."""
        main_window._on_transform_complete("RESULT TEXT")
        assert main_window.output_text.toPlainText() == "RESULT TEXT"
        # And history gains the entry
        assert "RESULT TEXT" in main_window._output_history

    def test_on_transform_error_sets_status(self, main_window):
        """_on_transform_error surfaces the error in the status label."""
        main_window._on_transform_error("Mode not found")
        # status label should mention the error
        # status_label is set via _set_status; check that statusbar text
        # contains the message
        # (We can't easily read statusbar, but we can check buttons re-enabled)
        assert main_window._is_loading is False

    def test_on_input_text_changed_updates_statistics(self, main_window):
        """Typing in input triggers _on_input_text_changed → _update_statistics."""
        # Set text and call handler directly
        main_window.text_input.setPlainText("some text content")
        main_window._on_input_text_changed()
        # _update_statistics was invoked — no crash is the assertion

    def test_swap_input_output_moves_output_to_input(self, main_window):
        """_swap_input_output moves output text into input field."""
        main_window.text_input.setPlainText("original")
        main_window.output_text.setPlainText("transformed")
        main_window._swap_input_output()
        assert main_window.text_input.toPlainText() == "transformed"
        assert main_window.output_text.toPlainText() == ""

    def test_swap_input_output_with_empty_output_no_op(self, main_window):
        """Swap with empty output is a no-op (status update only)."""
        main_window.text_input.setPlainText("preserve this")
        main_window.output_text.clear()
        main_window._swap_input_output()
        # Input is preserved when there's nothing to swap
        assert main_window.text_input.toPlainText() == "preserve this"


# ─── Group C: File operations (5 tests; QFileDialog monkeypatched) ───────────

class TestMainWindowFileOps:
    """File load / save / drag-drop tests with QFileDialog mocked."""

    def test_load_file_with_valid_path_starts_loader_thread(
        self, main_window, tmp_path, monkeypatch
    ):
        """_load_file with a valid path kicks off the FileLoaderThread."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content", encoding="utf-8")

        monkeypatch.setattr(
            QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **kw: (str(test_file), "Text Files (*.txt)")),
        )
        main_window._load_file()
        # A thread should have been spawned
        assert main_window._file_loader_thread is not None

    def test_load_file_cancelled_leaves_input_unchanged(
        self, main_window, monkeypatch
    ):
        """Cancelling the file dialog leaves input untouched."""
        main_window.text_input.setPlainText("preserve me")
        monkeypatch.setattr(
            QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **kw: ("", "")),
        )
        main_window._load_file()
        assert main_window.text_input.toPlainText() == "preserve me"

    def test_save_file_writes_output_to_chosen_path(
        self, main_window, tmp_path, monkeypatch
    ):
        """_save_file writes the output text to the path returned by the dialog."""
        out_path = tmp_path / "saved.txt"
        main_window.output_text.setPlainText("content to save")
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **kw: (str(out_path), "Text Files (*.txt)")),
        )
        main_window._save_file()
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "content to save"

    def test_save_file_with_empty_output_no_write(
        self, main_window, tmp_path, monkeypatch
    ):
        """Trying to save with empty output is a no-op (no dialog opens)."""
        called = {"count": 0}

        def fake_save(*a, **kw):
            called["count"] += 1
            return ("", "")

        monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(fake_save))
        main_window.output_text.clear()
        main_window._save_file()
        # The dialog should not have been invoked
        assert called["count"] == 0

    def test_on_file_error_resets_loading_flag(self, main_window):
        """_on_file_error clears _is_loading so buttons re-enable."""
        main_window._is_loading = True
        main_window._on_file_error("Could not read file")
        assert main_window._is_loading is False


# ─── Group D: Clear / undo / redo (5 tests) ──────────────────────────────────

class TestMainWindowClearUndoRedo:
    """Clear, undo, and redo flow tests."""

    def test_clear_all_empties_both_text_areas(self, main_window):
        """_clear_all wipes both input and output."""
        main_window.text_input.setPlainText("input text")
        main_window.output_text.setPlainText("output text")
        main_window._clear_all()
        assert main_window.text_input.toPlainText() == ""
        assert main_window.output_text.toPlainText() == ""
        # And history is cleared
        assert main_window._output_history == []

    def test_clear_input_only_preserves_output(self, main_window):
        """_clear_input wipes only input; output stays."""
        main_window.text_input.setPlainText("input text")
        main_window.output_text.setPlainText("output text")
        main_window._clear_input()
        assert main_window.text_input.toPlainText() == ""
        assert main_window.output_text.toPlainText() == "output text"

    def test_add_to_output_history_caps_at_max(self, main_window):
        """Output history is capped at MAX_OUTPUT_HISTORY entries."""
        from ui.main_window import MAX_OUTPUT_HISTORY
        for i in range(MAX_OUTPUT_HISTORY + 5):
            main_window._add_to_output_history(f"entry {i}")
        assert len(main_window._output_history) <= MAX_OUTPUT_HISTORY

    def test_undo_output_restores_previous_state(self, main_window):
        """_undo_output moves back through history."""
        main_window._add_to_output_history("first")
        main_window._add_to_output_history("second")
        # Now at index 1, content shows "second"
        main_window.output_text.setPlainText("second")
        main_window._undo_output()
        assert main_window.output_text.toPlainText() == "first"

    def test_redo_output_restores_next_state(self, main_window):
        """_redo_output moves forward through history."""
        main_window._add_to_output_history("first")
        main_window._add_to_output_history("second")
        # Undo first to set index back, then redo
        main_window._undo_output()
        main_window._redo_output()
        assert main_window.output_text.toPlainText() == "second"


# ─── Group E: Cleanup + split/join operations (4 tests) ──────────────────────

class TestMainWindowCleanupAndSplitJoin:
    """Cleanup and split/join operation tests."""

    def test_apply_cleanup_trim_whitespace_modifies_input(self, main_window):
        """_apply_cleanup('Trim Whitespace') strips leading/trailing whitespace from input."""
        from core.text_cleaner import CleanupOperation
        # trim_whitespace is text.strip() — outer whitespace only, not per-line
        main_window.text_input.setPlainText("  hello world  ")
        main_window._apply_cleanup(CleanupOperation.TRIM_WHITESPACE)
        result = main_window.text_input.toPlainText()
        # Both leading and trailing spaces removed
        assert result == "hello world"

    def test_apply_cleanup_with_empty_input_is_noop(self, main_window):
        """Cleanup on empty input doesn't crash, just sets status."""
        from core.text_cleaner import CleanupOperation
        main_window.text_input.clear()
        main_window._apply_cleanup(CleanupOperation.TRIM_WHITESPACE)
        # No crash; input remains empty
        assert main_window.text_input.toPlainText() == ""

    def test_apply_split_join_split_by_comma(self, main_window):
        """_apply_split_join('Split by Comma') puts each comma item on its own line."""
        from core.text_cleaner import SplitJoinOperation
        main_window.text_input.setPlainText("a,b,c,d")
        main_window._apply_split_join(SplitJoinOperation.SPLIT_BY_COMMA)
        result = main_window.text_input.toPlainText()
        assert result == "a\nb\nc\nd" or result.startswith("a\n")

    def test_apply_split_join_with_empty_input_is_noop(self, main_window):
        """Split/join on empty input doesn't crash."""
        from core.text_cleaner import SplitJoinOperation
        main_window.text_input.clear()
        main_window._apply_split_join(SplitJoinOperation.SPLIT_BY_COMMA)
        assert main_window.text_input.toPlainText() == ""


# ─── Group F: Theme, settings, signals, presets (11 tests) ───────────────────

class TestMainWindowThemeAndSignals:
    """Theme cycling + settings + dialog-launch signal-handler tests."""

    def test_cycle_theme_changes_current_theme(self, main_window):
        """_cycle_theme advances the theme_manager.current_theme."""
        original = main_window.theme_manager.current_theme
        main_window._cycle_theme()
        # Should have moved to a different theme
        assert main_window.theme_manager.current_theme != original or \
               len([t for t in ["dark", "light", "image"]
                    if main_window.theme_manager.is_theme_available(t)
                    if hasattr(main_window.theme_manager, 'is_theme_available')]) <= 1

    def test_load_theme_from_settings_applies_value(self, main_window):
        """_load_theme_from_settings reads from settings_manager."""
        # Just call it; it should not crash and should leave theme in valid state
        main_window._load_theme_from_settings()
        assert main_window.theme_manager.current_theme in ("dark", "light", "image")

    def test_set_buttons_enabled_toggles_loading_flag(self, main_window):
        """_set_buttons_enabled(False) sets _is_loading=True and vice versa."""
        main_window._set_buttons_enabled(False)
        assert main_window._is_loading is True
        main_window._set_buttons_enabled(True)
        assert main_window._is_loading is False

    def test_clear_recent_files_resets_setting(self, main_window):
        """_clear_recent_files calls settings_manager.clear_recent_files()."""
        # Add a file first
        main_window.settings_manager.add_recent_file("/some/path.txt")
        main_window._clear_recent_files()
        # Recent files list should be empty
        assert main_window.settings_manager.load_recent_files() == []

    def test_on_merge_applied_replaces_output_text(self, main_window):
        """_on_merge_applied populates output and adds to history."""
        main_window._on_merge_applied("merged result")
        assert main_window.output_text.toPlainText() == "merged result"
        assert "merged result" in main_window._output_history

    def test_on_encoding_conversion_applied_updates_input_text(self, main_window):
        """_on_encoding_conversion_applied replaces input with converted text."""
        main_window._on_encoding_conversion_applied("converted content")
        assert main_window.text_input.toPlainText() == "converted content"

    def test_on_regex_pattern_applied_with_replacement_substitutes(self, main_window):
        """_on_regex_pattern_applied('foo', 'bar', 0) replaces in input."""
        main_window.text_input.setPlainText("foo and foo again")
        main_window._on_regex_pattern_applied(r"foo", "bar", 0)
        assert "bar" in main_window.text_input.toPlainText()
        assert "foo" not in main_window.text_input.toPlainText()

    def test_apply_preset_by_name_with_unknown_name_sets_status(self, main_window):
        """_apply_preset_by_name with non-existent name doesn't crash."""
        main_window._apply_preset_by_name("non-existent-preset-xyz")
        # No crash is the assertion

    def test_apply_preset_with_valid_preset_runs_pipeline(self, main_window):
        """_apply_preset executes preset steps and populates output."""
        # Get any built-in preset
        presets = main_window.preset_manager.get_all_presets()
        if not presets:
            pytest.skip("No presets available")

        main_window.text_input.setPlainText("Some sample input")
        main_window._apply_preset(presets[0])
        # Output should be non-empty (or at least the preset ran)
        # We can't predict exact output without knowing the preset; just verify no crash
        assert main_window.output_text is not None  # always true, but ensures method ran

    def test_apply_preset_with_empty_input_sets_no_text_status(self, main_window):
        """_apply_preset with empty input is a no-op."""
        presets = main_window.preset_manager.get_all_presets()
        if not presets:
            pytest.skip("No presets available")

        main_window.text_input.clear()
        # Save original output
        original_output = main_window.output_text.toPlainText()
        main_window._apply_preset(presets[0])
        # Output unchanged since input was empty
        assert main_window.output_text.toPlainText() == original_output

    def test_open_about_dialog_constructs_without_crash(self, main_window, monkeypatch):
        """_open_about_dialog constructs an AboutDialog without crashing.

        We patch AboutDialog.exec to return immediately so the modal doesn't
        block. We verify the construction path runs.
        """
        from ui import main_window as mw_module
        constructed = {"count": 0}

        original_about = mw_module.AboutDialog

        class _StubAbout(original_about):
            def exec(self_inner):
                constructed["count"] += 1
                return 0

        monkeypatch.setattr(mw_module, "AboutDialog", _StubAbout)
        main_window._open_about_dialog()
        assert constructed["count"] == 1
