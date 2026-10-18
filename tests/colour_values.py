"""Every colour value the tests need that is not the application's colour.

RNV-COLOUR-SYNC, #53 A (2026-10-17). The application's own colours and the
brand's are named in utils/colors.py, which brand_map.json names, and a test
reads them from there. Every other colour value a test or the root suite
writes is named here, once, with why: samples given to a helper (EXAMPLE_),
values the application no longer uses (RETIRED_), and values the brand
publishes that this application does not draw (REGISTER_). It has no DATA_
and no INVALID_ values. tests/test_colour_values.py holds this file: no
colour value is written anywhere else in tests/ or in
test_rnv_text_transformer.py, not even in a sentence (#57 A), and every name
here says what kind it is, says why, and is used. What a value is, and why
it was retired, is said once, here, beside it; a test's comment or docstring
says the name, and its messages print the value through it.

Tests import it as `from tests import colour_values as cv`, the way
tests/test_tt_register.py already imports tests.test_brand_mirror;
tests/test_colours_in_sync.py loads it by path.

No content marker. This application's value sweeps (tests/test_named_and_used.py,
tests/test_derived_values.py, tests/test_gold_as_text.py,
tests/test_status_family.py) read only its own source and never tests/, so
none of them reads this file. The one sweep that does read tests/,
tests/test_semantic_naming.py, looks for retired NAMES as whole words, and
none is written here: a name such as RETIRED_REGEX_MATCH_LIGHT holds one only
inside a longer word, which that sweep does not match.
"""

# ------------------------------------------------------------------ examples

EXAMPLE_HAND_EDIT = '#123456'
"""The value tests/test_colours_in_sync.py plants over a brand line of the
colour file, to show that the sync puts the line back, and the colour it adds
on a line of its own, to show that the sync refuses one the map does not
hold. Any colour would do. Lower case: it is compared with value.lower()."""

EXAMPLE_HAND_EDIT_FALLBACK = '#654321'
"""The plant tests/test_colours_in_sync.py uses instead if the brand line
already holds EXAMPLE_HAND_EDIT."""

EXAMPLE_MOVED_ACCENT = '#6f94bc'
"""Where tests/test_colours_in_sync.py's simulated brand move sends
APP["accent"]: only somewhere else. It is rnv-brand's BRAND_BLUE from rev 32,
after this application's pin, which does not publish it. Lower case: the
sync writes it into the rewritten line as given, and the test looks for it."""

EXAMPLE_MOVED_ACCENT_FALLBACK = '#456c91'
"""Where the simulated move goes instead if the brand's accent already is
EXAMPLE_MOVED_ACCENT (rnv-brand's BRAND_DARK_BLUE from rev 32)."""

EXAMPLE_WITH_ALPHA_INPUT = '#1a1a1a'
"""The input of tests/test_derived_values.py's byte-order check on
with_alpha(). It is BRAND_BLACK's value today, but a sample: the expected
output beside it is fixed, so it must not follow a brand move."""

EXAMPLE_WITH_ALPHA_OUTPUT = '#bf1a1a1a'
"""What with_alpha() makes of EXAMPLE_WITH_ALPHA_INPUT at 0xBF: eight digits,
alpha first, in lower case (RNV-LOWER-EIGHT)."""

EXAMPLE_ROUND_TRIP = '#d2bc93'
"""The colour tests/test_derived_values.py puts through with_alpha() and takes
back apart with decompose(), which must hand it back unchanged. BRAND_GOLD's
value today, but a sample. Lower case, because decompose() lower-cases."""

EXAMPLE_HASHLESS_INPUT = '444444'
"""A colour given to with_alpha() without its '#', in
tests/test_derived_values.py. #54 A: a hash-less colour string, kept with
the value it must come back as, EXAMPLE_HASHLESS_EXPECTED."""

EXAMPLE_HASHLESS_EXPECTED = '#444444'
"""What decompose(with_alpha(EXAMPLE_HASHLESS_INPUT, ...)) hands back: the
same colour with its '#'. GREY_44's value today, but a sample."""

