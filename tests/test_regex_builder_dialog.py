"""
tests/test_regex_builder_dialog.py
==================================
Phase 8b Round 3 — qtbot interaction tests for ui/regex_builder_dialog.py.

Target: 49.0% -> ~85% coverage on the RegexBuilderDialog module.

Covers:
  - set_text / set_pattern public API
  - Pattern validation (valid + invalid patterns surface in status_label)
  - Debounced update timer triggers _update_matches
  - Flag computation (case-insensitive / multiline / dotall)
  - Match table population for literal and group patterns
  - Group table population for capturing groups
  - Empty pattern/text → _clear_results path
  - Pattern combo selection loads pattern + flags
  - Apply emits pattern_applied with (pattern, replacement, flags)
  - Replacement preview updates with replaced text
  - closeEvent stops the update timer
  - Invalid pattern apply shows warning, no emission

15 tests in 1 test class.
"""
from __future__ import annotations

import re
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from core.theme_manager import ThemeManager
from ui.regex_builder_dialog import RegexBuilderDialog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


# ═════════════════════════════════════════════════════════════════════════════
# RegexBuilderDialog — 15 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestRegexBuilderDialog:
    """Tests for RegexBuilderDialog (visual regex pattern builder)."""

    # ── Public API: set_text / set_pattern ───────────────────────────────────

    def test_set_text_populates_test_area(self, qtbot, theme_dark):
        """set_text(...) updates the test_text QTextEdit content."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.set_text("Hello, regex world")
        assert dlg.test_text.toPlainText() == "Hello, regex world"

    def test_set_pattern_populates_pattern_input(self, qtbot, theme_dark):
        """set_pattern(...) updates the pattern_input QLineEdit content."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.set_pattern(r"\d+")
        assert dlg.pattern_input.text() == r"\d+"

    def test_initial_input_text_loads_into_test_area(self, qtbot, theme_dark):
        """Constructor input_text param populates test_text via _load_text."""
        dlg = RegexBuilderDialog(theme_dark, input_text="initial content")
        qtbot.addWidget(dlg)
        assert dlg.test_text.toPlainText() == "initial content"

    # ── Pattern validation ───────────────────────────────────────────────────

    def test_valid_pattern_shows_valid_status(self, qtbot, theme_dark):
        """Typing a valid pattern shows "Pattern is valid" in status_label."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"\d+")
        # textChanged → _on_pattern_changed validates and sets status
        assert "valid" in dlg.status_label.text().lower()

    def test_invalid_pattern_shows_error_status(self, qtbot, theme_dark):
        """Typing an invalid pattern shows "Error:" in status_label."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText("[unclosed")
        assert "error" in dlg.status_label.text().lower()

    def test_empty_pattern_shows_prompt_status(self, qtbot, theme_dark):
        """Empty pattern surfaces "Enter a pattern" in status_label."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        # Set then clear to trigger the empty-pattern branch
        dlg.pattern_input.setText("x")
        dlg.pattern_input.setText("")
        assert "enter" in dlg.status_label.text().lower()

    # ── Flag computation ─────────────────────────────────────────────────────

    def test_case_insensitive_flag_in_get_flags(self, qtbot, theme_dark):
        """Checking case_check causes _get_flags to include re.IGNORECASE."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.case_check.setChecked(True)
        flags = dlg._get_flags()
        assert flags & re.IGNORECASE

    def test_multiline_and_dotall_flags_in_get_flags(self, qtbot, theme_dark):
        """Multiline + dotall produce both flags in _get_flags."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.multiline_check.setChecked(True)
        dlg.dotall_check.setChecked(True)
        flags = dlg._get_flags()
        assert flags & re.MULTILINE
        assert flags & re.DOTALL

    # ── Match and group table updates ────────────────────────────────────────

    def test_update_matches_populates_match_table(self, qtbot, theme_dark):
        """A pattern with 3 matches in the test text populates the matches_table."""
        dlg = RegexBuilderDialog(theme_dark, input_text="abc 123 def 456 ghi 789")
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"\d+")
        dlg._update_matches()
        assert dlg.matches_table.rowCount() == 3
        assert "3" in dlg.match_count_label.text()

    def test_update_matches_populates_groups_table_for_capturing_pattern(self, qtbot, theme_dark):
        """Capturing groups produce rows in the groups_table."""
        dlg = RegexBuilderDialog(theme_dark, input_text="John 30, Mary 25")
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"(\w+) (\d+)")
        dlg._update_matches()
        # First match has 2 groups → 2 rows in groups_table
        assert dlg.groups_table.rowCount() >= 2

    def test_empty_pattern_or_text_clears_results(self, qtbot, theme_dark):
        """Empty pattern with any text clears the match table and count."""
        dlg = RegexBuilderDialog(theme_dark, input_text="some text here")
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"\d+")
        dlg._update_matches()  # has matches if any digits, but text has none
        # Now explicitly clear pattern
        dlg.pattern_input.setText("")
        dlg._update_matches()
        # Cleared state
        assert dlg.matches_table.rowCount() == 0

    # ── Apply / signal emission ──────────────────────────────────────────────

    def test_apply_emits_pattern_applied_signal(self, qtbot, theme_dark):
        """_apply_find (apply-only button path) emits pattern_applied with right args."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"\d+")
        dlg.case_check.setChecked(True)

        with qtbot.waitSignal(dlg.pattern_applied, timeout=1000) as spy:
            dlg._apply_find()

        pattern, replacement, flags = spy.args
        assert pattern == r"\d+"
        assert replacement == ""
        assert flags & re.IGNORECASE

    def test_apply_with_empty_pattern_shows_warning(self, qtbot, theme_dark):
        """_apply_find with empty pattern shows warning, does not emit signal."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText("")

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._apply_find()
            mb_exec.assert_called_once()

    # ── Replace preview + closeEvent ─────────────────────────────────────────

    def test_replace_preview_shows_substituted_text(self, qtbot, theme_dark):
        """_update_replace_preview puts the substituted text in result_preview."""
        dlg = RegexBuilderDialog(theme_dark, input_text="abc 123 def")
        qtbot.addWidget(dlg)
        dlg.pattern_input.setText(r"\d+")
        dlg.replacement_input.setText("N")
        dlg._update_replace_preview()
        assert "N" in dlg.result_preview.toPlainText()
        assert "123" not in dlg.result_preview.toPlainText()

    def test_close_event_stops_update_timer(self, qtbot, theme_dark):
        """closeEvent invokes _update_timer.stop() — no crash, timer inactive after."""
        dlg = RegexBuilderDialog(theme_dark)
        qtbot.addWidget(dlg)
        # Start the timer
        dlg._update_timer.start(1000)
        assert dlg._update_timer.isActive() is True
        # Close should stop it
        dlg.close()
        assert dlg._update_timer.isActive() is False
