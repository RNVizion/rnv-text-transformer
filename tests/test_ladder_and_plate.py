"""Three ramp steps become register mirrors, and one hex is split in two.

WHAT THIS PASS DID. rnv-brand registered three values this app had been
carrying as anonymous ramp steps:

    GREY_3A  #3a3a3a  ->  APP_PANEL_HOVER          APP["panel-hover"]  rev 22
    GREY_EE  #eeeeee  ->  APP_HOVER_LIGHT          APP["hover-light"]  rev 23
    GREY_E8  #e8e8e8  ->  GOLD_TEXT_GROUND_FLOOR   module constant     rev 24

THE LATENT FAILURE THIS CLOSES. test_app_owned_values_are_not_register_values
in tests/test_brand_mirror.py fails when something classified app-owned is in
fact a register value. It skips where rnv-brand is not importable, and CI does
not have it -- so all three sat misclassified from the day the register ruled
them, with the suite reporting clean. The proving run is the one with the brand
on the path.

GREY_EE IS SPLIT, NOT RENAMED. Four entries hold #eeeeee and only one plays the
register's role: bg_hover in the light dialog palette. The other three --
diff_html_header_bg in both modes, and line_number_bg -- are STATIC surfaces. A
resting ground is not an interaction state, and wiring all four would claim a
role for three of them on the strength of a shared hex. GREY_EE therefore
survives as a ramp step, and the coincidence is recorded in COINCIDENT beside
GREY_DD / APP["text"], which is the same shape.

WHY #e8e8e8 IS REGISTERED AT ALL, AND WHY THIS FILE'S APP CAUSED IT.
BRAND_DARK_GOLD_DEEP is defined in utils/colors.py as the smallest uniform
per-channel step that clears #e8e8e8: -14 gives 4.5334, -13 gives 4.4675 and
fails. That derivative is published, checked, mirrored and pinned in five
repositories, and its INPUT was app-owned -- so nothing could mirror the
constraint the derivation rests on. The coupling is asserted below, both ways,
mirroring the guard the register now runs at import.
"""
from __future__ import annotations

import ast
import io
import pathlib
import re
import tokenize

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLORS = ROOT / 'utils' / 'colors.py'
STYLES = ROOT / 'utils' / 'dialog_styles.py'

GRID_STEP = 0x11
LADDER_STEP = 0x10
TEXT_FLOOR = 4.5

#: Constant -> the value it must hold. Resolution to rnv-brand is by the
#: convention tests/test_brand_mirror.py already uses: APP_<KEY> -> APP["key"],
#: anything else -> the module attribute of the same name.
NEW = {
    'APP_PANEL_HOVER': '#3a3a3a',
    'APP_HOVER_LIGHT': '#eeeeee',
    'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8',
}

#: The names this pass removes. A rename is only finished when the old name is
#: gone from every file, not merely unused in one.
GONE = ('GREY_3A', 'GREY_E8')

#: What the split leaves behind: the ramp step, and the three static surfaces
#: that keep it. If this list ever empties, the split has collapsed.
STATIC_EE_KEYS = ('diff_html_header_bg', 'line_number_bg')

#: Palette entries and what they must resolve to. Written as VALUES, because
#: this pass renames the constants that hold them -- a check that read the new
#: name's value would be reading the rename twice and proving nothing.
PINNED_ENTRIES = {
    ('DARK', 'bg_hover'): '#3a3a3a',
    ('LIGHT', 'bg_hover'): '#eeeeee',
    ('LIGHT', 'bg_tertiary'): '#e8e8e8',
    ('LIGHT', 'line_number_current_bg'): '#e8e8e8',
}


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _shift(value: str, step: int) -> str:
    parts = [max(0, min(255, int(value.lstrip('#')[i:i + 2], 16) + step))
             for i in (0, 2, 4)]
    return '#%02x%02x%02x' % tuple(parts)


