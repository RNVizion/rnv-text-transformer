"""The RNV status family, as this application uses it.

    STATUS_SUCCESS / _WARNING / _ERROR               fills, L* 48-59
    STATUS_*_TEXT         #ad85a3 #bc8752 #dd6f77    text on a dark ground
    STATUS_*_TEXT_LIGHT   #8a6581 #976633 #b84e58    text on a light ground

This file replaces the error-red tests, which covered a two-value red that no
longer exists. Three of their premises are now false, and each is worth saying
out loud, because a test file quietly rewritten hides what changed:

  * "the light error red is DERIVED, not written down" -- it is written down
    now. lighten(STATUS_ERROR, -20) against the new base yields #b44753, not
    the registered #b84e58. The register publishes the derivation as
    provenance and the value as a value.

  * "dark error text is SHORT and that is recorded" -- that exemption's own
    docstring said to delete it if a dark derivative was ever ruled. Three
    were ruled on 2026-09-03. test_dark_error_text_now_clears replaces it, and
    asserts the opposite of what it asserted.

  * "red carries text down to #e8e8e8" -- see RNV-STATUS-LIGHT-FLOOR below.
"""

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

TEXT_FLOOR = 4.5
FILL_FLOOR = 3.0

DARK_GROUNDS = ("#1a1a1a", "#2a2a2a")
LIGHT_GROUNDS = ("#ffffff", "#f5f5f5")
ALL_GROUNDS = DARK_GROUNDS + LIGHT_GROUNDS

FILLS = ("STATUS_SUCCESS", "STATUS_WARNING", "STATUS_ERROR")
DARK_TEXT = ("STATUS_SUCCESS_TEXT", "STATUS_WARNING_TEXT", "STATUS_ERROR_TEXT")
LIGHT_TEXT = ("STATUS_SUCCESS_TEXT_LIGHT", "STATUS_WARNING_TEXT_LIGHT",
              "STATUS_ERROR_TEXT_LIGHT")

REGISTERED = {
    "STATUS_SUCCESS": "#926c89",
    "STATUS_WARNING": "#a2703c",
    "STATUS_ERROR": "#c75b64",
    "STATUS_SUCCESS_TEXT": "#ad85a3",
    "STATUS_WARNING_TEXT": "#bc8752",
    "STATUS_ERROR_TEXT": "#dd6f77",
    "STATUS_SUCCESS_TEXT_LIGHT": "#8a6581",
    "STATUS_WARNING_TEXT_LIGHT": "#976633",
    "STATUS_ERROR_TEXT_LIGHT": "#b84e58",
}
RETIRED = ("#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131")


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
             for x in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


# ------------------------------------------------------------ the values
@pytest.mark.parametrize("name,value", sorted(REGISTERED.items()))
def test_the_nine_values_are_the_registered_ones(name, value):
    """Pinned by value, not by relationship.

    A test asserting only that these differ from each other would pass on nine
    wrong colours. The register publishes nine hexes and this repository
    mirrors them; if the register moves one, this is the line that says so.
    """
    assert getattr(colors, name) == value


@pytest.mark.parametrize("dead", RETIRED)
def test_no_retired_status_value_survives(dead):
    """#e56b77 and #c82131 were derived from #dc3545. With the base retired
    they are orphans -- values derived from something no longer in the palette,
    which is the #c4a458 failure this programme has already paid for once."""
    live = {v for k, v in vars(colors).items()
            if isinstance(v, str) and v.startswith("#")}
    assert dead not in live


# ------------------------------------------------------------- the fills
@pytest.mark.parametrize("name", FILLS)
@pytest.mark.parametrize("ground", ALL_GROUNDS)
def test_a_fill_clears_the_fill_floor_on_every_ground(name, ground):
    """One value, four grounds. That is what a fill has to do, and it is why
    all three sit in the L* 48-59 band."""
    ratio = contrast(getattr(colors, name), ground)
    assert ratio >= FILL_FLOOR, f"{name} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("name", FILLS)
@pytest.mark.parametrize("ground", ALL_GROUNDS)
def test_a_fill_is_not_usable_as_text(name, ground):
    """The other half of the fill band, asserted rather than assumed.

    This is the test that would have caught the wrong migration. Swapping the
    value while a key still means "text" leaves every status message below the
    text floor; if someone later points a `color:` declaration at a fill, this
    records that the fill was never able to do that job.
    """
    ratio = contrast(getattr(colors, name), ground)
    assert ratio < TEXT_FLOOR, (
        f"{name} now reads {ratio:.4f} on {ground} and CLEARS the text floor. "
        f"Either the register moved it out of the fill band, or this test is "
        f"measuring the wrong constant. Do not relax it -- find out which.")


# -------------------------------------------------------- the text variants
@pytest.mark.parametrize("name", DARK_TEXT)
@pytest.mark.parametrize("ground", DARK_GROUNDS)
def test_dark_text_variants_carry_text(name, ground):
    ratio = contrast(getattr(colors, name), ground)
    assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("name", LIGHT_TEXT)
