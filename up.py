#!/usr/bin/env python3
"""
Provenance guard + pytest.ini -> rnv-text-transformer
=====================================================

Two fixes.

1. THE MIRROR TEST'S HARDCODED LIST
   tests/test_brand_mirror.py carries MIRRORED, a hand-written map of twelve
   constants. utils/colors.py holds thirty-eight. Adding a thirteenth and
   forgetting the map entry leaves the test passing while checking twelve of
   thirteen -- stale in the direction that reports clean, which is the exact
   construct this ecosystem keeps finding.

   The fix is declarative provenance, in the file itself:

       PROVENANCE = {'TRUE_BLACK': 'register', 'GREY_3A': 'app-ramp', ...}

   and four checks that make it impossible to sit outside:

     a. completeness, BOTH directions -- every colour constant has an entry,
        every entry names a real constant. A new constant with no entry fails.
     b. register values match rnv-brand, resolved BY NAMING CONVENTION
        (APP_TEXT_DIM -> APP["text-dim"], STATUS_ERROR -> STATUS["error"])
        so there is no second hardcoded map to go stale behind the first.
     c. anything marked 'derived' is actually computed -- asserted against the
        AST, so a literal cannot wear the label.
     d. anything marked app-owned is NOT a register value, catching the
        misclassification in the opposite direction.

   BRAND_DARK_GOLD_DEEP was already outside MIRRORED, correctly, because it is
   derived rather than mirrored -- but nothing in the file said so. Now it does.

2. pytest.ini norecursedirs REPLACED THE DEFAULTS INSTEAD OF EXTENDING THEM
   Which is why every run warns about '.hypothesis'. Pre-existing since
   927d94b, "Initial release: v3.0.3", 2026-05-14. The pytest defaults are
   restored alongside the project's own entries.

    python3 apply_provenance_guard.py            # apply and verify
    python3 apply_provenance_guard.py --check    # dry run

Idempotent. Nothing is committed. No colour value changes.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    '\033[32m', '\033[33m', '\033[31m', '\033[2m', '\033[1m', '\033[0m')


def ok(m):   print(f"{GREEN}    + {m}{OFF}")
def skip(m): print(f"{DIM}    = {m} (already applied){OFF}")
def warn(m): print(f"{YELLOW}    ! {m}{OFF}")
def die(m):  print(f"{RED}\nABORT: {m}{OFF}"); sys.exit(1)
def step(n, m): print(f"\n{BOLD}[{n}]{OFF} {m}")


def sh(cmd, quiet=True):
    return subprocess.run(cmd, check=False, text=True, capture_output=quiet)


REGISTER = ['BRAND_GOLD', 'BRAND_DARK_GOLD', 'TRUE_BLACK', 'WHITE',
            'BRAND_BLACK', 'APP_CARD', 'APP_BORDER', 'APP_TEXT',
            'APP_TEXT_DIM', 'STATUS_SUCCESS', 'STATUS_WARNING', 'STATUS_ERROR']
DERIVED = ['BRAND_DARK_GOLD_DEEP', 'BRAND_DARK_GOLD_PRESSED',
           'GOLD_HOVER', 'GOLD_PRESSED']


def provenance_block(ramp, semantic):
    lines = [
        '',
        '# ==================== PROVENANCE ====================',
        '#',
        '# Where every colour constant in this module comes from. Declarative and',
        '# in the file rather than in the test, because a classification that lives',
        '# only in a test goes stale in the direction that reports clean: add a',
        '# constant, forget the test entry, and the test passes while checking one',
        '# fewer thing than it claims.',
        '#',
        '# tests/test_brand_mirror.py asserts this is complete in BOTH directions,',
        '# that every "register" entry still matches rnv-brand, that every',
        '# "derived" entry is genuinely computed rather than a literal wearing the',
        '# label, and that nothing app-owned is secretly a register value.',
        '#',
        '#   register      mirrored from RNVizion/rnv-brand engine/brand.py',
        '#   derived       computed here from a register value',
        '#   app-ramp      a step on this app\'s neutral ramp; the register',
        '#                 explicitly declines to name these',
        '#   app-semantic  neither brand nor ramp -- diff and regex highlighting',
        '',
        'PROVENANCE: Final[dict[str, str]] = {',
    ]
    for group, names in (('register', REGISTER), ('derived', DERIVED),
                         ('app-ramp', ramp), ('app-semantic', semantic)):
        lines.append(f'    # -- {group}')
        for n in names:
            lines.append(f"    '{n}': '{group}',")
    lines += ['}', '']
    return '\n'.join(lines)


GUARD = '''"""
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
        'colour constants with no provenance entry:\\n  ' + '\\n  '.join(missing)
        + '\\n\\nAdd each to PROVENANCE in utils/colors.py as one of '
        + ', '.join(sorted(VALID_GROUPS)))


def test_provenance_has_no_phantom_entries():
    """And no entry may name a constant that no longer exists."""
    phantom = sorted(set(colors.PROVENANCE) - set(_colour_constants()))
    assert not phantom, (
        'PROVENANCE names constants that are not defined:\\n  '
        + '\\n  '.join(phantom))


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
    assert not drift, 'the mirror has drifted:\\n  ' + '\\n  '.join(drift)


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
    assert not wrong, 'misclassified as app-owned:\\n  ' + '\\n  '.join(wrong)


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
    assert not literal, '\\n  '.join(literal)


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
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \\
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
                      'utils/colors.py:\\n  ' + '\\n  '.join(bare))