def _palette_names(name: str) -> dict:
    """key -> the NAME each entry is written as, read from the source. The live
    dict gives values; only the source says which constant was used."""
    tree = ast.parse(STYLES.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if getattr(target, 'id', None) != name or not isinstance(node.value, ast.Dict):
            continue
        out = {}
        for k, v in zip(node.value.keys, node.value.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Name):
                out[k.value] = v.id
        return out
    raise AssertionError(f'{name} is not a dict in utils/dialog_styles.py')


# ------------------------------------------------------------- guard the guard

def test_everything_this_file_reads_still_exists():
    for name in NEW:
        assert hasattr(colors, name), f'utils.colors has no {name}'
    assert hasattr(colors, 'GREY_EE'), 'the ramp step survived the split'
    for mode, key in PINNED_ENTRIES:
        live = getattr(DialogStyleManager, mode)
        assert key in live, f'{mode} has no {key!r}'


def test_the_maps_this_file_iterates_are_not_empty():
    """Every sweep below iterates one of these. An empty map passes all."""
    assert len(NEW) == 3 and len(PINNED_ENTRIES) == 4 and STATIC_EE_KEYS


# ------------------------------------------------------------------ the values

def test_the_new_constants_hold_the_registered_values():
    """The local half. Runs everywhere, including where engine.brand is not
    importable -- which is exactly the case that let these three sit
    misclassified for two days."""
    drift = {n: getattr(colors, n) for n, v in NEW.items()
             if getattr(colors, n) != v}
    assert not drift, f'these no longer hold their registered values: {drift}'


def test_the_new_constants_match_rnv_brand():
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local values are doing the work')
    drift = []
    for name in NEW:
        theirs = (brand.APP[name[4:].lower().replace('_', '-')]
                  if name.startswith('APP_') else getattr(brand, name))
        mine = getattr(colors, name)
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: ours {mine}, theirs {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


def test_all_three_are_classified_register():
    for name in NEW:
        assert colors.PROVENANCE.get(name) == 'register', (
            f'{name} is not classified register. The reclassification IS this '
            f'pass; a constant in the register section with an app-ramp label '
            f'is the misclassification it exists to fix.')


def _identifiers(source: str) -> set:
    """Every identifier a file actually USES, plus every string literal.

    Read from the token stream so COMMENTS ARE EXCLUDED. A regex cannot tell a
    use from a mention, and the comment beside APP_PANEL_HOVER says "WAS
    GREY_3A, A RAMP STEP" -- explaining the rename, in the file the rename
    happened in. A word-anchored regex flags that and reports the rename as
    incomplete, which is exactly what it did the first time this ran.
    """
    names = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME:
            names.add(token.string)
        elif token.type == tokenize.STRING:
            names.add(token.string.strip('\'"'))
    return names


def test_the_old_names_are_gone_everywhere():
    """A rename is finished when the old name is absent from every file, not
    merely unused in one. NAME tokens are uses, STRING tokens catch the
    __all__ entries, and comments -- where the rename is explained -- are
    neither."""
    stale = []
    for path in (COLORS, STYLES, ROOT / 'utils' / '__init__.py'):
        used = _identifiers(path.read_text(encoding='utf-8'))
        for name in GONE:
            if name in used:
                stale.append(f'{path.name}: {name}')
    assert not stale, f'renamed constants still used: {stale}'


def test_the_rename_is_still_explained_where_it_happened():
    """Guard the guard, from the other side. The sweep above deliberately
    cannot see comments, so passing it proves nothing about whether the note
    explaining the rename survived -- and that note is the only thing telling
    the next reader why GREY_3A vanished."""
    text = COLORS.read_text(encoding='utf-8')
    for name in GONE:
        assert re.search(rf'WAS {name}\b', text), (
            f'the comment recording that {name} was renamed is gone. The '
            f'token-stream sweep cannot see comments, so nothing else would '
            f'notice it went.')


# --------------------------------------------------------------------- the split

def test_the_ramp_step_survived_and_is_still_app_owned():
    """GREY_EE is NOT the register's. Three static surfaces keep it, and if it
    ever became a mirror those three would start following an interaction
    plate they have nothing to do with."""
    assert colors.GREY_EE == '#eeeeee'
    assert colors.PROVENANCE.get('GREY_EE') == 'app-ramp'


def test_the_static_surfaces_still_use_the_ramp_step():
    """The half of the split that a sweep for 'no old name survives' cannot
    see: if every use had moved to APP_HOVER_LIGHT the rename would look
    complete and the distinction would be gone."""
    names = {}
    for mode in ('DARK', 'LIGHT'):
        names.update(_palette_names(mode))
    using = [k for k in STATIC_EE_KEYS if names.get(k) == 'GREY_EE']
    assert len(using) == len(STATIC_EE_KEYS), (
        f'only {using} still name GREY_EE. The split puts the interaction '
        f'plate on APP_HOVER_LIGHT and leaves the static grounds on the ramp '
        f'step; if the grounds moved too, three surfaces are now claiming to '
        f'be a hover state.')


def test_the_hover_plate_names_the_register_constant():
    """And the other half: the one entry that IS the plate."""
    assert _palette_names('LIGHT').get('bg_hover') == 'APP_HOVER_LIGHT'
    assert _palette_names('DARK').get('bg_hover') == 'APP_PANEL_HOVER'


def test_the_coincidence_is_recorded():
    """A shared hex with two roles has to be named, or the next value check
    reads the sharing as a misclassification and the next person reads it as a
    mistake."""
    mirror = pathlib.Path(__file__).with_name('test_brand_mirror.py')
    text = mirror.read_text(encoding='utf-8')
    assert "'GREY_EE': (" in text, (
        'GREY_EE shares #eeeeee with APP["hover-light"] and is not in '
        'COINCIDENT. The exemption is what keeps the sharing deliberate.')


# ------------------------------------------------------------------ the ladder

def test_the_dark_rung_is_an_exact_step_on_the_ladder():
    """BRAND_BLACK + n * 0x10. This was app-owned on the argument that the
    ladder might not be real."""
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    want = base + 2 * (LADDER_STEP * 0x010101)
    assert int(colors.APP_PANEL_HOVER.lstrip('#'), 16) == want


def test_the_border_is_an_edge_and_not_a_rung():
    """The distinction that made the ladder look incomplete. #333333 is grey(3)
    on the ink grid, which governs inks and edges; it was never a surface."""
    assert colors.APP_BORDER == grey(3)
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}
    assert int(colors.APP_BORDER.lstrip('#'), 16) not in rungs


# --------------------------------------------------- the floor and the plate

def test_the_plate_is_a_step_on_the_ink_grid():
    assert colors.APP_HOVER_LIGHT == grey(14) == '#eeeeee'


def test_the_deep_gold_is_calibrated_against_the_floor():
    """The coupling the register now guards at import, asserted here too
    because this is the file the derivation is written in. One step less must
    FAIL -- a check that only proved the current value clears would pass on any
    darker gold and say nothing about why -14 is the number."""
    gold = colors.BRAND_DARK_GOLD_DEEP
    floor = colors.GOLD_TEXT_GROUND_FLOOR
    assert _contrast(gold, floor) >= TEXT_FLOOR, (
        f'{gold} reads {_contrast(gold, floor):.4f} on {floor}')
    softer = _shift(colors.BRAND_DARK_GOLD, -13)
    assert _contrast(softer, floor) < TEXT_FLOOR, (
        f'one step less than the published -14 still clears the floor at '
        f'{_contrast(softer, floor):.4f}, so -14 is no longer the SMALLEST '
        f'step that clears it and the derivation note is stale.')


def test_the_plate_is_not_the_floor():
    """Both clear the 4.5 floor. Only one clears it by enough to survive the
    gold moving, and the other is the value the gold is calibrated against."""
    gold = colors.BRAND_DARK_GOLD_DEEP
    here = _contrast(gold, colors.APP_HOVER_LIGHT)
    edge = _contrast(gold, colors.GOLD_TEXT_GROUND_FLOOR)
    assert colors.APP_HOVER_LIGHT != colors.GOLD_TEXT_GROUND_FLOOR
    assert here - TEXT_FLOOR >= 0.2, (
        f'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The '
        f'register moved APP["hover-light"] here for margin, not for a pass.')
    assert edge - TEXT_FLOOR < 0.05


# ------------------------------------------------------- nothing moved at all

def test_every_renamed_entry_resolves_to_what_it_resolved_to_before():
    """The values are written down rather than read from the new constants. A
    check that compared an entry against the name it now uses would be reading
    the rename twice and proving nothing about it."""
    wrong = []
    for (mode, key), want in PINNED_ENTRIES.items():
        got = getattr(DialogStyleManager, mode)[key]
        if got != want:
            wrong.append(f'{mode}[{key!r}] is {got}, not {want}')
    assert not wrong, 'a rename landed on the wrong value:\n  ' + '\n  '.join(wrong)
