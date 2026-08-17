#!/usr/bin/env python3
"""
Gold alignment -> rnv-text-transformer
=======================================

Applies the Brand Infrastructure ruling of August 17, 2026 (third and final
version) to a fresh checkout of rnv-text-transformer@main.

    BRAND_GOLD       #d2bc93   unchanged
    BRAND_DARK_GOLD  #b19145 -> #8c7337

Both the name and the value move. The value moves because the register's own
figure for gold-on-white was 3.00:1, a display rounding of 2.997638 -- short of
the 3.0 floor by 0.0024. #b19145 does 1 of its 6 jobs; #8c7337 does 5.

Run from the repository root:

    python3 apply_gold_alignment.py              # apply, regenerate, verify
    python3 apply_gold_alignment.py --check      # dry run, change nothing
    python3 apply_gold_alignment.py --setup-env  # apt+pip first (fresh Codespace)
    python3 apply_gold_alignment.py --skip-verify

Safe to run twice: every step detects its own prior application and no-ops.
Nothing is committed -- the working tree is left for you to review.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# The ruling
# ---------------------------------------------------------------------------

BRAND_GOLD = '#d2bc93'          # primary, unchanged
OLD_DARK_GOLD = '#b19145'       # retired
NEW_DARK_GOLD = '#8c7337'       # ruled value

# The light palette's hover tint has always been the accent plus a uniform +19
# on every channel (#b19145 -> #c4a458). Re-derived from the new accent rather
# than left behind: #8c7337 -> #9f864a. Same step, same relationship.
LIGHT_HOVER_STEP = 19
OLD_LIGHT_HOVER = '#c4a458'     # tint of the retired value
OLD_LIGHT_PRESSED = '#8a7236'   # shade of the retired value


def _lighten(color: str, step: int) -> str:
    rgb = color.lstrip('#')
    return '#' + ''.join(
        f'{max(0, min(255, int(rgb[i:i + 2], 16) + step)):02x}' for i in (0, 2, 4)
    )


NEW_LIGHT_HOVER = _lighten(NEW_DARK_GOLD, LIGHT_HOVER_STEP)   # -> #9f864a

# Sentinel for places that name the retired value *on purpose* -- change
# history, the docstring that explains why the value moved. A blanket sweep
# would otherwise rewrite them into nonsense ("#8c7337 replaced #8c7337").
RETIRED = '@@RETIRED_GOLD@@'

# Files the note counts. Used as a pre-flight fingerprint.
EXPECTED_BASE_COUNTS = {
    'utils/dialog_styles.py': 14,
    'ui/drag_drop_text_edit.py': 2,
    'test_rnv_text_transformer.py': 4,
    'docs/RNV_Brand_Color_System.md': 85,
    'docs/RNV_Custom_Tooltip_System.md': 3,
    'README.md': 2,
}

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    '\033[32m', '\033[33m', '\033[31m', '\033[2m', '\033[1m', '\033[0m'
)


def say(msg: str, colour: str = '') -> None:
    print(f"{colour}{msg}{OFF}" if colour else msg)


def step(n: str, msg: str) -> None:
    print(f"\n{BOLD}[{n}]{OFF} {msg}")


def ok(msg: str) -> None:
    say(f"    + {msg}", GREEN)


def skip(msg: str) -> None:
    say(f"    = {msg} (already applied)", DIM)


def warn(msg: str) -> None:
    say(f"    ! {msg}", YELLOW)


def die(msg: str) -> None:
    say(f"\nABORT: {msg}", RED)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Contrast -- WCAG 2.x relative luminance. The table in the brand doc is
# generated from this, not transcribed, because transcription is what produced
# a 4.0 where the true figure was 2.9976.
# ---------------------------------------------------------------------------

def _luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip('#')
    if len(h) == 8:                      # Qt #AARRGGBB -- drop alpha
        h = h[2:]
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chans = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def wcag_grade(ratio: float) -> str:
    if ratio >= 7.0:
        return 'AAA'
    if ratio >= 4.5:
        return 'AA'
    if ratio >= 3.0:
        return 'AA (large text only)'
    return 'FAIL'


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

class Editor:
    """Applies exact-string edits, refusing anything ambiguous."""

    def __init__(self, path: Path, dry_run: bool):
        self.path = path
        self.dry_run = dry_run
        self.text = path.read_text(encoding='utf-8')
        self.original = self.text
        self.edits = 0

    def replace_once(self, old: str, new: str, *, required: bool = True) -> bool:
        n = self.text.count(old)
        if n == 0:
            if required and self.text.count(new) == 0:
                die(f"{self.path}: expected to find:\n    {old[:120]!r}\n"
                    f"  but it is not present and neither is its replacement. "
                    f"Is this checkout at origin/main?")
            return False
        if n > 1:
            die(f"{self.path}: {old[:80]!r} appears {n} times; refusing an "
                f"ambiguous edit.")
        self.text = self.text.replace(old, new)
        self.edits += 1
        return True

    def replace_all(self, old: str, new: str) -> int:
        n = self.text.count(old)
        if n:
            self.text = self.text.replace(old, new)
            self.edits += n
        return n

    def save(self) -> bool:
        if self.text == self.original:
            return False
        if not self.dry_run:
            self.path.write_text(self.text, encoding='utf-8')
        return True


def sh(cmd: list[str], *, check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, check=check, text=True,
        capture_output=quiet,
    )


# ---------------------------------------------------------------------------
# Step 1 -- utils/colors.py
# ---------------------------------------------------------------------------

COLORS_PY = '''"""
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