EXAMPLE_CALIBRATION_GOLD = '#d2bc93'
"""One half of the pair tests/test_diff_floors.py calibrates its CIEDE2000
against: the gold the register walked from, at the figure the register
published, 8.4035. BRAND_GOLD's value today, but the instrument's figure is
fixed, so the pair must not follow a brand move."""

EXAMPLE_CALIBRATION_GOLD_MINUS_30 = '#b49e75'
"""The other half: that gold walked -30, which the register reads as
"perceptible at a glance" at 8.4035, the source of the 8.40 bar. The brand
at this application's pin writes it only in a comment, under no name, so it
is not a REGISTER_ value."""

EXAMPLE_CONTRAST_BLACK = '#000000'
"""The dark end of the contrast scale: tests/test_light_rewalk.py's
guard-the-guard measures 21:1 from it to EXAMPLE_CONTRAST_WHITE. A sample of
the maths, not TRUE_BLACK."""

EXAMPLE_CONTRAST_WHITE = '#ffffff'
"""The light end of the contrast scale: 21:1 from EXAMPLE_CONTRAST_BLACK, and
1:1 against itself. A sample of the maths, not WHITE."""

EXAMPLE_READER_WHITE = '#ffffff'
"""What tests/test_ink_on_the_golds.py's stylesheet reader makes of the CSS
word `white` in its sample sheet. Notation, not the brand's WHITE: the ruled
inks are checked by name elsewhere in that file."""

EXAMPLE_READER_BLACK = '#000000'
"""What the same reader makes of the sample sheet's `#000`: six digits, lower
case. Notation, not TRUE_BLACK."""

EXAMPLE_SWEEP_PROBE_HEX = '#ffcccc'
"""The hex tests/test_named_and_used.py writes into its probe source, and must
then find there: the sweep's guard-the-guard. Its quiet probe writes the same
hex in a bare string, which is prose, and must not be found. Both probes are
built from this name, so they cannot drift."""

EXAMPLE_SWEEP_PROBE_RGBA = 'rgba(255, 255, 255, 230)'
"""The rgba() the same probe writes, and the sweep must report. One space
after each comma: the sweep re-joins whitespace that way."""

EXAMPLE_CLEAR_RGBA = 'rgba(0, 0, 0, 0)'
"""Clear, in the rgba() spelling: what tests/test_named_and_used.py's quiet
probe writes to show the sweep does not report alpha 0. Clear is not a
colour; it is how a widget is told to paint nothing."""

EXAMPLE_READER_BLACK_SHORT = '#000'
"""The three-digit black tests/test_ink_on_the_golds.py writes in its sample
sheet, which the reader must hand back as EXAMPLE_READER_BLACK. The short
spelling is the point."""

EXAMPLE_SAMPLE_LABEL_INK = '#ffffff'
"""The ink of the sample sheet's QLabel rule in tests/test_ink_on_the_golds.py,
a rule the reader must not report, because its ground is not a gold."""

EXAMPLE_DARK_PANEL_ACHROMATOPSIA = '#191919'
"""What the dark panel, BRAND_BLACK, collapses to under achromatopsia, as the
simulation in tests/test_diff_floors.py writes it: the ground the retired dark
removed line was measured against."""

EXAMPLE_ERROR_TEXT_LIGHT_REDERIVED = '#b44753'
"""What the old derivation of the light error text, lighten(STATUS_ERROR, -20),
gives against the base the register holds now. It is neither the old value
nor STATUS_ERROR_TEXT_LIGHT, which is why that value is written down rather
than derived (tests/test_error_red.py)."""

EXAMPLE_GOLD_AT_BF = '#bfd2bc93'
"""with_alpha(BRAND_GOLD, 0xBF), as the docstrings of utils/colors.py show it:
an example in prose there, which tests/test_derived_values.py's sweep must
not count as a value written out."""

