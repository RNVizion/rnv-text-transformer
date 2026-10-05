"""
Every registered value in the palettes spelled as a NAME.

RNV-REGISTER-WIRING-GUARD, 2026-09-30. The picker, the mixer, the palette
manager and the icon builder each carry this test. This app never had it:
its palettes were wired to utils/colors.py before the fleet's wiring rounds,
and the register correction of 2026-09-07 (test_tt_register.py) covered two
light values only. Ruled 2026-09-30 that this app gets the same guard.

NOTHING MOVED. Both palettes already pass: every entry is a name, or a
with_alpha() of a name. This holds that in place.

THE POINT OF IT. A literal cannot follow its base. APP["text"] moved on
2026-08-28 and an app that had written the value down would have kept the
old one silently. Every registered value in the palettes is a name, so the
next register move carries.

WHAT IS DIFFERENT HERE. This app has two palettes, DARK and LIGHT, both class
attributes of DialogStyleManager; image mode reads DARK. Both were wired at
the same time, so both halves are swept for literals, and the light allowlist
is what the light palette names today, every entry of which has been through
a ruling (the light wiring, the gold rounds, the 2026-09-07 correction).
Eight entries in each palette are with_alpha(NAME, ALPHA) calls, so the
sweep looks inside a value, not only at it.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'utils/dialog_styles.py'

#: The register, as this app mirrors it: every name utils/colors.py classes
#: as 'register' in PROVENANCE, with the value it held when this was written.
#: Value-keyed, because a literal is found by its value: any entry holding one
#: of these must name it.
REGISTERED = {
    'BRAND_GOLD': '#d2bc93', 'BRAND_DARK_GOLD': '#8c7337',
    'TRUE_BLACK': '#000000', 'WHITE': '#ffffff',
    'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333',
    'APP_TEXT': '#dddddd', 'APP_TEXT_DIM': '#aaaaaa', 'APP_PANEL_HOVER': '#3a3a3a',
    'APP_HOVER_LIGHT': '#eeeeee', 'APP_SURFACE_LIGHT_3': '#f5f5f5',
    'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8',
    # RNV-NAMED-AND-USED, 2026-10-04: the three status fills stood here. The
    # application carried them unread, and no longer does.
    'STATUS_SUCCESS_TEXT': '#ad85a3', 'STATUS_WARNING_TEXT': '#bc8752',
    'STATUS_ERROR_TEXT': '#dd6f77',
    'STATUS_SUCCESS_TEXT_LIGHT': '#825d79', 'STATUS_WARNING_TEXT_LIGHT': '#8e5e2b',
    'STATUS_ERROR_TEXT_LIGHT': '#ae4650',
}

DARK_DICTS = ('DARK',)
LIGHT_DICTS = ('LIGHT',)

#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a
#: per-mode difference gets checked against the other mode's value and passes.
PALETTES = {'DARK': DialogStyleManager.DARK, 'LIGHT': DialogStyleManager.LIGHT}

#: The register's dark surface ladder and ink. The dark palette must name
#: every one of these: a sweep that finds no literal because the palette
#: stopped referencing the register would pass for the wrong reason.
DARK_LADDER = ('TRUE_BLACK', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER', 'APP_PANEL_HOVER', 'APP_TEXT')


def _dicts(names):
    tree = ast.parse(SRC.read_text(encoding='utf-8-sig'))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = getattr(target, 'id', None)
            if name in names and isinstance(node.value, ast.Dict):
                out[name] = node.value
    missing = set(names) - set(out)
    assert not missing, f'these palettes are no longer dict literals: {missing}'
    return out


def _names_in(value):
    """Every NAME inside a palette value: the value itself, or the arguments
    of a call such as with_alpha(NAME, ALPHA)."""
    return {n.id for n in ast.walk(value) if isinstance(n, ast.Name)}


def _strings_in(value):
    """Every string literal inside a palette value, however deep."""
    return [n.value for n in ast.walk(value)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


# ------------------------------------------------------------- guard the guard

def test_the_palettes_this_file_reads_still_exist():
    """Every assertion below walks these. If one is renamed or stops being a
    dict literal, this fails loudly instead of the rest passing over nothing."""
    assert _dicts(DARK_DICTS)
    assert _dicts(LIGHT_DICTS)


def test_the_register_map_is_not_empty():
    """A sweep with nothing to look for passes forever. The map is every name
    PROVENANCE classes as the register's, at the value the module holds."""
    assert len(REGISTERED) >= 4
    for name, value in REGISTERED.items():
        assert getattr(colors, name) == value, (
            f'{name} is {getattr(colors, name)}, not {value} -- the map this '
            f'file sweeps for has gone stale against the constants')
    registered = {n for n, kind in colors.PROVENANCE.items() if kind == 'register'}
    assert set(REGISTERED) == registered, (
        f'PROVENANCE classes {sorted(registered - set(REGISTERED))} as the register\'s '
        f'and this map does not; {sorted(set(REGISTERED) - registered)} the other way')


# ------------------------------------------------------------ the substitution

