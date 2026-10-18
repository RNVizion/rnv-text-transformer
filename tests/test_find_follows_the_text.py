"""Find Next, and Replace, follow the text as it now is.

RNV-RULINGS-2026-10-05, item 11. Ruled 2026-10-05: "Yes fix."

WHAT WAS THERE. A Find recorded where its matches were, and Find Next
stepped through those positions until Find was pressed again. Once the text
had been typed in, or the output had been written again by a transform, the
positions were places in a text that was gone. Measured on 2026-10-05, on a
Find for "ox" in "one fox, two foxes, three oxen":

- five characters typed at the top, then Find Next: it selected "tw";
- the output written again by a transform, then Find Next: it selected a
  line break and the letter after it;
- five characters typed at the top, then Replace: it wrote the replacement
  over "on", the two characters that stood where the match had been.

WHAT IS THERE NOW. The dialog keeps the text its matches were found in.
When the pane no longer holds that text, Find Next runs the same search
again in the text as it is and goes to the first match at or after the
caret, coming round to the first after the last. Replace does the same and
replaces nothing on that press: it shows the match and says so, and the
next press replaces it.

WHAT THIS GUARD HOLDS.

1. After the text has changed, Find Next selects a match of the text as it
   is, the highlights are where the matches are, and the count is theirs.
   In the input after typing, and in the output after a transform.
2. The match it goes to is the first at or after the caret, and after the
   last match the first.
3. When no match is left it says so and selects nothing.
4. After the text has changed, Replace changes nothing on that press, shows
   the match and says so. Pressed again, it replaces that match and no
   other character.
5. With the text unchanged, Find Next steps as it always has, and does not
   search again. A theme switched, a caret moved or a highlight painted
   again is not a change; nor is a change that has been undone.
6. The search run again is Find's search text. Since RNV-RULINGS-2026-10-11,
   item 24 (a), it reads the options as they are: an option changed since
   the Find is a change, held in tests/test_find_and_replace_do_what_they_say.py.
7. What is forgotten with the matches is forgotten whole: choosing the
   other pane or changing the find text leaves no text held.
"""
from __future__ import annotations

import re

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ui.base_dialog import BaseDialog
from ui.find_replace_dialog import FindReplaceDialog

IN = ("one fox, two foxes, three oxen\n"
      "four more of them\n")
TYPED = "Now: "


def _spots(text: str, needle: str = "ox") -> list:
    """(start, end) of every case-blind match of `needle`."""
    low, out, at = text.lower(), [], 0
    while (at := low.find(needle.lower(), at)) != -1:
        out.append((at, at + len(needle)))
        at += 1
    return out


def _selection(edit) -> tuple:
    cursor = edit.textCursor()
    return cursor.selectionStart(), cursor.selectionEnd()


def _highlighted(edit) -> list:
    return sorted((s.cursor.selectionStart(), s.cursor.selectionEnd())
                  for s in edit.extraSelections() if s.cursor.hasSelection())


def _caret_to(edit, position: int) -> None:
    cursor = edit.textCursor()
    cursor.setPosition(position)
    edit.setTextCursor(cursor)


def _type_at(edit, position: int, text: str = TYPED) -> None:
    """Type `text` into the pane, as a user would, with the caret at `position`."""
    _caret_to(edit, position)
    QTest.keyClicks(edit, text)
    QApplication.processEvents()


def _opened(win, opener: str, needle: str = "ox") -> FindReplaceDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    new[0].find_input.setText(needle)
    return new[0]


def _counting_searches(monkeypatch) -> list:
    """Counts the searches Find's dialog runs from here on."""
    ran, scan = [], FindReplaceDialog._matches_in

    def counted(text, search_text, options):
        ran.append(1)
        return scan(text, search_text, options)
    monkeypatch.setattr(FindReplaceDialog, "_matches_in", staticmethod(counted))
    return ran


@pytest.fixture
def filled(main_window):
    """The main window with a text in the input, and auto-transform off."""
    win = main_window
    win.settings_manager.save_auto_transform(False)
    win.text_input.setPlainText(IN)
    win.auto_transform_timer.stop()
    assert _spots(IN) == [(5, 7), (14, 16), (26, 28)]
    yield win
    win.auto_transform_timer.stop()


