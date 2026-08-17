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
]
