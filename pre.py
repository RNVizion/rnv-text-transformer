"""the highlights Find painted into the text follow a mode switch

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (29a485e).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-28: "2 and 3 look fine we can make those fixes" -- item 2 of
the three-questions render.

Find paints every match into the main window's text in the mode's accent, at
alpha 80, when it runs. RNV-DIALOG-SWITCH made the open dialog follow a theme
switch; the highlights it had drawn did not, and kept the old mode's accent
until the next Find -- dark's #d2bc93 on light's ground, where a Find run in
light paints #8c7337.

The dialog paints them again when it is refreshed: whatever carries the
colour they were painted in, wherever an edit since the Find has moved it,
through a cursor of the document's own. The caret, the current match's
selection and the view stay where they are -- repainting the dialog's own
way, _highlight_all_matches(), clears through the text's cursor and leaves
the caret at the end. The repaint is one step of the text's undo history,
and it does not count as an edit: the text's signals are held while it runs,
so the statistics and the auto-transform the main window runs on textChanged
stay still.
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
SENTINEL = 'RNV-FIND-REPAINT'
SENTINEL_FILE = 'ui/find_replace_dialog.py'
GUARD = 'tests/test_find_highlights_follow_a_switch.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_find_highlights_follow_a_switch.py']
DESCRIPTION = 'the highlights Find painted into the text follow a mode switch'

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

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "find_replace_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ["the Find itself. Painting its matches still counts as an edit of the text, as it always has: with auto-transform on, running Find re-runs the transform, so an output edited by hand is replaced, and each match it paints is a step of the text's undo history. Measured at this head and the one before it; raised in the round's doc, not changed here.", "the Regex Builder's test pane. Its own highlighting fires the pane's textChanged, which re-arms the 300 ms update, which highlights again: with a pattern and test text it re-runs about three times a second while nothing happens, and the pane's undo history grows. Measured at this head and the one before it; raised in the round's doc, not changed here.", "undo after a switch. One Ctrl+Z in the text takes the highlights back to the colour they had before the switch -- the repaint is a step of the history, as a Find's painting is -- and, as a Find does, a repaint ends any redo the text had."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/find_replace_dialog.py',
             "        'status_label', '_current_matches', '_current_match_index',\n        '_is_replace_mode'\n    )\n",
             "        'status_label', '_current_matches', '_current_match_index',\n        '_is_replace_mode', '_painted_highlight'\n    )\n")
    tree.sub('ui/find_replace_dialog.py',
             '        self._current_match_index: int = -1\n        \n        self._setup_ui()\n',
             '        self._current_match_index: int = -1\n        # RNV-FIND-REPAINT 2026-09-28: the colour the highlights in the text\n        # were painted in, while any are there; what a switch finds them by.\n        self._painted_highlight: QColor | None = None\n        \n        self._setup_ui()\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _configure_window(self) -> None:\n',
             '    def refresh_theme(self) -> None:\n        """\n        Refresh the dialog after a theme switch, and the highlights it drew.\n        \n        RNV-FIND-REPAINT 2026-09-28: Find paints its matches into the text\n        in the mode\'s accent when it runs, and a switch left them in the old\n        mode\'s until the next Find.\n        """\n        super().refresh_theme()\n        self._recolour_highlights()\n    \n    def _configure_window(self) -> None:\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def _highlight_all_matches(self) -> None:\n',
             '    def _highlight_colour(self) -> QColor:\n        """\n        The colour matches are highlighted in: the mode\'s accent, at alpha 80.\n        \n        RNV-FIND-REPAINT 2026-09-28: one place for it, read by the Find that\n        paints the highlights and by the switch that paints them again.\n        """\n        is_dark = self.theme_manager.current_theme in (\'dark\', \'image\')\n        highlight_color = QColor(DialogStyleManager.get_colors(is_dark)[\'accent\'])\n        highlight_color.setAlpha(80)  # Semi-transparent\n        return highlight_color\n    \n    def _highlight_all_matches(self) -> None:\n')
    tree.sub('ui/find_replace_dialog.py',
             "        self._clear_highlights()\n        \n        is_dark = self.theme_manager.current_theme in ('dark', 'image')\n        highlight_color = QColor(DialogStyleManager.get_colors(is_dark)['accent'])\n        highlight_color.setAlpha(80)  # Semi-transparent\n        \n",
             '        self._clear_highlights()\n        \n        highlight_color = self._highlight_colour()\n        \n')
    tree.sub('ui/find_replace_dialog.py',
             '        # Apply highlighting to all matches\n        for start, end in self._current_matches:\n            cursor.setPosition(start)\n            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n            cursor.mergeCharFormat(format_highlight)\n',
             '        # Apply highlighting to all matches\n        for start, end in self._current_matches:\n            cursor.setPosition(start)\n            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n            cursor.mergeCharFormat(format_highlight)\n        self._painted_highlight = QColor(highlight_color)\n')
    tree.sub('ui/find_replace_dialog.py',
             '        cursor.clearSelection()\n        self.target_text_edit.setTextCursor(cursor)\n',
             '        cursor.clearSelection()\n        self.target_text_edit.setTextCursor(cursor)\n        self._painted_highlight = None\n')
    tree.sub('ui/find_replace_dialog.py',
             '    def closeEvent(self, event) -> None:\n',
             '    def _recolour_highlights(self) -> None:\n        """\n        Paint the highlights this dialog drew again, in this mode\'s accent.\n        \n        RNV-FIND-REPAINT 2026-09-28. What is recoloured is whatever carries\n        the colour they were painted in, where it now sits: an edit since\n        the Find moves the highlights with the text, so the positions the\n        Find recorded may no longer be theirs. Through a cursor of the\n        document\'s own, so the caret, the current match\'s selection and\n        the view stay where they are -- _highlight_all_matches() clears\n        through the text\'s own cursor, which leaves the caret at the end.\n        In one edit block, so it is one step of the text\'s undo history;\n        and with the text\'s signals held, because a colour is not an edit:\n        the statistics and the auto-transform the main window runs on\n        textChanged have nothing to do.\n        """\n        painted, edit = self._painted_highlight, self.target_text_edit\n        if painted is None or edit is None:\n            return\n        colour = self._highlight_colour()\n        if colour == painted:\n            return\n        spans = []\n        block = edit.document().begin()\n        while block.isValid():\n            it = block.begin()\n            while not it.atEnd():\n                fragment = it.fragment()\n                brush = fragment.charFormat().background()\n                if brush.style() != Qt.BrushStyle.NoBrush and brush.color() == painted:\n                    spans.append((fragment.position(), fragment.length()))\n                it += 1\n            block = block.next()\n        self._painted_highlight = QColor(colour)\n        if not spans:\n            return\n        format_highlight = QTextCharFormat()\n        format_highlight.setBackground(QBrush(colour))\n        cursor = QTextCursor(edit.document())\n        was_blocked = edit.blockSignals(True)\n        try:\n            cursor.beginEditBlock()\n            for start, length in spans:\n                cursor.setPosition(start)\n                cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)\n                cursor.mergeCharFormat(format_highlight)\n            cursor.endEditBlock()\n        finally:\n            edit.blockSignals(was_blocked)\n    \n    def closeEvent(self, event) -> None:\n')
    if (tree.root / 'tests/test_find_highlights_follow_a_switch.py').exists():
        raise Stop('tests/test_find_highlights_follow_a_switch.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_find_highlights_follow_a_switch.py', '"""\ntests/test_find_highlights_follow_a_switch.py\n=============================================\nRNV-FIND-REPAINT, 2026-09-28. The highlights Find paints into the main\nwindow\'s text follow a theme switch made while the dialog is open.\n\nFind paints every match into the text in the mode\'s accent, at alpha 80,\nwhen it runs. RNV-DIALOG-SWITCH made the open dialog follow a switch; the\nhighlights it had drawn did not, and kept the old mode\'s accent until the\nnext Find -- dark\'s accent on light\'s ground. Now the dialog paints them\nagain when it is refreshed:\n\n- in the colour a Find run in the new mode paints, on the same characters;\n- where they now are, if the text was edited since the Find;\n- through a cursor of the document\'s own: the caret, the current match\'s\n  selection and the view stay where they are;\n- as one step of the text\'s undo history, and without counting as an edit.\n  The main window runs its statistics and its auto-transform on the text\'s\n  textChanged, and a colour is not a change to the text.\n\nEvery test drives the main window\'s own opener and its own two roads to a\nswitch: the theme cycle, and the theme Settings applies.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtWidgets import QApplication, QTextEdit\n\nfrom ui.base_dialog import BaseDialog\nfrom ui.find_replace_dialog import FindReplaceDialog\n\nTEXT = ("The quick brown fox jumps over the lazy dog.\\n"\n        "Pack my box with five dozen liquor jugs.\\n"\n        "How vexingly quick daft zebras jump over the log.\\n"\n        "Sphinx of black quartz, judge my vow.\\n"\n        "Two driven jocks help fax my big quiz.\\n")\nHEADER = "Header line\\n"        # no "o" in it: a Find for "o" finds nothing new\n\n\ndef _spans(edit) -> list:\n    """(position, length, colour, alpha) of every run of the text painted\n    with a background, block by block -- what a highlight is to the text."""\n    out = []\n    block = edit.document().begin()\n    while block.isValid():\n        it = block.begin()\n        while not it.atEnd():\n            fragment = it.fragment()\n            brush = fragment.charFormat().background()\n            if brush.style() != Qt.BrushStyle.NoBrush:\n                out.append((fragment.position(), fragment.length(),\n                            brush.color().name(), brush.color().alpha()))\n            it += 1\n        block = block.next()\n    return out\n\n\ndef _in_dark(win) -> None:\n    for _ in range(3):\n        if win.theme_manager.current_theme == "dark":\n            return\n        win._cycle_theme()\n    assert win.theme_manager.current_theme == "dark"\n\n\ndef _switch(win, road: str, theme: str | None = None) -> str:\n    """One switch by the main window\'s own road; the mode it lands in."""\n    if road == "cycle":\n        win._cycle_theme()\n    else:\n        order = ("dark", "light", "image")\n        now = win.theme_manager.current_theme\n        win._apply_theme_from_settings(theme or order[(order.index(now) + 1) % 3])\n    QApplication.processEvents()\n    return win.theme_manager.current_theme\n\n\ndef _found(win, needle: str = "o", nexts: int = 2, opener: str = "_open_find_dialog"):\n    """Find opened with the main window\'s own opener, run for `needle`, and\n    Find Next pressed `nexts` times: every match painted, one of them current."""\n    before = {id(d) for d in win.findChildren(BaseDialog)}\n    getattr(win, opener)()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, (opener, len(new))\n    dlg = new[0]\n    dlg.find_input.setText(needle)\n    dlg._on_find()\n    for _ in range(nexts):\n        dlg._on_find_next()\n    QApplication.processEvents()\n    assert dlg._current_matches, "the Find found nothing to paint"\n    return dlg\n\n\ndef _fresh(win, text: str, needle: str = "o") -> list:\n    """What a Find run now, in the current mode, paints: the same Find on a\n    copy of the text, in a dialog of its own."""\n    copy = QTextEdit()\n    copy.setPlainText(text)\n    dlg = FindReplaceDialog(theme_manager=win.theme_manager, font_family=win.font_family,\n                            target_text_edit=copy)\n    dlg.find_input.setText(needle)\n    dlg._on_find()\n    spans = _spans(copy)\n    dlg.deleteLater()\n    copy.deleteLater()\n    return spans\n\n\ndef _where(edit) -> tuple:\n    cursor = edit.textCursor()\n    return (cursor.position(), cursor.anchor(), cursor.selectedText(),\n            edit.verticalScrollBar().value())\n\n\nclass TestFindHighlightsFollowASwitch:\n\n    @pytest.mark.parametrize("road", ["cycle", "settings"])\n    def test_each_mode_paints_them_as_a_find_run_in_it_would(self, main_window, road):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        seen = {"dark": _spans(win.text_input)}\n        assert seen["dark"] == _fresh(win, TEXT), "the Find itself did not paint what a Find paints"\n        for _ in range(3):                                   # every mode, and back\n            mode = _switch(win, road)\n            seen[mode] = _spans(win.text_input)\n            assert seen[mode] == _fresh(win, TEXT), (road, mode)\n        assert {"dark", "light", "image"} <= set(seen), sorted(seen)\n        assert seen["dark"] != seen["light"], "dark and light paint the same colour: nothing was tested"\n        dlg.close()\n\n    def test_the_caret_the_current_match_and_the_view_stay_put(self, main_window, qtbot):\n        win = main_window\n        win.show()\n        qtbot.waitExposed(win)\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT * 8)\n        dlg = _found(win, nexts=40)                          # a current match far down\n        where = _where(win.text_input)\n        assert where[2] == "o" and where[3] > 0, f"the current match is not selected down the text: {where}"\n        for _ in range(3):\n            mode = _switch(win, "cycle")\n            assert _where(win.text_input) == where, (mode, _where(win.text_input), where)\n        dlg.close()\n\n    def test_a_switch_repaints_without_counting_as_an_edit(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.settings_manager.save_auto_transform(True)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        win.auto_transform_timer.stop()                      # the Find\'s own run, as shipped\n        win.output_text.setPlainText("an output edited by hand")\n        edits = []\n        win.text_input.textChanged.connect(lambda: edits.append(win.theme_manager.current_theme))\n        before = _spans(win.text_input)\n        assert _switch(win, "cycle") == "light"\n        assert _spans(win.text_input) != before, "the switch repainted nothing"\n        assert edits == [], f"the repaint counted as an edit of the text: {edits}"\n        assert not win.auto_transform_timer.isActive(), "a switch set the auto-transform going"\n        assert win.output_text.toPlainText() == "an output edited by hand"\n        win.text_input.insertPlainText("x")                  # and the text\'s signals are back\n        win.auto_transform_timer.stop()\n        assert edits, "the text\'s signals were left held after the repaint"\n        dlg.close()\n\n    def test_one_switch_is_one_step_of_undo(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        dark = _spans(win.text_input)\n        assert _switch(win, "cycle") == "light"\n        assert _spans(win.text_input) != dark, "the switch repainted nothing"\n        win.text_input.undo()\n        assert _spans(win.text_input) == dark, "undoing a switch\'s repaint took more than one step"\n        assert win.text_input.toPlainText() == TEXT\n        dlg.close()\n\n    def test_a_switch_that_keeps_the_colour_leaves_the_text_alone(self, main_window):\n        """Image paints with dark\'s accent: from image to dark there is\n        nothing to repaint, and nothing is added to the text\'s undo history."""\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        doc = win.text_input.document()\n        assert [_switch(win, "cycle"), _switch(win, "cycle")] == ["light", "image"]\n        spans, steps = _spans(win.text_input), doc.availableUndoSteps()\n        assert _switch(win, "cycle") == "dark"\n        assert _spans(win.text_input) == spans, "image to dark changed the highlights"\n        assert doc.availableUndoSteps() == steps, "a switch that keeps the colour added to the undo history"\n        dlg.close()\n\n    def test_highlights_moved_by_an_edit_are_repainted_where_they_now_are(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        dlg = _found(win)\n        dark = _spans(win.text_input)\n        edit = win.text_input\n        from PyQt6.QtGui import QTextCursor\n        QTextCursor(edit.document()).insertText(HEADER)      # typed at the top since the Find\n        moved = _spans(edit)\n        assert [s[0] for s in moved] == [s[0] + len(HEADER) for s in dark], "the edit did not move them"\n        assert _switch(win, "cycle") == "light"\n        assert _spans(edit) == _fresh(win, HEADER + TEXT), "not repainted on the characters they sit on"\n        dlg.close()\n\n    def test_with_nothing_painted_the_text_is_left_alone(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        doc = win.text_input.document()\n        dlg = _found(win)\n        dlg.find_input.setText("")                           # a new search clears them\n        steps = doc.availableUndoSteps()\n        for _ in range(3):\n            _switch(win, "cycle")\n            assert _spans(win.text_input) == [] and doc.availableUndoSteps() == steps\n        dlg.close()\n\n    def test_find_and_find_and_replace_open_together_both_follow(self, main_window):\n        win = main_window\n        _in_dark(win)\n        win.text_input.setPlainText(TEXT)\n        first = _found(win, needle="o")\n        second = _found(win, needle="u", opener="_open_replace_dialog")   # clears the first\'s\n        for _ in range(3):\n            mode = _switch(win, "cycle")\n            assert _spans(win.text_input) == _fresh(win, TEXT, needle="u"), mode\n        first.close()\n        second.close()\n')


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
    FIND, MAIN = "ui/find_replace_dialog.py", "ui/main_window.py"

    def dialog(src):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "FindReplaceDialog")
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}, c

    def body(fn):
        return [ast.unparse(s) for s in fn.body]

    old_src, new_src = _original(tree, FIND), tree.read(FIND)
    (o, oc), (n, nc) = dialog(old_src), dialog(new_src)
    added, gone = sorted(set(n) - set(o)), sorted(set(o) - set(n))
    moved = sorted(k for k in o if k in n and ast.dump(o[k]) != ast.dump(n[k]))
    assert added == ["_highlight_colour", "_recolour_highlights", "refresh_theme"] and not gone, \
        f"FindReplaceDialog: added {added}, removed {gone}"
    assert moved == ["__init__", "_clear_highlights", "_highlight_all_matches"], \
        f"FindReplaceDialog: moved {moved}"

    # the colour they were painted in: kept from the start, forgotten on a clear
    KEEP = "self._painted_highlight: QColor | None = None"
    init = body(n["__init__"])
    assert init.count(KEEP) == 1 and [s for s in init if s != KEEP] == body(o["__init__"]), \
        "__init__ changed beyond keeping the painted colour"
    assert init.index(KEEP) < init.index("self._setup_ui()"), "the painted colour is kept after the UI is built"
    assert body(n["_clear_highlights"]) == body(o["_clear_highlights"]) + ["self._painted_highlight = None"], \
        "_clear_highlights() changed beyond forgetting the painted colour"

    # the colour itself: one place, derived exactly as the Find derived it
    COLOUR = ["is_dark = self.theme_manager.current_theme in ('dark', 'image')",
              "highlight_color = QColor(DialogStyleManager.get_colors(is_dark)['accent'])",
              "highlight_color.setAlpha(80)"]
    oh, nh = body(o["_highlight_all_matches"]), body(n["_highlight_all_matches"])
    at = oh.index(COLOUR[0])
    assert oh[at:at + 3] == COLOUR, "the Find's colour is not derived where it was"
    assert nh == oh[:at] + ["highlight_color = self._highlight_colour()"] + oh[at + 3:] \
        + ["self._painted_highlight = QColor(highlight_color)"], \
        "_highlight_all_matches() changed beyond reading its colour from one place and keeping it"
    assert body(n["_highlight_colour"])[1:] == COLOUR + ["return highlight_color"], \
        "_highlight_colour() does not derive the colour the Find paints in"

    # the refresh: the dialog's own, then the highlights
    assert body(n["refresh_theme"])[1:] == ["super().refresh_theme()", "self._recolour_highlights()"], \
        "refresh_theme() does not repaint the highlights after the dialog"

    # the repaint: a cursor of the document's own, one edit block, the text's
    # signals held and given back, and only what carries the painted colour
    rc = n["_recolour_highlights"]
    text = ast.unparse(rc)
    assert "setTextCursor" not in text and "textCursor()" not in text, \
        "the repaint goes through the text's own cursor, which moves the caret"
    assert "cursor = QTextCursor(edit.document())" in text, "the repaint has no cursor of its own"
    assert "colour = self._highlight_colour()" in text, "the repaint reads another colour than the Find paints"
    assert "brush.color() == painted" in text, "the repaint does not find the highlights by their colour"
    assert "was_blocked = edit.blockSignals(True)" in text, "the repaint does not hold the text's signals"
    tries = [s for s in ast.walk(rc) if isinstance(s, ast.Try)]
    assert len(tries) == 1 and [ast.unparse(s) for s in tries[0].finalbody] == [
        "edit.blockSignals(was_blocked)"], "the repaint does not give the text's signals back"
    held = [ast.unparse(s) for s in tries[0].body]
    assert held[0] == "cursor.beginEditBlock()" and held[-1] == "cursor.endEditBlock()", \
        "the repaint is not one edit block"

    # __slots__ gains the one name; the rest of the class and module stay
    def slots(cls):
        a = next(s for s in cls.body if isinstance(s, ast.Assign) and ast.unparse(s.targets[0]) == "__slots__")
        return list(ast.literal_eval(a.value))
    assert slots(nc) == slots(oc) + ["_painted_highlight"], "__slots__ changed beyond the painted colour"

    def rest(cls):
        return [ast.dump(s) for s in cls.body if not isinstance(s, ast.FunctionDef)
                and not (isinstance(s, ast.Assign) and ast.unparse(s.targets[0]) == "__slots__")]
    assert rest(oc) == rest(nc), "the dialog's class body moved beyond its methods"
    outside = lambda src: [ast.dump(x) for x in ast.parse(src).body   # noqa: E731
                           if not (isinstance(x, ast.ClassDef) and x.name == "FindReplaceDialog")]
    assert outside(old_src) == outside(new_src), f"{FIND} moved beyond the dialog"

    # the premise: every Find the main window shows is kept, and both roads
    # to a switch refresh what it keeps -- the road RNV-DIALOG-SWITCH laid,
    # which the repaint rides on
    win = next(c for c in ast.parse(tree.read(MAIN)).body
               if isinstance(c, ast.ClassDef) and c.name == "MainWindow")
    fns = {f.name: f for f in win.body if isinstance(f, ast.FunctionDef)}
    finds = [f for f in fns.values() if "FindReplaceDialog(" in ast.unparse(f)]
    assert len(finds) >= 3, "the main window's Find openers were not found"
    for f in finds:
        assert "self._track_open_dialog(dialog)" in ast.unparse(f), f"{f.name}() shows a Find nothing refreshes"
    refresh = ast.unparse(fns["_refresh_open_dialogs_theme"])
    assert "_open_dialogs" in refresh and "dialog.refresh_theme()" in refresh, \
        "_refresh_open_dialogs_theme() does not reach the dialogs the main window keeps"
    for road in ("_cycle_theme", "_apply_theme_from_settings"):
        assert "self._refresh_open_dialogs_theme()" in ast.unparse(fns[road]), \
            f"{road}() switches the mode and does not refresh the open dialogs"

    # the guard: new, and marked
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert SENTINEL in guard and "class TestFindHighlightsFollowASwitch" in guard, \
        "the guard is not the one this round writes"
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
