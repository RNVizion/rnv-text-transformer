"""
RNV Text Transformer - Brand Colors Module
Single source of truth for the RNV brand gold values.

These two values are ruled by the RNV brand register. They are not local
styling choices and must not be re-derived from what the application happens
to do with them.


Naming
------
The light-mode value is ``BRAND_DARK_GOLD``, not ``BRAND_GOLD_DARK``.
"Dark gold" is the colour; "gold dark" reads as a modifier bolted on. It is
darker *because the ground is lighter* -- it serves light-mode surfaces, which
is the opposite of what the older name suggested.

This identifier is held constant across every RNV repository. A brand system
that cannot hold one identifier across its own repos is not positioned to
align anyone else's.


Why BRAND_DARK_GOLD is #8c7337 and not #b19145
--------------------------------------------------
The register read gold-on-white as 3.00:1 and granted permissions on that
figure. The true value for #b19145 is 2.997638 -- short of the 3.0 large-text
and non-text floors by 0.0024. Nothing caught it because 3.00 is what a
contrast tool displays; the number was read and the accompanying fail flags
were not.

Measured against the six jobs the value actually has:

                                   floor    #b19145    #8c7337
    as text on #ffffff              4.5     2.9976 x   4.5429 ok
    as a border on #ffffff          3.0     2.9976 x   4.5429 ok
    as a border on #f5f5f5          3.0     2.7495 x   4.1670 ok
    as a fill, black on it          4.5     7.0055 ok  4.6226 ok
    as a fill, white on it          4.5     2.9976 x   4.5429 ok
    as text on #eeeeee              4.5     2.5837 x   3.9156 x
                                            1 of 6     5 of 6

The cost is real and not hidden: black on the fill drops 7.0055 -> 4.6226,
headroom traded on the one job the old value did well to bring four failing
jobs across. Gold as text on #eeeeee still fails and is still not permitted.

TEXT ON GOLD IS STILL #000000. At this value black is 4.6226 and white is
4.5429, so black stays correct and the register's rule survives untouched.


Usage
-----
    from utils.colors import BRAND_GOLD, BRAND_DARK_GOLD, with_alpha

    DARK  = {'accent': BRAND_GOLD}
    LIGHT = {'accent': BRAND_DARK_GOLD}

    # Qt #AARRGGBB -- primary gold at 75% alpha
    highlight = with_alpha(BRAND_GOLD, 0xBF)   # '#BFd2bc93'
"""

from __future__ import annotations

from typing import Final


# ==================== BRAND VALUES ====================

#: Bright gold. Dark and image-mode surfaces.
BRAND_GOLD: Final[str] = '#d2bc93'

#: Deep gold. Light-mode surfaces -- darker because the ground is lighter.
BRAND_DARK_GOLD: Final[str] = '#8c7337'


# ==================== DERIVED (NOT REGISTER VALUES) ====================
#
# The two below are app-level interaction states, not brand values. The register
# does not rule them. They are DERIVED from BRAND_DARK_GOLD rather than written
# down, so that if the brand value moves again they move with it -- which is
# exactly what failed last time: #c4a458 was a tint of the retired #b19145 and
# would have been left behind pointing at a value no longer in the palette.

def lighten(color: str, step: int) -> str:
    """
    Raise every channel by ``step``, clamped to 0-255.

    A uniform per-channel step, which is the relationship the light palette has
    always used between its accent and its hover tint (#b19145 -> #c4a458 is
    +19 on each channel).

    Args:
        color: Six-digit hex string, with or without a leading '#'
        step: Amount to add to each channel; negative darkens

    Returns:
        Six-digit hex string, lowercase

    Example:
        >>> lighten(BRAND_DARK_GOLD, -14)
        '#7e6529'
    """
    rgb = color.lstrip('#')
    if len(rgb) != 6:
        raise ValueError(f"expected a six-digit hex colour, got {color!r}")
    chans = [int(rgb[i:i + 2], 16) for i in (0, 2, 4)]
    return '#' + ''.join(f'{max(0, min(255, c + step)):02x}' for c in chans)