@pytest.mark.parametrize('half', ['dark', 'light'])
def test_no_registered_value_is_spelled_as_a_literal(half):
    """The completeness half. A literal cannot follow its base, so there must
    not be one -- at the top of an entry or inside a with_alpha() call."""
    by_value = {v: k for k, v in REGISTERED.items()}
    literals = []
    for dict_name, node in _dicts(DARK_DICTS if half == 'dark' else LIGHT_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if not isinstance(key, ast.Constant):
                continue
            for s in _strings_in(value):
                if s.lower() in by_value:
                    literals.append(f'{dict_name}[{key.value!r}] holds {s} '
                                    f'(should read {by_value[s.lower()]})')
    assert not literals, (
        f'registered values written as literals in the {half} palette:\n  '
        + '\n  '.join(literals))


def test_every_dark_entry_that_names_a_constant_resolves_to_the_register():
    """The other half. A name is only worth having if it holds the right
    value. An entry that is a with_alpha() of a name is checked on the name."""
    wrong = []
    for dict_name, node in _dicts(DARK_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Name) and value.id in REGISTERED:
                actual = PALETTES[dict_name].get(key.value)
                if actual != REGISTERED[value.id]:
                    wrong.append(f'{dict_name}[{key.value!r}] -> {value.id} '
                                 f'resolves to {actual}')
    assert not wrong, 'names resolving wrongly:\n  ' + '\n  '.join(wrong)


def test_the_dark_palette_names_the_register_s_ladder():
    """Guard the guard, again. If the palette stopped referencing the register
    entirely, the sweep above would find no literals and pass -- for the wrong
    reason. The register's dark surfaces and ink are anchored by name, not by
    a count that fails when things get better."""
    used = set()
    for node in _dicts(DARK_DICTS).values():
        for value in node.values:
            used |= _names_in(value) & set(REGISTERED)
    missing = set(DARK_LADDER) - used
    assert not missing, (
        f'the dark palette no longer names {sorted(missing)} of the register\'s '
        f'ladder; it names {sorted(used)}')


# --------------------------------------------------------------- the light half

#: What the light palette may name from the register. Every entry has been
#: through a ruling: the light surface #f5f5f5 and the light hover #eeeeee
#: (rnv-brand rev 23 and 27, the 2026-09-07 correction), light ink and edges
#: (TRUE_BLACK, APP_BORDER), the dark gold and the ground it is held to
#: (BRAND_DARK_GOLD, GOLD_TEXT_GROUND_FLOOR, the gold rounds), the light
#: status inks, WHITE, APP_TEXT_DIM and the one BRAND_BLACK the light list
#: hover paints. A later pass extends this ON PURPOSE, in the commit that
#: wires the value.
LIGHT_RULED = (
    'APP_BORDER', 'APP_HOVER_LIGHT', 'APP_SURFACE_LIGHT_3', 'APP_TEXT_DIM',
    'BRAND_BLACK', 'BRAND_DARK_GOLD', 'GOLD_TEXT_GROUND_FLOOR',
    'STATUS_ERROR_TEXT_LIGHT', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_WARNING_TEXT_LIGHT',
    'TRUE_BLACK', 'WHITE',
)


def test_the_light_palette_references_only_what_the_register_has_ruled():
    """An allowlist, not a prohibition: the light palette names the register,
    and each name it uses is one a ruling put there. A new one is added to
    LIGHT_RULED in the same commit that wires it, or it is not wired."""
    named = []
    for dict_name, node in _dicts(LIGHT_DICTS).items():
        for key, value in zip(node.keys, node.values):
            for name in sorted(_names_in(value) & set(REGISTERED)):
                if name not in LIGHT_RULED:
                    named.append(f'{dict_name}[{key.value!r}] -> {name}')
    assert not named, (
        'the light palette references register values that are not ruled '
        'for light:\n  ' + '\n  '.join(named)
        + '\n\nAdd the name to LIGHT_RULED in the same commit that wires it, '
          'or do not wire it.')


def test_the_ruled_light_values_are_actually_wired():
    """The allowlist permits; this requires. An allowlist entry nothing uses is
    a licence with no subject -- the same shape as a dead exemption."""
    used = set()
    for node in _dicts(LIGHT_DICTS).values():
        for value in node.values:
            used |= _names_in(value) & set(LIGHT_RULED)
    assert used == set(LIGHT_RULED), (
        f'LIGHT_RULED lists {sorted(set(LIGHT_RULED) - used)} that the light '
        f'palette does not use')


def test_every_light_entry_that_names_a_constant_resolves_to_the_register():
    """The light half of the resolution check, since both halves are wired."""
    wrong = []
    for dict_name, node in _dicts(LIGHT_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Name) and value.id in REGISTERED:
                actual = PALETTES[dict_name].get(key.value)
                if actual != REGISTERED[value.id]:
                    wrong.append(f'{dict_name}[{key.value!r}] -> {value.id} '
                                 f'resolves to {actual}')
    assert not wrong, 'names resolving wrongly:\n  ' + '\n  '.join(wrong)
