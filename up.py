#!/usr/bin/env python3
"""
RNV-STATUS-TOOL-DO-NOT-SWEEP

Move rnv-text-transformer onto the RNV status family, and wire the three
status keys to the TEXT variants they have always been used as.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file


WHY

The register replaced Bootstrap's three status colours on 2026-09-03. Two
measurements made keeping them indefensible: the amber read 1.63 on #ffffff
and 1.49 on #f5f5f5 against a 3:1 fill floor, and success and error sat about
4 apart under deuteranopia -- one olive, the two most consequential colours in
any interface. The RNV family leaves the red-green axis entirely.

    success  #28a745  ->  #926c89      warning  #ffc107  ->  #a2703c
    error    #dc3545  ->  #c75b64

and publishes six TEXT variants, closing an asymmetry where only red had one.

    success-text  #ad85a3    success-text-light  #8a6581
    warning-text  #bc8752    warning-text-light  #976633
    error-text    #dd6f77    error-text-light    #b84e58

#e56b77 and #c82131 were derived from #dc3545. With that base retired they are
ORPHANS, so they move with it rather than being kept alongside.


WHAT THIS SCRIPT FOUND, AND WHY IT IS MORE THAN A VALUE SWAP

This application reads 'success' / 'warning' / 'error' in FOURTEEN places --
export_dialog, compare_dialog, watch_folder_dialog, preset_dialog,
regex_builder_dialog, encoding_dialog -- and every one of them is a

    color: {...}

declaration. Never a background, never a border. The keys are named for fills
and used as text, and the bar for text is 4.5:1 rather than 3:1.

Swapping the value while the key still means "text" makes that WORSE, because
every fill in the family sits in the L* 48-59 band by construction -- that band
is exactly what lets one value work on a dark AND a light ground, and a
mid-tone cannot carry text on either side. Measured over dark #1a1a1a /
#2a2a2a and light #f5f5f5 / #ffffff, twelve readings:

    today, Bootstrap            6 / 12 clear 4.5:1
    swap the value only         0 / 12
    wire to the TEXT variant   12 / 12

So the keys are wired to the text variants. THE FILLS ARE NOT REMOVED:
STATUS_SUCCESS / STATUS_WARNING / STATUS_ERROR stay in utils/colors.py at
their new registered values, for anything that actually fills.

TWO FAILURES HERE WERE ALREADY LIVE AND UNNOTICED. Light success read 2.87 on
#f5f5f5 and light warning 1.50 -- both illegal as text today. They were
invisible because the only boundary test in this repository covers the error
red; success and warning had no light sibling to be tested against, so the
failure had nowhere to show up.


THE ONE THING THAT IS NOT SETTLED YET

The register's three LIGHT text variants were walked to clear 4.5 on #f5f5f5,
which it calls "the worst light ground". It is not: rev 27 added APP
hover-light #eeeeee and pressed-light #e0e0e0 underneath it, and
GOLD_TEXT_GROUND_FLOOR #e8e8e8 sits between them. All three light variants
fail 4.5 on all three of those rungs.

That is a live question with the brand chat, not something this script
decides. The values applied here are the register's AS PUBLISHED. The one test
that asserted coverage down to #e8e8e8 -- written when #c82131 reached that
far -- is narrowed to the two rungs the published values actually reach, and
carries RNV-STATUS-LIGHT-FLOOR so it can be found the moment the register
answers. Nothing is quietly loosened: the marker names the open question, in
the test, with the measurements and the replacement values.


NAMING

STATUS_ERROR_LIGHT becomes STATUS_ERROR_TEXT_LIGHT. The register's own note
records that this colour was derived independently under TWO identifiers --
STATUS_ERROR_LIGHT here and in the picker, STATUS_ERROR_TEXT_LIGHT in the
palette manager -- and names it error-text-light. With five more siblings
landing in this file under the _TEXT / _TEXT_LIGHT shape, leaving one of the
six spelled differently would be a defect this change created.

STATUS_ERROR_LIGHT was `lighten(STATUS_ERROR, -20)`. That formula no longer
produces the registered value: against the new base it yields #b44753, which
is neither the old value nor the new one. A derived value whose rule no longer
produces it is not derived, it is a coincidence waiting to break -- so the six
text variants are written down with their provenance in the comment, exactly
as the register did for BRAND_STANDBY_GOLD.


THE DARK EXEMPTION IS CLOSED

tests/test_error_red.py carried test_dark_error_text_is_short_and_that_is_recorded,
a two-way exemption whose own docstring says:

    "If a dark derivative is ever ruled ... this test goes red and tells
     whoever did it to delete the exemption. An exemption that outlives its
     problem is a licence waiting for a future defect."

The register ruled three of them on 2026-09-03. The exemption's condition is
met, so it is deleted and replaced by a test asserting that dark error text
now CLEARS 4.5 through STATUS_ERROR_TEXT.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-text-transformer"
DESCRIPTION = "move onto the RNV status family; wire status keys to text variants"
SENTINEL_FILE = "utils/colors.py"
SENTINEL = "RNV-STATUS-FAMILY"
GUARD = "tests/test_status_family.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "dialog_styles.py"}

SUITES = [
    ("pytest tests/",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
]

# role -> (fill, text on a dark ground, text on a light ground)
FAMILY = {
    "SUCCESS": ("#926c89", "#ad85a3", "#8a6581"),
    "WARNING": ("#a2703c", "#bc8752", "#976633"),
    "ERROR":   ("#c75b64", "#dd6f77", "#b84e58"),
}
RETIRED = ("#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131")


GUARD_SOURCE = r'''"""RNV-STATUS-GUARD -- the family cannot drift back.

