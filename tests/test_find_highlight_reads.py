"""
tests/test_find_highlight_reads.py
==================================
Ruling 101 B, 2026-10-26. The text on a Find match reads, in every mode.

Find shows each match as an extra selection: the mode's accent at an alpha,
laid over the text pane. Brand Infrastructure measured the composite in
BRAND_COLORS.md rev 47. In image mode the pane is TRUE_BLACK at
IMAGE_FIELD_ALPHA over the background picture, and a match at
FIND_HIGHLIGHT_ALPHA under the pane's light text read 3.36:1 over a bright
part of the picture. The register's rule for an alpha under text over a
picture: the ink clears 4.5 against the composite over black AND over white,
and is darker than both or lighter than both. Every picture lies between the two.

Now image mode paints the matches at IMAGE_FIND_HIGHLIGHT_ALPHA with black
text, and dark and light keep FIND_HIGHLIGHT_ALPHA under the pane's own
text, on its opaque ground.

Each test drives the main window's own Find, in each mode, reads the
highlights it shows (their fill, and their ink or the pane's), and composites
the fill in eight bits, as Qt does. A switch with the dialog open paints
the same as a Find run in the new mode.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

import utils.colors as C
from ui.base_dialog import BaseDialog
from utils.dialog_styles import DialogStyleManager

FLOOR = 4.5
TEXT = "Pack my box with five dozen liquor jugs.\nHow vexingly quick daft zebras jump over the log.\n"
MODES = ("dark", "light", "image")


def _rgb(color: QColor) -> tuple[int, int, int]:
    return color.red(), color.green(), color.blue()


def _over(top: QColor, ground: tuple[int, int, int]) -> tuple[int, int, int]:
    """top at its alpha over an opaque ground, in eight bits."""
    a = top.alpha()
    return tuple(round((t * a + g * (255 - a)) / 255) for t, g in zip(_rgb(top), ground))


def _luminance(rgb: tuple[int, int, int]) -> float:
    chans = [c / 255 for c in rgb]
    chans = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def _contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _to_mode(win, mode: str) -> None:
    for _ in range(3):
        if win.theme_manager.current_theme == mode:
            return
        win._cycle_theme()
        QApplication.processEvents()
    assert win.theme_manager.current_theme == mode


def _find(win):
    before = {id(d) for d in win.findChildren(BaseDialog)}
    win._open_find_dialog()
    QApplication.processEvents()
    dlg = [d for d in win.findChildren(BaseDialog) if id(d) not in before and d.isVisible()][0]
    dlg.find_input.setText("o")
    dlg._on_find()
    QApplication.processEvents()
    return dlg


def _shown(edit) -> list[tuple[QColor, QColor | None]]:
    """(fill, ink or None) of every highlight shown over the text."""
    out = []
    for selection in edit.extraSelections():
        fmt = selection.format
        fill = fmt.background()
        if selection.cursor.hasSelection() and fill.style() != Qt.BrushStyle.NoBrush:
            ink = fmt.foreground()
            out.append((QColor(fill.color()),
                        QColor(ink.color()) if ink.style() != Qt.BrushStyle.NoBrush else None))
    return out


def _grounds(win, mode: str) -> list[tuple[int, int, int]]:
    """What a match lies on: the pane's opaque ground, or in image mode the
    pane's translucent black over the darkest and the lightest picture."""
    theme = win.theme_manager.colors
    if mode != "image":
        return [_rgb(QColor(theme["input_bg"]))]
    field = QColor(DialogStyleManager.DARK["image_overlay_bg"])
    assert field.alpha() < 255, "the image-mode pane is opaque now: this guard's premise moved"
    return [_over(field, _rgb(QColor(C.TRUE_BLACK))), _over(field, _rgb(QColor(C.WHITE)))]


@pytest.mark.parametrize("mode", MODES)
def test_the_text_on_a_match_reads(main_window, mode):
    win = main_window
    _to_mode(win, mode)
    win.text_input.setPlainText(TEXT)
    dlg = _find(win)
    shown = _shown(win.text_input)
    assert len(shown) >= 5, f"{mode}: Find showed {len(shown)} highlights; nothing was tested"
    pane_ink = QColor(win.theme_manager.colors["input_text"])
    for fill, ink in shown:
        ink = _rgb(ink if ink is not None else pane_ink)
        composites = [_over(fill, g) for g in _grounds(win, mode)]
        for composite in composites:
            ratio = _contrast(composite, ink)
            assert ratio >= FLOOR, f"{mode}: text {ink} on a match {composite} reads {ratio:.2f}:1"
        darker = [_luminance(ink) < _luminance(c) for c in composites]
        assert all(darker) or not any(darker), f"{mode}: the ink lies between the composites"
    dlg.close()


def test_image_mode_puts_black_text_on_the_brighter_alpha(main_window):
    win = main_window
    _to_mode(win, "image")
    win.text_input.setPlainText(TEXT)
    dlg = _find(win)
    shown = _shown(win.text_input)
    assert shown
    assert {fill.alpha() for fill, _ in shown} == {C.IMAGE_FIND_HIGHLIGHT_ALPHA}
    assert {_rgb(ink) for _, ink in shown if ink is not None} == {_rgb(QColor(C.TRUE_BLACK))}
    assert all(ink is not None for _, ink in shown)
    dlg.close()


@pytest.mark.parametrize("start, end", [("image", "dark"), ("dark", "image")])
def test_a_switch_with_find_open_paints_the_new_modes_highlight(main_window, start, end):
    """The repaint on a switch carries the ink too: on, into image mode; off, out of it."""
    win = main_window
    _to_mode(win, start)
    win.text_input.setPlainText(TEXT)
    dlg = _find(win)
    _to_mode(win, end)
    shown = _shown(win.text_input)
    assert shown
    want_alpha = C.IMAGE_FIND_HIGHLIGHT_ALPHA if end == "image" else C.FIND_HIGHLIGHT_ALPHA
    assert {fill.alpha() for fill, _ in shown} == {want_alpha}, end
    inks = {None if ink is None else _rgb(ink) for _, ink in shown}
    assert inks == ({_rgb(QColor(C.TRUE_BLACK))} if end == "image" else {None}), (start, end, inks)
    dlg.close()