#: Light-mode DEEP gold. The single derivative, serving two roles.
#:
#: 1. Hover backgrounds (combo, table, list, tree rows; slider handles).
#:    These carry white text, exactly as the selected row does, so they need a
#:    gold dark enough for white. The previous hover value was a LIGHTER tint
#:    (#9f864a) and white measured 3.5099 on it -- a failure inherited from
#:    the pre-alignment palette, where it was 2.3868.
#:
#: 2. Gold-bearing text on a light ground. #8c7337 fills and bounds
#:    correctly everywhere, but as text it measures 4.1670 on #f5f5f5, 3.9156
#:    on #eeeeee and 3.7077 on #e8e8e8, against a 4.5 floor.
#:
#: Both roles want the same thing -- a darker gold -- so they share one value
#: rather than each carrying its own.
#:
#:    white on it .................. 5.5547
#:    as text on #f5f5f5 ........... 5.0949
#:    as text on #eeeeee ........... 4.7875
#:    as text on #e8e8e8 ........... 4.5334   <- binding
#:
#: -14 per channel is the smallest uniform step that clears all four.
#: -13 gives 4.4675 on #e8e8e8 and fails. Hue is unchanged at 42.4 degrees.
#:
#: Hover moves AWAY from the ground, which is what dark mode already does:
#: a dark ground takes a lighter hover, a light ground takes a deeper one.
#:
#: Never use as a fill under BLACK text -- black on it is 3.66:1.
BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)

#: Light-mode pressed state. It IS the accent: darkening from BRAND_DARK_GOLD
#: drops black-on-gold under the 4.5 floor (a shade 18% darker measures 3.37),
#: which would force white text and break the register's text-on-gold rule.
#: There is nowhere for a darker pressed value to go.
BRAND_DARK_GOLD_PRESSED: Final[str] = BRAND_DARK_GOLD


# ==================== THE REGISTER, MIRRORED ====================
#
# Mirrored from RNVizion/rnv-brand engine/brand.py. MIRRORED, not
# imported: this application ships standalone and cannot take a
# dependency on the brand repository. tests/test_brand_mirror.py fails
# if these drift, whenever that package is importable.
#
# engine/brand.py's APP dict is this app's dark palette almost exactly --
# window, panel, card, border, text, text-dim. It was named there while
# this file spelled it out in hex.

#: App window ground; text on gold, on either surface
TRUE_BLACK: Final[str] = '#000000'

#: Light-surface cards and inputs; the ramp's far anchor
WHITE: Final[str] = '#ffffff'

#: Brand black (charcoal). Raised surfaces in apps
BRAND_BLACK: Final[str] = '#1a1a1a'

#: engine/brand.py APP["card"]
APP_CARD: Final[str] = '#2a2a2a'

#: engine/brand.py APP["border"]
APP_BORDER: Final[str] = '#333333'

#: engine/brand.py APP["text"]
APP_TEXT: Final[str] = '#dddddd'

#: engine/brand.py APP["text-dim"]
APP_TEXT_DIM: Final[str] = '#aaaaaa'

#: engine/brand.py APP["panel-hover"]. The dark interaction plate, and the n=+2
#: rung of the dark surface ladder BRAND_BLACK + n*0x10, n in -1..+2:
#: #0a0a0a canvas, #1a1a1a panel, #2a2a2a card, #3a3a3a panel-hover.
#:
#: WAS GREY_3A, A RAMP STEP, until rnv-brand rev 22 registered it on
#: 2026-08-29. The register had called the ladder "two-thirds specified"
#: because APP_BORDER #333333 is not #3a3a3a and so looked like a missing rung.
#: It is not a rung at all: #333333 is grey(3) on the INK grid, which governs
#: inks and EDGES, and a border is an edge. Two families compared to each
#: other. The ladder was complete the whole time.
APP_PANEL_HOVER: Final[str] = '#3a3a3a'