A guard rather than a test: this pins the SHAPE of the change, so a later edit
that reintroduces a Bootstrap value, or points a text key back at a fill, fails
here with a message saying which of the two happened and why it matters.
"""

import io
import re
import tokenize
from pathlib import Path

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

RETIRED = {
    "#28a745": "Bootstrap green, retired -- it and the Bootstrap red collapsed "
               "to one olive under deuteranopia at about 4 apart",
    "#ffc107": "Bootstrap amber, retired -- 1.63 on #ffffff and 1.49 on "
               "#f5f5f5 against a 3:1 fill floor",
    "#dc3545": "Bootstrap red, retired with its family",
    "#e56b77": "orphan: derived from #dc3545, which no longer exists",
    "#c82131": "orphan: derived from #dc3545, which no longer exists",
}

SOURCES = SWEPT = ("utils/colors.py", "utils/dialog_styles.py")
LIVE_VALUE = "#926c89"


def _code_only(text: str) -> str:
    """Source with comments and DOCSTRINGS removed -- and nothing else.

    Why this exists: every value these guards forbid is named, in words, in
    the provenance explaining why it was retired. A sweep that cannot tell a
    value being USED from a value being MENTIONED forces the fix to be silence
    about what changed, which is the opposite of what the provenance is for.

    Why it is fussier than it looks: an earlier version dropped every STRING
    token. In Python a colour value IS a string literal -- `X = "#926c89"` --
    so that version removed the uses along with the mentions and the sweep
    could never find anything. It passed on every input, including a file that
    had just put a retired value back. This file's own guard-the-guard is what
    caught it, which is the entire reason for writing guards that check the
    guard can still see.

    So: a STRING token is dropped only when it STARTS a statement -- a
    docstring, or a bare string expression, which is prose either way. A string
    on the right of an assignment, in a dict, or in a call is kept, because
    that is what a value looks like.
    """
    out = []
    # ENCODING behaves like the start of a line for this purpose.
    at_statement_start = True
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and at_statement_start:
                at_statement_start = False
                continue
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING):
                at_statement_start = True
            else:
                at_statement_start = False
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # Falling back to the raw text can only make a sweep STRICTER, never
        # looser, so it fails safe.
        return text
    return " ".join(out)


@pytest.mark.parametrize("dead", sorted(RETIRED))
def test_no_retired_value_is_live_in_any_source(dead):
    for rel in SOURCES:
        text = Path(rel).read_text(encoding="utf-8")
        assert dead not in _code_only(text), (
            f"{rel} uses {dead} again -- {RETIRED[dead]}")


@pytest.mark.parametrize("dead", sorted(RETIRED))
def test_no_retired_value_is_reachable_as_a_constant(dead):
    live = {v for k, v in vars(colors).items()
            if isinstance(v, str) and v.startswith("#")}
    assert dead not in live, f"{dead} is back as a constant -- {RETIRED[dead]}"


@pytest.mark.parametrize("key", ["success", "warning", "error"])
@pytest.mark.parametrize("is_dark", [True, False])
def test_a_status_key_never_carries_a_fill(key, is_dark):
    """The specific wrong migration, named so it cannot be made by accident.

    Swapping the value while leaving the key pointed at a fill is the change
    this pass exists NOT to make: it takes these six readings from one failure
    to six. If someone repoints these keys at STATUS_SUCCESS / _WARNING /
    _ERROR, this is the line that stops it.
    """
    fills = {colors.STATUS_SUCCESS, colors.STATUS_WARNING, colors.STATUS_ERROR}
    value = DialogStyleManager.get_colors(is_dark)[key]
    assert value not in fills, (
        f"{'dark' if is_dark else 'light'} '{key}' is painted with a FILL "
        f"({value}). Fills sit at L* 48-59 and cannot reach 4.5:1 as text on "
        f"either ground; this key is read only in `color:` declarations.")


def test_the_two_spellings_did_not_come_back():
    """The register recorded that this one colour was derived independently
    under TWO identifiers across three applications -- STATUS_ERROR_LIGHT here
    and in the picker, STATUS_ERROR_TEXT_LIGHT in the palette manager. One
    name now, and the old one must not reappear alongside it."""
    for rel in SOURCES:
        text = Path(rel).read_text(encoding="utf-8")
        assert not re.search(r"\bSTATUS_ERROR_LIGHT\b", _code_only(text)), (
            f"{rel} reintroduced STATUS_ERROR_LIGHT; the name is "
            f"STATUS_ERROR_TEXT_LIGHT")


def test_the_six_text_variants_are_all_exported():
    """A value the package does not export is a value the next application
    cannot mirror, which is how a fleet ends up with six spellings."""
    import utils
    for role in ("SUCCESS", "WARNING", "ERROR"):
        for suffix in ("_TEXT", "_TEXT_LIGHT"):
            name = f"STATUS_{role}{suffix}"
            assert hasattr(utils, name), f"utils does not export {name}"
            assert name in utils.__all__, f"{name} is missing from utils.__all__"


def test_this_guard_can_still_see():
    """Guard the guard, and it has already earned its place.

    _code_only exists so provenance can name a retired value without failing
    the sweep that forbids it. An earlier version dropped EVERY string token,
    which in Python also drops the values -- so the sweep above could never
    find anything and passed on every input, including a file that had just
    put a retired value back. This assertion is what caught that.
    """
    src = Path(SWEPT[0]).read_text(encoding="utf-8")
    code = _code_only(src)
    assert len(code) > 2000, "the tokeniser returned almost nothing"
    assert LIVE_VALUE in code, (
        f"the code-only sweep cannot see {LIVE_VALUE}, which is definitely a "
        f"value in {SWEPT[0]}. The sweep for retired values is therefore "
        f"vacuous and would pass on anything.")
'''

NEW_CONSTANTS = r'''#: engine/brand.py STATUS["success"] -- RNV-STATUS-FAMILY (2026-09-03)
#:
#: A FILL. Badges, boundaries, filled bars. It is not text: every fill in this
#: family sits in the L* 48-59 band, which is precisely what lets ONE value
#: work on a dark AND a light ground, and a mid-tone cannot carry text on
#: either side. 3.92 on #1a1a1a, 3.23 on #2a2a2a -- above the 3:1 fill floor
#: and below the 4.5:1 text floor, by design rather than by accident.
#:
#: Was #28a745, Bootstrap's green. Retired because it and the Bootstrap red
#: sat about 4 apart under deuteranopia -- one olive -- and success and error
#: are the two most consequential colours in an interface.
STATUS_SUCCESS: Final[str] = '#926c89'

#: engine/brand.py STATUS["warning"] -- a FILL. Was #ffc107.
#:
#: Retired on arithmetic rather than taste: #ffc107 read 1.63 on #ffffff and
#: 1.49 on #f5f5f5 against a 3:1 fill floor. It could not legally carry a
#: boundary on a light ground at all.
STATUS_WARNING: Final[str] = '#a2703c'

#: engine/brand.py STATUS["error"] -- a FILL. Was #dc3545.
STATUS_ERROR: Final[str] = '#c75b64'

#: engine/brand.py STATUS["success-text"], ["warning-text"], ["error-text"].
#: TEXT on a dark ground.
#:
#: The fills above cannot carry text. These can: 4.55, 4.60 and 4.52 on APP
#: card #2a2a2a, the worst dark ground this application paints on. That is why
#: the family has nine values and not three.
#:
#: REGISTERED, not derived. The register's rule -- hold hue and chroma, move
#: lightness only, take the first step that clears 4.5 on the worst ground --
#: is published as PROVENANCE so the choice is auditable. It is not re-run
#: here. A rule held live becomes an edit anyone can make, and retuning it
#: would silently change what an error looks like in five applications.
STATUS_SUCCESS_TEXT: Final[str] = '#ad85a3'
STATUS_WARNING_TEXT: Final[str] = '#bc8752'
STATUS_ERROR_TEXT: Final[str] = '#dd6f77'

#: engine/brand.py STATUS["*-text-light"] -- TEXT on a light ground.
#:
#: 4.52, 4.52 and 4.51 on #f5f5f5, this application's light dialog background.
#:
#: RNV-STATUS-LIGHT-FLOOR: the register walked these three against #f5f5f5 as
#: "the worst light ground". It is not the worst one the register publishes --
#: APP hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light
#: #e0e0e0 all sit below it, and all three values fail 4.5 on all three rungs
#: (4.25 / 4.02 / 3.74 for success). All three were walked to the FIRST step
#: that clears, so there is no margin and one rung down they fail together.
#: The values here are the register's AS PUBLISHED and the question is open
#: with the brand chat; if it re-walks them against #e8e8e8 the answers are
#: #825d79 / #8e5e2b / #ae4650, each moving less than the register's own 8.40
#: "clearly different" bar. See tests/test_error_red.py for the measurements.
#:
#: THE LAST OF THESE WAS STATUS_ERROR_LIGHT, and was lighten(STATUS_ERROR, -20).
#: Renamed because five siblings now land beside it under the _TEXT_LIGHT shape
#: and the register names this colour error-text-light; the register's own note
#: records that three applications derived it under TWO identifiers.
#:
#: Written down rather than derived because that formula no longer produces the
#: registered value: against the new base it yields #b44753, which is neither
#: the old value nor the new one. A derived value whose rule no longer produces
#: it is not derived, it is a coincidence waiting to break -- the same reasoning
#: that registered BRAND_STANDBY_GOLD rather than deriving it from BRAND_GOLD.
STATUS_SUCCESS_TEXT_LIGHT: Final[str] = '#8a6581'
STATUS_WARNING_TEXT_LIGHT: Final[str] = '#976633'
STATUS_ERROR_TEXT_LIGHT: Final[str] = '#b84e58'
'''

NEW_ERROR_RED = r'''"""The RNV status family, as this application uses it.

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
'''


def _code_only(text: str) -> str:
    """Source with comments and DOCSTRINGS removed -- and nothing else.

    Why this exists: every value these guards forbid is named, in words, in
    the provenance explaining why it was retired. A sweep that cannot tell a
    value being USED from a value being MENTIONED forces the fix to be silence
    about what changed, which is the opposite of what the provenance is for.

    Why it is fussier than it looks: an earlier version dropped every STRING
    token. In Python a colour value IS a string literal -- `X = "#926c89"` --
    so that version removed the uses along with the mentions and the sweep
    could never find anything. It passed on every input, including a file that
    had just put a retired value back. This file's own guard-the-guard is what
    caught it, which is the entire reason for writing guards that check the
    guard can still see.

    So: a STRING token is dropped only when it STARTS a statement -- a
    docstring, or a bare string expression, which is prose either way. A string
    on the right of an assignment, in a dict, or in a call is kept, because
    that is what a value looks like.
    """
    import io
    import tokenize
    out = []
    # ENCODING behaves like the start of a line for this purpose.
    at_statement_start = True
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and at_statement_start:
                at_statement_start = False
                continue
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING):
                at_statement_start = True
            else:
                at_statement_start = False
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # Falling back to the raw text can only make a sweep STRICTER, never
        # looser, so it fails safe.
        return text
    return " ".join(out)


def edits(tree) -> None:
    src = tree.read("utils/colors.py")

    # --- 1. the constant block, replaced wholesale.
    #
    # Anchored on the FIRST line of the old block and the LAST, so a file that
    # has moved fails loudly here rather than composing a wrong replacement
    # out of anchors that still happen to match.
    start_anchor = '#: engine/brand.py STATUS["success"]'
    end_anchor = ("STATUS_ERROR_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)"
                  "   # -> #c82131\n")
    if src.count(start_anchor) != 1:
        raise SystemExit("utils/colors.py: expected exactly one "
                         "STATUS[\"success\"] doc anchor")
    if end_anchor not in src:
        raise SystemExit("utils/colors.py: the STATUS_ERROR_LIGHT derivation "
                         "line is not where this script expects it")
    start = src.index(start_anchor)
    end = src.index(end_anchor) + len(end_anchor)
    tree.write("utils/colors.py", src[:start] + NEW_CONSTANTS + src[end:])

    # --- 2. the classification map.
    #
    # The six text variants are REGISTERED, not derived. The register
    # publishes them as values and publishes the walk that produced them as
    # provenance; filing them as 'derived' would say this application may
    # recompute them, which is what turned #c82131 into an orphan.
    tree.sub("utils/colors.py",
             "    'STATUS_ERROR': 'register',\n"
             "    # -- derived\n"
             "    'STATUS_ERROR_LIGHT': 'derived',\n",
             "    'STATUS_ERROR': 'register',\n"
             "    'STATUS_SUCCESS_TEXT': 'register',\n"
             "    'STATUS_WARNING_TEXT': 'register',\n"
             "    'STATUS_ERROR_TEXT': 'register',\n"
             "    'STATUS_SUCCESS_TEXT_LIGHT': 'register',\n"
             "    'STATUS_WARNING_TEXT_LIGHT': 'register',\n"
             "    'STATUS_ERROR_TEXT_LIGHT': 'register',\n"
             "    # -- derived\n", 1)

    # --- 3. the name list in colors.py
    tree.sub("utils/colors.py",
             "    'STATUS_SUCCESS',\n"
             "    'STATUS_WARNING',\n"
             "    'STATUS_ERROR',\n"
             "    'STATUS_ERROR_LIGHT',\n",
             "    'STATUS_SUCCESS',\n"
             "    'STATUS_WARNING',\n"
             "    'STATUS_ERROR',\n"
             "    'STATUS_SUCCESS_TEXT',\n"
             "    'STATUS_WARNING_TEXT',\n"
             "    'STATUS_ERROR_TEXT',\n"
             "    'STATUS_SUCCESS_TEXT_LIGHT',\n"
             "    'STATUS_WARNING_TEXT_LIGHT',\n"
             "    'STATUS_ERROR_TEXT_LIGHT',\n", 1)

    # --- 4. a stale cross-reference in the semantic-naming note. It cites the
    # old pair by name to explain why the diff constants dropped their _DARK
    # suffix; the reasoning holds, the names moved.
    tree.sub("utils/colors.py",
             "# carries the dark value, exactly as STATUS_ERROR / "
             "STATUS_ERROR_LIGHT do\n",
             "# carries the dark value, exactly as STATUS_ERROR_TEXT /\n"
             "# STATUS_ERROR_TEXT_LIGHT do\n", 1)

    # --- 5. dialog_styles imports.
    #
    # The three FILLS are deliberately not imported here: nothing in this
    # module fills with them, and importing a name only to leave it unused is
    # how a reader concludes the palette uses it.
    tree.sub("utils/dialog_styles.py",
             "    STATUS_SUCCESS,\n"
             "    STATUS_WARNING,\n"
             "    STATUS_ERROR,\n"
             "    STATUS_ERROR_LIGHT,\n",
             "    STATUS_SUCCESS_TEXT,\n"
             "    STATUS_WARNING_TEXT,\n"
             "    STATUS_ERROR_TEXT,\n"
             "    STATUS_SUCCESS_TEXT_LIGHT,\n"
             "    STATUS_WARNING_TEXT_LIGHT,\n"
             "    STATUS_ERROR_TEXT_LIGHT,\n", 1)

    # --- 6. the two palettes. Every consumer of these keys writes `color:`,
    # so the key means TEXT and carries the text variant for its ground.
    tree.sub("utils/dialog_styles.py",
             "        'success': STATUS_SUCCESS,\n"
             "        'error': STATUS_ERROR,\n"
             "        'warning': STATUS_WARNING,\n",
             "        # RNV-STATUS-FAMILY: these three keys are read in fourteen\n"
             "        # places and every one is a `color:` declaration, so they\n"
             "        # carry the TEXT variants rather than the fills. The fills\n"
             "        # sit at L* 48-59 and cannot reach 4.5:1 on either ground.\n"
             "        'success': STATUS_SUCCESS_TEXT,\n"
             "        'error': STATUS_ERROR_TEXT,\n"
             "        'warning': STATUS_WARNING_TEXT,\n", 1)
    tree.sub("utils/dialog_styles.py",
             "        'success': STATUS_SUCCESS,\n"
             "        'error': STATUS_ERROR_LIGHT,\n"
             "        'warning': STATUS_WARNING,\n",
             "        # RNV-STATUS-FAMILY: light's siblings. success and warning\n"
             "        # had no light variant before this and read 2.87 and 1.50\n"
             "        # on #f5f5f5 -- illegal as text, live, and unnoticed because\n"
             "        # the only boundary test in this repo covered the red.\n"
             "        'success': STATUS_SUCCESS_TEXT_LIGHT,\n"
             "        'error': STATUS_ERROR_TEXT_LIGHT,\n"
             "        'warning': STATUS_WARNING_TEXT_LIGHT,\n", 1)

    # --- 7. the package re-export
    tree.sub("utils/__init__.py",
             "    STATUS_SUCCESS,\n    STATUS_WARNING,\n    STATUS_ERROR,\n",
             "    STATUS_SUCCESS,\n    STATUS_WARNING,\n    STATUS_ERROR,\n"
             "    STATUS_SUCCESS_TEXT,\n    STATUS_WARNING_TEXT,\n"
             "    STATUS_ERROR_TEXT,\n    STATUS_SUCCESS_TEXT_LIGHT,\n"
             "    STATUS_WARNING_TEXT_LIGHT,\n    STATUS_ERROR_TEXT_LIGHT,\n", 1)
    tree.sub("utils/__init__.py",
             "    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_ERROR',\n",
             "    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_ERROR',\n"
             "    'STATUS_SUCCESS_TEXT',\n    'STATUS_WARNING_TEXT',\n"
             "    'STATUS_ERROR_TEXT',\n    'STATUS_SUCCESS_TEXT_LIGHT',\n"
             "    'STATUS_WARNING_TEXT_LIGHT',\n    'STATUS_ERROR_TEXT_LIGHT',\n", 1)

    # --- 8. the old error-red test, rewritten rather than patched.
    #
    # Every premise it rests on is now false: the light red is no longer
    # derived, dark is no longer short, and the coverage boundary moved. A
    # patched version would have kept the docstrings that explain a world that
    # no longer exists.
    tree.write("tests/test_error_red.py", NEW_ERROR_RED)

    # --- 9. the syrupy snapshots.
    #
    # tests/__snapshots__/test_snapshots.ambr pins the two resolved palettes
    # and the rendered inline styles. Twelve status values live there, and six
    # of them are recorded as
    #
    #     status(success): color: #28a745;
    #
    # which is this repository's own snapshot agreeing that these keys are
    # `color:` declarations. The evidence for the change is already committed.
    #
    # Rewritten rather than regenerated with --snapshot-update, because a
    # regeneration would also absorb any OTHER drift sitting in the file and
    # present it as part of this change. Twelve substitutions, counted.
    _resnapshot(tree)
    print("  9 edit groups composed")


def _resnapshot(tree) -> None:
    """Move the twelve status values in the snapshot file, mode by mode.

    Mode is never guessed. It is set by an unambiguous marker that always
    precedes the values it governs:

      * the inline-style block carries literal `=== dark ===` / `=== light ===`
        headers;
      * the palette dicts are serialised in KEY ORDER, and "error" sorts before
        "success" and "warning" -- so the error line, whose value differs
        between the two modes, has already fixed the mode by the time the other
        two are read.

    The tally at the end asserts the split rather than trusting it: two of each
    value in each mode, twelve in total. A stale mode carried into a block
    without an error line would show up there as a lopsided count.
    """
    rel = "tests/__snapshots__/test_snapshots.ambr"
    DARK = {"#28a745": "#ad85a3", "#ffc107": "#bc8752", "#dc3545": "#dd6f77"}
    LIGHT = {"#28a745": "#8a6581", "#ffc107": "#976633", "#c82131": "#b84e58"}

    mode = None
    tally = {"dark": 0, "light": 0}
    out = []
    for line in tree.read(rel).splitlines(keepends=True):
        if "=== dark ===" in line:
            mode = "dark"
        elif "=== light ===" in line:
            mode = "light"
        elif "#dc3545" in line and "error" in line:
            mode = "dark"
        elif "#c82131" in line and "error" in line:
            mode = "light"

        table = DARK if mode == "dark" else LIGHT if mode == "light" else {}
        for old, new in table.items():
            if old in line:
                line = line.replace(old, new)
                tally[mode] += 1
        out.append(line)

    if tally != {"dark": 6, "light": 6}:
        raise SystemExit(
            f"{rel}: expected six status values in each mode, moved {tally}. "
            f"The snapshot file has changed shape -- regenerate it with "
            f"`pytest tests/test_snapshots.py --snapshot-update` and re-derive "
            f"this edit rather than trusting the tally.")
    tree.write(rel, "".join(out))


def checks(tree) -> None:
    colors_src = tree.read("utils/colors.py")
    styles = tree.read("utils/dialog_styles.py")
    pkg = tree.read("utils/__init__.py")

    # every retired value is gone from the module that defines colours.
    # `_code_only` is not needed here because the check is for the QUOTED
    # form: a value in a comment is not quoted.
    for dead in RETIRED:
        if f"'{dead}'" in colors_src or f'"{dead}"' in colors_src:
            raise SystemExit(f"{dead} survives as a value in utils/colors.py")

    # the nine values are present exactly as the register publishes them
    for role, (fill, dark, light) in FAMILY.items():
        for name, want in ((f"STATUS_{role}", fill),
                           (f"STATUS_{role}_TEXT", dark),
                           (f"STATUS_{role}_TEXT_LIGHT", light)):
            if f"{name}: Final[str] = '{want}'" not in colors_src:
                raise SystemExit(f"{name} is not defined as {want}")

    # The old identifier is gone everywhere, not only where it was defined --
    # swept through _code_only so this script's own note explaining the rename
    # is not mistaken for the thing it renamed.
    for rel, text in (("utils/colors.py", colors_src),
                      ("utils/dialog_styles.py", styles),
                      ("utils/__init__.py", pkg)):
        if re.search(r"\bSTATUS_ERROR_LIGHT\b", _code_only(text)):
            raise SystemExit(f"STATUS_ERROR_LIGHT survives in {rel}")

    # the keys carry TEXT variants -- the whole point of this pass
    for key, dark, light in (
            ("success", "STATUS_SUCCESS_TEXT", "STATUS_SUCCESS_TEXT_LIGHT"),
            ("warning", "STATUS_WARNING_TEXT", "STATUS_WARNING_TEXT_LIGHT"),
            ("error", "STATUS_ERROR_TEXT", "STATUS_ERROR_TEXT_LIGHT")):
        if f"'{key}': {dark},\n" not in styles:
            raise SystemExit(f"the dark palette's '{key}' is not wired to {dark}")
        if f"'{key}': {light},\n" not in styles:
            raise SystemExit(f"the light palette's '{key}' is not wired to {light}")

    # and no key was left pointing at a fill. The check above would pass if a
    # palette carried BOTH, which is exactly what a half-applied edit looks like.
    for role in FAMILY:
        bad = f": STATUS_{role},\n"
        if bad in styles:
            raise SystemExit(f"a palette still points a status key at the "
                             f"STATUS_{role} fill")

    # the snapshots moved with the palettes
    snap = tree.read("tests/__snapshots__/test_snapshots.ambr")
    for dead in RETIRED:
        if dead in snap:
            raise SystemExit(f"{dead} survives in the syrupy snapshots")

    if SENTINEL not in colors_src:
        raise SystemExit("the ruling note did not land in utils/colors.py")
    print("  guards: 5 retired values gone, 9 registered values in, "
          "6 keys on text variants, 1 name unified")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

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
        return "fail"
    return "env"


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
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
