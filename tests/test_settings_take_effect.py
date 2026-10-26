"""
tests/test_settings_take_effect.py
==================================
Two settings that were saved but not applied.

- **Maximum recent files.** The list kept ten files whatever the setting
  said: Load and drag-and-drop called ``add_recent_file`` with its default
  of 10, and ``MainWindow._add_recent_file``, which reads the setting, had
  no caller. Lowering the setting now trims the list at once, and the
  limit is applied again at startup.
- **Show button tooltips.** Turned off, it was saved but not read at
  startup, so the button tooltips were back at the next start.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QFileDialog


def _files(n: int) -> list[str]:
    """n recent-file paths, newest first."""
    return [f"/recent/file_{i}.txt" for i in range(n)]


def _load(main_window, path, monkeypatch) -> None:
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(path), "Text Files (*.txt)")),
    )
    main_window._load_file()
    main_window._file_loader_thread.wait(5000)


@pytest.fixture
def opened_file(tmp_path):
    path = tmp_path / "opened.txt"
    path.write_text("some text", encoding="utf-8")
    return path


# ── Maximum recent files ──────────────────────────────────────────────────────

def test_loading_a_file_keeps_the_setting_number_of_recent_files(
    main_window, opened_file, monkeypatch
):
    sm = main_window.settings_manager
    sm.save_recent_files_max(3)
    sm.save_recent_files(_files(3))
    _load(main_window, opened_file, monkeypatch)
    assert sm.load_recent_files() == [str(opened_file)] + _files(2)


def test_dropping_a_file_keeps_the_setting_number_of_recent_files(
    main_window, opened_file
):
    sm = main_window.settings_manager
    sm.save_recent_files_max(2)
    sm.save_recent_files(_files(2))
    main_window._handle_dropped_file(str(opened_file))
    main_window._file_loader_thread.wait(5000)
    assert sm.load_recent_files() == [str(opened_file)] + _files(1)


def test_disabled_keeps_no_recent_files(main_window, opened_file, monkeypatch):
    sm = main_window.settings_manager
    sm.save_recent_files_max(0)
    sm.clear_recent_files()
    _load(main_window, opened_file, monkeypatch)
    assert sm.load_recent_files() == []


def test_lowering_the_maximum_in_settings_trims_the_list_at_once(main_window):
    from ui.settings_dialog import SettingsDialog
    sm = main_window.settings_manager
    sm.save_recent_files(_files(8))
    dialog = SettingsDialog(
        settings_manager=sm,
        theme_manager=main_window.theme_manager,
        font_family=main_window.font_family,
        parent=main_window,
    )
    try:
        dialog.recent_files_spin.setValue(3)
        assert sm.load_recent_files() == _files(3)
        # The History tab shows the trimmed list too
        assert dialog.recent_files_list.count() == 3
    finally:
        dialog.deleteLater()


def test_startup_applies_the_saved_maximum(qtbot, tmp_settings):
    from ui.main_window import MainWindow
    tmp_settings.save_recent_files(_files(8))
    tmp_settings.save_recent_files_max(2)
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.settings_manager.load_recent_files() == _files(2)


# ── Show button tooltips ──────────────────────────────────────────────────────

def test_button_tooltips_saved_off_stay_off_after_a_restart(qtbot, tmp_settings):
    from ui.main_window import MainWindow
    tmp_settings.save_show_tooltips(False)
    win = MainWindow()
    qtbot.addWidget(win)
    buttons = [win.transform_btn, win.copy_btn, win.load_btn, win.save_btn,
               win.theme_button, win.settings_button, win.mode_combo]
    assert [b.toolTip() for b in buttons] == [""] * len(buttons)


def test_button_tooltips_saved_on_are_there_at_startup(qtbot, tmp_settings):
    from ui.main_window import MainWindow
    tmp_settings.save_show_tooltips(True)
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.transform_btn.toolTip() == "Transform text (Ctrl+T)"
