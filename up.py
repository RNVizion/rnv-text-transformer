"""Find's painting and the Regex Builder's highlighting are not edits of the text

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (29a485e with up_tt_find_repaint.py applied).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-28: "We can work on those 2 fixes" -- the two faults the
find-and-watch round found and left alone. Built on up_tt_find_repaint.py:
run that script first. This one refuses, saying so, where it has not run.

1. Find's own painting counted as an edit of the text. Qt reports a change of
   format as a change of the text -- textChanged fires -- and records each
   one as a step of the undo history. A Find fired the main text's
   textChanged once per match; with auto-transform on, that re-ran the
   transform and replaced an output edited by hand; and each match was a
   Ctrl+Z press between you and your last edit. Typing into Find's field did
   the same once per key, with nothing painted, and so did closing Find.
2. The Regex Builder re-ran itself about three times a second, forever. Its
   highlighting fired the test pane's textChanged, which re-armed the 300 ms
   update, which highlighted again -- with a pattern, with none and with a
   broken one -- and the pane's undo history grew without end.

The approach the find-repaint round took for a theme switch, now in one
helper both dialogs use: BaseDialog._not_an_edit() holds the text's signals
and makes what is done inside it one step of the undo history; and
BaseDialog._carries_format() lets a reset that would change nothing not be
made at all. A Find is one Ctrl+Z; typing into Find's field and closing it
are none, and none of the three sets the auto-transform going. The Regex
Builder updates when its pattern or its text changes, and then rests.
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
SENTINEL = 'RNV-NOT-AN-EDIT'
SENTINEL_FILE = 'ui/base_dialog.py'
GUARD = 'tests/test_highlighting_is_not_an_edit.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py']
DESCRIPTION = "Find's painting and the Regex Builder's highlighting are not edits of the text"

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

SHADOWS = {"base_dialog.py", "colors.py", "conftest.py", "find_replace_dialog.py", "regex_builder_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ["the caret. Clearing Find's highlights still moves the main text's caret to the end and scrolls there -- on every key typed into Find's field, and on closing Find -- and the Regex Builder's clear, with no pattern or a broken one, still moves the test pane's caret to the end 300 ms after a key typed in the middle. Measured before and after this round; raised in the round's doc for a ruling.", "highlights in the undo history. A Find, a switch's repaint and a Regex Builder update are each still one step of the text's undo history: Qt records every change of format. Highlighting with extra selections instead would record nothing, and would change how the highlights are drawn and kept; raised in the round's doc.", 'the Compare dialog: its panes are read only and nothing listens to them.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # This round builds on up_tt_find_repaint.py: its anchors are that round's
    # text. Without it they would all be "missing", which says the wrong thing.
    if "RNV-FIND-REPAINT" not in tree.read("ui/find_replace_dialog.py"):
        raise Stop("this round builds on up_tt_find_repaint.py, which has not been "
                   "applied here: ui/find_replace_dialog.py has no 'RNV-FIND-REPAINT'.\n"
                   "Run that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tree.sub('ui/base_dialog.py',
             'from typing import TYPE_CHECKING, ClassVar\n\nfrom PyQt6.QtWidgets import (\n',
             'from contextlib import contextmanager\nfrom typing import TYPE_CHECKING, ClassVar\n\nfrom PyQt6.QtWidgets import (\n')
    tree.sub('ui/base_dialog.py',
             'from PyQt6.QtCore import Qt\n',
             'from PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QTextCursor\n')
    tree.sub('ui/base_dialog.py',
             'if TYPE_CHECKING:\n    from collections.abc import Callable\n\n    from core.theme_manager import ThemeManager\n',
             'if TYPE_CHECKING:\n    from collections.abc import Callable, Iterator\n\n    from PyQt6.QtWidgets import QTextEdit\n\n    from core.theme_manager import ThemeManager\n')
    tree.sub('ui/base_dialog.py',
             '        widget.setStyleSheet(sheet())\n        self._mode_styled[widget] = sheet\n    \n    def get_status_style(self, status: str) -> str:\n',
             '        widget.setStyleSheet(sheet())\n        self._mode_styled[widget] = sheet\n    \n    @contextmanager\n    def _not_an_edit(self, edit: QTextEdit) -> Iterator[None]:\n        """\n        Change the format of edit\'s text without editing it: what is done\n        inside the block is one step of the text\'s undo history, and the\n        text\'s signals are held until it ends.\n        \n        RNV-NOT-AN-EDIT 2026-09-28. Qt reports a change of format as a change\n        of the text -- textChanged fires -- and records each one as a step of\n        the undo history. Find\'s highlights and the Regex Builder\'s matches\n        are formats, and what listens to the text took each one for an edit:\n        the main window\'s statistics and auto-transform (a Find replaced an\n        output edited by hand), and the Regex Builder\'s own update, which\n        highlighted again, three times a second, for as long as it was open.\n        \n        A caret moved inside the block is not announced either. The one caret\n        that moves inside one, in Find\'s _highlight_all_matches(), is moved\n        again straight after, outside it.\n        \n        Args:\n            edit: The text edit whose text is formatted\n        """\n        cursor = QTextCursor(edit.document())\n        was_blocked = edit.blockSignals(True)\n        cursor.beginEditBlock()\n        try:\n            yield\n        finally:\n            cursor.endEditBlock()\n            edit.blockSignals(was_blocked)\n    \n    @staticmethod\n    def _carries_format(edit: QTextEdit) -> bool:\n        """\n        Whether any of edit\'s text carries a character format.\n        \n        RNV-NOT-AN-EDIT 2026-09-28: resetting the format of text that carries\n        none changes nothing, and Qt records it as a step of the undo history\n        all the same -- Find did it on every key typed into its field. A\n        block\'s own character format is the line break before it, which a\n        match that runs over a line break colours too.\n        \n        Args:\n            edit: The text edit to look at\n        \n        Returns:\n            True if any character, line breaks included, has a format\n        """\n        block = edit.document().begin()\n        while block.isValid():\n            if block.charFormat().properties():\n                return True\n            it = block.begin()\n            while not it.atEnd():\n                if it.fragment().charFormat().properties():\n                    return True\n                it += 1\n            block = block.next()\n        return False\n    \n    def get_status_style(self, status: str) -> str:\n')
    tree.sub('ui/find_replace_dialog.py',
             '        self._clear_highlights()\n        \n        highlight_color = self._highlight_colour()\n        \n        cursor = self.target_text_edit.textCursor()\n        format_highlight = QTextCharFormat()\n        format_highlight.setBackground(QBrush(highlight_color))\n        \n        # Apply highlighting to all matches\n        for start, end in self._current_matches:\n            cursor.setPosition(start)\n            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n            cursor.mergeCharFormat(format_highlight)\n        self._painted_highlight = QColor(highlight_color)\n',
             "        # RNV-NOT-AN-EDIT 2026-09-28: the clear and the paint are one step of\n        # the text's undo history -- a step per match, before -- and not an\n        # edit of it: with auto-transform on, a Find re-ran the transform.\n        with self._not_an_edit(self.target_text_edit):\n            self._clear_highlights()\n            \n            highlight_color = self._highlight_colour()\n            \n            cursor = self.target_text_edit.textCursor()\n            format_highlight = QTextCharFormat()\n            format_highlight.setBackground(QBrush(highlight_color))\n            \n            # Apply highlighting to all matches\n            for start, end in self._current_matches:\n                cursor.setPosition(start)\n                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n        self._painted_highlight = QColor(highlight_color)\n")
    tree.sub('ui/find_replace_dialog.py',
             '        format_clear = QTextCharFormat()\n        cursor.setCharFormat(format_clear)\n        cursor.clearSelection()\n',
             '        format_clear = QTextCharFormat()\n        # RNV-NOT-AN-EDIT 2026-09-28: not an edit of the text, and not made\n        # at all when the text carries no format -- it changed nothing, and\n        # was a step of the undo history for every key typed into Find.\n        if self._carries_format(self.target_text_edit):\n            with self._not_an_edit(self.target_text_edit):\n                cursor.setCharFormat(format_clear)\n        cursor.clearSelection()\n')
    tree.sub('ui/find_replace_dialog.py',
             '        cursor = QTextCursor(edit.document())\n        was_blocked = edit.blockSignals(True)\n        try:\n            cursor.beginEditBlock()\n            for start, length in spans:\n                cursor.setPosition(start)\n                cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n            cursor.endEditBlock()\n        finally:\n            edit.blockSignals(was_blocked)\n',
             '        cursor = QTextCursor(edit.document())\n        with self._not_an_edit(edit):\n            for start, length in spans:\n                cursor.setPosition(start)\n                cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n')
    tree.sub('ui/regex_builder_dialog.py',
             '        # Clear highlighting\n        cursor = self.test_text.textCursor()\n        cursor.select(QTextCursor.SelectionType.Document)\n        cursor.setCharFormat(QTextCharFormat())\n        cursor.clearSelection()\n',
             "        # Clear highlighting\n        cursor = self.test_text.textCursor()\n        cursor.select(QTextCursor.SelectionType.Document)\n        # RNV-NOT-AN-EDIT 2026-09-28: not an edit of the pane, and not made\n        # when the pane carries no format. The pane's textChanged re-arms the\n        # update that called this, so with no pattern, or a broken one, it\n        # ran again every 300 ms for as long as the dialog was open.\n        if self._carries_format(self.test_text):\n            with self._not_an_edit(self.test_text):\n                cursor.setCharFormat(QTextCharFormat())\n        cursor.clearSelection()\n")
    tree.sub('ui/regex_builder_dialog.py',
             '        """Highlight matches in test text area."""\n        # First, clear existing formatting\n        cursor = self.test_text.textCursor()\n        cursor.select(QTextCursor.SelectionType.Document)\n        cursor.setCharFormat(QTextCharFormat())\n        \n        if not self._current_matches:\n            return\n        \n        is_dark = self.theme_manager.current_theme in (\'dark\', \'image\')\n        highlight_color = QColor(self._MATCH_COLOR_DARK if is_dark else self._MATCH_COLOR_LIGHT)\n        \n        # Highlight each match\n        for match in self._current_matches:\n            cursor.setPosition(match.start)\n            cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)\n            \n            fmt = QTextCharFormat()\n            fmt.setBackground(QBrush(highlight_color))\n            cursor.mergeCharFormat(fmt)\n',
             '        """Highlight matches in test text area."""\n        # RNV-NOT-AN-EDIT 2026-09-28: one step of the pane\'s undo history --\n        # a step per match, before -- and not an edit of it. The pane\'s\n        # textChanged re-arms the update that called this, which highlighted\n        # again, three times a second, for as long as the dialog was open.\n        with self._not_an_edit(self.test_text):\n            # First, clear existing formatting\n            cursor = self.test_text.textCursor()\n            cursor.select(QTextCursor.SelectionType.Document)\n            if self._carries_format(self.test_text):\n                cursor.setCharFormat(QTextCharFormat())\n            \n            if not self._current_matches:\n                return\n            \n            is_dark = self.theme_manager.current_theme in (\'dark\', \'image\')\n            highlight_color = QColor(self._MATCH_COLOR_DARK if is_dark else self._MATCH_COLOR_LIGHT)\n            \n            # Highlight each match\n            for match in self._current_matches:\n                cursor.setPosition(match.start)\n                cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)\n                \n                fmt = QTextCharFormat()\n                fmt.setBackground(QBrush(highlight_color))\n                cursor.mergeCharFormat(fmt)\n')
    if (tree.root / 'tests/test_highlighting_is_not_an_edit.py').exists():
        raise Stop('tests/test_highlighting_is_not_an_edit.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_highlighting_is_not_an_edit.py', '"""\ntests/test_highlighting_is_not_an_edit.py\n=========================================\nRNV-NOT-AN-EDIT, 2026-09-28. Painting highlights is not an edit of the text.\n\nQt reports a change of format as a change of the text -- textChanged fires --\nand records each one as a step of the undo history. Two of this app\'s\ndialogs highlight by format, and what listens to the text took each\nhighlight for an edit:\n\n1. Find. A Find fired the main text\'s textChanged once per match; with\n   auto-transform on, that re-ran the transform and replaced an output\n   edited by hand; and each match was a Ctrl+Z press between you and your\n   last edit. Typing into Find\'s field did the same once per key, with\n   nothing painted; so did closing Find.\n2. The Regex Builder. Its highlighting fired the test pane\'s textChanged,\n   which re-armed the 300 ms update, which highlighted again: about three\n   times a second, for as long as the dialog was open, with a pattern, with\n   none and with a broken one. The pane\'s undo history grew without end.\n\nBaseDialog._not_an_edit() holds the text\'s signals and makes a paint one step\nof the undo history; BaseDialog._carries_format() lets a reset that would\nchange nothing not be made. Every test drives the main window\'s own openers.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtGui import QTextCursor\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.base_dialog import BaseDialog\n\nTEXT = ("The quick brown fox jumps over the lazy dog.\\n"\n        "Pack my box with five dozen liquor jugs.\\n"\n        "How vexingly quick daft zebras jump over the log.\\n")\nHAND = "an output edited by hand"\nPANE = "foo boo zoo\\nmoo\\n"\n\n\ndef _opened(win, opener: str) -> BaseDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    return new[0]\n\n\ndef _formatted(edit) -> list:\n    """Every run of the text that carries a character format, line breaks\n    included (a block\'s own format is the line break before it)."""\n    out = []\n    block = edit.document().begin()\n    while block.isValid():\n        if block.charFormat().properties():\n            out.append(("line break before", block.position()))\n        it = block.begin()\n        while not it.atEnd():\n            if it.fragment().charFormat().properties():\n                out.append((it.fragment().position(), it.fragment().length()))\n            it += 1\n        block = block.next()\n    return out\n\n\ndef _typed_at_the_end(edit, text: str = "X") -> None:\n    """A real edit: text typed at the end, through the text\'s own caret."""\n    cursor = edit.textCursor()\n    cursor.movePosition(QTextCursor.MoveOperation.End)\n    edit.setTextCursor(cursor)\n    edit.insertPlainText(text)\n\n\nclass _Edits:\n    """Counts the text\'s textChanged."""\n\n    def __init__(self, edit):\n        self.count = 0\n        edit.textChanged.connect(self._bump)\n\n    def _bump(self):\n        self.count += 1\n\n\n@pytest.fixture\ndef watched(main_window):\n    """The main window with auto-transform on, its text filled, and an\n    output edited by hand after the transform that filling started."""\n    win = main_window\n    win.settings_manager.save_auto_transform(True)\n    win.text_input.setPlainText(TEXT)\n    win.auto_transform_timer.stop()\n    win.output_text.setPlainText(HAND)\n    yield win, _Edits(win.text_input)\n    win.auto_transform_timer.stop()\n\n\nclass TestFindIsNotAnEdit:\n\n    def test_a_find_does_not_edit_the_text(self, watched):\n        win, edits = watched\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert _formatted(win.text_input), "the Find painted nothing: nothing was tested"\n        assert edits.count == 0, f"the Find fired the text\'s textChanged {edits.count} times"\n        assert not win.auto_transform_timer.isActive(), "the Find set the auto-transform going"\n        assert win.output_text.toPlainText() == HAND\n        _typed_at_the_end(win.text_input)                    # and a real edit still is one\n        assert edits.count == 1, "the text\'s signals were left held after the Find"\n        dlg.close()\n\n    def test_a_find_is_one_step_of_undo(self, main_window):\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        _typed_at_the_end(win.text_input)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert len(_formatted(win.text_input)) > 1, "fewer than two matches: nothing was tested"\n        win.text_input.undo()\n        assert _formatted(win.text_input) == [], "one Ctrl+Z did not take the Find\'s highlights away"\n        assert win.text_input.toPlainText() == TEXT + "X", "one Ctrl+Z undid more than the Find"\n        win.text_input.undo()\n        assert win.text_input.toPlainText() == TEXT, "the second Ctrl+Z did not reach the last edit"\n        dlg.close()\n\n    def test_typing_into_find_leaves_the_text_and_its_history_alone(self, watched):\n        win, edits = watched\n        _typed_at_the_end(win.text_input)\n        edits.count = 0\n        dlg = _opened(win, "_open_find_dialog")\n        steps = win.text_input.document().availableUndoSteps()\n        for i in range(1, 6):\n            dlg.find_input.setText("hello"[:i])              # five keys, nothing found yet\n        assert edits.count == 0, f"typing into Find fired the text\'s textChanged {edits.count} times"\n        assert win.text_input.document().availableUndoSteps() == steps, \\\n            "typing into Find added to the text\'s undo history"\n        win.text_input.undo()\n        assert win.text_input.toPlainText() == TEXT, "one Ctrl+Z did not reach the last edit"\n        dlg.close()\n\n    def test_closing_find_does_not_edit_the_text(self, watched):\n        win, edits = watched\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert _formatted(win.text_input)\n        dlg.close()\n        QApplication.processEvents()\n        assert _formatted(win.text_input) == [], "closing Find left its highlights"\n        assert edits.count == 0, f"closing Find fired the text\'s textChanged {edits.count} times"\n        assert win.output_text.toPlainText() == HAND and not win.auto_transform_timer.isActive()\n\n    def test_a_highlight_on_a_line_break_is_cleared_too(self, main_window):\n        """A regular expression can match line breaks alone, and a line\n        break\'s format is its block\'s, not a run of text. Left behind, it\n        colours what is typed at the start of the next line."""\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.regex_check.setChecked(True)\n        dlg.find_input.setText("\\\\n")\n        dlg._on_find()\n        breaks = _formatted(win.text_input)\n        assert breaks and all(b[0] == "line break before" for b in breaks), \\\n            f"the Find did not colour line breaks alone: {breaks}"\n        dlg.find_input.setText("")                           # a new search clears them\n        assert _formatted(win.text_input) == [], "a line break kept the Find\'s colour"\n        dlg.close()\n\n\nclass TestTheRegexBuilderRests:\n\n    @pytest.mark.parametrize("pattern", ["o", "", "(o"], ids=["pattern", "no-pattern", "broken-pattern"])\n    def test_it_does_nothing_while_nothing_changes(self, main_window, qtbot, pattern):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText(pattern)\n        builder.test_text.setPlainText(PANE)\n        qtbot.wait(700)                                      # the update the edits asked for\n        runs = []\n        builder._update_timer.timeout.connect(lambda: runs.append(1))\n        steps = builder.test_text.document().availableUndoSteps()\n        qtbot.wait(1500)                                     # nothing happens for 1.5 s\n        assert runs == [], f"the Regex Builder updated {len(runs)} times with nothing changed"\n        assert builder.test_text.document().availableUndoSteps() == steps, \\\n            "the test pane\'s undo history grew with nothing changed"\n        builder.close()\n\n    def test_an_edit_still_updates_the_matches(self, main_window, qtbot):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("o")\n        builder.test_text.setPlainText(PANE)\n        qtbot.wait(700)\n        before = len(builder._current_matches)\n        assert before == 8, before\n        builder.test_text.insertPlainText("oo")              # a real edit of the pane\n        qtbot.wait(700)\n        assert len(builder._current_matches) == before + 2, "an edit of the test text no longer updates"\n        builder.close()\n\n    def test_clearing_the_pattern_is_not_an_edit_of_the_pane(self, main_window, qtbot):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("o")\n        builder.test_text.setPlainText(PANE)\n        qtbot.wait(700)\n        assert _formatted(builder.test_text), "nothing was painted: nothing was tested"\n        edits = _Edits(builder.test_text)\n        builder.pattern_input.setText("")                    # the results are cleared\n        qtbot.wait(700)\n        assert _formatted(builder.test_text) == [], "clearing the pattern left the matches painted"\n        assert edits.count == 0, f"clearing the matches fired the pane\'s textChanged {edits.count} times"\n        builder.close()\n\n    @pytest.mark.parametrize("pattern", ["", "(o", "zzz"], ids=["no-pattern", "broken-pattern", "no-match"])\n    def test_with_nothing_to_paint_the_pane_s_history_is_its_own(self, main_window, qtbot, pattern):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText(pattern)\n        builder.test_text.setPlainText(PANE)                 # a new text: its history starts empty\n        qtbot.wait(700)                                      # the update runs and paints nothing\n        assert _formatted(builder.test_text) == []\n        assert builder.test_text.document().availableUndoSteps() == 0, \\\n            "an update that painted nothing added to the pane\'s undo history"\n        builder.close()\n\n    def test_an_update_is_one_step_of_the_pane_s_undo(self, main_window, qtbot):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("o")\n        builder.test_text.setPlainText(PANE)\n        qtbot.wait(700)\n        pane = builder.test_text\n        assert len(_formatted(pane)) > 1, "fewer than two matches painted: nothing was tested"\n        pane.undo()\n        assert _formatted(pane) == [] and pane.toPlainText() == PANE, \\\n            "one Ctrl+Z did not take the update\'s highlights away, and only those"\n        builder._update_timer.stop()\n        builder.close()\n')


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
    BASE, FIND = "ui/base_dialog.py", "ui/find_replace_dialog.py"
    REGEX, MAIN = "ui/regex_builder_dialog.py", "ui/main_window.py"

    def dialog(src, name):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == name)
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}, c

    def compare(rel, name):
        (o, oc), (n, nc) = dialog(_original(tree, rel), name), dialog(tree.read(rel), name)
        moved = sorted(k for k in o if k in n and ast.dump(o[k]) != ast.dump(n[k]))
        return o, n, oc, nc, moved, sorted(set(n) - set(o)), sorted(set(o) - set(n))

    def dumps(stmts):
        return [ast.dump(s) for s in stmts]

    def held(node, item):
        return isinstance(node, ast.With) and len(node.items) == 1 \
            and ast.unparse(node.items[0]) == item

    def rest(cls):
        return dumps(s for s in cls.body if not isinstance(s, ast.FunctionDef))

    def outside(src, name):
        return [ast.dump(x) for x in ast.parse(src).body
                if not (isinstance(x, ast.ClassDef) and x.name == name)]

    def reset_wrapped(old_fn, new_fn, reset, edit):
        """The one reset statement, now made only when the text carries a
        format and then held; every other statement as it was."""
        ob = old_fn.body
        at = [ast.unparse(s) for s in ob].index(reset)
        nb = new_fn.body
        gate = nb[at]
        ok = (isinstance(gate, ast.If) and ast.unparse(gate.test) == f"self._carries_format({edit})"
              and not gate.orelse and len(gate.body) == 1
              and held(gate.body[0], f"self._not_an_edit({edit})")
              and dumps(gate.body[0].body) == [ast.dump(ob[at])])
        return ok and dumps(nb[:at] + nb[at + 1:]) == dumps(ob[:at] + ob[at + 1:])

    # --- BaseDialog: the two helpers, and nothing else in the class
    o, n, oc, nc, moved, added, gone = compare(BASE, "BaseDialog")
    assert added == ["_carries_format", "_not_an_edit"] and not gone and not moved, \
        f"BaseDialog: added {added}, removed {gone}, moved {moved}"
    assert rest(oc) == rest(nc), "BaseDialog's class body moved beyond its two helpers"
    ne = n["_not_an_edit"]
    assert [ast.unparse(d) for d in ne.decorator_list] == ["contextmanager"], \
        "_not_an_edit() is not a context manager"
    assert [ast.unparse(s) for s in ne.body[1:]] == [
        "cursor = QTextCursor(edit.document())",
        "was_blocked = edit.blockSignals(True)",
        "cursor.beginEditBlock()",
        "try:\n    yield\nfinally:\n    cursor.endEditBlock()\n    edit.blockSignals(was_blocked)"], \
        "_not_an_edit() does not hold the text's signals and make one step, and give both back"
    cf = n["_carries_format"]
    cft = ast.unparse(cf)
    assert [ast.unparse(d) for d in cf.decorator_list] == ["staticmethod"] \
        and "block.charFormat().properties()" in cft and "it.fragment().charFormat().properties()" in cft, \
        "_carries_format() misses the line breaks or the runs of text"
    ob, nb = outside(_original(tree, BASE), "BaseDialog"), outside(tree.read(BASE), "BaseDialog")
    gone_top, new_top = [x for x in ob if x not in nb], [x for x in nb if x not in ob]
    module = ast.parse(tree.read(BASE)).body
    added_imports = sorted(ast.unparse(x) for x in module if ast.dump(x) in new_top
                           and isinstance(x, ast.ImportFrom))
    assert added_imports == ["from PyQt6.QtGui import QTextCursor", "from contextlib import contextmanager"] \
        and len(gone_top) == 1 and len(new_top) == 3, "the module moved beyond the helpers' imports"
    checking = next(x for x in module if isinstance(x, ast.If) and ast.unparse(x.test) == "TYPE_CHECKING")
    assert [ast.unparse(s) for s in checking.body] == [
        "from collections.abc import Callable, Iterator", "from PyQt6.QtWidgets import QTextEdit",
        "from core.theme_manager import ThemeManager"], "the type-checking imports moved beyond the helpers'"

    # --- Find: its paint one held step; its reset held, and not made when it changes nothing
    o, n, oc, nc, moved, added, gone = compare(FIND, "FindReplaceDialog")
    assert not added and not gone and moved == ["_clear_highlights", "_highlight_all_matches",
                                                "_recolour_highlights"], \
        f"FindReplaceDialog: moved {moved}, added {added}, removed {gone}"
    assert rest(oc) == rest(nc), "the Find dialog's class body moved beyond its methods"
    ob, nb = o["_highlight_all_matches"].body, n["_highlight_all_matches"].body
    assert len(nb) == 4 and held(nb[2], "self._not_an_edit(self.target_text_edit)"), \
        "the Find's clear and paint are not one held step"
    assert dumps(nb[2].body) == dumps(ob[2:-1]) and dumps(nb[:2] + nb[3:]) == dumps(ob[:2] + ob[-1:]), \
        "_highlight_all_matches() changed beyond holding its clear and paint"
    assert reset_wrapped(o["_clear_highlights"], n["_clear_highlights"],
                         "cursor.setCharFormat(format_clear)", "self.target_text_edit"), \
        "_clear_highlights() changed beyond holding its reset and not making one that changes nothing"
    ob, nb = o["_recolour_highlights"].body, n["_recolour_highlights"].body
    tried = ob[-1]
    assert isinstance(tried, ast.Try) and len(tried.body) == 3 \
        and [ast.unparse(s) for s in (tried.body[0], tried.body[2])] == [
            "cursor.beginEditBlock()", "cursor.endEditBlock()"] \
        and [ast.unparse(s) for s in tried.finalbody] == ["edit.blockSignals(was_blocked)"], \
        "the switch's repaint is not the one this round was derived against"
    assert dumps(nb[:-1]) == dumps(ob[:-2]) and held(nb[-1], "self._not_an_edit(edit)") \
        and dumps(nb[-1].body) == [ast.dump(tried.body[1])], \
        "_recolour_highlights() changed beyond taking the one helper"
    assert outside(_original(tree, FIND), "FindReplaceDialog") == outside(tree.read(FIND), "FindReplaceDialog"), \
        f"{FIND} moved beyond the dialog"

    # --- the Regex Builder: its paint one held step; its reset held, and not made when it changes nothing
    o, n, oc, nc, moved, added, gone = compare(REGEX, "RegexBuilderDialog")
    assert not added and not gone and moved == ["_clear_results", "_highlight_matches"], \
        f"RegexBuilderDialog: moved {moved}, added {added}, removed {gone}"
    assert rest(oc) == rest(nc), "the Regex Builder's class body moved beyond its methods"
    assert reset_wrapped(o["_clear_results"], n["_clear_results"],
                         "cursor.setCharFormat(QTextCharFormat())", "self.test_text"), \
        "_clear_results() changed beyond holding its reset and not making one that changes nothing"
    ob, nb = o["_highlight_matches"].body, n["_highlight_matches"].body
    assert len(nb) == 2 and ast.dump(nb[0]) == ast.dump(ob[0]) \
        and held(nb[1], "self._not_an_edit(self.test_text)"), \
        "the Regex Builder's clear and paint are not one held step"
    inner = nb[1].body
    at = [ast.unparse(s) for s in ob].index("cursor.setCharFormat(QTextCharFormat())") - 1
    gate = inner[at]
    assert isinstance(gate, ast.If) and ast.unparse(gate.test) == "self._carries_format(self.test_text)" \
        and dumps(gate.body) == [ast.dump(ob[at + 1])] and not gate.orelse \
        and dumps(inner[:at] + inner[at + 1:]) == dumps(ob[1:at + 1] + ob[at + 2:]), \
        "_highlight_matches() changed beyond holding its paint and not making a reset that changes nothing"
    assert outside(_original(tree, REGEX), "RegexBuilderDialog") == outside(tree.read(REGEX), "RegexBuilderDialog"), \
        f"{REGEX} moved beyond the dialog"

    # --- derived, not listed: every change of format either dialog makes is held
    for rel, name in ((FIND, "FindReplaceDialog"), (REGEX, "RegexBuilderDialog")):
        fns, _cls = dialog(tree.read(rel), name)
        for fname, fn in fns.items():
            inside = set()
            for w in ast.walk(fn):
                if isinstance(w, ast.With) and ast.unparse(w.items[0]).startswith("self._not_an_edit("):
                    inside |= {id(c) for c in ast.walk(w)}
            for c in ast.walk(fn):
                if isinstance(c, ast.Call) and getattr(c.func, "attr", None) in ("setCharFormat", "mergeCharFormat"):
                    assert id(c) in inside, f"{name}.{fname} changes a format that is not held"

    # --- the premise: the two texts are listened to -- the main window's
    # statistics and auto-transform, and the Regex Builder's own update
    win = next(c for c in ast.parse(tree.read(MAIN)).body
               if isinstance(c, ast.ClassDef) and c.name == "MainWindow")
    assert "self.text_input.textChanged.connect(self._on_input_text_changed)" in ast.unparse(win), \
        "the main window no longer listens to its text: re-derive what Find's painting set off"
    rb = ast.unparse(dialog(tree.read(REGEX), "RegexBuilderDialog")[1])
    assert "self.test_text.textChanged.connect(self._on_test_text_changed)" in rb \
        and "self._update_timer.timeout.connect(self._update_matches)" in rb, \
        "the Regex Builder no longer updates on its pane's textChanged: re-derive the loop"

    # --- the guard: new, and marked
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert SENTINEL in guard and "class TestFindIsNotAnEdit" in guard and "class TestTheRegexBuilderRests" in guard, \
        "the guard is not the one this round writes"
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
