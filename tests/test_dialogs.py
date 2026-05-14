"""
tests/test_dialogs.py
=====================
Phase 3 — Dialog smoke tests.

Covers:
  BaseDialog              (architectural centerpiece)
  AboutDialog             (extends QDialog directly, not BaseDialog)
  + 10 BaseDialog subclasses

For each dialog, two tests:
  1. Instantiate with required args (verifies window title, no crash on init)
  2. Verify one expected signal is defined and reachable

No deep interaction flows. The goal is "constructs + state + signal wired."
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import pyqtBoundSignal


# ════════════════════════════════════════════════════════════════════════════
# BaseDialog — 3 tests (architectural centerpiece)
# ════════════════════════════════════════════════════════════════════════════

class TestBaseDialog:
    """
    BaseDialog is the parent of every project dialog. Testing it directly
    is the highest-leverage thing in Phase 3.
    """

    def test_basedialog_instantiates_with_dark_theme(self, qtbot, theme_manager_dark):
        from ui.base_dialog import BaseDialog
        dlg = BaseDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert dlg._is_dark is True

    def test_basedialog_instantiates_with_light_theme(self, qtbot, theme_manager_light):
        from ui.base_dialog import BaseDialog
        dlg = BaseDialog(theme_manager_light)
        qtbot.addWidget(dlg)
        assert dlg._is_dark is False

    def test_basedialog_window_title_default(self, qtbot, theme_manager_dark):
        """Default _DIALOG_TITLE class var ('Dialog') is applied to the window."""
        from ui.base_dialog import BaseDialog
        dlg = BaseDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Dialog"


# ════════════════════════════════════════════════════════════════════════════
# AboutDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestAboutDialog:
    """AboutDialog extends QDialog directly, not BaseDialog."""

    def test_aboutdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.about_dialog import AboutDialog
        dlg = AboutDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert dlg is not None
        # Window title should reference the app name
        assert "About" in dlg.windowTitle()

    def test_aboutdialog_modal_after_init(self, qtbot, theme_manager_dark):
        """About dialog is modal."""
        from ui.about_dialog import AboutDialog
        dlg = AboutDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert dlg.isModal() is True


# ════════════════════════════════════════════════════════════════════════════
# BatchDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestBatchDialog:
    def test_batchdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.batch_dialog import BatchDialog
        dlg = BatchDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert "Batch" in dlg.windowTitle()

    def test_batchdialog_worker_signals_via_thread_class(self, qtbot, theme_manager_dark):
        """
        BatchWorkerThread defines progress_update / file_processed /
        finished_processing signals. Verify the class exposes them.
        """
        from ui.batch_dialog import BatchWorkerThread
        for sig_name in ("progress_update", "file_processed", "finished_processing"):
            assert hasattr(BatchWorkerThread, sig_name)


# ════════════════════════════════════════════════════════════════════════════
# CompareDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestCompareDialog:
    def test_comparedialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.compare_dialog import CompareDialog
        dlg = CompareDialog(theme_manager_dark, "Arial",
                            "alpha\nbeta", "alpha\nBETA")
        qtbot.addWidget(dlg)
        assert "Compare" in dlg.windowTitle()

    def test_comparedialog_merge_applied_signal_exists(self, qtbot, theme_manager_dark):
        from ui.compare_dialog import CompareDialog
        dlg = CompareDialog(theme_manager_dark, "Arial", "x", "y")
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "merge_applied")
        assert isinstance(dlg.merge_applied, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# EncodingDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestEncodingDialog:
    def test_encodingdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.encoding_dialog import EncodingDialog
        dlg = EncodingDialog(theme_manager_dark, "Arial", "Hello World")
        qtbot.addWidget(dlg)
        assert "Encoding" in dlg.windowTitle()

    def test_encodingdialog_signal_exists(self, qtbot, theme_manager_dark):
        from ui.encoding_dialog import EncodingDialog
        dlg = EncodingDialog(theme_manager_dark, "Arial", "")
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "encoding_applied")
        assert isinstance(dlg.encoding_applied, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# ExportDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestExportDialog:
    def test_exportdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.export_dialog import ExportDialog
        dlg = ExportDialog(theme_manager_dark, "Arial", "sample text")
        qtbot.addWidget(dlg)
        assert "Export" in dlg.windowTitle()

    def test_exportdialog_signal_exists(self, qtbot, theme_manager_dark):
        from ui.export_dialog import ExportDialog
        dlg = ExportDialog(theme_manager_dark, "Arial", "")
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "export_completed")
        assert isinstance(dlg.export_completed, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# FindReplaceDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestFindReplaceDialog:
    def test_findreplacedialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.find_replace_dialog import FindReplaceDialog
        dlg = FindReplaceDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert "Find" in dlg.windowTitle()

    def test_findreplacedialog_signal_exists(self, qtbot, theme_manager_dark):
        from ui.find_replace_dialog import FindReplaceDialog
        dlg = FindReplaceDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "find_requested")
        assert isinstance(dlg.find_requested, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# PresetDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestPresetDialog:
    def test_presetdialog_instantiates(self, qtbot, theme_manager_dark, preset_manager_empty):
        from ui.preset_dialog import PresetDialog
        dlg = PresetDialog(theme_manager_dark, preset_manager_empty)
        qtbot.addWidget(dlg)
        assert "Preset" in dlg.windowTitle()

    def test_presetdialog_signal_exists(self, qtbot, theme_manager_dark, preset_manager_empty):
        from ui.preset_dialog import PresetDialog
        dlg = PresetDialog(theme_manager_dark, preset_manager_empty)
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "preset_saved")
        assert isinstance(dlg.preset_saved, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# RegexBuilderDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestRegexBuilderDialog:
    def test_regexbuilderdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.regex_builder_dialog import RegexBuilderDialog
        dlg = RegexBuilderDialog(theme_manager_dark, "Arial", "test input")
        qtbot.addWidget(dlg)
        assert "Regex" in dlg.windowTitle()

    def test_regexbuilderdialog_signal_exists(self, qtbot, theme_manager_dark):
        from ui.regex_builder_dialog import RegexBuilderDialog
        dlg = RegexBuilderDialog(theme_manager_dark, "Arial", "")
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "pattern_applied")
        assert isinstance(dlg.pattern_applied, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# SettingsDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestSettingsDialog:
    def test_settingsdialog_instantiates(self, qtbot, tmp_settings, theme_manager_dark):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(tmp_settings, theme_manager_dark)
        qtbot.addWidget(dlg)
        assert "Settings" in dlg.windowTitle()

    def test_settingsdialog_signal_exists(self, qtbot, tmp_settings, theme_manager_dark):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(tmp_settings, theme_manager_dark)
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "theme_change_requested")
        assert isinstance(dlg.theme_change_requested, pyqtBoundSignal)


# ════════════════════════════════════════════════════════════════════════════
# WatchFolderDialog — 2 tests
# ════════════════════════════════════════════════════════════════════════════

class TestWatchFolderDialog:
    def test_watchfolderdialog_instantiates(self, qtbot, theme_manager_dark):
        from ui.watch_folder_dialog import WatchFolderDialog
        dlg = WatchFolderDialog(theme_manager_dark)
        qtbot.addWidget(dlg)
        assert "Watch" in dlg.windowTitle()

    def test_watchfolderdialog_signal_exists_on_rule_widget(self, qtbot):
        """
        rule_changed and rule_deleted signals are defined on RuleEditWidget,
        the inner widget the dialog uses to manage individual watch rules.
        """
        from ui.watch_folder_dialog import RuleEditWidget
        # Just verify the class has the signals defined as class attributes
        for sig_name in ("rule_changed", "rule_deleted"):
            assert hasattr(RuleEditWidget, sig_name), f"Missing signal: {sig_name}"
