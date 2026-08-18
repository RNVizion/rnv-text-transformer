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
APP_TEXT: Final[str] = '#e0e0e0'

#: engine/brand.py APP["text-dim"]
APP_TEXT_DIM: Final[str] = '#aaaaaa'

#: engine/brand.py STATUS["success"]
STATUS_SUCCESS: Final[str] = '#28a745'

#: engine/brand.py STATUS["warning"]
STATUS_WARNING: Final[str] = '#ffc107'

#: engine/brand.py STATUS["error"]
STATUS_ERROR: Final[str] = '#dc3545'


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
# The light-mode equivalents ARE derived (BRAND_DARK_GOLD_DEEP). Dark
# mode is the half still minting, and a future pass should close it --
# which would change these values, so it is not this pass.

#: dark-mode hover. Named in the register by hex, not promoted
GOLD_HOVER: Final[str] = '#dcc9a3'

#: dark-mode pressed. Same standing
GOLD_PRESSED: Final[str] = '#b7a480'


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

GREY_25: Final[str] = '#252525'
GREY_3A: Final[str] = '#3a3a3a'
GREY_44: Final[str] = '#444444'
GREY_50: Final[str] = '#505050'
GREY_55: Final[str] = '#555555'
GREY_60: Final[str] = '#606060'
GREY_66: Final[str] = '#666666'
GREY_88: Final[str] = '#888888'
GREY_99: Final[str] = '#999999'
GREY_CC: Final[str] = '#cccccc'
GREY_DD: Final[str] = '#dddddd'
GREY_E8: Final[str] = '#e8e8e8'
GREY_EE: Final[str] = '#eeeeee'
GREY_F0: Final[str] = '#f0f0f0'
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


__all__ = [
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
    'STATUS_SUCCESS',
    'STATUS_WARNING',
    'STATUS_ERROR',
    'GOLD_HOVER',
    'GOLD_PRESSED',
    'GREY_25',
    'GREY_3A',
    'GREY_44',
    'GREY_50',
    'GREY_55',
    'GREY_60',
    'GREY_66',
    'GREY_88',
    'GREY_99',
    'GREY_CC',
    'GREY_DD',
    'GREY_E8',
    'GREY_EE',
    'GREY_F0',
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
