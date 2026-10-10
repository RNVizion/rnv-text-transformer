"""Replace works on the output, and what it writes joins the output's history.

RNV-RULINGS-2026-10-05, item 10. Ruled 2026-10-05: "Yes."

WHAT WAS THERE. With "Search in: Output" chosen, Replace and Replace All
were off and said why: the output is read only. That was RNV-FIND-TARGET
(2026-10-04), which wired the pair and left this question for a ruling,
because the main window keeps its own history of the output (Ctrl+Z and
Ctrl+Y step through it) and a Replace there would have to join it.

WHAT IS THERE NOW. Replace and Replace All work on the pane chosen. When
that pane is the output, the dialog says so (`output_edited`), and the
window does what it does after every writer of the output: the text joins
the history, the statistics are counted again, the status says what was
done. The output is still read only to typing.

WHAT THIS GUARD HOLDS.

1. Replace and Replace All write to the output when it is the pane chosen,
   and leave the input alone.
2. Each press is one step of the output's history: undo brings back the
   text as it was before that press, redo the text as the press left it.
3. A Replace made after an undo drops what was undone, as every writer's
   does.
4. The statistics count the output as Replace left it, and the window's
   status says a Replace was applied.
5. The dialog says so once for each write to the output, and never
   otherwise: not for a write to the input, not when nothing was found,
   not for a pattern that does not compile.
6. The output is still read only to typing.

Every test drives the main window's own opener, and the output is written
by the window's own transform, so its history starts as the app leaves it.
"""
from __future__ import annotations

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from core.text_statistics import TextStatistics
from ui.base_dialog import BaseDialog
from ui.find_replace_dialog import FindReplaceDialog

IN = ("one fox, two foxes, three oxen\n"
      "four more of them\n")
OUT = IN.upper()
MODE = "UPPERCASE"
#: The output with its first, its first two, and all of its "OX" replaced.
ONE = OUT.replace("OX", "__", 1)
TWO = OUT.replace("OX", "__", 2)
ALL = OUT.replace("OX", "__")


@pytest.fixture
def transformed(main_window):
    """The main window after one transform: an input, and the output the
    window itself wrote from it, which is the one state of its history."""
    win = main_window
    win.settings_manager.save_auto_transform(False)
    win.text_input.setPlainText(IN)
    win.auto_transform_timer.stop()
    win.mode_combo.setCurrentText(MODE)
    assert win.mode_combo.currentText() == MODE, "the transform this guard uses is gone"
    win._transform_text()
    assert win.output_text.toPlainText() == OUT
    assert (win._output_history, win._output_history_index) == ([OUT], 0)
    assert OUT.count("OX") == 3 and ONE != TWO != ALL
    yield win
    win.auto_transform_timer.stop()


def _replace_dialog(win, search_output: bool = True) -> FindReplaceDialog:
    before = {id(d) for d in win.findChildren(BaseDialog)}
    win._open_replace_dialog()
    QApplication.processEvents()
    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, len(new)
    dlg = new[0]
    if search_output:
        dlg.search_output_radio.click()
    dlg.find_input.setText("OX")
    dlg.replace_input.setText("__")
    return dlg


def _said(dlg) -> list:
    """Counts the times the dialog says it wrote to the output."""
    said = []
    dlg.output_edited.connect(lambda: said.append(1))
    return said


