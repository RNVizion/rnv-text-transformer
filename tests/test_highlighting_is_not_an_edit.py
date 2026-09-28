"""
tests/test_highlighting_is_not_an_edit.py
=========================================
RNV-NOT-AN-EDIT, 2026-09-28. Painting highlights is not an edit of the text.

Qt reports a change of format as a change of the text -- textChanged fires --
and records each one as a step of the undo history. Two of this app's
dialogs highlight by format, and what listens to the text took each
highlight for an edit:

1. Find. A Find fired the main text's textChanged once per match; with
   auto-transform on, that re-ran the transform and replaced an output
   edited by hand; and each match was a Ctrl+Z press between you and your
   last edit. Typing into Find's field did the same once per key, with
   nothing painted; so did closing Find.
2. The Regex Builder. Its highlighting fired the test pane's textChanged,
   which re-armed the 300 ms update, which highlighted again: about three
   times a second, for as long as the dialog was open, with a pattern, with
   none and with a broken one. The pane's undo history grew without end.

BaseDialog._not_an_edit() holds the text's signals and makes a paint one step
of the undo history; BaseDialog._carries_format() lets a reset that would
change nothing not be made. Every test drives the main window's own openers.
"""
from __future__ import annotations

import pytest
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication

from ui.base_dialog import BaseDialog

TEXT = ("The quick brown fox jumps over the lazy dog.\n"
        "Pack my box with five dozen liquor jugs.\n"
        "How vexingly quick daft zebras jump over the log.\n")
HAND = "an output edited by hand"
PANE = "foo boo zoo\nmoo\n"


def _opened(win, opener: str) -> BaseDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    return new[0]


def _formatted(edit) -> list:
    """Every run of the text that carries a character format, line breaks
    included (a block's own format is the line break before it)."""
    out = []
    block = edit.document().begin()
    while block.isValid():
        if block.charFormat().properties():
            out.append(("line break before", block.position()))
        it = block.begin()
        while not it.atEnd():
            if it.fragment().charFormat().properties():
                out.append((it.fragment().position(), it.fragment().length()))
            it += 1
        block = block.next()
    return out


def _typed_at_the_end(edit, text: str = "X") -> None:
    """A real edit: text typed at the end, through the text's own caret."""
    cursor = edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    edit.setTextCursor(cursor)
    edit.insertPlainText(text)


class _Edits:
    """Counts the text's textChanged."""

    def __init__(self, edit):
        self.count = 0
        edit.textChanged.connect(self._bump)

    def _bump(self):
        self.count += 1


@pytest.fixture
def watched(main_window):
    """The main window with auto-transform on, its text filled, and an
    output edited by hand after the transform that filling started."""
    win = main_window
    win.settings_manager.save_auto_transform(True)
    win.text_input.setPlainText(TEXT)
    win.auto_transform_timer.stop()
    win.output_text.setPlainText(HAND)
    yield win, _Edits(win.text_input)
    win.auto_transform_timer.stop()


class TestFindIsNotAnEdit:

    def test_a_find_does_not_edit_the_text(self, watched):
        win, edits = watched
        dlg = _opened(win, "_open_find_dialog")
        dlg.find_input.setText("o")
        dlg._on_find()
        assert _formatted(win.text_input), "the Find painted nothing: nothing was tested"
        assert edits.count == 0, f"the Find fired the text's textChanged {edits.count} times"
        assert not win.auto_transform_timer.isActive(), "the Find set the auto-transform going"
        assert win.output_text.toPlainText() == HAND
        _typed_at_the_end(win.text_input)                    # and a real edit still is one
        assert edits.count == 1, "the text's signals were left held after the Find"
        dlg.close()

    def test_a_find_is_one_step_of_undo(self, main_window):
        win = main_window
        win.text_input.setPlainText(TEXT)
        _typed_at_the_end(win.text_input)
        dlg = _opened(win, "_open_find_dialog")
        dlg.find_input.setText("o")
        dlg._on_find()
        assert len(_formatted(win.text_input)) > 1, "fewer than two matches: nothing was tested"
        win.text_input.undo()
        assert _formatted(win.text_input) == [], "one Ctrl+Z did not take the Find's highlights away"
        assert win.text_input.toPlainText() == TEXT + "X", "one Ctrl+Z undid more than the Find"
        win.text_input.undo()
        assert win.text_input.toPlainText() == TEXT, "the second Ctrl+Z did not reach the last edit"
        dlg.close()

    def test_typing_into_find_leaves_the_text_and_its_history_alone(self, watched):
        win, edits = watched
        _typed_at_the_end(win.text_input)
        edits.count = 0
        dlg = _opened(win, "_open_find_dialog")
        steps = win.text_input.document().availableUndoSteps()
        for i in range(1, 6):
            dlg.find_input.setText("hello"[:i])              # five keys, nothing found yet
        assert edits.count == 0, f"typing into Find fired the text's textChanged {edits.count} times"
        assert win.text_input.document().availableUndoSteps() == steps, \
            "typing into Find added to the text's undo history"
        win.text_input.undo()
        assert win.text_input.toPlainText() == TEXT, "one Ctrl+Z did not reach the last edit"
        dlg.close()

    def test_closing_find_does_not_edit_the_text(self, watched):
        win, edits = watched
        dlg = _opened(win, "_open_find_dialog")
        dlg.find_input.setText("o")
        dlg._on_find()
        assert _formatted(win.text_input)
        dlg.close()
        QApplication.processEvents()
        assert _formatted(win.text_input) == [], "closing Find left its highlights"
        assert edits.count == 0, f"closing Find fired the text's textChanged {edits.count} times"
        assert win.output_text.toPlainText() == HAND and not win.auto_transform_timer.isActive()

    def test_a_highlight_on_a_line_break_is_cleared_too(self, main_window):
        """A regular expression can match line breaks alone, and a line
        break's format is its block's, not a run of text. Left behind, it
        colours what is typed at the start of the next line."""
        win = main_window
        win.text_input.setPlainText(TEXT)
        dlg = _opened(win, "_open_find_dialog")
        dlg.regex_check.setChecked(True)
        dlg.find_input.setText("\\n")
        dlg._on_find()
        breaks = _formatted(win.text_input)
        assert breaks and all(b[0] == "line break before" for b in breaks), \
            f"the Find did not colour line breaks alone: {breaks}"
        dlg.find_input.setText("")                           # a new search clears them
        assert _formatted(win.text_input) == [], "a line break kept the Find's colour"
        dlg.close()