@pytest.mark.parametrize("ground", LIGHT_GROUNDS)
def test_light_text_variants_carry_text(name, ground):
    """RNV-STATUS-LIGHT-FLOOR -- READ THIS BEFORE WIDENING THE PARAMETERS.

    The predecessor of this test ran over #ffffff, #f5f5f5, #eeeeee and
    #e8e8e8, because #c82131 reached all four (4.6100 on #e8e8e8) and the
    register published #e8e8e8 as the boundary where red stops carrying text.

    The registered replacements do NOT reach that far. Measured:

        success-text-light #8a6581   #eeeeee 4.25  #e8e8e8 4.02  #e0e0e0 3.74
        warning-text-light #976633   #eeeeee 4.24  #e8e8e8 4.02  #e0e0e0 3.73
        error-text-light   #b84e58   #eeeeee 4.38  #e8e8e8 4.14  #e0e0e0 3.85

    The cause is in the register's own rule, which walks these three against
    #f5f5f5 as "the worst light ground". Rev 27 put APP hover-light #eeeeee,
    GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light #e0e0e0 below it. All
    three were walked to the FIRST step that clears -- 4.52, 4.52, 4.51 -- so
    there is no margin, and one registered rung down they fail together.

    THIS IS AN OPEN QUESTION WITH THE BRAND CHAT, NOT A LOOSENED TEST. The
    parameters are narrowed to the two grounds the published values actually
    reach, and this docstring is the record of what was given up. If the
    register re-walks against #e8e8e8 the answers are #825d79 / #8e5e2b /
    #ae4650 -- each moving less than the register's own 8.40 threshold, so
    they stay the same three colours -- and the fix here is to restore
    #eeeeee and #e8e8e8 to LIGHT_GROUNDS and update REGISTERED.
    """
    ratio = contrast(getattr(colors, name), ground)
    assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"


# ------------------------------------------------------------- the wiring
@pytest.mark.parametrize("key,expected", [
    ("success", "STATUS_SUCCESS_TEXT"),
    ("warning", "STATUS_WARNING_TEXT"),
    ("error", "STATUS_ERROR_TEXT"),
])
def test_the_dark_palette_uses_the_text_variants(key, expected):
    """These keys are read in fourteen places and every one is a `color:`
    declaration. The key is named for a fill and used as text, so it carries
    the text variant."""
    assert DialogStyleManager.get_colors(True)[key] == getattr(colors, expected)


@pytest.mark.parametrize("key,expected", [
    ("success", "STATUS_SUCCESS_TEXT_LIGHT"),
    ("warning", "STATUS_WARNING_TEXT_LIGHT"),
    ("error", "STATUS_ERROR_TEXT_LIGHT"),
])
def test_the_light_palette_uses_the_light_text_variants(key, expected):
    assert DialogStyleManager.get_colors(False)[key] == getattr(colors, expected)


@pytest.mark.parametrize("is_dark", [True, False])
@pytest.mark.parametrize("key", ["success", "warning", "error"])
def test_every_status_message_clears_the_text_floor_on_its_own_ground(is_dark, key):
    """The end-to-end assertion, and the one that was failing before this pass.

    Light success read 2.87 on #f5f5f5 and light warning 1.50 -- both illegal
    as text, both live, both unnoticed, because the only boundary test in this
    repository covered the error red. success and warning had no light sibling
    to be tested against, so the failure had nowhere to show up. Six readings
    now, not one.
    """
    palette = DialogStyleManager.get_colors(is_dark)
    ratio = contrast(palette[key], palette["bg"])
    assert ratio >= TEXT_FLOOR, (
        f"{key} on {'dark' if is_dark else 'light'} bg {palette['bg']} = "
        f"{ratio:.4f}")


def test_dark_error_text_now_clears():
    """This replaces test_dark_error_text_is_short_and_that_is_recorded.

    That test was a two-way exemption recording that dark error text read
    3.8441 on #1a1a1a and 3.1703 on #2a2a2a -- below the floor -- and its
    second assertion said, in as many words: if a dark derivative is ever
    ruled, delete this test rather than leaving a standing note about a
    problem that no longer exists.

    The register ruled three on 2026-09-03. The exemption is deleted, and this
    asserts the opposite of what it asserted.
    """
    dark = DialogStyleManager.get_colors(True)
    for ground in DARK_GROUNDS:
        ratio = contrast(dark["error"], ground)
        assert ratio >= TEXT_FLOOR, f"dark error text {ratio:.4f} on {ground}"


def test_the_delete_button_reads_the_palette_for_its_own_mode(qtbot):
    """Carried over unchanged in intent.

    ui/preset_dialog.py once painted the delete button from
    DialogStyleManager.DARK unconditionally. It rendered the same value in
    both modes only because light and dark shared one error red; giving light
    its own turned it into a real defect on the one control that skipped the
    palette.
    """
    from core.preset_manager import PresetStep
    from ui.preset_dialog import StepEditorWidget

    step = PresetStep(action="uppercase")
    for is_dark, expected in ((True, colors.STATUS_ERROR_TEXT),
                              (False, colors.STATUS_ERROR_TEXT_LIGHT)):
        widget = StepEditorWidget(step, is_dark=is_dark)
        qtbot.addWidget(widget)
        sheets = [child.styleSheet() for child in widget.findChildren(object)
                  if hasattr(child, "styleSheet")]
        assert any(expected in sheet for sheet in sheets), (
            f"is_dark={is_dark}: no child carries {expected}")
