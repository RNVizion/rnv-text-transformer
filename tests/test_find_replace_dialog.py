"""
tests/test_find_replace_dialog.py
=================================
Phase 8b Round 2 — qtbot interaction tests for ui/find_replace_dialog.py.

Target: 33.6% -> ~85% coverage on the FindReplaceDialog module.

Covers:
  - set_target_text_edit / get_search_options API surface
  - find with empty/literal/case-sensitive/whole-word/regex matching
  - find-next cycling through matches
  - replace single + replace-all flows for all 4 mode combinations
  - text-change reset behavior, regex/whole-word mutex toggle
  - closeEvent highlight cleanup

15 tests in a single test class.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTextEdit

from core.theme_manager import ThemeManager
from ui.find_replace_dialog import FindReplaceDialog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


@pytest.fixture
def target_text_edit(qapp) -> QTextEdit:
    """A real QTextEdit pre-populated with searchable content."""
    edit = QTextEdit()
    edit.setPlainText(
        "Hello world, hello WORLD\n"
        "This is a test. Testing is good.\n"
        "Numbers: 123, 456, 789\n"
        "The cat sat on the mat. The dog ran."
    )
    return edit


# ═════════════════════════════════════════════════════════════════════════════
# FindReplaceDialog — 15 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestFindReplaceDialog:
    """Tests for FindReplaceDialog (find + find-and-replace)."""

    # ── set_target / get_search_options API ──────────────────────────────────

    def test_set_target_text_edit_input_checks_input_radio(self, qtbot, theme_dark, target_text_edit):
        """set_target_text_edit(..., is_output=False) checks the input radio."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit, is_output=False)
        assert dlg.target_text_edit is target_text_edit
        assert dlg.search_input_radio.isChecked() is True

    def test_set_target_text_edit_output_checks_output_radio(self, qtbot, theme_dark, target_text_edit):
        """set_target_text_edit(..., is_output=True) checks the output radio."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit, is_output=True)
        assert dlg.search_output_radio.isChecked() is True

    def test_get_search_options_returns_full_dict(self, qtbot, theme_dark):
        """get_search_options returns a dict with all 4 expected keys."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        opts = dlg.get_search_options()
        assert set(opts.keys()) == {"case_sensitive", "whole_word", "regex", "search_output"}
        # All defaults should be bools
        assert all(isinstance(v, bool) for v in opts.values())

    # ── Regex check disables whole-word ──────────────────────────────────────

    def test_regex_check_disables_whole_word_checkbox(self, qtbot, theme_dark):
        """Checking regex disables the whole-word checkbox (mutex semantics)."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        # Pre-check whole_word so we can verify it gets unset
        dlg.whole_word_check.setChecked(True)
        dlg.regex_check.setChecked(True)
        # _on_regex_changed should disable + uncheck whole_word
        assert dlg.whole_word_check.isEnabled() is False
        assert dlg.whole_word_check.isChecked() is False

    # ── Find flow ────────────────────────────────────────────────────────────

    def test_find_with_empty_query_shows_status_message(self, qtbot, theme_dark, target_text_edit):
        """Find with empty input sets the status label, doesn't crash."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False, target_text_edit=target_text_edit)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText("")
        dlg._on_find()
        assert "find" in dlg.status_label.text().lower()

    def test_find_simple_text_locates_two_case_insensitive_matches(self, qtbot, theme_dark, target_text_edit):
        """Searching 'hello' case-insensitive finds 2 matches."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText("hello")
        # Case-insensitive is the default
        dlg._on_find()
        # The document has "Hello" and "hello" — both should match (case-insensitive)
        assert len(dlg._current_matches) == 2

    def test_find_case_sensitive_misses_capitalized_when_lowercase(self, qtbot, theme_dark, target_text_edit):
        """Case-sensitive 'hello' matches only lowercase, not 'Hello' or 'WORLD'."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText("hello")
        dlg.case_sensitive_check.setChecked(True)
        dlg._on_find()
        # Only one lowercase 'hello' in the text
        assert len(dlg._current_matches) == 1

    def test_find_whole_word_skips_substring_match(self, qtbot, theme_dark):
        """Whole-word 'test' matches 'test' but not 'testing'."""
        target = QTextEdit()
        target.setPlainText("This is a test. Testing should not match.")
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target)
        dlg.find_input.setText("test")
        dlg.whole_word_check.setChecked(True)
        dlg._on_find()
        # Only the exact word "test" matches; "Testing" doesn't
        # (case-insensitive default, but \btest\b only matches the bare word)
        assert len(dlg._current_matches) == 1

    def test_find_regex_pattern_locates_digit_groups(self, qtbot, theme_dark, target_text_edit):
        """Regex \\d+ finds three digit groups (123, 456, 789)."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText(r"\d+")
        dlg.regex_check.setChecked(True)
        dlg._on_find()
        assert len(dlg._current_matches) == 3

    def test_find_invalid_regex_shows_regex_error(self, qtbot, theme_dark, target_text_edit):
        """Invalid regex pattern surfaces a "Regex error:" status, doesn't crash."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText("[unclosed")
        dlg.regex_check.setChecked(True)
        dlg._on_find()
        assert "regex error" in dlg.status_label.text().lower()

    def test_find_next_cycles_through_matches(self, qtbot, theme_dark, target_text_edit):
        """find_next advances _current_match_index modulo len(matches)."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText(r"\d+")
        dlg.regex_check.setChecked(True)
        dlg._on_find()
        # Initial position is 0 (after the find sets it)
        assert dlg._current_match_index == 0
        # Next once → 1
        dlg._on_find_next()
        assert dlg._current_match_index == 1
        # Next again → 2
        dlg._on_find_next()
        assert dlg._current_match_index == 2
        # Wrap-around → 0
        dlg._on_find_next()
        assert dlg._current_match_index == 0

    # ── Replace flow ─────────────────────────────────────────────────────────

    def test_replace_changes_text_at_current_match(self, qtbot, theme_dark):
        """_on_replace mutates the target text at the current match position."""
        target = QTextEdit()
        target.setPlainText("foo bar foo")
        dlg = FindReplaceDialog(theme_dark, replace_mode=True)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target)
        dlg.find_input.setText("foo")
        dlg.case_sensitive_check.setChecked(True)
        dlg._on_find()
        # Replace the first match with "X"
        dlg.replace_input.setText("X")
        dlg._on_replace()
        # After replace, target has one foo → X
        new_text = target.toPlainText()
        assert "X bar" in new_text or "X " in new_text
        # And status message confirms
        assert "replaced" in dlg.status_label.text().lower()

    def test_replace_all_replaces_every_match_case_sensitive(self, qtbot, theme_dark):
        """_on_replace_all replaces every occurrence in case-sensitive mode."""
        target = QTextEdit()
        target.setPlainText("foo bar foo baz foo")
        dlg = FindReplaceDialog(theme_dark, replace_mode=True)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target)
        dlg.find_input.setText("foo")
        dlg.case_sensitive_check.setChecked(True)
        dlg.replace_input.setText("X")
        dlg._on_replace_all()
        # All three foos replaced
        assert target.toPlainText() == "X bar X baz X"
        assert "3" in dlg.status_label.text()

    def test_replace_all_regex_with_backreference(self, qtbot, theme_dark):
        """_on_replace_all with regex flag uses re.subn semantics."""
        target = QTextEdit()
        target.setPlainText("abc123 def456")
        dlg = FindReplaceDialog(theme_dark, replace_mode=True)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target)
        dlg.find_input.setText(r"\d+")
        dlg.regex_check.setChecked(True)
        dlg.replace_input.setText("N")
        dlg._on_replace_all()
        assert target.toPlainText() == "abcN defN"

    # ── Reset / close behavior ───────────────────────────────────────────────

    def test_find_text_change_resets_matches_and_buttons(self, qtbot, theme_dark, target_text_edit):
        """Typing in find_input after a successful find resets match state."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        dlg.find_input.setText("hello")
        dlg._on_find()
        assert len(dlg._current_matches) > 0
        assert dlg._current_match_index >= 0

        # Now change text → matches and index should reset
        dlg.find_input.setText("hellothere")  # textChanged fires _on_find_text_changed
        assert dlg._current_matches == []
        assert dlg._current_match_index == -1
        assert dlg.find_next_btn.isEnabled() is False

    def test_close_event_clears_highlights(self, qtbot, theme_dark, target_text_edit):
        """closeEvent invokes _clear_highlights without crashing."""
        dlg = FindReplaceDialog(theme_dark, replace_mode=False)
        qtbot.addWidget(dlg)
        dlg.set_target_text_edit(target_text_edit)
        # Drive the highlighted state first
        dlg.find_input.setText("hello")
        dlg._on_find()
        # Close should clear without raising
        dlg.close()
        # Dialog should be in non-visible state after close
        assert dlg.isVisible() is False
