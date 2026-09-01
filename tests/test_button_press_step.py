"""
The main button's pressed state is declared in the stylesheet, not assembled
in Python.

RULED 2026-08-26.

WHAT WAS WRONG, AND IT WAS NOT THE COLOURS

The app already had a press state: `_on_press` rewrote the base rule's label
colour, and image mode swapped to a dedicated pressed pixmap. Under the mouse
it looked right. It was reached two ways that do not hold up:

  1. THE GROUND CAME FROM `:hover`. Pressed and hovered are different states
     that merely coincide under a mouse. Press the button any other way --
     Space or Enter on a focused button, a programmatic click(), or holding
     the mouse down and dragging off -- and `:hover` stops matching while the
     label stays flipped. Measured on this palette:

         DARK   #000000 on #1a1a1a = 1.21:1
         LIGHT  #ffffff on #ffffff = 1.00:1   -- white on white

  2. A RESIZE WHILE HELD REVERTED THE LABEL. `resizeEvent` calls
     `update_text_font_size`, which rebuilds the stylesheet with no text_color
     argument, so the label fell back to resting while `is_pressed_state` was
     still True. The image-mode branch of the same method checks
     `is_pressed_state`; the text branch did not.

Both disappear once `QPushButton:pressed` carries the ground AND the label.
Qt applies that rule to the sunken state however the press arrived -- verified
against `setDown(True)`, which is the path keyboard activation takes -- and
being declarative it survives every stylesheet rebuild.

`_update_text_mode_pressed` still runs and still sets the same label colour.
It is now reinforcement rather than the mechanism, and the tests below hold
the stylesheet, which is the thing that has to be right.
"""
from __future__ import annotations

import collections
import re

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from utils.dialog_styles import DialogStyleManager

THEMES = {"DARK": True, "LIGHT": False}


def _lum(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:                      # Qt #AARRGGBB
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_both_palettes_carry_the_button_keys():
    """Guard the guard. Every test below reads these; a rename that emptied
    them would leave the rest passing while checking nothing."""
    for name, is_dark in THEMES.items():
        colors = DialogStyleManager.get_colors(is_dark)
        for key in ("main_btn_bg", "main_btn_hover_bg", "main_btn_pressed_bg",
                    "main_btn_text", "main_btn_pressed_text"):
            assert key in colors, f"{name} has no {key}"


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_plate_steps_on_press(name):
    colors = DialogStyleManager.get_colors(THEMES[name])
    hover, pressed = colors["main_btn_hover_bg"], colors["main_btn_pressed_bg"]
    assert hover != pressed, (
        f"{name}: the pressed plate is the hover plate, so a press changes "
        f"only the label")
    assert _lum(pressed) > _lum(hover), (
        f"{name}: pressed plate {pressed} does not lift from hover {hover}")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_label_inverts_on_press(name):
    colors = DialogStyleManager.get_colors(THEMES[name])
    resting, pressed = colors["main_btn_text"], colors["main_btn_pressed_text"]
    assert (_lum(resting) > 0.5) != (_lum(pressed) > 0.5), (
        f"{name}: {resting} -> {pressed} is not an inversion")


def _rule(css: str, selector: str) -> dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert match, f"no {selector} rule in the rendered stylesheet"
    return {k.strip(): v.strip()
            for k, _, v in (d.partition(":") for d in match.group(1).split(";"))
            if k.strip()}


def _button(qtbot, is_dark: bool):
    from ui.image_button import ImageButton

    colors = DialogStyleManager.get_colors(is_dark)

    class _Stub:
        def __init__(self, c): self.colors = c
        def is_image_mode(self): return False

    button = ImageButton("copy", "Export")
    qtbot.addWidget(button)
    button.theme_manager = _Stub(colors)
    button.resize(180, 48)
    button.apply_style()
    return button, colors


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_pressed_rule_carries_the_ground_and_the_label(name, qtbot):
    """The whole pressed appearance must live in one rule.

    Splitting it -- ground from `:hover`, label from Python -- is what made a
    keyboard press render white on white.
    """
    button, colors = _button(qtbot, THEMES[name])
    rule = _rule(button.styleSheet(), "QPushButton:pressed")
    assert rule.get("background-color") == colors["main_btn_pressed_bg"], (
        f"{name}: the pressed rule does not carry the pressed plate")
    assert rule.get("color") == colors["main_btn_pressed_text"], (
        f"{name}: the pressed rule does not carry the pressed label, so the "
        f"label depends on the Python path and any press without a hover "
        f"renders it on the resting plate")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_a_press_without_a_hover_is_still_legible(name, qtbot):
    """The regression itself, rendered.

    `setDown(True)` is the state keyboard activation puts the button in --
    sunken, not hovered. Before the pressed rule existed this drew the flipped
    label on the resting plate: 1.21:1 in dark, and white on white in light.
    """
    button, colors = _button(qtbot, THEMES[name])
    button.show()
    # Both halves of a real keyboard press: the app's own press handler runs
    # (it flips the label in the base rule) and Qt sinks the button. What does
    # NOT happen is a hover, and that was the load-bearing assumption.
    button._on_press()
    button.setDown(True)
    button.style().unpolish(button)
    button.style().polish(button)

    pixmap = QPixmap(button.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    button.render(pixmap)
    image = pixmap.toImage()

    seen = collections.Counter()
    for y in range(6, button.height() - 6):
        for x in range(6, button.width() - 6):
            px = image.pixel(x, y)
            seen[((px >> 16) & 255, (px >> 8) & 255, px & 255)] += 1
    ordered = seen.most_common()
    plate = ordered[0][0]
    ink = next((c for c, _ in ordered[1:]
                if abs(sum(c) - sum(plate)) > 90), None)
    assert ink is not None, (
        f"{name}: no label pixels distinguishable from the plate while the "
        f"button is down -- the label is invisible")

    as_hex = lambda c: "#%02x%02x%02x" % c
    ratio = _contrast(as_hex(plate), as_hex(ink))
    assert ratio > 2.0, (
        f"{name}: label {as_hex(ink)} on plate {as_hex(plate)} = {ratio:.2f}:1 "
        f"while down without a hover")
