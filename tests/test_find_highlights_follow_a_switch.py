"""
tests/test_find_highlights_follow_a_switch.py
=============================================
RNV-FIND-REPAINT, 2026-09-28. The highlights Find paints into the main
window's text follow a theme switch made while the dialog is open.

Find paints every match into the text in the mode's accent, at alpha 80,
when it runs. RNV-DIALOG-SWITCH made the open dialog follow a switch; the
highlights it had drawn did not, and kept the old mode's accent until the
next Find -- dark's accent on light's ground. Now the dialog paints them
again when it is refreshed:

- in the colour a Find run in the new mode paints, on the same characters;
- where they now are, if the text was edited since the Find;
- with the caret, the current match's selection and the view where they are;
- without touching the text: since RNV-EXTRA-SELECTIONS (2026-09-30) the
  highlights are extra selections, shown over the text and not in it, so a
  switch adds nothing to the undo history and fires nothing. The main window
  runs its statistics and its auto-transform on the text's textChanged, and
  a colour is not a change to the text.

Every test drives the main window's own opener and its own two roads to a
switch: the theme cycle, and the theme Settings applies.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTextEdit

from ui.base_dialog import BaseDialog
from ui.find_replace_dialog import FindReplaceDialog

TEXT = ("The quick brown fox jumps over the lazy dog.\n"
        "Pack my box with five dozen liquor jugs.\n"
        "How vexingly quick daft zebras jump over the log.\n"
        "Sphinx of black quartz, judge my vow.\n"
        "Two driven jocks help fax my big quiz.\n")
HEADER = "Header line\n"        # no "o" in it: a Find for "o" finds nothing new


def _spans(edit) -> list:
    """(position, length, colour, alpha) of every highlight shown over the
    text: its extra selections. RNV-EXTRA-SELECTIONS 2026-09-30: this read
    the runs of the text painted with a background; none is, now."""
    out = []
    for selection in edit.extraSelections():
        cursor, brush = selection.cursor, selection.format.background()
        if cursor.hasSelection() and brush.style() != Qt.BrushStyle.NoBrush:
            out.append((cursor.selectionStart(), cursor.selectionEnd() - cursor.selectionStart(),
                        brush.color().name(), brush.color().alpha()))
    return sorted(out)


def _in_dark(win) -> None:
    for _ in range(3):
        if win.theme_manager.current_theme == "dark":
            return
        win._cycle_theme()
    assert win.theme_manager.current_theme == "dark"


def _switch(win, road: str, theme: str | None = None) -> str:
    """One switch by the main window's own road; the mode it lands in."""
    if road == "cycle":
        win._cycle_theme()
    else:
        order = ("dark", "light", "image")
        now = win.theme_manager.current_theme
        win._apply_theme_from_settings(theme or order[(order.index(now) + 1) % 3])
    QApplication.processEvents()
    return win.theme_manager.current_theme


def _found(win, needle: str = "o", nexts: int = 2, opener: str = "_open_find_dialog"):
    """Find opened with the main window's own opener, run for `needle`, and
    Find Next pressed `nexts` times: every match painted, one of them current."""
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    dlg = new[0]
    dlg.find_input.setText(needle)
    dlg._on_find()
    for _ in range(nexts):
        dlg._on_find_next()
    QApplication.processEvents()
    assert dlg._current_matches, "the Find found nothing to paint"
    return dlg


def _fresh(win, text: str, needle: str = "o") -> list:
    """What a Find run now, in the current mode, paints: the same Find on a
    copy of the text, in a dialog of its own."""
    copy = QTextEdit()
    copy.setPlainText(text)
    dlg = FindReplaceDialog(theme_manager=win.theme_manager, font_family=win.font_family,
                            target_text_edit=copy)
    dlg.find_input.setText(needle)
    dlg._on_find()
    spans = _spans(copy)
    dlg.deleteLater()
    copy.deleteLater()
    return spans


def _where(edit) -> tuple:
    cursor = edit.textCursor()
    return (cursor.position(), cursor.anchor(), cursor.selectedText(),
            edit.verticalScrollBar().value())


