"""
tests/test_caret_stays_put.py
=============================
RNV-CARET-STAYS, 2026-09-28. Clearing highlights leaves the caret where it is.

Find and the Regex Builder cleared their highlights by selecting the whole
text with the widget's own cursor, clearing the selection and setting that
cursor back -- which left the caret at the end of the text and scrolled
there. Three places a person met it:

1. typing into Find's search box: every key sent the main text's caret to
   the end and scrolled to the bottom;
2. closing Find: the same, so the match you had found was lost;
3. the Regex Builder, with no pattern or a broken one: a key typed in the
   middle of the test text sent the caret to the end 300 ms later.

The clears now reset through a cursor of the document's own. A Find still
shows its first match at the top of the view, where it always has; that
placement came from the clear's detour to the end, and is now made on
purpose. Every test drives the main window's own openers, with the window
shown, so the view has a size to scroll.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from ui.base_dialog import BaseDialog

LINES = [f"line {i:02d}: the quick brown fox jumps over the lazy dog" for i in range(1, 61)]
LINES[4] = "line 05: here is the word needle, on line five"
LINES[39] = "line 40: here is the word pin, on line forty"
TEXT = "\n".join(LINES) + "\n"
PANE = "foo boo zoo\nmoo\n"


@pytest.fixture
def shown(main_window, qtbot):
    win = main_window
    win.resize(1200, 860)
    win.show()
    qtbot.waitExposed(win)
    win.text_input.setPlainText(TEXT)
    QApplication.processEvents()
    return win


def _opened(win, opener: str) -> BaseDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    return new[0]


def _put(edit, position: int, view: int = 0) -> None:
    cursor = edit.textCursor()
    cursor.setPosition(position)
    edit.setTextCursor(cursor)
    edit.verticalScrollBar().setValue(view)
    QApplication.processEvents()


def _where(edit) -> tuple:
    """The caret, the selection and the view: what a person sees move."""
    cursor = edit.textCursor()
    return (cursor.anchor(), cursor.position(), cursor.selectedText(),
            edit.verticalScrollBar().value())


def _painted(edit) -> int:
    """The highlights shown over the text. RNV-EXTRA-SELECTIONS 2026-09-30:
    this counted the runs of the text carrying a format; none does, now."""
    return sum(1 for s in edit.extraSelections() if s.cursor.hasSelection())


def _found_the_second(win):
    """Find for "quick", then Find Next: the second match selected."""
    dlg = _opened(win, "_open_find_dialog")
    dlg.find_input.setText("quick")
    dlg._on_find()
    dlg._on_find_next()
    QApplication.processEvents()
    where = _where(win.text_input)
    assert where[2] == "quick" and _painted(win.text_input), "the Find found nothing to keep"
    return dlg, where


class TestFindLeavesTheCaret:

    def test_typing_into_find_leaves_the_caret_and_the_view(self, shown):
        edit = shown.text_input
        _put(edit, 100)
        before = _where(edit)
        dlg = _opened(shown, "_open_find_dialog")
        for i in range(1, 6):
            dlg.find_input.setText("hello"[:i])              # five keys, no Find run
        assert _where(edit) == before, f"typing into Find moved the text: {before} -> {_where(edit)}"
        dlg.close()

    def test_typing_a_new_search_keeps_the_match_you_found(self, shown):
        edit = shown.text_input
        dlg, where = _found_the_second(shown)
        for i in range(1, 5):
            dlg.find_input.setText("lazy"[:i])               # a new search, typed
        assert _painted(edit) == 0, "the old search's highlights stayed"
        assert _where(edit) == where, f"typing a new search moved the text: {where} -> {_where(edit)}"
        dlg.close()

    def test_closing_find_leaves_the_found_match_selected(self, shown):
        edit = shown.text_input
        dlg, where = _found_the_second(shown)
        dlg.close()
        QApplication.processEvents()
        assert _painted(edit) == 0, "closing Find left its highlights"
        assert _where(edit) == where, f"closing Find moved the text: {where} -> {_where(edit)}"

    def test_a_find_that_finds_nothing_leaves_the_caret(self, shown):
        edit = shown.text_input
        _put(edit, 100)
        before = _where(edit)
        dlg = _opened(shown, "_open_find_dialog")
        dlg.find_input.setText("zzz")
        dlg._on_find()
        assert dlg.status_label.text() == "No matches found"
        assert _where(edit) == before, f"a Find with no match moved the text: {before} -> {_where(edit)}"
        dlg.close()

    @pytest.mark.parametrize("word, view", [("needle", "top"), ("pin", "top"), ("needle", "bottom")],
                             ids=["on-screen", "below-the-view", "above-the-view"])
    def test_a_find_still_shows_its_first_match_at_the_top(self, shown, word, view):
        edit = shown.text_input
        bar = edit.verticalScrollBar()
        _put(edit, 0, 0 if view == "top" else bar.maximum())
        dlg = _opened(shown, "_open_find_dialog")
        dlg.find_input.setText(word)
        dlg._on_find()
        QApplication.processEvents()
        assert edit.textCursor().selectedText() == word
        assert edit.cursorRect().top() == 0 and bar.value() < bar.maximum(), \
            f"the first match is drawn at y {edit.cursorRect().top()}, not at the top of the view"
        dlg.close()


class TestTheRegexBuilderLeavesTheCaret:

    @pytest.mark.parametrize("pattern", ["", "(o", "o"], ids=["no-pattern", "broken-pattern", "pattern"])
    def test_a_key_typed_in_the_middle_stays_in_the_middle(self, main_window, qtbot, pattern):
        builder = _opened(main_window, "_open_regex_builder_dialog")
        builder.pattern_input.setText(pattern)
        pane = builder.test_text
        pane.setPlainText(PANE)
        qtbot.wait(700)
        cursor = pane.textCursor()
        cursor.setPosition(3)
        pane.setTextCursor(cursor)
        pane.insertPlainText("x")                            # a key typed in the middle
        qtbot.wait(700)                                      # the update runs
        assert pane.textCursor().position() == 4, \
            f"the caret went from 4 to {pane.textCursor().position()} (the text ends at {len(pane.toPlainText())})"
        builder.close()

    def test_a_selection_in_the_pane_survives_an_update(self, main_window, qtbot):
        builder = _opened(main_window, "_open_regex_builder_dialog")
        pane = builder.test_text
        pane.setPlainText(PANE)
        qtbot.wait(700)
        cursor = pane.textCursor()
        cursor.setPosition(4)
        cursor.setPosition(7, cursor.MoveMode.KeepAnchor)
        pane.setTextCursor(cursor)
        builder.pattern_input.setText("(")                   # a broken pattern: the results clear
        qtbot.wait(700)
        assert pane.textCursor().selectedText() == "boo", "an update dropped the selection in the pane"
        builder.close()