class TestFindNextAfterTheTextHasChanged:

    def test_after_typing_it_selects_a_match_of_the_text_as_it_is(self, filled):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        assert dlg._current_matches == _spots(IN) and _selection(win.text_input) == (5, 7)
        _type_at(win.text_input, 0)
        now = win.text_input.toPlainText()
        assert now == TYPED + IN and _spots(now) == [(10, 12), (19, 21), (31, 33)]
        dlg._on_find_next()
        start, end = _selection(win.text_input)
        assert now[start:end] == "ox", (
            f"Find Next selected {now[start:end]!r} at {start}: a position the Find recorded, in a "
            f"text that has changed since")
        assert (start, end) == (10, 12), "it is not the first match at or after the caret"
        assert dlg._current_matches == _spots(now), "the positions kept are not the matches' in the text as it is"
        assert _highlighted(win.text_input) == _spots(now)
        assert dlg.status_label.text() == "Match 1 of 3"
        dlg._on_find_next()
        assert _selection(win.text_input) == (19, 21), "the next press did not step on from there"
        dlg.close()

    def test_after_a_transform_writes_the_output_again(self, filled):
        win = filled
        win.mode_combo.setCurrentText("UPPERCASE")
        win._transform_text()
        dlg = _opened(win, "_open_find_dialog")
        dlg.search_output_radio.click()
        dlg._on_find()
        assert dlg._current_matches == _spots(IN) and _highlighted(win.output_text) == _spots(IN)
        win.text_input.setPlainText("a box of rocks\n" + IN)
        win.auto_transform_timer.stop()
        win._transform_text()
        now = win.output_text.toPlainText()
        assert now == ("a box of rocks\n" + IN).upper() and len(_spots(now)) == 4
        assert _highlighted(win.output_text) == [], "the premise: the highlights went with the text they were on"
        dlg._on_find_next()
        start, end = _selection(win.output_text)
        assert now[start:end] == "OX" and (start, end) == _spots(now)[0], \
            f"Find Next selected {now[start:end]!r} in the output a transform wrote again"
        assert _highlighted(win.output_text) == _spots(now), "the highlights were not painted on the new text"
        assert dlg.status_label.text() == "Match 1 of 4"
        dlg.close()

    @pytest.mark.parametrize("caret,expected", [
        (0, 0),          # before every match: the first
        (10, 0),         # at the start of a match: that match
        (11, 1),         # inside one: the next
        (13, 1),
        (22, 2),
        (34, 0),         # after the last: round to the first
    ])
    def test_it_goes_to_the_first_match_at_or_after_the_caret(self, filled, caret, expected):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        _type_at(win.text_input, 0)
        now = win.text_input.toPlainText()
        _caret_to(win.text_input, caret)
        dlg._on_find_next()
        assert _selection(win.text_input) == _spots(now)[expected], (caret, expected)
        assert dlg.status_label.text() == f"Match {expected + 1} of 3"
        dlg.close()

    def test_when_no_match_is_left_it_says_so_and_selects_nothing(self, filled):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        win.text_input.setPlainText("nothing here to find\n")
        win.auto_transform_timer.stop()
        dlg._on_find_next()
        assert dlg.status_label.text() == "No matches found"
        assert dlg._current_matches == [] and dlg._current_match_index == -1
        assert not win.text_input.textCursor().hasSelection(), "a position from the old text was selected"
        assert _highlighted(win.text_input) == []
        dlg.close()


