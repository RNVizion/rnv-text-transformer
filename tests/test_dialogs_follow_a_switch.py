"""
tests/test_dialogs_follow_a_switch.py
=====================================
RNV-DIALOG-SWITCH, 2026-09-27. A window open through a theme switch is
styled, after the switch, as the same window opened in the new mode.

Two faults, found by the fleet's switch-open sweep:

1. Find, Find & Replace, the Regex Builder and Watch Folders are non-modal,
   so the theme can be cycled while one is open. None followed: each was
   built, shown and never referred to again, so the main window's
   _refresh_open_dialogs_theme() could not reach it. After dark -> light the
   whole dialog kept dark -- grounds, fields, buttons, the pattern tables.
2. The Settings dialog switches the mode itself, from its Default Theme box,
   and restyled its own sheet alone: the tab headings, the muted
   descriptions and the gold tips kept the mode it was opened in.

In the two classes that switch whole windows, the first test is the general
one: after a switch, every widget carries the stylesheet a window opened in
that mode gives it. The rest pin what a stylesheet does not show -- a status
line that follows its state, the matches painted into the Regex Builder's
test pane -- and the mechanism: the main window keeps each open dialog,
forgets it when it closes, and BaseDialog.refresh_theme() keeps a dialog's
extended styles.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from core.theme_manager import ThemeManager
from ui.base_dialog import BaseDialog
from ui.regex_builder_dialog import RegexBuilderDialog
from ui.settings_dialog import SettingsDialog
from utils.dialog_styles import DialogStyleManager

OPENERS = ("_open_find_dialog", "_open_replace_dialog",
           "_open_regex_builder_dialog", "_open_watch_folder_dialog")


def _styles(dlg) -> list:
    return [dlg.styleSheet()] + [(type(w).__name__, w.objectName(), w.styleSheet())
                                 for w in dlg.findChildren(QWidget)]


def _opened(win, opener: str) -> BaseDialog:
    """The dialog the main window's own opener shows."""
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog)
           if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    return new[0]


def _palette(win) -> dict:
    return DialogStyleManager.get_colors(win.theme_manager.is_dark_mode)


def _ink(label) -> str:
    from PyQt6.QtGui import QPalette
    label.ensurePolished()
    return label.palette().color(QPalette.ColorRole.WindowText).name()


# ─────────────────────────────────────────────────────────────────────────────
# 1. The four non-modal dialogs, opened and switched with the main window's
#    own opener and theme cycle
# ─────────────────────────────────────────────────────────────────────────────

class TestTheNonModalDialogsFollowASwitch:

    @pytest.mark.parametrize("opener", OPENERS)
    def test_a_switched_dialog_is_styled_as_one_opened_in_that_mode(self, main_window, opener):
        win = main_window
        dlg = _opened(win, opener)
        modes = []
        for _ in range(3):                                   # every mode, and back
            win._cycle_theme()
            QApplication.processEvents()
            modes.append(win.theme_manager.current_theme)
            fresh = _opened(win, opener)
            a, b = _styles(dlg), _styles(fresh)
            assert len(a) == len(b), (opener, modes[-1], len(a), len(b))
            differ = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
            assert not differ, (opener, modes[-1], differ[:2])
            fresh.close()
        assert {"dark", "light"} <= set(modes), modes
        dlg.close()

    def test_watch_folders_without_watchdog_warns_in_the_new_mode(self, main_window, monkeypatch):
        """The warning shown when watchdog is missing is coloured error."""
        import ui.watch_folder_dialog as watch
        monkeypatch.setattr(watch, "WATCHDOG_AVAILABLE", False)
        win = main_window
        dlg = _opened(win, "_open_watch_folder_dialog")
        warning = [w for w in dlg.findChildren(QLabel) if "watchdog" in w.text()]
        assert len(warning) == 1
        for _ in range(3):
            win._cycle_theme()
            assert _ink(warning[0]) == _palette(win)["error"].lower()
        dlg.close()

    def test_two_find_dialogs_open_at_once_both_follow(self, main_window):
        win = main_window
        first, second = _opened(win, "_open_find_dialog"), _opened(win, "_open_find_dialog")
        for _ in range(3):
            win._cycle_theme()
            muted = _palette(win)["text_muted"].lower()
            assert _ink(first.status_label) == muted
            assert _ink(second.status_label) == muted
        first.close()
        second.close()

    def test_the_find_dialog_apply_find_opens_follows_too(self, main_window):
        """The Regex Builder's Apply Find, with no replacement, opens Find
        with the pattern -- a second road to a non-modal Find."""
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText("qu")
        before = {id(d) for d in win.findChildren(BaseDialog)}
        builder._apply_find()
        QApplication.processEvents()
        found = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
        assert len(found) == 1 and found[0].find_input.text() == "qu"
        for _ in range(3):
            win._cycle_theme()
            fresh = _opened(win, "_open_find_dialog")
            assert _styles(found[0]) == _styles(fresh), win.theme_manager.current_theme
            fresh.close()
        found[0].close()

    def test_a_closed_dialog_is_let_go(self, main_window):
        win = main_window
        for opener in OPENERS:
            dlg = _opened(win, opener)
            assert dlg in win._open_dialogs, opener
            dlg.close()
            QApplication.processEvents()
            assert dlg not in win._open_dialogs, opener


