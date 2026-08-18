"""
Brand mirror and palette-literal guard.

Two invariants:

1. No palette entry is a bare hex literal. Every colour in DialogStyleManager
   .DARK and .LIGHT resolves through a named constant in utils/colors.py.
   Enforced by parsing the source, because a value check cannot see the
   difference between '#333333' and APP_BORDER -- they are the same string at
   runtime and completely different in a diff.

2. The values mirrored from RNVizion/rnv-brand still match the register.
   This app ships standalone and cannot depend on the brand package, so the
   check runs only when that package happens to be importable and skips
   loudly otherwise. A mirror nobody checks is a copy waiting to drift.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

STYLES = pathlib.Path(__file__).resolve().parents[1] / 'utils' / 'dialog_styles.py'

# constant name in utils/colors.py -> how to reach it in engine/brand.py
MIRRORED = {
    'BRAND_GOLD':      ('BRAND_GOLD', None),
    'BRAND_DARK_GOLD': ('BRAND_DARK_GOLD', None),
    'BRAND_BLACK':     ('BRAND_BLACK', None),
    'TRUE_BLACK':      ('TRUE_BLACK', None),
    'WHITE':           ('WHITE', None),
    'APP_CARD':        ('APP', 'card'),
    'APP_BORDER':      ('APP', 'border'),
    'APP_TEXT':        ('APP', 'text'),
    'APP_TEXT_DIM':    ('APP', 'text-dim'),
    'STATUS_SUCCESS':  ('STATUS', 'success'),
    'STATUS_WARNING':  ('STATUS', 'warning'),
    'STATUS_ERROR':    ('STATUS', 'error'),
}


def _palette_nodes():
    """Yield (theme, key, value_node) for both palette dicts."""
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
    """Every colour entry resolves through a named constant."""
    bare = []
    for t, key, node in _palette_nodes():
        if t != theme:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and node.value.startswith('#'):
            bare.append(f'{t}[{key!r}] = {node.value!r}')
    assert not bare, (
        'bare hex literals in the palette -- give them a name in '
        'utils/colors.py:\n  ' + '\n  '.join(bare))


def test_every_palette_colour_is_a_known_constant():
    """The name used must exist in utils/colors.py and hold that value."""
    unknown = []
    for theme, key, node in _palette_nodes():
        if isinstance(node, ast.Name):
            if not hasattr(colors, node.id):
                unknown.append(f'{theme}[{key!r}] -> utils.colors.{node.id} missing')
    assert not unknown, '\n  '.join(unknown)


def test_regex_group_palette_is_named():
    """The capture-group colours live in colors.py, not inline."""
    assert tuple(DialogStyleManager.REGEX_GROUP_COLORS) == \
        tuple(colors.REGEX_GROUP_PALETTE)


def test_mirror_matches_the_register():
    """Mirrored values still equal RNVizion/rnv-brand. Skips if absent."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; mirror unverified this run')
    drift = []
    for local, (attr, key) in MIRRORED.items():
        mine = getattr(colors, local)
        theirs = getattr(brand, attr)
        if key is not None:
            theirs = theirs[key]
        if mine.lower() != theirs.lower():
            drift.append(f'{local}: mirror {mine} vs register {theirs}')
    assert not drift, 'the mirror has drifted from the register:\n  ' + \
        '\n  '.join(drift)