EXAMPLE_EIGHT_DIGIT_LOWER = '#ed1a1a1a'
"""An eight-digit hex in lower case, the register's notation since
RNV-LOWER-EIGHT (2026-09-25): how tests/test_derived_values.py says what is
ruled."""

EXAMPLE_EIGHT_DIGIT_UPPER = '#ED1A1A1A'
"""The same value in upper case, which RNV-LOWER-EIGHT ruled out. The case is
the point."""

EXAMPLE_RENDER_PROBE = '#ff00ff'
"""The colour a render set the removed image_scrollbar_handle_hover key to on
2026-09-25 (RNV-HOVER-KEY-GONE), to see whether anything painted it. Nothing
did, across the main window and twelve dialogs in all three modes."""

# ---------------------------------------------------------------------- data

# None in this application. #56 A: the one data colour a test exempted, the
# Hex Color pattern's example, is named in utils/colors.py now.

# ------------------------------------------------------------------- retired

RETIRED_SCROLLBAR_HANDLE = '#505050'
"""The image-mode scrollbar handle until 2026-09-25, when RNV-COLLAPSE-505050
moved it to GREY_44. tests/test_derived_values.py sweeps the application for
it in every spelling. Lower case: the sweep compares it with what its decoder
reports."""

RETIRED_SCROLLBAR_HANDLE_RGBA = 'rgba(80, 80, 80, 150)'
"""The same retired handle as the palettes spelled it until 2026-09-25. The
sweep's decoder is given it, and must report RETIRED_SCROLLBAR_HANDLE."""

RETIRED_DIFF_REMOVED = '#4d1a1a'
"""The diff view's removed line in dark, until RNV-DIFF-FLOORS (2026-09-13)
found it too faint against its pane. tests/test_diff_floors.py pins every
figure it prints about it."""

RETIRED_DIFF_REMOVED_ACHROMATOPSIA = '#292929'
"""What RETIRED_DIFF_REMOVED collapses to under achromatopsia: one of the
figures tests/test_diff_floors.py pins (RNV-FIGURE-PIN), as the simulation
writes it, in lower case."""

RETIRED_DIFF_REMOVED_LIGHT = '#f8d7da'
"""The removed line in light, retired with its dark partner for the same
reason."""

RETIRED_DIFF_REMOVED_LIGHT_ACHROMATOPSIA = '#e1e1e1'
"""What RETIRED_DIFF_REMOVED_LIGHT collapses to under achromatopsia, pinned
with it."""

RETIRED_BOOTSTRAP_GREEN = '#28a745'
"""Bootstrap's green, the status family's success fill until it was retired.
tests/test_status_family.py and tests/test_error_red.py hold that no source
and no constant uses it again."""

RETIRED_BOOTSTRAP_AMBER = '#ffc107'
"""Bootstrap's amber, the old warning fill, retired with it."""

RETIRED_BOOTSTRAP_RED = '#dc3545'
"""Bootstrap's red, the old error fill, retired with its family."""

RETIRED_ERROR_TEXT_FROM_BOOTSTRAP = '#e56b77'
"""The register's old error text, derived from RETIRED_BOOTSTRAP_RED and an
orphan once that was retired."""

RETIRED_ERROR_TEXT_LIGHT_FROM_BOOTSTRAP = '#c82131'
"""The register's old light error text, RETIRED_BOOTSTRAP_RED darkened by 20:
the same orphan, in light. It carried text on every light rung down to
GOLD_TEXT_GROUND_FLOOR (4.6100 there)."""

RETIRED_SUCCESS_TEXT_LIGHT_REV30 = '#8a6581'
"""The light success text at register rev 30, walked against
APP_SURFACE_LIGHT_3. Rev 31 re-walked it against GOLD_TEXT_GROUND_FLOOR to
STATUS_SUCCESS_TEXT_LIGHT."""

RETIRED_WARNING_TEXT_LIGHT_REV30 = '#976633'
"""The light warning text at rev 30, re-walked the same way at rev 31."""

RETIRED_ERROR_TEXT_LIGHT_REV30 = '#b84e58'
"""The light error text at rev 30, re-walked the same way at rev 31."""

