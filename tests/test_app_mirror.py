"""
The ink moves, the light surface stays behind, and the golds finish their
rename.

THE FIND THAT SHAPED THIS PASS. APP_TEXT was #e0e0e0 and this app spelled SIX
palette entries with it -- five in dark, and ONE IN LIGHT:

    utils/dialog_styles.py:273    'scrollbar_bg': APP_TEXT,      <- light

That is #e0e0e0's other half wearing the ink's name. The light scrollbar
track is a SURFACE, and the published grid governs inks and edges and
deliberately not surfaces. Moving APP_TEXT with the light entry still pointing
at it would have dragged a surface onto the ink grid and quietly changed a
light-mode track that rnv-color-picker and rnv-icon-builder both keep at
#e0e0e0.

So the value split before it moved: APP_TEXT went to grey(13) and the light
track got GREY_E0, named by its byte like every other step in this app's ramp.

The other four apps show the same split as two DIFFERENT keys holding the same
hex. Here it was one name holding two roles, which is harder to see and was
found only by checking which side of the light palette boundary each use sat
on.

TWO GUARDS, NOT ONE. test_brand_mirror.py guards the register with
importorskip('engine.brand'), so where rnv-brand is not importable it reports
clean and drift hides. APP_TEXT is pinned locally here as well.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLORS = ROOT / 'utils' / 'colors.py'
STYLES = ROOT / 'utils' / 'dialog_styles.py'

GRID_STEP = 0x11

DARK = DialogStyleManager.get_colors(True)
LIGHT = DialogStyleManager.get_colors(False)

#: Dark-mode entries that carry the ink.
INK_KEYS = ('text', 'button_text', 'input_text', 'label_text', 'text_color')

#: The golds that finished their rename in this pass. Upstream settled on the
#: BRAND_ prefix in rnv-brand@faf1fd6; four of the five apps already used it.
RENAMED_GOLDS = ('BRAND_GOLD_HOVER', 'BRAND_GOLD_PRESSED')


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


# ------------------------------------------------------------- guard the guard

def test_the_keys_this_file_reads_still_exist():
    for key in INK_KEYS:
        assert key in DARK, f'the dark palette has no {key}'
    assert 'scrollbar_bg' in LIGHT
    for name in ('APP_TEXT', 'GREY_E0', 'TRUE_BLACK') + RENAMED_GOLDS:
        assert hasattr(colors, name), f'utils.colors has no {name}'


# ------------------------------------------------------------------- the value

def test_the_ink_is_a_step_on_the_grid():
    assert colors.APP_TEXT == grey(13) == '#dddddd', (
        f'APP_TEXT is {colors.APP_TEXT}, not grey(13).')


def test_the_local_pin_holds_when_the_brand_is_absent():
    """test_brand_mirror.py checks APP_TEXT against engine.brand and SKIPS when
    rnv-brand is not importable. This is the half that always runs."""
    assert colors.APP_TEXT == '#dddddd', (
        'APP_TEXT no longer holds the registered value. If the brand moved, '
        'update this pin in the same commit that updates utils/colors.py.')


def test_every_dark_ink_entry_carries_the_constant():
    for key in INK_KEYS:
        assert DARK[key] == colors.APP_TEXT, f'dark {key!r} is {DARK[key]}'


def test_the_light_ink_is_true_black():
    """Primary text is one role with two mode values: dark is a grey on the
    grid, light is TRUE_BLACK."""
    assert LIGHT['text'] == colors.TRUE_BLACK == '#000000'


# ------------------------------------------------------- the half that stayed

def test_the_light_scrollbar_track_did_not_follow_the_ink():
    """The whole reason this pass split a constant. #e0e0e0 was doing two
    jobs under one name; the surface half stays exactly where it was."""
    assert LIGHT['scrollbar_bg'] == colors.GREY_E0 == '#e0e0e0', (
        f'the light scrollbar track is {LIGHT["scrollbar_bg"]}. It is a '
        f'SURFACE -- the ink grid does not govern it, and picker and '
        f'icon-builder both keep this track at #e0e0e0.')


def test_the_light_track_no_longer_reads_the_ink_constant():
    """Spelling, not just value. If it points at APP_TEXT again it will follow
    the next ink move silently, which is what this pass existed to stop."""
    source = STYLES.read_text(encoding='utf-8')
    assert "'scrollbar_bg': APP_TEXT," not in source, (
        'the light scrollbar track reads APP_TEXT again')
    assert "'scrollbar_bg': GREY_E0," in source


def test_no_dark_entry_accidentally_took_the_surface_step():
    """The mirror of the test above. GREY_E0 belongs to the light track and
    nothing in dark should have picked it up."""
    strays = [k for k, v in DARK.items() if v == colors.GREY_E0]
    assert not strays, f'dark entries now carrying the light surface: {strays}'


# ------------------------------------------------------------------ provenance

def test_the_new_step_is_classified():
    assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp', (
        'GREY_E0 has no provenance entry, or the wrong one. It is a ramp step, '
        'not a register value -- #e0e0e0 is no longer what the brand holds.')


def test_the_ramp_is_still_ordered_by_byte():
    """This app names ramp steps by their byte so the ramp reads in order.
    GREY_E0 has to sit where its value says, not where it was appended."""
    names = re.findall(r'^(GREY_[0-9A-F]{2}): Final',
                       COLORS.read_text(encoding='utf-8'), re.M)
    values = [int(n[5:], 16) for n in names]
    assert values == sorted(values), (
        f'the ramp is out of order: {names}')


# ---------------------------------------------------------------- the renames

@pytest.mark.parametrize('name', RENAMED_GOLDS)
def test_the_golds_carry_the_brand_prefix(name):
    assert hasattr(colors, name)
    assert name in colors.PROVENANCE, f'{name} has no provenance entry'


def test_no_bare_gold_name_survives():
    """Anchored so BRAND_DARK_GOLD_PRESSED does not count as a bare
    GOLD_PRESSED -- the substring trap that would have renamed it to
    BRAND_DARK_BRAND_GOLD_PRESSED."""
    stale = []
    for path in (COLORS, STYLES, ROOT / 'utils' / '__init__.py'):
        text = path.read_text(encoding='utf-8')
        for bare in ('GOLD_HOVER', 'GOLD_PRESSED'):
            for match in re.finditer(rf'(?<![A-Z_]){bare}\b', text):
                line = text[:match.start()].count('\n') + 1
                stale.append(f'{path.name}:{line}')
    assert not stale, (
        'the unprefixed gold names survive at: ' + ', '.join(stale))


def test_the_renamed_golds_are_still_derived_not_restated():
    """A rename must not turn a derivative into a literal."""
    source = COLORS.read_text(encoding='utf-8')
    assert re.search(r'BRAND_GOLD_HOVER: Final\[str\] = lighten\(', source), (
        'BRAND_GOLD_HOVER is no longer computed from its base')
    assert colors.BRAND_GOLD_HOVER == colors.lighten(colors.BRAND_GOLD, 13)
    assert colors.BRAND_GOLD_PRESSED == colors.BRAND_GOLD


# ---------------------------------------------------------------- what it costs

def _luminance(value: str) -> float:
    ch = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():
    grounds = ('#000000', '#1a1a1a', '#2a2a2a', '#333333', '#3a3a3a', '#444444')
    worst = min((_contrast(colors.APP_TEXT, g), g) for g in grounds)
    assert worst[0] >= 4.5, (
        f'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor')
