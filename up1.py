"""Find's highlights and the Regex Builder's matches as extra selections, for rnv-text-transformer

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (d101615).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-30: "Yes do this" -- item 3 of decisions-pending-2026-09-29.md.

Find's highlights and the Regex Builder's matches were character formats in
the text. RNV-NOT-AN-EDIT (2026-09-28) held the text's signals and made each
paint one step of the undo history, and a step it still was: the first
Ctrl+Z after a Find took the highlights, not your last edit. A copy of
highlighted text put the colour on the clipboard as HTML -- background-color
on each match -- and a paste into a rich-text editor brought the gold along.
And a character format splits the text into runs, which Qt lays out one by
one, so highlighting nudged the letters around a match.

Qt's extra selections are the overlay made for search results: drawn over
the document and kept out of it. Both dialogs paint through them now, via
one helper in BaseDialog, _show_highlights(). No step of the undo history,
no signal, nothing a copy carries, and the letters stay where they are. The
two helpers that held the text's signals go, with nothing left to hold. The
switch's repaint (RNV-FIND-REPAINT) still finds the highlights by the colour
they were painted in, and their cursors follow an edit made since the Find.

Rendered before building: the fills are the same colour; each fill's edge
lands up to one pixel apart; and against the same text with nothing
highlighted, the letters outside the highlights differ in 3,456 pixels as
shipped and in none with the change. Four guards read the highlights where
they are now, and the two that held "one step of undo" hold "no step".
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
SENTINEL = 'RNV-EXTRA-SELECTIONS'
SENTINEL_FILE = 'ui/base_dialog.py'
GUARD = 'tests/test_highlighting_is_not_an_edit.py'
GUARD_FILES = ['tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py', 'tests/test_caret_stays_put.py', 'tests/test_dialogs_follow_a_switch.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py', 'tests/test_caret_stays_put.py', 'tests/test_dialogs_follow_a_switch.py']
DESCRIPTION = "Find's highlights and the Regex Builder's matches as extra selections, for rnv-text-transformer"

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

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "base_dialog.py", "find_replace_dialog.py", "regex_builder_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ['the Compare dialog: it highlights by format too, but its panes are read only and nothing listens to them.', "the current match: still a real selection of the text, made with the text's own cursor, as it always was.", 'where a Find puts its first match: at the top of the view, as ruled 2026-09-30 (item 2, left as it is).', "Find's Input / Output buttons: nothing connects them, so Find always searches the input. Found on the way; not changed here."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/base_dialog.py',
             'from contextlib import contextmanager\nfrom typing import TYPE_CHECKING, ClassVar\n',
             'from typing import TYPE_CHECKING, ClassVar\n')
    tree.sub('ui/base_dialog.py',
             'from PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QTextCursor\n',
             'from PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QBrush, QColor, QTextCharFormat, QTextCursor\n')
    tree.sub('ui/base_dialog.py',
             '    from collections.abc import Callable, Iterator\n\n    from PyQt6.QtWidgets import QTextEdit\n',
             '    from collections.abc import Callable, Iterable\n')
    tree.sub('ui/base_dialog.py',
             'from PyQt6.QtWidgets import (\n    QDialog, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,\n    QLabel, QFrame\n)\n',
             'from PyQt6.QtWidgets import (\n    QDialog, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,\n    QLabel, QFrame, QTextEdit\n)\n')
    tree.sub('ui/base_dialog.py',
             '    @contextmanager\n    def _not_an_edit(self, edit: QTextEdit) -> Iterator[None]:\n        """\n        Change the format of edit\'s text without editing it: what is done\n        inside the block is one step of the text\'s undo history, and the\n        text\'s signals are held until it ends.\n        \n        RNV-NOT-AN-EDIT 2026-09-28. Qt reports a change of format as a change\n        of the text -- textChanged fires -- and records each one as a step of\n        the undo history. Find\'s highlights and the Regex Builder\'s matches\n        are formats, and what listens to the text took each one for an edit:\n        the main window\'s statistics and auto-transform (a Find replaced an\n        output edited by hand), and the Regex Builder\'s own update, which\n        highlighted again, three times a second, for as long as it was open.\n        \n        A caret moved inside the block would not be announced either, so none\n        is: RNV-CARET-STAYS took out the last one, the caret Find\'s clear\n        moved to the end.\n        \n        Args:\n            edit: The text edit whose text is formatted\n        """\n        cursor = QTextCursor(edit.document())\n        was_blocked = edit.blockSignals(True)\n        cursor.beginEditBlock()\n        try:\n            yield\n        finally:\n            cursor.endEditBlock()\n            edit.blockSignals(was_blocked)\n    \n    @staticmethod\n    def _carries_format(edit: QTextEdit) -> bool:\n        """\n        Whether any of edit\'s text carries a character format.\n        \n        RNV-NOT-AN-EDIT 2026-09-28: resetting the format of text that carries\n        none changes nothing, and Qt records it as a step of the undo history\n        all the same -- Find did it on every key typed into its field. A\n        block\'s own character format is the line break before it, which a\n        match that runs over a line break colours too.\n        \n        Args:\n            edit: The text edit to look at\n        \n        Returns:\n            True if any character, line breaks included, has a format\n        """\n        block = edit.document().begin()\n        while block.isValid():\n            if block.charFormat().properties():\n                return True\n            it = block.begin()\n            while not it.atEnd():\n                if it.fragment().charFormat().properties():\n                    return True\n                it += 1\n            block = block.next()\n        return False\n    \n',
             '    @staticmethod\n    def _show_highlights(edit: QTextEdit, spans: Iterable[tuple[int, int]],\n                         colour: QColor) -> None:\n        """\n        Show highlights over edit\'s text without touching the text.\n        \n        RNV-EXTRA-SELECTIONS 2026-09-30. Find\'s highlights and the Regex\n        Builder\'s matches were character formats in the text: Qt reports a\n        change of format as a change of the text and records it as a step\n        of the undo history, and a copy of highlighted text carried the\n        colour to the clipboard as HTML. RNV-NOT-AN-EDIT (2026-09-28) held\n        the text\'s signals and made each paint one step; a step it still\n        was. Extra selections are Qt\'s overlay for search results: drawn\n        over the document and kept out of it, so they are no step of the\n        undo history, fire no signal, and are not copied with the text.\n        Their cursors follow an edit, so a highlight stays on the\n        characters it was painted on. An empty spans clears them.\n        \n        Args:\n            edit: The text edit the highlights are shown over\n            spans: (start, end) positions in the text, in order\n            colour: The colour every span is filled with\n        """\n        fmt = QTextCharFormat()\n        fmt.setBackground(QBrush(colour))\n        selections = []\n        for start, end in spans:\n            cursor = QTextCursor(edit.document())\n            cursor.setPosition(start)\n            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n            selection = QTextEdit.ExtraSelection()\n            selection.cursor = cursor\n            selection.format = fmt\n            selections.append(selection)\n        edit.setExtraSelections(selections)\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _highlight_all_matches(self) -> None:\n        """Highlight all matches in the text edit."""\n        if self.target_text_edit is None:\n            return\n        \n        # RNV-NOT-AN-EDIT 2026-09-28: the clear and the paint are one step of\n        # the text\'s undo history -- a step per match, before -- and not an\n        # edit of it: with auto-transform on, a Find re-ran the transform.\n        with self._not_an_edit(self.target_text_edit):\n            self._clear_highlights()\n            \n            highlight_color = self._highlight_colour()\n            \n            cursor = self.target_text_edit.textCursor()\n            format_highlight = QTextCharFormat()\n            format_highlight.setBackground(QBrush(highlight_color))\n            \n            # Apply highlighting to all matches\n            for start, end in self._current_matches:\n                cursor.setPosition(start)\n                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n        self._painted_highlight = QColor(highlight_color)\n',
             '    def _highlight_all_matches(self) -> None:\n        """Highlight all matches in the text edit."""\n        if self.target_text_edit is None:\n            return\n        \n        # RNV-EXTRA-SELECTIONS 2026-09-30: shown over the text, not written\n        # into it. This painted character formats -- one step of the undo\n        # history (RNV-NOT-AN-EDIT), and a colour a copy carried to the\n        # clipboard. Setting the selections replaces the old ones.\n        highlight_color = self._highlight_colour()\n        self._show_highlights(self.target_text_edit, self._current_matches, highlight_color)\n        self._painted_highlight = QColor(highlight_color)\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _clear_highlights(self) -> None:\n        """Clear all highlights from the text edit."""\n        if self.target_text_edit is None:\n            return\n        \n        # Reset formatting by getting plain text and setting it back\n        # This preserves the text but removes formatting\n        # RNV-CARET-STAYS 2026-09-28: through a cursor of the document\'s own,\n        # and the text\'s own is left alone. This selected the whole text with\n        # the text\'s cursor and set it back, which put the caret at the end\n        # and scrolled there -- on every key typed into Find\'s field, and on\n        # closing Find, where the match you had found was lost.\n        cursor = QTextCursor(self.target_text_edit.document())\n        cursor.select(QTextCursor.SelectionType.Document)\n        format_clear = QTextCharFormat()\n        # RNV-NOT-AN-EDIT 2026-09-28: not an edit of the text, and not made\n        # at all when the text carries no format -- it changed nothing, and\n        # was a step of the undo history for every key typed into Find.\n        if self._carries_format(self.target_text_edit):\n            with self._not_an_edit(self.target_text_edit):\n                cursor.setCharFormat(format_clear)\n        self._painted_highlight = None\n',
             '    def _clear_highlights(self) -> None:\n        """Clear all highlights from the text edit."""\n        if self.target_text_edit is None:\n            return\n        \n        # RNV-EXTRA-SELECTIONS 2026-09-30: the highlights are not in the\n        # text, so clearing them touches neither the text nor its cursor\n        # (RNV-CARET-STAYS) nor its undo history (RNV-NOT-AN-EDIT).\n        self.target_text_edit.setExtraSelections([])\n        self._painted_highlight = None\n')
    tree.sub('ui/find_replace_dialog.py',
             '        painted, edit = self._painted_highlight, self.target_text_edit\n        if painted is None or edit is None:\n            return\n        colour = self._highlight_colour()\n        if colour == painted:\n            return\n        spans = []\n        block = edit.document().begin()\n        while block.isValid():\n            it = block.begin()\n            while not it.atEnd():\n                fragment = it.fragment()\n                brush = fragment.charFormat().background()\n                if brush.style() != Qt.BrushStyle.NoBrush and brush.color() == painted:\n                    spans.append((fragment.position(), fragment.length()))\n                it += 1\n            block = block.next()\n        self._painted_highlight = QColor(colour)\n        if not spans:\n            return\n        format_highlight = QTextCharFormat()\n        format_highlight.setBackground(QBrush(colour))\n        cursor = QTextCursor(edit.document())\n        with self._not_an_edit(edit):\n            for start, length in spans:\n                cursor.setPosition(start)\n                cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n',
             '        painted, edit = self._painted_highlight, self.target_text_edit\n        if painted is None or edit is None:\n            return\n        colour = self._highlight_colour()\n        if colour == painted:\n            return\n        # RNV-EXTRA-SELECTIONS 2026-09-30: the highlights are extra\n        # selections now, whose cursors have followed any edit since the\n        # Find. Those that carry the painted colour take the new one; the\n        # text, its cursor and its undo history are not touched.\n        selections = edit.extraSelections()\n        recoloured = QTextCharFormat()\n        recoloured.setBackground(QBrush(colour))\n        for selection in selections:\n            if selection.format.background().color() == painted:\n                selection.format = recoloured\n        self._painted_highlight = QColor(colour)\n        edit.setExtraSelections(selections)\n')
    tree.sub('ui/find_replace_dialog.py',
             '            if count > 0:\n                self.target_text_edit.setPlainText(new_text)\n                self.status_label.setText(f"Replaced {count} occurrence(s)")\n',
             '            if count > 0:\n                self.target_text_edit.setPlainText(new_text)\n                # RNV-EXTRA-SELECTIONS 2026-09-30: the new text has no\n                # matches painted; the old highlights are taken down too.\n                self._clear_highlights()\n                self.status_label.setText(f"Replaced {count} occurrence(s)")\n')
    tree.sub('ui/find_replace_dialog.py',
             "        RNV-FIND-REPAINT 2026-09-28. What is recoloured is whatever carries\n        the colour they were painted in, where it now sits: an edit since\n        the Find moves the highlights with the text, so the positions the\n        Find recorded may no longer be theirs. Through a cursor of the\n        document's own, so the caret, the current match's selection and\n        the view stay where they are -- _highlight_all_matches() clears\n        through the text's own cursor, which leaves the caret at the end.\n        In one edit block, so it is one step of the text's undo history;\n        and with the text's signals held, because a colour is not an edit:\n        the statistics and the auto-transform the main window runs on\n        textChanged have nothing to do.\n",
             "        RNV-FIND-REPAINT 2026-09-28. What is recoloured is whatever carries\n        the colour they were painted in, where it now sits: an edit since\n        the Find moves the highlights with the text, so the positions the\n        Find recorded may no longer be theirs. The caret, the current\n        match's selection and the view stay where they are, and the text\n        is not edited: since RNV-EXTRA-SELECTIONS (2026-09-30) the\n        highlights are not in the text at all.\n")
    tree.sub('ui/regex_builder_dialog.py',
             "        # Clear highlighting\n        # RNV-CARET-STAYS 2026-09-28: through a cursor of the document's own,\n        # and the pane's own is left alone. This set the pane's cursor back\n        # after selecting all of it, which put the caret at the end: with no\n        # pattern or a broken one, a key typed in the middle of the test text\n        # sent it there 300 ms later.\n        cursor = QTextCursor(self.test_text.document())\n        cursor.select(QTextCursor.SelectionType.Document)\n        # RNV-NOT-AN-EDIT 2026-09-28: not an edit of the pane, and not made\n        # when the pane carries no format. The pane's textChanged re-arms the\n        # update that called this, so with no pattern, or a broken one, it\n        # ran again every 300 ms for as long as the dialog was open.\n        if self._carries_format(self.test_text):\n            with self._not_an_edit(self.test_text):\n                cursor.setCharFormat(QTextCharFormat())\n",
             "        # Clear highlighting\n        # RNV-EXTRA-SELECTIONS 2026-09-30: the matches are shown over the\n        # pane, not written into it, so taking them down touches neither\n        # the pane's text, nor its cursor (RNV-CARET-STAYS), nor its undo\n        # history, and fires nothing the update re-arms on (RNV-NOT-AN-EDIT).\n        self.test_text.setExtraSelections([])\n")
    tree.sub('ui/regex_builder_dialog.py',
             '    def _highlight_matches(self) -> None:\n        """Highlight matches in test text area."""\n        # RNV-NOT-AN-EDIT 2026-09-28: one step of the pane\'s undo history --\n        # a step per match, before -- and not an edit of it. The pane\'s\n        # textChanged re-arms the update that called this, which highlighted\n        # again, three times a second, for as long as the dialog was open.\n        with self._not_an_edit(self.test_text):\n            # First, clear existing formatting\n            cursor = self.test_text.textCursor()\n            cursor.select(QTextCursor.SelectionType.Document)\n            if self._carries_format(self.test_text):\n                cursor.setCharFormat(QTextCharFormat())\n            \n            if not self._current_matches:\n                return\n            \n            is_dark = self.theme_manager.current_theme in (\'dark\', \'image\')\n            highlight_color = QColor(self._MATCH_COLOR_DARK if is_dark else self._MATCH_COLOR_LIGHT)\n            \n            # Highlight each match\n            for match in self._current_matches:\n                cursor.setPosition(match.start)\n                cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)\n                \n                fmt = QTextCharFormat()\n                fmt.setBackground(QBrush(highlight_color))\n                cursor.mergeCharFormat(fmt)\n',
             '    def _highlight_matches(self) -> None:\n        """Highlight matches in test text area."""\n        # RNV-EXTRA-SELECTIONS 2026-09-30: shown over the pane, not written\n        # into it. This painted character formats -- one step of the pane\'s\n        # undo history (RNV-NOT-AN-EDIT) -- and setting the selections\n        # replaces the old ones, so nothing is cleared first.\n        is_dark = self.theme_manager.current_theme in (\'dark\', \'image\')\n        highlight_color = QColor(self._MATCH_COLOR_DARK if is_dark else self._MATCH_COLOR_LIGHT)\n        self._show_highlights(self.test_text,\n                              [(match.start, match.end) for match in self._current_matches],\n                              highlight_color)\n')
    tree.sub('ui/regex_builder_dialog.py',
             'from PyQt6.QtGui import (\n    QTextCharFormat, QColor, QBrush, QTextCursor, QFont\n)\n',
             'from PyQt6.QtGui import (\n    QColor, QTextCursor, QFont\n)\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             'BaseDialog._not_an_edit() holds the text\'s signals and makes a paint one step\nof the undo history; BaseDialog._carries_format() lets a reset that would\nchange nothing not be made. Every test drives the main window\'s own openers.\n"""\n',
             'RNV-NOT-AN-EDIT held the text\'s signals and made a paint one step of the\nundo history. RNV-EXTRA-SELECTIONS (2026-09-30) went the rest of the way:\nboth dialogs show their highlights as extra selections, over the text and\nnot in it -- no step of the undo history, no signal, and nothing a copy\ncarries. BaseDialog._show_highlights() paints them; _formatted() below\nnow proves the text carries no format at all, and _highlighted() reads the\nhighlights where they are. Every test drives the main window\'s own openers.\n"""\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             'def _formatted(edit) -> list:\n    """Every run of the text that carries a character format, line breaks\n    included (a block\'s own format is the line break before it)."""\n',
             'def _highlighted(edit) -> list:\n    """Every highlight shown over the text: (position, length) of each extra\n    selection that selects something. RNV-EXTRA-SELECTIONS 2026-09-30."""\n    return sorted((s.cursor.selectionStart(), s.cursor.selectionEnd() - s.cursor.selectionStart())\n                  for s in edit.extraSelections() if s.cursor.hasSelection())\n\n\ndef _formatted(edit) -> list:\n    """Every run of the text that carries a character format, line breaks\n    included (a block\'s own format is the line break before it). Since\n    RNV-EXTRA-SELECTIONS a highlight is never one of these."""\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '        assert _formatted(win.text_input), "the Find painted nothing: nothing was tested"\n        assert edits.count == 0, f"the Find fired the text\'s textChanged {edits.count} times"\n',
             '        assert _highlighted(win.text_input), "the Find painted nothing: nothing was tested"\n        assert _formatted(win.text_input) == [], "the Find wrote its highlights into the text"\n        assert edits.count == 0, f"the Find fired the text\'s textChanged {edits.count} times"\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '    def test_a_find_is_one_step_of_undo(self, main_window):\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        _typed_at_the_end(win.text_input)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert len(_formatted(win.text_input)) > 1, "fewer than two matches: nothing was tested"\n        win.text_input.undo()\n        assert _formatted(win.text_input) == [], "one Ctrl+Z did not take the Find\'s highlights away"\n        assert win.text_input.toPlainText() == TEXT + "X", "one Ctrl+Z undid more than the Find"\n        win.text_input.undo()\n        assert win.text_input.toPlainText() == TEXT, "the second Ctrl+Z did not reach the last edit"\n        dlg.close()\n',
             '    def test_a_find_adds_no_step_of_undo(self, main_window):\n        """RNV-EXTRA-SELECTIONS 2026-09-30. A Find was one step of the undo\n        history (RNV-NOT-AN-EDIT); it is none: the first Ctrl+Z after a Find\n        takes your last edit, and the highlights stay, since they are not\n        in the text to be undone."""\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        _typed_at_the_end(win.text_input)\n        steps = win.text_input.document().availableUndoSteps()\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert len(_highlighted(win.text_input)) > 1, "fewer than two matches: nothing was tested"\n        assert win.text_input.document().availableUndoSteps() == steps, \\\n            "the Find added to the text\'s undo history"\n        shown = _highlighted(win.text_input)\n        win.text_input.undo()\n        assert win.text_input.toPlainText() == TEXT, "one Ctrl+Z did not reach the last edit"\n        assert _highlighted(win.text_input) == shown, "Ctrl+Z took the highlights, which are not an edit"\n        dlg.close()\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '        assert _formatted(win.text_input)\n        dlg.close()\n        QApplication.processEvents()\n        assert _formatted(win.text_input) == [], "closing Find left its highlights"\n',
             '        assert _highlighted(win.text_input)\n        dlg.close()\n        QApplication.processEvents()\n        assert _highlighted(win.text_input) == [], "closing Find left its highlights"\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '    def test_a_highlight_on_a_line_break_is_cleared_too(self, main_window):\n        """A regular expression can match line breaks alone, and a line\n        break\'s format is its block\'s, not a run of text. Left behind, it\n        colours what is typed at the start of the next line."""\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.regex_check.setChecked(True)\n        dlg.find_input.setText("\\\\n")\n        dlg._on_find()\n        breaks = _formatted(win.text_input)\n        assert breaks and all(b[0] == "line break before" for b in breaks), \\\n            f"the Find did not colour line breaks alone: {breaks}"\n        dlg.find_input.setText("")                           # a new search clears them\n        assert _formatted(win.text_input) == [], "a line break kept the Find\'s colour"\n        dlg.close()\n',
             '    def test_a_highlight_on_a_line_break_is_cleared_too(self, main_window):\n        """A regular expression can match line breaks alone. As a format,\n        a line break\'s colour was its block\'s and could be left behind,\n        colouring what was typed at the start of the next line. As an\n        extra selection it is a selection of one character, cleared like\n        any other, and never in the text at all."""\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.regex_check.setChecked(True)\n        dlg.find_input.setText("\\\\n")\n        dlg._on_find()\n        breaks = _highlighted(win.text_input)\n        assert breaks and all(length == 1 and TEXT[pos] == "\\n" for pos, length in breaks), \\\n            f"the Find did not highlight line breaks alone: {breaks}"\n        assert _formatted(win.text_input) == [], "a line break\'s highlight was written into the text"\n        dlg.find_input.setText("")                           # a new search clears them\n        assert _highlighted(win.text_input) == [], "a line break kept the Find\'s highlight"\n        dlg.close()\n\n    def test_a_copy_of_highlighted_text_carries_no_highlight(self, main_window):\n        """RNV-EXTRA-SELECTIONS 2026-09-30. A copy made while Find\'s highlights\n        showed put them on the clipboard as HTML -- background-color on each\n        match -- and a paste into a rich-text editor brought the gold along.\n        The highlights are not in the text now, so a copy cannot carry them."""\n        win = main_window\n        win.text_input.setPlainText(TEXT)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.find_input.setText("o")\n        dlg._on_find()\n        assert _highlighted(win.text_input), "the Find painted nothing: nothing was tested"\n        cursor = win.text_input.textCursor()\n        cursor.setPosition(0)\n        cursor.setPosition(TEXT.index("\\n"), QTextCursor.MoveMode.KeepAnchor)    # the first line, 4 matches in it\n        win.text_input.setTextCursor(cursor)\n        html = win.text_input.createMimeDataFromSelection().html()\n        assert "background" not in html, "a copy of highlighted text carries the highlight: " + html[-300:]\n        assert "background" not in win.text_input.document().toHtml(), "the highlights are in the document"\n        dlg.close()\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '        assert _formatted(builder.test_text), "nothing was painted: nothing was tested"\n        edits = _Edits(builder.test_text)\n        builder.pattern_input.setText("")                    # the results are cleared\n        qtbot.wait(700)\n        assert _formatted(builder.test_text) == [], "clearing the pattern left the matches painted"\n',
             '        assert _highlighted(builder.test_text), "nothing was painted: nothing was tested"\n        assert _formatted(builder.test_text) == [], "the matches were written into the pane"\n        edits = _Edits(builder.test_text)\n        builder.pattern_input.setText("")                    # the results are cleared\n        qtbot.wait(700)\n        assert _highlighted(builder.test_text) == [], "clearing the pattern left the matches painted"\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '        qtbot.wait(700)                                      # the update runs and paints nothing\n        assert _formatted(builder.test_text) == []\n',
             '        qtbot.wait(700)                                      # the update runs and paints nothing\n        assert _highlighted(builder.test_text) == []\n')
    tree.sub('tests/test_highlighting_is_not_an_edit.py',
             '    def test_an_update_is_one_step_of_the_pane_s_undo(self, main_window, qtbot):\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("o")\n        builder.test_text.setPlainText(PANE)\n        qtbot.wait(700)\n        pane = builder.test_text\n        assert len(_formatted(pane)) > 1, "fewer than two matches painted: nothing was tested"\n        pane.undo()\n        assert _formatted(pane) == [] and pane.toPlainText() == PANE, \\\n            "one Ctrl+Z did not take the update\'s highlights away, and only those"\n        builder._update_timer.stop()\n        builder.close()\n',
             '    def test_an_update_adds_no_step_to_the_pane_s_undo(self, main_window, qtbot):\n        """RNV-EXTRA-SELECTIONS 2026-09-30. An update was one step of the\n        pane\'s undo history (RNV-NOT-AN-EDIT); it is none. A new text starts\n        its history empty, and the update leaves it so."""\n        win = main_window\n        builder = _opened(win, "_open_regex_builder_dialog")\n        builder.pattern_input.setText("o")\n        builder.test_text.setPlainText(PANE)                 # a new text: its history starts empty\n        qtbot.wait(700)\n        pane = builder.test_text\n        assert len(_highlighted(pane)) > 1, "fewer than two matches painted: nothing was tested"\n        assert pane.document().availableUndoSteps() == 0, \\\n            "the update added to the pane\'s undo history"\n        shown = _highlighted(pane)\n        pane.undo()                                          # nothing to undo\n        assert pane.toPlainText() == PANE and _highlighted(pane) == shown, \\\n            "Ctrl+Z took the update\'s highlights, which are not an edit"\n        builder._update_timer.stop()\n        builder.close()\n')
    tree.sub('tests/test_find_highlights_follow_a_switch.py',
             "- in the colour a Find run in the new mode paints, on the same characters;\n- where they now are, if the text was edited since the Find;\n- through a cursor of the document's own: the caret, the current match's\n  selection and the view stay where they are;\n- as one step of the text's undo history, and without counting as an edit.\n  The main window runs its statistics and its auto-transform on the text's\n  textChanged, and a colour is not a change to the text.\n",
             "- in the colour a Find run in the new mode paints, on the same characters;\n- where they now are, if the text was edited since the Find;\n- with the caret, the current match's selection and the view where they are;\n- without touching the text: since RNV-EXTRA-SELECTIONS (2026-09-30) the\n  highlights are extra selections, shown over the text and not in it, so a\n  switch adds nothing to the undo history and fires nothing. The main window\n  runs its statistics and its auto-transform on the text's textChanged, and\n  a colour is not a change to the text.\n")
    tree.sub('tests/test_find_highlights_follow_a_switch.py',
             'def _spans(edit) -> list:\n    """(position, length, colour, alpha) of every run of the text painted\n    with a background, block by block -- what a highlight is to the text."""\n    out = []\n    block = edit.document().begin()\n    while block.isValid():\n        it = block.begin()\n        while not it.atEnd():\n            fragment = it.fragment()\n            brush = fragment.charFormat().background()\n            if brush.style() != Qt.BrushStyle.NoBrush:\n                out.append((fragment.position(), fragment.length(),\n                            brush.color().name(), brush.color().alpha()))\n            it += 1\n        block = block.next()\n    return out\n',
             'def _spans(edit) -> list:\n    """(position, length, colour, alpha) of every highlight shown over the\n    text: its extra selections. RNV-EXTRA-SELECTIONS 2026-09-30: this read\n    the runs of the text painted with a background; none is, now."""\n    out = []\n    for selection in edit.extraSelections():\n        cursor, brush = selection.cursor, selection.format.background()\n        if cursor.hasSelection() and brush.style() != Qt.BrushStyle.NoBrush:\n            out.append((cursor.selectionStart(), cursor.selectionEnd() - cursor.selectionStart(),\n                        brush.color().name(), brush.color().alpha()))\n    return sorted(out)\n')
    tree.sub('tests/test_find_highlights_follow_a_switch.py',
             '    def test_one_switch_is_one_step_of_undo(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        dark = _spans(win.text_input)\n        assert _switch(win, "cycle") == "light"\n        assert _spans(win.text_input) != dark, "the switch repainted nothing"\n        win.text_input.undo()\n        assert _spans(win.text_input) == dark, "undoing a switch\'s repaint took more than one step"\n        assert win.text_input.toPlainText() == TEXT\n        dlg.close()\n',
             '    def test_a_switch_adds_no_step_of_undo(self, main_window):\n        """RNV-EXTRA-SELECTIONS 2026-09-30. A switch\'s repaint was one step of\n        the undo history; it is none, and Ctrl+Z cannot take it back."""\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        dark = _spans(win.text_input)\n        steps = win.text_input.document().availableUndoSteps()\n        assert _switch(win, "cycle") == "light"\n        light = _spans(win.text_input)\n        assert light != dark, "the switch repainted nothing"\n        assert win.text_input.document().availableUndoSteps() == steps, "the switch added to the undo history"\n        win.text_input.undo()\n        assert _spans(win.text_input) == light, "Ctrl+Z took the repaint, which is not an edit"\n        assert win.text_input.toPlainText() == TEXT\n        dlg.close()\n')
    tree.sub('tests/test_caret_stays_put.py',
             'def _painted(edit) -> int:\n    runs, block = 0, edit.document().begin()\n    while block.isValid():\n        it = block.begin()\n        while not it.atEnd():\n            runs += bool(it.fragment().charFormat().properties())\n            it += 1\n        block = block.next()\n    return runs\n',
             'def _painted(edit) -> int:\n    """The highlights shown over the text. RNV-EXTRA-SELECTIONS 2026-09-30:\n    this counted the runs of the text carrying a format; none does, now."""\n    return sum(1 for s in edit.extraSelections() if s.cursor.hasSelection())\n')
    tree.sub('tests/test_dialogs_follow_a_switch.py',
             '        for _ in range(3):\n            win._cycle_theme()\n            cursor = dlg.test_text.textCursor()\n            cursor.setPosition(start + 1)\n            painted = cursor.charFormat().background().color().name()\n',
             '        for _ in range(3):\n            win._cycle_theme()\n            # RNV-EXTRA-SELECTIONS 2026-09-30: the matches are extra selections\n            # over the pane, not formats in it; the one on the first match\n            over = [s for s in dlg.test_text.extraSelections()\n                    if s.cursor.selectionStart() <= start < s.cursor.selectionEnd()]\n            assert len(over) == 1, f"the first match is under {len(over)} highlights"\n            painted = over[0].format.background().color().name()\n')


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
    def methods(src, cls):
        body = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == cls).body
        return {n.name: n for n in body if isinstance(n, ast.FunctionDef)}

    def outside(src, cls):
        """The module minus the class, its imports and its TYPE_CHECKING imports."""
        return [ast.dump(x) for x in ast.parse(src).body
                if not (isinstance(x, (ast.Import, ast.ImportFrom))
                        or (isinstance(x, ast.ClassDef) and x.name == cls)
                        or (isinstance(x, ast.If) and ast.unparse(x.test) == "TYPE_CHECKING"))]

    def calls(node):
        return {getattr(c.func, "attr", getattr(c.func, "id", None)) for c in ast.walk(node) if isinstance(c, ast.Call)}

    def tests_in(src):
        return [n.name for c in ast.parse(src).body if isinstance(c, ast.ClassDef)
                for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]

    # ---- BaseDialog: the two helpers that held the text go, one that paints over it comes
    old_b, new_b = _original(tree, "ui/base_dialog.py"), tree.read("ui/base_dialog.py")
    o, n = methods(old_b, "BaseDialog"), methods(new_b, "BaseDialog")
    assert set(o) - set(n) == {"_not_an_edit", "_carries_format"}, f"BaseDialog lost {sorted(set(o) - set(n))}"
    assert set(n) - set(o) == {"_show_highlights"}, f"BaseDialog gained {sorted(set(n) - set(o))}"
    kept = sorted(k for k in set(o) & set(n) if ast.dump(o[k]) != ast.dump(n[k]))
    assert not kept, f"BaseDialog: methods moved beyond the three: {kept}"
    assert outside(old_b, "BaseDialog") == outside(new_b, "BaseDialog"), "base_dialog.py moved beyond the class and its imports"
    show = n["_show_highlights"]
    assert "edit.setExtraSelections(selections)" in ast.unparse(show) and "QTextEdit.ExtraSelection()" in ast.unparse(show), \
        "_show_highlights() does not paint through extra selections"
    assert not calls(show) & {"mergeCharFormat", "setCharFormat", "beginEditBlock", "blockSignals", "insertText"}, \
        "_show_highlights() touches the text"

    # ---- the two dialogs: the methods derived moved, and no other
    old_f, new_f = _original(tree, "ui/find_replace_dialog.py"), tree.read("ui/find_replace_dialog.py")
    o, n = methods(old_f, "FindReplaceDialog"), methods(new_f, "FindReplaceDialog")
    assert set(o) == set(n), f"FindReplaceDialog: methods added or removed: {sorted(set(o) ^ set(n))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["_clear_highlights", "_highlight_all_matches", "_on_replace_all", "_recolour_highlights"], \
        f"FindReplaceDialog: moved {moved}"
    assert outside(old_f, "FindReplaceDialog") == outside(new_f, "FindReplaceDialog"), "find_replace_dialog.py moved beyond the class"
    import copy
    def without_clear(fn):
        fn = copy.deepcopy(fn)
        for node in ast.walk(fn):
            for field in ("body", "orelse", "finalbody"):
                stmts = getattr(node, field, None)
                if isinstance(stmts, list):
                    setattr(node, field, [s for s in stmts if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                                                                   and ast.unparse(s.value) == "self._clear_highlights()")])
        return fn
    assert ast.dump(without_clear(n["_on_replace_all"])) == ast.dump(o["_on_replace_all"]), \
        "_on_replace_all() changed beyond clearing the highlights"
    replaced = [x for x in ast.walk(n["_on_replace_all"]) if isinstance(x, ast.If) and ast.unparse(x.test) == "count > 0"]
    assert len(replaced) == 1 and [ast.unparse(s) for s in replaced[0].body[:2]] == \
        ["self.target_text_edit.setPlainText(new_text)", "self._clear_highlights()"], \
        "the highlights are not cleared straight after the text is replaced"
    ham = ast.unparse(n["_highlight_all_matches"])
    assert "self._show_highlights(self.target_text_edit, self._current_matches, highlight_color)" in ham \
        and "self._painted_highlight = QColor(highlight_color)" in ham, "the Find does not paint through the helper"
    assert "self.target_text_edit.setExtraSelections([])" in ast.unparse(n["_clear_highlights"]) \
        and "self._painted_highlight = None" in ast.unparse(n["_clear_highlights"]), "the clear does not take the selections down"
    rc = ast.unparse(n["_recolour_highlights"])
    assert "edit.extraSelections()" in rc and "edit.setExtraSelections(selections)" in rc \
        and "selection.format.background().color() == painted" in rc, "the switch does not recolour the selections by colour"
    old_r, new_r = _original(tree, "ui/regex_builder_dialog.py"), tree.read("ui/regex_builder_dialog.py")
    o, n = methods(old_r, "RegexBuilderDialog"), methods(new_r, "RegexBuilderDialog")
    assert set(o) == set(n), f"RegexBuilderDialog: methods added or removed: {sorted(set(o) ^ set(n))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["_clear_results", "_highlight_matches"], f"RegexBuilderDialog: moved {moved}"
    assert outside(old_r, "RegexBuilderDialog") == outside(new_r, "RegexBuilderDialog"), "regex_builder_dialog.py moved beyond the class"
    assert "self.test_text.setExtraSelections([])" in ast.unparse(n["_clear_results"]), "the clear does not take the selections down"
    assert "self._show_highlights(self.test_text" in ast.unparse(n["_highlight_matches"]), "the Regex Builder does not paint through the helper"
    # derived: in the two dialogs, highlighting is never a change of format now; and
    # nothing in the application still names the helpers that held the text
    for rel, src in (("ui/find_replace_dialog.py", new_f), ("ui/regex_builder_dialog.py", new_r)):
        hit = calls(ast.parse(src)) & {"mergeCharFormat", "setCharFormat", "beginEditBlock", "blockSignals"}
        assert not hit, f"{rel} still changes a format or holds a signal: {sorted(hit)}"
    for p in sorted(tree.root.rglob("*.py")):
        rel = p.relative_to(tree.root).as_posix()
        if rel.startswith(("tests/", ".")) or "/__pycache__/" in rel or rel in ("up.py", "conftest.py") \
                or rel.startswith(("test_", "up")):
            continue
        text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
        assert "_not_an_edit" not in text and "_carries_format" not in text, \
            f"{rel} still names a helper this round removes"

    # ---- the premise: the widgets the highlights are shown over are QTextEdits
    main = tree.read("ui/main_window.py")
    for opener in ("_open_find_dialog", "_open_replace_dialog"):
        assert "target_text_edit=self.text_input" in ast.unparse(_function(main, opener, "MainWindow")), \
            f"{opener}() no longer hands Find the main text"
    assert "self.text_input = DragDropTextEdit()" in main, "the main text is no longer a DragDropTextEdit"
    assert "class DragDropTextEdit(QTextEdit):" in tree.read("ui/drag_drop_text_edit.py"), \
        "DragDropTextEdit is no longer a QTextEdit: extra selections need one"
    assert "self.test_text = QTextEdit()" in new_r, "the Regex Builder's pane is no longer a QTextEdit"

    # ---- the guards: each reads the highlights where they are, and the tests derived are there
    want = {
        "tests/test_highlighting_is_not_an_edit.py": [
            "test_a_find_does_not_edit_the_text", "test_a_find_adds_no_step_of_undo",
            "test_typing_into_find_leaves_the_text_and_its_history_alone", "test_closing_find_does_not_edit_the_text",
            "test_a_highlight_on_a_line_break_is_cleared_too", "test_a_copy_of_highlighted_text_carries_no_highlight",
            "test_it_does_nothing_while_nothing_changes", "test_an_edit_still_updates_the_matches",
            "test_clearing_the_pattern_is_not_an_edit_of_the_pane", "test_with_nothing_to_paint_the_pane_s_history_is_its_own",
            "test_an_update_adds_no_step_to_the_pane_s_undo"],
        "tests/test_find_highlights_follow_a_switch.py": [
            "test_each_mode_paints_them_as_a_find_run_in_it_would", "test_the_caret_the_current_match_and_the_view_stay_put",
            "test_a_switch_repaints_without_counting_as_an_edit", "test_a_switch_adds_no_step_of_undo",
            "test_a_switch_that_keeps_the_colour_leaves_the_text_alone",
            "test_highlights_moved_by_an_edit_are_repainted_where_they_now_are",
            "test_with_nothing_painted_the_text_is_left_alone", "test_find_and_find_and_replace_open_together_both_follow"],
    }
    for rel, names in want.items():
        assert tests_in(tree.read(rel)) == names, f"{rel}: its tests are {tests_in(tree.read(rel))}"
    for rel in ("tests/test_caret_stays_put.py", "tests/test_dialogs_follow_a_switch.py"):
        assert tests_in(_original(tree, rel)) == tests_in(tree.read(rel)), f"{rel}: its tests moved"
    for rel in GUARD_FILES:
        assert "extraSelections()" in tree.read(rel), f"{rel} does not read the highlights where they are"
        assert "charFormat().background" not in tree.read(rel) or rel == "tests/test_highlighting_is_not_an_edit.py", \
            f"{rel} still reads highlights as character formats"
    assert SENTINEL in new_b and SENTINEL in new_f and SENTINEL in new_r, "the sentinel is not in every file this round changes"
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
