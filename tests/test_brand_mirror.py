"""
Brand mirror, palette-literal and provenance guard.

Three things this file refuses to let happen:

1. A colour appears in the palette as a bare hex literal instead of a name.
2. A mirrored value drifts from RNVizion/rnv-brand.
3. A constant is added to utils/colors.py without saying where it came from.

(3) is the one that matters most, and it is why PROVENANCE lives in colors.py
rather than here. A hand-written list inside a test covers what it covers and
says nothing about what it misses -- it goes stale in the direction that
reports clean. The completeness checks below close that: every colour constant
must have a provenance entry, and every entry must name a real constant.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLES = ROOT / 'utils' / 'dialog_styles.py'
COLORS = ROOT / 'utils' / 'colors.py'

VALID_GROUPS = {'register', 'derived', 'app-ramp', 'app-semantic'}


def _colour_constants() -> dict[str, ast.AST]:
    """Every module-level colour constant in colors.py -> its value node."""
    tree = ast.parse(COLORS.read_text(encoding='utf-8'))
    out = {}
    for node in tree.body:
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        name = node.target.id
        if name == 'PROVENANCE':
            continue
        value = getattr(colors, name, None)
        is_colour = (isinstance(value, str) and value.startswith('#')) or (
            isinstance(value, tuple) and value
            and all(isinstance(v, str) and v.startswith('#') for v in value))
        if is_colour:
            out[name] = node.value
    return out


def _brand_value(brand, name: str):
    """Resolve a mirrored constant in engine/brand.py BY CONVENTION.

    APP_TEXT_DIM  -> APP["text-dim"]
    STATUS_ERROR  -> STATUS["error"]
    anything else -> the module attribute of the same name

    Convention rather than a second hardcoded map, which would go stale behind
    the first one exactly as MIRRORED did.
    """
    for prefix in ('APP', 'STATUS'):
        if name.startswith(prefix + '_'):
            key = name[len(prefix) + 1:].lower().replace('_', '-')
            return getattr(brand, prefix)[key]
    return getattr(brand, name)


# ---------------------------------------------------------------- completeness

def test_provenance_covers_every_constant():
    """No colour constant may sit outside PROVENANCE."""
    missing = sorted(set(_colour_constants()) - set(colors.PROVENANCE))
    assert not missing, (
        'colour constants with no provenance entry:\n  ' + '\n  '.join(missing)
        + '\n\nAdd each to PROVENANCE in utils/colors.py as one of '
        + ', '.join(sorted(VALID_GROUPS)))


def test_provenance_has_no_phantom_entries():
    """And no entry may name a constant that no longer exists."""
    phantom = sorted(set(colors.PROVENANCE) - set(_colour_constants()))
    assert not phantom, (
        'PROVENANCE names constants that are not defined:\n  '
        + '\n  '.join(phantom))


def test_provenance_groups_are_valid():
    bad = {k: v for k, v in colors.PROVENANCE.items() if v not in VALID_GROUPS}
    assert not bad, f'unknown provenance group(s): {bad}'


# ---------------------------------------------------------------- the register

def test_register_values_match_rnv_brand():
    """Every 'register' constant still equals the register. Skips if absent."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; mirror unverified this run')
    drift = []
    for name, group in colors.PROVENANCE.items():
        if group != 'register':
            continue
        mine = getattr(colors, name)
        try:
            theirs = _brand_value(brand, name)
        except (AttributeError, KeyError):
            drift.append(f'{name}: not found in engine/brand.py by convention')
            continue
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: mirror {mine} vs register {theirs}')
    assert not drift, 'the mirror has drifted:\n  ' + '\n  '.join(drift)


def test_app_owned_values_are_not_register_values():
    """Something app-owned that IS a brand value is misclassified."""
    brand = pytest.importorskip(
        'engine.brand', reason='rnv-brand not importable here')
    named = {}
    for attr in ('BRAND_GOLD', 'BRAND_DARK_GOLD', 'BRAND_BLACK',
                 'TRUE_BLACK', 'WHITE', 'WEB_BLACK'):
        named[getattr(brand, attr).lower()] = attr
    for dict_name in ('APP', 'STATUS'):
        for key, value in getattr(brand, dict_name).items():
            if isinstance(value, str) and value.startswith('#'):
                named.setdefault(value.lower(), f'{dict_name}["{key}"]')

    wrong = []
    for name, group in colors.PROVENANCE.items():
        if not group.startswith('app-'):
            continue
        value = getattr(colors, name)
        for v in (value,) if isinstance(value, str) else value:
            if v.lower() in named:
                wrong.append(f'{name} = {v} is {named[v.lower()]} in the register, '
                             f'but marked {group}')
    assert not wrong, 'misclassified as app-owned:\n  ' + '\n  '.join(wrong)


# ------------------------------------------------------------------- derived

def test_derived_constants_are_actually_derived():
    """A literal must not wear the 'derived' label."""
    nodes = _colour_constants()
    literal = []
    for name, group in colors.PROVENANCE.items():
        if group != 'derived':
            continue
        node = nodes.get(name)
        if isinstance(node, ast.Constant):
            literal.append(f'{name} is marked derived but assigned the literal '
                           f'{node.value!r}')
    assert not literal, '\n  '.join(literal)


def test_register_constants_are_literals_not_computed():
    """A mirrored value must be written down, so the mirror can be compared."""
    nodes = _colour_constants()
    computed = [n for n, g in colors.PROVENANCE.items()
                if g == 'register' and not isinstance(nodes.get(n), ast.Constant)]
    assert not computed, (
        'marked register but computed, so nothing mirrors: ' + ', '.join(computed))


# ------------------------------------------------------------------- palette

def _palette_nodes():
    tree = ast.parse(STYLES.read_text(encoding='utf-8'))
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == 'DialogStyleManager')
    for node in cls.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target in ('DARK', 'LIGHT') and isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                yield target, getattr(k, 'value', '?'), v


@pytest.mark.parametrize('theme', ['DARK', 'LIGHT'])
def test_no_bare_hex_in_palette(theme):
    bare = [f'{t}[{key!r}] = {n.value!r}' for t, key, n in _palette_nodes()
            if t == theme and isinstance(n, ast.Constant)
            and isinstance(n.value, str) and n.value.startswith('#')]
    assert not bare, ('bare hex literals in the palette -- give them a name in '
                      'utils/colors.py:\n  ' + '\n  '.join(bare))


def test_every_palette_colour_is_a_known_constant():
    unknown = [f'{t}[{key!r}] -> utils.colors.{n.id} missing'
               for t, key, n in _palette_nodes()
               if isinstance(n, ast.Name) and not hasattr(colors, n.id)]
    assert not unknown, '\n  '.join(unknown)


def test_regex_group_palette_is_named():
    assert tuple(DialogStyleManager.REGEX_GROUP_COLORS) == \
        tuple(colors.REGEX_GROUP_PALETTE)