Why BRAND_DARK_GOLD is {new} and not {old}
--------------------------------------------------
The register read gold-on-white as 3.00:1 and granted permissions on that
figure. The true value for {old} is 2.997638 -- short of the 3.0 large-text
and non-text floors by 0.0024. Nothing caught it because 3.00 is what a
contrast tool displays; the number was read and the accompanying fail flags
were not.

Measured against the six jobs the value actually has:

                                   floor    {old}    {new}
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

    DARK  = {{'accent': BRAND_GOLD}}
    LIGHT = {{'accent': BRAND_DARK_GOLD}}

    # Qt #AARRGGBB -- primary gold at 75% alpha
    highlight = with_alpha(BRAND_GOLD, 0xBF)   # '#BFd2bc93'
"""

from __future__ import annotations

from typing import Final


# ==================== BRAND VALUES ====================

#: Bright gold. Dark and image-mode surfaces.
BRAND_GOLD: Final[str] = '{primary}'

#: Deep gold. Light-mode surfaces -- darker because the ground is lighter.
BRAND_DARK_GOLD: Final[str] = '{new}'


# ==================== DERIVED (NOT REGISTER VALUES) ====================
#
# The two below are app-level interaction states, not brand values. The register
# does not rule them. They are DERIVED from BRAND_DARK_GOLD rather than written
# down, so that if the brand value moves again they move with it -- which is
# exactly what failed last time: #c4a458 was a tint of the retired {old} and
# would have been left behind pointing at a value no longer in the palette.

def lighten(color: str, step: int) -> str:
    """
    Raise every channel by ``step``, clamped to 0-255.

    A uniform per-channel step, which is the relationship the light palette has
    always used between its accent and its hover tint ({old} -> {oldhover} is
    +19 on each channel).

    Args:
        color: Six-digit hex string, with or without a leading '#'
        step: Amount to add to each channel; negative darkens

    Returns:
        Six-digit hex string, lowercase

    Example:
        >>> lighten(BRAND_DARK_GOLD, 19)
        '{newhover}'
    """
    rgb = color.lstrip('#')
    if len(rgb) != 6:
        raise ValueError(f"expected a six-digit hex colour, got {{color!r}}")
    chans = [int(rgb[i:i + 2], 16) for i in (0, 2, 4)]
    return '#' + ''.join(f'{{max(0, min(255, c + step)):02x}}' for c in chans)


#: Light-mode hover tint. Derived, not ruled.
BRAND_DARK_GOLD_HOVER: Final[str] = lighten(BRAND_DARK_GOLD, {step})

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
    a ``#[0-9a-f]{{6}}`` search does not find them -- it either misses the value
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
            f"expected a six-digit hex colour, got {{color!r}} "
            f"({{len(rgb)}} digits) -- if this is already #AARRGGBB, pass the "
            f"six-digit value instead"
        )

    try:
        int(rgb, 16)
    except ValueError as exc:
        raise ValueError(f"not a hex colour: {{color!r}}") from exc

    if not 0 <= alpha <= 255:
        raise ValueError(f"alpha must be 0-255, got {{alpha}}")

    return f"#{{alpha:02X}}{{rgb}}"


__all__ = [
    'BRAND_GOLD',
    'BRAND_DARK_GOLD',
    'BRAND_DARK_GOLD_HOVER',
    'BRAND_DARK_GOLD_PRESSED',
    'lighten',
    'with_alpha',
]
'''.format(primary=BRAND_GOLD, old=OLD_DARK_GOLD, new=NEW_DARK_GOLD,
           oldhover=OLD_LIGHT_HOVER, newhover=NEW_LIGHT_HOVER,
           step=LIGHT_HOVER_STEP)


def step_colors_module(root: Path, dry: bool) -> None:
    step('1', 'utils/colors.py -- single source of truth')
    target = root / 'utils' / 'colors.py'
    if target.exists() and NEW_DARK_GOLD in target.read_text(encoding='utf-8'):
        skip('utils/colors.py')
        return
    if not dry:
        target.write_text(COLORS_PY, encoding='utf-8')
    ok(f"utils/colors.py  BRAND_GOLD={BRAND_GOLD}  BRAND_DARK_GOLD={NEW_DARK_GOLD}")


# ---------------------------------------------------------------------------
# Step 2 -- utils/dialog_styles.py
# ---------------------------------------------------------------------------

def step_dialog_styles(root: Path, dry: bool) -> None:
    step('2', 'utils/dialog_styles.py -- 14 literals + the two text-on-gold keys')
    ed = Editor(root / 'utils' / 'dialog_styles.py', dry)

    if 'from utils.colors import' not in ed.text:
        ed.replace_once(
            "from typing import ClassVar\nfrom functools import lru_cache",
            "from typing import ClassVar\nfrom functools import lru_cache\n\n"
            "from utils.colors import (\n    BRAND_GOLD,\n    BRAND_DARK_GOLD,\n"
            "    BRAND_DARK_GOLD_HOVER,\n    BRAND_DARK_GOLD_PRESSED,\n)",
        )
        ok('import added')
    else:
        skip('import')

    n_primary = ed.replace_all(f"'{BRAND_GOLD}'", 'BRAND_GOLD')
    n_dark = ed.replace_all(f"'{OLD_DARK_GOLD}'", 'BRAND_DARK_GOLD')
    if n_primary or n_dark:
        ok(f"{n_primary} x BRAND_GOLD, {n_dark} x BRAND_DARK_GOLD (expected 7 and 7)")
        if (n_primary, n_dark) != (7, 7):
            die(f"expected 7 and 7, got {n_primary} and {n_dark} -- base is not "
                f"what the note counted")
    else:
        skip('literal substitution')

    # The register's rule: text on gold is #000000. LIGHT had #ffffff, which was
    # 2.9976 against the old value -- the misuse the false doc figure licensed.
    changed = False
    changed |= ed.replace_once(
        "'accent_text': '#ffffff',  # Text on accent background",
        "'accent_text': '#000000',  # Text on accent background",
        required=False,
    )
    changed |= ed.replace_once(
        "'selection_text': '#ffffff',",
        "'selection_text': '#000000',",
        required=False,
    )
    if changed:
        ok('LIGHT accent_text and selection_text -> #000000 (register rule)')
    else:
        skip('text-on-gold keys')

    # The light hover/pressed tints were derived from the retired value and
    # would otherwise be left behind: #c4a458 is a tint of #b19145, and
    # #8a7236 sits 4 channel-steps from the new accent, making the pressed
    # state invisible. Both now come from BRAND_DARK_GOLD.
    tints = False
    tints |= ed.replace_once(
        f"'accent_hover': '{OLD_LIGHT_HOVER}',",
        "'accent_hover': BRAND_DARK_GOLD_HOVER,",
        required=False,
    )
    tints |= ed.replace_once(
        f"'accent_pressed': '{OLD_LIGHT_PRESSED}',",
        "'accent_pressed': BRAND_DARK_GOLD_PRESSED,",
        required=False,
    )
    if tints:
        ok(f'LIGHT accent_hover -> {NEW_LIGHT_HOVER} (derived, +{LIGHT_HOVER_STEP}/channel)')
        ok(f'LIGHT accent_pressed -> {NEW_DARK_GOLD} (the accent; darker breaks black-on-gold)')
    else:
        skip('light hover/pressed tints')

    ed.save()


# ---------------------------------------------------------------------------
# Step 3 -- utils/__init__.py
# ---------------------------------------------------------------------------

def step_utils_init(root: Path, dry: bool) -> None:
    step('3', 'utils/__init__.py -- export the constants')
    ed = Editor(root / 'utils' / '__init__.py', dry)
    if 'from utils.colors import' in ed.text:
        skip('utils/__init__.py')
        return
    ed.replace_once(
        "from utils.config import (\n    APP_NAME,",
        "from utils.colors import (\n    BRAND_GOLD,\n    BRAND_DARK_GOLD,\n"
        "    BRAND_DARK_GOLD_HOVER,\n    BRAND_DARK_GOLD_PRESSED,\n    lighten,\n"
        "    with_alpha,\n)\n\nfrom utils.config import (\n    APP_NAME,",
    )
    ed.replace_once(
        "__all__ = [\n    # Config\n    'APP_NAME',",
        "__all__ = [\n    # Brand Colors\n    'BRAND_GOLD',\n    'BRAND_DARK_GOLD',\n"
        "    'BRAND_DARK_GOLD_HOVER',\n    'BRAND_DARK_GOLD_PRESSED',\n    'lighten',\n"
        "    'with_alpha',\n    # Config\n    'APP_NAME',",
    )
    ed.save()
    ok('exported')


# ---------------------------------------------------------------------------
# Step 4 -- ui/drag_drop_text_edit.py (the 8-digit form; value unchanged)
# ---------------------------------------------------------------------------

def step_drag_drop(root: Path, dry: bool) -> None:
    step('4', 'ui/drag_drop_text_edit.py -- the 8-digit form (primary gold, unchanged)')
    ed = Editor(root / 'ui' / 'drag_drop_text_edit.py', dry)
    if 'with_alpha' in ed.text:
        skip('ui/drag_drop_text_edit.py')
        return
    ed.replace_once(
        "from utils.config import SUPPORTED_FORMATS",
        "from utils.colors import BRAND_GOLD, with_alpha\n"
        "from utils.config import SUPPORTED_FORMATS",
    )
    ed.replace_once(
        '''    # Drag highlight style
    _DRAG_HIGHLIGHT_STYLE: str = """
        QTextEdit {
            border: 2px dashed #BFd2bc93;
            background-color: #BFd2bc93;
            color: #000000;
            padding: 4px;
        }
    """''',
        '''    # Drag highlight gold -- Qt #AARRGGBB, primary brand gold at 75% alpha.
    # Not a six-digit hex: the alpha channel comes first, so a plain
    # #[0-9a-f]{6} search will neither find it nor safely rewrite it.
    _DRAG_HIGHLIGHT_GOLD: str = with_alpha(BRAND_GOLD, 0xBF)

    # Drag highlight style
    _DRAG_HIGHLIGHT_STYLE: str = f"""
        QTextEdit {{
            border: 2px dashed {_DRAG_HIGHLIGHT_GOLD};
            background-color: {_DRAG_HIGHLIGHT_GOLD};
            color: #000000;
            padding: 4px;
        }}
    """''',
    )
    ed.save()
    ok('via with_alpha(BRAND_GOLD, 0xBF) -- renders #BFd2bc93, byte-identical')


# ---------------------------------------------------------------------------
# Step 5 -- test_rnv_text_transformer.py
# ---------------------------------------------------------------------------

def step_tests(root: Path, dry: bool) -> None:
    step('5', 'test_rnv_text_transformer.py -- 2 of 4 literals change value')
    ed = Editor(root / 'test_rnv_text_transformer.py', dry)
    n = ed.replace_all(f'"{OLD_DARK_GOLD}"', f'"{NEW_DARK_GOLD}"')
    if n:
        ok(f'{n} light-accent assertions -> {NEW_DARK_GOLD} (expected 2)')
    else:
        skip('assertions')
    ed.save()


# ---------------------------------------------------------------------------
# Step 6 -- README.md and the tooltip doc
# ---------------------------------------------------------------------------

def step_small_docs(root: Path, dry: bool) -> None:
    step('6', 'README.md + docs/RNV_Custom_Tooltip_System.md')
    for rel in ('README.md', 'docs/RNV_Custom_Tooltip_System.md'):
        ed = Editor(root / rel, dry)
        n = ed.replace_all(OLD_DARK_GOLD, NEW_DARK_GOLD)
        ed.save()
        ok(f'{rel}: {n} occurrence(s)') if n else skip(rel)


# ---------------------------------------------------------------------------
# Step 7 -- docs/RNV_Brand_Color_System.md
#
# This is the file the wrong number came from. Six of its seven contrast rows
# were wrong; the seventh overstated the figure that governs. The table is
# regenerated from measurement below rather than retyped.
# ---------------------------------------------------------------------------

def _contrast_table() -> str:
    rows = [
        ('#000000', '#E0E0E0'),
        ('#1A1A1A', '#E0E0E0'),
        ('#2A2A2A', '#E0E0E0'),
        (BRAND_GOLD, '#000000'),
        ('#F5F5F5', '#000000'),
        ('#FFFFFF', '#000000'),
        (NEW_DARK_GOLD, '#000000'),
    ]
    out = [
        '| Background | Text Color | Contrast Ratio | WCAG |',
        '|-----------|------------|----------------|------|',
    ]
    for bg, fg in rows:
        r = contrast(bg, fg)
        out.append(f'| `{bg}` | `{fg}` | {r:.2f}:1 | {wcag_grade(r)} |')
    return '\n'.join(out)


def _accent_table() -> str:
    rows = [
        ('#1A1A1A', BRAND_GOLD, 'Gold text/border on dark — high visibility'),
        ('#2A2A2A', BRAND_GOLD, 'Gold border on tooltip — clear definition'),
        ('#FFFFFF', NEW_DARK_GOLD, 'Dark gold on white'),
        ('#F5F5F5', NEW_DARK_GOLD, 'Dark gold on light gray'),
        ('#EEEEEE', NEW_DARK_GOLD, 'Dark gold on hover gray — **not permitted for text**'),
    ]
    out = [
        '| Background | Accent | Measured | Result |',
        '|-----------|--------|----------|--------|',
    ]
    for bg, accent, note in rows:
        r = contrast(bg, accent)
        out.append(f'| `{bg}` | `{accent}` | {r:.4f}:1 | {note} |')
    return '\n'.join(out)


def step_brand_doc(root: Path, dry: bool) -> None:
    step('7', 'docs/RNV_Brand_Color_System.md -- values, prose, and the wrong table')
    ed = Editor(root / 'docs' / 'RNV_Brand_Color_System.md', dry)

    if 'Measured, not transcribed' in ed.text:
        skip('docs/RNV_Brand_Color_System.md')
        return

    # -- 7a. The "Why Two Golds?" prose asserted the retired value was readable.
    ed.replace_once(
        "`#d2bc93` (bright gold) on a white background has poor contrast (fails "
        "WCAG AA). `#b19145` (dark gold) provides proper readability on light "
        "surfaces while maintaining the same gold identity. On dark backgrounds, "
        "`#d2bc93` reads clearly and feels premium.",

        f"`{BRAND_GOLD}` (bright gold) on a white background has poor contrast "
        f"(fails WCAG AA). `{NEW_DARK_GOLD}` (dark gold) clears the 4.5 floor on "
        f"light surfaces — as text, as a border, and as a fill under black — "
        f"while keeping the same gold identity. On dark backgrounds, "
        f"`{BRAND_GOLD}` reads clearly and feels premium.\n\n"
        f"**`{NEW_DARK_GOLD}` replaced `{RETIRED}` on 17 August 2026.** The "
        f"retired value measured **2.997638:1** against white — short of the 3.0 "
        f"floor by 0.0024, and of the 4.5 text floor by far more. It cleared 1 of "
        f"its 6 jobs; the current value clears 5. The exception is gold as text on "
        f"`#EEEEEE` ({contrast(NEW_DARK_GOLD, '#EEEEEE'):.4f}:1), which still fails "
        f"and is still not permitted.\n\n"
        f"**Text on gold is `#000000`.** At `{NEW_DARK_GOLD}` black measures "
        f"{contrast(NEW_DARK_GOLD, '#000000'):.4f}:1 and white "
        f"{contrast(NEW_DARK_GOLD, '#FFFFFF'):.4f}:1.",
    )
    ok('"Why Two Golds?" — retired value no longer described as readable')

    # -- 7b. Dialog button pressed row: white on gold -> black on gold.
    ed.replace_once(
        f"| Pressed | **`{OLD_DARK_GOLD}`** | `#FFFFFF` | `{OLD_DARK_GOLD}` |",
        f"| Pressed | **`{NEW_DARK_GOLD}`** | `#000000` | `{NEW_DARK_GOLD}` |",
    )
    ok('dialog button pressed text -> #000000')

    # -- 7b2. The light hover/pressed tints in the identity table and the
    # LIGHT palette listing.
    ed.replace_once(
        f"| **Brand Gold (Hover)** | `#dcc9a3` | `{OLD_LIGHT_HOVER}` | "
        f"Lighter tint for hover feedback |\n"
        f"| **Brand Gold (Pressed)** | `#b7a480` | `{OLD_LIGHT_PRESSED}` | "
        f"Darker shade for pressed/active states |",

        f"| **Brand Gold (Hover)** | `#dcc9a3` | `{NEW_LIGHT_HOVER}` | "
        f"Lighter tint for hover feedback — derived as accent +{LIGHT_HOVER_STEP}/channel |\n"
        f"| **Brand Gold (Pressed)** | `#b7a480` | `{NEW_DARK_GOLD}` | "
        f"Pressed/active. On light this **is** the accent: a darker shade drops "
        f"black-on-gold under 4.5 and would force white text |",
    )
    ed.replace_all(f"'{OLD_LIGHT_HOVER}',   # Hover tint",
                   f"'{NEW_LIGHT_HOVER}',   # Hover tint (derived from accent)")
    ed.replace_all(f"'{OLD_LIGHT_PRESSED}',   # Pressed/active shade",
                   f"'{NEW_DARK_GOLD}',   # Pressed/active — the accent itself")
    ok(f'light tints in identity table -> {NEW_LIGHT_HOVER} / {NEW_DARK_GOLD}')

    # -- 7c. The contrast table. Generated, not transcribed.
    old_table_start = '| Background | Text Color | Contrast Ratio | WCAG |'
    i = ed.text.index(old_table_start)
    j = ed.text.index('\n\n', i)
    ed.text = (
        ed.text[:i]
        + _contrast_table()
        + '\n\n> **Measured, not transcribed.** Every ratio above is computed from '
          'the hex values by `apply_gold_alignment.py` using the WCAG 2.x relative-'
          'luminance formula. The previous version of this table had six of its '
          'seven rows wrong; the seventh read `4.0:1, AA (large text)` for a pair '
          'that measures 2.9976:1, and the light palette was built on it.'
        + ed.text[j:]
    )
    ed.edits += 1
    ok('contrast table regenerated from measurement (7 rows)')

    # -- 7d. "Accent on Background" -- drop the "sufficient contrast" claim.
    acc_start = '| Background | Accent | Result |'
    i = ed.text.index(acc_start)
    j = ed.text.index('\n\n', i)
    ed.text = ed.text[:i] + _accent_table() + ed.text[j:]
    ed.edits += 1
    ok('accent table regenerated; "sufficient contrast" claim removed')

    # -- 7e. Every remaining reference to the retired value.
    #
    # A file that explains a rule about a value cannot be swept for that value.
    # The paragraph above deliberately names the retired value as history; it is
    # held behind a sentinel so this sweep cannot eat it. (It did, on the first
    # run of this script: "#8c7337 replaced #8c7337".)
    n = ed.replace_all(OLD_DARK_GOLD, NEW_DARK_GOLD)
    ok(f'{n} remaining value reference(s) updated')

    restored = ed.replace_all(RETIRED, OLD_DARK_GOLD)
    ok(f'{restored} historical mention(s) of {OLD_DARK_GOLD} preserved')

    ed.save()


# ---------------------------------------------------------------------------
# Step 8 -- .gitignore / .vs (routing finding, unrelated to gold)
# ---------------------------------------------------------------------------

def step_gitignore(root: Path, dry: bool) -> None:
    step('8', '.gitignore -- .vs/ (routing finding, unrelated to gold)')
    ed = Editor(root / '.gitignore', dry)
    if '.vs/' in ed.text:
        skip('.gitignore')
    else:
        ed.replace_once(
            "# Visual Studio Code\n.vscode/\n*.code-workspace",
            "# Visual Studio Code\n.vscode/\n*.code-workspace\n\n"
            "# Visual Studio\n.vs/\n*.suo\n*.user",
        )
        ed.save()
        ok('.vs/, *.suo, *.user ignored')

    tracked = sh(['git', 'ls-files', '.vs'], check=False, quiet=True).stdout.split()
    if tracked and not dry:
        sh(['git', 'rm', '-r', '--cached', '.vs', '--quiet'], check=False)
        ok(f'{len(tracked)} tracked .vs/ file(s) untracked (kept on disk)')
    elif tracked:
        ok(f'{len(tracked)} tracked .vs/ file(s) would be untracked')
    else:
        skip('.vs/ tracking')


# ---------------------------------------------------------------------------
# Step 9 -- snapshots
# ---------------------------------------------------------------------------

def step_snapshots(root: Path, dry: bool) -> None:
    step('9', 'snapshots -- regenerate (181 gold occurrences will move)')
    ambr = root / 'tests' / '__snapshots__' / 'test_snapshots.ambr'
    before_old = ambr.read_text(encoding='utf-8').count(OLD_DARK_GOLD)
    if dry:
        ok(f'would regenerate; {before_old} occurrence(s) of {OLD_DARK_GOLD} present')
        return
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '--snapshot-update', '-q',
            '--benchmark-disable'], check=False, quiet=True)
    if r.returncode != 0:
        warn('pytest --snapshot-update did not exit clean:')
        print((r.stdout or '')[-1500:])
        die('snapshot regeneration failed -- fix the above, then re-run')
    after = ambr.read_text(encoding='utf-8')
    ok(f'{before_old} x {OLD_DARK_GOLD} -> {after.count(NEW_DARK_GOLD)} x {NEW_DARK_GOLD}')
    if after.count(OLD_DARK_GOLD):
        die(f'{after.count(OLD_DARK_GOLD)} occurrence(s) of the retired value '
            f'survive in the snapshot')


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify(root: Path) -> None:
    step('V', 'verification')

    # A *use* is the value standing as a colour: a quoted literal in Python, or
    # anything at all in a rendered snapshot. A *mention* is prose naming the
    # retired value as history, which is legitimate and must survive. Conflating
    # the two is what makes colour audits sweep documentation into nonsense.
    def classify(value: str) -> tuple[list[str], list[str]]:
        hits = sh(['grep', '-rn', value, '--include=*.py', '--include=*.md',
                   '--include=*.ambr', '.'], check=False, quiet=True).stdout.strip()
        hits = [h for h in hits.splitlines() if 'apply_gold_alignment' not in h]
        uses, mentions = [], []
        for h in hits:
            path, _, body = h.partition(':')
            quoted = (f"'{value}'" in body) or (f'"{value}"' in body)
            (uses if (quoted or path.endswith('.ambr')) else mentions).append(h)
        return uses, mentions

    uses, mentions = classify(OLD_DARK_GOLD)

    if uses:
        say('    retired value still USED as a colour:', RED)
        for line in uses[:20]:
            print(f'      {line}')
        die(f'{len(uses)} live use(s) of {OLD_DARK_GOLD} remain')
    ok(f'0 live uses of {OLD_DARK_GOLD} (0 in .py literals, 0 in snapshots)')
    ok(f'{len(mentions)} historical mention(s) preserved in prose')

    # Same use/mention split for the retired light tints. colors.py names
    # #c4a458 in prose to explain where the new tint's +19 step comes from;
    # that is history, not a palette entry.
    tint_mentions = 0
    for old_tint, label in ((OLD_LIGHT_HOVER, 'hover'), (OLD_LIGHT_PRESSED, 'pressed')):
        t_uses, t_mentions = classify(old_tint)
        tint_mentions += len(t_mentions)
        if t_uses:
            for line in t_uses[:10]:
                print(f'      {line}')
            die(f'{len(t_uses)} live use(s) of the retired light {label} tint '
                f'{old_tint} remain')
    ok(f'0 live uses of the retired light tints {OLD_LIGHT_HOVER} / '
       f'{OLD_LIGHT_PRESSED} ({tint_mentions} mention(s) kept)')

    stray = sh(['grep', '-rn', RETIRED, '--include=*.py', '--include=*.md', '.'],
               check=False, quiet=True).stdout.strip()
    stray = [s for s in stray.splitlines() if 'apply_gold_alignment' not in s]
    if stray:
        for line in stray:
            print(f'      {line}')
        die('sentinel leaked into output')
    ok('no sentinel residue')

    n8 = sh(['grep', '-rno', '#BFd2bc93', '--include=*.py', '--include=*.md', '.'],
            check=False, quiet=True).stdout.strip().splitlines()
    ok(f'{len(n8)} x #BFd2bc93 intact (8-digit form uncorrupted)')

    say('\n    running pytest ...', DIM)
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '-q', '--benchmark-disable'],
           check=False, quiet=True)
    tail = (r.stdout or '').strip().splitlines()[-1:]
    if r.returncode != 0:
        print((r.stdout or '')[-2500:])
        die('pytest failed')
    ok(f'pytest: {tail[0] if tail else "passed"}')

    say('    running unittest ...', DIM)
    r = sh([sys.executable, '-m', 'unittest', 'test_rnv_text_transformer'],
           check=False, quiet=True)
    if r.returncode != 0:
        print((r.stderr or '')[-2500:])
        die('unittest failed')
    line = [l for l in (r.stderr or '').splitlines() if l.startswith('Ran ')]
    ok(f'unittest: {line[0] if line else "passed"} -- OK')


# ---------------------------------------------------------------------------
# Environment (fresh Codespace)
# ---------------------------------------------------------------------------

APT = """libegl1 libxkbcommon0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0
libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1
libxcb-xfixes0 libxcb-xinerama0 libxcb-cursor0 libdbus-1-3 libgl1
libfontconfig1 libnss3 xvfb""".split()


def setup_env() -> None:
    step('0', 'environment (from this repo\'s own .github/workflows/tests.yml)')
    sh(['sudo', 'apt-get', 'update', '-qq'])
    sh(['sudo', 'apt-get', 'install', '-y', '-qq', *APT])
    for req in ('requirements.txt', 'requirements-dev.txt'):
        sh([sys.executable, '-m', 'pip', 'install', '-q', '-r', req], check=False)
    ok('Qt system libraries + requirements-dev.txt installed')


# ---------------------------------------------------------------------------

def preflight(root: Path, dry: bool) -> None:
    step('0', 'pre-flight')

    for rel in EXPECTED_BASE_COUNTS:
        if not (root / rel).exists():
            die(f'{rel} not found -- run this from the repository root')
    ok('repository layout recognised')

    already = (root / 'utils' / 'colors.py').exists()
    if already:
        warn('utils/colors.py already exists -- re-running; steps will no-op')
    else:
        mismatched = []
        for rel, expected in EXPECTED_BASE_COUNTS.items():
            text = (root / rel).read_text(encoding='utf-8').lower()
            n = text.count('d2bc93') + text.count('b19145')
            if n != expected:
                mismatched.append(f'{rel}: expected {expected}, found {n}')
        if mismatched:
            say('    base does not match the note\'s counts:', RED)
            for m in mismatched:
                print(f'      {m}')
            die('refusing to run against an unexpected base')
        ok('all six source/doc files match the note\'s counts exactly')

    if not dry:
        dirty = sh(['git', 'status', '--porcelain'], check=False, quiet=True).stdout.strip()
        if dirty and not already:
            warn(f'working tree has {len(dirty.splitlines())} uncommitted change(s)')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='dry run; change nothing')
    ap.add_argument('--setup-env', action='store_true', help='apt + pip first')
    ap.add_argument('--skip-verify', action='store_true', help='skip test run')
    args = ap.parse_args()

    root = Path.cwd()
    say(f"\n{BOLD}Gold alignment -> rnv-text-transformer{OFF}")
    say(f"{OLD_DARK_GOLD} -> {NEW_DARK_GOLD}   (BRAND_GOLD {BRAND_GOLD} unchanged)", DIM)
    if args.check:
        say('DRY RUN -- nothing will be written', YELLOW)

    if args.setup_env:
        setup_env()

    preflight(root, args.check)
    step_colors_module(root, args.check)
    step_dialog_styles(root, args.check)
    step_utils_init(root, args.check)
    step_drag_drop(root, args.check)
    step_tests(root, args.check)
    step_small_docs(root, args.check)
    step_brand_doc(root, args.check)
    step_gitignore(root, args.check)
    step_snapshots(root, args.check)

    if not args.check and not args.skip_verify:
        verify(root)

    say(f"\n{GREEN}{BOLD}Done.{OFF} Nothing was committed — review with `git diff`.")
    say("\nLight-mode interaction states, for the record:", YELLOW)
    say(f"  accent          {NEW_DARK_GOLD}   black on it {contrast(NEW_DARK_GOLD, '#000000'):.4f}\n"
        f"  accent_hover    {NEW_LIGHT_HOVER}   black on it {contrast(NEW_LIGHT_HOVER, '#000000'):.4f}\n"
        f"  accent_pressed  {NEW_DARK_GOLD}   black on it {contrast(NEW_DARK_GOLD, '#000000'):.4f}\n"
        f"\n"
        f"  Both are derived from BRAND_DARK_GOLD, not written down, so a future\n"
        f"  value change carries them along. Pressed IS the accent because any\n"
        f"  darker shade drops black-on-gold under 4.5 and would force white text.\n"
        f"  Hover keeps the +{LIGHT_HOVER_STEP}/channel step the light palette always used, so a\n"
        f"  hovered row stays distinguishable from a selected one.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
