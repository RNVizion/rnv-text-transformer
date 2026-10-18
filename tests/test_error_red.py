"""The RNV status family, as this application uses it.

    STATUS_*_TEXT         success, warning, error    text on a dark ground
    STATUS_*_TEXT_LIGHT   success, warning, error    text on a light ground

RNV-NAMED-AND-USED, 2026-10-04: the family's three fills stood here too, with
two tests on their arithmetic. This application draws status as text and no
fill; nothing read the three, so it carries none, and those tests went with
them. The register holds the fills.

This file replaces the error-red tests, which covered a two-value red that no
longer exists. Three of their premises are now false, and each is worth saying
out loud, because a test file quietly rewritten hides what changed:

  * "the light error red is DERIVED, not written down" -- it is written down
    now. lighten(STATUS_ERROR, -20) against the new base yields
    EXAMPLE_ERROR_TEXT_LIGHT_REDERIVED, not the registered
    STATUS_ERROR_TEXT_LIGHT. The register publishes the derivation as
    provenance and the value as a value.

  * "dark error text is SHORT and that is recorded" -- that exemption's own
    docstring said to delete it if a dark derivative was ever ruled. Three
    were ruled on 2026-09-03. test_dark_error_text_now_clears replaces it, and
    asserts the opposite of what it asserted.

  * "red carries text down to GOLD_TEXT_GROUND_FLOOR" -- see
    RNV-STATUS-LIGHT-FLOOR below.
"""

import json
import pathlib

import pytest

from tests import colour_values as cv
from utils import colors
from utils.dialog_styles import DialogStyleManager

#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json
#: says. The values are held by tests/test_colours_in_sync.py, against the
#: register at the pin; what this file holds is the name each one takes.
BRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json").read_text(encoding="utf-8"))["colours"]

TEXT_FLOOR = 4.5

# RNV-COLOUR-SYNC, 2026-10-16: the grounds by name, where they were their hex
# codes: the dark bg and bg_secondary.
DARK_GROUNDS = (colors.BRAND_BLACK, colors.APP_CARD)
# All four registered rungs, down to GOLD_TEXT_GROUND_FLOOR. Narrowed to
# two while RNV-STATUS-LIGHT-FLOOR was open; restored at rev 31 because
# the re-walked values REACH them, not to make a point.
LIGHT_GROUNDS = (colors.WHITE, colors.APP_SURFACE_LIGHT_3, colors.APP_HOVER_LIGHT,
                 colors.GOLD_TEXT_GROUND_FLOOR)

DARK_TEXT = ("STATUS_SUCCESS_TEXT", "STATUS_WARNING_TEXT", "STATUS_ERROR_TEXT")
LIGHT_TEXT = ("STATUS_SUCCESS_TEXT_LIGHT", "STATUS_WARNING_TEXT_LIGHT",
              "STATUS_ERROR_TEXT_LIGHT")

#: Each value by the register name it is written from. RNV-COLOUR-SYNC,
#: 2026-10-16: the values were written here; they are written from the
#: register now, and held there.
REGISTERED = {
    "STATUS_SUCCESS_TEXT": "STATUS.success-text",
    "STATUS_WARNING_TEXT": "STATUS.warning-text",
    "STATUS_ERROR_TEXT": "STATUS.error-text",
    "STATUS_SUCCESS_TEXT_LIGHT": "STATUS.success-text-light",
    "STATUS_WARNING_TEXT_LIGHT": "STATUS.warning-text-light",
    "STATUS_ERROR_TEXT_LIGHT": "STATUS.error-text-light",
}
RETIRED = (cv.RETIRED_BOOTSTRAP_GREEN, cv.RETIRED_BOOTSTRAP_AMBER, cv.RETIRED_BOOTSTRAP_RED,
           cv.RETIRED_ERROR_TEXT_FROM_BOOTSTRAP, cv.RETIRED_ERROR_TEXT_LIGHT_FROM_BOOTSTRAP)


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
def test_the_six_values_are_the_registered_ones(name, value):
    """Pinned by value, not by relationship.

    A test asserting only that these differ from each other would pass on six
    wrong colours. The register publishes nine hexes and this repository
    mirrors the six it draws; if the register moves one, this is the line
    that says so.

    RNV-COLOUR-SYNC, 2026-10-16: pinned by the register name brand_map.json
    writes it from; tests/test_colours_in_sync.py holds the value, against
    the register at the pin.
    """
    assert BRAND_MAP[name] == value