class TestReplaceAfterTheTextHasChanged:

    def test_the_first_press_changes_nothing_and_shows_the_match(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.replace_input.setText("OX")
        dlg._on_find()
        _type_at(win.text_input, 0)
        now = win.text_input.toPlainText()
        dlg._on_replace()
        assert win.text_input.toPlainText() == now, (
            f"Replace wrote at a position the Find recorded, in a text that has changed since: "
            f"{win.text_input.toPlainText()[:16]!r}")
        assert _selection(win.text_input) == (10, 12), "the match it would replace is not the one shown"
        assert dlg.status_label.text() == FindReplaceDialog._TEXT_CHANGED_STATUS.format(1, 3)
        assert dlg.status_label.text() == "Text changed, nothing replaced: match 1 of 3"
        dlg.close()

    def test_the_next_press_replaces_that_match_and_no_other_character(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.replace_input.setText("OX")
        dlg._on_find()
        _type_at(win.text_input, 0)
        now = win.text_input.toPlainText()
        dlg._on_replace()
        dlg._on_replace()
        assert win.text_input.toPlainText() == now[:10] + "OX" + now[12:]
        assert dlg.status_label.text() == "Replaced 1 occurrence"
        dlg.close()

    def test_in_the_output_too_and_nothing_joins_its_history_until_something_is_replaced(self, filled):
        win = filled
        win.mode_combo.setCurrentText("UPPERCASE")
        win._transform_text()
        dlg = _opened(win, "_open_replace_dialog")
        dlg.search_output_radio.click()
        dlg.replace_input.setText("__")
        dlg._on_find()
        win.text_input.setPlainText("a box of rocks\n" + IN)
        win.auto_transform_timer.stop()
        win._transform_text()
        now = win.output_text.toPlainText()
        history = list(win._output_history)
        dlg._on_replace()
        assert win.output_text.toPlainText() == now and win._output_history == history
        assert _selection(win.output_text) == _spots(now)[0]
        assert dlg.status_label.text() == FindReplaceDialog._TEXT_CHANGED_STATUS.format(1, 4)
        dlg._on_replace()
        first = _spots(now)[0][0]
        assert win.output_text.toPlainText() == now[:first] + "__" + now[first + 2:]
        assert win._output_history == history + [win.output_text.toPlainText()]
        dlg.close()

    def test_when_no_match_is_left_replace_says_so_and_changes_nothing(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.replace_input.setText("OX")
        dlg._on_find()
        win.text_input.setPlainText("nothing here to find\n")
        win.auto_transform_timer.stop()
        dlg._on_replace()
        assert win.text_input.toPlainText() == "nothing here to find\n"
        assert dlg.status_label.text() == "No matches found"
        dlg.close()


class TestWithTheTextUnchangedNothingIsDifferent:

    def test_find_next_steps_through_the_matches_and_does_not_search_again(self, filled, monkeypatch):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        ran = _counting_searches(monkeypatch)
        seen = []
        for _ in range(4):
            dlg._on_find_next()
            seen.append(_selection(win.text_input))
        assert seen == [(14, 16), (26, 28), (5, 7), (14, 16)], "Find Next no longer steps and comes round"
        assert ran == [], f"Find Next searched again {len(ran)} times in a text that had not changed"
        dlg.close()

    def test_the_counter_above_counts(self, filled, monkeypatch):
        """Or the test above passes whatever Find Next does."""
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        ran = _counting_searches(monkeypatch)
        _type_at(win.text_input, 0)
        dlg._on_find_next()
        assert ran == [1]
        dlg.close()

    def test_a_switch_a_caret_moved_and_a_repaint_are_not_a_change(self, filled, monkeypatch):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        ran = _counting_searches(monkeypatch)
        win._cycle_theme()
        QApplication.processEvents()
        _caret_to(win.text_input, 40)
        dlg._recolor_highlights()
        assert not dlg._matches_are_stale()
        dlg._on_find_next()
        assert _selection(win.text_input) == (14, 16) and ran == [], \
            "Find Next took a switch, a caret or a repaint for a change of the text"
        dlg.close()

    def test_a_change_that_was_undone_is_not_a_change(self, filled, monkeypatch):
        win = filled
        dlg = _opened(win, "_open_find_dialog")
        dlg._on_find()
        ran = _counting_searches(monkeypatch)
        _type_at(win.text_input, 0, "x")
        assert dlg._matches_are_stale()
        win.text_input.undo()
        assert win.text_input.toPlainText() == IN and not dlg._matches_are_stale()
        dlg._on_find_next()
        assert _selection(win.text_input) == (14, 16) and ran == []
        dlg.close()

    def test_replace_with_the_text_unchanged_replaces_at_once(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        dlg.replace_input.setText("OX")
        dlg._on_find()
        dlg._on_replace()
        assert win.text_input.toPlainText() == IN[:5] + "OX" + IN[7:]
        assert dlg.status_label.text() == "Replaced 1 occurrence"
        dlg.close()


class TestWhatIsForgottenIsForgottenWhole:

    def test_the_text_is_held_only_while_the_matches_are(self, filled):
        win = filled
        dlg = _opened(win, "_open_replace_dialog")
        assert dlg._found_in is None and dlg._found_for is None
        dlg._on_find()
        assert dlg._found_in == IN and dlg._found_for[0] == "ox"
        dlg.find_input.setText("oxe")
        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a new find text"
        dlg._on_find()
        dlg.search_output_radio.click()
        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "the other pane"
        dlg.search_input_radio.click()
        dlg._on_find()
        dlg.replace_input.setText("-")
        dlg._on_replace_all()
        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a Replace All"
        dlg.find_input.setText("no such text")
        dlg._on_find()
        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a Find with no match"
        dlg.close()

    def test_the_scan_is_the_one_find_has_always_run(self):
        """The four ways it searches, on one text."""
        text = "Ox ox OX box.\nox-cart (ox)"
        scan = FindReplaceDialog._matches_in
        blind = {"case_sensitive": False, "whole_word": False, "regex": False}
        assert scan(text, "ox", blind) == [(0, 2), (3, 5), (6, 8), (10, 12), (14, 16), (23, 25)]
        assert scan(text, "ox", {**blind, "case_sensitive": True}) == [(3, 5), (10, 12), (14, 16), (23, 25)]
        assert scan(text, "ox", {**blind, "whole_word": True}) == [(0, 2), (3, 5), (6, 8), (14, 16), (23, 25)]
        assert scan(text, r"\(o(x)\)", {**blind, "regex": True}) == [(22, 26)]
        assert scan("aaaa", "aa", blind) == [(0, 2), (1, 3), (2, 4)], "matches that overlap are each found"
        with pytest.raises(re.error):
            scan(text, "(", {**blind, "regex": True})
