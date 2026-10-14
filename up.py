"""the transformer's rulings of 13 October: the Regex Builder highlights a match where it is, a stale copy of conftest.py and a feature the app does not have go, and the ink on the gold fill is held

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (b3c40a9).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-13, items 28, 29, 30 and 32 of the list of 11 October:

  28  "A"
  29  "A"
  30  "A"
  32  "A"

ITEM 28. tests/tests_conftest.py goes: an older copy of tests/conftest.py,
from the first release. Pytest reads only conftest.py, nothing imports it,
and the hypothesis strategies it held are defined again in
tests/test_properties.py, which says why. It still called the root suite
frozen, the word item 21 took out of the documents on 11 October.

ITEM 29. The header of RNV_Text_Transformer.py lists the app's features.
One was "Clipboard history": the app copies to the clipboard and keeps no
history of it. The line goes.

ITEM 30. The Regex Builder found its matches in the text as Python holds
it, where an emoji is one position, and drew them where the test pane
counts, which counts it as two: after an emoji every highlight sat to the
left of its match. A click on a match in the table selected the same wrong
characters. Both count as the pane counts now, with the conversion Find has
used since 11 October (item 24 (d)), which moves from FindReplaceDialog to
BaseDialog, beside the function that draws highlights, unchanged.
tests/test_regex_builder_highlights_the_match.py holds it, and holds every
function that draws highlights to converting first.

ITEM 32. tests/test_ink_on_the_golds.py holds item 4's ruling here: text on
the gold fill is white on the dark gold, #8c7337, and black on the bright
gold, #d2bc93. It reads every sheet and palette of the main window and of
each window its openers show, in each mode the theme button reaches.
Nothing it found here is against the ruling.
tests/test_gold_as_text.py, which holds gold drawn as text, points to it.

No colour anything draws in moves; the Regex Builder's highlights and its
selection move onto the matches.
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
SENTINEL = 'RNV-RULINGS-2026-10-13'
SENTINEL_FILE = 'tests/test_gold_as_text.py'
GUARD = 'tests/test_regex_builder_highlights_the_match.py'
GUARD_FILES = ['tests/test_regex_builder_highlights_the_match.py', 'tests/test_ink_on_the_golds.py', 'tests/test_find_and_replace_do_what_they_say.py']
INK_GUARD = 'tests/test_ink_on_the_golds.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_regex_builder_highlights_the_match.py', 'tests/test_ink_on_the_golds.py', 'tests/test_find_and_replace_do_what_they_say.py']
DESCRIPTION = "the transformer's rulings of 13 October: the Regex Builder highlights a match where it is, a stale copy of conftest.py and a feature the app does not have go, and the ink on the gold fill is held"

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

SHADOWS = {"conftest.py", "run_tests.py", "test_rnv_text_transformer.py", "test_regex_builder_highlights_the_match.py", "test_ink_on_the_golds.py", "test_gold_as_text.py", "test_find_and_replace_do_what_they_say.py"}

LEFT_ALONE = ["the matches table's Start and End columns: they give a match's place in the text, counting an emoji as one character, as the pattern does.", "the rulings still open: the Find and Replace dialog's clipped buttons (item 12) and the transformer's Export tab (9), which wait on a look at the machine, and items 33 and 34, asked on 13 October. Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('RNV_Text_Transformer.py',
             '- Clipboard history\n',
             '')
    tree.sub('ui/find_replace_dialog.py',
             '    @staticmethod\n    def _in_qt(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:\n        """\n        Spans of a text, as its QTextDocument counts positions.\n        \n        RNV-RULINGS-2026-10-11, item 24 (d). A match is found in the\n        text as Python holds it, where a character outside the basic plane,\n        an emoji, is one position. The document counts it as two, as UTF-16\n        does. Every highlight after one was drawn a place to the left, and\n        Replace wrote over the characters there.\n        """\n        wide = [index for index, char in enumerate(text) if ord(char) > 0xFFFF]\n        if not wide:\n            return list(spans)\n        return [(start + bisect_left(wide, start), end + bisect_left(wide, end)) for start, end in spans]\n    \n    @staticmethod\n    def _text_index(text: str, position: int) -> int:\n        """\n        A document\'s position, as an index of the text Python holds: the\n        other way round from _in_qt().\n        """\n        units = 0\n        for index, char in enumerate(text):\n            if units >= position:\n                return index\n            units += 2 if ord(char) > 0xFFFF else 1\n        return len(text)\n    \n',
             '')
    tree.sub('ui/find_replace_dialog.py',
             'import re\nfrom bisect import bisect_left\nfrom typing import TYPE_CHECKING, ClassVar\n',
             'import re\nfrom typing import TYPE_CHECKING, ClassVar\n')
    tree.sub('ui/base_dialog.py',
             'from __future__ import annotations\n\nfrom typing import TYPE_CHECKING, ClassVar\n',
             'from __future__ import annotations\n\nfrom bisect import bisect_left\nfrom typing import TYPE_CHECKING, ClassVar\n')
    tree.sub('ui/base_dialog.py',
             '            selections.append(selection)\n        edit.setExtraSelections(selections)\n    \n',
             '            selections.append(selection)\n        edit.setExtraSelections(selections)\n    \n    @staticmethod\n    def _in_qt(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:\n        """\n        Spans of a text, as its QTextDocument counts positions.\n        \n        RNV-RULINGS-2026-10-11, item 24 (d). A match is found in the\n        text as Python holds it, where a character outside the basic plane,\n        an emoji, is one position. The document counts it as two, as UTF-16\n        does. Every highlight after one was drawn a place to the left, and\n        Replace wrote over the characters there. RNV-RULINGS-2026-10-13,\n        item 30: moved here from FindReplaceDialog, beside\n        _show_highlights(), for the Regex Builder had the same fault.\n        """\n        wide = [index for index, char in enumerate(text) if ord(char) > 0xFFFF]\n        if not wide:\n            return list(spans)\n        return [(start + bisect_left(wide, start), end + bisect_left(wide, end)) for start, end in spans]\n    \n    @staticmethod\n    def _text_index(text: str, position: int) -> int:\n        """\n        A document\'s position, as an index of the text Python holds: the\n        other way round from _in_qt().\n        """\n        units = 0\n        for index, char in enumerate(text):\n            if units >= position:\n                return index\n            units += 2 if ord(char) > 0xFFFF else 1\n        return len(text)\n    \n')
    tree.sub('ui/regex_builder_dialog.py',
             '        self._show_highlights(self.test_text,\n                              [(match.start, match.end) for match in self._current_matches],\n                              highlight_color)\n',
             '        # RNV-RULINGS-2026-10-13, item 30: the matches are found in the text\n        # as Python counts it, and drawn where the pane counts, which counts\n        # an emoji as two.\n        self._show_highlights(self.test_text,\n                              self._in_qt(self.test_text.toPlainText(),\n                                          [(match.start, match.end) for match in self._current_matches]),\n                              highlight_color)\n')
    tree.sub('ui/regex_builder_dialog.py',
             '            # Select the match in test text\n            cursor = self.test_text.textCursor()\n            cursor.setPosition(match.start)\n            cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)\n',
             '            # Select the match in test text, where the pane counts it\n            # (RNV-RULINGS-2026-10-13, item 30)\n            start, end = self._in_qt(self.test_text.toPlainText(), [(match.start, match.end)])[0]\n            cursor = self.test_text.textCursor()\n            cursor.setPosition(start)\n            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)\n')
    tree.sub('tests/test_gold_as_text.py',
             '"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.\n\n',
             '"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.\n\nTEXT ON THE GOLD, the other way round, is held in tests/test_ink_on_the_golds.py:\nwhite on the dark gold, black on the bright gold. RNV-RULINGS-2026-10-13,\nitem 32.\n\n')
    if (tree.root / 'tests/test_regex_builder_highlights_the_match.py').exists():
        raise Stop('tests/test_regex_builder_highlights_the_match.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_regex_builder_highlights_the_match.py', '"""The Regex Builder highlights and selects a match where it is.\n\nRNV-RULINGS-2026-10-13, item 30. Ruled 2026-10-13: "A".\n\nWHAT WAS THERE. The Regex Builder found its matches in the text as Python\nholds it, where a character outside the basic plane, an emoji, is one\nposition, and drew them where the test pane counts, which counts it as two.\nMeasured on 2026-10-11 in "😀 fox, 😀😀 the fox" with the pattern fox: the\nhighlights sat on " fo" and "he ". A click on a match in the table selected\nthe same wrong characters. It was the fault Find had until item 24 (d) of\n2026-10-11.\n\nWHAT IS THERE NOW. Both count positions as the pane counts them, with the\nconversion Find uses. It moved to BaseDialog, beside the function that\ndraws highlights.\n\nWHAT THIS GUARD HOLDS, through the main window\'s own Regex Builder:\n\n1. The highlights sit on the matches after an emoji, with groups and\n   without.\n2. A click on a match in the table selects that match.\n3. Every function that draws highlights converts the positions it is\n   given: each one that calls _show_highlights() calls _in_qt() too.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.regex_builder_dialog import RegexBuilderDialog\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nEMOJI = "\\U0001F600"\nTEXT = f"{EMOJI} fox, {EMOJI}{EMOJI} the fox\\n"\n\n\ndef _utf16(text: str) -> int:\n    return len(text.encode("utf-16-le")) // 2\n\n\n@pytest.fixture\ndef builder(main_window):\n    """The main window\'s own Regex Builder, opened on TEXT in the input."""\n    win = main_window\n    win.settings_manager.save_auto_transform(False)\n    win.auto_transform_timer.stop()\n    win.text_input.setPlainText(TEXT)\n    win.auto_transform_timer.stop()\n    before = {id(d) for d in win.findChildren(RegexBuilderDialog)}\n    win._open_regex_builder_dialog()\n    QApplication.processEvents()\n    new = [d for d in win.findChildren(RegexBuilderDialog) if id(d) not in before and d.isVisible()]\n    assert len(new) == 1, len(new)\n    dlg = new[0]\n\n    def matching(pattern: str) -> RegexBuilderDialog:\n        dlg.pattern_input.setText(pattern)\n        dlg._update_timer.stop()\n        dlg._update_matches()\n        return dlg\n    yield matching\n    dlg.close()\n\n\ndef _highlighted(edit) -> list:\n    return [s.cursor.selectedText() for s in edit.extraSelections() if s.cursor.hasSelection()]\n\n\n@pytest.mark.parametrize("pattern", ["fox", "f(o)x", "(?P<first>f)ox"])\ndef test_the_highlights_sit_on_the_matches(builder, pattern):\n    dlg = builder(pattern)\n    assert dlg.test_text.toPlainText() == TEXT\n    assert len(dlg._current_matches) == 2\n    assert _highlighted(dlg.test_text) == ["fox", "fox"], \\\n        f"the highlights sit on {_highlighted(dlg.test_text)}"\n\n\ndef test_a_click_on_a_match_selects_it(builder):\n    dlg = builder("fox")\n    dlg._on_match_clicked(dlg.matches_table.item(1, 0))\n    cursor = dlg.test_text.textCursor()\n    assert cursor.selectedText() == "fox", f"the click selected {cursor.selectedText()!r}"\n    assert cursor.selectionStart() == _utf16(f"{EMOJI} fox, {EMOJI}{EMOJI} the ")\n\n\ndef _drawers() -> dict:\n    """(file, function) -> whether it converts, for every function in ui/\n    that calls _show_highlights()."""\n    found = {}\n    for path in sorted((ROOT / "ui").glob("*.py")):\n        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):\n            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n                continue\n            calls = {c.func.attr for c in ast.walk(node)\n                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}\n            if "_show_highlights" in calls:\n                found[(path.name, node.name)] = "_in_qt" in calls\n    return found\n\n\ndef test_every_function_that_draws_highlights_converts_the_positions():\n    drawers = _drawers()\n    assert {("find_replace_dialog.py", "_highlight_all_matches"),\n            ("regex_builder_dialog.py", "_highlight_matches")} <= set(drawers), \\\n        f"the reader does not find the two dialogs that draw highlights: {sorted(drawers)}"\n    raw = sorted(where for where, converts in drawers.items() if not converts)\n    assert not raw, ("these draw highlights at positions as Python counts them, which the pane "\n                     f"counts otherwise after an emoji: {raw}. Pass them through _in_qt().")\n')
    if (tree.root / 'tests/test_ink_on_the_golds.py').exists():
        raise Stop('tests/test_ink_on_the_golds.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_ink_on_the_golds.py', '"""White on the dark gold, black on the bright gold.\n\nRNV-RULINGS-2026-10-13, item 32. Ruled 2026-10-13: "A". It holds item 4,\nruled 2026-10-11: "Keep this is a core look identity for my brand."\n\nWHAT IS RULED. Text on the gold fill is white on the dark gold, #8c7337,\nand black on the bright gold, #d2bc93. On the dark gold white reads 4.54:1\nand black 4.62:1: both clear the 4.5 floor, and the arithmetic of which is\nbetter would pick black. The ink is a decision, not a measurement, and it\nis the brand\'s look in all five apps. The picker has held it since\n2026-09-02, in its tests/test_ink_rule.py. Until this guard nothing held it\nhere, though the application painted it in every rule measured on\n2026-10-05.\n\nWHAT THIS GUARD HOLDS, in every mode the theme button reaches, through the\nmain window and every window its own openers show:\n\n1. Every stylesheet rule that fills with a gold and sets an ink sets that\n   gold\'s ink: `color` on a fill, `selection-color` on a selection.\n2. A rule that fills with a gold and sets no ink fills a part that holds no\n   text: a check box\'s indicator, a handle, a progress bar\'s chunk. A\n   selection that sets no ink takes the palette\'s, which 3 holds.\n3. The application\'s palette and each window\'s, where a selection takes\n   its ink when no rule sets one: if it highlights in a gold, it gives the\n   highlighted text that gold\'s ink.\n4. The reader is looking: in each mode it reads every window, and finds at\n   least as many rules putting an ink on a gold as it found on 2026-10-13;\n   and it reads a sample sheet as Qt reads it.\n\nThe theme button is pressed round to the mode it started in, so a run\nleaves the saved mode as it found it.\n"""\nfrom __future__ import annotations\n\nimport re\n\nimport pytest\nfrom PyQt6.QtCore import QEventLoop, QTimer\nfrom PyQt6.QtGui import QColor, QPalette\nfrom PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QWidget\n\n@pytest.fixture\ndef window(main_window):\n    """The main window, its settings kept apart (tests/conftest.py)."""\n    return main_window\n\n#: The windows the main window\'s own openers show.\nOPENERS = (\'_open_about_dialog\', \'_open_settings\', \'_open_find_dialog\', \'_open_replace_dialog\', \'_open_batch_dialog\', \'_open_compare_dialog\', \'_open_export_dialog\', \'_open_encoding_dialog\', \'_open_regex_builder_dialog\', \'_open_preset_manager_dialog\', \'_open_preset_editor_dialog\', \'_open_watch_folder_dialog\')\n\n#: Rules that put an ink on a gold, found in each mode on 2026-10-13. Fewer\n#: and the reader has gone blind.\nMIN_INKED = {\'dark\': 11, \'light\': 20, \'image\': 20}\n\n#: The modes the theme button must reach here. A mode it reaches beyond them\n#: is read as well.\nMODES = (\'dark\', \'light\', \'image\')\n\n#: What was found against the ruling and is held as found while a ruling is\n#: asked on it, -> why: ("rule", mode, selector, gold, ink) for a rule of a\n#: sheet, ("palette", mode, gold, ink) for a palette. One that is no longer\n#: found fails: take it out.\nHELD = {}\n\n\ndef _mode(win) -> str:\n    tm = getattr(win, "theme_manager", None) or win.ui_handler.theme_manager\n    return "image" if tm.is_image_mode() else str(tm.current_theme)\n\n\ndef _prepare(win) -> None:\n    """What the windows need before every opener shows one."""\n    body = "The quick brown fox\\njumps over the lazy dog.\\n" * 20\n    win.text_input.setPlainText(body)\n    win.output_text.setPlainText(body.upper())\n\n#: The ruled ink for text on each gold fill: white on the dark gold, black on\n#: the bright gold.\nGOLD_INK = {"#8c7337": "#ffffff", "#d2bc93": "#000000"}\nGOLD_NAME = {"#8c7337": "the dark gold", "#d2bc93": "the bright gold"}\n\nHEX = re.compile(r"#[0-9a-fA-F]{6}(?![0-9a-fA-F])")\nRULE = re.compile(r"([^{}]+)\\{([^{}]*)\\}")\nDECL = re.compile(r"([a-zA-Z-]+)\\s*:\\s*([^;]+);?")\n#: A part of a widget that holds no text. A gold fill there needs no ink.\nTEXT_FREE = re.compile(r"::(?:indicator|handle|chunk|sub-page|add-page|up-button|down-button|groove|"\n                       r"add-line|sub-line|up-arrow|down-arrow|branch)\\b")\n#: The palettes\' two colour groups text is drawn in.\nGROUPS = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)\n\n\ndef _rules(sheet: str):\n    """(selector, {property: value}) for each rule of a sheet, as Qt reads it.\n    A sheet with no braces is a list of declarations set on one widget."""\n    sheet = re.sub(r"/\\*.*?\\*/", "", sheet, flags=re.S)\n    if "{" not in sheet:\n        yield "(the widget itself)", {k.lower(): v.strip() for k, v in DECL.findall(sheet)}\n        return\n    for selector, body in RULE.findall(sheet):\n        yield " ".join(selector.split()), {k.lower(): v.strip() for k, v in DECL.findall(body)}\n\n\ndef _gold(value: str):\n    """The gold a value fills with, or None."""\n    for found in HEX.findall(value or ""):\n        if found.lower() in GOLD_INK:\n            return found.lower()\n    return None\n\n\ndef _ink(value):\n    """A colour written in a rule, as #rrggbb: None when the rule sets none."""\n    if not value:\n        return None\n    found = HEX.findall(value)\n    if found:\n        return found[0].lower()\n    return QColor(value.strip()).name() if QColor.isValidColorName(value.strip()) else value.strip().lower()\n\n\ndef _fills(top: QWidget, where: str) -> list:\n    """(where, holder, selector, kind, gold, ink) for each rule of every sheet\n    the window and the application hold that fills with a gold."""\n    sheets = [("(application)", QApplication.instance().styleSheet())]\n    sheets += [(type(w).__name__, w.styleSheet()) for w in [top] + top.findChildren(QWidget) if w.styleSheet()]\n    out = []\n    for holder, sheet in sheets:\n        for selector, decl in _rules(sheet):\n            gold = _gold(decl.get("background-color", "")) or _gold(decl.get("background", ""))\n            if gold:\n                out.append((where, holder, selector, "fill", gold, _ink(decl.get("color"))))\n            gold = _gold(decl.get("selection-background-color", ""))\n            if gold:\n                out.append((where, holder, selector, "selection", gold, _ink(decl.get("selection-color"))))\n    return out\n\n\ndef _palettes(top: QWidget, where: str) -> list:\n    """(where, holder, highlight, highlighted text) for the application\'s\n    palette and the window\'s, in each group text is drawn in: the ink a\n    selection takes where no rule of a sheet sets one. A palette a widget is\n    given for itself is not read: what it would draw, a sheet\'s rule draws\n    over (a combo box\'s list in image mode, read back from its pixels on\n    2026-10-13), and 1 holds the rules."""\n    held = [("(application)", QApplication.instance().palette()), (type(top).__name__, top.palette())]\n    out = set()\n    for holder, palette in held:\n        for group in GROUPS:\n            out.add((where, holder, palette.color(group, QPalette.ColorRole.Highlight).name(),\n                     palette.color(group, QPalette.ColorRole.HighlightedText).name()))\n    return sorted(out)\n\n\ndef _settle(ms: int = 150) -> None:\n    loop = QEventLoop()\n    QTimer.singleShot(ms, loop.quit)\n    loop.exec()\n    QApplication.processEvents()\n\n\ndef _shown(self, *_a, **_k):\n    """A modal dialog\'s exec(), shown and returned from at once."""\n    _KEEP.append(self)\n    self.show()\n    QApplication.processEvents()\n    return 0\n\n\n_KEEP: list = []\n_TOUR: dict = {}\n\n\ndef _tour(win, monkeypatch) -> dict:\n    """mode -> (fills, palettes), the main window and every window its\n    openers show, in each mode the theme button reaches. Taken once; the\n    theme button is pressed round to where it started."""\n    if _TOUR:\n        return _TOUR\n    monkeypatch.setattr(QDialog, "exec", _shown)\n    monkeypatch.setattr(QMessageBox, "exec", _shown)\n    for name in ("warning", "information", "critical", "question"):\n        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))\n    for name in ("getOpenFileName", "getOpenFileNames", "getSaveFileName"):\n        monkeypatch.setattr(QFileDialog, name, staticmethod(lambda *a, **k: ("", "")))\n    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: ""))\n    _prepare(win)\n    tour, start = {}, _mode(win)\n    for _ in range(4):\n        mode = _mode(win)\n        if mode in tour:\n            break\n        fills, palettes = _fills(win, "main window"), _palettes(win, "main window")\n        for opener in OPENERS:\n            before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}\n            getattr(win, opener)()\n            _settle()\n            for shown in [w for w in QApplication.topLevelWidgets()\n                          if w.isVisible() and id(w) not in before and w is not win]:\n                fills += _fills(shown, opener)\n                palettes += _palettes(shown, opener)\n                shown.close()\n            _settle(50)\n        tour[mode] = (fills, palettes)\n        win.theme_button.click()\n        _settle()\n    assert _mode(win) == start, f"the theme button did not come back round to {start}"\n    _TOUR.update(tour)\n    return _TOUR\n\n\ndef test_every_ink_on_a_gold_is_the_ruled_one(window, monkeypatch):\n    seen, wrong = set(), []\n    for mode, (fills, _p) in _tour(window, monkeypatch).items():\n        for where, holder, selector, _kind, gold, ink in fills:\n            if ink and ink != GOLD_INK[gold]:\n                if ("rule", mode, selector, gold, ink) in HELD:\n                    seen.add(("rule", mode, selector, gold, ink))\n                    continue\n                wrong.append(f"{mode}, {where} ({holder}): {selector} puts {ink} on {GOLD_NAME[gold]}, "\n                             f"not {GOLD_INK[gold]}")\n    assert not wrong, ("text on the gold fill is ruled: white on the dark gold, black on the bright "\n                       "gold (2026-10-11, item 4):\\n  " + "\\n  ".join(sorted(set(wrong))))\n    stale = sorted(k for k in set(HELD) - seen if k[0] == "rule")\n    assert not stale, f"held as found and no longer found: {stale}. Take it out of HELD."\n\n\ndef test_a_gold_fill_without_an_ink_holds_no_text(window, monkeypatch):\n    """A selection that sets no ink takes the palette\'s, which the next test holds."""\n    bare = [f"{mode}, {where} ({holder}): {selector}"\n            for mode, (fills, _p) in _tour(window, monkeypatch).items()\n            for where, holder, selector, kind, _gold, ink in fills\n            if ink is None and kind == "fill" and not TEXT_FREE.search(selector)]\n    assert not bare, ("a rule fills with a gold under text and leaves the ink to whatever the "\n                      "widget inherits:\\n  " + "\\n  ".join(sorted(set(bare))))\n\n\ndef test_every_window_palette_that_highlights_in_a_gold_gives_its_ink(window, monkeypatch):\n    seen, wrong = set(), []\n    for mode, (_f, palettes) in _tour(window, monkeypatch).items():\n        for where, holder, highlight, text in palettes:\n            if highlight in GOLD_INK and text != GOLD_INK[highlight]:\n                if ("palette", mode, highlight, text) in HELD:\n                    seen.add(("palette", mode, highlight, text))\n                    continue\n                wrong.append(f"{mode}, {where} ({holder}): highlighted text {text} on {GOLD_NAME[highlight]}")\n    assert not wrong, ("a palette highlights in a gold and gives the highlighted text another ink "\n                       "than the ruled one:\\n  " + "\\n  ".join(sorted(set(wrong))))\n    stale = sorted(k for k in set(HELD) - seen if k[0] == "palette")\n    assert not stale, f"held as found and no longer found: {stale}. Take it out of HELD."\n\n\ndef test_the_reader_is_looking(window, monkeypatch):\n    """A reader that finds nothing passes every test above."""\n    tour = _tour(window, monkeypatch)\n    assert set(MODES) <= set(tour), f"the theme button reached {sorted(tour)}, not {sorted(MODES)}"\n    for mode, (fills, palettes) in tour.items():\n        inked = {(selector, kind, gold) for _w, _h, selector, kind, gold, ink in fills if ink}\n        assert len(inked) >= MIN_INKED.get(mode, 1), (\n            f"{mode}: the reader finds {len(inked)} rules that put an ink on a gold, not {MIN_INKED.get(mode, 1)}")\n        reached = {where for where, *_rest in fills} | {where for where, *_rest in palettes}\n        assert set(OPENERS) <= reached, f"{mode}: no window was read from {sorted(set(OPENERS) - reached)}"\n    sample = ("/* a comment { } */ QPushButton:pressed { background-color: #8C7337; color: white; }\\n"\n              "QLineEdit, QSpinBox { selection-background-color: #d2bc93; selection-color: #000; }\\n"\n              "QSlider::handle:horizontal { background: #8c7337; }\\n"\n              "QComboBox QAbstractItemView { selection-background-color: #d2bc93; }\\n"\n              "QLabel { background-color: #8c73370a; color: #ffffff; }\\n")\n    probe = QWidget()\n    probe.setStyleSheet(sample)\n    try:\n        found = [f[2:] for f in _fills(probe, "sample") if f[1] == "QWidget"]\n    finally:\n        probe.deleteLater()\n    assert found == [("QPushButton:pressed", "fill", "#8c7337", "#ffffff"),\n                     ("QLineEdit, QSpinBox", "selection", "#d2bc93", "#000000"),\n                     ("QSlider::handle:horizontal", "fill", "#8c7337", None),\n                     ("QComboBox QAbstractItemView", "selection", "#d2bc93", None)], found\n    assert TEXT_FREE.search("QSlider::handle:horizontal") and not TEXT_FREE.search("QPushButton:pressed")\n')
    tree.delete('tests/tests_conftest.py')


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
    check_moves([('RNV_Text_Transformer.py', [], [], []), ('tests/test_gold_as_text.py', [], [], []), ('ui/base_dialog.py', ['BaseDialog._in_qt()', 'BaseDialog._text_index()'], [], []), ('ui/find_replace_dialog.py', [], ['FindReplaceDialog._in_qt()', 'FindReplaceDialog._text_index()'], []), ('ui/regex_builder_dialog.py', [], [], ['RegexBuilderDialog._highlight_matches()', 'RegexBuilderDialog._on_match_clicked()'])])
    # ---- item 28: the stale copy goes, and nothing named it
    assert "tests/tests_conftest.py" in tree.deleted, "tests/tests_conftest.py is still there"
    near = set(p.relative_to(tree.root).as_posix() for p in list(tree.root.glob("*.py")) + list(tree.root.glob("tests/*.py")))
    for rel in sorted((near | set(r for r in tree.files if r.endswith(".py"))) - tree.deleted):
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" not in as_written(rel):
            assert "tests_conftest" not in names_in(as_written(rel)), f"{rel} imports tests_conftest"
    # ---- item 29
    assert "Clipboard history" not in tree.read("RNV_Text_Transformer.py"), "the header still lists Clipboard history"
    # ---- item 30: the conversion moves unchanged, and the Regex Builder uses it where it draws and selects
    was = code(_original(tree, "ui/find_replace_dialog.py"))
    base, find = code(tree.read("ui/base_dialog.py")), code(tree.read("ui/find_replace_dialog.py"))
    builder = code(tree.read("ui/regex_builder_dialog.py"))
    for name in ("_in_qt", "_text_index"):
        assert base.get(f"BaseDialog.{name}()") == was[f"FindReplaceDialog.{name}()"], \
            f"(30) {name}() is not in BaseDialog as it was in Find"
        assert f"FindReplaceDialog.{name}()" not in find, f"(30) Find keeps a copy of {name}()"
    assert "self._in_qt(" in builder["RegexBuilderDialog._highlight_matches()"], \
        "(30) the Regex Builder draws highlights at positions as Python counts them"
    assert "self._in_qt(" in builder["RegexBuilderDialog._on_match_clicked()"], \
        "(30) a click on a match selects at positions as Python counts them"
    assert "from bisect import bisect_left" in tree.read("ui/base_dialog.py") \
        and "bisect" not in tree.read("ui/find_replace_dialog.py"), "(30) the import did not move with the conversion"

    # ================= item 32: the guard, as this round writes it, holding what this round found
    import hashlib
    got = hashlib.sha256(tree.read(INK_GUARD).encode("utf-8")).hexdigest()
    assert got == 'dc99450ad2ce40a45d164e178376577aa462ab3a995a454b3da9db06b39f6b40', f"{INK_GUARD} is not the file this round writes: {got[:12]}"
    ink = tree.read(INK_GUARD)
    assert tests_in(ink) == ['test_every_ink_on_a_gold_is_the_ruled_one', 'test_a_gold_fill_without_an_ink_holds_no_text', 'test_every_window_palette_that_highlights_in_a_gold_gives_its_ink', 'test_the_reader_is_looking'], f"{INK_GUARD}: its tests are {tests_in(ink)}"
    values = dict()
    for node in ast.parse(ink).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("GOLD_INK", "OPENERS", "MODES", "MIN_INKED", "HELD"):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    assert values['GOLD_INK'] == {'#8c7337': '#ffffff', '#d2bc93': '#000000'}, f"{INK_GUARD} holds GOLD_INK = {values['GOLD_INK']}"
    assert values['HELD'] == {}, f"{INK_GUARD} holds HELD = {values['HELD']}"
    assert values['MIN_INKED'] == {'dark': 11, 'light': 20, 'image': 20}, f"{INK_GUARD} holds MIN_INKED = {values['MIN_INKED']}"
    assert values['MODES'] == ('dark', 'light', 'image'), f"{INK_GUARD} holds MODES = {values['MODES']}"
    assert values['OPENERS'] == ('_open_about_dialog', '_open_settings', '_open_find_dialog', '_open_replace_dialog', '_open_batch_dialog', '_open_compare_dialog', '_open_export_dialog', '_open_encoding_dialog', '_open_regex_builder_dialog', '_open_preset_manager_dialog', '_open_preset_editor_dialog', '_open_watch_folder_dialog'), f"{INK_GUARD} holds OPENERS = {values['OPENERS']}"
    assert values["GOLD_INK"] == {"#8c7337": "#ffffff", "#d2bc93": "#000000"}, "the guard does not hold the ruling"
    source = "\n".join(text for _rel, text in app_sources())
    missing = [o for o in values["OPENERS"] if f"def {o}(" not in source]
    assert not missing, f"the main window defines no {missing}: the guard would open nothing there"

    # ================= every other file this round creates, as this round writes it
    import hashlib
    for rel, sha in (('tests/test_regex_builder_highlights_the_match.py', '1d37015f82aa85cebc2b0a6cb7c5c4ba39c1e1b01256644f18a4a9bb1569f91d'),):
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == sha, f"{rel} is not the file this round writes: {got[:12]}"

    import hashlib
    # ================= what goes is what was read: each file this round deletes is, on disk, the file the
    # round was derived from. One edited since would go with whatever it gained.
    for rel, sha in (('tests/tests_conftest.py', '7ccef351c924ec4a9780154377be293b3e046531e498452a3f17f4f0c8e836dd'),):
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