@pytest.mark.parametrize("dead", RETIRED)
def test_no_retired_status_value_survives(dead):
    """RETIRED_ERROR_TEXT_FROM_BOOTSTRAP and RETIRED_ERROR_TEXT_LIGHT_FROM_BOOTSTRAP
    were derived from RETIRED_BOOTSTRAP_RED. With the base retired
    they are orphans -- values derived from something no longer in the palette,
    which is the RETIRED_OLD_DARK_GOLD_TINT failure this programme has already
    paid for once."""
    live = {v for k, v in vars(colors).items()
            if isinstance(v, str) and v.startswith("#")}
    assert dead not in live


# ------------------------------------------------------------- the fills
# RNV-NAMED-AND-USED, 2026-10-04: two tests stood here on the arithmetic of
# the three fills -- that each clears 3:1 on every ground and 4.5:1 on none.
# This application draws no fill and no longer carries them; the arithmetic
# is the register's, where the fills are.


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

    The predecessor of this test ran over WHITE, APP_SURFACE_LIGHT_3,
    APP_HOVER_LIGHT and GOLD_TEXT_GROUND_FLOOR, because
    RETIRED_ERROR_TEXT_LIGHT_FROM_BOOTSTRAP reached all four (4.6100 on
    GOLD_TEXT_GROUND_FLOOR) and the register published GOLD_TEXT_GROUND_FLOOR
    as the boundary where red stops carrying text.

    The registered replacements do NOT reach that far. Measured, on
    APP_HOVER_LIGHT, GOLD_TEXT_GROUND_FLOOR and REGISTER_APP_PRESSED_LIGHT:

        STATUS_SUCCESS_TEXT_LIGHT    4.77  4.52  4.20
        STATUS_WARNING_TEXT_LIGHT    4.78  4.53  4.20
        STATUS_ERROR_TEXT_LIGHT      4.77  4.52  4.20

    The first three columns now pass. REGISTER_APP_PRESSED_LIGHT still does
    not, and that is the boundary rather than a gap: BRAND_DARK_GOLD_DEEP reads
    4.21 there too, so no brand text of any family is carried below
    GOLD_TEXT_GROUND_FLOOR.

    The cause is in the register's own rule, which walks these three against
    APP_SURFACE_LIGHT_3 as "the worst light ground". Rev 27 put APP hover-light
    (APP_HOVER_LIGHT), GOLD_TEXT_GROUND_FLOOR and pressed-light
    (REGISTER_APP_PRESSED_LIGHT) below it. All
    three were walked to the FIRST step that clears -- 4.52, 4.52, 4.51 -- so
    there is no margin, and one registered rung down they fail together.

    THIS IS AN OPEN QUESTION WITH THE BRAND CHAT, NOT A LOOSENED TEST. The
    parameters are narrowed to the two grounds the published values actually
    reach, and this docstring is the record of what was given up. If the
    register re-walks against GOLD_TEXT_GROUND_FLOOR the answers are
    STATUS_SUCCESS_TEXT_LIGHT / STATUS_WARNING_TEXT_LIGHT /
    STATUS_ERROR_TEXT_LIGHT -- each moving less than the register's own 8.40
    threshold, so they stay the same three colours -- and the fix here is to
    restore APP_HOVER_LIGHT and GOLD_TEXT_GROUND_FLOOR to LIGHT_GROUNDS and
    update REGISTERED.
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

    Light success read 2.87 on APP_SURFACE_LIGHT_3 and light warning 1.50 -- both illegal
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
    3.8441 on BRAND_BLACK and 3.1703 on APP_CARD -- below the floor -- and its
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