class TestTheRegexBuilderFollowsItsState:

    def test_the_status_line_keeps_its_state_across_a_switch(self, main_window):
        win = main_window
        dlg = _opened(win, "_open_regex_builder_dialog")
        for pattern, key in (("qu", "success"), ("(", "error"), ("", "text_muted")):
            dlg.pattern_input.setText(pattern)
            for _ in range(3):
                win._cycle_theme()
                assert _ink(dlg.status_label) == _palette(win)[key].lower(), (pattern, key)
        dlg.close()

    def test_the_matches_are_painted_again_in_the_new_mode(self, main_window):
        win = main_window
        win.text_input.setPlainText("The quick brown fox jumps over the lazy dog.")
        dlg = _opened(win, "_open_regex_builder_dialog")
        dlg.pattern_input.setText("o")
        dlg._update_matches()
        assert dlg._current_matches
        start = dlg._current_matches[0].start
        for _ in range(3):
            win._cycle_theme()
            cursor = dlg.test_text.textCursor()
            cursor.setPosition(start + 1)
            painted = cursor.charFormat().background().color().name()
            want = (RegexBuilderDialog._MATCH_COLOR_DARK if win.theme_manager.is_dark_mode
                    else RegexBuilderDialog._MATCH_COLOR_LIGHT)
            assert painted == want.lower(), (win.theme_manager.current_theme, painted, want)
        dlg.close()


# ─────────────────────────────────────────────────────────────────────────────
# 2. The Settings dialog, switched by its own Default Theme box
# ─────────────────────────────────────────────────────────────────────────────

class TestSettingsFollowsItsOwnThemeBox:

    NAMES = {"Dark Mode": "dark", "Light Mode": "light", "Image Mode": "image"}

    @staticmethod
    def _theme_manager(mode: str) -> ThemeManager:
        tm = ThemeManager()
        tm.detect_image_resources()
        tm.set_theme(mode)
        return tm

    def _walk(self, dlg) -> list[str]:
        """Every ordered pair of different modes the box offers."""
        items = [dlg.theme_combo.itemText(i) for i in range(dlg.theme_combo.count())]
        assert {"Dark Mode", "Light Mode"} <= set(items), items
        walk = []
        for a in items:
            for b in items:
                if a != b:
                    walk += [a, b]
        return walk

    def test_switched_by_its_box_it_is_styled_as_one_opened_in_that_mode(self, qtbot, tmp_settings):
        dlg = SettingsDialog(tmp_settings, self._theme_manager("dark"))
        qtbot.addWidget(dlg)
        for text in self._walk(dlg):
            dlg.theme_combo.setCurrentText(text)
            fresh = SettingsDialog(tmp_settings, self._theme_manager(self.NAMES[text]))
            qtbot.addWidget(fresh)
            a, b = _styles(dlg), _styles(fresh)
            assert len(a) == len(b), (text, len(a), len(b))
            differ = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
            assert not differ, (text, differ[:2])

    def test_the_headings_descriptions_and_tips_change_colour(self, qtbot, tmp_settings):
        """The labels that read the mode, by the ink Qt draws them in: every
        one of them differs between dark and light, and follows the box."""
        dlg = SettingsDialog(tmp_settings, self._theme_manager("dark"))
        qtbot.addWidget(dlg)
        labels = [w for w in dlg.findChildren(QLabel) if w.styleSheet() and "color" in w.styleSheet()]
        dark = [_ink(w) for w in labels]
        dlg.theme_combo.setCurrentText("Light Mode")
        light = [_ink(w) for w in labels]
        moved = [w.text()[:30] for w, a, b in zip(labels, dark, light) if a != b]
        assert len(moved) == len(labels) >= 17, (len(moved), len(labels))
        dlg.theme_combo.setCurrentText("Dark Mode")
        assert [_ink(w) for w in labels] == dark


# ─────────────────────────────────────────────────────────────────────────────
# 3. The mechanism, in BaseDialog
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseDialogRefresh:

    def test_refresh_keeps_the_components_the_dialog_was_built_with(self, qtbot):
        tm = ThemeManager()
        tm.set_theme("dark")
        dlg = BaseDialog(tm)
        qtbot.addWidget(dlg)
        dlg.apply_extended_styling("tab", "table")
        tm.set_theme("light")
        dlg.refresh_theme()
        assert dlg.styleSheet() == DialogStyleManager.get_extended_stylesheet(
            False, dlg.font_family, "tab", "table")
        dlg.apply_base_styling()
        tm.set_theme("dark")
        dlg.refresh_theme()
        assert dlg.styleSheet() == DialogStyleManager.get_dialog_stylesheet(True, dlg.font_family)

    def test_a_widget_styled_again_keeps_the_later_sheet(self, qtbot):
        tm = ThemeManager()
        tm.set_theme("dark")
        dlg = BaseDialog(tm)
        qtbot.addWidget(dlg)
        label = QLabel("status", dlg)
        dlg._style_for_mode(label, lambda: f"color: {dlg.get_colors()['success']};")
        dlg._style_for_mode(label, lambda: f"color: {dlg.get_colors()['error']};")
        tm.set_theme("light")
        dlg.refresh_theme()
        assert label.styleSheet() == f"color: {DialogStyleManager.LIGHT['error']};"
        assert len(dlg._mode_styled) == 1