class TestReplaceWritesToTheOutput:

    def test_replace_all_replaces_every_match_in_the_output_and_leaves_the_input(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg._on_replace_all()
        assert win.output_text.toPlainText() == ALL, "Replace All did not write to the output"
        assert win.text_input.toPlainText() == IN, "Replace All edited the input with Output chosen"
        assert dlg.status_label.text() == "Replaced 3 occurrence(s)"
        dlg.close()

    def test_replace_replaces_the_match_shown_and_leaves_the_input(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg._on_find()
        assert dlg.replace_btn.isEnabled(), "a Find did not turn Replace on with Output chosen"
        dlg._on_replace()
        assert win.output_text.toPlainText() == ONE, "Replace did not replace the output's first match"
        assert win.text_input.toPlainText() == IN, "Replace edited the input with Output chosen"
        assert dlg.status_label.text() == "Replaced 1 occurrence"
        dlg.close()

    def test_the_output_is_still_read_only_to_typing(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg._on_replace_all()
        assert win.output_text.isReadOnly(), "the output was made editable to let Replace write to it"
        QTest.keyClicks(win.output_text, "typed")
        QApplication.processEvents()
        assert win.output_text.toPlainText() == ALL, "typing changed the output"
        dlg.close()


class TestWhatReplaceWritesJoinsTheOutputsHistory:

    def test_replace_all_is_one_step_and_undo_and_redo_cross_it(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg._on_replace_all()
        assert (win._output_history, win._output_history_index) == ([OUT, ALL], 1), \
            "the text Replace All left is not the newest state of the output's history"
        win._undo_output()
        assert win.output_text.toPlainText() == OUT, "undo did not bring back the output as it was before Replace All"
        win._redo_output()
        assert win.output_text.toPlainText() == ALL, "redo did not bring back the output as Replace All left it"
        dlg.close()

    def test_each_press_of_replace_is_a_step_of_its_own(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg._on_find()
        dlg._on_replace()
        dlg._on_replace()
        assert win.output_text.toPlainText() == TWO
        assert (win._output_history, win._output_history_index) == ([OUT, ONE, TWO], 2)
        win._undo_output()
        assert win.output_text.toPlainText() == ONE, "undo did not step back over one Replace"
        win._undo_output()
        assert win.output_text.toPlainText() == OUT
        dlg.close()

    def test_a_replace_after_an_undo_drops_what_was_undone(self, transformed):
        win = transformed
        win.mode_combo.setCurrentText("lowercase")
        assert win.mode_combo.currentText() == "lowercase"
        win._transform_text()
        assert win._output_history == [OUT, IN.lower()]
        win._undo_output()
        assert win.output_text.toPlainText() == OUT and win._output_history_index == 0
        dlg = _replace_dialog(win)
        dlg._on_replace_all()
        assert (win._output_history, win._output_history_index) == ([OUT, ALL], 1), \
            "a Replace after an undo kept the state that was undone"
        win._redo_output()
        assert win.output_text.toPlainText() == ALL, "there was something to redo after a new edit"
        dlg.close()

    def test_the_statistics_and_the_status_are_the_windows_own_for_a_writer(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        dlg.replace_input.setText("")                         # three matches of two characters go
        dlg._on_replace_all()
        left = win.output_text.toPlainText()
        assert left == OUT.replace("OX", "") and len(left) == len(OUT) - 6
        want = TextStatistics.format_comparison(TextStatistics.calculate(IN), TextStatistics.calculate(left))
        stale = TextStatistics.format_comparison(TextStatistics.calculate(IN), TextStatistics.calculate(OUT))
        assert want != stale, "this replace does not change the statistics: the test would pass with them left stale"
        assert win.stats_label.text() == want, "the statistics do not count the output as Replace left it"
        assert win.status_label.text() == "Replace applied to output"
        dlg.close()


class TestTheDialogSaysSoOnceForEachWriteToTheOutput:

    def test_once_for_a_replace_and_once_for_a_replace_all(self, transformed):
        dlg = _replace_dialog(transformed)
        said = _said(dlg)
        dlg._on_find()
        dlg._on_replace()
        assert len(said) == 1, f"Replace said it wrote to the output {len(said)} times"
        dlg._on_replace_all()
        assert len(said) == 2, f"Replace All said it wrote to the output {len(said) - 1} times"
        dlg.close()

    def test_never_for_a_write_to_the_input(self, transformed):
        win = transformed
        dlg = _replace_dialog(win, search_output=False)
        said = _said(dlg)
        dlg.find_input.setText("ox")
        dlg._on_find()
        dlg._on_replace()
        dlg._on_replace_all()
        win.auto_transform_timer.stop()
        assert win.text_input.toPlainText() == IN.replace("ox", "__"), "Replace did not work on the input"
        assert said == [], "a Replace in the input was reported as a write to the output"
        assert (win.output_text.toPlainText(), win._output_history, win._output_history_index) == (OUT, [OUT], 0), \
            "a Replace in the input touched the output or its history"
        dlg.close()

    def test_never_when_nothing_was_written(self, transformed):
        win = transformed
        dlg = _replace_dialog(win)
        said = _said(dlg)
        dlg.find_input.setText("no such text")
        dlg._on_replace_all()
        assert dlg.status_label.text() == "No matches found"
        dlg.regex_check.setChecked(True)
        dlg.find_input.setText("(")
        dlg._on_replace_all()
        assert dlg.status_label.text().startswith("Regex error")
        dlg._on_replace()
        assert dlg.status_label.text() == "No match selected"
        assert said == [] and (win._output_history, win._output_history_index) == ([OUT], 0)
        assert win.output_text.toPlainText() == OUT
        dlg.close()

    def test_find_alone_never_says_so(self, transformed):
        """Find has no Replace, and the window does not listen to it."""
        win = transformed
        before = {id(d) for d in win.findChildren(BaseDialog)}
        win._open_find_dialog()
        QApplication.processEvents()
        dlg = [d for d in win.findChildren(BaseDialog) if id(d) not in before][0]
        said = _said(dlg)
        dlg.search_output_radio.click()
        dlg.find_input.setText("OX")
        dlg._on_find()
        dlg._on_find_next()
        assert said == [] and win._output_history == [OUT]
        dlg.close()
