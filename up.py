"""the transformer's rulings of 11 October: the line-number editor goes and the README says what building it would need; Find and Replace do what their controls say; the tests' README is tests/README.md and says nothing that is not so

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (c5321cc).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-11, items 7, 21, 23, 24 and 25 of the list of 5 October:

   7  "We can remove it and set a note in the app repo maybe in the read me
       as a potential feature later with a detailed write up what would need
       to be decided and the purpose of the tool."
  21  "A"
  23  "Yes"
  24  "Yes fix a to d remove e"
  25  "Rename file to README.md"

ITEM 7. ui/line_number_text_edit.py goes: a text box with line numbers that
nothing in the app created. So do its export from ui/, the four colours it
read in each palette (line_number_bg, line_number_fg, line_number_current_bg,
line_number_current_fg), the six tests that built it, its rows in the
snapshot of the palettes and in three other tests, and the README's line for
it. The app's own header stops listing "Line numbers toggle". The README
gains a section, Considered for Later, saying what the tool would be for,
what there was, and what would need deciding before it is built again.

ITEM 21. The README and the tests' README said the root suite was frozen,
SHA-pinned and never edited after release, and gave a digest. Nothing checks
the digest, and it is the digest of no version of the file the repository
has held. Those words go, from both, and from tests/conftest.py's docstring,
which said the same.

ITEM 23. The tests' README said 786 tests, 398 in the root suite, and a
count beside each of sixteen files; the runner's banner said 398. The totals
are floors now: over 1,000, over 300, over 600. The column of per-file counts
goes, and a line says the table lists the suite's first files. The banner
names the suite without a number. The count guard reads tests/README.md as
well as the README.

ITEM 24. In ui/find_replace_dialog.py: (a) an option ticked or unticked since
a Find is a change, as an edit is, so Find Next searches again with the
options as they are, and Replace shows the match first and says "Options
changed, nothing replaced"; (b) with Regular expression off, Replace All
writes the replacement as typed, where a backslash was read as an escape;
(c) with it on, Replace fills group references in, as Replace All does;
(d) positions are counted as the text pane counts them, so a match after an
emoji is highlighted, selected and replaced where it is; (e) three signals
nothing emitted or connected go, and the dialog test that read one reads
the one the dialog has. tests/test_find_and_replace_do_what_they_say.py
holds all five. The class in tests/test_find_follows_the_text.py that held
the old answer to (a) goes.

ITEM 25. tests/tests_README.md is tests/README.md, the name the README links
to, twice.

No setting, no saved file and no colour anything draws in moves.
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
SENTINEL = 'RNV-RULINGS-2026-10-11'
SENTINEL_FILE = 'tests/test_readme_test_counts.py'
GUARD = 'tests/test_find_and_replace_do_what_they_say.py'
GUARD_FILES = ['tests/test_find_and_replace_do_what_they_say.py', 'tests/test_find_follows_the_text.py', 'tests/test_named_and_used.py', 'tests/test_readme_test_counts.py', 'tests/test_workflow_actions.py']
ROOT_SUITE = 'test_rnv_text_transformer.py'
ACTIONS_GUARD = 'tests/test_workflow_actions.py'
COUNTS_GUARD = 'tests/test_readme_test_counts.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_find_and_replace_do_what_they_say.py', 'tests/test_find_follows_the_text.py', 'tests/test_named_and_used.py', 'tests/test_readme_test_counts.py', 'tests/test_workflow_actions.py']
DESCRIPTION = "the transformer's rulings of 11 October: the line-number editor goes and the README says what building it would need; Find and Replace do what their controls say; the tests' README is tests/README.md and says nothing that is not so"

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
CI_MIRRORS = {'.github/workflows/tests.yml': 'bd7e8e60c462b76f374f1f0d9e4b1a8e880d929e06b58a22467f094583b43af9'}

SHADOWS = {"find_replace_dialog.py", "dialog_styles.py", "colors.py", "conftest.py", "run_tests.py", "test_rnv_text_transformer.py", "test_find_and_replace_do_what_they_say.py", "test_find_follows_the_text.py", "test_workflow_actions.py", "test_readme_test_counts.py"}

LEFT_ALONE = ['tests/tests_conftest.py: an older copy of tests/conftest.py, which pytest does not read. Not ruled.', 'the app\'s header still lists "Clipboard history"; the app copies to the clipboard and keeps no history of it. Not ruled.', "the Regex Builder's highlights, which are drawn by the same shared function as Find's and are found in the text as Python counts it: not this round's. Measured and asked about separately.", "the coverage figures in the tests' README: a coverage figure depends on the platform it was taken on.", "the rulings still open on the list of 11 October: the Find and Replace dialog's clipped buttons (item 12, asked about on 11 October) and the transformer's Export tab (9). Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/__init__.py',
             'from ui.line_number_text_edit import LineNumberTextEdit\n\n',
             '')
    tree.sub('ui/__init__.py',
             "    'LineNumberTextEdit',\n",
             '')
    tree.sub('RNV_Text_Transformer.py',
             '- Line numbers toggle and clipboard history\n',
             '- Clipboard history\n')
    tree.sub('utils/dialog_styles.py',
             "        # Line number gutter widget\n        'line_number_bg': BRAND_BLACK,\n        'line_number_fg': GREY_88,\n        'line_number_current_bg': APP_CARD,\n        'line_number_current_fg': BRAND_GOLD,\n\n",
             '')
    tree.sub('utils/dialog_styles.py',
             "        # Line number gutter widget\n        'line_number_bg': GREY_EE,\n        'line_number_fg': GREY_66,\n        'line_number_current_bg': GOLD_TEXT_GROUND_FLOOR,\n        'line_number_current_fg': BRAND_DARK_GOLD_DEEP,\n\n",
             '')
    tree.sub('utils/colors.py',
             "#: Both uses here are grounds the gold family draws on: bg_tertiary, which\n#: carries the About dialog's tab labels, and line_number_current_bg, whose\n#: foreground is BRAND_DARK_GOLD_DEEP itself.\n",
             "#: Its use here is a ground the gold family draws on: bg_tertiary, which\n#: carries the About dialog's tab labels. The second, line_number_current_bg,\n#: went with the line-number editor nothing created: RNV-RULINGS-2026-10-11,\n#: item 7.\n")
    tree.sub('test_rnv_text_transformer.py',
             '                  "drag_drop_text_edit", "line_number_text_edit"],\n',
             '                  "drag_drop_text_edit"],\n')
    tree.sub('test_rnv_text_transformer.py',
             '            "output_text_color", "border_color", "text_color",\n            "line_number_bg", "line_number_fg",\n            "line_number_current_bg", "line_number_current_fg",\n        ]\n',
             '            "output_text_color", "border_color", "text_color",\n            # RNV-RULINGS-2026-10-11, item 7: the line-number editor\'s four\n            # keys stood here. Nothing created the editor, and they went with it.\n        ]\n')
    tree.sub('tests/test_widgets.py',
             '# ════════════════════════════════════════════════════════════════════════════\n# LineNumberTextEdit — 4 tests\n# ════════════════════════════════════════════════════════════════════════════\n\nclass TestLineNumberTextEdit:\n    """Smoke tests for the LineNumberTextEdit (QPlainTextEdit-based) widget."""\n\n    def test_lntextedit_instantiates(self, qtbot):\n        from ui.line_number_text_edit import LineNumberTextEdit\n        edit = LineNumberTextEdit()\n        qtbot.addWidget(edit)\n        assert edit is not None\n\n    def test_lntextedit_setplaintext_updates_content(self, qtbot):\n        """setPlainText followed by toPlainText round-trips the content."""\n        from ui.line_number_text_edit import LineNumberTextEdit\n        edit = LineNumberTextEdit()\n        qtbot.addWidget(edit)\n        edit.setPlainText("hello\\nworld")\n        assert edit.toPlainText() == "hello\\nworld"\n\n    def test_lntextedit_textmodified_signal_exists(self, qtbot):\n        """The custom textModified signal is defined and reachable."""\n        from ui.line_number_text_edit import LineNumberTextEdit\n        edit = LineNumberTextEdit()\n        qtbot.addWidget(edit)\n        assert hasattr(edit, "textModified")\n        # Signal access doesn\'t raise; the bound signal can be subscribed\n        assert isinstance(edit.textModified, pyqtBoundSignal)\n\n    def test_lntextedit_line_number_area_attached(self, qtbot):\n        """A LineNumberArea child widget exists after construction."""\n        from ui.line_number_text_edit import LineNumberTextEdit, LineNumberArea\n        edit = LineNumberTextEdit()\n        qtbot.addWidget(edit)\n        # Find a LineNumberArea among children\n        children = edit.findChildren(LineNumberArea)\n        assert len(children) >= 1, "Expected at least one LineNumberArea child"\n\n\n# ════════════════════════════════════════════════════════════════════════════\n# LineNumberQTextEdit — 2 tests (rich-text variant)\n# ════════════════════════════════════════════════════════════════════════════\n\nclass TestLineNumberQTextEdit:\n    """Smoke tests for the QTextEdit-based variant."""\n\n    def test_lnqtextedit_instantiates(self, qtbot):\n        from ui.line_number_text_edit import LineNumberQTextEdit\n        edit = LineNumberQTextEdit()\n        qtbot.addWidget(edit)\n        assert edit is not None\n\n    def test_lnqtextedit_setplaintext_updates(self, qtbot):\n        """Plain-text setting works on the rich-text variant."""\n        from ui.line_number_text_edit import LineNumberQTextEdit\n        edit = LineNumberQTextEdit()\n        qtbot.addWidget(edit)\n        edit.setPlainText("alpha")\n        assert "alpha" in edit.toPlainText()\n\n\n',
             '')
    tree.sub('tests/test_widgets.py',
             '  LineNumberTextEdit    (ui/line_number_text_edit.py, plain-text variant)\n  LineNumberQTextEdit   (ui/line_number_text_edit.py, rich-text variant)\n',
             '')
    tree.sub('tests/test_contrast_pairs.py',
             "              'output_text_color', 'line_number_current_fg')}\n",
             "              'output_text_color')}\n")
    tree.sub('tests/test_ladder_and_plate.py',
             "#: What the split leaves behind: the ramp step, and the static surfaces that\n#: keep it -- two since RNV-NAMED-AND-USED, 2026-10-04, when the dark\n#: palette's copy of diff_html_header_bg, which nothing read, went. If this\n#: list ever empties, the split has collapsed.\nSTATIC_EE_KEYS = ('diff_html_header_bg', 'line_number_bg')\n",
             "#: What the split leaves behind: the ramp step, and the static surfaces that\n#: keep it -- two since RNV-NAMED-AND-USED, 2026-10-04, when the dark\n#: palette's copy of diff_html_header_bg, which nothing read, went; one since\n#: RNV-RULINGS-2026-10-11, item 7, when line_number_bg went with the editor\n#: nothing created. If this list ever empties, the split has collapsed.\nSTATIC_EE_KEYS = ('diff_html_header_bg',)\n")
    tree.sub('tests/test_ladder_and_plate.py',
             "    ('LIGHT', 'bg_tertiary'): '#e8e8e8',\n    ('LIGHT', 'line_number_current_bg'): '#e8e8e8',\n}\n",
             "    ('LIGHT', 'bg_tertiary'): '#e8e8e8',\n}\n")
    tree.sub('tests/test_ladder_and_plate.py',
             '    assert len(NEW) == 3 and len(PINNED_ENTRIES) == 4 and STATIC_EE_KEYS\n',
             '    # 3 entries since RNV-RULINGS-2026-10-11, item 7: line_number_current_bg went.\n    assert len(NEW) == 3 and len(PINNED_ENTRIES) == 3 and STATIC_EE_KEYS\n')
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "label_text": "#dddddd",\n    "line_number_bg": "#1a1a1a",\n    "line_number_current_bg": "#2a2a2a",\n    "line_number_current_fg": "#d2bc93",\n    "line_number_fg": "#888888",\n',
             '    "label_text": "#dddddd",\n')
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "label_text": "#000000",\n    "line_number_bg": "#eeeeee",\n    "line_number_current_bg": "#e8e8e8",\n    "line_number_current_fg": "#7e6529",\n    "line_number_fg": "#666666",\n',
             '    "label_text": "#000000",\n')
    tree.sub('README.md',
             '│   ├── line_number_text_edit.py   # Gutter-enabled text widget\n',
             '')
    tree.sub('README.md',
             '- [Engineering Notes](#engineering-notes)\n',
             '- [Engineering Notes](#engineering-notes)\n- [Considered for Later](#considered-for-later)\n')
    tree.sub('README.md',
             '---\n\n## Built With\n',
             '---\n\n## Considered for Later\n\n### Line numbers in the text panes\n\n**What it would be.** A gutter down the left edge of the input and output panes that numbers their lines, marks the line the caret is on, and can be hidden. It serves text where a line\'s number is how a place in it is named: code, logs, and the formats among those the app reads (`.py`, `.js`, `.html`, `.log`) where a reader is told "see line 120".\n\n**What there was.** A widget for it, `ui/line_number_text_edit.py`: `LineNumberTextEdit`, and a rich-text variant, with a gutter, the caret\'s line marked, a switch to hide the numbers, and a method to go to a line. Nothing in the app created it: both panes are another class, and no menu, setting or shortcut reached it. It knew dark and light but not image mode; in dark its text area stayed white, so the caret\'s marked line could not be read; and it lacked what the panes have, from a dropped file to the right-click menu and the app\'s styling. It was removed on 11 October 2026, with the four colours it read in each palette (`line_number_bg`, `line_number_fg`, `line_number_current_bg`, `line_number_current_fg`) and the tests that built it.\n\n**What would need to be decided before it is built again.**\n\n- **Which panes.** The input, the output, or both; and whether the output\'s numbers follow the input\'s lines, which a transform keeps and a cleanup that removes lines does not.\n- **On or off, and where the switch lives.** A setting with a default, a menu entry, a shortcut, or all three; and whether the choice is remembered between runs.\n- **How it looks in each mode.** Dark, light and image, from palette entries named for the gutter\'s ground, its numbers and the caret\'s line. In image mode the gutter sits over the background image, as the panes do. Each colour shown drawn, read back from the pixels, and the numbers held to 4.5:1 on their ground.\n- **Wrapped lines.** Whether a line the pane wraps is numbered once, as a line of the file, or on each row it fills.\n- **The caret\'s line.** Marked in the gutter only, or across the pane as well, and how that sits with Find\'s highlights, which are drawn over the text.\n- **Going to a line.** Whether it is offered, and from where: a menu, a shortcut, or Find.\n- **Large files.** The gutter repaints as the view scrolls; how large a file it must stay smooth on.\n- **Where it is built.** Into the panes\' own class, not beside it: dropping a file, the right-click menu, the output\'s undo history, Find\'s highlights and the theme switch all live there.\n\n---\n\n## Built With\n')
    tree.sub('README.md',
             '└── test_rnv_text_transformer.py   # Frozen unittest regression suite\n',
             '└── test_rnv_text_transformer.py   # unittest regression suite\n')
    tree.sub('README.md',
             '| `test_rnv_text_transformer.py` (unittest) | over 300 | Frozen regression suite — core logic, file I/O, transformations, exports, error handling. SHA-pinned and never edited after release. |\n',
             '| `test_rnv_text_transformer.py` (unittest) | over 300 | Regression suite — core logic, file I/O, transformations, exports, error handling. |\n')
    tree.sub('README.md',
             '- **`unittest`** for the frozen core regression suite\n',
             '- **`unittest`** for the core regression suite\n')
    tree.sub('tests/conftest.py',
             'The frozen test_rnv_text_transformer.py at the project root does NOT\n',
             'The unittest suite, test_rnv_text_transformer.py, at the project root does NOT\n')
    tree.sub('run_tests.py',
             '  Suite 1 — test_rnv_text_transformer.py    (398 unittest tests)\n',
             '  Suite 1 — test_rnv_text_transformer.py    (the unittest suite)\n')
    tree.sub('ui/find_replace_dialog.py',
             '    Signals:\n        find_requested: Emitted when find is requested\n        replace_requested: Emitted when replace is requested\n        replace_all_requested: Emitted when replace all is requested\n        output_edited: Emitted after Replace or Replace All has written\n            to the output\n',
             '    Signals:\n        output_edited: Emitted after Replace or Replace All has written\n            to the output\n')
    tree.sub('ui/find_replace_dialog.py',
             '    # Signals\n    find_requested = pyqtSignal(str, dict)  # search_text, options\n    replace_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    replace_all_requested = pyqtSignal(str, str, dict)  # search, replace, options\n    # RNV-RULINGS-2026-10-05, item 10:',
             '    # Signals\n    # RNV-RULINGS-2026-10-11, item 24 (e): find_requested, replace_requested\n    # and replace_all_requested stood here, declared for the main window. It\n    # never connected them, and nothing emitted them: Find and Replace act on\n    # the pane themselves. They went.\n    # RNV-RULINGS-2026-10-05, item 10:')
    tree.sub('ui/find_replace_dialog.py',
             '    _TEXT_CHANGED_STATUS: ClassVar[str] = "Text changed, nothing replaced: match {} of {}"\n',
             '    _TEXT_CHANGED_STATUS: ClassVar[str] = "Text changed, nothing replaced: match {} of {}"\n    # RNV-RULINGS-2026-10-11, item 24 (a): the same, when what changed since\n    # the Find is an option it read: case, whole word or regular expression.\n    _OPTIONS_CHANGED_STATUS: ClassVar[str] = "Options changed, nothing replaced: match {} of {}"\n    _SEARCH_OPTIONS: ClassVar[tuple[str, ...]] = (\'case_sensitive\', \'whole_word\', \'regex\')\n')
    tree.sub('ui/find_replace_dialog.py',
             '        if self._matches_are_stale():\n            if self._find_again():\n                self.status_label.setText(self._TEXT_CHANGED_STATUS.format(\n                    self._current_match_index + 1, len(self._current_matches)))\n            return\n        \n        replace_text = self.replace_input.text()\n        start, end = self._current_matches[self._current_match_index]\n        \n        # Replace the current match\n        cursor = self.target_text_edit.textCursor()\n',
             '        if self._matches_are_stale():\n            said = self._TEXT_CHANGED_STATUS if self._text_changed() else self._OPTIONS_CHANGED_STATUS\n            if self._find_again():\n                self.status_label.setText(said.format(\n                    self._current_match_index + 1, len(self._current_matches)))\n            return\n        \n        replace_text = self.replace_input.text()\n        # RNV-RULINGS-2026-10-11, item 24 (c): with Regular expression on, a\n        # group reference in the replacement is filled in, as Replace All has\n        # always done. Replace wrote \\1 as typed.\n        if self._found_for[1][\'regex\']:\n            try:\n                replace_text = self._expanded(replace_text)\n            except re.error as e:\n                self.status_label.setText(f"Regex error: {e}")\n                return\n        text = self.target_text_edit.toPlainText()\n        start, end = self._in_qt(text, [self._current_matches[self._current_match_index]])[0]\n        \n        # Replace the current match\n        cursor = self.target_text_edit.textCursor()\n')
    tree.sub('ui/find_replace_dialog.py',
             "            else:\n                if options['whole_word']:\n                    flags = 0 if options['case_sensitive'] else re.IGNORECASE\n                    pattern = re.compile(r'\\b' + re.escape(search_text) + r'\\b', flags)\n                    new_text, count = pattern.subn(replace_text, text)\n                elif options['case_sensitive']:\n                    count = text.count(search_text)\n                    new_text = text.replace(search_text, replace_text)\n                else:\n                    # Case insensitive replace\n                    pattern = re.compile(re.escape(search_text), re.IGNORECASE)\n                    new_text, count = pattern.subn(replace_text, text)\n",
             "            else:\n                # RNV-RULINGS-2026-10-11, item 24 (b): with Regular expression\n                # off, the replacement is the text as typed. A string handed to\n                # subn() is read as a template, so a backslash in it was an\n                # escape: C:\\new\\dir was refused as a bad escape, and \\n was\n                # written as a new line. Case sensitive alone never did this.\n                def as_typed(_match: re.Match) -> str:\n                    return replace_text\n                if options['whole_word']:\n                    flags = 0 if options['case_sensitive'] else re.IGNORECASE\n                    pattern = re.compile(r'\\b' + re.escape(search_text) + r'\\b', flags)\n                    new_text, count = pattern.subn(as_typed, text)\n                elif options['case_sensitive']:\n                    count = text.count(search_text)\n                    new_text = text.replace(search_text, replace_text)\n                else:\n                    # Case insensitive replace\n                    pattern = re.compile(re.escape(search_text), re.IGNORECASE)\n                    new_text, count = pattern.subn(as_typed, text)\n")
    tree.sub('ui/find_replace_dialog.py',
             '    def _matches_are_stale(self) -> bool:\n        """\n        Whether the pane no longer holds the text the matches were found in.\n        \n        RNV-RULINGS-2026-10-05, item 11. Asked of the text itself, so it\n        is true exactly when the positions recorded may no longer be the\n        matches\': after typing, or after the output has been written\n        again by a transform or an undo. A highlight painted again, a\n        theme switched or a caret moved changes no text.\n        """\n        return (self.target_text_edit is not None\n                and self.target_text_edit.toPlainText() != self._found_in)\n',
             '    def _matches_are_stale(self) -> bool:\n        """\n        Whether the matches may no longer be the search\'s: the text or an\n        option has changed since the Find.\n        \n        RNV-RULINGS-2026-10-11, item 24 (a): an option ticked or unticked\n        since the Find is a change, as an edit is. It waited for Find to be\n        pressed again, and Find Next went on stepping through the matches of\n        the options as they had been.\n        """\n        return self._text_changed() or self._options_changed()\n    \n    def _text_changed(self) -> bool:\n        """\n        Whether the pane no longer holds the text the matches were found in.\n        \n        RNV-RULINGS-2026-10-05, item 11. Asked of the text itself, so it\n        is true exactly when the positions recorded may no longer be the\n        matches\': after typing, or after the output has been written\n        again by a transform or an undo. A highlight painted again, a\n        theme switched or a caret moved changes no text.\n        """\n        return (self.target_text_edit is not None\n                and self.target_text_edit.toPlainText() != self._found_in)\n    \n    def _options_changed(self) -> bool:\n        """\n        Whether an option the Find read is not what it was then.\n        \n        RNV-RULINGS-2026-10-11, item 24 (a). Ticking one and unticking it\n        again is no change.\n        """\n        if self._found_for is None:\n            return False\n        now, then = self.get_search_options(), self._found_for[1]\n        return any(now[name] != then[name] for name in self._SEARCH_OPTIONS)\n')
    tree.sub('ui/find_replace_dialog.py',
             '        RNV-RULINGS-2026-10-05, item 11. The search is the one Find ran:\n        its text and its options as they were then. Past the last match\n        it comes round to the first, as Find Next does. The view moves\n        only as far as it must to show the match: it is Find that puts\n        the first match at the top.\n        \n        Returns:\n            Whether the text still holds a match\n        """\n        search_text, options = self._found_for\n        text = self.target_text_edit.toPlainText()\n        matches = self._matches_in(text, search_text, options)\n        self._forget_matches()\n        if not matches:\n',
             '        RNV-RULINGS-2026-10-05, item 11. The search is Find\'s: its text,\n        and since RNV-RULINGS-2026-10-11, item 24 (a), the options as they\n        are now. Past the last match it comes round to the first, as Find\n        Next does. The view moves only as far as it must to show the match:\n        it is Find that puts the first match at the top.\n        \n        Returns:\n            Whether the text still holds a match\n        """\n        search_text, _then = self._found_for\n        options = self.get_search_options()\n        text = self.target_text_edit.toPlainText()\n        try:\n            matches = self._matches_in(text, search_text, options)\n        except re.error as e:\n            # an option ticked since the Find can make the text a pattern\n            self._forget_matches()\n            self.status_label.setText(f"Regex error: {e}")\n            self._clear_highlights()\n            return False\n        self._forget_matches()\n        if not matches:\n')
    tree.sub('ui/find_replace_dialog.py',
             '        self._current_matches.extend(matches)\n        self._found_in = text\n        self._found_for = (search_text, options)\n        caret = self.target_text_edit.textCursor().selectionEnd()\n',
             '        self._current_matches.extend(matches)\n        self._found_in = text\n        self._found_for = (search_text, dict(options))\n        caret = self._text_index(text, self.target_text_edit.textCursor().selectionEnd())\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _highlight_colour(self) -> QColor:',
             '    @staticmethod\n    def _in_qt(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:\n        """\n        Spans of a text, as its QTextDocument counts positions.\n        \n        RNV-RULINGS-2026-10-11, item 24 (d). A match is found in the\n        text as Python holds it, where a character outside the basic plane,\n        an emoji, is one position. The document counts it as two, as UTF-16\n        does. Every highlight after one was drawn a place to the left, and\n        Replace wrote over the characters there.\n        """\n        wide = [index for index, char in enumerate(text) if ord(char) > 0xFFFF]\n        if not wide:\n            return list(spans)\n        return [(start + bisect_left(wide, start), end + bisect_left(wide, end)) for start, end in spans]\n    \n    @staticmethod\n    def _text_index(text: str, position: int) -> int:\n        """\n        A document\'s position, as an index of the text Python holds: the\n        other way round from _in_qt().\n        """\n        units = 0\n        for index, char in enumerate(text):\n            if units >= position:\n                return index\n            units += 2 if ord(char) > 0xFFFF else 1\n        return len(text)\n    \n    def _expanded(self, replace_text: str) -> str:\n        """\n        The replacement for the current match with its group references\n        filled in, as Replace All writes it: the match is the scan\'s own.\n        \n        RNV-RULINGS-2026-10-11, item 24 (c). Raises re.error for a group\n        the pattern does not have, as Replace All does.\n        """\n        search_text, options = self._found_for\n        flags = 0 if options[\'case_sensitive\'] else re.IGNORECASE\n        text = self.target_text_edit.toPlainText()\n        match = list(re.compile(search_text, flags).finditer(text))[self._current_match_index]\n        return match.expand(replace_text)\n    \n    def _highlight_colour(self) -> QColor:')
    tree.sub('ui/find_replace_dialog.py',
             '        highlight_color = self._highlight_colour()\n        self._show_highlights(self.target_text_edit, self._current_matches, highlight_color)\n',
             '        highlight_color = self._highlight_colour()\n        spans = self._in_qt(self.target_text_edit.toPlainText(), self._current_matches)\n        self._show_highlights(self.target_text_edit, spans, highlight_color)\n')
    tree.sub('ui/find_replace_dialog.py',
             '        start, end = self._current_matches[self._current_match_index]\n        \n        # Move cursor to current match and select it\n',
             '        start, end = self._in_qt(self.target_text_edit.toPlainText(),\n                                 [self._current_matches[self._current_match_index]])[0]\n        \n        # Move cursor to current match and select it\n')
    tree.sub('ui/find_replace_dialog.py',
             'import re\nfrom typing import TYPE_CHECKING, ClassVar\n',
             'import re\nfrom bisect import bisect_left\nfrom typing import TYPE_CHECKING, ClassVar\n')
    tree.sub('tests/test_dialogs.py',
             '    def test_findreplacedialog_signal_exists(self, qtbot, theme_manager_dark):\n        from ui.find_replace_dialog import FindReplaceDialog\n        dlg = FindReplaceDialog(theme_manager_dark)\n        qtbot.addWidget(dlg)\n        assert hasattr(dlg, "find_requested")\n        assert isinstance(dlg.find_requested, pyqtBoundSignal)\n',
             '    def test_findreplacedialog_signal_exists(self, qtbot, theme_manager_dark):\n        # RNV-RULINGS-2026-10-11, item 24 (e): find_requested, which this\n        # read, went with two more nothing used. output_edited is the one the\n        # dialog declares, and the main window connects it.\n        from ui.find_replace_dialog import FindReplaceDialog\n        dlg = FindReplaceDialog(theme_manager_dark)\n        qtbot.addWidget(dlg)\n        assert hasattr(dlg, "output_edited")\n        assert isinstance(dlg.output_edited, pyqtBoundSignal)\n')
    tree.sub('tests/test_find_follows_the_text.py',
             '6. The search run again is the one Find ran: an option ticked since then\n   waits for Find, as it did before this round.\n',
             "6. The search run again is Find's search text. Since RNV-RULINGS-2026-10-11,\n   item 24 (a), it reads the options as they are: an option changed since\n   the Find is a change, held in tests/test_find_and_replace_do_what_they_say.py.\n")
    tree.sub('tests/test_find_follows_the_text.py',
             'class TestTheSearchRunAgainIsTheOneFindRan:\n\n    def test_an_option_ticked_since_the_find_waits_for_find(self, filled):\n        """As before this round: the options are read when Find is pressed.\n        Whether ticking one should search again is a question of its own."""\n        win = filled\n        win.text_input.setPlainText("Ox ox OX\\n")\n        win.auto_transform_timer.stop()\n        dlg = _opened(win, "_open_find_dialog")\n        dlg._on_find()\n        assert len(dlg._current_matches) == 3\n        dlg.case_sensitive_check.setChecked(True)\n        _type_at(win.text_input, 0, "- ")\n        dlg._on_find_next()\n        assert dlg._current_matches == [(2, 4), (5, 7), (8, 10)], \\\n            "the search run again read the options as they are now, not as Find ran it"\n        dlg._on_find()\n        assert dlg._current_matches == [(5, 7)], "Find itself no longer reads the options as they are"\n        dlg.close()\n\n\n',
             '')
    tree.sub('tests/test_workflow_actions.py',
             '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n',
             '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\nRNV-RULINGS-2026-10-11, item 22. Ruled 2026-10-11: "A". An upload names no\nhidden file.\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nAN UPLOAD NAMES NO HIDDEN FILE. upload-artifact leaves out a file or a\nfolder whose name begins with a dot, unless the step sets\ninclude-hidden-files: true; its default is false, at v4 and at v6. Until\n2026-10-11 three steps, in the picker and the palette manager, named only\n.coverage files: they uploaded nothing, and said so to no one, since each\nwas told to ignore finding nothing. Ruled A: they went. The mixer\'s step\nnamed .coverage beside its two reports, which it uploads; that line went.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. Every path an upload-artifact step names is a file or folder it can\n   upload: none is hidden, unless the step includes hidden files.\n3. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor. It finds\n   every upload step\'s paths, written on one line or as a block.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n#: A path with a part whose name begins with a dot: what upload-artifact leaves out.\nHIDDEN = re.compile(r"(?:^|/)\\.[^./]")\nUPLOAD = "actions/upload-artifact"\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _indent(line: str) -> int:\n    return len(line) - len(line.lstrip())\n\n\ndef _uploads(text: str) -> list:\n    """(line number of its `uses:`, the paths it names, whether it includes\n    hidden files) for every step that uses upload-artifact."""\n    lines = text.splitlines()\n    found = []\n    for number, action, _ref in _uses(text):\n        if action != UPLOAD:\n            continue\n        start = number - 1\n        while start > 0 and not lines[start].lstrip().startswith("- "):\n            start -= 1\n        end = start + 1\n        while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > _indent(lines[start])):\n            end += 1\n        step = lines[start:end]\n        paths, hidden_too = [], False\n        for i, line in enumerate(step):\n            key, _, value = line.strip().partition(":")\n            value = value.strip()\n            if key == "include-hidden-files":\n                hidden_too = value.strip("\'\\"").lower() == "true"\n            elif key == "path" and value in ("|", "|-", ">", ">-"):\n                block = i + 1\n                while block < len(step) and (not step[block].strip() or _indent(step[block]) > _indent(line)):\n                    if step[block].strip():\n                        paths.append(step[block].strip())\n                    block += 1\n            elif key == "path":\n                paths.append(value)\n        found.append((number, paths, hidden_too))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_an_upload_names_no_hidden_file():\n    problems = [f"{name}:{number}: {path}" for name, text in _workflows().items()\n                for number, paths, hidden_too in _uploads(text) if not hidden_too\n                for path in paths if HIDDEN.search(path)]\n    assert not problems, (\n        "upload-artifact leaves hidden files out unless the step sets include-hidden-files: "\n        "true, so these upload nothing:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n\n    for name, text in workflows.items():\n        steps = [n for n, action, _ref in _uses(text) if action == UPLOAD]\n        assert [n for n, _p, _h in _uploads(text)] == steps, f"{name}: the reader misses an upload step"\n        assert all(paths for _n, paths, _h in _uploads(text)), f"{name}: the reader finds an upload with no path"\n    uploads = ("    steps:\\n"\n               "      - name: Two reports and the data\\n"\n               "        # a comment\\n"\n               "        uses: actions/upload-artifact@v6\\n"\n               "        with:\\n"\n               "          name: coverage\\n"\n               "          path: |\\n"\n               "            htmlcov/\\n"\n               "            .coverage\\n"\n               "          retention-days: 14\\n"\n               "      - uses: actions/upload-artifact@v6\\n"\n               "        with:\\n"\n               "          path: reports/.hidden.txt\\n"\n               "          include-hidden-files: true\\n"\n               "      - name: One line\\n"\n               "        uses: actions/upload-artifact@v6\\n"\n               "        with: {path: dist/}\\n")\n    assert _uploads(uploads) == [(4, ["htmlcov/", ".coverage"], False), (11, ["reports/.hidden.txt"], True),\n                                 (16, [], False)], _uploads(uploads)\n    assert [p for p in ("htmlcov/", ".coverage", ".coverage.*", "reports/.hidden.txt", "./out", "../x")\n            if HIDDEN.search(p)] == [".coverage", ".coverage.*", "reports/.hidden.txt"]\n')
    tree.sub('tests/test_readme_test_counts.py',
             '"""The README says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 786 tests and pytest collected 1,178.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests the README states is a floor. An exact count,\n   written as a sentence, as a badge or as a cell of the suites\' table, is\n   how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the README\'s number.\n3. The reader is looking. It finds the README\'s floors, and it tells an\n   exact count from a floor in each of the three ways one is written.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nREADME = ROOT / "README.md"\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_text_transformer.py"\n\n#: The README states this many floors. Fewer and the reader has gone blind,\n#: or the README has stopped saying.\nMIN_FLOORS = 6\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nCELL = re.compile(rf"\\|\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\s*(?=\\|)", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\nA_SUITE_ROW = re.compile(r"unittest|pytest|\\btests\\b|coverage", re.I)\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        seen = set()\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):\n            for match in CELL.finditer(line):\n                add(match, bool(match.group("over")))\n    return found\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_the_readme_states_is_a_floor():\n    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in\n             _claims(README.read_text(encoding="utf-8")) if not floor]\n    assert not exact, (\n        "the README states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "the README promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the README\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]\n    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Ctrl+T | 12 | a row of some other table |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (4, 398, False, "root"),\n        (5, 600, True, "pytest"),\n    ], _claims(sample)\n',
             '"""Every document says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\nRNV-RULINGS-2026-10-11, item 23. Ruled 2026-10-11: "Yes". The other\ndocuments that state how many tests there are take the README\'s floors, and\nthis guard reads them too.\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 786 tests and pytest collected 1,178.\ntests/README.md, then tests/tests_README.md, said 786 as well, and 398 for the root suite.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nA DATED RECORD IS LEFT AS IT WAS. A section that records the counts at a\nmoment past, such as the log of the campaign that built the suite, says\nwhat was true then; a floor would make it say something else. Each such\nsection is named in RECORDS, and its counts are not read.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests a document in DOCUMENTS states, outside a dated\n   record, is a floor. An exact count, written as a sentence, as a badge\n   or as a cell of a table of suites, is how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the document\'s number.\n3. The reader is looking. It finds each document\'s floors, and every dated\n   record it is told to leave alone, still holding counts; it tells an\n   exact count from a floor in each of the three ways one is written; and\n   it reads a table\'s cell for its column\'s heading alone, as for its row\'s\n   label alone.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_text_transformer.py"\n\n#: Every document that says how many tests there are, and how many floors it\n#: states. Fewer and the reader has gone blind, or the document has stopped\n#: saying. The README is the first.\nDOCUMENTS = {\'README.md\': 6, \'tests/README.md\': 4}\n\n#: Sections that are dated records, by the document and the heading\'s text.\n#: Their counts are what was true when they were written, and are not read.\nRECORDS = {}\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\n#: A table\'s cell holds a count of tests when its column is headed so, or\n#: when its row is labelled so ("Total tests"). A cell is its number alone.\nSEPARATOR = re.compile(r"^\\s*\\|?(?:\\s*:?-{2,}:?\\s*\\|)+\\s*:?-*:?\\s*$")\nCOUNT_COLUMN = re.compile(r"\\b(?:tests?|count)\\b", re.I)\nTEST_ROW = re.compile(r"\\btests?\\b|unittest|pytest", re.I)\nCELL = re.compile(rf"^\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\*?\\s*$", re.I)\nHEADING = re.compile(r"^(?P<level>#{1,6})\\s+(?P<text>.+?)\\s*$")\nFENCE = re.compile(r"^\\s*(```|~~~)")\n\n\ndef _cells(line: str) -> list:\n    """(where it starts in the line, its text) for each cell of a table\'s row."""\n    edges = [i for i, ch in enumerate(line) if ch == "|"]\n    return [(a + 1, line[a + 1:b]) for a, b in zip(edges, edges[1:])]\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    lines = text.splitlines()\n    header = None\n    for number, line in enumerate(lines, 1):\n        seen = set()\n        in_table = line.lstrip().startswith("|")\n        if not in_table:\n            header = None\n        elif SEPARATOR.match(line):\n            continue\n        elif number < len(lines) and SEPARATOR.match(lines[number]):\n            header = [cell.strip() for _at, cell in _cells(line)]\n            continue\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if in_table and header is not None:\n            cells = _cells(line)\n            labelled = bool(cells) and bool(TEST_ROW.search(cells[0][1]))\n            for column, (at, cell) in enumerate(cells):\n                match = CELL.match(cell)\n                headed = column < len(header) and bool(COUNT_COLUMN.search(header[column]))\n                if match and column and (headed or labelled):\n                    add(_Shifted(match, at), bool(match.group("over")))\n    return found\n\n\nclass _Shifted:\n    """A match in a cell, read as a match in its line."""\n\n    def __init__(self, match, at: int) -> None:\n        self.match, self.at = match, at\n\n    def start(self, group: str) -> int:\n        return self.at + self.match.start(group)\n\n    def group(self, name: str):\n        return self.match.group(name)\n\n\ndef _records(text: str, headings) -> dict:\n    """heading -> the line numbers of its section, for each dated record a\n    text holds: from its heading to the next heading of its level or above.\n    A heading inside a fenced block of code is not one."""\n    lines, fenced, found = text.splitlines(), False, {}\n    marks = []\n    for number, line in enumerate(lines, 1):\n        if FENCE.match(line):\n            fenced = not fenced\n            continue\n        match = None if fenced else HEADING.match(line)\n        if match:\n            marks.append((number, len(match.group("level")), match.group("text")))\n    for i, (number, level, title) in enumerate(marks):\n        if title in headings:\n            end = next((n for n, lv, _t in marks[i + 1:] if lv <= level), len(lines) + 1)\n            found.setdefault(title, []).append(range(number, end))\n    return found\n\n\ndef _read(rel: str) -> str:\n    return (ROOT / rel).read_text(encoding="utf-8-sig")\n\n\ndef _stated(rel: str) -> list:\n    """The claims a document makes, outside its dated records."""\n    text = _read(rel)\n    skipped = set()\n    for spans in _records(text, RECORDS.get(rel, ())).values():\n        for span in spans:\n            skipped.update(span)\n    return [claim for claim in _claims(text) if claim[0] not in skipped]\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_a_document_states_is_a_floor():\n    exact = [f"{rel}:{line}: {n:,}" for rel in DOCUMENTS\n             for line, n, floor, _s in _stated(rel) if not floor]\n    assert not exact, (\n        "a document states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N. A section that records the "\n        "counts at a moment past is named in RECORDS instead.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"{rel}:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for rel in DOCUMENTS for line, n, floor, suites in _stated(rel)\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "a document promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the document\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    readme = next(iter(DOCUMENTS))\n    assert readme == "README.md", f"the README is not the first document: {list(DOCUMENTS)}"\n    for rel, least in DOCUMENTS.items():\n        floors = [c for c in _stated(rel) if c[2]]\n        assert len(floors) >= least, f"the reader finds {len(floors)} floors in {rel}, not {least}"\n    floors = [c for c in _stated(readme) if c[2]]\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    for rel, headings in RECORDS.items():\n        text = _read(rel)\n        found = _records(text, headings)\n        for heading in headings:\n            spans = found.get(heading, [])\n            assert len(spans) == 1, f"{rel}: the dated record {heading!r} is there {len(spans)} times"\n            held = [c for c in _claims(text) if c[0] in spans[0]]\n            assert held, f"{rel}: the dated record {heading!r} holds no count: it needs no exemption"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              "| Suite | Tests | Purpose |\\n"\n              "|---|---:|---|\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | the root suite |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Both, together | over 1,000 | read for its column alone |\\n"\n              "\\n"\n              "| Metric | Value |\\n"\n              "|---|---|\\n"\n              "| Total tests | **1,641** |\\n"\n              "| Modules at 90% coverage | 12 |\\n"\n              "| Shortcut | Count |\\n"\n              "\\n"\n              "| # | Item | Status |\\n"\n              "|---|---|---|\\n"\n              "| 1 | pytest-qt with qtbot | Done |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (6, 398, False, "root"),\n        (7, 600, True, "pytest"),\n        (8, 1000, True, "all"),\n        (12, 1641, False, "all"),\n    ], _claims(sample)\n    record = ("## Now\\nover 300 unittest tests\\n## The log\\n### Phase 1\\n| 1 | unittest | 400 |\\n"\n              "```\\n# not a heading\\n```\\n## After\\n12 tests\\n")\n    assert _records(record, ("The log",)) == {"The log": [range(3, 9)]}, _records(record, ("The log",))\n')
    if (tree.root / 'tests/README.md').exists():
        raise Stop('tests/README.md' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/README.md', "# RNV Text Transformer — Test Suite\n\nThe test suite combines two complementary frameworks: a `unittest` suite for the\ncore regression tests, and a `pytest` suite for the broader test plan covering UI\ninteractions, property-based tests, snapshot tests, benchmarks, and gap-fill\ncoverage.\n\nBoth suites run under a single coverage report via `run_tests.py`.\n\n---\n\n## Quick start\n\n```bash\n# Run everything (both suites + combined coverage report)\npython run_tests.py\n\n# Run only the pytest suite\npython -m pytest tests/\n\n# Run only the unittest suite\npython -m unittest test_rnv_text_transformer\n\n# Run a single pytest file\npython -m pytest tests/test_main_window.py -v\n\n# Run with benchmarks (off by default)\npython -m pytest tests/test_benchmarks.py --benchmark-enable\n```\n\nOn Windows, `python -m pytest` is required (not `pytest tests/...`) so the\nworking directory is added to `sys.path`.\n\n---\n\n## Test inventory\n\n### Regression suite (`unittest`)\n\n| File | Tests | Purpose |\n|------|------:|---------|\n| `test_rnv_text_transformer.py` | over 300 | Core regression suite — covers logic, file I/O, transformations, exports, error handling. |\n\n### Pytest suite (`tests/`)\n\n| File | Purpose |\n|------|---------|\n| `test_main_window.py` | MainWindow construction, transformation flow, file ops, undo/redo, cleanup, theme cycling, signal handlers |\n| `test_compare_dialog.py` | Compare & merge UI — ChangeWidget signals, navigation, accept/reject all, export, merge signal |\n| `test_preset_dialog.py` | StepEditorWidget + PresetDialog + PresetManagerDialog interactions |\n| `test_find_replace_dialog.py` | Find/replace modes (literal, case-sensitive, whole-word, regex), navigation, highlighting |\n| `test_watch_folder_dialog.py` | RuleEditWidget + WatchFolderDialog — add/remove rules, start/stop watcher, activity log |\n| `test_regex_builder_dialog.py` | Pattern validation, flag computation, match/group tables, replace preview |\n| `test_encoding_dialog.py` | Encoding detection, mojibake fix, conversion preview, EncodingWidget signal |\n| `test_batch_dialog.py` | Source/output browse, file count, start validation, progress + finished handlers |\n| `test_dialogs.py` | Construction + signal smoke tests for every dialog |\n| `test_widgets.py` | Custom widgets (ImageButton, DragDropTextEdit) |\n| `test_workers.py` | QThread workers — FileLoaderThread, TextTransformThread, BatchWorkerThread, FolderWatcher |\n| `test_cli.py` | CLI command dispatch, validation errors, output writing, argument parsing |\n| `test_logic_gap_fill.py` | Pure-logic coverage gap-fill across FileHandler, DialogHelper, ErrorHandler, PresetManager, FolderWatcher, ExportManager, ThemeManager |\n| `test_properties.py` | Hypothesis property-based tests for transformations, cleaning, diffs, statistics |\n| `test_snapshots.py` | Syrupy snapshot tests for dialog stylesheets and export formats |\n| `test_benchmarks.py` | Performance benchmarks (import time, stylesheet cache, transforms, diff, file loading) |\n\nThese are the suite's first files. Files added since are not listed here; each opens with a\ndocstring that says what it holds.\n\n**Total: over 1,000 tests** (over 300 unittest tests and over 600 pytest tests, snapshot tests and benchmarks among them)\n\n---\n\n## Coverage\n\nThe project tracks coverage with `coverage.py` and reports it on every run.\n\nCurrent landing: **~76% on Windows** (Python 3.13).\n\nPer-module highlights (above 85%):\n- `core/text_transformer.py` — 99.4%\n- `core/text_statistics.py` — 100%\n- `cli/__init__.py` — 100%\n- `utils/dialog_styles.py` — 94.2%\n- `utils/settings_manager.py` — 91.9%\n- `core/regex_patterns.py` — 88.9%\n- `utils/dialog_helper.py` — 88.5%\n- `ui/find_replace_dialog.py` — 87.0%\n- `core/preset_manager.py` — 87.0%\n- `ui/watch_folder_dialog.py` — 86.7%\n- `core/text_cleaner.py` — 85.6%\n- `core/export_manager.py` — 85.7%\n- `utils/base_dialog.py` — 86.0%\n\nModules with lower coverage are documented limitations:\n- QThread `run()` bodies don't instrument under `coverage.py` (affects `batch_dialog`, `encoding_dialog`, `compare_dialog` scroll-sync handlers)\n- CSS stylesheet builders in `main_window.py` are exercised transitively but not per-branch (~315 statements)\n- `drag_drop_text_edit.py` event handlers (Qt drag events are hard to simulate)\n\n---\n\n## Conventions\n\n**Fixtures.** Common fixtures live in `tests/conftest.py`:\n- `qapp` — single `QApplication` instance shared across tests\n- `qtbot` — pytest-qt helper (from the plugin)\n- `main_window` — fully-constructed `MainWindow` with isolated `QSettings`\n- `tmp_settings` — temporary `QSettings` scope so tests don't pollute the user's real settings\n- `tmp_workdir` — fresh temporary directory per test\n\n**Modal dialog mocking.** `QFileDialog` and `QMessageBox` are mocked via\n`monkeypatch` and `unittest.mock.patch.object` to avoid blocking the test\nthread on modal child dialogs.\n\n**QThread handler testing.** Worker threads (`FileLoaderThread`,\n`TextTransformThread`, `BatchWorkerThread`, `DetectionThread`) have their\nhandlers driven directly with hand-emitted signal payloads rather than\nspinning up the thread. This sidesteps the `coverage.py` limitation around\nQThread bodies while still exercising the dialog's response code paths.\n\n**Snapshot tests.** Use `syrupy` for stylesheets and export output formats.\nRe-record snapshots after intentional changes with:\n\n```bash\npython -m pytest tests/test_snapshots.py --snapshot-update\n```\n\n**Property tests.** Use `hypothesis` with the `default` profile. Re-run a\nspecific failing seed:\n\n```bash\npython -m pytest tests/test_properties.py -k test_name --hypothesis-seed=12345\n```\n\n---\n\n## Adding new tests\n\n1. **Smoke tests** for new dialogs → add to `test_dialogs.py`\n2. **Interaction tests** for new dialogs → create `test_<dialog_name>.py`\n3. **Pure logic** with no Qt dependencies → add to `test_logic_gap_fill.py`\n4. **Properties / invariants** → add to `test_properties.py`\n5. **New worker threads** → add to `test_workers.py`\n6. **CLI commands** → add to `test_cli.py`\n\nEach test file follows the same skeleton: a docstring header summarizing\nscope and coverage targets, fixtures at the top, then one test class per\ncomponent under test.\n\n---\n\n## Production bugs caught by this suite\n\n| # | Bug | Found by | Severity |\n|---|-----|----------|----------|\n| 1 | `remove_duplicate_lines` non-idempotent for non-LF separators | Property test | Logic |\n| 2 | 4 sibling cleanup functions had the same root cause | Property test | Logic |\n| 3 | `preset_dialog._setup_ui` called wrong method name on `TextCleaner` | StepEditorWidget interaction test | Crash |\n| 4 | `watch_folder_dialog._load_rule` silently reset `rule.file_patterns` | RuleEditWidget interaction test | **Data loss** |\n\nEach bug has a dedicated regression guard test that fails against the buggy\nproduction code and passes against the fix. See the commit history for\ndetails on each fix.\n\n---\n\n## CI\n\nTests run on GitHub Actions for both Linux (Ubuntu) and Windows on every push\nand pull request. See `.github/workflows/tests.yml`.\n\nStatus badges in the project README reflect the most recent CI run per platform.\n")
    if (tree.root / 'tests/test_find_and_replace_do_what_they_say.py').exists():
        raise Stop('tests/test_find_and_replace_do_what_they_say.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_find_and_replace_do_what_they_say.py', '"""Find and Replace do what their controls say.\n\nRNV-RULINGS-2026-10-11, item 24. Ruled 2026-10-11: "Yes fix a to d remove e".\n\nWHAT WAS THERE. Five things the dialog did as shipped, measured on\n2026-10-05:\n\n(a) An option ticked after a Find (Case sensitive, Whole word, Regular\n    expression) was not read until Find was pressed again. Find Next went on\n    stepping through the matches of the options as they had been.\n(b) Replace All, with Regular expression off and Case sensitive off, which is\n    the default, read the replacement as a regular expression\'s template: a\n    backslash in it was an escape. C:\\\\new\\\\dir was refused as a bad escape.\n(c) With Regular expression on, Replace wrote a group reference such as \\\\1\n    as typed, and Replace All filled it in.\n(d) A character outside the basic plane, an emoji, put every highlight after\n    it one place to the left, and Replace wrote over the characters there.\n    Python counts such a character as one position; the text pane, as two.\n(e) The dialog declared three signals that nothing emitted or connected.\n\nWHAT IS THERE NOW. (a) An option changed since the Find is a change, as an\nedit is: Find Next runs Find\'s search again with the options as they are,\nand Replace shows the match first and says so. (b) With Regular expression\noff, the replacement is the text as typed. (c) Replace fills the groups in,\nas Replace All does. (d) Positions are counted as the pane counts them.\n(e) The three signals went.\n\nWHAT THIS GUARD HOLDS. Each of the five, driven through the main window\'s\nown Find and Replace. That the search is run again only when something has\nchanged is held in tests/test_find_follows_the_text.py.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nimport pytest\nfrom PyQt6.QtTest import QTest\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.base_dialog import BaseDialog\nfrom ui.find_replace_dialog import FindReplaceDialog\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nEMOJI = "\\U0001F600"\n\n\ndef _opened(win, opener: str, needle: str) -> FindReplaceDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    new[0].find_input.setText(needle)\n    return new[0]\n\n\ndef _selected(edit) -> str:\n    return edit.textCursor().selectedText()\n\n\ndef _highlighted(edit) -> list:\n    return [s.cursor.selectedText() for s in edit.extraSelections() if s.cursor.hasSelection()]\n\n\ndef _counting_searches(monkeypatch) -> list:\n    ran, scan = [], FindReplaceDialog._matches_in\n\n    def counted(text, search_text, options):\n        ran.append(1)\n        return scan(text, search_text, options)\n    monkeypatch.setattr(FindReplaceDialog, "_matches_in", staticmethod(counted))\n    return ran\n\n\n@pytest.fixture\ndef pane(main_window):\n    """The main window, auto-transform off; a test puts its own text in the input."""\n    win = main_window\n    win.settings_manager.save_auto_transform(False)\n    win.auto_transform_timer.stop()\n\n    def holding(text: str):\n        win.text_input.setPlainText(text)\n        win.auto_transform_timer.stop()\n        QApplication.processEvents()\n        return win\n    yield holding\n    win.auto_transform_timer.stop()\n\n\nclass TestAnOptionChangedSinceTheFindIsAChange:\n    """(a)"""\n\n    def test_find_next_searches_again_with_the_options_as_they_are(self, pane):\n        win = pane("Ox ox OX\\n")\n        dlg = _opened(win, "_open_find_dialog", "ox")\n        dlg._on_find()\n        assert dlg._current_matches == [(0, 2), (3, 5), (6, 8)]\n        dlg.case_sensitive_check.setChecked(True)\n        dlg._on_find_next()\n        assert dlg._current_matches == [(3, 5)], \\\n            "Find Next stepped through the matches of the options as they were at the Find"\n        assert _selected(win.text_input) == "ox" and _highlighted(win.text_input) == ["ox"]\n        assert dlg.status_label.text() == "Match 1 of 1"\n        dlg.close()\n\n    def test_replace_shows_the_match_first_and_says_why(self, pane):\n        win = pane("Ox ox OX\\n")\n        dlg = _opened(win, "_open_replace_dialog", "ox")\n        dlg.replace_input.setText("no")\n        dlg._on_find()\n        dlg.case_sensitive_check.setChecked(True)\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "Ox ox OX\\n", "Replace wrote on the press that found a change"\n        assert dlg.status_label.text() == "Options changed, nothing replaced: match 1 of 1"\n        assert _selected(win.text_input) == "ox"\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "Ox no OX\\n"\n        dlg.close()\n\n    def test_an_option_ticked_and_unticked_again_is_no_change(self, pane, monkeypatch):\n        win = pane("Ox ox OX\\n")\n        dlg = _opened(win, "_open_find_dialog", "ox")\n        dlg._on_find()\n        ran = _counting_searches(monkeypatch)\n        dlg.whole_word_check.setChecked(True)\n        dlg.whole_word_check.setChecked(False)\n        dlg._on_find_next()\n        assert ran == [] and dlg._current_match_index == 1, "an option put back as it was is no change"\n        dlg.close()\n\n    def test_a_find_text_that_becomes_a_bad_pattern_says_so(self, pane):\n        win = pane("a(b) a(b)\\n")\n        dlg = _opened(win, "_open_find_dialog", "a(")\n        dlg._on_find()\n        assert len(dlg._current_matches) == 2\n        dlg.regex_check.setChecked(True)\n        dlg._on_find_next()\n        assert dlg.status_label.text().startswith("Regex error"), dlg.status_label.text()\n        assert dlg._current_matches == [] and _highlighted(win.text_input) == []\n        dlg.close()\n\n\nAS_TYPED = (r"C:\\new\\dir", r"one\\ntwo", r"\\1")\nMODES = ((False, False, "the default"), (False, True, "whole word"), (True, False, "case sensitive"),\n         (True, True, "case sensitive, whole word"))\n\n\nclass TestReplaceAllWritesTheReplacementAsTyped:\n    """(b)"""\n\n    def test_with_regular_expression_off(self, pane):\n        """Every way of searching without a pattern, and three replacements\n        a template would read otherwise: a bad escape, an escape it knows, and\n        a group reference."""\n        win = pane("")\n        dlg = _opened(win, "_open_replace_dialog", "here")\n        wrong = []\n        for case, whole, called in MODES:\n            dlg.case_sensitive_check.setChecked(case)\n            dlg.whole_word_check.setChecked(whole)\n            for replacement in AS_TYPED:\n                pane("path here, and here\\n")\n                dlg.replace_input.setText(replacement)\n                dlg._on_replace_all()\n                got = win.text_input.toPlainText()\n                if got != f"path {replacement}, and {replacement}\\n" or dlg.status_label.text() != "Replaced 2 occurrence(s)":\n                    wrong.append(f"{called}, {replacement!r}: {got!r} ({dlg.status_label.text()})")\n        assert not wrong, "Replace All read the replacement as a pattern\'s template:\\n  " + "\\n  ".join(wrong)\n        dlg.close()\n\n    def test_replace_writes_it_as_typed_too(self, pane):\n        win = pane("path here\\n")\n        dlg = _opened(win, "_open_replace_dialog", "here")\n        dlg.replace_input.setText(r"C:\\new\\dir")\n        dlg._on_find()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "path C:\\\\new\\\\dir\\n"\n        dlg.close()\n\n\nclass TestReplaceFillsInTheGroupsAsReplaceAllDoes:\n    """(c)"""\n\n    def test_the_two_write_the_same(self, pane):\n        win = pane("ab ab\\n")\n        dlg = _opened(win, "_open_replace_dialog", "(a)(b)")\n        dlg.regex_check.setChecked(True)\n        dlg.replace_input.setText(r"\\2\\1")\n        dlg._on_find()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "ba ab\\n", \\\n            f"Replace wrote {win.text_input.toPlainText()!r}: the group references as typed"\n        dlg._on_replace_all()\n        assert win.text_input.toPlainText() == "ba ba\\n"\n        dlg.close()\n\n    def test_a_group_the_pattern_does_not_have_is_refused_by_both(self, pane):\n        win = pane("ab ab\\n")\n        dlg = _opened(win, "_open_replace_dialog", "(a)(b)")\n        dlg.regex_check.setChecked(True)\n        dlg.replace_input.setText(r"\\3")\n        dlg._on_find()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == "ab ab\\n" and dlg.status_label.text().startswith("Regex error")\n        dlg._on_replace_all()\n        assert win.text_input.toPlainText() == "ab ab\\n" and dlg.status_label.text().startswith("Regex error")\n        dlg.close()\n\n\nclass TestAMatchAfterAnEmojiIsWhereItIs:\n    """(d)"""\n\n    TEXT = f"{EMOJI} fox, {EMOJI}{EMOJI} the fox\\n"\n\n    @pytest.mark.parametrize("regex", [False, True], ids=("text", "regular expression"))\n    def test_find_and_find_next_select_the_match(self, pane, regex):\n        win = pane(self.TEXT)\n        dlg = _opened(win, "_open_find_dialog", "f.x" if regex else "fox")\n        dlg.regex_check.setChecked(regex)\n        dlg._on_find()\n        assert _selected(win.text_input) == "fox", f"Find selected {_selected(win.text_input)!r}"\n        assert _highlighted(win.text_input) == ["fox", "fox"], _highlighted(win.text_input)\n        dlg._on_find_next()\n        assert _selected(win.text_input) == "fox", f"Find Next selected {_selected(win.text_input)!r}"\n        dlg.close()\n\n    def test_replace_writes_over_the_match(self, pane):\n        win = pane(self.TEXT)\n        dlg = _opened(win, "_open_replace_dialog", "fox")\n        dlg.replace_input.setText("cat")\n        dlg._on_find()\n        dlg._on_find_next()\n        dlg._on_replace()\n        assert win.text_input.toPlainText() == f"{EMOJI} fox, {EMOJI}{EMOJI} the cat\\n", \\\n            repr(win.text_input.toPlainText())\n        dlg.close()\n\n    def test_after_typing_find_next_goes_to_the_next_match_after_the_caret(self, pane):\n        """Typed right before the last match, after three emoji: the pane\n        counts the caret three places further on than Python does, so a caret\n        read as the pane counts it is past the match, and Find Next comes\n        round to the first."""\n        win = pane(self.TEXT)\n        dlg = _opened(win, "_open_find_dialog", "fox")\n        dlg._on_find()\n        cursor = win.text_input.textCursor()\n        cursor.setPosition(len(f"{EMOJI} fox, {EMOJI}{EMOJI} the ".encode("utf-16-le")) // 2)\n        win.text_input.setTextCursor(cursor)\n        QTest.keyClicks(win.text_input, "x")\n        QApplication.processEvents()\n        dlg._on_find_next()\n        assert _selected(win.text_input) == "fox"\n        assert dlg.status_label.text() == "Match 2 of 2", dlg.status_label.text()\n        dlg.close()\n\n\nclass TestTheDialogDeclaresTheSignalsItUses:\n    """(e)"""\n\n    def test_each_signal_it_declares_it_emits(self):\n        source = (ROOT / "ui" / "find_replace_dialog.py").read_text(encoding="utf-8-sig")\n        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "FindReplaceDialog")\n        declared = [t.id for node in cls.body if isinstance(node, ast.Assign)\n                    and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "pyqtSignal"\n                    for t in node.targets]\n        assert declared == ["output_edited"], f"the dialog declares {declared}"\n        for name in declared:\n            assert re.search(rf"\\.{name}\\.emit\\(", source), f"{name} is declared and never emitted"\n        for gone in ("find_requested", "replace_requested", "replace_all_requested"):\n            assert not hasattr(FindReplaceDialog, gone), f"{gone} is back"\n')
    tree.delete('ui/line_number_text_edit.py')
    tree.delete('tests/tests_README.md')


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
    check_moves([('RNV_Text_Transformer.py', [], [], []), ('run_tests.py', [], [], []), ('test_rnv_text_transformer.py', [], [], ['TestDialogStyleManager.test_required_keys_present_dark()']), ('tests/conftest.py', [], [], []), ('tests/test_contrast_pairs.py', [], [], ['test_light_mode_has_exactly_two_golds()']), ('tests/test_dialogs.py', [], [], ['TestFindReplaceDialog.test_findreplacedialog_signal_exists()']), ('tests/test_find_follows_the_text.py', [], ['TestTheSearchRunAgainIsTheOneFindRan.test_an_option_ticked_since_the_find_waits_for_find()'], []), ('tests/test_ladder_and_plate.py', [], [], ['PINNED_ENTRIES', 'STATIC_EE_KEYS', 'test_the_maps_this_file_iterates_are_not_empty()']), ('tests/test_readme_test_counts.py', ['COUNT_COLUMN', 'DOCUMENTS', 'FENCE', 'HEADING', 'RECORDS', 'SEPARATOR', 'TEST_ROW', '_Shifted.__init__()', '_Shifted.group()', '_Shifted.start()', '_cells()', '_read()', '_records()', '_stated()', 'test_every_number_of_tests_a_document_states_is_a_floor()'], ['A_SUITE_ROW', 'MIN_FLOORS', 'README', 'test_every_number_of_tests_the_readme_states_is_a_floor()'], ['CELL', '_claims()', 'test_every_floor_is_true()', 'test_the_reader_is_looking()']), ('tests/test_widgets.py', [], ['TestLineNumberQTextEdit.test_lnqtextedit_instantiates()', 'TestLineNumberQTextEdit.test_lnqtextedit_setplaintext_updates()', 'TestLineNumberTextEdit.test_lntextedit_instantiates()', 'TestLineNumberTextEdit.test_lntextedit_line_number_area_attached()', 'TestLineNumberTextEdit.test_lntextedit_setplaintext_updates_content()', 'TestLineNumberTextEdit.test_lntextedit_textmodified_signal_exists()'], []), ('tests/test_workflow_actions.py', ['HIDDEN', 'UPLOAD', '_indent()', '_uploads()', 'test_an_upload_names_no_hidden_file()'], [], ['test_the_reader_is_looking()']), ('ui/__init__.py', [], [], ['__all__']), ('ui/find_replace_dialog.py', ['FindReplaceDialog._OPTIONS_CHANGED_STATUS', 'FindReplaceDialog._SEARCH_OPTIONS', 'FindReplaceDialog._expanded()', 'FindReplaceDialog._in_qt()', 'FindReplaceDialog._options_changed()', 'FindReplaceDialog._text_changed()', 'FindReplaceDialog._text_index()'], ['FindReplaceDialog.find_requested', 'FindReplaceDialog.replace_all_requested', 'FindReplaceDialog.replace_requested'], ['FindReplaceDialog._find_again()', 'FindReplaceDialog._highlight_all_matches()', 'FindReplaceDialog._highlight_current_match()', 'FindReplaceDialog._matches_are_stale()', 'FindReplaceDialog._on_replace()', 'FindReplaceDialog._on_replace_all()']), ('utils/colors.py', [], [], []), ('utils/dialog_styles.py', [], [], ['DialogStyleManager.DARK', 'DialogStyleManager.LIGHT'])])
    # ---- item 7: the editor is gone, and nothing in the application names it or its colours
    assert "ui/line_number_text_edit.py" in tree.deleted, "the line-number editor is still there"
    for rel, text in app_sources():
        found = sorted(n for n in names_in(text) if n.startswith(("LineNumber", "line_number_")) or n == "line_number_text_edit")
        assert not found, f"{rel} still names {found}"
    styles = tree.read("utils/dialog_styles.py")
    assert "'line_number_" not in styles, "a palette still holds the editor's colours"
    readme = tree.read("README.md")
    assert readme.count("\n## Considered for Later\n") == 1 and "### Line numbers in the text panes" in readme, \
        "the README does not hold the write-up of the line numbers"
    assert "- [Considered for Later](#considered-for-later)\n" in readme and "line_number_text_edit.py   #" not in readme, \
        "the README's contents miss the write-up, or its tree still lists the editor"
    assert "- Line numbers toggle" not in tree.read("RNV_Text_Transformer.py"), "the header still lists the line numbers"
    # ---- item 21: nothing says the root suite is frozen, pinned or never edited
    for rel in ("README.md", "tests/README.md", "tests/conftest.py"):
        low = tree.read(rel).lower()
        said = [w for w in ("frozen", "sha-pinned", "sha-256", "404d6b93", "never edited") if w in low]
        assert not said, f"{rel} still says {said}"
    # ---- item 25: the tests' README is tests/README.md, which the README's links name
    assert "tests/tests_README.md" in tree.deleted and "tests/README.md" in tree.files, "the tests' README is not renamed"
    assert readme.count("tests/README.md") == 3, "the README does not point to tests/README.md where it did"
    # ---- item 23: the banner names no number (COMMON holds the documents)
    assert "(the unittest suite)" in tree.read("run_tests.py") and "398 unittest tests" not in tree.read("run_tests.py"), \
        "the runner's banner still counts"
    # ---- item 24: Find and Replace
    dialog = tree.read("ui/find_replace_dialog.py")
    have = code(dialog)
    for gone in ("find_requested", "replace_requested", "replace_all_requested"):
        assert f"FindReplaceDialog.{gone}" not in have and gone not in names_in(tree.read("tests/test_dialogs.py")), \
            f"(e) {gone} is still declared, or a test still reads it"
    assert "self.get_search_options()" in have["FindReplaceDialog._find_again()"], "(a) the search run again reads the old options"
    assert "self._options_changed()" in have["FindReplaceDialog._matches_are_stale()"], "(a) an option changed is not a change"
    replace_all = have["FindReplaceDialog._on_replace_all()"]
    assert replace_all.count("pattern.subn(as_typed, text)") == 2 and "pattern.subn(replace_text, text)" in replace_all, \
        "(b) a replacement is still read as a template with Regular expression off, or no longer with it on"
    assert "self._expanded(replace_text)" in have["FindReplaceDialog._on_replace()"], "(c) Replace does not fill groups in"
    for name in ("_highlight_all_matches", "_highlight_current_match", "_on_replace"):
        assert "self._in_qt(" in have[f"FindReplaceDialog.{name}()"], f"(d) {name} uses positions as Python counts them"
    assert "self._text_index(" in have["FindReplaceDialog._find_again()"], "(d) the caret is not counted as the text is"
    assert "TestTheSearchRunAgainIsTheOneFindRan" not in tree.read("tests/test_find_follows_the_text.py"), \
        "the item 11 guard still holds that an option waits for Find"

    # ================= the two guards every app carries: the shared files, unchanged
    import hashlib
    for rel, sha in ((ACTIONS_GUARD, '319a0347a68250459ab8205513fbfb0039660572decaf2e3a3bde9dff6936a09'), (COUNTS_GUARD, '7115592971f45cd2dab3f57d844a296d33036b6348d732c8f8bb086dd8368d34')):
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == sha, f"{rel} is not the file this round writes: {got[:12]}"
    assert SENTINEL in tree.read(COUNTS_GUARD), "the sentinel is not in the count guard"

    # ================= item 22's rule, as the workflows will read: no upload names a hidden file
    ag = dict(__name__="workflow_actions_guard", __file__=str(tree.root / ACTIONS_GUARD))
    exec(compile(tree.read(ACTIONS_GUARD), ACTIONS_GUARD, "exec"), ag)
    assert tests_in(tree.read(ACTIONS_GUARD)) == ['test_every_action_is_at_a_version_built_for_node_24', 'test_an_upload_names_no_hidden_file', 'test_the_reader_is_looking'], f"{ACTIONS_GUARD}: its tests are {tests_in(tree.read(ACTIONS_GUARD))}"
    wfs = sorted(p.relative_to(tree.root).as_posix() for p in (tree.root / ".github" / "workflows").glob("*.y*ml"))
    assert wfs == ['.github/workflows/tests.yml'], f"the workflows here are {wfs}"
    uploads_left = 0
    for wf in wfs:
        text = as_written(wf)
        name = wf.rsplit("/", 1)[1]
        assert ag["_problems"](name, text) == [], f"{wf}: {ag['_problems'](name, text)}"
        steps = [n for n, action, _r in ag["_uses"](text) if action == ag["UPLOAD"]]
        found = ag["_uploads"](text)
        assert [n for n, _p, _h in found] == steps, f"{wf}: the reader misses an upload step"
        hidden = [p for _n, paths, too in found if not too for p in paths if ag["HIDDEN"].search(p)]
        assert not hidden, f"{wf}: an upload still names {hidden}"
        uploads_left += len(found)
    assert uploads_left == 0, f"the workflows would hold {uploads_left} upload steps"

    # ================= item 23: every document the count guard reads states floors, and every floor is true
    cg = dict(__name__="counts_guard", __file__=str(tree.root / COUNTS_GUARD))
    exec(compile(tree.read(COUNTS_GUARD), COUNTS_GUARD, "exec"), cg)
    assert tests_in(tree.read(COUNTS_GUARD)) == ['test_every_number_of_tests_a_document_states_is_a_floor', 'test_every_floor_is_true', 'test_the_reader_is_looking'], f"{COUNTS_GUARD}: its tests are {tests_in(tree.read(COUNTS_GUARD))}"
    assert cg["ROOT_SUITE"] == ROOT_SUITE, f"{COUNTS_GUARD} is set for {cg['ROOT_SUITE']}"
    assert cg["DOCUMENTS"] == {'README.md': 6, 'tests/README.md': 4} and cg["RECORDS"] == {}, \
        f"{COUNTS_GUARD} reads {cg['DOCUMENTS']}, leaving {cg['RECORDS']}"
    modern = sorted((set(p.relative_to(tree.root).as_posix() for p in (tree.root / "tests").glob("test_*.py"))
                     | set(r for r in tree.files if r.startswith("tests/test_") and r.count("/") == 1
                           and r.endswith(".py"))) - tree.deleted)
    defined = dict(root=cg["_defined_in"](as_written(ROOT_SUITE), True),
                   pytest=sum(cg["_defined_in"](as_written(rel), False) for rel in modern))
    defined["all"] = defined["root"] + defined["pytest"]
    assert len(modern) >= 49 and defined["root"] > 100, f"the count of tests has gone blind: {len(modern)} files, {defined}"
    for rel, least in cg["DOCUMENTS"].items():
        text = as_written(rel)
        skipped = set()
        for spans in cg["_records"](text, cg["RECORDS"].get(rel, ())).values():
            assert len(spans) == 1, f"{rel}: a dated record is there {len(spans)} times"
            skipped.update(spans[0])
        claims = [c for c in cg["_claims"](text) if c[0] not in skipped]
        exact = [f"{rel}:{line}: {n:,}" for line, n, floor, _s in claims if not floor]
        assert not exact, f"a document would still state an exact count: {exact}"
        floors = [c for c in claims if c[2]]
        assert len(floors) >= least, f"{rel} would state {len(floors)} floors, not {least}"
        false = [f"{rel}:{line}: over {n:,}, and {suites} defines {defined[suites]:,}"
                 for line, n, _f, suites in floors if not n < defined[suites]]
        assert not false, f"a floor would not be true: {false}"

    # ================= what goes is what was read: each file this round deletes is, on disk, the file the
    # round was derived from. One edited since would go with whatever it gained.
    for rel, sha in (('ui/line_number_text_edit.py', 'd5d4035880f09f2160d06e37596a30174628fb2cd5830c82db0b258628ffcf82'), ('tests/tests_README.md', 'fcf39ac4146593a2191d736b412aa4e69845915c5b41bdb12a54ff5de8a8c3a6')):
        got = hashlib.sha256(_original(tree, rel).encode("utf-8")).hexdigest()
        assert got == sha, (f"{rel} has been edited since this round read it: {got[:12]}. The file moved; "
                            f"re-derive this edit before trusting the script.")

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
