"""clearing highlights leaves the caret, the selection and the view where they are

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (c30f796).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-28: "Scripts have run read this note and we can fix these
three" -- the caret jumps the not-an-edit round measured and left for a
ruling. Built on up_tt_not_an_edit.py, which has landed; this refuses,
saying so, where it has not.

1. Typing into Find's search box: every key moved the main text's caret to
   the very end and scrolled to the bottom.
2. Closing Find: the same jump, so the match you had found was lost.
3. The Regex Builder, with no pattern or a broken one: a key typed in the
   middle of the test text sent the caret to the end 300 ms later.

All three came from the two clears. Each selected the whole text with the
widget's own cursor, cleared the selection and set the cursor back, which
leaves it at the end. They now reset through a cursor of the document's
own and never set the widget's: the caret, the selection and the view stay
where they are. A Find that finds nothing no longer moves the text either.

A Find still shows its first match at the top of the view, where it always
has. That placement came from the clear's detour to the end, so it is now
made on purpose, once the match is selected; what a Find shows is unchanged,
pixel for pixel.
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
SENTINEL = 'RNV-CARET-STAYS'
SENTINEL_FILE = 'ui/find_replace_dialog.py'
GUARD = 'tests/test_caret_stays_put.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_caret_stays_put.py', 'tests/test_highlighting_is_not_an_edit.py', 'tests/test_find_highlights_follow_a_switch.py']
DESCRIPTION = 'clearing highlights leaves the caret, the selection and the view where they are'

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

SHADOWS = {"base_dialog.py", "colors.py", "conftest.py", "find_replace_dialog.py", "regex_builder_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ["where a Find puts its first match: at the top of the view, as before, even when the match was already on screen. It used to come from the clear's detour to the end and is now made on purpose; scrolling only when the match is off screen would be a separate ruling.", "Find Next, and the Regex Builder's table: each already moved the caret to a match on purpose, and still does."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # This round builds on up_tt_not_an_edit.py: its anchors are that round's
    # text. Without it they would all be "missing", which says the wrong thing.
    if "RNV-NOT-AN-EDIT" not in tree.read("ui/base_dialog.py"):
        raise Stop("this round builds on up_tt_not_an_edit.py, which has not been "
                   "applied here: ui/base_dialog.py has no 'RNV-NOT-AN-EDIT'.\n"
                   "Run that round first (after up_tt_find_repaint.py), then this "
                   "one. Nothing was written.", EXIT_CANNOT_RUN)
    tree.sub('ui/find_replace_dialog.py',
             '        # Reset formatting by getting plain text and setting it back\n        # This preserves the text but removes formatting\n        cursor = self.target_text_edit.textCursor()\n        cursor.select(QTextCursor.SelectionType.Document)\n',
             "        # Reset formatting by getting plain text and setting it back\n        # This preserves the text but removes formatting\n        # RNV-CARET-STAYS 2026-09-28: through a cursor of the document's own,\n        # and the text's own is left alone. This selected the whole text with\n        # the text's cursor and set it back, which put the caret at the end\n        # and scrolled there -- on every key typed into Find's field, and on\n        # closing Find, where the match you had found was lost.\n        cursor = QTextCursor(self.target_text_edit.document())\n        cursor.select(QTextCursor.SelectionType.Document)\n")
    tree.sub('ui/find_replace_dialog.py',
             '                cursor.setCharFormat(format_clear)\n        cursor.clearSelection()\n        self.target_text_edit.setTextCursor(cursor)\n        self._painted_highlight = None\n',
             '                cursor.setCharFormat(format_clear)\n        self._painted_highlight = None\n')
    tree.sub('ui/find_replace_dialog.py',
             '                self._highlight_all_matches()\n                self._highlight_current_match()\n                self.find_next_btn.setEnabled(True)\n',
             '                self._highlight_all_matches()\n                self._highlight_current_match()\n                # RNV-CARET-STAYS 2026-09-28: the first match at the top of the\n                # view, where a Find has always shown it. That came from the\n                # clear, which took the caret to the end on the way; it no\n                # longer does, so the placement is made here.\n                bar = self.target_text_edit.verticalScrollBar()\n                bar.setValue(bar.value() + self.target_text_edit.cursorRect().top())\n                self.find_next_btn.setEnabled(True)\n')
    tree.sub('ui/regex_builder_dialog.py',
             '        # Clear highlighting\n        cursor = self.test_text.textCursor()\n        cursor.select(QTextCursor.SelectionType.Document)\n',
             "        # Clear highlighting\n        # RNV-CARET-STAYS 2026-09-28: through a cursor of the document's own,\n        # and the pane's own is left alone. This set the pane's cursor back\n        # after selecting all of it, which put the caret at the end: with no\n        # pattern or a broken one, a key typed in the middle of the test text\n        # sent it there 300 ms later.\n        cursor = QTextCursor(self.test_text.document())\n        cursor.select(QTextCursor.SelectionType.Document)\n")
    tree.sub('ui/regex_builder_dialog.py',
             '                cursor.setCharFormat(QTextCharFormat())\n        cursor.clearSelection()\n        self.test_text.setTextCursor(cursor)\n',
             '                cursor.setCharFormat(QTextCharFormat())\n')
    tree.sub('ui/base_dialog.py',
             "        A caret moved inside the block is not announced either. The one caret\n        that moves inside one, in Find's _highlight_all_matches(), is moved\n        again straight after, outside it.\n",
             "        A caret moved inside the block would not be announced either, so none\n        is: RNV-CARET-STAYS took out the last one, the caret Find's clear\n        moved to the end.\n")
    if (tree.root / 'tests/test_caret_stays_put.py').exists():
        raise Stop('tests/test_caret_stays_put.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_caret_stays_put.py', '"""\ntests/test_caret_stays_put.py\n=============================\nRNV-CARET-STAYS, 2026-09-28. Clearing highlights leaves the caret where it is.\n\nFind and the Regex Builder cleared their highlights by selecting the whole\ntext with the widget\'s own cursor, clearing the selection and setting that\ncursor back -- which left the caret at the end of the text and scrolled\nthere. Three places a person met it:\n\n1. typing into Find\'s search box: every key sent the main text\'s caret to\n   the end and scrolled to the bottom;\n2. closing Find: the same, so the match you had found was lost;\n3. the Regex Builder, with no pattern or a broken one: a key typed in the\n   middle of the test text sent the caret to the end 300 ms later.\n\nThe clears now reset through a cursor of the document\'s own. A Find still\nshows its first match at the top of the view, where it always has; that\nplacement came from the clear\'s detour to the end, and is now made on\npurpose. Every test drives the main window\'s own openers, with the window\nshown, so the view has a size to scroll.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.base_dialog import BaseDialog\n\nLINES = [f"line {i:02d}: the quick brown fox jumps over the lazy dog" for i in range(1, 61)]\nLINES[4] = "line 05: here is the word needle, on line five"\nLINES[39] = "line 40: here is the word pin, on line forty"\nTEXT = "\\n".join(LINES) + "\\n"\nPANE = "foo boo zoo\\nmoo\\n"\n\n\n@pytest.fixture\ndef shown(main_window, qtbot):\n    win = main_window\n    win.resize(1200, 860)\n    win.show()\n    qtbot.waitExposed(win)\n    win.text_input.setPlainText(TEXT)\n    QApplication.processEvents()\n    return win\n\n\ndef _opened(win, opener: str) -> BaseDialog:\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    return new[0]\n\n\ndef _put(edit, position: int, view: int = 0) -> None:\n    cursor = edit.textCursor()\n    cursor.setPosition(position)\n    edit.setTextCursor(cursor)\n    edit.verticalScrollBar().setValue(view)\n    QApplication.processEvents()\n\n\ndef _where(edit) -> tuple:\n    """The caret, the selection and the view: what a person sees move."""\n    cursor = edit.textCursor()\n    return (cursor.anchor(), cursor.position(), cursor.selectedText(),\n            edit.verticalScrollBar().value())\n\n\ndef _painted(edit) -> int:\n    runs, block = 0, edit.document().begin()\n    while block.isValid():\n        it = block.begin()\n        while not it.atEnd():\n            runs += bool(it.fragment().charFormat().properties())\n            it += 1\n        block = block.next()\n    return runs\n\n\ndef _found_the_second(win):\n    """Find for "quick", then Find Next: the second match selected."""\n    dlg = _opened(win, "_open_find_dialog")\n    dlg.find_input.setText("quick")\n    dlg._on_find()\n    dlg._on_find_next()\n    QApplication.processEvents()\n    where = _where(win.text_input)\n    assert where[2] == "quick" and _painted(win.text_input), "the Find found nothing to keep"\n    return dlg, where\n\n\nclass TestFindLeavesTheCaret:\n\n    def test_typing_into_find_leaves_the_caret_and_the_view(self, shown):\n        edit = shown.text_input\n        _put(edit, 100)\n        before = _where(edit)\n        dlg = _opened(shown, "_open_find_dialog")\n        for i in range(1, 6):\n            dlg.find_input.setText("hello"[:i])              # five keys, no Find run\n        assert _where(edit) == before, f"typing into Find moved the text: {before} -> {_where(edit)}"\n        dlg.close()\n\n    def test_typing_a_new_search_keeps_the_match_you_found(self, shown):\n        edit = shown.text_input\n        dlg, where = _found_the_second(shown)\n        for i in range(1, 5):\n            dlg.find_input.setText("lazy"[:i])               # a new search, typed\n        assert _painted(edit) == 0, "the old search\'s highlights stayed"\n        assert _where(edit) == where, f"typing a new search moved the text: {where} -> {_where(edit)}"\n        dlg.close()\n\n    def test_closing_find_leaves_the_found_match_selected(self, shown):\n        edit = shown.text_input\n        dlg, where = _found_the_second(shown)\n        dlg.close()\n        QApplication.processEvents()\n        assert _painted(edit) == 0, "closing Find left its highlights"\n        assert _where(edit) == where, f"closing Find moved the text: {where} -> {_where(edit)}"\n\n    def test_a_find_that_finds_nothing_leaves_the_caret(self, shown):\n        edit = shown.text_input\n        _put(edit, 100)\n        before = _where(edit)\n        dlg = _opened(shown, "_open_find_dialog")\n        dlg.find_input.setText("zzz")\n        dlg._on_find()\n        assert dlg.status_label.text() == "No matches found"\n        assert _where(edit) == before, f"a Find with no match moved the text: {before} -> {_where(edit)}"\n        dlg.close()\n\n    @pytest.mark.parametrize("word, view", [("needle", "top"), ("pin", "top"), ("needle", "bottom")],\n                             ids=["on-screen", "below-the-view", "above-the-view"])\n    def test_a_find_still_shows_its_first_match_at_the_top(self, shown, word, view):\n        edit = shown.text_input\n        bar = edit.verticalScrollBar()\n        _put(edit, 0, 0 if view == "top" else bar.maximum())\n        dlg = _opened(shown, "_open_find_dialog")\n        dlg.find_input.setText(word)\n        dlg._on_find()\n        QApplication.processEvents()\n        assert edit.textCursor().selectedText() == word\n        assert edit.cursorRect().top() == 0 and bar.value() < bar.maximum(), \\\n            f"the first match is drawn at y {edit.cursorRect().top()}, not at the top of the view"\n        dlg.close()\n\n\nclass TestTheRegexBuilderLeavesTheCaret:\n\n    @pytest.mark.parametrize("pattern", ["", "(o", "o"], ids=["no-pattern", "broken-pattern", "pattern"])\n    def test_a_key_typed_in_the_middle_stays_in_the_middle(self, main_window, qtbot, pattern):\n        builder = _opened(main_window, "_open_regex_builder_dialog")\n        builder.pattern_input.setText(pattern)\n        pane = builder.test_text\n        pane.setPlainText(PANE)\n        qtbot.wait(700)\n        cursor = pane.textCursor()\n        cursor.setPosition(3)\n        pane.setTextCursor(cursor)\n        pane.insertPlainText("x")                            # a key typed in the middle\n        qtbot.wait(700)                                      # the update runs\n        assert pane.textCursor().position() == 4, \\\n            f"the caret went from 4 to {pane.textCursor().position()} (the text ends at {len(pane.toPlainText())})"\n        builder.close()\n\n    def test_a_selection_in_the_pane_survives_an_update(self, main_window, qtbot):\n        builder = _opened(main_window, "_open_regex_builder_dialog")\n        pane = builder.test_text\n        pane.setPlainText(PANE)\n        qtbot.wait(700)\n        cursor = pane.textCursor()\n        cursor.setPosition(4)\n        cursor.setPosition(7, cursor.MoveMode.KeepAnchor)\n        pane.setTextCursor(cursor)\n        builder.pattern_input.setText("(")                   # a broken pattern: the results clear\n        qtbot.wait(700)\n        assert pane.textCursor().selectedText() == "boo", "an update dropped the selection in the pane"\n        builder.close()\n')


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
    BASE, FIND, REGEX = "ui/base_dialog.py", "ui/find_replace_dialog.py", "ui/regex_builder_dialog.py"

    def dialog(src, name):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == name)
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}, c

    def compare(rel, name):
        (o, oc), (n, nc) = dialog(_original(tree, rel), name), dialog(tree.read(rel), name)
        moved = sorted(k for k in o if k in n and ast.dump(o[k]) != ast.dump(n[k]))
        rest = lambda c: [ast.dump(s) for s in c.body if not isinstance(s, ast.FunctionDef)]  # noqa: E731
        assert set(o) == set(n) and rest(oc) == rest(nc), f"{name}: methods added or removed, or its body moved"
        outside = lambda src: [ast.dump(x) for x in ast.parse(src).body   # noqa: E731
                               if not (isinstance(x, ast.ClassDef) and x.name == name)]
        assert outside(_original(tree, rel)) == outside(tree.read(rel)), f"{rel} moved beyond {name}"
        return o, n, moved

    def lines(fn):
        return [ast.unparse(s) for s in fn.body]

    def own_cursor_only(old_fn, new_fn, edit):
        """The clear, reset through a cursor of the document's own, and the
        widget's cursor no longer set; every other statement as it was."""
        was = lines(old_fn)
        want = [f"cursor = QTextCursor({edit}.document())" if s == f"cursor = {edit}.textCursor()" else s
                for s in was if s not in ("cursor.clearSelection()", f"{edit}.setTextCursor(cursor)")]
        return f"cursor = {edit}.textCursor()" in was and f"{edit}.setTextCursor(cursor)" in was \
            and lines(new_fn) == want

    # --- Find: the clear leaves the caret; a Find places its first match as it always has
    o, n, moved = compare(FIND, "FindReplaceDialog")
    assert moved == ["_clear_highlights", "_perform_find"], f"FindReplaceDialog: moved {moved}"
    assert own_cursor_only(o["_clear_highlights"], n["_clear_highlights"], "self.target_text_edit"), \
        "_clear_highlights() changed beyond resetting through its own cursor and leaving the caret"
    PLACE = ["bar = self.target_text_edit.verticalScrollBar()",
             "bar.setValue(bar.value() + self.target_text_edit.cursorRect().top())"]
    new_find = ast.unparse(n["_perform_find"]).split("\n")
    at = [i for i, s in enumerate(new_find) if s.strip() == PLACE[0]]
    assert len(at) == 1 and new_find[at[0] - 1].strip() == "self._highlight_current_match()" \
        and new_find[at[0] + 1].strip() == PLACE[1], \
        "a Find does not place its first match at the top once it is selected"
    assert "\n".join(s for s in new_find if s.strip() not in PLACE) == ast.unparse(o["_perform_find"]), \
        "_perform_find() changed beyond placing the first match"

    # --- the Regex Builder: the clear leaves the caret
    o, n, moved = compare(REGEX, "RegexBuilderDialog")
    assert moved == ["_clear_results"], f"RegexBuilderDialog: moved {moved}"
    assert own_cursor_only(o["_clear_results"], n["_clear_results"], "self.test_text"), \
        "_clear_results() changed beyond resetting through its own cursor and leaving the caret"

    # --- BaseDialog: one docstring sentence, nothing else
    o, n, moved = compare(BASE, "BaseDialog")
    assert moved == ["_not_an_edit"] and [ast.dump(s) for s in o["_not_an_edit"].body[1:]] == \
        [ast.dump(s) for s in n["_not_an_edit"].body[1:]], f"BaseDialog: moved {moved} beyond a docstring"

    # --- derived, not listed: nothing in either dialog that changes a format sets the widget's cursor
    for rel, name in ((FIND, "FindReplaceDialog"), (REGEX, "RegexBuilderDialog")):
        for fname, fn in dialog(tree.read(rel), name)[0].items():
            calls = {getattr(c.func, "attr", None) for c in ast.walk(fn) if isinstance(c, ast.Call)}
            if calls & {"setCharFormat", "mergeCharFormat"}:
                assert "setTextCursor" not in calls, f"{name}.{fname} changes a format and moves the caret"

    # --- the premise: a Find selects its current match and makes it visible,
    # which is what the placement adjusts
    fns = dialog(tree.read(FIND), "FindReplaceDialog")[0]
    current = ast.unparse(fns["_highlight_current_match"])
    assert "self.target_text_edit.setTextCursor(cursor)" in current \
        and "self.target_text_edit.ensureCursorVisible()" in current, \
        "_highlight_current_match() no longer selects the match and shows it: re-derive the placement"

    # --- the guard: new, and marked
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert SENTINEL in guard and "class TestFindLeavesTheCaret" in guard \
        and "class TestTheRegexBuilderLeavesTheCaret" in guard, "the guard is not the one this round writes"
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
