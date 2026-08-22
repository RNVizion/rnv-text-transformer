"""The error red: one registered value, one derivative, and an honest gap.

    STATUS_ERROR        #dc3545   register -- fills, borders, dark text
    STATUS_ERROR_LIGHT  #c82131   derived  -- text on a light dialog ground

Dark is SHORT and is not fixed here. That is a decision, and the test which
records it fails in both directions so it cannot outlive the problem.
"""

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

TEXT_FLOOR = 4.5


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
             for x in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def test_the_light_error_red_is_derived_not_written():
    """A written-down derivative orphans the moment its base moves -- which
    is what happened to #c4a458 when the gold it tinted was retired."""
    assert colors.STATUS_ERROR_LIGHT == colors.lighten(colors.STATUS_ERROR, -20)
    assert colors.STATUS_ERROR_LIGHT != colors.STATUS_ERROR


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])
def test_light_error_text_carries_to_the_published_boundary(ground):
    """#e8e8e8 is where the gold stops carrying text. The red is derived to
    the same boundary so the two rules need not be remembered separately."""
    ratio = contrast(colors.STATUS_ERROR_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_LIGHT} on {ground} = {ratio:.4f}"


def test_the_light_dialog_palette_uses_the_derivative():
    light = DialogStyleManager.get_colors(False)
    assert light["error"] == colors.STATUS_ERROR_LIGHT
    assert contrast(light["error"], light["bg"]) >= TEXT_FLOOR


def test_the_dark_dialog_palette_still_uses_the_register_value():
    """Dark is not touched by this pass. Asserted so a later change cannot
    move it quietly while nobody is looking at dark."""
    dark = DialogStyleManager.get_colors(True)
    assert dark["error"] == colors.STATUS_ERROR


def test_dark_error_text_is_short_and_that_is_recorded():
    """A TWO-WAY exemption.

    Dark error text reads 3.8441 on #1a1a1a and 3.1703 on #2a2a2a. The ruling
    of this pass left dark alone: the other apps' dark reds pass on their
    grounds and replacing a colour that is not broken to buy uniformity is a
    bigger change than the problem justifies. This app's dark red does NOT
    pass, so the gap is written down rather than left to be rediscovered.

    The second assertion is the important half. If a dark derivative is ever
    ruled -- lighten(STATUS_ERROR, +32) = #fc5565 is the natural candidate,
    5.4918 on #1a1a1a and 4.5291 on #2a2a2a -- this test goes red and tells
    whoever did it to delete the exemption. An exemption that outlives its
    problem is a licence waiting for a future defect.
    """
    dark = DialogStyleManager.get_colors(True)
    for ground, measured in (("#1a1a1a", 3.8441), ("#2a2a2a", 3.1703)):
        ratio = contrast(dark["error"], ground)
        assert ratio >= measured - 0.0001, (
            f"dark error text regressed to {ratio:.4f} on {ground}, below the "
            f"{measured} recorded when this exemption was written")
        assert ratio < TEXT_FLOOR, (
            f"dark error text now measures {ratio:.4f} on {ground} and CLEARS "
            f"the floor. A dark error red has presumably been ruled -- delete "
            f"this test and its exemption rather than leaving a standing note "
            f"about a problem that no longer exists.")


def test_the_delete_button_reads_the_palette_for_its_own_mode(qtbot):
    """The bypass this pass removed.

    ui/preset_dialog.py painted the delete button from DialogStyleManager.DARK
    unconditionally. It rendered the same value in both modes only because
    light and dark shared one error red; giving light its own turned it into
    a real defect on the one control that skipped the palette.
    """
    from core.preset_manager import PresetStep
    from ui.preset_dialog import StepEditorWidget

    step = PresetStep(action="uppercase")
    for is_dark, expected in ((True, colors.STATUS_ERROR),
                              (False, colors.STATUS_ERROR_LIGHT)):
        widget = StepEditorWidget(step, is_dark=is_dark)
        qtbot.addWidget(widget)
        sheets = [child.styleSheet() for child in widget.findChildren(object)
                  if hasattr(child, "styleSheet")]
        assert any(expected in sheet for sheet in sheets), (
            f"is_dark={is_dark}: no child carries {expected}")