class TestFindHighlightsFollowASwitch:

    @pytest.mark.parametrize("road", ["cycle", "settings"])
    def test_each_mode_paints_them_as_a_find_run_in_it_would(self, main_window, road):
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        dlg = _found(win)
        seen = {"dark": _spans(win.text_input)}
        assert seen["dark"] == _fresh(win, TEXT), "the Find itself did not paint what a Find paints"
        for _ in range(3):                                   # every mode, and back
            mode = _switch(win, road)
            seen[mode] = _spans(win.text_input)
            assert seen[mode] == _fresh(win, TEXT), (road, mode)
        assert {"dark", "light", "image"} <= set(seen), sorted(seen)
        assert seen["dark"] != seen["light"], "dark and light paint the same colour: nothing was tested"
        dlg.close()

    def test_the_caret_the_current_match_and_the_view_stay_put(self, main_window, qtbot):
        win = main_window
        win.show()
        qtbot.waitExposed(win)
        _in_dark(win)
        win.text_input.setPlainText(TEXT * 8)
        dlg = _found(win, nexts=40)                          # a current match far down
        where = _where(win.text_input)
        assert where[2] == "o" and where[3] > 0, f"the current match is not selected down the text: {where}"
        for _ in range(3):
            mode = _switch(win, "cycle")
            assert _where(win.text_input) == where, (mode, _where(win.text_input), where)
        dlg.close()

    def test_a_switch_repaints_without_counting_as_an_edit(self, main_window):
        win = main_window
        _in_dark(win)
        win.settings_manager.save_auto_transform(True)
        win.text_input.setPlainText(TEXT)
        dlg = _found(win)
        win.auto_transform_timer.stop()                      # the Find's own run, as shipped
        win.output_text.setPlainText("an output edited by hand")
        edits = []
        win.text_input.textChanged.connect(lambda: edits.append(win.theme_manager.current_theme))
        before = _spans(win.text_input)
        assert _switch(win, "cycle") == "light"
        assert _spans(win.text_input) != before, "the switch repainted nothing"
        assert edits == [], f"the repaint counted as an edit of the text: {edits}"
        assert not win.auto_transform_timer.isActive(), "a switch set the auto-transform going"
        assert win.output_text.toPlainText() == "an output edited by hand"
        win.text_input.insertPlainText("x")                  # and the text's signals are back
        win.auto_transform_timer.stop()
        assert edits, "the text's signals were left held after the repaint"
        dlg.close()

    def test_a_switch_adds_no_step_of_undo(self, main_window):
        """RNV-EXTRA-SELECTIONS 2026-09-30. A switch's repaint was one step of
        the undo history; it is none, and Ctrl+Z cannot take it back."""
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        dlg = _found(win)
        dark = _spans(win.text_input)
        steps = win.text_input.document().availableUndoSteps()
        assert _switch(win, "cycle") == "light"
        light = _spans(win.text_input)
        assert light != dark, "the switch repainted nothing"
        assert win.text_input.document().availableUndoSteps() == steps, "the switch added to the undo history"
        win.text_input.undo()
        assert _spans(win.text_input) == light, "Ctrl+Z took the repaint, which is not an edit"
        assert win.text_input.toPlainText() == TEXT
        dlg.close()

    def test_a_switch_that_keeps_the_colour_leaves_the_text_alone(self, main_window):
        """Image paints with dark's accent: from image to dark there is
        nothing to repaint, and nothing is added to the text's undo history."""
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        dlg = _found(win)
        doc = win.text_input.document()
        assert [_switch(win, "cycle"), _switch(win, "cycle")] == ["light", "image"]
        spans, steps = _spans(win.text_input), doc.availableUndoSteps()
        assert _switch(win, "cycle") == "dark"
        assert _spans(win.text_input) == spans, "image to dark changed the highlights"
        assert doc.availableUndoSteps() == steps, "a switch that keeps the colour added to the undo history"
        dlg.close()

    def test_highlights_moved_by_an_edit_are_repainted_where_they_now_are(self, main_window):
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        dlg = _found(win)
        dark = _spans(win.text_input)
        edit = win.text_input
        from PyQt6.QtGui import QTextCursor
        QTextCursor(edit.document()).insertText(HEADER)      # typed at the top since the Find
        moved = _spans(edit)
        assert [s[0] for s in moved] == [s[0] + len(HEADER) for s in dark], "the edit did not move them"
        assert _switch(win, "cycle") == "light"
        assert _spans(edit) == _fresh(win, HEADER + TEXT), "not repainted on the characters they sit on"
        dlg.close()

    def test_with_nothing_painted_the_text_is_left_alone(self, main_window):
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        doc = win.text_input.document()
        dlg = _found(win)
        dlg.find_input.setText("")                           # a new search clears them
        steps = doc.availableUndoSteps()
        for _ in range(3):
            _switch(win, "cycle")
            assert _spans(win.text_input) == [] and doc.availableUndoSteps() == steps
        dlg.close()

    def test_find_and_find_and_replace_open_together_both_follow(self, main_window):
        win = main_window
        _in_dark(win)
        win.text_input.setPlainText(TEXT)
        first = _found(win, needle="o")
        second = _found(win, needle="u", opener="_open_replace_dialog")   # clears the first's
        for _ in range(3):
            mode = _switch(win, "cycle")
            assert _spans(win.text_input) == _fresh(win, TEXT, needle="u"), mode
        first.close()
        second.close()