RETIRED_DIFF_REMOVED_CANDIDATE = '#2e0f10'
"""A candidate for the dark removed line, derived during RNV-DIFF-FLOORS
(2026-09-13) and rejected, never used. Its figures -- 0.31, a collapse to
RETIRED_DIFF_REMOVED_CANDIDATE_ACHROMATOPSIA, 15.87, and a text contrast of
12.97 -- were printed for a day as RETIRED_DIFF_REMOVED's (RNV-FIGURE-PIN)."""

RETIRED_DIFF_REMOVED_CANDIDATE_ACHROMATOPSIA = '#181818'
"""What RETIRED_DIFF_REMOVED_CANDIDATE collapses to under achromatopsia: one of
the four figures that described the wrong value."""

RETIRED_REGEX_MATCH_LIGHT = '#ffff99'
"""The light regex match highlight until RNV-REGEX-FLOOR (2026-09-13): 23.83
from the test pane in normal vision and 0.41 under achromatopsia, where it
collapsed onto APP_SURFACE_LIGHT_3 and a matched span showed no highlight."""

RETIRED_OLD_DARK_GOLD_TINT = '#c4a458'
"""A tint of the retired dark gold, kept as a light hover after that gold
went. rnv-color-picker rendered it on one key for months with nothing to
notice: the failure the derived golds exist to stop."""

RETIRED_GOLD_PRESSED = '#bba57c'
"""BRAND_GOLD_PRESSED until the dark golds were counted: lighten(BRAND_GOLD, -23),
a third gold whose only job was a 2px tab underline. Pressed returned to the
accent."""

RETIRED_IMAGE_LABEL_RGBA = 'rgba(26, 26, 26, 191)'
"""How image mode wrote BRAND_BLACK at alpha 191 until 2026-09-25, with nothing
relating it to BRAND_BLACK. It is with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA)
now (RNV-DERIVE-ALPHA)."""

RETIRED_SCROLLBAR_HANDLE_HOVER_RGBA = 'rgba(100, 100, 100, 200)'
"""What image_scrollbar_handle_hover held, a grey on no register row, until
the key was removed on 2026-09-25 (RNV-HOVER-KEY-GONE): nothing painted it."""

# ------------------------------------------------------------------ register

REGISTER_APP_SURFACE_LIGHT_2 = '#fbfbfb'
"""The second light rung, which the brand publishes and this application does
not draw. tests/test_light_rewalk.py measures the re-walked status text on
every light rung down to GOLD_TEXT_GROUND_FLOOR, this one included."""

REGISTER_APP_PRESSED_LIGHT = '#e0e0e0'
"""The light pressed plate, the rung below GOLD_TEXT_GROUND_FLOOR where brand
text stops: tests/test_light_rewalk.py asserts the text fails here. This
application draws the same hex only as GREY_E0, its scrollbar track, a
declared coincidence in another role; it draws no pressed plate at it."""

REGISTER_STATUS_SUCCESS = '#926c89'
"""The brand's success fill. This application draws status as text and
carries no fill (RNV-NAMED-AND-USED, 2026-10-04); tests/test_status_family.py
holds that no status key is painted with one."""

REGISTER_STATUS_WARNING = '#a2703c'
"""The brand's warning fill, held for the same check."""

REGISTER_STATUS_ERROR = '#c75b64'
"""The brand's error fill, held for the same check."""

# ------------------------------------------------------------------- invalid

# None in this application.

REGISTER_REFS = {
    'REGISTER_APP_SURFACE_LIGHT_2': 'APP.surface-light-2',
    'REGISTER_APP_PRESSED_LIGHT': 'APP.pressed-light',
    'REGISTER_STATUS_SUCCESS': 'STATUS.success',
    'REGISTER_STATUS_WARNING': 'STATUS.warning',
    'REGISTER_STATUS_ERROR': 'STATUS.error',
}
"""The brand name each REGISTER_ value is published under, at this
application's pin; tests/test_colour_values.py checks each against it."""
