"""Find, Find & Replace, the Regex Builder and Watch Folders follow a mode switch; Settings follows its own theme box

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (165523d).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-27: "Yes we can build the reachables" -- the switch-open
sweep's two reachable findings in this app.

1. Find, Find & Replace, the Regex Builder and Watch Folders are non-modal,
   so the theme can be cycled while one is open. None followed: each was
   built, shown and never referred to again, so _refresh_open_dialogs_theme()
   -- which refreshes the Compare dialog -- could not reach it. After a
   switch from dark to light the whole dialog kept dark. The main window
   keeps each one while it is open now, lets it go when it closes, and
   refreshes it on every switch -- the Find dialog the Regex Builder's
   Apply Find opens included.
2. The Settings dialog switches the mode itself, from its Default Theme box,
   and restyled its own sheet alone: its tab headings, muted descriptions
   and gold tips kept the mode it was opened in.

One mechanism in BaseDialog serves both. refresh_theme() builds the dialog's
sheet again with the components it was built with -- it applied the base
sheet alone, which would have dropped the Regex Builder's tab, table and
list styles -- and sets again every sheet registered with _style_for_mode(),
the helper of the same name the picker's windows use. The sheets are the
same text as before. The Regex Builder also paints its matches again in the
new mode's colour, and its status line keeps its state's colour (muted,
success or error) across a switch.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-text-transformer'
SENTINEL = 'RNV-DIALOG-SWITCH'
SENTINEL_FILE = 'ui/base_dialog.py'
GUARD = 'tests/test_dialogs_follow_a_switch.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_dialogs_follow_a_switch.py']
DESCRIPTION = 'Find, Find & Replace, the Regex Builder and Watch Folders follow a mode switch; Settings follows its own theme box'

_COV = [sys.executable, "-m", "coverage", "run", "--source=core,utils,ui,cli",
        "--branch"]
SUITES = [
    ("CI step 1: unittest test_rnv_text_transformer",
     _COV[:4] + ["--data-file=.coverage.unittest"] + _COV[4:]
     + ["-m", "unittest", "test_rnv_text_transformer"]),
    ("CI step 2: pytest tests/ --benchmark-disable",
     _COV[:4] + ["--data-file=.coverage.pytest"] + _COV[4:]
     + ["-m", "pytest", "tests/", "--benchmark-disable"]),
]

#: The environment the workflow sets for both steps.
CI_ENV = {"QT_QPA_PLATFORM": "offscreen"}


def post_write() -> None:
    """CI's environment: both test steps run with QT_QPA_PLATFORM=offscreen."""
    os.environ.update(CI_ENV)
    print("CI environment: " + ", ".join(f"{k}={v}" for k, v in CI_ENV.items()))

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests.yml': '22c4f261f69cda029e0801f148e9b061e3bd65b5c9472b1bf321fc998b5a0434'}

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "base_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ['the modal dialogs -- About, Batch, Export, Encoding, Preset Manager and Preset Editor. Each blocks the theme button and the shortcut while it is open, so no switch reaches it; the sweep lists them.', "the match highlights Find draws in the main window's text. Find paints them when it runs, in the accent of the mode it runs in; a switch leaves them in that colour until the next Find.", "every stylesheet's text: the same sheets are set, now again on a switch."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/base_dialog.py',
             'if TYPE_CHECKING:\n    from core.theme_manager import ThemeManager\n',
             'if TYPE_CHECKING:\n    from collections.abc import Callable\n\n    from core.theme_manager import ThemeManager\n')
    tree.sub('ui/base_dialog.py',
             "    __slots__ = ('theme_manager', 'font_family', '_is_dark')\n",
             "    __slots__ = ('theme_manager', 'font_family', '_is_dark',\n                 '_style_components', '_mode_styled')\n")
    tree.sub('ui/base_dialog.py',
             '        self.theme_manager = theme_manager\n        self.font_family = font_family\n        self._is_dark = self._detect_dark_theme()\n        \n        self._configure_window()\n',
             "        self.theme_manager = theme_manager\n        self.font_family = font_family\n        self._is_dark = self._detect_dark_theme()\n        \n        # RNV-DIALOG-SWITCH 2026-09-27: what refresh_theme() builds again.\n        # The components of the dialog's own sheet, as the last call to\n        # apply_base_styling() or apply_extended_styling() set them, and\n        # every sheet set with _style_for_mode(), by widget.\n        self._style_components: tuple[str, ...] = ()\n        self._mode_styled: dict[QWidget, Callable[[], str]] = {}\n        \n        self._configure_window()\n")
    tree.sub('ui/base_dialog.py',
             '        from utils.dialog_styles import DialogStyleManager\n        stylesheet = DialogStyleManager.get_dialog_stylesheet(\n            self._is_dark, \n            self.font_family\n        )\n        self.setStyleSheet(stylesheet)\n',
             '        from utils.dialog_styles import DialogStyleManager\n        self._style_components = ()\n        stylesheet = DialogStyleManager.get_dialog_stylesheet(\n            self._is_dark, \n            self.font_family\n        )\n        self.setStyleSheet(stylesheet)\n')
    tree.sub('ui/base_dialog.py',
             '        from utils.dialog_styles import DialogStyleManager\n        stylesheet = DialogStyleManager.get_extended_stylesheet(\n',
             '        from utils.dialog_styles import DialogStyleManager\n        self._style_components = components\n        stylesheet = DialogStyleManager.get_extended_stylesheet(\n')
    tree.sub('ui/base_dialog.py',
             '        Call this when the application theme changes to update the dialog.\n        """\n        self._is_dark = self._detect_dark_theme()\n        self.apply_base_styling()\n',
             '        Call this when the application theme changes to update the dialog.\n        \n        RNV-DIALOG-SWITCH 2026-09-27: the dialog\'s sheet is built again\n        with the components it was built with. This applied the base sheet\n        alone, which dropped the tab, table and list styles of a dialog\n        built with them. Then every sheet set with _style_for_mode() is set\n        again, in the new mode.\n        """\n        self._is_dark = self._detect_dark_theme()\n        if self._style_components:\n            self.apply_extended_styling(*self._style_components)\n        else:\n            self.apply_base_styling()\n        for widget, sheet in list(self._mode_styled.items()):\n            try:\n                widget.setStyleSheet(sheet())\n            except RuntimeError:  # the widget has been deleted\n                del self._mode_styled[widget]\n    \n    def _style_for_mode(self, widget: QWidget, sheet: Callable[[], str]) -> None:\n        """\n        Style widget with sheet(), now and again on every refresh_theme().\n        \n        RNV-DIALOG-SWITCH 2026-09-27 -- the helper of the same name in the\n        picker\'s Settings panel and About dialog, for the same fault. For a\n        stylesheet that reads the mode when it is set: set once, it kept\n        the mode the dialog was opened in. A widget styled this way again\n        keeps the later sheet, so a status line whose colour follows its\n        state is set again in the colour it shows now.\n        \n        Args:\n            widget: The widget to style\n            sheet: Builds the widget\'s stylesheet from the current mode\n        """\n        widget.setStyleSheet(sheet())\n        self._mode_styled[widget] = sheet\n')
    tree.sub('ui/base_dialog.py',
             '        label = QLabel(text)\n        label.setStyleSheet(DialogStyleManager.get_header_style(self._is_dark))\n',
             '        label = QLabel(text)\n        self._style_for_mode(label, lambda: (\n            DialogStyleManager.get_header_style(self._is_dark)))\n')
    tree.sub('ui/base_dialog.py',
             '        label = QLabel(text)\n        label.setStyleSheet(DialogStyleManager.get_subtitle_style(self._is_dark))\n',
             '        label = QLabel(text)\n        self._style_for_mode(label, lambda: (\n            DialogStyleManager.get_subtitle_style(self._is_dark)))\n')
    tree.sub('ui/base_dialog.py',
             '        label = QLabel(text)\n        label.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))\n',
             '        label = QLabel(text)\n        self._style_for_mode(label, lambda: (\n            DialogStyleManager.get_description_style(self._is_dark)))\n')
    tree.sub('ui/base_dialog.py',
             '        label = QLabel(text)\n        label.setStyleSheet(DialogStyleManager.get_tip_style(self._is_dark))\n',
             '        label = QLabel(text)\n        self._style_for_mode(label, lambda: (\n            DialogStyleManager.get_tip_style(self._is_dark)))\n')
    tree.sub('ui/settings_dialog.py',
             "        # Update dialog styling for new theme\n        self.theme_manager.set_theme(theme)\n        self._is_dark = self._detect_dark_theme()\n        self.apply_extended_styling('tab', 'spinbox', 'slider', 'list', 'table')\n",
             "        # Update dialog styling for new theme. RNV-DIALOG-SWITCH 2026-09-27:\n        # refresh_theme() builds the dialog's sheet again and every label\n        # sheet that reads the mode. This restyled the dialog's own sheet\n        # alone, so the tab headings, the muted descriptions and the gold\n        # tips kept the mode the dialog was opened in.\n        self.theme_manager.set_theme(theme)\n        self.refresh_theme()\n")
    tree.sub('ui/settings_dialog.py',
             '        shortcut_info.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))\n',
             '        self._style_for_mode(shortcut_info, lambda: (\n            DialogStyleManager.get_description_style(self._is_dark)))\n')
    tree.sub('ui/settings_dialog.py',
             '            desc_label.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))\n',
             '            self._style_for_mode(desc_label, lambda: (\n                DialogStyleManager.get_description_style(self._is_dark)))\n')
    tree.sub('ui/settings_dialog.py',
             '        options_info.setStyleSheet(DialogStyleManager.get_description_style(self._is_dark))\n',
             '        self._style_for_mode(options_info, lambda: (\n            DialogStyleManager.get_description_style(self._is_dark)))\n')
    tree.sub('ui/find_replace_dialog.py',
             '        self.status_label = QLabel("")\n        c = self.get_colors()\n        self.status_label.setStyleSheet(f"color: {c[\'text_muted\']};")\n',
             '        self.status_label = QLabel("")\n        self._style_for_mode(self.status_label, lambda: (\n            f"color: {self.get_colors()[\'text_muted\']};"))\n')
    tree.sub('ui/regex_builder_dialog.py',
             '        self._populate_patterns()\n        self._load_text()\n    \n\n    def _setup_ui(self) -> None:\n',
             '        self._populate_patterns()\n        self._load_text()\n    \n    def refresh_theme(self) -> None:\n        """\n        Refresh the dialog after a theme switch, and paint the matches again.\n        \n        RNV-DIALOG-SWITCH 2026-09-27: the matches in the test pane are painted\n        in the mode\'s regex_match_bg when they are found; a switch left them\n        in the old mode\'s until the next edit.\n        """\n        super().refresh_theme()\n        if self._current_matches:\n            self._highlight_matches()\n    \n\n    def _setup_ui(self) -> None:\n')
    tree.sub('ui/regex_builder_dialog.py',
             '        self.status_label = QLabel("Ready")\n        c = self.get_colors()\n        self.status_label.setStyleSheet(f"color: {c[\'text_muted\']};")\n',
             '        self.status_label = QLabel("Ready")\n        self._set_status_colour(\'text_muted\')\n')
    tree.sub('ui/regex_builder_dialog.py',
             '                self.status_label.setStyleSheet(f"color: {self.get_colors()[\'success\']};")\n',
             "                self._set_status_colour('success')\n")
    tree.sub('ui/regex_builder_dialog.py',
             '                self.status_label.setStyleSheet(f"color: {self.get_colors()[\'error\']};")\n',
             "                self._set_status_colour('error')\n")
    tree.sub('ui/regex_builder_dialog.py',
             '            self.status_label.setStyleSheet(f"color: {self.get_colors()[\'text_muted\']};")\n',
             "            self._set_status_colour('text_muted')\n")
    tree.sub('ui/regex_builder_dialog.py',
             '\n            self.status_label.setStyleSheet(f"color: {self.get_colors()[\'error\']};")\n',
             "\n            self._set_status_colour('error')\n")
    tree.sub('ui/regex_builder_dialog.py',
             '        c = self.get_colors()\n        self.status_label.setStyleSheet(f"color: {c[\'success\']};" if count > 0 else f"color: {c[\'text_muted\']};")\n',
             "        self._set_status_colour('success' if count > 0 else 'text_muted')\n")
    tree.sub('ui/regex_builder_dialog.py',
             '    def _on_replacement_changed(self, text: str) -> None:\n',
             '    def _set_status_colour(self, key: str) -> None:\n        """\n        Colour the status line with the palette\'s `key`, in the dialog\'s mode.\n        \n        RNV-DIALOG-SWITCH 2026-09-27: through _style_for_mode(), so a theme\n        switch sets it again in the new mode, in the colour of the state it\n        shows (text_muted, success or error).\n        """\n        self._style_for_mode(self.status_label, lambda: (\n            f"color: {self.get_colors()[key]};"))\n    \n    def _on_replacement_changed(self, text: str) -> None:\n')
    tree.sub('ui/watch_folder_dialog.py',
             '            warning.setStyleSheet(f"color: {self.get_colors()[\'error\']}; font-weight: bold; padding: 10px;")\n',
             '            self._style_for_mode(warning, lambda: (\n                f"color: {self.get_colors()[\'error\']}; font-weight: bold; padding: 10px;"))\n')
    tree.sub('ui/main_window.py',
             'from pathlib import Path\nfrom typing import TYPE_CHECKING\n',
             'from functools import partial\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING\n')
    tree.sub('ui/main_window.py',
             'from ui.settings_dialog import SettingsDialog\n',
             'from ui.base_dialog import BaseDialog\nfrom ui.settings_dialog import SettingsDialog\n')
    tree.sub('ui/main_window.py',
             '            target_text_edit=self.text_input,\n            replace_mode=False,\n            parent=self\n        )\n        dialog.show()\n',
             '            target_text_edit=self.text_input,\n            replace_mode=False,\n            parent=self\n        )\n        self._track_open_dialog(dialog)\n        dialog.show()\n')
    tree.sub('ui/main_window.py',
             '            target_text_edit=self.text_input,\n            replace_mode=True,\n            parent=self\n        )\n        dialog.show()\n',
             '            target_text_edit=self.text_input,\n            replace_mode=True,\n            parent=self\n        )\n        self._track_open_dialog(dialog)\n        dialog.show()\n')
    tree.sub('ui/main_window.py',
             '        # Connect pattern applied signal\n        dialog.pattern_applied.connect(self._on_regex_pattern_applied)\n        \n        dialog.show()\n',
             '        # Connect pattern applied signal\n        dialog.pattern_applied.connect(self._on_regex_pattern_applied)\n        \n        self._track_open_dialog(dialog)\n        dialog.show()\n')
    tree.sub('ui/main_window.py',
             '        """Open Watch Folder dialog for automatic file transformation."""\n        dialog = WatchFolderDialog(\n            theme_manager=self.theme_manager,\n            font_family=self.font_family,\n            parent=self\n        )\n        dialog.show()\n',
             '        """Open Watch Folder dialog for automatic file transformation."""\n        dialog = WatchFolderDialog(\n            theme_manager=self.theme_manager,\n            font_family=self.font_family,\n            parent=self\n        )\n        self._track_open_dialog(dialog)\n        dialog.show()\n')
    tree.sub('ui/main_window.py',
             '            dialog.find_input.setText(pattern)\n            dialog.regex_check.setChecked(True)\n            dialog.show()\n',
             '            dialog.find_input.setText(pattern)\n            dialog.regex_check.setChecked(True)\n            self._track_open_dialog(dialog)\n            dialog.show()\n')
    tree.sub('ui/main_window.py',
             '    def _refresh_open_dialogs_theme(self) -> None:\n        """\n        Propagate the current theme to any open non-modal dialog.\n        \n        Called whenever the application theme changes (via Ctrl+Shift+T or\n        from the settings dialog). The compare dialog is the only non-modal\n        one — modal dialogs cannot be open during a theme cycle so they\n        don\'t need this. Wrapped defensively in case the Qt object was\n        destroyed without the finished signal firing.\n        """\n        compare_dialog = getattr(self, \'_compare_dialog\', None)\n        if compare_dialog is not None:\n            try:\n                compare_dialog.refresh_theme()\n            except RuntimeError:\n                self._compare_dialog = None\n',
             '    def _track_open_dialog(self, dialog: BaseDialog) -> None:\n        """\n        Keep a non-modal dialog where _refresh_open_dialogs_theme() reaches\n        it, for as long as it is open.\n        \n        RNV-DIALOG-SWITCH 2026-09-27. Find, Find & Replace, the Regex Builder\n        and Watch Folders are non-modal, so the theme can be cycled while one\n        is open -- and nothing referred to them after show(), so they kept\n        the mode they were opened in. More than one can be open at once, and\n        Find opens from the Regex Builder\'s Apply Find as well as from here.\n        """\n        if not hasattr(self, \'_open_dialogs\'):\n            self._open_dialogs: list[BaseDialog] = []\n        self._open_dialogs.append(dialog)\n        dialog.finished.connect(partial(self._forget_open_dialog, dialog))\n    \n    def _forget_open_dialog(self, dialog: BaseDialog, _result: int = 0) -> None:\n        """Stop refreshing a dialog once it has closed."""\n        if dialog in getattr(self, \'_open_dialogs\', ()):\n            self._open_dialogs.remove(dialog)\n    \n    def _refresh_open_dialogs_theme(self) -> None:\n        """\n        Propagate the current theme to any open non-modal dialog.\n        \n        Called whenever the application theme changes (via Ctrl+Shift+T or\n        from the settings dialog). The non-modal dialogs are Compare and the\n        ones _track_open_dialog() keeps: Find, Find & Replace, the Regex\n        Builder and Watch Folders. A modal dialog blocks the theme button and\n        the shortcut while it is open; the settings dialog, which switches\n        the theme itself, restyles itself. Wrapped defensively in case the\n        Qt object was destroyed without the finished signal firing.\n        """\n        compare_dialog = getattr(self, \'_compare_dialog\', None)\n        if compare_dialog is not None:\n            try:\n                compare_dialog.refresh_theme()\n            except RuntimeError:\n                self._compare_dialog = None\n        for dialog in list(getattr(self, \'_open_dialogs\', ())):\n            try:\n                dialog.refresh_theme()\n            except RuntimeError:\n                self._forget_open_dialog(dialog)\n')
    if (tree.root / 'tests/test_dialogs_follow_a_switch.py').exists():
        raise Stop('tests/test_dialogs_follow_a_switch.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_dialogs_follow_a_switch.py', '"""\ntests/test_dialogs_follow_a_switch.py\n=====================================\nRNV-DIALOG-SWITCH, 2026-09-27. A window open through a theme switch is\nstyled, after the switch, as the same window opened in the new mode.\n\nTwo faults, found by the fleet\'s switch-open sweep:\n\n1. Find, Find & Replace, the Regex Builder and Watch Folders are non-modal,\n   so the theme can be cycled while one is open. None followed: each was\n   built, shown and never referred to again, so the main window\'s\n   _refresh_open_dialogs_theme() could not reach it. After dark -> light the\n   whole dialog kept dark -- grounds, fields, buttons, the pattern tables.\n2. The Settings dialog switches the mode itself, from its Default Theme box,\n   and restyled its own sheet alone: the tab headings, the muted\n   descriptions and the gold tips kept the mode it was opened in.\n\nIn the two classes that switch whole windows, the first test is the general\none: after a switch, every widget carries the stylesheet a window opened in\nthat mode gives it. The rest pin what a stylesheet does not show -- a status\nline that follows its state, the matches painted into the Regex Builder\'s\ntest pane -- and the mechanism: the main window keeps each open dialog,\nforgets it when it closes, and BaseDialog.refresh_theme() keeps a dialog\'s\nextended styles.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication, QLabel, QWidget\n\nfrom core.theme_manager import ThemeManager\nfrom ui.base_dialog import BaseDialog\nfrom ui.regex_builder_dialog import RegexBuilderDialog\nfrom ui.settings_dialog import SettingsDialog\nfrom utils.dialog_styles import DialogStyleManager\n\nOPENERS = ("_open_find_dialog", "_open_replace_dialog",\n           "_open_regex_builder_dialog", "_open_watch_folder_dialog")\n\n\ndef _styles(dlg) -> list:\n    return [dlg.styleSheet()] + [(type(w).__name__, w.objectName(), w.styleSheet())\n                                 for w in dlg.findChildren(QWidget)]\n\n\ndef _opened(win, opener: str) -> BaseDialog:\n    """The dialog the main window\'s own opener shows."""\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog)\n           if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    return new[0]\n\n\ndef _palette(win) -> dict:\n    return DialogStyleManager.get_colors(win.theme_manager.is_dark_mode)\n\n\ndef _ink(label) -> str:\n    from PyQt6.QtGui import QPalette\n    label.ensurePolished()\n    return label.palette().color(QPalette.ColorRole.WindowText).name()\n\n\n# ─────────────────────────────────────────────────────────────────────────────\n# 1. The four non-modal dialogs, opened and switched with the main window\'s\n#    own opener and theme cycle\n# ─────────────────────────────────────────────────────────────────────────────\n\nclass TestTheNonModalDialogsFollowASwitch:\n\n    @pytest.mark.parametrize("opener", OPENERS)\n    def test_a_switched_dialog_is_styled_as_one_opened_in_that_mode(self, main_window, opener):\n        win = main_window\n        dlg = _opened(win, opener)\n        modes = []\n        for _ in range(3):                                   # every mode, and back\n            win._cycle_theme()\n            QApplication.processEvents()\n            modes.append(win.theme_manager.current_theme)\n            fresh = _opened(win, opener)\n            a, b = _styles(dlg), _styles(fresh)\n            assert len(a) == len(b), (opener, modes[-1], len(a), len(b))\n            differ = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]\n            assert not differ, (opener, modes[-1], differ[:2])\n            fresh.close()\n        assert {"dark", "light"} <= set(modes), modes\n        dlg.close()\n\n    def test_watch_folders_without_watchdog_warns_in_the_new_mode(self, main_window, monkeypatch):\n        """The warning shown when watchdog is missing is coloured error."""\n        import ui.watch_folder_dialog as watch\n        monkeypatch.setattr(watch, "WATCHDOG_AVAILABLE", False)\n        win = main_window\n        dlg = _opened(win, "_open_watch_folder_dialog")\n        warning = [w for w in dlg.findChildren(QLabel) if "watchdog" in w.text()]\n        assert len(warning) == 1\n        for _ in range(3):\n            win._cycle_theme()\n            assert _ink(warning[0]) == _palette(win)["error"].lower()\n        dlg.close()\n\n    def test_two_find_dialogs_open_at_once_both_follow(self, main_window):\n        win = main_window\n        first, second = _opened(win, "_open_find_dialog"), _opened(win, "_open_find_dialog")\n        for _ in range(3):\n            win._cycle_theme()\n            muted = _palette(win)["text_muted"].lower()\n            assert _ink(first.status_label) == muted\n            assert _ink(second.status_label) == muted\n        first.close()\n        second.close()\n\n    def test_the_find_dialog_apply_find_opens_follows_too(self, main_window):\n        """The Regex Builder\'s Apply Find, with no replacement, opens Find\n        with the pattern -- a second road to a non-modal Find."""\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("qu")\n        before = {id(d) for d in win.findChildren(BaseDialog)}\n        builder._apply_find()\n        QApplication.processEvents()\n        found = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n        assert len(found) == 1 and found[0].find_input.text() == "qu"\n        for _ in range(3):\n            win._cycle_theme()\n            fresh = _opened(win, "_open_find_dialog")\n            assert _styles(found[0]) == _styles(fresh), win.theme_manager.current_theme\n            fresh.close()\n        found[0].close()\n\n    def test_a_closed_dialog_is_let_go(self, main_window):\n        win = main_window\n        for opener in OPENERS:\n            dlg = _opened(win, opener)\n            assert dlg in win._open_dialogs, opener\n            dlg.close()\n            QApplication.processEvents()\n            assert dlg not in win._open_dialogs, opener\n\n\nclass TestTheRegexBuilderFollowsItsState:\n\n    def test_the_status_line_keeps_its_state_across_a_switch(self, main_window):\n        win = main_window\n        dlg = _opened(win, "_open_regex_builder_dialog")\n        for pattern, key in (("qu", "success"), ("(", "error"), ("", "text_muted")):\n            dlg.pattern_input.setText(pattern)\n            for _ in range(3):\n                win._cycle_theme()\n                assert _ink(dlg.status_label) == _palette(win)[key].lower(), (pattern, key)\n        dlg.close()\n\n    def test_the_matches_are_painted_again_in_the_new_mode(self, main_window):\n        win = main_window\n        win.text_input.setPlainText("The quick brown fox jumps over the lazy dog.")\n        dlg = _opened(win, "_open_regex_builder_dialog")\n        dlg.pattern_input.setText("o")\n        dlg._update_matches()\n        assert dlg._current_matches\n        start = dlg._current_matches[0].start\n        for _ in range(3):\n            win._cycle_theme()\n            cursor = dlg.test_text.textCursor()\n            cursor.setPosition(start + 1)\n            painted = cursor.charFormat().background().color().name()\n            want = (RegexBuilderDialog._MATCH_COLOR_DARK if win.theme_manager.is_dark_mode\n                    else RegexBuilderDialog._MATCH_COLOR_LIGHT)\n            assert painted == want.lower(), (win.theme_manager.current_theme, painted, want)\n        dlg.close()\n\n\n# ─────────────────────────────────────────────────────────────────────────────\n# 2. The Settings dialog, switched by its own Default Theme box\n# ─────────────────────────────────────────────────────────────────────────────\n\nclass TestSettingsFollowsItsOwnThemeBox:\n\n    NAMES = {"Dark Mode": "dark", "Light Mode": "light", "Image Mode": "image"}\n\n    @staticmethod\n    def _theme_manager(mode: str) -> ThemeManager:\n        tm = ThemeManager()\n        tm.detect_image_resources()\n        tm.set_theme(mode)\n        return tm\n\n    def _walk(self, dlg) -> list[str]:\n        """Every ordered pair of different modes the box offers."""\n        items = [dlg.theme_combo.itemText(i) for i in range(dlg.theme_combo.count())]\n        assert {"Dark Mode", "Light Mode"} <= set(items), items\n        walk = []\n        for a in items:\n            for b in items:\n                if a != b:\n                    walk += [a, b]\n        return walk\n\n    def test_switched_by_its_box_it_is_styled_as_one_opened_in_that_mode(self, qtbot, tmp_settings):\n        dlg = SettingsDialog(tmp_settings, self._theme_manager("dark"))\n        qtbot.addWidget(dlg)\n        for text in self._walk(dlg):\n            dlg.theme_combo.setCurrentText(text)\n            fresh = SettingsDialog(tmp_settings, self._theme_manager(self.NAMES[text]))\n            qtbot.addWidget(fresh)\n            a, b = _styles(dlg), _styles(fresh)\n            assert len(a) == len(b), (text, len(a), len(b))\n            differ = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]\n            assert not differ, (text, differ[:2])\n\n    def test_the_headings_descriptions_and_tips_change_colour(self, qtbot, tmp_settings):\n        """The labels that read the mode, by the ink Qt draws them in: every\n        one of them differs between dark and light, and follows the box."""\n        dlg = SettingsDialog(tmp_settings, self._theme_manager("dark"))\n        qtbot.addWidget(dlg)\n        labels = [w for w in dlg.findChildren(QLabel) if w.styleSheet() and "color" in w.styleSheet()]\n        dark = [_ink(w) for w in labels]\n        dlg.theme_combo.setCurrentText("Light Mode")\n        light = [_ink(w) for w in labels]\n        moved = [w.text()[:30] for w, a, b in zip(labels, dark, light) if a != b]\n        assert len(moved) == len(labels) >= 17, (len(moved), len(labels))\n        dlg.theme_combo.setCurrentText("Dark Mode")\n        assert [_ink(w) for w in labels] == dark\n\n\n# ─────────────────────────────────────────────────────────────────────────────\n# 3. The mechanism, in BaseDialog\n# ─────────────────────────────────────────────────────────────────────────────\n\nclass TestBaseDialogRefresh:\n\n    def test_refresh_keeps_the_components_the_dialog_was_built_with(self, qtbot):\n        tm = ThemeManager()\n        tm.set_theme("dark")\n        dlg = BaseDialog(tm)\n        qtbot.addWidget(dlg)\n        dlg.apply_extended_styling("tab", "table")\n        tm.set_theme("light")\n        dlg.refresh_theme()\n        assert dlg.styleSheet() == DialogStyleManager.get_extended_stylesheet(\n            False, dlg.font_family, "tab", "table")\n        dlg.apply_base_styling()\n        tm.set_theme("dark")\n        dlg.refresh_theme()\n        assert dlg.styleSheet() == DialogStyleManager.get_dialog_stylesheet(True, dlg.font_family)\n\n    def test_a_widget_styled_again_keeps_the_later_sheet(self, qtbot):\n        tm = ThemeManager()\n        tm.set_theme("dark")\n        dlg = BaseDialog(tm)\n        qtbot.addWidget(dlg)\n        label = QLabel("status", dlg)\n        dlg._style_for_mode(label, lambda: f"color: {dlg.get_colors()[\'success\']};")\n        dlg._style_for_mode(label, lambda: f"color: {dlg.get_colors()[\'error\']};")\n        tm.set_theme("light")\n        dlg.refresh_theme()\n        assert label.styleSheet() == f"color: {DialogStyleManager.LIGHT[\'error\']};"\n        assert len(dlg._mode_styled) == 1\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    import copy

    BASE, SETTINGS = "ui/base_dialog.py", "ui/settings_dialog.py"
    FIND, REGEX = "ui/find_replace_dialog.py", "ui/regex_builder_dialog.py"
    WATCH, MAIN = "ui/watch_folder_dialog.py", "ui/main_window.py"
    MODE = {"get_colors", "get_header_style", "get_subtitle_style",
            "get_description_style", "get_tip_style"}

    def methods(src, cls):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == cls)
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}

    def compare(rel, cls):
        o, n = methods(_original(tree, rel), cls), methods(tree.read(rel), cls)
        moved = sorted(k for k in o if k in n and ast.dump(o[k]) != ast.dump(n[k]))
        return o, n, moved, sorted(set(n) - set(o)), sorted(set(o) - set(n))

    def outside(src, cls):
        return [ast.dump(x) for x in ast.parse(src).body
                if not (isinstance(x, ast.ClassDef) and x.name == cls)]

    def reads_mode(node):
        return any(isinstance(c, ast.Call) and getattr(c.func, "attr", None) in MODE
                   for c in ast.walk(node))

    def with_locals(fn, expr):
        local = {a.targets[0].id: a.value for a in ast.walk(fn)
                 if isinstance(a, ast.Assign) and len(a.targets) == 1
                 and isinstance(a.targets[0], ast.Name) and reads_mode(a.value)}

        class Sub(ast.NodeTransformer):
            def visit_Name(self, node):
                return copy.deepcopy(local[node.id]) if node.id in local else node
        return Sub().visit(copy.deepcopy(expr))

    def direct(fn):
        """(target, sheet) for every sheet set straight away that reads the mode."""
        out = []
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "setStyleSheet" and c.args:
                arg = with_locals(fn, c.args[0])
                if reads_mode(arg):
                    out.append((ast.unparse(c.func.value), ast.dump(arg)))
        return sorted(out)

    def registered(fn):
        out = []
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "_style_for_mode":
                target, sheet = c.args
                assert isinstance(sheet, ast.Lambda), ast.unparse(c)
                out.append((ast.unparse(target), ast.dump(sheet.body)))
        return sorted(out)

    def same_sheets(o, n, names, where):
        for name in names:
            assert direct(o[name]) == sorted(direct(n[name]) + registered(n[name])), \
                f"{where}.{name}: a stylesheet changed on the way"
            assert not direct(n[name]), \
                f"{where}.{name}: a stylesheet reads the mode at build and nothing redraws it"

    # --- BaseDialog: the register, the helper, the refresh
    o, n, moved, added, gone = compare(BASE, "BaseDialog")
    assert added == ["_style_for_mode"] and not gone, f"BaseDialog: added {added}, removed {gone}"
    labels = ["_create_header_label", "_create_subtitle_label",
              "_create_description_label", "_create_tip_label"]
    assert moved == sorted(["__init__", "apply_base_styling", "apply_extended_styling",
                            "refresh_theme"] + labels), f"BaseDialog: moved {moved}"
    assert [ast.unparse(s) for s in n["_style_for_mode"].body[1:]] == [
        "widget.setStyleSheet(sheet())", "self._mode_styled[widget] = sheet"], \
        "_style_for_mode() does not set the sheet and keep it"
    init = [ast.unparse(s) for s in n["__init__"].body]
    conf = init.index("self._configure_window()")
    made = [i for i, s in enumerate(init) if s.startswith(("self._mode_styled", "self._style_components"))]
    assert len(made) == 2 and max(made) < conf, "the register is made after the window is configured"
    assert "self._style_components = ()" in [ast.unparse(s) for s in n["apply_base_styling"].body], \
        "apply_base_styling() does not forget the components"
    assert "self._style_components = components" in [ast.unparse(s) for s in n["apply_extended_styling"].body], \
        "apply_extended_styling() does not keep its components"
    refresh = ast.unparse(n["refresh_theme"])
    assert "self.apply_extended_styling(*self._style_components)" in refresh \
        and "self.apply_base_styling()" in refresh, "refresh_theme() drops a dialog's extended styles"
    loops = [s for s in n["refresh_theme"].body if isinstance(s, ast.For)]
    assert len(loops) == 1 and "self._mode_styled.items()" in ast.unparse(loops[0].iter) \
        and "widget.setStyleSheet(sheet())" in ast.unparse(loops[0]), \
        "refresh_theme() does not restyle what was styled for a mode"
    same_sheets(o, n, labels, "BaseDialog")
    ob, nb = outside(_original(tree, BASE), "BaseDialog"), outside(tree.read(BASE), "BaseDialog")
    new_top = [x for x in nb if x not in ob]
    assert len(nb) == len(ob) and len(new_top) == 1 and "collections.abc" in new_top[0], \
        "the module moved beyond the dialog"

    # --- SettingsDialog: every mode-read sheet registered, and its box refreshes
    o, n, moved, added, gone = compare(SETTINGS, "SettingsDialog")
    assert not added and not gone, f"SettingsDialog: added {added}, removed {gone}"
    assert moved == ["_create_adjustments_tab", "_create_export_tab", "_on_theme_changed"], \
        f"SettingsDialog: moved {moved}"
    same_sheets(o, n, ["_create_adjustments_tab", "_create_export_tab"], "SettingsDialog")
    assert [ast.unparse(s) for s in n["_on_theme_changed"].body[-2:]] == [
        "self.theme_manager.set_theme(theme)", "self.refresh_theme()"], \
        "the theme box does not refresh the dialog"
    for name, fn in n.items():
        assert not direct(fn), f"SettingsDialog.{name}: a stylesheet reads the mode at build and nothing redraws it"
    assert outside(_original(tree, SETTINGS), "SettingsDialog") == outside(tree.read(SETTINGS), "SettingsDialog"), \
        f"{SETTINGS} moved beyond the dialog"

    # --- Find & Replace and Watch Folders: their one mode-read sheet, registered
    for rel, cls in ((FIND, "FindReplaceDialog"), (WATCH, "WatchFolderDialog")):
        o, n, moved, added, gone = compare(rel, cls)
        assert moved == ["_setup_ui"] and not added and not gone, \
            f"{cls}: moved {moved}, added {added}, removed {gone}"
        same_sheets(o, n, ["_setup_ui"], cls)
        for name, fn in n.items():
            assert not direct(fn), f"{cls}.{name}: a stylesheet reads the mode at build and nothing redraws it"
        assert outside(_original(tree, rel), cls) == outside(tree.read(rel), cls), f"{rel} moved beyond {cls}"

    # --- the Regex Builder: its status line keeps its state's key; its matches repaint
    o, n, moved, added, gone = compare(REGEX, "RegexBuilderDialog")
    assert added == ["_set_status_colour", "refresh_theme"] and not gone, \
        f"RegexBuilderDialog: added {added}, removed {gone}"
    assert moved == ["_on_pattern_changed", "_setup_ui", "_update_matches"], f"RegexBuilderDialog: moved {moved}"
    assert [ast.unparse(s) for s in n["_set_status_colour"].body[1:]] == [
        "self._style_for_mode(self.status_label, lambda: f'color: {self.get_colors()[key]};')"], \
        "_set_status_colour() does not register the status sheet"

    def keys_before(fn):
        out = []
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "setStyleSheet" \
                    and ast.unparse(c.func.value) == "self.status_label":
                arg = with_locals(fn, c.args[0])
                out.append(sorted(s.slice.value for s in ast.walk(arg)
                                  if isinstance(s, ast.Subscript) and isinstance(s.slice, ast.Constant)))
        return sorted(out)

    def keys_after(fn):
        return sorted(sorted(k.value for k in ast.walk(c.args[0])
                             if isinstance(k, ast.Constant) and isinstance(k.value, str))
                      for c in ast.walk(fn) if isinstance(c, ast.Call)
                      and getattr(c.func, "attr", None) == "_set_status_colour")

    for name in moved:
        assert keys_before(o[name]) == keys_after(n[name]), f"RegexBuilderDialog.{name}: the status line changed colour on the way"
        assert not keys_before(n[name]), f"RegexBuilderDialog.{name}: the status line is still styled once"
    for name, fn in n.items():
        assert not direct(fn), f"RegexBuilderDialog.{name}: a stylesheet reads the mode at build and nothing redraws it"
    assert [ast.unparse(s) for s in n["refresh_theme"].body[1:]] == [
        "super().refresh_theme()", "if self._current_matches:\n    self._highlight_matches()"], \
        "the Regex Builder does not repaint its matches on a switch"
    assert outside(_original(tree, REGEX), "RegexBuilderDialog") == outside(tree.read(REGEX), "RegexBuilderDialog"), \
        f"{REGEX} moved beyond the dialog"

    # --- the main window keeps every non-modal dialog it shows, and refreshes it
    o, n, moved, added, gone = compare(MAIN, "MainWindow")
    assert added == ["_forget_open_dialog", "_track_open_dialog"] and not gone, \
        f"MainWindow: added {added}, removed {gone}"
    # every method that SHOWS a dialog -- non-modal -- keeps it. Derived, not
    # listed: this is how the Regex Builder's Apply Find road was found.
    for name, fn in n.items():
        shows = any(isinstance(c, ast.Call) and ast.unparse(c) == "dialog.show()" for c in ast.walk(fn))
        if shows and name != "_open_compare_dialog":
            assert "self._track_open_dialog(dialog)" in ast.unparse(fn), f"{name} shows a dialog nothing refreshes"
    openers = ["_open_find_dialog", "_open_replace_dialog", "_open_regex_builder_dialog",
               "_open_watch_folder_dialog"]
    for name in openers:
        body = [ast.unparse(s) for s in n[name].body]
        assert body[-2:] == ["self._track_open_dialog(dialog)", "dialog.show()"], f"{name} shows a dialog it does not keep"
    assert moved == sorted(openers + ["_on_regex_pattern_applied", "_refresh_open_dialogs_theme"]), \
        f"MainWindow: moved {moved}"
    for name in openers + ["_on_regex_pattern_applied"]:
        kept = "\n".join(line for line in ast.unparse(n[name]).split("\n")
                         if line.strip() != "self._track_open_dialog(dialog)")
        assert kept == ast.unparse(o[name]), f"{name} changed beyond keeping its dialog"
    track = ast.unparse(n["_track_open_dialog"])
    assert "dialog.finished.connect(partial(self._forget_open_dialog, dialog))" in track, "a closed dialog is never let go"
    refresh = n["_refresh_open_dialogs_theme"]
    loops = [s for s in refresh.body if isinstance(s, ast.For)]
    assert len(loops) == 1 and "_open_dialogs" in ast.unparse(loops[0].iter) \
        and "dialog.refresh_theme()" in ast.unparse(loops[0]), \
        "_refresh_open_dialogs_theme() does not reach the dialogs it keeps"
    assert [ast.dump(s) for s in o["_refresh_open_dialogs_theme"].body[1:]] == \
        [ast.dump(s) for s in refresh.body[1:-1]], "the Compare dialog's refresh moved"
    om, nm = outside(_original(tree, MAIN), "MainWindow"), outside(tree.read(MAIN), "MainWindow")
    new_top = [x for x in nm if x not in om]
    assert not [x for x in om if x not in nm] and len(new_top) == 2 \
        and any("'functools'" in x for x in new_top) and any("'ui.base_dialog'" in x for x in new_top), \
        "the module moved beyond the main window"

    # --- the guard: new, and marked
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert SENTINEL in guard and "class TestTheNonModalDialogsFollowASwitch" in guard \
        and "class TestSettingsFollowsItsOwnThemeBox" in guard, "the guard is not the one this round writes"
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""

KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