#: engine/brand.py APP["hover-light"]. grey(14). The light interaction plate --
#: bg_hover in the light dialog palette.
#:
#: Registered 2026-08-29 as #e8e8e8 and moved here on 2026-08-30 in rev 23,
#: before any app had been wired to it. #e8e8e8 is the ground
#: BRAND_DARK_GOLD_DEEP is calibrated against -- see GOLD_TEXT_GROUND_FLOOR
#: below -- so a hover plate on that value clears the 4.5 text floor by 0.0334
#: and fails the moment the gold moves one step. This clears by 0.2875.
#: A boundary is not a plate.
#:
#: GREY_EE HOLDS THE SAME HEX AND IS NOT THIS. Three static surfaces still use
#: the ramp step; only the hover plate is the register's. Recorded as a
#: coincidence in tests/test_brand_mirror.py and asserted in both directions.
APP_HOVER_LIGHT: Final[str] = '#eeeeee'

#: engine/brand.py GOLD_TEXT_GROUND_FLOOR. The darkest light ground on which
#: the gold family carries text.
#:
#: WAS GREY_E8, A RAMP STEP, until rnv-brand rev 24 registered it on
#: 2026-08-30 -- and it was registered because this file showed it was doing
#: register work with no register entry. BRAND_DARK_GOLD_DEEP is defined above
#: as the smallest uniform step that clears #e8e8e8: -14 gives 4.5334, and -13
#: gives 4.4675 and fails. That derivative is published, checked, mirrored and
#: pinned in five repositories. Its INPUT was app-owned, so nothing could
#: mirror the constraint the whole derivation rests on.
#:
#: Both uses here are grounds the gold family draws on: bg_tertiary, which
#: carries the About dialog's tab labels, and line_number_current_bg, whose
#: foreground is BRAND_DARK_GOLD_DEEP itself.
GOLD_TEXT_GROUND_FLOOR: Final[str] = '#e8e8e8'

#: engine/brand.py STATUS["success"]
STATUS_SUCCESS: Final[str] = '#28a745'

#: engine/brand.py STATUS["warning"]
STATUS_WARNING: Final[str] = '#ffc107'

#: engine/brand.py STATUS["error"]
STATUS_ERROR: Final[str] = '#dc3545'

#: Derived. Error TEXT on a light dialog ground.
#:
#: No red carries text at 4.5:1 on a real light panel: STATUS_ERROR clears
#: only pure white, at 4.5275, and reads 4.1528 on this app's #f5f5f5 dialog
#: background. Light therefore spends a derivative on TEXT for exactly the
#: reason the gold does -- the fill and text jobs occupy non-overlapping
#: luminance bands.
#:
#: 5.1811 on #f5f5f5, 4.8685 on #eeeeee, 4.6100 on #e8e8e8 -- the same
#: coverage boundary BRAND_DARK_GOLD_DEEP publishes. Below #e8e8e8 red does
#: not carry text, which is a ruling rather than a gap.
#:
#: Derived, not written down, so it cannot orphan the way #c4a458 did when
#: the gold it was a tint of was retired. A uniform per-channel step holds
#: hue at 354.25 degrees, identical to STATUS_ERROR.
#:
#: DARK is deliberately not given one. See test_dark_error_text_is_short,
#: which records the shortfall in both directions.
STATUS_ERROR_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)   # -> #c82131


# ============ HAND-PICKED GOLD MODULATIONS ============
#
# The register names #dcc9a3 by hex and refuses to promote it:
#
#   "Values between and beyond the two are modulations, and none of
#    them is promoted. #dcc9a3 (three apps) sits on the gold axis
#    extended past brand gold by about 30%... A surface that needs a
#    lighter or darker gold derives it; it doesn't mint one."
#
# These two were minted. They are named here rather than re-derived,
# because no simple rule reproduces them: against BRAND_GOLD their
# deltas are +10,+13,+16 and -27,-24,-19, and neither an HLS lightness
# move nor a white/black mix lands on them exactly. Inventing a formula
# that happens to hit a hand-picked number is a literal in disguise.
#
# That future pass is this one. Dark mode now runs on two golds:
# BRAND_GOLD and BRAND_GOLD_HOVER derived from it. BRAND_GOLD_PRESSED returned
# to the accent, which is where the third value went.

