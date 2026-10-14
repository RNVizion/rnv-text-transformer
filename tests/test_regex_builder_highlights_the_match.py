"""The Regex Builder highlights and selects a match where it is.

RNV-RULINGS-2026-10-13, item 30. Ruled 2026-10-13: "A".

WHAT WAS THERE. The Regex Builder found its matches in the text as Python
holds it, where a character outside the basic plane, an emoji, is one
position, and drew them where the test pane counts, which counts it as two.
Measured on 2026-10-11 in "😀 fox, 😀😀 the fox" with the pattern fox: the
highlights sat on " fo" and "he ". A click on a match in the table selected
the same wrong characters. It was the fault Find had until item 24 (d) of
2026-10-11.

WHAT IS THERE NOW. Both count positions as the pane counts them, with the
conversion Find uses. It moved to BaseDialog, beside the function that
draws highlights.

WHAT THIS GUARD HOLDS, through the main window's own Regex Builder:

1. The highlights sit on the matches after an emoji, with groups and
   without.
2. A click on a match in the table selects that match.
3. Every function that draws highlights converts the positions it is
   given: each one that calls _show_highlights() calls _in_qt() too.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
from PyQt6.QtWidgets import QApplication

from ui.regex_builder_dialog import RegexBuilderDialog

ROOT = pathlib.Path(__file__).resolve().parents[1]
EMOJI = "\U0001F600"
TEXT = f"{EMOJI} fox, {EMOJI}{EMOJI} the fox\n"


def _utf16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


@pytest.fixture
def builder(main_window):
    """The main window's own Regex Builder, opened on TEXT in the input."""
    win = main_window
    win.settings_manager.save_auto_transform(False)
    win.auto_transform_timer.stop()
    win.text_input.setPlainText(TEXT)
    win.auto_transform_timer.stop()
    before = {id(d) for d in win.findChildren(RegexBuilderDialog)}
    win._open_regex_builder_dialog()
    QApplication.processEvents()
    new = [d for d in win.findChildren(RegexBuilderDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, len(new)
    dlg = new[0]

    def matching(pattern: str) -> RegexBuilderDialog:
        dlg.pattern_input.setText(pattern)
        dlg._update_timer.stop()
        dlg._update_matches()
        return dlg
    yield matching
    dlg.close()


def _highlighted(edit) -> list:
    return [s.cursor.selectedText() for s in edit.extraSelections() if s.cursor.hasSelection()]


@pytest.mark.parametrize("pattern", ["fox", "f(o)x", "(?P<first>f)ox"])
def test_the_highlights_sit_on_the_matches(builder, pattern):
    dlg = builder(pattern)
    assert dlg.test_text.toPlainText() == TEXT
    assert len(dlg._current_matches) == 2
    assert _highlighted(dlg.test_text) == ["fox", "fox"], \
        f"the highlights sit on {_highlighted(dlg.test_text)}"


def test_a_click_on_a_match_selects_it(builder):
    dlg = builder("fox")
    dlg._on_match_clicked(dlg.matches_table.item(1, 0))
    cursor = dlg.test_text.textCursor()
    assert cursor.selectedText() == "fox", f"the click selected {cursor.selectedText()!r}"
    assert cursor.selectionStart() == _utf16(f"{EMOJI} fox, {EMOJI}{EMOJI} the ")


def _drawers() -> dict:
    """(file, function) -> whether it converts, for every function in ui/
    that calls _show_highlights()."""
    found = {}
    for path in sorted((ROOT / "ui").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = {c.func.attr for c in ast.walk(node)
                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
            if "_show_highlights" in calls:
                found[(path.name, node.name)] = "_in_qt" in calls
    return found


def test_every_function_that_draws_highlights_converts_the_positions():
    drawers = _drawers()
    assert {("find_replace_dialog.py", "_highlight_all_matches"),
            ("regex_builder_dialog.py", "_highlight_matches")} <= set(drawers), \
        f"the reader does not find the two dialogs that draw highlights: {sorted(drawers)}"
    raw = sorted(where for where, converts in drawers.items() if not converts)
    assert not raw, ("these draw highlights at positions as Python counts them, which the pane "
                     f"counts otherwise after an emoji: {raw}. Pass them through _in_qt().")