class TestTheRegexBuilderRests:

    @pytest.mark.parametrize("pattern", ["o", "", "(o"], ids=["pattern", "no-pattern", "broken-pattern"])
    def test_it_does_nothing_while_nothing_changes(self, main_window, qtbot, pattern):
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText(pattern)
        builder.test_text.setPlainText(PANE)
        qtbot.wait(700)                                      # the update the edits asked for
        runs = []
        builder._update_timer.timeout.connect(lambda: runs.append(1))
        steps = builder.test_text.document().availableUndoSteps()
        qtbot.wait(1500)                                     # nothing happens for 1.5 s
        assert runs == [], f"the Regex Builder updated {len(runs)} times with nothing changed"
        assert builder.test_text.document().availableUndoSteps() == steps, \
            "the test pane's undo history grew with nothing changed"
        builder.close()

    def test_an_edit_still_updates_the_matches(self, main_window, qtbot):
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText("o")
        builder.test_text.setPlainText(PANE)
        qtbot.wait(700)
        before = len(builder._current_matches)
        assert before == 8, before
        builder.test_text.insertPlainText("oo")              # a real edit of the pane
        qtbot.wait(700)
        assert len(builder._current_matches) == before + 2, "an edit of the test text no longer updates"
        builder.close()

    def test_clearing_the_pattern_is_not_an_edit_of_the_pane(self, main_window, qtbot):
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText("o")
        builder.test_text.setPlainText(PANE)
        qtbot.wait(700)
        assert _formatted(builder.test_text), "nothing was painted: nothing was tested"
        edits = _Edits(builder.test_text)
        builder.pattern_input.setText("")                    # the results are cleared
        qtbot.wait(700)
        assert _formatted(builder.test_text) == [], "clearing the pattern left the matches painted"
        assert edits.count == 0, f"clearing the matches fired the pane's textChanged {edits.count} times"
        builder.close()

    @pytest.mark.parametrize("pattern", ["", "(o", "zzz"], ids=["no-pattern", "broken-pattern", "no-match"])
    def test_with_nothing_to_paint_the_pane_s_history_is_its_own(self, main_window, qtbot, pattern):
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText(pattern)
        builder.test_text.setPlainText(PANE)                 # a new text: its history starts empty
        qtbot.wait(700)                                      # the update runs and paints nothing
        assert _formatted(builder.test_text) == []
        assert builder.test_text.document().availableUndoSteps() == 0, \
            "an update that painted nothing added to the pane's undo history"
        builder.close()

    def test_an_update_is_one_step_of_the_pane_s_undo(self, main_window, qtbot):
        win = main_window
        builder = _opened(win, "_open_regex_builder_dialog")
        builder.pattern_input.setText("o")
        builder.test_text.setPlainText(PANE)
        qtbot.wait(700)
        pane = builder.test_text
        assert len(_formatted(pane)) > 1, "fewer than two matches painted: nothing was tested"
        pane.undo()
        assert _formatted(pane) == [] and pane.toPlainText() == PANE, \
            "one Ctrl+Z did not take the update's highlights away, and only those"
        builder._update_timer.stop()
        builder.close()