def test_every_palette_colour_is_a_known_constant():
    unknown = [f'{t}[{key!r}] -> utils.colors.{n.id} missing'
               for t, key, n in _palette_nodes()
               if isinstance(n, ast.Name) and not hasattr(colors, n.id)]
    assert not unknown, '\\n  '.join(unknown)


def test_regex_group_palette_is_named():
    assert tuple(DialogStyleManager.REGEX_GROUP_COLORS) == \\
        tuple(colors.REGEX_GROUP_PALETTE)
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--skip-tests', action='store_true')
    args = ap.parse_args()
    dry, root = args.check, Path.cwd()

    colors_py = root / 'utils' / 'colors.py'
    guard_py = root / 'tests' / 'test_brand_mirror.py'
    ini = root / 'pytest.ini'

    print(f"\n{BOLD}Provenance guard{OFF}")
    print(f"{DIM}a hardcoded twelve becomes a completeness check over "
          f"thirty-eight{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    step('0', 'pre-flight')
    for f in (colors_py, guard_py, ini):
        if not f.exists():
            die(f'{f} not found -- run from the repository root')
    ctext = colors_py.read_text(encoding='utf-8')
    ok('repository recognised')

    # enumerate what is actually there, rather than trusting a list
    tree = ast.parse(ctext)
    literals, computed = [], []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name == 'PROVENANCE':
                continue
            v = node.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                    and v.value.startswith('#'):
                literals.append(name)
            elif isinstance(v, (ast.Call, ast.Name, ast.Tuple)):
                computed.append(name)
    everything = literals + computed
    ramp = [n for n in literals if n.startswith('GREY_')]
    semantic = [n for n in everything
                if n.startswith(('DIFF_', 'REGEX_'))]
    classified = set(REGISTER) | set(DERIVED) | set(ramp) | set(semantic)
    unclassified = [n for n in everything if n not in classified]
    if unclassified:
        die(f'constants this script cannot classify: {unclassified}\n'
            f'  Add them to REGISTER / DERIVED or adjust the prefixes.')
    ok(f'{len(everything)} colour constants: {len(REGISTER)} register, '
       f'{len(DERIVED)} derived, {len(ramp)} ramp, {len(semantic)} semantic')

    step('1', 'utils/colors.py -- declarative PROVENANCE')
    if 'PROVENANCE' in ctext:
        skip('PROVENANCE')
    else:
        anchor = '\n__all__ = ['
        if ctext.count(anchor) != 1:
            die('cannot locate __all__ in colors.py')
        ctext = ctext.replace(anchor, provenance_block(ramp, semantic) + anchor)
        ctext = ctext.replace("__all__ = [\n", "__all__ = [\n    'PROVENANCE',\n")
        if not dry:
            colors_py.write_text(ctext, encoding='utf-8')
        ok(f'{len(everything)} entries, 4 groups')

    step('2', 'tests/test_brand_mirror.py -- completeness instead of a list')
    if 'PROVENANCE' in guard_py.read_text(encoding='utf-8'):
        skip('guard')
    else:
        if not dry:
            guard_py.write_text(GUARD, encoding='utf-8')
        ok('MIRRORED removed; 10 checks, resolved by naming convention')

    step('3', 'pytest.ini -- extend norecursedirs instead of replacing it')
    itext = ini.read_text(encoding='utf-8')
    if '_darcs' in itext:
        skip('pytest.ini')
    else:
        old = ('norecursedirs =\n'
               '    .git .tox dist build *.egg __pycache__\n'
               '    coverage_html .venv venv env')
        if old not in itext:
            die('pytest.ini norecursedirs is not in the expected form')
        new = ('# EXTENDS pytest\'s defaults rather than replacing them. Setting this\n'
               '# key at all overrides the built-in list, which is why hypothesis\n'
               '# warned about .hypothesis on every run -- the leading ".*" is what\n'
               '# had gone missing.\n'
               'norecursedirs =\n'
               '    *.egg .* _darcs build CVS dist node_modules venv {arch}\n'
               '    .git .tox __pycache__ coverage_html .venv env')
        itext = itext.replace(old, new)
        if not dry:
            ini.write_text(itext, encoding='utf-8')
        ok("pytest defaults restored; '.*' covers .hypothesis")

    if dry:
        print(f"\n{GREEN}{BOLD}Dry run complete.{OFF}")
        return 0

    step('V', 'verification')
    sys.path.insert(0, str(root))
    for m in [m for m in sys.modules if m.startswith('utils')]:
        del sys.modules[m]
    from utils import colors as C
    if len(C.PROVENANCE) != len(everything):
        die(f'PROVENANCE has {len(C.PROVENANCE)}, expected {len(everything)}')
    ok(f'PROVENANCE covers all {len(C.PROVENANCE)} constants')

    if args.skip_tests:
        return 0
    print(f'{DIM}    pytest ...{OFF}')
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '-q', '--benchmark-disable'])
    out = r.stdout or ''
    if r.returncode != 0:
        print(out[-2500:]); die('pytest failed')
    tail = out.strip().splitlines()[-1]
    ok(f'pytest: {tail}')
    if 'warning' in tail:
        warn('a warning remains — check it is not the .hypothesis one')
    else:
        ok('no warnings')

    print(f'{DIM}    unittest ...{OFF}')
    r = sh([sys.executable, '-m', 'unittest', 'test_rnv_text_transformer'])
    if r.returncode != 0:
        print((r.stderr or '')[-2000:]); die('unittest failed')
    ok('unittest: OK')

    print(f"\n{GREEN}{BOLD}Done.{OFF} No colour value changed. Nothing committed.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