#: dark-mode hover. DERIVED, not minted -- the register rules that a surface
#: needing a lighter or darker gold derives it. Held closest to the value it
#: replaces (#dcc9a3, RGB distance 2.4) rather than to a tidy step, because the
#: brief was to change the provenance and not the appearance. Hue snaps back to
#: BRAND_GOLD's 39.0 degrees exactly; the minted value had drifted to 40.0.
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)

#: dark-mode pressed. It IS the accent, mirroring light mode.
#:
#: The brand registers two golds and derives the rest when needed. Each mode
#: gets the registered gold and ONE derivative -- light spends its on
#: BRAND_DARK_GOLD_DEEP, dark spends its on BRAND_GOLD_HOVER -- and every other gold
#: role reuses one of the two. Pressed returning to rest is what holds the
#: count there, and tests/test_brand_mirror.py asserts the count.
#:
#: This replaced lighten(BRAND_GOLD, -23) = #bba57c, a third gold whose only
#: consumer was a 2px tab underline. On the dark hover ground #3a3a3a that
#: underline moves 4.7589 -> 6.1503, both above the 3.0 component floor, so
#: nothing was failing -- which is the point. An extra gold is usually
#: perfectly legible, so only counting finds it.
#:
#: The interaction still reads: rest at the accent, hover lifts away from the
#: dark ground, pressed drops back to rest.
BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD


# ============ THE APP'S NEUTRAL RAMP ============
#
# The register declines to name these, deliberately:
#
#   "Every neutral in all five desktop apps -- twenty-three distinct
#    values from #000000 to #ffffff -- is a pure grey, R = G = B,
#    without exception. That isn't twenty-three colors; it's one ramp
#    with steps chosen per surface. The brand doesn't publish them,
#    doesn't count them, and doesn't drift when an app adds one."
#
# So these are APP-OWNED, named as ramp steps rather than dressed up as
# brand values. The two anchors (TRUE_BLACK, WHITE) and the four steps
# the register does name (BRAND_BLACK, APP_CARD, APP_BORDER, APP_TEXT,
# APP_TEXT_DIM) are above; these are the rest of this app's layering.
#
# Named by their byte so the ramp reads in order and a step cannot be
# confused with a role. Adding one is not drift.

GREY_44: Final[str] = '#444444'
GREY_55: Final[str] = '#555555'
GREY_60: Final[str] = '#606060'
GREY_66: Final[str] = '#666666'
GREY_88: Final[str] = '#888888'
GREY_CC: Final[str] = '#cccccc'
GREY_DD: Final[str] = '#dddddd'
#: The LIGHT scrollbar track. Held by APP_TEXT until 2026-08-28, when the ink
#: moved to grey(13) and this did not follow -- it is a surface, and the
#: published grid governs inks and edges only. rnv-color-picker and
#: rnv-icon-builder both carry this same track at this same value.
#:
#: THIS COMMENT SAT ONE CONSTANT LOWER until 2026-08-30, where it documented
#: GREY_E8 while describing GREY_E0's job: the scrollbar track is #e0e0e0
#: (utils/dialog_styles.py 'scrollbar_bg'), and #e0e0e0 is what APP["text"]
#: held before the ink moved. Moved when GREY_E8 became a register mirror --
#: carrying a docstring that describes a different value into a mirror is how
#: a wrong fact acquires the authority of a checked one.
GREY_E0: Final[str] = '#e0e0e0'
#: grey(14). Three STATIC surfaces: the diff export header in both modes, and
#: the line number gutter's resting ground. NOT the light hover plate, which is
#: APP_HOVER_LIGHT and holds this same hex -- one value, two roles, and only
#: one of them is the register's. See COINCIDENT in tests/test_brand_mirror.py.
GREY_EE: Final[str] = '#eeeeee'
GREY_F5: Final[str] = '#f5f5f5'


