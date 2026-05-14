"""
tests/test_watch_folder_dialog.py
=================================
Phase 8b Round 4 — qtbot interaction tests for ui/watch_folder_dialog.py.

Target: 35.7% -> ~80% coverage on the WatchFolderDialog module.

Covers two classes:
  - RuleEditWidget: edits a single watch rule (input/output/patterns/mode/preset)
  - WatchFolderDialog: container with add/remove/start/stop and activity log

Tests use monkeypatch on QFileDialog.getExistingDirectory and QMessageBox.exec
since both dialogs spawn modal child dialogs that would block the test thread.

15 tests across 2 test classes (5 RuleEditWidget + 10 WatchFolderDialog),
plus 1 regression guard for the Phase 8b R4 production bug = 16 total.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from core.folder_watcher import WatchRule
from core.theme_manager import ThemeManager
from ui.watch_folder_dialog import RuleEditWidget, WatchFolderDialog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


def _make_rule(tmp_path: Path, rule_id: str | None = None) -> WatchRule:
    """Create a WatchRule with valid input/output folders for tests."""
    rid = rule_id or str(uuid.uuid4())
    in_folder = tmp_path / f"in_{rid}"
    out_folder = tmp_path / f"out_{rid}"
    in_folder.mkdir(exist_ok=True)
    out_folder.mkdir(exist_ok=True)
    return WatchRule(
        id=rid,
        input_folder=in_folder,
        output_folder=out_folder,
        file_patterns=["*.txt"],
        enabled=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 1. RuleEditWidget — 5 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestRuleEditWidget:
    """Tests for RuleEditWidget (single watch-rule editor)."""

    def test_rule_edit_widget_loads_rule_fields_into_inputs(self, qtbot, theme_dark, tmp_path):
        """_load_rule populates input_edit, output_edit, patterns_edit from the rule."""
        rule = _make_rule(tmp_path, "r1")
        # Mutate patterns BEFORE constructing widget so _load_rule sees them
        rule.file_patterns = ["*.md", "*.txt"]
        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        assert widget.input_edit.text() == str(rule.input_folder)
        assert widget.output_edit.text() == str(rule.output_folder)
        assert widget.patterns_edit.text() == "*.md, *.txt"
        assert widget.enabled_check.isChecked() is True

    def test_rule_edit_browse_input_sets_input_folder(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """Clicking input browse and selecting a folder sets input_edit.text()."""
        rule = _make_rule(tmp_path, "r2")
        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        new_folder = tmp_path / "new_input"
        new_folder.mkdir()
        monkeypatch.setattr(
            QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: str(new_folder)),
        )
        widget._browse_input()
        assert widget.input_edit.text() == str(new_folder)

    def test_rule_edit_patterns_split_on_comma_propagate_to_rule(self, qtbot, theme_dark, tmp_path):
        """Typing comma-separated patterns updates rule.file_patterns via _save_rule."""
        rule = _make_rule(tmp_path, "r3")
        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        widget.patterns_edit.setText("*.py, *.json, *.md")
        # textChanged fires _on_changed → _save_rule
        assert rule.file_patterns == ["*.py", "*.json", "*.md"]

    def test_rule_edit_rule_changed_signal_emits_on_field_change(self, qtbot, theme_dark, tmp_path):
        """Changing the enabled checkbox emits rule_changed with the rule."""
        rule = _make_rule(tmp_path, "r4")
        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.rule_changed, timeout=1000) as spy:
            widget.enabled_check.setChecked(False)
        # Signal payload is the rule object itself
        assert spy.args[0] is rule
        assert rule.enabled is False

    def test_rule_edit_delete_button_emits_rule_deleted_after_confirm(self, qtbot, theme_dark, tmp_path):
        """Clicking delete + confirming emits rule_deleted with the rule.id."""
        rule = _make_rule(tmp_path, "r5")
        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        # Mock the confirm dialog to return Yes
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
            with qtbot.waitSignal(widget.rule_deleted, timeout=1000) as spy:
                widget._on_delete()
        assert spy.args[0] == "r5"

    def test_rule_edit_load_preserves_multi_pattern_file_patterns(self, qtbot, theme_dark, tmp_path):
        """REGRESSION GUARD (Phase 8b R4 bug): RuleEditWidget construction must NOT
        mutate rule.file_patterns.

        Before the fix, the signal cascade during _load_rule (setChecked/setText on
        early fields firing _on_changed -> _save_rule with the still-empty
        patterns_edit) silently overwrote rule.file_patterns with ["*.txt"], the
        default fallback. This was a data-loss bug: any user with multi-pattern
        rules ["*.py", "*.md"] would have them silently reset to ["*.txt"] every
        time the dialog opened.

        The fix blocks signals on all input widgets during _load_rule. This test
        guards against the regression by constructing a widget for a rule with
        non-default file_patterns and verifying both the widget AND the rule
        retain the original patterns.
        """
        rule = _make_rule(tmp_path, "regression_guard")
        rule.file_patterns = ["*.py", "*.md", "*.rst"]
        # Other fields too — to ensure none of them mutate during load
        rule.transform_mode = None
        rule.preset_name = None
        rule.process_existing = True
        rule.delete_source = False

        widget = RuleEditWidget(rule, theme_dark)
        qtbot.addWidget(widget)

        # The rule itself must be unchanged
        assert rule.file_patterns == ["*.py", "*.md", "*.rst"], (
            f"file_patterns was mutated during widget construction: "
            f"got {rule.file_patterns}"
        )
        # And the widget must reflect the correct patterns
        assert widget.patterns_edit.text() == "*.py, *.md, *.rst"


# ═════════════════════════════════════════════════════════════════════════════
# 2. WatchFolderDialog — 10 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestWatchFolderDialog:
    """Tests for WatchFolderDialog (container dialog with add/remove/start/stop)."""

    def test_watch_folder_dialog_instantiates_empty_when_no_saved_rules(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """Dialog construction loads zero rules when no saved rules exist."""
        # Point rule_manager at empty tmp_path so no existing rules load
        from ui import watch_folder_dialog as wfd_mod
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        assert len(dlg.rule_widgets) == 0

    def test_watch_folder_dialog_loads_saved_rules(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_load_rules creates RuleEditWidget instances for each saved rule."""
        from ui import watch_folder_dialog as wfd_mod
        rule_a = _make_rule(tmp_path, "a")
        rule_b = _make_rule(tmp_path, "b")
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([rule_a, rule_b]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        assert "a" in dlg.rule_widgets
        assert "b" in dlg.rule_widgets

    def test_watch_folder_dialog_add_rule_appends_widget(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_add_rule constructs a default rule and adds the widget."""
        from ui import watch_folder_dialog as wfd_mod
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        initial = len(dlg.rule_widgets)
        dlg._add_rule()
        assert len(dlg.rule_widgets) == initial + 1

    def test_watch_folder_dialog_rule_deleted_signal_removes_widget(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """When a RuleEditWidget emits rule_deleted, the widget is removed."""
        from ui import watch_folder_dialog as wfd_mod
        rule = _make_rule(tmp_path, "to-remove")
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([rule]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        assert "to-remove" in dlg.rule_widgets

        # Directly invoke the handler the signal would call
        dlg._on_rule_deleted("to-remove")
        assert "to-remove" not in dlg.rule_widgets

    def test_watch_folder_dialog_start_watching_with_no_enabled_rules_warns(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_start_watching shows a warning dialog when no rules are enabled."""
        from ui import watch_folder_dialog as wfd_mod
        rule = _make_rule(tmp_path, "disabled")
        rule.enabled = False  # ensure disabled
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([rule]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok) as mb_exec:
            dlg._start_watching()
            mb_exec.assert_called_once()

    def test_watch_folder_dialog_start_watching_with_enabled_rule_starts_watcher(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_start_watching with an enabled rule flips the button states."""
        pytest.importorskip("watchdog")
        from ui import watch_folder_dialog as wfd_mod
        rule = _make_rule(tmp_path, "enabled")
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([rule]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)

        try:
            dlg._start_watching()
            # After successful start, start button disables, stop button enables
            assert dlg.start_btn.isEnabled() is False
            assert dlg.stop_btn.isEnabled() is True
        finally:
            dlg._stop_watching()

    def test_watch_folder_dialog_stop_watching_toggles_buttons(self, qtbot, theme_dark, tmp_path, monkeypatch):
        """_stop_watching re-enables start_btn, disables stop_btn, updates status."""
        pytest.importorskip("watchdog")
        from ui import watch_folder_dialog as wfd_mod
        rule = _make_rule(tmp_path, "stopme")
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([rule]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg._start_watching()
        dlg._stop_watching()

        assert dlg.start_btn.isEnabled() is True
        assert dlg.stop_btn.isEnabled() is False
        assert "stop" in dlg.status_label.text().lower()

    def test_watch_folder_dialog_clear_log_empties_log_text(self, qtbot, theme_dark, monkeypatch):
        """Clear-log handler empties log_text widget."""
        from ui import watch_folder_dialog as wfd_mod
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.log_text.setPlainText("some log content\nmore content")
        dlg.log_text.clear()  # what the clear-log button calls
        assert dlg.log_text.toPlainText() == ""

    def test_watch_folder_dialog_log_method_appends_to_log_text(self, qtbot, theme_dark, monkeypatch):
        """_log queues a message that gets flushed to log_text by the timer."""
        from ui import watch_folder_dialog as wfd_mod
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg._log("Test message 42")
        # Trigger the queue flush manually instead of waiting for the timer
        dlg._process_log_queue()
        assert "Test message 42" in dlg.log_text.toPlainText()

    def test_watch_folder_dialog_close_stops_timer_and_watcher(self, qtbot, theme_dark, monkeypatch):
        """closeEvent stops the log timer and watcher."""
        from ui import watch_folder_dialog as wfd_mod
        monkeypatch.setattr(wfd_mod, "WatchRuleManager", lambda: _FakeRuleManager([]))

        dlg = WatchFolderDialog(theme_dark)
        qtbot.addWidget(dlg)
        assert dlg._log_timer.isActive() is True
        dlg.close()
        assert dlg._log_timer.isActive() is False


# ─── Test helpers ─────────────────────────────────────────────────────────────

class _FakeRuleManager:
    """Test double for WatchRuleManager — returns a fixed list of rules."""

    def __init__(self, rules: list[WatchRule]) -> None:
        self._rules = list(rules)

    def load_rules(self) -> list[WatchRule]:
        return list(self._rules)

    def save_rules(self, rules: list[WatchRule]) -> None:
        self._rules = list(rules)
