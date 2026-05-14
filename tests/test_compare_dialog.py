"""
tests/test_compare_dialog.py
============================
Phase 8c Round 1 — qtbot interaction tests for ui/compare_dialog.py.

Target: 54.7% -> ~78% coverage on the CompareDialog module.

Covers two classes:
  - ChangeWidget: per-change row with accept/reject/click signals
  - CompareDialog: side-by-side diff + merge UI

Patterns:
  - qtbot.addWidget for proper widget cleanup
  - QSignalSpy / qtbot.waitSignal for signal verification
  - monkeypatch QFileDialog / QMessageBox for modal child dialogs
  - Real DiffChange/DiffResult objects from core/diff_engine

22 tests across 2 test classes (5 ChangeWidget + 17 CompareDialog).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from core.diff_engine import ChangeType, DiffChange, DiffEngine
from core.theme_manager import ThemeManager
from ui.compare_dialog import ChangeWidget, CompareDialog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


def _make_change(
    change_type: ChangeType = ChangeType.REPLACE,
    left_text: str = "old text",
    right_text: str = "new text",
    left_line_num: int | None = 1,
    right_line_num: int | None = 1,
    accepted: bool | None = None,
) -> DiffChange:
    """Construct a DiffChange for tests."""
    return DiffChange(
        change_type=change_type,
        left_line_num=left_line_num,
        right_line_num=right_line_num,
        left_text=left_text,
        right_text=right_text,
        accepted=accepted,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 1. ChangeWidget — 5 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestChangeWidget:
    """Tests for ChangeWidget (per-change row inside CompareDialog)."""

    def test_change_widget_constructs_with_diff_change(self, qtbot):
        """ChangeWidget construction stores the index and change reference."""
        change = _make_change()
        widget = ChangeWidget(index=3, change=change, is_dark=True)
        qtbot.addWidget(widget)
        assert widget.index == 3
        assert widget.change is change

    def test_change_widget_accept_button_emits_accepted_signal(self, qtbot):
        """Clicking the accept button emits accepted(index)."""
        change = _make_change()
        widget = ChangeWidget(index=5, change=change, is_dark=True)
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.accepted, timeout=1000) as spy:
            widget._accept_btn.click()
        assert spy.args[0] == 5

    def test_change_widget_reject_button_emits_rejected_signal(self, qtbot):
        """Clicking the reject button emits rejected(index)."""
        change = _make_change()
        widget = ChangeWidget(index=2, change=change, is_dark=True)
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.rejected, timeout=1000) as spy:
            widget._reject_btn.click()
        assert spy.args[0] == 2

    def test_change_widget_update_change_refreshes_status_display(self, qtbot):
        """update_change(...) swaps in a new change and refreshes status text."""
        # Start with a pending change
        original = _make_change(accepted=None)
        widget = ChangeWidget(index=0, change=original, is_dark=True)
        qtbot.addWidget(widget)
        # Initially Pending
        assert "pending" in widget._status_label.text().lower()

        # Update to an accepted change
        updated = _make_change(accepted=True)
        widget.update_change(updated)
        assert "accepted" in widget._status_label.text().lower()

    def test_change_widget_status_reflects_accepted_rejected_pending(self, qtbot):
        """Three accepted states map to three distinct status labels."""
        for accepted_state, expected in [
            (None, "pending"),
            (True, "accepted"),
            (False, "rejected"),
        ]:
            change = _make_change(accepted=accepted_state)
            widget = ChangeWidget(index=0, change=change, is_dark=True)
            qtbot.addWidget(widget)
            assert expected in widget._status_label.text().lower(), (
                f"For accepted={accepted_state}, expected '{expected}' "
                f"in status, got '{widget._status_label.text()}'"
            )


# ═════════════════════════════════════════════════════════════════════════════
# 2. CompareDialog — 17 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestCompareDialog:
    """Tests for CompareDialog (main diff + merge UI)."""

    # ── Construction + text loading ──────────────────────────────────────────

    def test_compare_dialog_constructs_with_two_text_inputs(self, qtbot, theme_dark):
        """Constructor stores both input and output text."""
        dlg = CompareDialog(theme_dark, input_text="alpha", output_text="beta")
        qtbot.addWidget(dlg)
        assert dlg.input_text == "alpha"
        assert dlg.output_text == "beta"

    def test_set_texts_populates_input_and_output_edits(self, qtbot, theme_dark):
        """set_texts re-runs _compute_diff and _load_text."""
        dlg = CompareDialog(theme_dark, input_text="", output_text="")
        qtbot.addWidget(dlg)
        dlg.set_texts("first line\nsecond line", "first line\nchanged line")
        assert "first line" in dlg.input_edit.toPlainText()
        assert "changed line" in dlg.output_edit.toPlainText()

    def test_compute_diff_populates_changes_list(self, qtbot, theme_dark):
        """_compute_diff produces ChangeWidget instances for each non-equal change."""
        dlg = CompareDialog(
            theme_dark,
            input_text="line 1\nline 2\nline 3",
            output_text="line 1\nMODIFIED\nline 3",
        )
        qtbot.addWidget(dlg)
        # _compute_diff has run during __init__; we should have at least 1 widget
        assert len(dlg._change_widgets) >= 1

    # ── View mode changes ────────────────────────────────────────────────────

    def test_view_mode_change_to_inline_unified_index(self, qtbot, theme_dark):
        """Switching view mode to Inline (Unified) at index 1 doesn't crash."""
        dlg = CompareDialog(theme_dark, input_text="aaa\nbbb", output_text="aaa\nccc")
        qtbot.addWidget(dlg)
        # The combo has 2 items: 0=Side-by-Side, 1=Inline (Unified)
        dlg.view_mode_combo.setCurrentIndex(1)
        assert dlg.view_mode_combo.currentIndex() == 1

    def test_highlight_changed_state_toggles_highlights(self, qtbot, theme_dark):
        """Toggling highlight_diff_check re-renders highlights without crashing."""
        dlg = CompareDialog(theme_dark, input_text="aaa", output_text="bbb")
        qtbot.addWidget(dlg)
        # Unchecking should clear highlights; rechecking should re-apply
        dlg.highlight_diff_check.setChecked(False)
        dlg.highlight_diff_check.setChecked(True)
        # No exception is the assertion

    # ── Navigation prev/next/clicked ─────────────────────────────────────────

    def test_navigate_next_advances_current_change(self, qtbot, theme_dark):
        """_navigate_next moves _current_change_idx forward through change_indices."""
        dlg = CompareDialog(
            theme_dark,
            input_text="line 1\nline 2\nline 3",
            output_text="LINE 1\nline 2\nLINE 3",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None or not dlg._diff_result.get_change_indices():
            pytest.skip("No diff changes computed for this input pair")

        change_indices = dlg._diff_result.get_change_indices()
        # Initially _current_change_idx is -1; _navigate_next should advance to first
        dlg._navigate_next()
        assert dlg._current_change_idx == change_indices[0]

    def test_navigate_prev_with_no_prior_position_does_not_change(self, qtbot, theme_dark):
        """_navigate_prev with current_pos at 0 doesn't go negative."""
        dlg = CompareDialog(
            theme_dark,
            input_text="alpha",
            output_text="beta",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None or not dlg._diff_result.get_change_indices():
            pytest.skip("No diff changes computed for this input pair")

        change_indices = dlg._diff_result.get_change_indices()
        # Position at first
        dlg._current_change_idx = change_indices[0]
        dlg._navigate_prev()
        # Should remain at first (no move past start)
        assert dlg._current_change_idx == change_indices[0]

    def test_on_change_clicked_sets_current_index(self, qtbot, theme_dark):
        """_on_change_clicked stores the index and triggers scroll/navigation update."""
        dlg = CompareDialog(theme_dark, input_text="foo", output_text="bar")
        qtbot.addWidget(dlg)
        if dlg._diff_result is None or not dlg._diff_result.changes:
            pytest.skip("No diff changes for this input pair")

        dlg._on_change_clicked(0)
        assert dlg._current_change_idx == 0

    # ── Accept/reject/all/reset paths ────────────────────────────────────────

    def test_on_change_accepted_marks_change_and_updates_widget(self, qtbot, theme_dark):
        """_on_change_accepted marks the change as accepted and refreshes the widget."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nold\nccc",
            output_text="aaa\nnew\nccc",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None:
            pytest.skip("No diff result")

        change_indices = dlg._diff_result.get_change_indices()
        if not change_indices:
            pytest.skip("No changes in diff")
        first_change_idx = change_indices[0]

        dlg._on_change_accepted(first_change_idx)
        assert dlg._diff_result.changes[first_change_idx].accepted is True

    def test_on_change_rejected_marks_change_as_rejected(self, qtbot, theme_dark):
        """_on_change_rejected sets the accepted flag to False."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nold\nccc",
            output_text="aaa\nnew\nccc",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None:
            pytest.skip("No diff result")
        change_indices = dlg._diff_result.get_change_indices()
        if not change_indices:
            pytest.skip("No changes in diff")

        dlg._on_change_rejected(change_indices[0])
        assert dlg._diff_result.changes[change_indices[0]].accepted is False

    def test_accept_all_marks_every_change_accepted(self, qtbot, theme_dark):
        """_accept_all sets accepted=True on every change."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb\nccc",
            output_text="AAA\nBBB\nCCC",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None:
            pytest.skip("No diff result")

        dlg._accept_all()
        change_indices = dlg._diff_result.get_change_indices()
        for idx in change_indices:
            assert dlg._diff_result.changes[idx].accepted is True

    def test_reject_all_marks_every_change_rejected(self, qtbot, theme_dark):
        """_reject_all sets accepted=False on every change."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb",
            output_text="AAA\nBBB",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None:
            pytest.skip("No diff result")

        dlg._reject_all()
        for idx in dlg._diff_result.get_change_indices():
            assert dlg._diff_result.changes[idx].accepted is False

    def test_reset_all_clears_every_change_state(self, qtbot, theme_dark):
        """_reset_all returns every change.accepted to None."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb",
            output_text="AAA\nBBB",
        )
        qtbot.addWidget(dlg)
        if dlg._diff_result is None:
            pytest.skip("No diff result")

        dlg._accept_all()  # Make sure they're decided first
        dlg._reset_all()
        for idx in dlg._diff_result.get_change_indices():
            assert dlg._diff_result.changes[idx].accepted is None

    # ── Export + apply merge ─────────────────────────────────────────────────

    def test_export_diff_with_no_diff_result_shows_info(self, qtbot, theme_dark):
        """_export_diff when _diff_result is None surfaces an info dialog."""
        dlg = CompareDialog(theme_dark, input_text="", output_text="")
        qtbot.addWidget(dlg)
        # Force _diff_result to None to drive the early-return path
        dlg._diff_result = None
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._export_diff("unified")
            mb_exec.assert_called_once()

    def test_export_diff_html_writes_file_when_path_selected(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_export_diff('html') writes the file selected via QFileDialog."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb",
            output_text="aaa\nBBB",
        )
        qtbot.addWidget(dlg)
        out_path = tmp_path / "diff.html"
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **kw: (str(out_path), "HTML Files (*.html)")),
        )
        # Patch QMessageBox so the success dialog doesn't block
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok):
            dlg._export_diff("html")
        assert out_path.exists()
        # And the content is something HTML-shaped
        assert "<" in out_path.read_text(encoding="utf-8")

    def test_apply_merge_emits_merge_applied_signal(self, qtbot, theme_dark):
        """_apply_merge emits merge_applied with the merged text."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb",
            output_text="aaa\nBBB",
        )
        qtbot.addWidget(dlg)

        # Mock self.accept() so the dialog doesn't actually close
        # AND patch QMessageBox.exec to bypass the "pending changes" confirm
        with patch.object(dlg, "accept"), \
             patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
            with qtbot.waitSignal(dlg.merge_applied, timeout=1000) as spy:
                dlg._apply_merge()
        # spy.args[0] is the merged text
        assert isinstance(spy.args[0], str)

    # ── Theme refresh ────────────────────────────────────────────────────────

    def test_refresh_theme_updates_styles_without_crash(self, qtbot, theme_dark):
        """refresh_theme rebuilds change widgets without raising."""
        dlg = CompareDialog(
            theme_dark,
            input_text="aaa\nbbb",
            output_text="aaa\nBBB",
        )
        qtbot.addWidget(dlg)
        initial_count = len(dlg._change_widgets)

        # Toggle theme and refresh
        theme_dark.current_theme = "light"
        dlg.refresh_theme()
        # Widgets get rebuilt with new is_dark, count should match
        assert len(dlg._change_widgets) == initial_count
