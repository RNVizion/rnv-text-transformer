"""Find's Search in: Input / Output pair chooses the pane searched, for rnv-text-transformer

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (d101615 with up_tt_extra_selections.py applied).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-04: "This should be wired properly."

Find's dialog has a "Search in: Input / Output" pair that nothing was
connected to. Find, Find Next, Replace and Replace All acted on the input
whichever was chosen: with Output chosen a Find painted its matches into the
input, and Replace All rewrote the input.

The main window now hands the dialog both panes, and the pair chooses the one
Find works on. Choosing the other pane takes the highlights down from the
one searched and forgets its matches, as a change of the find text does; the
next Find runs in the new pane. A theme switch and a close act on the pane
searched.

The output is read only, so it is searched and not replaced: with Output
chosen Replace and Replace All are off, and the status line says why. The
pane's own read-only flag is asked, not its name.

Built on up_tt_extra_selections.py, whose text this round's anchors are;
this refuses, saying so, where that has not been run. Rendered before
building: probes/find_target_render.png.
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
SENTINEL = 'RNV-FIND-TARGET'
SENTINEL_FILE = 'ui/find_replace_dialog.py'
GUARD = 'tests/test_find_searches_the_pane_chosen.py'
GUARD_FILES = ['tests/test_find_searches_the_pane_chosen.py', 'tests/test_find_replace_dialog.py', 'tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py', 'tests/test_caret_stays_put.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_find_searches_the_pane_chosen.py', 'tests/test_find_replace_dialog.py', 'tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py', 'tests/test_caret_stays_put.py']
DESCRIPTION = "Find's Search in: Input / Output pair chooses the pane searched, for rnv-text-transformer"

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

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "base_dialog.py", "find_replace_dialog.py", "main_window.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ['Replace on the output: off, because the pane is read only. Whether Replace should edit the output is a ruling of its own; the app keeps its own history of the output, which a replace there would have to join.', 'the selection in the pane left behind: the match found stays selected, as it does when Find closes (RNV-CARET-STAYS).', 'which pane Find opens on: the input, as before.', 'Find Next after the text has changed: it steps through the positions the Find recorded. Found on the way, in both panes; not changed here.', "the Find and Replace dialog's buttons: at 450 wide, Find Next, Replace and Replace All are narrower than their labels. Found on the way; not changed here.", 'the three signals the dialog declares and never emits, and get_search_options().']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # This round builds on up_tt_extra_selections.py: its anchors are that round's text.
    # Without it they would all be "missing", which says the wrong thing.
    if 'RNV-EXTRA-SELECTIONS' not in tree.read('ui/find_replace_dialog.py'):
        raise Stop("this round builds on up_tt_extra_selections.py, which has not been applied here: ui/find_replace_dialog.py has no 'RNV-EXTRA-SELECTIONS'.\nRun that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tree.sub('ui/find_replace_dialog.py',
             '    _MODAL: ClassVar[bool] = False\n    \n    # Highlight colors — sourced from DialogStyleManager (no hardcoded hex)\n',
             '    _MODAL: ClassVar[bool] = False\n    # RNV-FIND-TARGET 2026-10-04: said when Replace is asked of a pane that\n    # cannot be edited. The output is read only: it is searched, not replaced.\n    _READ_ONLY_STATUS: ClassVar[str] = "The output is read-only: Replace is unavailable"\n    \n    # Highlight colors — sourced from DialogStyleManager (no hardcoded hex)\n')
    tree.sub('ui/find_replace_dialog.py',
             "        '_is_replace_mode', '_painted_highlight'\n    )\n",
             "        '_is_replace_mode', '_painted_highlight',\n        '_input_text_edit', '_output_text_edit'\n    )\n")
    tree.sub('ui/find_replace_dialog.py',
             '        replace_mode: bool = False,\n        parent: QWidget | None = None\n    ) -> None:\n        """\n        Initialize Find/Replace dialog.\n        \n        Args:\n            theme_manager: Theme manager instance\n            font_family: Font family to use\n            target_text_edit: Text edit widget to search in\n            replace_mode: If True, show replace options\n            parent: Parent widget\n        """\n',
             '        replace_mode: bool = False,\n        parent: QWidget | None = None,\n        output_text_edit: QTextEdit | None = None\n    ) -> None:\n        """\n        Initialize Find/Replace dialog.\n        \n        Args:\n            theme_manager: Theme manager instance\n            font_family: Font family to use\n            target_text_edit: Text edit widget to search in: the input\n            replace_mode: If True, show replace options\n            parent: Parent widget\n            output_text_edit: The output\'s text edit, searched when\n                "Search in: Output" is chosen\n        """\n')
    tree.sub('ui/find_replace_dialog.py',
             '        self.target_text_edit = target_text_edit\n        self._current_matches: list[tuple[int, int]] = []  # (start, end) positions\n',
             '        self.target_text_edit = target_text_edit\n        # RNV-FIND-TARGET 2026-10-04: the two panes "Search in:" chooses\n        # between. Nothing was connected to its buttons, so Find searched\n        # the input whichever was chosen.\n        self._input_text_edit = target_text_edit\n        self._output_text_edit = output_text_edit\n        self._current_matches: list[tuple[int, int]] = []  # (start, end) positions\n')
    tree.sub('ui/find_replace_dialog.py',
             '        self.search_group.addButton(self.search_input_radio, 0)\n        self.search_group.addButton(self.search_output_radio, 1)\n',
             "        self.search_group.addButton(self.search_input_radio, 0)\n        self.search_group.addButton(self.search_output_radio, 1)\n        # RNV-FIND-TARGET 2026-10-04: the pair chooses the pane searched.\n        # One signal says both: the output's button going on, or off.\n        self.search_output_radio.toggled.connect(self._on_search_area_changed)\n")
    tree.sub('ui/find_replace_dialog.py',
             '        close_btn = self._create_action_button("Close", self._on_close)\n        buttons_layout.addWidget(close_btn)\n        \n        layout.addLayout(buttons_layout)\n',
             '        close_btn = self._create_action_button("Close", self._on_close)\n        buttons_layout.addWidget(close_btn)\n        \n        layout.addLayout(buttons_layout)\n        self._sync_replace_buttons()\n')
    tree.sub('ui/find_replace_dialog.py',
             '        Set the target text edit widget to search in.\n        \n        Args:\n            text_edit: QTextEdit widget\n            is_output: If True, select output radio button\n        """\n        self.target_text_edit = text_edit\n        if is_output:\n            self.search_output_radio.setChecked(True)\n        else:\n            self.search_input_radio.setChecked(True)\n',
             '        Set the target text edit widget to search in.\n        \n        RNV-FIND-TARGET 2026-10-04: the widget becomes the pane its button\n        stands for, so choosing that button again comes back to it.\n        \n        Args:\n            text_edit: QTextEdit widget\n            is_output: If True, select output radio button\n        """\n        if is_output:\n            self._output_text_edit = text_edit\n            self.search_output_radio.setChecked(True)\n        else:\n            self._input_text_edit = text_edit\n            self.search_input_radio.setChecked(True)\n        self._search_in(text_edit)\n    \n    def _on_search_area_changed(self, search_output: bool) -> None:\n        """\n        Search the pane "Search in:" now names.\n        \n        RNV-FIND-TARGET 2026-10-04: nothing was connected to the two\n        buttons, so Find, Find Next, Replace and Replace All acted on the\n        input whichever was chosen.\n        """\n        self._search_in(self._output_text_edit if search_output else self._input_text_edit)\n    \n    def _search_in(self, text_edit: QTextEdit | None) -> None:\n        """\n        Make `text_edit` the text this dialog works on.\n        \n        RNV-FIND-TARGET 2026-10-04. The search that was showing belongs to\n        the pane it was run in: its highlights come down and its matches\n        are forgotten, as when the find text changes. The next Find runs\n        in the new pane.\n        """\n        if text_edit is self.target_text_edit:\n            return\n        self._on_find_text_changed(self.find_input.text())\n        self.target_text_edit = text_edit\n        self._sync_replace_buttons()\n    \n    def _target_is_read_only(self) -> bool:\n        """\n        Whether the pane searched cannot be edited, as the output cannot.\n        \n        RNV-FIND-TARGET 2026-10-04: Replace edits the text, so it is\n        offered only where the text can be edited. A cursor of the\n        document\'s own writes to a read-only pane all the same, so the\n        pane\'s own flag is asked.\n        """\n        return self.target_text_edit is not None and self.target_text_edit.isReadOnly()\n    \n    def _sync_replace_buttons(self) -> None:\n        """Offer Replace and Replace All only where the text can be edited."""\n        if not self._is_replace_mode:\n            return\n        read_only = self._target_is_read_only()\n        self.replace_all_btn.setEnabled(not read_only)\n        if read_only:\n            self.replace_btn.setEnabled(False)\n            self.status_label.setText(self._READ_ONLY_STATUS)\n')
    tree.sub('ui/find_replace_dialog.py',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        replace_text = self.replace_input.text()\n        start, end = self._current_matches[self._current_match_index]\n',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        # RNV-FIND-TARGET 2026-10-04: a read-only pane is searched, not edited.\n        if self._target_is_read_only():\n            self.status_label.setText(self._READ_ONLY_STATUS)\n            return\n        \n        replace_text = self.replace_input.text()\n        start, end = self._current_matches[self._current_match_index]\n')
    tree.sub('ui/find_replace_dialog.py',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        replace_text = self.replace_input.text()\n        options = self.get_search_options()\n',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        # RNV-FIND-TARGET 2026-10-04: a read-only pane is searched, not edited.\n        if self._target_is_read_only():\n            self.status_label.setText(self._READ_ONLY_STATUS)\n            return\n        \n        replace_text = self.replace_input.text()\n        options = self.get_search_options()\n')
    tree.sub('ui/find_replace_dialog.py',
             '                self.find_next_btn.setEnabled(True)\n                if self.replace_btn:\n                    self.replace_btn.setEnabled(True)\n',
             '                self.find_next_btn.setEnabled(True)\n                if self.replace_btn:\n                    # RNV-FIND-TARGET 2026-10-04: not on a read-only pane.\n                    self.replace_btn.setEnabled(not self._target_is_read_only())\n')
    tree.sub('ui/main_window.py',
             '            target_text_edit=self.text_input,\n            replace_mode=False,\n            parent=self\n        )\n        self._track_open_dialog(dialog)\n',
             '            target_text_edit=self.text_input,\n            replace_mode=False,\n            parent=self,\n            output_text_edit=self.output_text\n        )\n        self._track_open_dialog(dialog)\n')
    tree.sub('ui/main_window.py',
             '            target_text_edit=self.text_input,\n            replace_mode=True,\n            parent=self\n        )\n',
             '            target_text_edit=self.text_input,\n            replace_mode=True,\n            parent=self,\n            output_text_edit=self.output_text\n        )\n')
    tree.sub('ui/main_window.py',
             '                target_text_edit=self.text_input,\n                replace_mode=False,\n                parent=self\n            )\n',
             '                target_text_edit=self.text_input,\n                replace_mode=False,\n                parent=self,\n                output_text_edit=self.output_text\n            )\n')
    if (tree.root / 'tests/test_find_searches_the_pane_chosen.py').exists():
        raise Stop('tests/test_find_searches_the_pane_chosen.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_find_searches_the_pane_chosen.py', '"""\ntests/test_find_searches_the_pane_chosen.py\n===========================================\nRNV-FIND-TARGET, 2026-10-04. Find\'s "Search in: Input / Output" pair chooses\nthe pane Find works on.\n\nThe pair was there and nothing was connected to it. Find, Find Next, Replace\nand Replace All acted on the input whichever was chosen: with Output chosen,\na Find painted its matches into the input, and Replace All rewrote the input.\n\nNow the main window hands the dialog both panes and the pair chooses:\n\n- a Find paints its matches in the pane chosen, and nowhere else;\n- choosing the other pane takes the highlights down from the one searched\n  and forgets its matches, as a change of the find text does;\n- the output is read only, so it is searched and not replaced: with Output\n  chosen Replace and Replace All are off, and say why;\n- a theme switch and a close act on the pane searched.\n\nEvery test drives the main window\'s own openers.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication, QTextEdit\n\nfrom ui.base_dialog import BaseDialog\nfrom ui.find_replace_dialog import FindReplaceDialog\n\nIN = ("The quick brown fox jumps over the lazy dog.\\n"\n      "Pack my box with five dozen liquor jugs.\\n")\nOUT = ("ONE GOOD BOOK\\n"\n       "TWO MORE\\n")\nOPENERS = ("_open_find_dialog", "_open_replace_dialog")\n\n\ndef _spots(text: str, needle: str = "o") -> list:\n    """Where a case-blind Find for `needle` finds it: (position, length)."""\n    low, out, at = text.lower(), [], 0\n    while (at := low.find(needle, at)) != -1:\n        out.append((at, len(needle)))\n        at += 1\n    return out\n\n\ndef _highlighted(edit) -> list:\n    """(position, length) of every highlight shown over the text."""\n    return sorted((s.cursor.selectionStart(), s.cursor.selectionEnd() - s.cursor.selectionStart())\n                  for s in edit.extraSelections() if s.cursor.hasSelection())\n\n\ndef _colours(edit) -> set:\n    return {s.format.background().color().name() for s in edit.extraSelections()\n            if s.cursor.hasSelection()}\n\n\ndef _opened(win, opener: str) -> FindReplaceDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    return new[0]\n\n\ndef _find(dlg, needle: str = "o") -> None:\n    dlg.find_input.setText(needle)\n    dlg._on_find()\n    QApplication.processEvents()\n\n\ndef _in_dark(win) -> None:\n    for _ in range(3):\n        if win.theme_manager.current_theme == "dark":\n            return\n        win._cycle_theme()\n    assert win.theme_manager.current_theme == "dark"\n\n\n@pytest.fixture\ndef filled(main_window):\n    """The main window with a text in each pane, the two unlike each other."""\n    win = main_window\n    win.settings_manager.save_auto_transform(False)\n    win.text_input.setPlainText(IN)\n    win.auto_transform_timer.stop()\n    win.output_text.setPlainText(OUT)\n    assert _spots(IN) and _spots(OUT) and _spots(IN) != _spots(OUT)\n    yield win\n    win.auto_transform_timer.stop()\n\n\nclass TestTheOpenersHandFindBothPanes:\n\n    @pytest.mark.parametrize("opener", OPENERS)\n    def test_the_dialog_is_handed_the_input_and_the_output(self, filled, opener):\n        win = filled\n        dlg = _opened(win, opener)\n        assert dlg._input_text_edit is win.text_input\n        assert dlg._output_text_edit is win.output_text\n        assert dlg.search_input_radio.isChecked() and dlg.target_text_edit is win.text_input, \\\n            "Find no longer opens on the input"\n        dlg.close()\n\n    def test_the_find_the_regex_builder_opens_is_handed_both_too(self, filled):\n        win = filled\n        before = {id(d) for d in win.findChildren(FindReplaceDialog)}\n        win._on_regex_pattern_applied("o", "", 0)\n        QApplication.processEvents()\n        new = [d for d in win.findChildren(FindReplaceDialog) if id(d) not in before]\n        assert len(new) == 1\n        assert new[0]._input_text_edit is win.text_input and new[0]._output_text_edit is win.output_text\n        new[0].close()\n\n\nclass TestThePairChoosesThePaneSearched:\n\n    @pytest.mark.parametrize("opener", OPENERS)\n    def test_with_output_chosen_a_find_searches_the_output(self, filled, opener):\n        win = filled\n        dlg = _opened(win, opener)\n        dlg.search_output_radio.click()\n        _find(dlg)\n        assert dlg.target_text_edit is win.output_text\n        assert _highlighted(win.output_text) == _spots(OUT), "the Find did not paint the output\'s matches"\n        assert _highlighted(win.text_input) == [], "the Find painted the input with Output chosen"\n        assert dlg._current_matches == [(at, at + n) for at, n in _spots(OUT)]\n        assert dlg.status_label.text() == f"Found {len(_spots(OUT))} match(es)"\n        dlg.close()\n\n    @pytest.mark.parametrize("opener", OPENERS)\n    def test_with_input_chosen_a_find_searches_the_input_as_it_always_has(self, filled, opener):\n        win = filled\n        dlg = _opened(win, opener)\n        _find(dlg)\n        assert _highlighted(win.text_input) == _spots(IN)\n        assert _highlighted(win.output_text) == []\n        dlg.close()\n\n    def test_find_next_steps_through_the_pane_chosen(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        before = win.text_input.textCursor().position(), win.text_input.textCursor().selectedText()\n        seen = []\n        for _ in _spots(OUT):\n            cursor = win.output_text.textCursor()\n            seen.append((cursor.selectionStart(), cursor.selectionEnd() - cursor.selectionStart()))\n            dlg._on_find_next()\n        assert seen == _spots(OUT), "Find Next did not select the output\'s matches in turn"\n        assert (win.text_input.textCursor().position(), win.text_input.textCursor().selectedText()) == before, \\\n            "Find Next moved the input\'s caret while the output was searched"\n        dlg.close()\n\n    def test_choosing_the_other_pane_takes_the_highlights_down_and_forgets_the_matches(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        _find(dlg)\n        assert _highlighted(win.text_input) and dlg.find_next_btn.isEnabled()\n        dlg.search_output_radio.click()\n        assert _highlighted(win.text_input) == [], "the input kept the highlights of a search that has moved on"\n        assert dlg._current_matches == [] and dlg._current_match_index == -1\n        assert not dlg.find_next_btn.isEnabled() and dlg.status_label.text() == ""\n        assert _highlighted(win.output_text) == [], "choosing a pane ran a Find nobody asked for"\n        _find(dlg)\n        assert _highlighted(win.output_text) == _spots(OUT)\n        dlg.search_input_radio.click()\n        assert _highlighted(win.output_text) == [], "the output kept the highlights of a search that has moved on"\n        assert dlg.target_text_edit is win.text_input\n        _find(dlg)\n        assert _highlighted(win.text_input) == _spots(IN) and _highlighted(win.output_text) == []\n        dlg.close()\n\n    def test_choosing_the_pane_already_searched_leaves_the_search_alone(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        _find(dlg)\n        dlg.search_input_radio.click()\n        assert _highlighted(win.text_input) == _spots(IN) and dlg.find_next_btn.isEnabled()\n        dlg.close()\n\n    def test_the_text_is_not_edited_by_choosing_a_pane(self, filled):\n        win = filled\n        steps = (win.text_input.document().availableUndoSteps(),\n                 win.output_text.document().availableUndoSteps())\n        fired = []\n        win.text_input.textChanged.connect(lambda: fired.append("input"))\n        win.output_text.textChanged.connect(lambda: fired.append("output"))\n        dlg = _opened(win, "_open_find_dialog")\n        _find(dlg)\n        dlg.search_output_radio.click()\n        _find(dlg)\n        dlg.search_input_radio.click()\n        dlg.close()\n        assert fired == [], f"choosing a pane fired textChanged: {fired}"\n        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT)\n        assert steps == (win.text_input.document().availableUndoSteps(),\n                         win.output_text.document().availableUndoSteps())\n\n\nclass TestTheOutputIsSearchedNotReplaced:\n\n    def test_the_premise_the_output_is_read_only_and_the_input_is_not(self, filled):\n        assert filled.output_text.isReadOnly() and not filled.text_input.isReadOnly()\n\n    def test_with_output_chosen_replace_and_replace_all_are_off_and_say_why(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        assert dlg.replace_all_btn.isEnabled(), "Replace All is off on the input"\n        dlg.search_output_radio.click()\n        assert not dlg.replace_all_btn.isEnabled() and not dlg.replace_btn.isEnabled()\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        _find(dlg)\n        assert _highlighted(win.output_text) == _spots(OUT), "the output is not searched in Find and Replace"\n        assert not dlg.replace_btn.isEnabled(), "a Find turned Replace on for a pane that is read only"\n        assert not dlg.replace_all_btn.isEnabled()\n        dlg.close()\n\n    def test_asked_all_the_same_they_leave_both_texts_alone(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        dlg.replace_input.setText("0")\n        dlg._on_replace()\n        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \\\n            "Replace edited a text with Output chosen"\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        dlg.status_label.setText("")\n        dlg._on_replace_all()\n        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \\\n            "Replace All edited a text with Output chosen"\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        dlg.close()\n\n    def test_back_on_the_input_replace_works_as_it_always_has(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        dlg.search_input_radio.click()\n        assert dlg.replace_all_btn.isEnabled() and dlg.status_label.text() == ""\n        _find(dlg)\n        assert dlg.replace_btn.isEnabled()\n        dlg.replace_input.setText("0")\n        dlg._on_replace_all()\n        assert win.text_input.toPlainText() == IN.replace("o", "0")\n        assert win.output_text.toPlainText() == OUT\n        dlg.close()\n\n    def test_find_alone_has_no_replace_to_turn_off(self, filled):\n        dlg = _opened(filled, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        assert dlg.replace_btn is None and dlg.replace_all_btn is None\n        assert dlg.status_label.text() == ""\n        dlg.close()\n\n\nclass TestASwitchAndACloseActOnThePaneSearched:\n\n    def test_a_switch_repaints_the_output_s_highlights(self, filled):\n        win = filled\n        _in_dark(win)\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        dark = _colours(win.output_text)\n        win._cycle_theme()\n        QApplication.processEvents()\n        assert win.theme_manager.current_theme == "light"\n        light = _colours(win.output_text)\n        assert len(dark) == len(light) == 1 and dark != light, (dark, light)\n        assert _highlighted(win.output_text) == _spots(OUT)\n        assert _highlighted(win.text_input) == []\n        dlg.close()\n\n    @pytest.mark.parametrize("how", ["button", "window"])\n    def test_closing_find_takes_the_output_s_highlights_down(self, filled, how):\n        """By the Close button, and by the window\'s own close."""\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        assert _highlighted(win.output_text)\n        dlg._on_close() if how == "button" else dlg.close()\n        QApplication.processEvents()\n        assert _highlighted(win.output_text) == []\n\n\nclass TestTheApiThatSetsAPane:\n    """set_target_text_edit() is not called by the app; tests/ drive the\n    dialog through it, and it has to agree with the pair."""\n\n    def test_a_pane_set_as_the_output_is_what_the_output_button_comes_back_to(self, qtbot, theme_manager_dark):\n        first, second = QTextEdit(), QTextEdit()\n        first.setPlainText(IN)\n        second.setPlainText(OUT)\n        dlg = FindReplaceDialog(theme_manager_dark, target_text_edit=first)\n        qtbot.addWidget(dlg)\n        _find(dlg)\n        assert _highlighted(first) == _spots(IN)\n        dlg.set_target_text_edit(second, is_output=True)\n        assert dlg.search_output_radio.isChecked() and dlg.target_text_edit is second\n        assert _highlighted(first) == [], "the pane left behind kept its highlights"\n        _find(dlg)\n        assert _highlighted(second) == _spots(OUT)\n        dlg.search_input_radio.click()\n        assert dlg.target_text_edit is first and _highlighted(second) == []\n        dlg.search_output_radio.click()\n        assert dlg.target_text_edit is second\n\n    def test_with_no_output_handed_in_choosing_it_searches_nothing(self, qtbot, theme_manager_dark):\n        only = QTextEdit()\n        only.setPlainText(IN)\n        dlg = FindReplaceDialog(theme_manager_dark, target_text_edit=only)\n        qtbot.addWidget(dlg)\n        dlg.search_output_radio.click()\n        _find(dlg)\n        assert dlg.target_text_edit is None and dlg.status_label.text() == "No text area selected"\n        assert _highlighted(only) == []\n')


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
    FIND, MAIN = "ui/find_replace_dialog.py", "ui/main_window.py"

    def klass(src, name):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == name)
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}, c

    def outside(src, name):
        return [ast.dump(x) for x in ast.parse(src).body if not (isinstance(x, ast.ClassDef) and x.name == name)]

    def lines(fn):
        return [ast.unparse(s) for s in fn.body]

    def without(fn, drop):
        """The function with every statement `drop` says yes to taken out, at any depth."""
        fn = copy.deepcopy(fn)
        for node in ast.walk(fn):
            for field in ("body", "orelse", "finalbody"):
                stmts = getattr(node, field, None)
                if isinstance(stmts, list):
                    setattr(node, field, [s for s in stmts if not drop(s)])
        return fn

    def tests_in(src):
        return [n.name for c in ast.parse(src).body if isinstance(c, ast.ClassDef)
                for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]

    # ---- the dialog: four methods come, six move, none goes
    old_f, new_f = _original(tree, FIND), tree.read(FIND)
    (o, oc), (n, nc) = klass(old_f, "FindReplaceDialog"), klass(new_f, "FindReplaceDialog")
    assert set(o) - set(n) == set(), f"FindReplaceDialog lost {sorted(set(o) - set(n))}"
    assert set(n) - set(o) == {"_on_search_area_changed", "_search_in", "_target_is_read_only",
                               "_sync_replace_buttons"}, f"FindReplaceDialog gained {sorted(set(n) - set(o))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["__init__", "_on_replace", "_on_replace_all", "_perform_find", "_setup_ui",
                     "set_target_text_edit"], f"FindReplaceDialog: moved {moved}"
    assert outside(old_f, "FindReplaceDialog") == outside(new_f, "FindReplaceDialog"), \
        "find_replace_dialog.py moved beyond the class"
    rest = lambda c: {ast.unparse(s.targets[0] if isinstance(s, ast.Assign) else s.target): ast.dump(s)   # noqa: E731
                      for s in c.body if isinstance(s, (ast.Assign, ast.AnnAssign))}
    ro, rn = rest(oc), rest(nc)
    assert set(rn) - set(ro) == {"_READ_ONLY_STATUS"} and set(ro) <= set(rn), "the class's constants moved"
    assert sorted(k for k in ro if ro[k] != rn[k]) == ["__slots__"], "a class constant other than __slots__ moved"
    slots = lambda c: set(ast.literal_eval(next(s.value for s in c.body if isinstance(s, ast.Assign)   # noqa: E731
                                                 and getattr(s.targets[0], "id", None) == "__slots__")))
    assert slots(nc) - slots(oc) == {"_input_text_edit", "_output_text_edit"} and slots(oc) <= slots(nc), \
        "__slots__ moved beyond the two panes"

    # ---- the pair is connected, once, to the handler; the constructor keeps both panes
    setup = n["_setup_ui"]
    CONNECT = "self.search_output_radio.toggled.connect(self._on_search_area_changed)"
    SYNC = "self._sync_replace_buttons()"
    assert ast.unparse(setup).count(CONNECT) == 1, "the pair is not connected to the handler, once"
    assert ast.dump(without(setup, lambda s: ast.unparse(s) in (CONNECT, SYNC))) == ast.dump(o["_setup_ui"]), \
        "_setup_ui() changed beyond connecting the pair and setting Replace as the pane allows"
    assert lines(setup)[-1] == SYNC, "_setup_ui() does not end by setting Replace as the pane allows"
    init = n["__init__"]
    assert [a.arg for a in init.args.args] == [a.arg for a in o["__init__"].args.args] + ["output_text_edit"], \
        "__init__() takes something other than one new last argument, output_text_edit"
    assert ast.unparse(init.args.defaults[-1]) == "None", "output_text_edit is not optional"
    KEPT = ("self._input_text_edit = target_text_edit", "self._output_text_edit = output_text_edit")
    assert [s for s in lines(init) if s in KEPT] == list(KEPT), "__init__() does not keep the two panes"
    assert [ast.dump(s) for s in without(init, lambda s: ast.unparse(s) in KEPT).body[1:]] == \
        [ast.dump(s) for s in o["__init__"].body[1:]], "__init__() changed beyond keeping the two panes"
    at = lines(init)
    assert at.index(KEPT[1]) < at.index("self._setup_ui()"), "the panes are kept after the pair is connected"

    # ---- choosing a pane: the search that was showing is taken down first
    assert lines(n["_on_search_area_changed"])[1:] == [
        "self._search_in(self._output_text_edit if search_output else self._input_text_edit)"], \
        "the handler does not search the pane the pair names"
    assert lines(n["_search_in"])[1:] == [
        "if text_edit is self.target_text_edit:\n    return",
        "self._on_find_text_changed(self.find_input.text())",
        "self.target_text_edit = text_edit",
        "self._sync_replace_buttons()"], "_search_in() does not take the old search down before it moves on"
    reset = ast.unparse(o["_on_find_text_changed"])
    assert ast.dump(o["_on_find_text_changed"]) == ast.dump(n["_on_find_text_changed"]) \
        and "self._current_matches.clear()" in reset and "self._clear_highlights()" in reset \
        and "self.find_next_btn.setEnabled(False)" in reset and "self.status_label.setText('')" in reset, \
        "_on_find_text_changed() is no longer the reset _search_in() stands on"
    assert lines(n["set_target_text_edit"])[1:] == [
        "if is_output:\n    self._output_text_edit = text_edit\n    self.search_output_radio.setChecked(True)\n"
        "else:\n    self._input_text_edit = text_edit\n    self.search_input_radio.setChecked(True)",
        "self._search_in(text_edit)"], "set_target_text_edit() does not agree with the pair"

    # ---- Replace: offered, and done, only where the text can be edited
    assert lines(n["_target_is_read_only"])[1:] == [
        "return self.target_text_edit is not None and self.target_text_edit.isReadOnly()"], \
        "_target_is_read_only() does not ask the pane's own flag"
    assert lines(n["_sync_replace_buttons"])[1:] == [
        "if not self._is_replace_mode:\n    return",
        "read_only = self._target_is_read_only()",
        "self.replace_all_btn.setEnabled(not read_only)",
        "if read_only:\n    self.replace_btn.setEnabled(False)\n    self.status_label.setText(self._READ_ONLY_STATUS)"], \
        "_sync_replace_buttons() does not turn Replace off for a read-only pane, saying why"
    GUARDED = "if self._target_is_read_only():\n    self.status_label.setText(self._READ_ONLY_STATUS)\n    return"
    for name in ("_on_replace", "_on_replace_all"):
        new_lines = lines(n[name])
        assert new_lines.count(GUARDED) == 1, f"{name}() does not refuse a read-only pane"
        assert ast.dump(without(n[name], lambda s: ast.unparse(s) == GUARDED)) == ast.dump(o[name]), \
            f"{name}() changed beyond refusing a read-only pane"
        assert new_lines[new_lines.index(GUARDED) - 1] == \
            "if self.target_text_edit is None or self.replace_input is None:\n    return", \
            f"{name}() does not refuse a read-only pane before anything else is done"
    was = ast.unparse(o["_perform_find"]).replace(
        "self.replace_btn.setEnabled(True)", "self.replace_btn.setEnabled(not self._target_is_read_only())")
    assert was == ast.unparse(n["_perform_find"]) and was != ast.unparse(o["_perform_find"]), \
        "_perform_find() changed beyond turning Replace on only where the text can be edited"

    # ---- the main window: every Find it opens is handed both panes, and nothing else moves
    old_m, new_m = _original(tree, MAIN), tree.read(MAIN)
    (o, oc), (n, nc) = klass(old_m, "MainWindow"), klass(new_m, "MainWindow")
    assert set(o) == set(n), f"MainWindow: methods added or removed: {sorted(set(o) ^ set(n))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["_on_regex_pattern_applied", "_open_find_dialog", "_open_replace_dialog"], f"MainWindow: moved {moved}"
    assert outside(old_m, "MainWindow") == outside(new_m, "MainWindow"), "main_window.py moved beyond the class"
    opened = 0
    for p in sorted(tree.root.rglob("*.py")):
        rel = p.relative_to(tree.root).as_posix()
        if rel.startswith(("tests/", ".", "test_", "up")) or "/__pycache__/" in rel or rel == "conftest.py":
            continue
        text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
        for call in ast.walk(ast.parse(text)):
            if isinstance(call, ast.Call) and getattr(call.func, "id", getattr(call.func, "attr", None)) == "FindReplaceDialog":
                kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
                assert kw.get("target_text_edit") == "self.text_input" and kw.get("output_text_edit") == "self.output_text", \
                    f"{rel}: a Find is opened without both panes: {ast.unparse(call)[:120]}"
                opened += 1
    assert opened == 3, f"the app opens Find in {opened} places; three were derived"

    # ---- the premise: the pair was unconnected, and the output is the pane that is read only
    for node in ast.walk(ast.parse(old_f)):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "connect":
            assert "search_" not in ast.unparse(node.func), \
                f"the pair was connected already: {ast.unparse(node)[:100]} -- re-derive this round"
    assert "self.output_text.setReadOnly(True)" in new_m and "self.text_input.setReadOnly" not in new_m, \
        "the output is no longer the pane that is read only"
    assert "self.text_input = DragDropTextEdit()" in new_m and "self.output_text = DragDropTextEdit()" in new_m, \
        "a pane is no longer a DragDropTextEdit"
    assert "class DragDropTextEdit(QTextEdit):" in tree.read("ui/drag_drop_text_edit.py"), \
        "DragDropTextEdit is no longer a QTextEdit"

    # ---- the guard: new, marked, and the tests derived
    guard = tree.read(GUARD)
    assert tests_in(guard) == ['test_the_dialog_is_handed_the_input_and_the_output', 'test_the_find_the_regex_builder_opens_is_handed_both_too', 'test_with_output_chosen_a_find_searches_the_output', 'test_with_input_chosen_a_find_searches_the_input_as_it_always_has', 'test_find_next_steps_through_the_pane_chosen', 'test_choosing_the_other_pane_takes_the_highlights_down_and_forgets_the_matches', 'test_choosing_the_pane_already_searched_leaves_the_search_alone', 'test_the_text_is_not_edited_by_choosing_a_pane', 'test_the_premise_the_output_is_read_only_and_the_input_is_not', 'test_with_output_chosen_replace_and_replace_all_are_off_and_say_why', 'test_asked_all_the_same_they_leave_both_texts_alone', 'test_back_on_the_input_replace_works_as_it_always_has', 'test_find_alone_has_no_replace_to_turn_off', 'test_a_switch_repaints_the_output_s_highlights', 'test_closing_find_takes_the_output_s_highlights_down', 'test_a_pane_set_as_the_output_is_what_the_output_button_comes_back_to', 'test_with_no_output_handed_in_choosing_it_searches_nothing'], f"{GUARD}: its tests are {tests_in(guard)}"
    assert SENTINEL in guard and SENTINEL in new_f, "the sentinel is not in the dialog and its guard"
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
