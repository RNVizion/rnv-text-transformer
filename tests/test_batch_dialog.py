"""
tests/test_batch_dialog.py
==========================
Phase 8b Round 6 — qtbot interaction tests for ui/batch_dialog.py.

Target: 46.4% -> ~80% coverage on the BatchDialog module.

Covers two classes:
  - BatchWorkerThread (QThread — we drive the handlers, not the run loop)
  - BatchDialog (the main dialog)

Tests use hand-emitted signal payloads for the worker handlers rather than
spinning up the real thread, sidestepping the QThread coverage limitation
documented in Phase 4.

Modal child dialogs (QFileDialog directory pickers, QMessageBox confirms)
are mocked via monkeypatch and patch.object.

12 tests in 1 test class.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from core.batch_processor import BatchResult
from core.theme_manager import ThemeManager
from ui.batch_dialog import BatchDialog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


def _make_batch_result(filename: str = "file.txt", success: bool = True,
                       message: str = "OK") -> BatchResult:
    """Construct a BatchResult for handler tests."""
    return BatchResult(
        file_path=Path(filename),
        success=success,
        message=message,
        original_size=100,
        processed_size=120,
    )


# ═════════════════════════════════════════════════════════════════════════════
# BatchDialog — 12 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestBatchDialog:
    """Tests for BatchDialog (batch-processing dialog body)."""

    # ── Browse handlers ──────────────────────────────────────────────────────

    def test_browse_source_populates_source_input(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """Clicking browse source and picking a folder sets source_input.text()."""
        (tmp_path / "test.txt").write_text("hello", encoding="utf-8")
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)

        monkeypatch.setattr(
            QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: str(tmp_path)),
        )
        dlg._browse_source()
        assert dlg.source_input.text() == str(tmp_path)

    def test_browse_output_populates_output_input(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """Browsing an output folder fills output_input."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        # Uncheck same-location so output_input is enabled
        dlg.same_location_check.setChecked(False)

        out_folder = tmp_path / "out"
        out_folder.mkdir()
        monkeypatch.setattr(
            QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: str(out_folder)),
        )
        dlg._browse_output()
        assert dlg.output_input.text() == str(out_folder)

    def test_browse_source_cancelled_leaves_input_empty(self, qtbot, theme_dark, monkeypatch):
        """If the user cancels the file dialog, source_input stays empty."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)

        monkeypatch.setattr(
            QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: ""),  # cancelled = empty string
        )
        dlg._browse_source()
        assert dlg.source_input.text() == ""

    # ── Same-location checkbox toggle ────────────────────────────────────────

    def test_same_location_unchecked_enables_output_input(self, qtbot, theme_dark):
        """Unchecking same_location_check enables output_input and browse button."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        # Starts checked → output_input disabled
        assert dlg.output_input.isEnabled() is False

        dlg.same_location_check.setChecked(False)
        assert dlg.output_input.isEnabled() is True
        assert dlg.browse_output_btn.isEnabled() is True

    def test_same_location_checked_clears_output_input(self, qtbot, theme_dark):
        """Re-checking same_location clears output_input contents."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.same_location_check.setChecked(False)
        dlg.output_input.setText("/some/path")
        dlg.same_location_check.setChecked(True)
        assert dlg.output_input.text() == ""

    # ── _update_file_count ───────────────────────────────────────────────────

    def test_update_file_count_finds_supported_files(self, qtbot, theme_dark, tmp_path):
        """_update_file_count counts files and updates progress_label."""
        (tmp_path / "a.txt").write_text("x", encoding="utf-8")
        (tmp_path / "b.txt").write_text("y", encoding="utf-8")

        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.source_input.setText(str(tmp_path))
        dlg._update_file_count()
        # progress_label gets "Found N supported file(s)"
        assert "2" in dlg.progress_label.text()
        assert "found" in dlg.progress_label.text().lower()

    # ── _start_processing validation ─────────────────────────────────────────

    def test_start_processing_with_empty_source_shows_warning(self, qtbot, theme_dark):
        """Starting with empty source_input surfaces a warning dialog, no thread."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._start_processing()
            mb_exec.assert_called_once()
        assert dlg._worker_thread is None

    def test_start_processing_with_nonexistent_source_shows_warning(self, qtbot, theme_dark):
        """Starting with a non-existent folder surfaces a warning."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.source_input.setText("/does/not/exist/anywhere")

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._start_processing()
            mb_exec.assert_called_once()
        assert dlg._worker_thread is None

    def test_start_processing_with_empty_folder_shows_info(self, qtbot, theme_dark, tmp_path):
        """Starting on a folder with no supported files shows info, no thread."""
        # Empty tmp_path → no supported files
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.source_input.setText(str(tmp_path))

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._start_processing()
            mb_exec.assert_called_once()
        assert dlg._worker_thread is None

    # ── Progress / file-processed / finished handlers ────────────────────────

    def test_on_progress_updates_progress_bar_and_label(self, qtbot, theme_dark):
        """_on_progress sets progress_bar value and progress_label text."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.progress_bar.setMaximum(10)
        dlg._on_progress(3, 10, "file3.txt")
        assert dlg.progress_bar.value() == 3
        assert "3/10" in dlg.progress_label.text()
        assert "file3.txt" in dlg.progress_label.text()

    def test_on_file_processed_appends_status_to_log(self, qtbot, theme_dark):
        """_on_file_processed appends a status line with checkmark and filename."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        result_ok = _make_batch_result("success.txt", success=True, message="OK")
        result_fail = _make_batch_result("fail.txt", success=False, message="Permission denied")

        dlg._on_file_processed(result_ok)
        dlg._on_file_processed(result_fail)
        log = dlg.log_text.toPlainText()
        assert "success.txt" in log
        assert "fail.txt" in log
        assert "Permission denied" in log

    def test_on_finished_stores_results_and_reenables_start_button(self, qtbot, theme_dark):
        """_on_finished stores the results list and re-enables the start button."""
        dlg = BatchDialog(theme_dark)
        qtbot.addWidget(dlg)
        # Simulate the "running" state
        dlg.start_btn.setEnabled(False)
        dlg.cancel_btn.setEnabled(True)
        dlg.close_btn.setEnabled(False)

        results = [
            _make_batch_result("a.txt", success=True),
            _make_batch_result("b.txt", success=True),
            _make_batch_result("c.txt", success=False, message="error"),
        ]
        dlg._on_finished(results)

        assert dlg._results == results
        assert dlg.start_btn.isEnabled() is True
        assert dlg.cancel_btn.isEnabled() is False
        assert dlg.close_btn.isEnabled() is True
        # Log should contain summary
        log = dlg.log_text.toPlainText()
        assert "Total files: 3" in log
        assert "Successful: 2" in log
        assert "Failed: 1" in log
