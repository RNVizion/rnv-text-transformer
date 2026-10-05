"""
tests/test_find_searches_the_pane_chosen.py
===========================================
RNV-FIND-TARGET, 2026-10-04. Find's "Search in: Input / Output" pair chooses
the pane Find works on.

The pair was there and nothing was connected to it. Find, Find Next, Replace
and Replace All acted on the input whichever was chosen: with Output chosen,
a Find painted its matches into the input, and Replace All rewrote the input.

Now the main window hands the dialog both panes and the pair chooses:

- a Find paints its matches in the pane chosen, and nowhere else;
- choosing the other pane takes the highlights down from the one searched
  and forgets its matches, as a change of the find text does;
- the output is read only, so it is searched and not replaced: with Output
  chosen Replace and Replace All are off, and say why;
- a theme switch and a close act on the pane searched.

Every test drives the main window's own openers.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QTextEdit

from ui.base_dialog import BaseDialog
from ui.find_replace_dialog import FindReplaceDialog

IN = ("The quick brown fox jumps over the lazy dog.\n"
      "Pack my box with five dozen liquor jugs.\n")
OUT = ("ONE GOOD BOOK\n"
       "TWO MORE\n")
OPENERS = ("_open_find_dialog", "_open_replace_dialog")


def _spots(text: str, needle: str = "o") -> list:
    """Where a case-blind Find for `needle` finds it: (position, length)."""
    low, out, at = text.lower(), [], 0
    while (at := low.find(needle, at)) != -1:
        out.append((at, len(needle)))
        at += 1
    return out


def _highlighted(edit) -> list:
    """(position, length) of every highlight shown over the text."""
    return sorted((s.cursor.selectionStart(), s.cursor.selectionEnd() - s.cursor.selectionStart())
                  for s in edit.extraSelections() if s.cursor.hasSelection())


def _colours(edit) -> set:
    return {s.format.background().color().name() for s in edit.extraSelections()
            if s.cursor.hasSelection()}


def _opened(win, opener: str) -> FindReplaceDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    return new[0]


def _find(dlg, needle: str = "o") -> None:
    dlg.find_input.setText(needle)
    dlg._on_find()
    QApplication.processEvents()


def _in_dark(win) -> None:
    for _ in range(3):
        if win.theme_manager.current_theme == "dark":
            return
        win._cycle_theme()
    assert win.theme_manager.current_theme == "dark"


@pytest.fixture
def filled(main_window):
    """The main window with a text in each pane, the two unlike each other."""
    win = main_window
    win.settings_manager.save_auto_transform(False)
    win.text_input.setPlainText(IN)
    win.auto_transform_timer.stop()
    win.output_text.setPlainText(OUT)
    assert _spots(IN) and _spots(OUT) and _spots(IN) != _spots(OUT)
    yield win
    win.auto_transform_timer.stop()


class TestTheOpenersHandFindBothPanes:

    @pytest.mark.parametrize("opener", OPENERS)
    def test_the_dialog_is_handed_the_input_and_the_output(self, filled, opener):
        win = filled
        dlg = _opened(win, opener)
        assert dlg._input_text_edit is win.text_input
        assert dlg._output_text_edit is win.output_text
        assert dlg.search_input_radio.isChecked() and dlg.target_text_edit is win.text_input, \
            "Find no longer opens on the input"
        dlg.close()

    def test_the_find_the_regex_builder_opens_is_handed_both_too(self, filled):
        win = filled
        before = {id(d) for d in win.findChildren(FindReplaceDialog)}
        win._on_regex_pattern_applied("o", "", 0)
        QApplication.processEvents()
        new = [d for d in win.findChildren(FindReplaceDialog) if id(d) not in before]
        assert len(new) == 1
        assert new[0]._input_text_edit is win.text_input and new[0]._output_text_edit is win.output_text
        new[0].close()


class TestThePairChoosesThePaneSearched:

    @pytest.mark.parametrize("opener", OPENERS)
    def test_with_output_chosen_a_find_searches_the_output(self, filled, opener):
        win = filled
        dlg = _opened(win, opener)
        dlg.search_output_radio.click()
        _find(dlg)
        assert dlg.target_text_edit is win.output_text
        assert _highlighted(win.output_text) == _spots(OUT), "the Find did not paint the output's matches"
        assert _highlighted(win.text_input) == [], "the Find painted the input with Output chosen"
        assert dlg._current_matches == [(at, at + n) for at, n in _spots(OUT)]
        assert dlg.status_label.text() == f"Found {len(_spots(OUT))} match(es)"
        dlg.close()

    @pytest.mark.parametrize("opener", OPENERS)
    def test_with_input_chosen_a_find_searches_the_input_as_it_always_has(self, filled, opener):
        win = filled
        dlg = _opened(win, opener)
        _find(dlg)
        assert _highlighted(win.text_input) == _spots(IN)
        assert _highlighted(win.output_text) == []
        dlg.close()

    def test_find_next_steps_through_the_pane_chosen(self, filled):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg.search_output_radio.click()
        _find(dlg)
        before = win.text_input.textCursor().position(), win.text_input.textCursor().selectedText()
        seen = []
        for _ in _spots(OUT):
            cursor = win.output_text.textCursor()
            seen.append((cursor.selectionStart(), cursor.selectionEnd() - cursor.selectionStart()))
            dlg._on_find_next()
        assert seen == _spots(OUT), "Find Next did not select the output's matches in turn"
        assert (win.text_input.textCursor().position(), win.text_input.textCursor().selectedText()) == before, \
            "Find Next moved the input's caret while the output was searched"
        dlg.close()

    def test_choosing_the_other_pane_takes_the_highlights_down_and_forgets_the_matches(self, filled):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        _find(dlg)
        assert _highlighted(win.text_input) and dlg.find_next_btn.isEnabled()
        dlg.search_output_radio.click()
        assert _highlighted(win.text_input) == [], "the input kept the highlights of a search that has moved on"
        assert dlg._current_matches == [] and dlg._current_match_index == -1
        assert not dlg.find_next_btn.isEnabled() and dlg.status_label.text() == ""
        assert _highlighted(win.output_text) == [], "choosing a pane ran a Find nobody asked for"
        _find(dlg)
        assert _highlighted(win.output_text) == _spots(OUT)
        dlg.search_input_radio.click()
        assert _highlighted(win.output_text) == [], "the output kept the highlights of a search that has moved on"
        assert dlg.target_text_edit is win.text_input
        _find(dlg)
        assert _highlighted(win.text_input) == _spots(IN) and _highlighted(win.output_text) == []
        dlg.close()

    def test_choosing_the_pane_already_searched_leaves_the_search_alone(self, filled):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        _find(dlg)
        dlg.search_input_radio.click()
        assert _highlighted(win.text_input) == _spots(IN) and dlg.find_next_btn.isEnabled()
        dlg.close()

    def test_the_text_is_not_edited_by_choosing_a_pane(self, filled):
        win = filled
        steps = (win.text_input.document().availableUndoSteps(),
                 win.output_text.document().availableUndoSteps())
        fired = []
        win.text_input.textChanged.connect(lambda: fired.append("input"))
        win.output_text.textChanged.connect(lambda: fired.append("output"))
        dlg = _opened(win, "_open_find_dialog")
        _find(dlg)
        dlg.search_output_radio.click()
        _find(dlg)
        dlg.search_input_radio.click()
        dlg.close()
        assert fired == [], f"choosing a pane fired textChanged: {fired}"
        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT)
        assert steps == (win.text_input.document().availableUndoSteps(),
                         win.output_text.document().availableUndoSteps())


class TestTheOutputIsSearchedNotReplaced:

    def test_the_premise_the_output_is_read_only_and_the_input_is_not(self, filled):
        assert filled.output_text.isReadOnly() and not filled.text_input.isReadOnly()

    def test_with_output_chosen_replace_and_replace_all_are_off_and_say_why(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        assert dlg.replace_all_btn.isEnabled(), "Replace All is off on the input"
        dlg.search_output_radio.click()
        assert not dlg.replace_all_btn.isEnabled() and not dlg.replace_btn.isEnabled()
        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS
        _find(dlg)
        assert _highlighted(win.output_text) == _spots(OUT), "the output is not searched in Find and Replace"
        assert not dlg.replace_btn.isEnabled(), "a Find turned Replace on for a pane that is read only"
        assert not dlg.replace_all_btn.isEnabled()
        dlg.close()

    def test_asked_all_the_same_they_leave_both_texts_alone(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.search_output_radio.click()
        _find(dlg)
        dlg.replace_input.setText("0")
        dlg._on_replace()
        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \
            "Replace edited a text with Output chosen"
        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS
        dlg.status_label.setText("")
        dlg._on_replace_all()
        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \
            "Replace All edited a text with Output chosen"
        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS
        dlg.close()

    def test_back_on_the_input_replace_works_as_it_always_has(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.search_output_radio.click()
        dlg.search_input_radio.click()
        assert dlg.replace_all_btn.isEnabled() and dlg.status_label.text() == ""
        _find(dlg)
        assert dlg.replace_btn.isEnabled()
        dlg.replace_input.setText("0")
        dlg._on_replace_all()
        assert win.text_input.toPlainText() == IN.replace("o", "0")
        assert win.output_text.toPlainText() == OUT
        dlg.close()

    def test_find_alone_has_no_replace_to_turn_off(self, filled):
        dlg = _opened(filled, "_open_find_dialog")
        dlg.search_output_radio.click()
        assert dlg.replace_btn is None and dlg.replace_all_btn is None
        assert dlg.status_label.text() == ""
        dlg.close()


class TestASwitchAndACloseActOnThePaneSearched:

    def test_a_switch_repaints_the_output_s_highlights(self, filled):
        win = filled
        _in_dark(win)
        dlg = _opened(win, "_open_find_dialog")
        dlg.search_output_radio.click()
        _find(dlg)
        dark = _colours(win.output_text)
        win._cycle_theme()
        QApplication.processEvents()
        assert win.theme_manager.current_theme == "light"
        light = _colours(win.output_text)
        assert len(dark) == len(light) == 1 and dark != light, (dark, light)
        assert _highlighted(win.output_text) == _spots(OUT)
        assert _highlighted(win.text_input) == []
        dlg.close()

    @pytest.mark.parametrize("how", ["button", "window"])
    def test_closing_find_takes_the_output_s_highlights_down(self, filled, how):
        """By the Close button, and by the window's own close."""
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg.search_output_radio.click()
        _find(dlg)
        assert _highlighted(win.output_text)
        dlg._on_close() if how == "button" else dlg.close()
        QApplication.processEvents()
        assert _highlighted(win.output_text) == []