# ============ APP SEMANTICS ============
#
# Neither brand values nor ramp steps. Diff highlighting borrows the
# Bootstrap alert palette; the regex colours are this app alone.


DIFF_ADDED_DARK: Final[str] = '#1a4d1a'

DIFF_REMOVED_DARK: Final[str] = '#4d1a1a'

DIFF_CHANGED_DARK: Final[str] = '#4d4d1a'

DIFF_CURRENT_DARK: Final[str] = '#4d1a4d'
#: Bootstrap alert-success background
DIFF_ADDED_LIGHT: Final[str] = '#d4edda'
#: Bootstrap alert-danger background
DIFF_REMOVED_LIGHT: Final[str] = '#f8d7da'
#: Bootstrap alert-warning background
DIFF_CHANGED_LIGHT: Final[str] = '#fff3cd'

DIFF_CURRENT_LIGHT: Final[str] = '#e2d4f0'

REGEX_MATCH_DARK: Final[str] = '#4a4a00'

REGEX_MATCH_LIGHT: Final[str] = '#ffff99'


#: Dark-only capture-group highlighting; index 0 is group 1.
REGEX_GROUP_PALETTE: Final[tuple[str, ...]] = (
    '#3d5c5c',
    '#5c3d5c',
    '#5c5c3d',
    '#3d5c3d',
    '#5c3d3d',
    '#3d3d5c',
    '#5c4d3d',
    '#3d5c4d',
)

# ==================== ALPHA HELPER ====================

def with_alpha(color: str, alpha: int) -> str:
    """
    Express a six-digit brand hex in Qt's ``#AARRGGBB`` form.

    Qt writes translucent colours with the alpha channel *first*, which is why
    a ``#[0-9a-f]{6}`` search does not find them -- it either misses the value
    or matches the wrong six characters. Any guard that audits brand colour
    usage has to read this form as well as the plain one, and any sweep that
    rewrites a six-digit value has to avoid corrupting it.

    Args:
        color: Six-digit hex string, with or without a leading '#'
        alpha: Alpha channel, 0-255 (0xBF is 75%)

    Returns:
        Eight-digit ``#AARRGGBB`` string, RGB digits preserved as given

    Raises:
        ValueError: If color is not six hex digits or alpha is out of range

    Example:
        >>> with_alpha(BRAND_GOLD, 0xBF)
        '#BFd2bc93'
    """
    rgb = color.lstrip('#')

    if len(rgb) != 6:
        raise ValueError(
            f"expected a six-digit hex colour, got {color!r} "
            f"({len(rgb)} digits) -- if this is already #AARRGGBB, pass the "
            f"six-digit value instead"
        )

    try:
        int(rgb, 16)
    except ValueError as exc:
        raise ValueError(f"not a hex colour: {color!r}") from exc

    if not 0 <= alpha <= 255:
        raise ValueError(f"alpha must be 0-255, got {alpha}")

    return f"#{alpha:02X}{rgb}"


# ==================== PROVENANCE ====================
#
# Where every colour constant in this module comes from. Declarative and
# in the file rather than in the test, because a classification that lives
# only in a test goes stale in the direction that reports clean: add a
# constant, forget the test entry, and the test passes while checking one
# fewer thing than it claims.
#
# tests/test_brand_mirror.py asserts this is complete in BOTH directions,
# that every "register" entry still matches rnv-brand, that every
# "derived" entry is genuinely computed rather than a literal wearing the
# label, and that nothing app-owned is secretly a register value.
#
#   register      mirrored from RNVizion/rnv-brand engine/brand.py
#   derived       computed here from a register value
#   app-ramp      a step on this app's neutral ramp; the register
#                 explicitly declines to name these
#   app-semantic  neither brand nor ramp -- diff and regex highlighting

