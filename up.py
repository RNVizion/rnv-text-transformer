"""the transformer's rulings of 5 October: Replace works on the output and joins its history, Find Next and Replace follow the text as it now is, the workflow's actions are at the versions built for Node 24, and the README's test counts cannot go stale

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (7d79df5).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-05, items 10, 11, 14 and 18 of the list of 4 October:

  10  "Yes."
  11  "Yes fix."
  14  "Yes do it."
  18  "Do B."

ITEM 10, REPLACE ON THE OUTPUT. With "Search in: Output" chosen, Replace
and Replace All were off, because the output is read only. They work there
now. The output is still read only to typing. The main window keeps a
history of the output (Ctrl+Z and Ctrl+Y step through it), and every writer
of the output joins it: so the dialog tells the window when it has written
to the output, and the window does what it does after every writer. The
text joins the history, the statistics are counted again, and the status
says "Replace applied to output". Each press is one step of that history.

ITEM 11, FIND NEXT AFTER THE TEXT HAS CHANGED. A Find recorded where its
matches were, and Find Next stepped through those positions until Find was
pressed again. Once the text had been typed in, or the output written again
by a transform, they were places in a text that was gone. Measured on the
live head, on a Find for "ox" in "one fox, two foxes, three oxen":
  five characters typed at the top, then Find Next: it selected "tw";
  the output written again by a transform, then Find Next: it selected a
  line break and the letter after it;
  five characters typed at the top, then Replace: it wrote the replacement
  over "on", the two characters that stood where the match had been.
Now the dialog keeps the text its matches were found in. When the pane no
longer holds that text, Find Next runs the same search again in the text as
it is and goes to the first match at or after the caret, coming round to
the first after the last. Replace does the same and replaces nothing on
that press: it shows the match, says "Text changed, nothing replaced", and
the next press replaces it. With the text unchanged, both do what they did.
The scan itself is Find's own, moved line for line into a method of its own
so that it can be run again.

ITEM 14. The workflow used actions/checkout@v4 and actions/setup-python@v5
in both of its jobs. Each is built for Node 20, which GitHub took off its
runners on 2026-09-23; since then they are run on Node 24 with a warning on
every job. They move to the first versions built for Node 24: checkout v5
and setup-python v6, the versions the brand repository moved to on
2026-10-04. Each action's own action.yml was read at both versions: every
input this workflow passes is an input of the newer one, with the same
default.

ITEM 18. The README stated 786 tests; pytest collected 1,178. Every count
is a floor now: over 1,000 tests, over 300 in the root suite, over 600
under tests/. A floor is the number of test functions the suite defines,
rounded down to the hundred, so the next test leaves it true.

THE GUARDS. tests/test_find_follows_the_text.py and
tests/test_replace_edits_the_output.py drive the main window's own Find and
Find and Replace. The class of tests/test_find_searches_the_pane_chosen.py
that held Replace off for the output holds it on. tests/
test_workflow_actions.py holds every action at its floor. tests/
test_readme_test_counts.py holds every count in the README to a floor, and
every floor to the truth.

WHAT ONLY A RUN ON GITHUB SHOWS. That the workflow runs with the newer
actions. The first run after this is committed is that test.
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
SENTINEL = 'RNV-RULINGS-2026-10-05'
SENTINEL_FILE = '.github/workflows/tests.yml'
GUARD = 'tests/test_find_follows_the_text.py'
GUARD_FILES = ['tests/test_find_follows_the_text.py', 'tests/test_replace_edits_the_output.py', 'tests/test_find_searches_the_pane_chosen.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
ROOT_SUITE = 'test_rnv_text_transformer.py'
ACTIONS_GUARD = 'tests/test_workflow_actions.py'
README_GUARD = 'tests/test_readme_test_counts.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_find_follows_the_text.py', 'tests/test_replace_edits_the_output.py', 'tests/test_find_searches_the_pane_chosen.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
DESCRIPTION = "the transformer's rulings of 5 October: Replace works on the output and joins its history, Find Next and Replace follow the text as it now is, the workflow's actions are at the versions built for Node 24, and the README's test counts cannot go stale"

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
CI_MIRRORS = {'.github/workflows/tests.yml': '01165ae05fd077e038078ee15033b2630999d4299378c1ee97e125bad28e80b6'}

SHADOWS = {"find_replace_dialog.py", "main_window.py", "conftest.py", "run_tests.py", "test_rnv_text_transformer.py", "test_find_searches_the_pane_chosen.py", "test_find_follows_the_text.py", "test_replace_edits_the_output.py", "test_workflow_actions.py", "test_readme_test_counts.py"}

LEFT_ALONE = ['five things Find and Replace does as shipped, measured while this was built and not changed. (a) An option ticked after a Find (case, whole word, regex) does not search again until Find is pressed. (b) Replace All with regex off and Case sensitive off, which is the default, treats a backslash in the replacement as a regex escape: C:\\new\\dir is refused as a bad escape. (c) With regex on, Replace inserts a group reference such as \\1 as written, and Replace All expands it. (d) A character outside the basic plane, an emoji, shifts every highlight after it one place to the left. (e) The dialog declares three signals nothing emits or connects. A ruling is asked on each.', "the output's history holds ten states, and each press of Replace in the output is one of them.", "the Find and Replace dialog's width (item 12, still open). The new status line fits: 293 pixels of the label's 420 as drawn here.", "the README's note that the root suite is SHA-pinned, and its link to tests/README.md: the suite's digest is checked by nothing, and the file is tests/tests_README.md. Found on the way; a ruling is asked.", 'the counts other documents state: tests/tests_README.md. Item 18 ruled the README.', 'the coverage figures printed beside the counts: a coverage figure depends on the platform it was taken on.', "the rulings still open on the list of 5 October: white or black text on the light gold fill (item 4), the Find and Replace dialog's clipped buttons (12), the transformer's line-number editor (7) and its Export tab (9). Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/find_replace_dialog.py',
             '        replace_all_requested: Emitted when replace all is requested\n    """\n    \n    # Signals\n    find_requested = pyqtSignal(str, dict)  # search_text, options\n    replace_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    replace_all_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    \n',
             '        replace_all_requested: Emitted when replace all is requested\n        output_edited: Emitted after Replace or Replace All has written\n            to the output\n    """\n    \n    # Signals\n    find_requested = pyqtSignal(str, dict)  # search_text, options\n    replace_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    replace_all_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    # RNV-RULINGS-2026-10-05, item 10: Replace works on the output too. The\n    # main window keeps a history of the output, which every writer joins,\n    # so it is told of each write.\n    output_edited = pyqtSignal()\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             '    _MODAL: ClassVar[bool] = False\n    # RNV-FIND-TARGET 2026-10-04: said when Replace is asked of a pane that\n    # cannot be edited. The output is read only: it is searched, not replaced.\n    _READ_ONLY_STATUS: ClassVar[str] = "The output is read-only: Replace is unavailable"\n    \n',
             '    _MODAL: ClassVar[bool] = False\n    # RNV-RULINGS-2026-10-05, item 11: said when Replace is pressed and the\n    # text is no longer the text the matches were found in. Nothing is\n    # replaced on that press: the match is found again and shown.\n    _TEXT_CHANGED_STATUS: ClassVar[str] = "Text changed, nothing replaced: match {} of {}"\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             "        '_is_replace_mode', '_painted_highlight',\n        '_input_text_edit', '_output_text_edit'\n    )\n",
             "        '_is_replace_mode', '_painted_highlight',\n        '_input_text_edit', '_output_text_edit',\n        '_found_in', '_found_for'\n    )\n")
    tree.sub('ui/find_replace_dialog.py',
             '        self._current_matches: list[tuple[int, int]] = []  # (start, end) positions\n        self._current_match_index: int = -1\n',
             '        self._current_matches: list[tuple[int, int]] = []  # (start, end) positions\n        self._current_match_index: int = -1\n        # RNV-RULINGS-2026-10-05, item 11: the text the matches were found\n        # in, and the search that found them. The matches are positions in\n        # that text, and good for as long as the pane still holds it.\n        self._found_in: str | None = None\n        self._found_for: tuple[str, dict] | None = None\n')
    tree.sub('ui/find_replace_dialog.py',
             '        layout.addLayout(buttons_layout)\n        self._sync_replace_buttons()\n    \n',
             '        layout.addLayout(buttons_layout)\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             '        self._on_find_text_changed(self.find_input.text())\n        self.target_text_edit = text_edit\n        self._sync_replace_buttons()\n    \n',
             '        self._on_find_text_changed(self.find_input.text())\n        self.target_text_edit = text_edit\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _target_is_read_only(self) -> bool:\n        """\n        Whether the pane searched cannot be edited, as the output cannot.\n        \n        RNV-FIND-TARGET 2026-10-04: Replace edits the text, so it is\n        offered only where the text can be edited. A cursor of the\n        document\'s own writes to a read-only pane all the same, so the\n        pane\'s own flag is asked.\n        """\n        return self.target_text_edit is not None and self.target_text_edit.isReadOnly()\n    \n    def _sync_replace_buttons(self) -> None:\n        """Offer Replace and Replace All only where the text can be edited."""\n        if not self._is_replace_mode:\n            return\n        read_only = self._target_is_read_only()\n        self.replace_all_btn.setEnabled(not read_only)\n        if read_only:\n            self.replace_btn.setEnabled(False)\n            self.status_label.setText(self._READ_ONLY_STATUS)\n    \n',
             '    def _edited(self) -> None:\n        """\n        Say so when the pane just written to is the output.\n        \n        RNV-RULINGS-2026-10-05, item 10: Replace and Replace All work on\n        the pane chosen, the output included. The output stays read only\n        to typing; a cursor of the document\'s own writes to it all the\n        same, and so does setPlainText(). The main window keeps a history\n        of the output, so it is told.\n        """\n        if self.target_text_edit is not None and self.target_text_edit is self._output_text_edit:\n            self.output_edited.emit()\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             '        """Handle find text change - reset matches."""\n        self._current_matches.clear()\n        self._current_match_index = -1\n        self.find_next_btn.setEnabled(False)\n',
             '        """Handle find text change - reset matches."""\n        self._forget_matches()\n        self.find_next_btn.setEnabled(False)\n')
    tree.sub('ui/find_replace_dialog.py',
             '        if not self._current_matches:\n            self._on_find()\n            return\n        \n        # Move to next match\n',
             '        if not self._current_matches:\n            self._on_find()\n            return\n        \n        # RNV-RULINGS-2026-10-05, item 11: the matches are positions in the\n        # text the Find read. Once that text was typed in, or written again\n        # by a transform, this stepped through places where the matches no\n        # longer were. Now the search is run again in the text as it is,\n        # and the next match is the first at or after the caret.\n        if self._matches_are_stale():\n            self._find_again()\n            return\n        \n        # Move to next match\n')
    tree.sub('ui/find_replace_dialog.py',
             '        # RNV-FIND-TARGET 2026-10-04: a read-only pane is searched, not edited.\n        if self._target_is_read_only():\n            self.status_label.setText(self._READ_ONLY_STATUS)\n            return\n        \n        replace_text = self.replace_input.text()\n        start, end = self._current_matches[self._current_match_index]\n        \n        # Replace the current match\n        cursor = self.target_text_edit.textCursor()\n        cursor.setPosition(start)\n        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n        cursor.insertText(replace_text)\n        \n',
             '        # RNV-RULINGS-2026-10-05, item 11: the positions recorded are places\n        # in the text the Find read. In a text that had changed since, this\n        # wrote over whatever stood there. The match is found again and\n        # shown, and nothing is replaced until Replace is pressed on it.\n        if self._matches_are_stale():\n            if self._find_again():\n                self.status_label.setText(self._TEXT_CHANGED_STATUS.format(\n                    self._current_match_index + 1, len(self._current_matches)))\n            return\n        \n        replace_text = self.replace_input.text()\n        start, end = self._current_matches[self._current_match_index]\n        \n        # Replace the current match\n        cursor = self.target_text_edit.textCursor()\n        cursor.setPosition(start)\n        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n        cursor.insertText(replace_text)\n        self._edited()\n        \n')
    tree.sub('ui/find_replace_dialog.py',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        # RNV-FIND-TARGET 2026-10-04: a read-only pane is searched, not edited.\n        if self._target_is_read_only():\n            self.status_label.setText(self._READ_ONLY_STATUS)\n            return\n        \n        replace_text = self.replace_input.text()\n        options = self.get_search_options()\n',
             '        if self.target_text_edit is None or self.replace_input is None:\n            return\n        \n        replace_text = self.replace_input.text()\n        options = self.get_search_options()\n')
    tree.sub('ui/find_replace_dialog.py',
             '            if count > 0:\n                self.target_text_edit.setPlainText(new_text)\n',
             '            if count > 0:\n                self.target_text_edit.setPlainText(new_text)\n                self._edited()\n')
    tree.sub('ui/find_replace_dialog.py',
             '            self.status_label.setText(f"Regex error: {e}")\n        \n        self._current_matches.clear()\n        self._current_match_index = -1\n    \n',
             '            self.status_label.setText(f"Regex error: {e}")\n        \n        self._forget_matches()\n    \n')
    tree.sub('ui/find_replace_dialog.py',
             "        text = self.target_text_edit.toPlainText()\n        self._current_matches.clear()\n        self._current_match_index = -1\n        \n        try:\n            if options['regex']:\n                flags = 0 if options['case_sensitive'] else re.IGNORECASE\n                pattern = re.compile(search_text, flags)\n                for match in pattern.finditer(text):\n                    self._current_matches.append((match.start(), match.end()))\n            else:\n                if options['whole_word']:\n                    flags = 0 if options['case_sensitive'] else re.IGNORECASE\n                    pattern = re.compile(r'\\b' + re.escape(search_text) + r'\\b', flags)\n                    for match in pattern.finditer(text):\n                        self._current_matches.append((match.start(), match.end()))\n                else:\n                    # Simple text search\n                    search_in = text if options['case_sensitive'] else text.lower()\n                    find_text = search_text if options['case_sensitive'] else search_text.lower()\n                    \n                    start = 0\n                    while True:\n                        pos = search_in.find(find_text, start)\n                        if pos == -1:\n                            break\n                        self._current_matches.append((pos, pos + len(search_text)))\n                        start = pos + 1\n            \n",
             '        text = self.target_text_edit.toPlainText()\n        self._forget_matches()\n        \n        try:\n            self._current_matches.extend(self._matches_in(text, search_text, options))\n            \n')
    tree.sub('ui/find_replace_dialog.py',
             '            if self._current_matches:\n                self._current_match_index = 0\n                self._highlight_all_matches()\n',
             "            if self._current_matches:\n                # RNV-RULINGS-2026-10-05, item 11: the text read and the\n                # search run, kept so that Find Next and Replace can tell\n                # when these positions are no longer the matches'.\n                self._found_in = text\n                self._found_for = (search_text, dict(options))\n                self._current_match_index = 0\n                self._highlight_all_matches()\n")
    tree.sub('ui/find_replace_dialog.py',
             '                if self.replace_btn:\n                    # RNV-FIND-TARGET 2026-10-04: not on a read-only pane.\n                    self.replace_btn.setEnabled(not self._target_is_read_only())\n',
             '                if self.replace_btn:\n                    self.replace_btn.setEnabled(True)\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _highlight_colour(self) -> QColor:\n',
             '    def _forget_matches(self) -> None:\n        """\n        Forget the search that was showing: its matches, and the text\n        they were found in.\n        \n        RNV-RULINGS-2026-10-05, item 11: one place for it, so that the\n        text is held for exactly as long as the matches are.\n        """\n        self._current_matches.clear()\n        self._current_match_index = -1\n        self._found_in = None\n        self._found_for = None\n    \n    @staticmethod\n    def _matches_in(text: str, search_text: str, options: dict) -> list[tuple[int, int]]:\n        """\n        Where the search matches in a text.\n        \n        RNV-RULINGS-2026-10-05, item 11: the scan Find has always run,\n        line for line, moved here so that it can be run again once the\n        text has changed.\n        \n        Args:\n            text: The text to search\n            search_text: Text to search for\n            options: Search options dictionary\n        \n        Returns:\n            (start, end) of every match, in order\n        \n        Raises:\n            re.error: The pattern does not compile\n        """\n        matches: list[tuple[int, int]] = []\n        if options[\'regex\']:\n            flags = 0 if options[\'case_sensitive\'] else re.IGNORECASE\n            pattern = re.compile(search_text, flags)\n            for match in pattern.finditer(text):\n                matches.append((match.start(), match.end()))\n        else:\n            if options[\'whole_word\']:\n                flags = 0 if options[\'case_sensitive\'] else re.IGNORECASE\n                pattern = re.compile(r\'\\b\' + re.escape(search_text) + r\'\\b\', flags)\n                for match in pattern.finditer(text):\n                    matches.append((match.start(), match.end()))\n            else:\n                # Simple text search\n                search_in = text if options[\'case_sensitive\'] else text.lower()\n                find_text = search_text if options[\'case_sensitive\'] else search_text.lower()\n                \n                start = 0\n                while True:\n                    pos = search_in.find(find_text, start)\n                    if pos == -1:\n                        break\n                    matches.append((pos, pos + len(search_text)))\n                    start = pos + 1\n        return matches\n    \n    def _matches_are_stale(self) -> bool:\n        """\n        Whether the pane no longer holds the text the matches were found in.\n        \n        RNV-RULINGS-2026-10-05, item 11. Asked of the text itself, so it\n        is true exactly when the positions recorded may no longer be the\n        matches\': after typing, or after the output has been written\n        again by a transform or an undo. A highlight painted again, a\n        theme switched or a caret moved changes no text.\n        """\n        return (self.target_text_edit is not None\n                and self.target_text_edit.toPlainText() != self._found_in)\n    \n    def _find_again(self) -> bool:\n        """\n        Run the search Find ran again, in the text as it is now, and make\n        the first match at or after the caret the current one.\n        \n        RNV-RULINGS-2026-10-05, item 11. The search is the one Find ran:\n        its text and its options as they were then. Past the last match\n        it comes round to the first, as Find Next does. The view moves\n        only as far as it must to show the match: it is Find that puts\n        the first match at the top.\n        \n        Returns:\n            Whether the text still holds a match\n        """\n        search_text, options = self._found_for\n        text = self.target_text_edit.toPlainText()\n        matches = self._matches_in(text, search_text, options)\n        self._forget_matches()\n        if not matches:\n            self.status_label.setText("No matches found")\n            self._clear_highlights()\n            return False\n        \n        self._current_matches.extend(matches)\n        self._found_in = text\n        self._found_for = (search_text, options)\n        caret = self.target_text_edit.textCursor().selectionEnd()\n        self._current_match_index = next(\n            (index for index, (start, _end) in enumerate(matches) if start >= caret), 0)\n        self._highlight_all_matches()\n        self._highlight_current_match()\n        return True\n    \n    def _highlight_colour(self) -> QColor:\n')
    tree.sub('ui/main_window.py',
             '            replace_mode=True,\n            parent=self,\n            output_text_edit=self.output_text\n        )\n        self._track_open_dialog(dialog)\n',
             "            replace_mode=True,\n            parent=self,\n            output_text_edit=self.output_text\n        )\n        # RNV-RULINGS-2026-10-05, item 10: a Replace in the output joins\n        # the output's history.\n        dialog.output_edited.connect(self._on_output_replaced)\n        self._track_open_dialog(dialog)\n")
    tree.sub('ui/main_window.py',
             '            self._set_status(f"Redo ({self._output_history_index + 1}/{len(self._output_history)})")\n        else:\n            self._set_status("Nothing to redo")\n    \n',
             '            self._set_status(f"Redo ({self._output_history_index + 1}/{len(self._output_history)})")\n        else:\n            self._set_status("Nothing to redo")\n    \n    def _on_output_replaced(self) -> None:\n        """\n        Find and Replace has written to the output: record it, as every\n        writer of the output does.\n        \n        RNV-RULINGS-2026-10-05, item 10. Replace was off for the output\n        because the pane is read only. It is on now. The output\'s\n        history is this window\'s own (Ctrl+Z and Ctrl+Y step through\n        it), so the text Replace left joins it, and the statistics are\n        counted again.\n        """\n        self._add_to_output_history(self.output_text.toPlainText())\n        self._update_statistics()\n        self._set_status("Replace applied to output")\n    \n')
    tree.sub('tests/test_find_searches_the_pane_chosen.py',
             '- the output is read only, so it is searched and not replaced: with Output\n  chosen Replace and Replace All are off, and say why;\n',
             '- Replace and Replace All work on the pane chosen. Until 2026-10-05 they\n  were off for the output, which is read only to typing; item 10 of\n  RNV-RULINGS-2026-10-05 turned them on, and what they do there is held\n  by tests/test_replace_edits_the_output.py;\n')
    tree.sub('tests/test_find_searches_the_pane_chosen.py',
             'class TestTheOutputIsSearchedNotReplaced:\n\n    def test_the_premise_the_output_is_read_only_and_the_input_is_not(self, filled):\n        assert filled.output_text.isReadOnly() and not filled.text_input.isReadOnly()\n\n    def test_with_output_chosen_replace_and_replace_all_are_off_and_say_why(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        assert dlg.replace_all_btn.isEnabled(), "Replace All is off on the input"\n        dlg.search_output_radio.click()\n        assert not dlg.replace_all_btn.isEnabled() and not dlg.replace_btn.isEnabled()\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        _find(dlg)\n        assert _highlighted(win.output_text) == _spots(OUT), "the output is not searched in Find and Replace"\n        assert not dlg.replace_btn.isEnabled(), "a Find turned Replace on for a pane that is read only"\n        assert not dlg.replace_all_btn.isEnabled()\n        dlg.close()\n\n    def test_asked_all_the_same_they_leave_both_texts_alone(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        dlg.replace_input.setText("0")\n        dlg._on_replace()\n        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \\\n            "Replace edited a text with Output chosen"\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        dlg.status_label.setText("")\n        dlg._on_replace_all()\n        assert (win.text_input.toPlainText(), win.output_text.toPlainText()) == (IN, OUT), \\\n            "Replace All edited a text with Output chosen"\n        assert dlg.status_label.text() == FindReplaceDialog._READ_ONLY_STATUS\n        dlg.close()\n\n    def test_back_on_the_input_replace_works_as_it_always_has(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        dlg.search_input_radio.click()\n        assert dlg.replace_all_btn.isEnabled() and dlg.status_label.text() == ""\n        _find(dlg)\n        assert dlg.replace_btn.isEnabled()\n        dlg.replace_input.setText("0")\n        dlg._on_replace_all()\n        assert win.text_input.toPlainText() == IN.replace("o", "0")\n        assert win.output_text.toPlainText() == OUT\n        dlg.close()\n\n    def test_find_alone_has_no_replace_to_turn_off(self, filled):\n        dlg = _opened(filled, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        assert dlg.replace_btn is None and dlg.replace_all_btn is None\n        assert dlg.status_label.text() == ""\n        dlg.close()\n\n\n',
             'class TestReplaceIsOfferedInThePaneChosen:\n    """Until 2026-10-05 this class held that the output was searched and not\n    replaced, because it is read only. Item 10 of RNV-RULINGS-2026-10-05\n    ruled that Replace works there too. What it writes, and how that joins\n    the output\'s history, is held by tests/test_replace_edits_the_output.py."""\n\n    def test_the_premise_the_output_is_read_only_and_the_input_is_not(self, filled):\n        assert filled.output_text.isReadOnly() and not filled.text_input.isReadOnly()\n\n    def test_with_output_chosen_replace_and_replace_all_are_offered(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        assert dlg.replace_all_btn.isEnabled(), "Replace All is off on the input"\n        dlg.search_output_radio.click()\n        assert dlg.replace_all_btn.isEnabled(), "Replace All is off with Output chosen"\n        assert not dlg.replace_btn.isEnabled(), "Replace is on before anything is found"\n        assert dlg.status_label.text() == ""\n        _find(dlg)\n        assert _highlighted(win.output_text) == _spots(OUT), "the output is not searched in Find and Replace"\n        assert dlg.replace_btn.isEnabled(), "a Find did not turn Replace on with Output chosen"\n        dlg.close()\n\n    def test_they_edit_the_pane_chosen_and_leave_the_other_alone(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        _find(dlg)\n        dlg.replace_input.setText("0")\n        dlg._on_replace()\n        first = _spots(OUT)[0][0]\n        assert win.output_text.toPlainText() == OUT[:first] + "0" + OUT[first + 1:], \\\n            "Replace did not replace the output\'s first match, and that alone"\n        assert win.text_input.toPlainText() == IN, "Replace edited the input with Output chosen"\n        dlg._on_replace_all()\n        assert win.output_text.toPlainText() == OUT.replace("O", "0"), \\\n            "Replace All did not replace every match in the output"\n        assert win.text_input.toPlainText() == IN, "Replace All edited the input with Output chosen"\n        dlg.close()\n\n    def test_back_on_the_input_replace_works_as_it_always_has(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        dlg.search_input_radio.click()\n        assert dlg.replace_all_btn.isEnabled() and dlg.status_label.text() == ""\n        _find(dlg)\n        assert dlg.replace_btn.isEnabled()\n        dlg.replace_input.setText("0")\n        dlg._on_replace_all()\n        assert win.text_input.toPlainText() == IN.replace("o", "0")\n        assert win.output_text.toPlainText() == OUT\n        dlg.close()\n\n    def test_find_alone_has_no_replace(self, filled):\n        dlg = _opened(filled, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        assert dlg.replace_btn is None and dlg.replace_all_btn is None\n        assert dlg.status_label.text() == ""\n        dlg.close()\n\n\n')
    tree.sub('.github/workflows/tests.yml',
             'uses: actions/checkout@v4\n',
             'uses: actions/checkout@v5\n', times=2)
    tree.sub('.github/workflows/tests.yml',
             'uses: actions/setup-python@v5\n',
             'uses: actions/setup-python@v6\n', times=2)
    tree.sub('.github/workflows/tests.yml',
             '\njobs:\n',
             '\n# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version\n# built for Node 24: checkout v5 and setup-python v6.\n# GitHub took Node 20 off its runners on 2026-09-23, and ran the versions\n# before these on Node 24 with a warning. tests/test_workflow_actions.py\n# holds the floor.\njobs:\n')
    tree.sub('README.md',
             '![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\n',
             '![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\n')
    tree.sub('README.md',
             '- **Comprehensive test suite** — 786 tests across `unittest`, `pytest`, `hypothesis`, and `syrupy`,',
             '- **Comprehensive test suite** — over 1,000 tests across `unittest`, `pytest`, `hypothesis`, and `syrupy`,')
    tree.sub('README.md',
             'The project ships with **786 tests across two complementary suites**,',
             'The project ships with **over 1,000 tests across two complementary suites**,')
    tree.sub('README.md',
             '| `test_rnv_text_transformer.py` (unittest) | 398 | Frozen regression suite',
             '| `test_rnv_text_transformer.py` (unittest) | over 300 | Frozen regression suite')
    tree.sub('README.md',
             '| `tests/` (pytest) | 388 | UI interactions,',
             '| `tests/` (pytest) | over 600 | UI interactions,')
    tree.sub('README.md',
             '  Built with PyQt6 · 786 tests · 76% coverage\n',
             '  Built with PyQt6 · over 1,000 tests · 76% coverage\n')
    if (tree.root / 'tests/test_replace_edits_the_output.py').exists():
        raise Stop('tests/test_replace_edits_the_output.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_replace_edits_the_output.py', '"""Replace works on the output, and what it writes joins the output\'s history.\n\nRNV-RULINGS-2026-10-05, item 10. Ruled 2026-10-05: "Yes."\n\nWHAT WAS THERE. With "Search in: Output" chosen, Replace and Replace All\nwere off and said why: the output is read only. That was RNV-FIND-TARGET\n(2026-10-04), which wired the pair and left this question for a ruling,\nbecause the main window keeps its own history of the output (Ctrl+Z and\nCtrl+Y step through it) and a Replace there would have to join it.\n\nWHAT IS THERE NOW. Replace and Replace All work on the pane chosen. When\nthat pane is the output, the dialog says so (`output_edited`), and the\nwindow does what it does after every writer of the output: the text joins\nthe history, the statistics are counted again, the status says what was\ndone. The output is still read only to typing.\n\nWHAT THIS GUARD HOLDS.\n\n1. Replace and Replace All write to the output when it is the pane chosen,\n   and leave the input alone.\n2. Each press is one step of the output\'s history: undo brings back the\n   text as it was before that press, redo the text as the press left it.\n3. A Replace made after an undo drops what was undone, as every writer\'s\n   does.\n4. The statistics count the output as Replace left it, and the window\'s\n   status says a Replace was applied.\n5. The dialog says so once for each write to the output, and never\n   otherwise: not for a write to the input, not when nothing was found,\n   not for a pattern that does not compile.\n6. The output is still read only to typing.\n\nEvery test drives the main window\'s own opener, and the output is written\nby the window\'s own transform, so its history starts as the app leaves it.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtTest import QTest\nfrom PyQt6.QtWidgets import QApplication\n\nfrom core.text_statistics import TextStatistics\nfrom ui.base_dialog import BaseDialog\nfrom ui.find_replace_dialog import FindReplaceDialog\n\nIN = ("one fox, two foxes, three oxen\\n"\n      "four more of them\\n")\nOUT = IN.upper()\nMODE = "UPPERCASE"\n#: The output with its first, its first two, and all of its "OX" replaced.\nONE = OUT.replace("OX", "__", 1)\nTWO = OUT.replace("OX", "__", 2)\nALL = OUT.replace("OX", "__")\n\n\n@pytest.fixture\ndef transformed(main_window):\n    """The main window after one transform: an input, and the output the\n    window itself wrote from it, which is the one state of its history."""\n    win = main_window\n    win.settings_manager.save_auto_transform(False)\n    win.text_input.setPlainText(IN)\n    win.auto_transform_timer.stop()\n    win.mode_combo.setCurrentText(MODE)\n    assert win.mode_combo.currentText() == MODE, "the transform this guard uses is gone"\n    win._transform_text()\n    assert win.output_text.toPlainText() == OUT\n    assert (win._output_history, win._output_history_index) == ([OUT], 0)\n    assert OUT.count("OX") == 3 and ONE != TWO != ALL\n    yield win\n    win.auto_transform_timer.stop()\n\n\ndef _replace_dialog(win, search_output: bool = True) -> FindReplaceDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    win._open_replace_dialog()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, len(new)\n    dlg = new[0]\n    if search_output:\n        dlg.search_output_radio.click()\n    dlg.find_input.setText("OX")\n    dlg.replace_input.setText("__")\n    return dlg\n\n\ndef _said(dlg) -> list:\n    """Counts the times the dialog says it wrote to the output."""\n    said = []\n    dlg.output_edited.connect(lambda: said.append(1))\n    return said\n\n\nclass TestReplaceWritesToTheOutput:\n\n    def test_replace_all_replaces_every_match_in_the_output_and_leaves_the_input(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg._on_replace_all()\n        assert win.output_text.toPlainText() == ALL, "Replace All did not write to the output"\n        assert win.text_input.toPlainText() == IN, "Replace All edited the input with Output chosen"\n        assert dlg.status_label.text() == "Replaced 3 occurrence(s)"\n        dlg.close()\n\n    def test_replace_replaces_the_match_shown_and_leaves_the_input(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg._on_find()\n        assert dlg.replace_btn.isEnabled(), "a Find did not turn Replace on with Output chosen"\n        dlg._on_replace()\n        assert win.output_text.toPlainText() == ONE, "Replace did not replace the output\'s first match"\n        assert win.text_input.toPlainText() == IN, "Replace edited the input with Output chosen"\n        assert dlg.status_label.text() == "Replaced 1 occurrence"\n        dlg.close()\n\n    def test_the_output_is_still_read_only_to_typing(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg._on_replace_all()\n        assert win.output_text.isReadOnly(), "the output was made editable to let Replace write to it"\n        QTest.keyClicks(win.output_text, "typed")\n        QApplication.processEvents()\n        assert win.output_text.toPlainText() == ALL, "typing changed the output"\n        dlg.close()\n\n\nclass TestWhatReplaceWritesJoinsTheOutputsHistory:\n\n    def test_replace_all_is_one_step_and_undo_and_redo_cross_it(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg._on_replace_all()\n        assert (win._output_history, win._output_history_index) == ([OUT, ALL], 1), \\\n            "the text Replace All left is not the newest state of the output\'s history"\n        win._undo_output()\n        assert win.output_text.toPlainText() == OUT, "undo did not bring back the output as it was before Replace All"\n        win._redo_output()\n        assert win.output_text.toPlainText() == ALL, "redo did not bring back the output as Replace All left it"\n        dlg.close()\n\n    def test_each_press_of_replace_is_a_step_of_its_own(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg._on_find()\n        dlg._on_replace()\n        dlg._on_replace()\n        assert win.output_text.toPlainText() == TWO\n        assert (win._output_history, win._output_history_index) == ([OUT, ONE, TWO], 2)\n        win._undo_output()\n        assert win.output_text.toPlainText() == ONE, "undo did not step back over one Replace"\n        win._undo_output()\n        assert win.output_text.toPlainText() == OUT\n        dlg.close()\n\n    def test_a_replace_after_an_undo_drops_what_was_undone(self, transformed):\n        win = transformed\n        win.mode_combo.setCurrentText("lowercase")\n        assert win.mode_combo.currentText() == "lowercase"\n        win._transform_text()\n        assert win._output_history == [OUT, IN.lower()]\n        win._undo_output()\n        assert win.output_text.toPlainText() == OUT and win._output_history_index == 0\n        dlg = _replace_dialog(win)\n        dlg._on_replace_all()\n        assert (win._output_history, win._output_history_index) == ([OUT, ALL], 1), \\\n            "a Replace after an undo kept the state that was undone"\n        win._redo_output()\n        assert win.output_text.toPlainText() == ALL, "there was something to redo after a new edit"\n        dlg.close()\n\n    def test_the_statistics_and_the_status_are_the_windows_own_for_a_writer(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        dlg.replace_input.setText("")                         # three matches of two characters go\n        dlg._on_replace_all()\n        left = win.output_text.toPlainText()\n        assert left == OUT.replace("OX", "") and len(left) == len(OUT) - 6\n        want = TextStatistics.format_comparison(TextStatistics.calculate(IN), TextStatistics.calculate(left))\n        stale = TextStatistics.format_comparison(TextStatistics.calculate(IN), TextStatistics.calculate(OUT))\n        assert want != stale, "this replace does not change the statistics: the test would pass with them left stale"\n        assert win.stats_label.text() == want, "the statistics do not count the output as Replace left it"\n        assert win.status_label.text() == "Replace applied to output"\n        dlg.close()\n\n\nclass TestTheDialogSaysSoOnceForEachWriteToTheOutput:\n\n    def test_once_for_a_replace_and_once_for_a_replace_all(self, transformed):\n        dlg = _replace_dialog(transformed)\n        said = _said(dlg)\n        dlg._on_find()\n        dlg._on_replace()\n        assert len(said) == 1, f"Replace said it wrote to the output {len(said)} times"\n        dlg._on_replace_all()\n        assert len(said) == 2, f"Replace All said it wrote to the output {len(said) - 1} times"\n        dlg.close()\n\n    def test_never_for_a_write_to_the_input(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win, search_output=False)\n        said = _said(dlg)\n        dlg.find_input.setText("ox")\n        dlg._on_find()\n        dlg._on_replace()\n        dlg._on_replace_all()\n        win.auto_transform_timer.stop()\n        assert win.text_input.toPlainText() == IN.replace("ox", "__"), "Replace did not work on the input"\n        assert said == [], "a Replace in the input was reported as a write to the output"\n        assert (win.output_text.toPlainText(), win._output_history, win._output_history_index) == (OUT, [OUT], 0), \\\n            "a Replace in the input touched the output or its history"\n        dlg.close()\n\n    def test_never_when_nothing_was_written(self, transformed):\n        win = transformed\n        dlg = _replace_dialog(win)\n        said = _said(dlg)\n        dlg.find_input.setText("no such text")\n        dlg._on_replace_all()\n        assert dlg.status_label.text() == "No matches found"\n        dlg.regex_check.setChecked(True)\n        dlg.find_input.setText("(")\n        dlg._on_replace_all()\n        assert dlg.status_label.text().startswith("Regex error")\n        dlg._on_replace()\n        assert dlg.status_label.text() == "No match selected"\n        assert said == [] and (win._output_history, win._output_history_index) == ([OUT], 0)\n        assert win.output_text.toPlainText() == OUT\n        dlg.close()\n\n    def test_find_alone_never_says_so(self, transformed):\n        """Find has no Replace, and the window does not listen to it."""\n        win = transformed\n        before = {id(d) for d in win.findChildren(BaseDialog)}\n        win._open_find_dialog()\n        QApplication.processEvents()\n        dlg = [d for d in win.findChildren(BaseDialog) if id(d) not in before][0]\n        said = _said(dlg)\n        dlg.search_output_radio.click()\n        dlg.find_input.setText("OX")\n        dlg._on_find()\n        dlg._on_find_next()\n        assert said == [] and win._output_history == [OUT]\n        dlg.close()\n')
    if (tree.root / 'tests/test_find_follows_the_text.py').exists():
        raise Stop('tests/test_find_follows_the_text.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_find_follows_the_text.py', '"""Find Next, and Replace, follow the text as it now is.\n\nRNV-RULINGS-2026-10-05, item 11. Ruled 2026-10-05: "Yes fix."\n\nWHAT WAS THERE. A Find recorded where its matches were, and Find Next\nstepped through those positions until Find was pressed again. Once the text\nhad been typed in, or the output had been written again by a transform, the\npositions were places in a text that was gone. Measured on 2026-10-05, on a\nFind for "ox" in "one fox, two foxes, three oxen":\n\n- five characters typed at the top, then Find Next: it selected "tw";\n- the output written again by a transform, then Find Next: it selected a\n  line break and the letter after it;\n- five characters typed at the top, then Replace: it wrote the replacement\n  over "on", the two characters that stood where the match had been.\n\nWHAT IS THERE NOW. The dialog keeps the text its matches were found in.\nWhen the pane no longer holds that text, Find Next runs the same search\nagain in the text as it is and goes to the first match at or after the\ncaret, coming round to the first after the last. Replace does the same and\nreplaces nothing on that press: it shows the match and says so, and the\nnext press replaces it.\n\nWHAT THIS GUARD HOLDS.\n\n1. After the text has changed, Find Next selects a match of the text as it\n   is, the highlights are where the matches are, and the count is theirs.\n   In the input after typing, and in the output after a transform.\n2. The match it goes to is the first at or after the caret, and after the\n   last match the first.\n3. When no match is left it says so and selects nothing.\n4. After the text has changed, Replace changes nothing on that press, shows\n   the match and says so. Pressed again, it replaces that match and no\n   other character.\n5. With the text unchanged, Find Next steps as it always has, and does not\n   search again. A theme switched, a caret moved or a highlight painted\n   again is not a change; nor is a change that has been undone.\n6. The search run again is the one Find ran: an option ticked since then\n   waits for Find, as it did before this round.\n7. What is forgotten with the matches is forgotten whole: choosing the\n   other pane or changing the find text leaves no text held.\n"""\nfrom __future__ import annotations\n\nimport re\n\nimport pytest\nfrom PyQt6.QtTest import QTest\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.base_dialog import BaseDialog\nfrom ui.find_replace_dialog import FindReplaceDialog\n\nIN = ("one fox, two foxes, three oxen\\n"\n      "four more of them\\n")\nTYPED = "Now: "\n\n\ndef _spots(text: str, needle: str = "ox") -> list:\n    """(start, end) of every case-blind match of `needle`."""\n    low, out, at = text.lower(), [], 0\n    while (at := low.find(needle.lower(), at)) != -1:\n        out.append((at, at + len(needle)))\n        at += 1\n    return out\n\n\ndef _selection(edit) -> tuple:\n    cursor = edit.textCursor()\n    return cursor.selectionStart(), cursor.selectionEnd()\n\n\ndef _highlighted(edit) -> list:\n    return sorted((s.cursor.selectionStart(), s.cursor.selectionEnd())\n                  for s in edit.extraSelections() if s.cursor.hasSelection())\n\n\ndef _caret_to(edit, position: int) -> None:\n    cursor = edit.textCursor()\n    cursor.setPosition(position)\n    edit.setTextCursor(cursor)\n\n\ndef _type_at(edit, position: int, text: str = TYPED) -> None:\n    """Type `text` into the pane, as a user would, with the caret at `position`."""\n    _caret_to(edit, position)\n    QTest.keyClicks(edit, text)\n    QApplication.processEvents()\n\n\ndef _opened(win, opener: str, needle: str = "ox") -> FindReplaceDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    new[0].find_input.setText(needle)\n    return new[0]\n\n\ndef _counting_searches(monkeypatch) -> list:\n    """Counts the searches Find\'s dialog runs from here on."""\n    ran, scan = [], FindReplaceDialog._matches_in\n\n    def counted(text, search_text, options):\n        ran.append(1)\n        return scan(text, search_text, options)\n    monkeypatch.setattr(FindReplaceDialog, "_matches_in", staticmethod(counted))\n    return ran\n\n\n@pytest.fixture\ndef filled(main_window):\n    """The main window with a text in the input, and auto-transform off."""\n    win = main_window\n    win.settings_manager.save_auto_transform(False)\n    win.text_input.setPlainText(IN)\n    win.auto_transform_timer.stop()\n    assert _spots(IN) == [(5, 7), (14, 16), (26, 28)]\n    yield win\n    win.auto_transform_timer.stop()\n\n\nclass TestFindNextAfterTheTextHasChanged:\n\n    def test_after_typing_it_selects_a_match_of_the_text_as_it_is(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        assert dlg._current_matches == _spots(IN) and _selection(win.text_input) == (5, 7)\n        _type_at(win.text_input, 0)\n        now = win.text_input.toPlainText()\n        assert now == TYPED + IN and _spots(now) == [(10, 12), (19, 21), (31, 33)]\n        dlg._on_find_next()\n        start, end = _selection(win.text_input)\n        assert now[start:end] == "ox", (\n            f"Find Next selected {now[start:end]!r} at {start}: a position the Find recorded, in a "\n            f"text that has changed since")\n        assert (start, end) == (10, 12), "it is not the first match at or after the caret"\n        assert dlg._current_matches == _spots(now), "the positions kept are not the matches\' in the text as it is"\n        assert _highlighted(win.text_input) == _spots(now)\n        assert dlg.status_label.text() == "Match 1 of 3"\n        dlg._on_find_next()\n        assert _selection(win.text_input) == (19, 21), "the next press did not step on from there"\n        dlg.close()\n\n    def test_after_a_transform_writes_the_output_again(self, filled):\n        win = filled\n        win.mode_combo.setCurrentText("UPPERCASE")\n        win._transform_text()\n        dlg = _opened(win, "_open_find_dialog")\n        dlg.search_output_radio.click()\n        dlg._on_find()\n        assert dlg._current_matches == _spots(IN) and _highlighted(win.output_text) == _spots(IN)\n        win.text_input.setPlainText("a box of rocks\\n" + IN)\n        win.auto_transform_timer.stop()\n        win._transform_text()\n        now = win.output_text.toPlainText()\n        assert now == ("a box of rocks\\n" + IN).upper() and len(_spots(now)) == 4\n        assert _highlighted(win.output_text) == [], "the premise: the highlights went with the text they were on"\n        dlg._on_find_next()\n        start, end = _selection(win.output_text)\n        assert now[start:end] == "OX" and (start, end) == _spots(now)[0], \\\n            f"Find Next selected {now[start:end]!r} in the output a transform wrote again"\n        assert _highlighted(win.output_text) == _spots(now), "the highlights were not painted on the new text"\n        assert dlg.status_label.text() == "Match 1 of 4"\n        dlg.close()\n\n    @pytest.mark.parametrize("caret,expected", [\n        (0, 0),          # before every match: the first\n        (10, 0),         # at the start of a match: that match\n        (11, 1),         # inside one: the next\n        (13, 1),\n        (22, 2),\n        (34, 0),         # after the last: round to the first\n    ])\n    def test_it_goes_to_the_first_match_at_or_after_the_caret(self, filled, caret, expected):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        _type_at(win.text_input, 0)\n        now = win.text_input.toPlainText()\n        _caret_to(win.text_input, caret)\n        dlg._on_find_next()\n        assert _selection(win.text_input) == _spots(now)[expected], (caret, expected)\n        assert dlg.status_label.text() == f"Match {expected + 1} of 3"\n        dlg.close()\n\n    def test_when_no_match_is_left_it_says_so_and_selects_nothing(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        win.text_input.setPlainText("nothing here to find\\n")\n        win.auto_transform_timer.stop()\n        dlg._on_find_next()\n        assert dlg.status_label.text() == "No matches found"\n        assert dlg._current_matches == [] and dlg._current_match_index == -1\n        assert not win.text_input.textCursor().hasSelection(), "a position from the old text was selected"\n        assert _highlighted(win.text_input) == []\n        dlg.close()\n\n\nclass TestReplaceAfterTheTextHasChanged:\n\n    def test_the_first_press_changes_nothing_and_shows_the_match(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.replace_input.setText("OX")\n        dlg._on_find()\n        _type_at(win.text_input, 0)\n        now = win.text_input.toPlainText()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == now, (\n            f"Replace wrote at a position the Find recorded, in a text that has changed since: "\n            f"{win.text_input.toPlainText()[:16]!r}")\n        assert _selection(win.text_input) == (10, 12), "the match it would replace is not the one shown"\n        assert dlg.status_label.text() == FindReplaceDialog._TEXT_CHANGED_STATUS.format(1, 3)\n        assert dlg.status_label.text() == "Text changed, nothing replaced: match 1 of 3"\n        dlg.close()\n\n    def test_the_next_press_replaces_that_match_and_no_other_character(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.replace_input.setText("OX")\n        dlg._on_find()\n        _type_at(win.text_input, 0)\n        now = win.text_input.toPlainText()\n        dlg._on_replace()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == now[:10] + "OX" + now[12:]\n        assert dlg.status_label.text() == "Replaced 1 occurrence"\n        dlg.close()\n\n    def test_in_the_output_too_and_nothing_joins_its_history_until_something_is_replaced(self, filled):\n        win = filled\n        win.mode_combo.setCurrentText("UPPERCASE")\n        win._transform_text()\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.search_output_radio.click()\n        dlg.replace_input.setText("__")\n        dlg._on_find()\n        win.text_input.setPlainText("a box of rocks\\n" + IN)\n        win.auto_transform_timer.stop()\n        win._transform_text()\n        now = win.output_text.toPlainText()\n        history = list(win._output_history)\n        dlg._on_replace()\n        assert win.output_text.toPlainText() == now and win._output_history == history\n        assert _selection(win.output_text) == _spots(now)[0]\n        assert dlg.status_label.text() == FindReplaceDialog._TEXT_CHANGED_STATUS.format(1, 4)\n        dlg._on_replace()\n        first = _spots(now)[0][0]\n        assert win.output_text.toPlainText() == now[:first] + "__" + now[first + 2:]\n        assert win._output_history == history + [win.output_text.toPlainText()]\n        dlg.close()\n\n    def test_when_no_match_is_left_replace_says_so_and_changes_nothing(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.replace_input.setText("OX")\n        dlg._on_find()\n        win.text_input.setPlainText("nothing here to find\\n")\n        win.auto_transform_timer.stop()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "nothing here to find\\n"\n        assert dlg.status_label.text() == "No matches found"\n        dlg.close()\n\n\nclass TestWithTheTextUnchangedNothingIsDifferent:\n\n    def test_find_next_steps_through_the_matches_and_does_not_search_again(self, filled, monkeypatch):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        ran = _counting_searches(monkeypatch)\n        seen = []\n        for _ in range(4):\n            dlg._on_find_next()\n            seen.append(_selection(win.text_input))\n        assert seen == [(14, 16), (26, 28), (5, 7), (14, 16)], "Find Next no longer steps and comes round"\n        assert ran == [], f"Find Next searched again {len(ran)} times in a text that had not changed"\n        dlg.close()\n\n    def test_the_counter_above_counts(self, filled, monkeypatch):\n        """Or the test above passes whatever Find Next does."""\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        ran = _counting_searches(monkeypatch)\n        _type_at(win.text_input, 0)\n        dlg._on_find_next()\n        assert ran == [1]\n        dlg.close()\n\n    def test_a_switch_a_caret_moved_and_a_repaint_are_not_a_change(self, filled, monkeypatch):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        ran = _counting_searches(monkeypatch)\n        win._cycle_theme()\n        QApplication.processEvents()\n        _caret_to(win.text_input, 40)\n        dlg._recolour_highlights()\n        assert not dlg._matches_are_stale()\n        dlg._on_find_next()\n        assert _selection(win.text_input) == (14, 16) and ran == [], \\\n            "Find Next took a switch, a caret or a repaint for a change of the text"\n        dlg.close()\n\n    def test_a_change_that_was_undone_is_not_a_change(self, filled, monkeypatch):\n        win = filled\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        ran = _counting_searches(monkeypatch)\n        _type_at(win.text_input, 0, "x")\n        assert dlg._matches_are_stale()\n        win.text_input.undo()\n        assert win.text_input.toPlainText() == IN and not dlg._matches_are_stale()\n        dlg._on_find_next()\n        assert _selection(win.text_input) == (14, 16) and ran == []\n        dlg.close()\n\n    def test_replace_with_the_text_unchanged_replaces_at_once(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        dlg.replace_input.setText("OX")\n        dlg._on_find()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == IN[:5] + "OX" + IN[7:]\n        assert dlg.status_label.text() == "Replaced 1 occurrence"\n        dlg.close()\n\n\nclass TestTheSearchRunAgainIsTheOneFindRan:\n\n    def test_an_option_ticked_since_the_find_waits_for_find(self, filled):\n        """As before this round: the options are read when Find is pressed.\n        Whether ticking one should search again is a question of its own."""\n        win = filled\n        win.text_input.setPlainText("Ox ox OX\\n")\n        win.auto_transform_timer.stop()\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        assert len(dlg._current_matches) == 3\n        dlg.case_sensitive_check.setChecked(True)\n        _type_at(win.text_input, 0, "- ")\n        dlg._on_find_next()\n        assert dlg._current_matches == [(2, 4), (5, 7), (8, 10)], \\\n            "the search run again read the options as they are now, not as Find ran it"\n        dlg._on_find()\n        assert dlg._current_matches == [(5, 7)], "Find itself no longer reads the options as they are"\n        dlg.close()\n\n\nclass TestWhatIsForgottenIsForgottenWhole:\n\n    def test_the_text_is_held_only_while_the_matches_are(self, filled):\n        win = filled\n        dlg = _opened(win, "_open_replace_dialog")\n        assert dlg._found_in is None and dlg._found_for is None\n        dlg._on_find()\n        assert dlg._found_in == IN and dlg._found_for[0] == "ox"\n        dlg.find_input.setText("oxe")\n        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a new find text"\n        dlg._on_find()\n        dlg.search_output_radio.click()\n        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "the other pane"\n        dlg.search_input_radio.click()\n        dlg._on_find()\n        dlg.replace_input.setText("-")\n        dlg._on_replace_all()\n        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a Replace All"\n        dlg.find_input.setText("no such text")\n        dlg._on_find()\n        assert (dlg._current_matches, dlg._found_in, dlg._found_for) == ([], None, None), "a Find with no match"\n        dlg.close()\n\n    def test_the_scan_is_the_one_find_has_always_run(self):\n        """The four ways it searches, on one text."""\n        text = "Ox ox OX box.\\nox-cart (ox)"\n        scan = FindReplaceDialog._matches_in\n        blind = {"case_sensitive": False, "whole_word": False, "regex": False}\n        assert scan(text, "ox", blind) == [(0, 2), (3, 5), (6, 8), (10, 12), (14, 16), (23, 25)]\n        assert scan(text, "ox", {**blind, "case_sensitive": True}) == [(3, 5), (10, 12), (14, 16), (23, 25)]\n        assert scan(text, "ox", {**blind, "whole_word": True}) == [(0, 2), (3, 5), (6, 8), (14, 16), (23, 25)]\n        assert scan(text, r"\\(o(x)\\)", {**blind, "regex": True}) == [(22, 26)]\n        assert scan("aaaa", "aa", blind) == [(0, 2), (1, 3), (2, 4)], "matches that overlap are each found"\n        with pytest.raises(re.error):\n            scan(text, "(", {**blind, "regex": True})\n')
    if (tree.root / 'tests/test_workflow_actions.py').exists():
        raise Stop('tests/test_workflow_actions.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_workflow_actions.py', '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n')
    if (tree.root / 'tests/test_readme_test_counts.py').exists():
        raise Stop('tests/test_readme_test_counts.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_readme_test_counts.py', '"""The README says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 786 tests and pytest collected 1,178.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests the README states is a floor. An exact count,\n   written as a sentence, as a badge or as a cell of the suites\' table, is\n   how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the README\'s number.\n3. The reader is looking. It finds the README\'s floors, and it tells an\n   exact count from a floor in each of the three ways one is written.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nREADME = ROOT / "README.md"\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_text_transformer.py"\n\n#: The README states this many floors. Fewer and the reader has gone blind,\n#: or the README has stopped saying.\nMIN_FLOORS = 6\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nCELL = re.compile(rf"\\|\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\s*(?=\\|)", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\nA_SUITE_ROW = re.compile(r"unittest|pytest|\\btests\\b|coverage", re.I)\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        seen = set()\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):\n            for match in CELL.finditer(line):\n                add(match, bool(match.group("over")))\n    return found\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_the_readme_states_is_a_floor():\n    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in\n             _claims(README.read_text(encoding="utf-8")) if not floor]\n    assert not exact, (\n        "the README states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "the README promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the README\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]\n    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Ctrl+T | 12 | a row of some other table |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (4, 398, False, "root"),\n        (5, 600, True, "pytest"),\n    ], _claims(sample)\n')


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
    def units(src):
        """Every function, method and assignment a source defines, each under its
        name -> its text. A comment is not part of it; a docstring is."""
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name + "()"] = ast.unparse(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name + "()"] = ast.unparse(sub)
                    elif isinstance(sub, (ast.Assign, ast.AnnAssign)) and sub.value is not None:
                        t = sub.targets[0] if isinstance(sub, ast.Assign) else sub.target
                        if isinstance(t, ast.Name):
                            out[node.name + "." + t.id] = ast.unparse(sub.value)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                t = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if isinstance(t, ast.Name):
                    out[t.id] = ast.unparse(node.value)
        return out

    def code(src):
        """units() of a source with every docstring taken out: what the code
        does, not what it says of itself."""
        module = ast.parse(src)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    node.body = node.body[1:] or [ast.Pass()]
        return units(ast.unparse(module))

    def moved(was_src, now_src):
        """(what arrives, what goes, what changes) between two sources, by name."""
        was, now = units(was_src), units(now_src)
        return (sorted(set(now) - set(was)), sorted(set(was) - set(now)),
                sorted(k for k in set(was) & set(now) if was[k] != now[k]))

    def as_written(rel):
        """A file as this round leaves it: from the tree if the round holds it, else from disk."""
        if rel in tree.files:
            return tree.files[rel]
        return (tree.root / rel).read_text(encoding="utf-8-sig", errors="replace")

    def app_sources():
        """(path, text) of the application's Python as this round leaves it: no
        tests, no runner, no delivery script."""
        skip = ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__",
                "venv", "env", "htmlcov", "node_modules")
        paths = set(p.relative_to(tree.root).as_posix() for p in tree.root.rglob("*.py"))
        paths |= set(r for r in tree.files if r.endswith(".py"))
        for rel in sorted(paths - tree.deleted):
            parts = rel.split("/")
            if any(q in skip or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "conftest", "run_tests")):
                continue
            text = as_written(rel)
            if len(parts) == 1 and "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def names_in(text):
        """Every name, attribute and imported name a source reaches for, and
        every string it writes out whole."""
        found = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name):
                found.add(node.id)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.add(node.name)
        return found

    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")]

    def check_moves(table):
        """Each file moves by what the table lists for it, and by nothing else."""
        for rel, arrives, goes, changes in table:
            got = moved(_original(tree, rel), tree.read(rel))
            assert got == (arrives, goes, changes), (
                f"{rel} moved by other than what this round lists: arrives {got[0]}, goes {got[1]}, "
                f"changes {got[2]}")
    DIALOG, WINDOW = "ui/find_replace_dialog.py", "ui/main_window.py"
    MOVES = [('tests/test_find_searches_the_pane_chosen.py', ['TestReplaceIsOfferedInThePaneChosen.test_back_on_the_input_replace_works_as_it_always_has()', 'TestReplaceIsOfferedInThePaneChosen.test_find_alone_has_no_replace()', 'TestReplaceIsOfferedInThePaneChosen.test_the_premise_the_output_is_read_only_and_the_input_is_not()', 'TestReplaceIsOfferedInThePaneChosen.test_they_edit_the_pane_chosen_and_leave_the_other_alone()', 'TestReplaceIsOfferedInThePaneChosen.test_with_output_chosen_replace_and_replace_all_are_offered()'], ['TestTheOutputIsSearchedNotReplaced.test_asked_all_the_same_they_leave_both_texts_alone()', 'TestTheOutputIsSearchedNotReplaced.test_back_on_the_input_replace_works_as_it_always_has()', 'TestTheOutputIsSearchedNotReplaced.test_find_alone_has_no_replace_to_turn_off()', 'TestTheOutputIsSearchedNotReplaced.test_the_premise_the_output_is_read_only_and_the_input_is_not()', 'TestTheOutputIsSearchedNotReplaced.test_with_output_chosen_replace_and_replace_all_are_off_and_say_why()'], []), ('ui/find_replace_dialog.py', ['FindReplaceDialog._TEXT_CHANGED_STATUS', 'FindReplaceDialog._edited()', 'FindReplaceDialog._find_again()', 'FindReplaceDialog._forget_matches()', 'FindReplaceDialog._matches_are_stale()', 'FindReplaceDialog._matches_in()', 'FindReplaceDialog.output_edited'], ['FindReplaceDialog._READ_ONLY_STATUS', 'FindReplaceDialog._sync_replace_buttons()', 'FindReplaceDialog._target_is_read_only()'], ['FindReplaceDialog.__init__()', 'FindReplaceDialog.__slots__', 'FindReplaceDialog._on_find_next()', 'FindReplaceDialog._on_find_text_changed()', 'FindReplaceDialog._on_replace()', 'FindReplaceDialog._on_replace_all()', 'FindReplaceDialog._perform_find()', 'FindReplaceDialog._search_in()', 'FindReplaceDialog._setup_ui()']), ('ui/main_window.py', ['MainWindow._on_output_replaced()'], [], ['MainWindow._open_replace_dialog()'])]
    GONE = ('_READ_ONLY_STATUS', '_target_is_read_only', '_sync_replace_buttons')
    D = "FindReplaceDialog."
    check_moves(MOVES)

    # ---- item 10, over the whole application as this round leaves it: nothing reaches for what held Replace off
    swept = []
    for rel, text in app_sources():
        swept.append(rel)
        hit = sorted(names_in(text) & set(GONE))
        assert not hit, f"{rel} reaches for {hit}, which this round removes"
    assert len(swept) >= 42 and DIALOG in swept and WINDOW in swept, \
        f"the sweep read {len(swept)} files of the application"
    dialog, window = code(tree.read(DIALOG)), code(tree.read(WINDOW))

    # ---- the dialog writes to a pane in two places, and after each it says so; it says so only of the output
    writers = sorted(name for name, text in dialog.items() if ".insertText(" in text or ".setPlainText(" in text)
    assert writers == [D + "_on_replace()", D + "_on_replace_all()"], f"the dialog writes to a pane in {writers}"
    for name, wrote in ((D + "_on_replace()", "cursor.insertText(replace_text)"),
                        (D + "_on_replace_all()", "self.target_text_edit.setPlainText(new_text)")):
        lines = [line.strip() for line in dialog[name].splitlines()]
        at = [n for n, line in enumerate(lines) if line == wrote]
        assert len(at) == 1 and lines[at[0] + 1] == "self._edited()", \
            f"{name} writes to the pane and does not say so on the next line"
    tellers = sorted(name for name, text in dialog.items() if "self.output_edited.emit()" in text)
    assert tellers == [D + "_edited()"] \
        and "self.target_text_edit is self._output_text_edit" in dialog[D + "_edited()"], \
        "the dialog reports a write to the output other than from _edited(), or for a pane that is not the output"

    # ---- the window listens to Find and Replace alone, and records the write as it does every writer's
    listeners = sorted(name for name, text in window.items() if ".output_edited.connect(" in text)
    assert listeners == ["MainWindow._open_replace_dialog()"] \
        and "dialog.output_edited.connect(self._on_output_replaced)" in window[listeners[0]], \
        f"the window listens for a write to the output in {listeners}"
    slot = _function(tree.read(WINDOW), "_on_output_replaced", cls="MainWindow")
    does = [ast.unparse(s) for s in slot.body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert does == ["self._add_to_output_history(self.output_text.toPlainText())",
                    "self._update_statistics()", "self._set_status('Replace applied to output')"], \
        f"the window's record of a Replace in the output is {does}"
    assert tree.read(WINDOW).count("self.output_text.setReadOnly(True)") == 1 \
        and "output_text.setReadOnly(False)" not in tree.read(WINDOW), \
        "the output is not made read only once, and left so"

    # ---- item 11: the scan that moved is the scan Find ran, statement for statement
    was_find = _function(_original(tree, DIALOG), "_perform_find", cls="FindReplaceDialog")
    was_try = next(s for s in was_find.body if isinstance(s, ast.Try))
    ran = ast.unparse(was_try.body[0]).replace("self._current_matches.append(", "matches.append(")
    scan = _function(tree.read(DIALOG), "_matches_in", cls="FindReplaceDialog")
    body = [s for s in scan.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert [type(s).__name__ for s in body] == ["AnnAssign", "If", "Return"] and ast.unparse(body[1]) == ran, \
        "the scan moved into _matches_in() is not the scan Find ran"
    assert ast.unparse(body[0]) == "matches: list[tuple[int, int]] = []" and ast.unparse(body[2]) == "return matches"

    # ---- Find keeps the text it read; Find Next and Replace ask whether the pane still holds it before a position is used
    assert "self.target_text_edit.toPlainText() != self._found_in" in dialog[D + "_matches_are_stale()"], \
        "what is asked is not whether the pane still holds the text the matches were found in"
    found = dialog[D + "_perform_find()"]
    assert "self._found_in = text" in found and "self._found_for = (search_text, dict(options))" in found, \
        "Find does not keep the text it read and the search it ran"
    for name, uses in ((D + "_on_find_next()", "self._current_match_index = (self._current_match_index + 1)"),
                       (D + "_on_replace()", "start, end = self._current_matches[self._current_match_index]")):
        text = dialog[name]
        assert text.count("if self._matches_are_stale():") == 1 and text.count(uses) == 1 \
            and text.index("if self._matches_are_stale():") < text.index(uses), \
            f"{name} uses a recorded position before asking whether the text has changed"
    again = dialog[D + "_find_again()"]
    assert "search_text, options = self._found_for" in again and "self._matches_in(text, search_text, options)" in again \
        and "caret = self.target_text_edit.textCursor().selectionEnd()" in again and "if start >= caret" in again, \
        "the search run again is not Find's own, from the caret on"
    replace = dialog[D + "_on_replace()"]
    stale = replace[replace.index("if self._matches_are_stale():"):replace.index("replace_text = self.replace_input.text()")]
    assert "insertText" not in stale and stale.rstrip().endswith("return"), \
        "Replace can write on the press that finds the text has changed"
    forgets = sorted(name for name, text in dialog.items() if "self._forget_matches()" in text)
    assert forgets == [D + "_find_again()", D + "_on_find_text_changed()", D + "_on_replace_all()", D + "_perform_find()"], \
        f"the search is forgotten in {forgets}"
    for rel, tests in [('tests/test_find_follows_the_text.py', ['test_after_typing_it_selects_a_match_of_the_text_as_it_is', 'test_after_a_transform_writes_the_output_again', 'test_it_goes_to_the_first_match_at_or_after_the_caret', 'test_when_no_match_is_left_it_says_so_and_selects_nothing', 'test_the_first_press_changes_nothing_and_shows_the_match', 'test_the_next_press_replaces_that_match_and_no_other_character', 'test_in_the_output_too_and_nothing_joins_its_history_until_something_is_replaced', 'test_when_no_match_is_left_replace_says_so_and_changes_nothing', 'test_find_next_steps_through_the_matches_and_does_not_search_again', 'test_the_counter_above_counts', 'test_a_switch_a_caret_moved_and_a_repaint_are_not_a_change', 'test_a_change_that_was_undone_is_not_a_change', 'test_replace_with_the_text_unchanged_replaces_at_once', 'test_an_option_ticked_since_the_find_waits_for_find', 'test_the_text_is_held_only_while_the_matches_are', 'test_the_scan_is_the_one_find_has_always_run']), ('tests/test_replace_edits_the_output.py', ['test_replace_all_replaces_every_match_in_the_output_and_leaves_the_input', 'test_replace_replaces_the_match_shown_and_leaves_the_input', 'test_the_output_is_still_read_only_to_typing', 'test_replace_all_is_one_step_and_undo_and_redo_cross_it', 'test_each_press_of_replace_is_a_step_of_its_own', 'test_a_replace_after_an_undo_drops_what_was_undone', 'test_the_statistics_and_the_status_are_the_windows_own_for_a_writer', 'test_once_for_a_replace_and_once_for_a_replace_all', 'test_never_for_a_write_to_the_input', 'test_never_when_nothing_was_written', 'test_find_alone_never_says_so']), ('tests/test_find_searches_the_pane_chosen.py', ['test_the_dialog_is_handed_the_input_and_the_output', 'test_the_find_the_regex_builder_opens_is_handed_both_too', 'test_with_output_chosen_a_find_searches_the_output', 'test_with_input_chosen_a_find_searches_the_input_as_it_always_has', 'test_find_next_steps_through_the_pane_chosen', 'test_choosing_the_other_pane_takes_the_highlights_down_and_forgets_the_matches', 'test_choosing_the_pane_already_searched_leaves_the_search_alone', 'test_the_text_is_not_edited_by_choosing_a_pane', 'test_the_premise_the_output_is_read_only_and_the_input_is_not', 'test_with_output_chosen_replace_and_replace_all_are_offered', 'test_they_edit_the_pane_chosen_and_leave_the_other_alone', 'test_back_on_the_input_replace_works_as_it_always_has', 'test_find_alone_has_no_replace', 'test_a_switch_repaints_the_output_s_highlights', 'test_closing_find_takes_the_output_s_highlights_down', 'test_a_pane_set_as_the_output_is_what_the_output_button_comes_back_to', 'test_with_no_output_handed_in_choosing_it_searches_nothing'])]:
        assert tests_in(tree.read(rel)) == tests, f"{rel}: its tests are {tests_in(tree.read(rel))}"

    # ================= item 14: the workflows' actions, each at the first version built for Node 24
    ACTIONS = (('actions/checkout', 'v4', 'v5'), ('actions/setup-python', 'v5', 'v6'), ('actions/upload-artifact', 'v4', 'v6'))
    WORKFLOW_STEPS = (('.github/workflows/tests.yml', (('actions/checkout', 2), ('actions/setup-python', 2))),)
    NOTE_OPENS = '# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version'
    here = sorted(p.relative_to(tree.root).as_posix()
                  for p in (tree.root / ".github" / "workflows").glob("*.y*ml"))
    assert here == [wf for wf, _steps in WORKFLOW_STEPS], f"the workflows here are {here}"
    ag = dict(__name__="workflow_actions_guard", __file__=str(tree.root / ACTIONS_GUARD))
    exec(compile(tree.read(ACTIONS_GUARD), ACTIONS_GUARD, "exec"), ag)
    assert ag["FLOOR"] == dict((action, int(new[1:])) for action, _old, new in ACTIONS), \
        f"{ACTIONS_GUARD}: its floor is {ag['FLOOR']}"
    assert tests_in(tree.read(ACTIONS_GUARD)) == ['test_every_action_is_at_a_version_built_for_node_24', 'test_the_reader_is_looking'], f"{ACTIONS_GUARD}: its tests are {tests_in(tree.read(ACTIONS_GUARD))}"
    for wf, steps in WORKFLOW_STEPS:
        was, now = _original(tree, wf).splitlines(), tree.read(wf).splitlines()
        opens = [n for n, line in enumerate(now) if line == NOTE_OPENS]
        assert len(opens) == 1, f"{wf}: the note is there {len(opens)} times"
        ends = opens[0]
        while now[ends].startswith("#"):
            ends += 1
        assert now[ends] == "jobs:" and ends - opens[0] == 5, f"{wf}: the note is not the five lines above jobs:"
        short = [action.split("/")[1] + " " + new for action, _old, new in ACTIONS if dict(steps).get(action)]
        said = (", ".join(short[:-1]) + " and " + short[-1]) if len(short) > 1 else short[0]
        assert now[opens[0] + 1] == f"# built for Node 24: {said}.", \
            f"{wf}: the note names {now[opens[0] + 1]!r}, and the file's steps are {said}"
        rest = now[:opens[0]] + now[ends:]
        assert len(rest) == len(was), f"{wf}: lines came or went beyond the note"
        counted = dict()
        for before, after in zip(was, rest):
            if before == after:
                continue
            hit = [action for action, old, new in ACTIONS
                   if before.strip() in (f"uses: {action}@{old}", f"- uses: {action}@{old}")
                   and after == before.replace(f"{action}@{old}", f"{action}@{new}")]
            assert len(hit) == 1, (
                f"{wf}: a line moved that is not one of the three actions going to its new version: "
                f"{before.strip()!r} -> {after.strip()!r}")
            counted[hit[0]] = counted.get(hit[0], 0) + 1
        assert sorted(counted.items()) == sorted(steps), f"{wf}: the steps moved are {sorted(counted.items())}"
        name = wf.rsplit("/", 1)[1]
        flagged = ag["_problems"](name, "\n".join(was))
        assert len(flagged) == sum(n for _a, n in steps) and all("is under v" in p for p in flagged), \
            f"{wf}: as it is here, the guard names {flagged}"
        still = ag["_problems"](name, "\n".join(now))
        assert still == [], f"{wf}: the guard would still name {still}"

    # ================= item 18: every count the README states is a floor, and true of this checkout as it will be
    FLOORS = [(300, 'root'), (600, 'pytest'), (1000, 'all'), (1000, 'all'), (1000, 'all'), (1000, 'all')]
    WAS_EXACT = 6
    rg = dict(__name__="readme_counts_guard", __file__=str(tree.root / README_GUARD))
    exec(compile(tree.read(README_GUARD), README_GUARD, "exec"), rg)
    assert rg["ROOT_SUITE"] == ROOT_SUITE and rg["MIN_FLOORS"] == len(FLOORS), \
        f"{README_GUARD}: it is set for {rg['ROOT_SUITE']} and {rg['MIN_FLOORS']} floors"
    assert tests_in(tree.read(README_GUARD)) == ['test_every_number_of_tests_the_readme_states_is_a_floor', 'test_every_floor_is_true', 'test_the_reader_is_looking'], f"{README_GUARD}: its tests are {tests_in(tree.read(README_GUARD))}"
    was_claims, now_claims = rg["_claims"](_original(tree, "README.md")), rg["_claims"](tree.read("README.md"))
    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in was_claims if not floor]
    assert len(exact) == WAS_EXACT and len(was_claims) == WAS_EXACT, \
        f"README.md states {len(exact)} exact counts here, of {len(was_claims)} counts: {exact}"
    left = [f"README.md:{line}: {n:,}" for line, n, floor, _s in now_claims if not floor]
    assert not left, f"README.md would still state an exact count: {left}"
    assert sorted((n, s) for _l, n, _f, s in now_claims) == FLOORS, \
        f"README.md would state {sorted((n, s) for _l, n, _f, s in now_claims)}"
    modern = sorted((set(p.relative_to(tree.root).as_posix() for p in (tree.root / "tests").glob("test_*.py"))
                     | set(r for r in tree.files if r.startswith("tests/test_") and r.count("/") == 1
                           and r.endswith(".py"))) - tree.deleted)
    defined = dict(root=rg["_defined_in"](as_written(ROOT_SUITE), True),
                   pytest=sum(rg["_defined_in"](as_written(rel), False) for rel in modern))
    defined["all"] = defined["root"] + defined["pytest"]
    assert len(modern) >= 45 and defined["root"] > 100, f"the count of tests has gone blind: {len(modern)} files, {defined}"
    for number, suites in FLOORS:
        assert number < defined[suites], \
            f"README.md would say over {number:,}, and here {suites} defines {defined[suites]:,}"
    for wf, _steps in WORKFLOW_STEPS[:1]:
        assert SENTINEL in tree.read(wf) and SENTINEL in tree.read(ACTIONS_GUARD) and SENTINEL in tree.read(README_GUARD), \
            "the sentinel is not in the workflow and the two guards"
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
