"""Find and Replace do what their controls say.

RNV-RULINGS-2026-10-11, item 24. Ruled 2026-10-11: "Yes fix a to d remove e".

WHAT WAS THERE. Five things the dialog did as shipped, measured on
2026-10-05:

(a) An option ticked after a Find (Case sensitive, Whole word, Regular
    expression) was not read until Find was pressed again. Find Next went on
    stepping through the matches of the options as they had been.
(b) Replace All, with Regular expression off and Case sensitive off, which is
    the default, read the replacement as a regular expression's template: a
    backslash in it was an escape. C:\\new\\dir was refused as a bad escape.
(c) With Regular expression on, Replace wrote a group reference such as \\1
    as typed, and Replace All filled it in.
(d) A character outside the basic plane, an emoji, put every highlight after
    it one place to the left, and Replace wrote over the characters there.
    Python counts such a character as one position; the text pane, as two.
(e) The dialog declared three signals that nothing emitted or connected.

WHAT IS THERE NOW. (a) An option changed since the Find is a change, as an
edit is: Find Next runs Find's search again with the options as they are,
and Replace shows the match first and says so. (b) With Regular expression
off, the replacement is the text as typed. (c) Replace fills the groups in,
as Replace All does. (d) Positions are counted as the pane counts them.
(e) The three signals went.

WHAT THIS GUARD HOLDS. Each of the five, driven through the main window's
own Find and Replace. That the search is run again only when something has
changed is held in tests/test_find_follows_the_text.py.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ui.base_dialog import BaseDialog
from ui.find_replace_dialog import FindReplaceDialog

ROOT = pathlib.Path(__file__).resolve().parents[1]
EMOJI = "\U0001F600"


def _opened(win, opener: str, needle: str) -> FindReplaceDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    getattr(win, opener)()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    new[0].find_input.setText(needle)
    return new[0]


def _selected(edit) -> str:
    return edit.textCursor().selectedText()


def _highlighted(edit) -> list:
    return [s.cursor.selectedText() for s in edit.extraSelections() if s.cursor.hasSelection()]


def _counting_searches(monkeypatch) -> list:
    ran, scan = [], FindReplaceDialog._matches_in

    def counted(text, search_text, options):
        ran.append(1)
        return scan(text, search_text, options)
    monkeypatch.setattr(FindReplaceDialog, "_matches_in", staticmethod(counted))
    return ran


@pytest.fixture
def pane(main_window):
    """The main window, auto-transform off; a test puts its own text in the input."""
    win = main_window
    win.settings_manager.save_auto_transform(False)
    win.auto_transform_timer.stop()

    def holding(text: str):
        win.text_input.setPlainText(text)
        win.auto_transform_timer.stop()
        QApplication.processEvents()
        return win
    yield holding
    win.auto_transform_timer.stop()


class TestAnOptionChangedSinceTheFindIsAChange:
    """(a)"""

    def test_find_next_searches_again_with_the_options_as_they_are(self, pane):
        win = pane("Ox ox OX\n")
        dlg = _opened(win, "_open_find_dialog", "ox")
        dlg._on_find()
        assert dlg._current_matches == [(0, 2), (3, 5), (6, 8)]
        dlg.case_sensitive_check.setChecked(True)
        dlg._on_find_next()
        assert dlg._current_matches == [(3, 5)], \
            "Find Next stepped through the matches of the options as they were at the Find"
        assert _selected(win.text_input) == "ox" and _highlighted(win.text_input) == ["ox"]
        assert dlg.status_label.text() == "Match 1 of 1"
        dlg.close()

    def test_replace_shows_the_match_first_and_says_why(self, pane):
        win = pane("Ox ox OX\n")
        dlg = _opened(win, "_open_replace_dialog", "ox")
        dlg.replace_input.setText("no")
        dlg._on_find()
        dlg.case_sensitive_check.setChecked(True)
        dlg._on_replace()
        assert win.text_input.toPlainText() == "Ox ox OX\n", "Replace wrote on the press that found a change"
        assert dlg.status_label.text() == "Options changed, nothing replaced: match 1 of 1"
        assert _selected(win.text_input) == "ox"
        dlg._on_replace()
        assert win.text_input.toPlainText() == "Ox no OX\n"
        dlg.close()

    def test_an_option_ticked_and_unticked_again_is_no_change(self, pane, monkeypatch):
        win = pane("Ox ox OX\n")
        dlg = _opened(win, "_open_find_dialog", "ox")
        dlg._on_find()
        ran = _counting_searches(monkeypatch)
        dlg.whole_word_check.setChecked(True)
        dlg.whole_word_check.setChecked(False)
        dlg._on_find_next()
        assert ran == [] and dlg._current_match_index == 1, "an option put back as it was is no change"
        dlg.close()

    def test_a_find_text_that_becomes_a_bad_pattern_says_so(self, pane):
        win = pane("a(b) a(b)\n")
        dlg = _opened(win, "_open_find_dialog", "a(")
        dlg._on_find()
        assert len(dlg._current_matches) == 2
        dlg.regex_check.setChecked(True)
        dlg._on_find_next()
        assert dlg.status_label.text().startswith("Regex error"), dlg.status_label.text()
        assert dlg._current_matches == [] and _highlighted(win.text_input) == []
        dlg.close()


AS_TYPED = (r"C:\new\dir", r"one\ntwo", r"\1")
MODES = ((False, False, "the default"), (False, True, "whole word"), (True, False, "case sensitive"),
         (True, True, "case sensitive, whole word"))


class TestReplaceAllWritesTheReplacementAsTyped:
    """(b)"""

    def test_with_regular_expression_off(self, pane):
        """Every way of searching without a pattern, and three replacements
        a template would read otherwise: a bad escape, an escape it knows, and
        a group reference."""
        win = pane("")
        dlg = _opened(win, "_open_replace_dialog", "here")
        wrong = []
        for case, whole, called in MODES:
            dlg.case_sensitive_check.setChecked(case)
            dlg.whole_word_check.setChecked(whole)
            for replacement in AS_TYPED:
                pane("path here, and here\n")
                dlg.replace_input.setText(replacement)
                dlg._on_replace_all()
                got = win.text_input.toPlainText()
                if got != f"path {replacement}, and {replacement}\n" or dlg.status_label.text() != "Replaced 2 occurrence(s)":
                    wrong.append(f"{called}, {replacement!r}: {got!r} ({dlg.status_label.text()})")
        assert not wrong, "Replace All read the replacement as a pattern's template:\n  " + "\n  ".join(wrong)
        dlg.close()

    def test_replace_writes_it_as_typed_too(self, pane):
        win = pane("path here\n")
        dlg = _opened(win, "_open_replace_dialog", "here")
        dlg.replace_input.setText(r"C:\new\dir")
        dlg._on_find()
        dlg._on_replace()
        assert win.text_input.toPlainText() == "path C:\\new\\dir\n"
        dlg.close()


class TestReplaceFillsInTheGroupsAsReplaceAllDoes:
    """(c)"""

    def test_the_two_write_the_same(self, pane):
        win = pane("ab ab\n")
        dlg = _opened(win, "_open_replace_dialog", "(a)(b)")
        dlg.regex_check.setChecked(True)
        dlg.replace_input.setText(r"\2\1")
        dlg._on_find()
        dlg._on_replace()
        assert win.text_input.toPlainText() == "ba ab\n", \
            f"Replace wrote {win.text_input.toPlainText()!r}: the group references as typed"
        dlg._on_replace_all()
        assert win.text_input.toPlainText() == "ba ba\n"
        dlg.close()

    def test_a_group_the_pattern_does_not_have_is_refused_by_both(self, pane):
        win = pane("ab ab\n")
        dlg = _opened(win, "_open_replace_dialog", "(a)(b)")
        dlg.regex_check.setChecked(True)
        dlg.replace_input.setText(r"\3")
        dlg._on_find()
        dlg._on_replace()
        assert win.text_input.toPlainText() == "ab ab\n" and dlg.status_label.text().startswith("Regex error")
        dlg._on_replace_all()
        assert win.text_input.toPlainText() == "ab ab\n" and dlg.status_label.text().startswith("Regex error")
        dlg.close()


class TestAMatchAfterAnEmojiIsWhereItIs:
    """(d)"""

    TEXT = f"{EMOJI} fox, {EMOJI}{EMOJI} the fox\n"

    @pytest.mark.parametrize("regex", [False, True], ids=("text", "regular expression"))
    def test_find_and_find_next_select_the_match(self, pane, regex):
        win = pane(self.TEXT)
        dlg = _opened(win, "_open_find_dialog", "f.x" if regex else "fox")
        dlg.regex_check.setChecked(regex)
        dlg._on_find()
        assert _selected(win.text_input) == "fox", f"Find selected {_selected(win.text_input)!r}"
        assert _highlighted(win.text_input) == ["fox", "fox"], _highlighted(win.text_input)
        dlg._on_find_next()
        assert _selected(win.text_input) == "fox", f"Find Next selected {_selected(win.text_input)!r}"
        dlg.close()

    def test_replace_writes_over_the_match(self, pane):
        win = pane(self.TEXT)
        dlg = _opened(win, "_open_replace_dialog", "fox")
        dlg.replace_input.setText("cat")
        dlg._on_find()
        dlg._on_find_next()
        dlg._on_replace()
        assert win.text_input.toPlainText() == f"{EMOJI} fox, {EMOJI}{EMOJI} the cat\n", \
            repr(win.text_input.toPlainText())
        dlg.close()

    def test_after_typing_find_next_goes_to_the_next_match_after_the_caret(self, pane):
        """Typed right before the last match, after three emoji: the pane
        counts the caret three places further on than Python does, so a caret
        read as the pane counts it is past the match, and Find Next comes
        round to the first."""
        win = pane(self.TEXT)
        dlg = _opened(win, "_open_find_dialog", "fox")
        dlg._on_find()
        cursor = win.text_input.textCursor()
        cursor.setPosition(len(f"{EMOJI} fox, {EMOJI}{EMOJI} the ".encode("utf-16-le")) // 2)
        win.text_input.setTextCursor(cursor)
        QTest.keyClicks(win.text_input, "x")
        QApplication.processEvents()
        dlg._on_find_next()
        assert _selected(win.text_input) == "fox"
        assert dlg.status_label.text() == "Match 2 of 2", dlg.status_label.text()
        dlg.close()


class TestTheDialogDeclaresTheSignalsItUses:
    """(e)"""

    def test_each_signal_it_declares_it_emits(self):
        source = (ROOT / "ui" / "find_replace_dialog.py").read_text(encoding="utf-8-sig")
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "FindReplaceDialog")
        declared = [t.id for node in cls.body if isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "pyqtSignal"
                    for t in node.targets]
        assert declared == ["output_edited"], f"the dialog declares {declared}"
        for name in declared:
            assert re.search(rf"\.{name}\.emit\(", source), f"{name} is declared and never emitted"
        for gone in ("find_requested", "replace_requested", "replace_all_requested"):
            assert not hasattr(FindReplaceDialog, gone), f"{gone} is back"