PROVENANCE: Final[dict[str, str]] = {
    # -- register
    'BRAND_GOLD': 'register',
    'BRAND_DARK_GOLD': 'register',
    'TRUE_BLACK': 'register',
    'WHITE': 'register',
    'BRAND_BLACK': 'register',
    'APP_CARD': 'register',
    'APP_BORDER': 'register',
    'APP_TEXT': 'register',
    'APP_TEXT_DIM': 'register',
    'APP_PANEL_HOVER': 'register',
    'APP_HOVER_LIGHT': 'register',
    'GOLD_TEXT_GROUND_FLOOR': 'register',
    'STATUS_SUCCESS': 'register',
    'STATUS_WARNING': 'register',
    'STATUS_ERROR': 'register',
    # -- derived
    'STATUS_ERROR_LIGHT': 'derived',
    'BRAND_DARK_GOLD_DEEP': 'derived',
    'BRAND_DARK_GOLD_PRESSED': 'derived',
    'BRAND_GOLD_HOVER': 'derived',
    'BRAND_GOLD_PRESSED': 'derived',
    # -- app-ramp
    'GREY_44': 'app-ramp',
    'GREY_55': 'app-ramp',
    'GREY_60': 'app-ramp',
    'GREY_66': 'app-ramp',
    'GREY_88': 'app-ramp',
    'GREY_CC': 'app-ramp',
    'GREY_DD': 'app-ramp',
    'GREY_E0': 'app-ramp',
    'GREY_EE': 'app-ramp',
    'GREY_F5': 'app-ramp',
    # -- app-semantic
    'DIFF_ADDED_DARK': 'app-semantic',
    'DIFF_REMOVED_DARK': 'app-semantic',
    'DIFF_CHANGED_DARK': 'app-semantic',
    'DIFF_CURRENT_DARK': 'app-semantic',
    'DIFF_ADDED_LIGHT': 'app-semantic',
    'DIFF_REMOVED_LIGHT': 'app-semantic',
    'DIFF_CHANGED_LIGHT': 'app-semantic',
    'DIFF_CURRENT_LIGHT': 'app-semantic',
    'REGEX_MATCH_DARK': 'app-semantic',
    'REGEX_MATCH_LIGHT': 'app-semantic',
    'REGEX_GROUP_PALETTE': 'app-semantic',
}

__all__ = [
    'PROVENANCE',
    'BRAND_GOLD',
    'BRAND_DARK_GOLD',
    'BRAND_DARK_GOLD_DEEP',
    'BRAND_DARK_GOLD_PRESSED',
    'lighten',
    'with_alpha',
    'TRUE_BLACK',
    'WHITE',
    'BRAND_BLACK',
    'APP_CARD',
    'APP_BORDER',
    'APP_TEXT',
    'APP_TEXT_DIM',
    'APP_PANEL_HOVER',
    'APP_HOVER_LIGHT',
    'GOLD_TEXT_GROUND_FLOOR',
    'STATUS_SUCCESS',
    'STATUS_WARNING',
    'STATUS_ERROR',
    'STATUS_ERROR_LIGHT',
    'BRAND_GOLD_HOVER',
    'BRAND_GOLD_PRESSED',
    'GREY_44',
    'GREY_55',
    'GREY_60',
    'GREY_66',
    'GREY_88',
    'GREY_CC',
    'GREY_DD',
    'GREY_E0',
    'GREY_EE',
    'GREY_F5',
    'DIFF_ADDED_DARK',
    'DIFF_REMOVED_DARK',
    'DIFF_CHANGED_DARK',
    'DIFF_CURRENT_DARK',
    'DIFF_ADDED_LIGHT',
    'DIFF_REMOVED_LIGHT',
    'DIFF_CHANGED_LIGHT',
    'DIFF_CURRENT_LIGHT',
    'REGEX_MATCH_DARK',
    'REGEX_MATCH_LIGHT',
    'REGEX_GROUP_PALETTE',
]