class TestTheApiThatSetsAPane:
    """set_target_text_edit() is not called by the app; tests/ drive the
    dialog through it, and it has to agree with the pair."""

    def test_a_pane_set_as_the_output_is_what_the_output_button_comes_back_to(self, qtbot, theme_manager_dark):
        first, second = QTextEdit(), QTextEdit()
        first.setPlainText(IN)
        second.setPlainText(OUT)
        dlg = FindReplaceDialog(theme_manager_dark, target_text_edit=first)
        qtbot.addWidget(dlg)
        _find(dlg)
        assert _highlighted(first) == _spots(IN)
        dlg.set_target_text_edit(second, is_output=True)
        assert dlg.search_output_radio.isChecked() and dlg.target_text_edit is second
        assert _highlighted(first) == [], "the pane left behind kept its highlights"
        _find(dlg)
        assert _highlighted(second) == _spots(OUT)
        dlg.search_input_radio.click()
        assert dlg.target_text_edit is first and _highlighted(second) == []
        dlg.search_output_radio.click()
        assert dlg.target_text_edit is second

    def test_with_no_output_handed_in_choosing_it_searches_nothing(self, qtbot, theme_manager_dark):
        only = QTextEdit()
        only.setPlainText(IN)
        dlg = FindReplaceDialog(theme_manager_dark, target_text_edit=only)
        qtbot.addWidget(dlg)
        dlg.search_output_radio.click()
        _find(dlg)
        assert dlg.target_text_edit is None and dlg.status_label.text() == "No text area selected"
        assert _highlighted(only) == []
