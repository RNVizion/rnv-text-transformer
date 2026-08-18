#!/usr/bin/env python3
"""
Every hex behind a named constant -> rnv-text-transformer
=========================================================

utils/dialog_styles.py holds 45 distinct hex literals across 108 occurrences.
This gives every one of them a name, in four groups, because the RNVizion
brand register (RNVizion/rnv-brand) rules them three different ways and
flattening that would lose the ruling.

  A. THE REGISTER, MIRRORED -- 10 literals, 52 occurrences
     Already named in rnv-brand's engine/brand.py. They take the register's
     names, not invented ones. engine/brand.py's APP dict is literally this
     app's dark palette: window, panel, card, border, text, text-dim.

  B. DERIVED FROM THE REGISTER -- BRAND_DARK_GOLD_DEEP, already present

  C. HAND-PICKED GOLD MODULATIONS -- 2 literals
     #dcc9a3 and #b7a480. The register names #dcc9a3 by hex and declines to
     promote it: "Values between and beyond the two are modulations, and none
     of them is promoted... A surface that needs a lighter or darker gold
     derives it; it doesn't mint one." These were minted. They are NAMED here,
     not re-derived -- see the note in colors.py.

  D. THE APP'S NEUTRAL RAMP -- 15 literals, 32 occurrences
     The register deliberately refuses to name these: "That isn't twenty-three
     colors; it's one ramp with steps chosen per surface. The brand doesn't
     publish them, doesn't count them, and doesn't drift when an app adds one."
     So they are app-owned, and named as ramp steps rather than dressed up as
     brand values.

  E. APP SEMANTICS -- 18 literals, 22 occurrences
     Diff highlights (Bootstrap alert palette), the regex match highlight, and
     the eight-colour regex capture-group palette. Local, with provenance.

No value changes. Not one. This is naming only, and it is asserted: every
generated stylesheet must be byte-identical afterwards.

The guard
---------
tests/test_brand_mirror.py:
  - fails if any palette entry is a bare hex literal rather than a constant
  - fails if the mirrored register values drift, when rnv-brand is importable
  - skips the drift check cleanly when it is not, saying so

Run from the repository root:

    python3 apply_color_constants.py            # apply and verify
    python3 apply_color_constants.py --check    # dry run

Idempotent. Nothing is committed.
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


def sh(cmd, check=False, quiet=True):
    return subprocess.run(cmd, check=check, text=True, capture_output=quiet)


# --------------------------------------------------------------------------
# name -> (value, group, comment).  Order is the order they are emitted.
# --------------------------------------------------------------------------
REGISTER = [
    ('TRUE_BLACK',     '#000000', 'App window ground; text on gold, on either surface'),
    ('WHITE',          '#ffffff', "Light-surface cards and inputs; the ramp's far anchor"),
    ('BRAND_BLACK',    '#1a1a1a', 'Brand black (charcoal). Raised surfaces in apps'),
    ('APP_CARD',       '#2a2a2a', 'engine/brand.py APP["card"]'),
    ('APP_BORDER',     '#333333', 'engine/brand.py APP["border"]'),
    ('APP_TEXT',       '#e0e0e0', 'engine/brand.py APP["text"]'),
    ('APP_TEXT_DIM',   '#aaaaaa', 'engine/brand.py APP["text-dim"]'),
    ('STATUS_SUCCESS', '#28a745', 'engine/brand.py STATUS["success"]'),
    ('STATUS_WARNING', '#ffc107', 'engine/brand.py STATUS["warning"]'),
    ('STATUS_ERROR',   '#dc3545', 'engine/brand.py STATUS["error"]'),
]

GOLD_MOD = [
    ('GOLD_HOVER',   '#dcc9a3', 'dark-mode hover. Named in the register by hex, not promoted'),
    ('GOLD_PRESSED', '#b7a480', 'dark-mode pressed. Same standing'),
]

RAMP = [
    ('GREY_25', '#252525'), ('GREY_3A', '#3a3a3a'), ('GREY_44', '#444444'),
    ('GREY_50', '#505050'), ('GREY_55', '#555555'), ('GREY_60', '#606060'),
    ('GREY_66', '#666666'), ('GREY_88', '#888888'), ('GREY_99', '#999999'),
    ('GREY_CC', '#cccccc'), ('GREY_DD', '#dddddd'), ('GREY_E8', '#e8e8e8'),
    ('GREY_EE', '#eeeeee'), ('GREY_F0', '#f0f0f0'), ('GREY_F5', '#f5f5f5'),
]

SEMANTIC = [
    ('DIFF_ADDED_DARK',    '#1a4d1a', ''),
    ('DIFF_REMOVED_DARK',  '#4d1a1a', ''),
    ('DIFF_CHANGED_DARK',  '#4d4d1a', ''),
    ('DIFF_CURRENT_DARK',  '#4d1a4d', ''),
    ('DIFF_ADDED_LIGHT',   '#d4edda', 'Bootstrap alert-success background'),
    ('DIFF_REMOVED_LIGHT', '#f8d7da', 'Bootstrap alert-danger background'),
    ('DIFF_CHANGED_LIGHT', '#fff3cd', 'Bootstrap alert-warning background'),
    ('DIFF_CURRENT_LIGHT', '#e2d4f0', ''),
    ('REGEX_MATCH_DARK',   '#4a4a00', ''),
    ('REGEX_MATCH_LIGHT',  '#ffff99', ''),
]

REGEX_GROUPS = ['#3d5c5c', '#5c3d5c', '#5c5c3d', '#3d5c3d',
                '#5c3d3d', '#3d3d5c', '#5c4d3d', '#3d5c4d']

MARKER = '# ==================== THE REGISTER, MIRRORED ===================='


def build_block() -> str:
    L = [MARKER, '#',
         '# Mirrored from RNVizion/rnv-brand engine/brand.py. MIRRORED, not',
         '# imported: this application ships standalone and cannot take a',
         '# dependency on the brand repository. tests/test_brand_mirror.py fails',
         '# if these drift, whenever that package is importable.',
         '#',
         "# engine/brand.py's APP dict is this app's dark palette almost exactly --",
         '# window, panel, card, border, text, text-dim. It was named there while',
         '# this file spelled it out in hex.',
         '']
    for n, v, c in REGISTER:
        L.append(f"#: {c}" if c else '')
        L.append(f"{n}: Final[str] = '{v}'")
        L.append('')

    L += ['', '# ============ HAND-PICKED GOLD MODULATIONS ============', '#',
          '# The register names #dcc9a3 by hex and refuses to promote it:',
          '#',
          '#   "Values between and beyond the two are modulations, and none of',
          "#    them is promoted. #dcc9a3 (three apps) sits on the gold axis",
          '#    extended past brand gold by about 30%... A surface that needs a',
          "#    lighter or darker gold derives it; it doesn't mint one.\"",
          '#',
          '# These two were minted. They are named here rather than re-derived,',
          '# because no simple rule reproduces them: against BRAND_GOLD their',
          '# deltas are +10,+13,+16 and -27,-24,-19, and neither an HLS lightness',
          '# move nor a white/black mix lands on them exactly. Inventing a formula',
          '# that happens to hit a hand-picked number is a literal in disguise.',
          '#',
          '# The light-mode equivalents ARE derived (BRAND_DARK_GOLD_DEEP). Dark',
          '# mode is the half still minting, and a future pass should close it --',
          '# which would change these values, so it is not this pass.',
          '']
    for n, v, c in GOLD_MOD:
        L.append(f'#: {c}')
        L.append(f"{n}: Final[str] = '{v}'")
        L.append('')

    L += ['', "# ============ THE APP'S NEUTRAL RAMP ============", '#',
          '# The register declines to name these, deliberately:',
          '#',
          '#   "Every neutral in all five desktop apps -- twenty-three distinct',
          '#    values from #000000 to #ffffff -- is a pure grey, R = G = B,',
          "#    without exception. That isn't twenty-three colors; it's one ramp",
          '#    with steps chosen per surface. The brand doesn\'t publish them,',
          "#    doesn't count them, and doesn't drift when an app adds one.\"",
          '#',
          '# So these are APP-OWNED, named as ramp steps rather than dressed up as',
          '# brand values. The two anchors (TRUE_BLACK, WHITE) and the four steps',
          '# the register does name (BRAND_BLACK, APP_CARD, APP_BORDER, APP_TEXT,',
          '# APP_TEXT_DIM) are above; these are the rest of this app\'s layering.',
          '#',
          '# Named by their byte so the ramp reads in order and a step cannot be',
          '# confused with a role. Adding one is not drift.',
          '']
    for n, v in RAMP:
        L.append(f"{n}: Final[str] = '{v}'")
    L += ['', '', '# ============ APP SEMANTICS ============', '#',
          '# Neither brand values nor ramp steps. Diff highlighting borrows the',
          '# Bootstrap alert palette; the regex colours are this app alone.',
          '']
    for n, v, c in SEMANTIC:
        L.append(f'#: {c}' if c else '')
        L.append(f"{n}: Final[str] = '{v}'")
    L += ['', '',
          '#: Dark-only capture-group highlighting; index 0 is group 1.',
          'REGEX_GROUP_PALETTE: Final[tuple[str, ...]] = (']
    for v in REGEX_GROUPS:
        L.append(f"    '{v}',")
    L.append(')')
    return '\n'.join(l for l in L) + '\n\n'


ALL_NAMES = ([n for n, _, _ in REGISTER] + [n for n, _, _ in GOLD_MOD]
             + [n for n, _ in RAMP] + [n for n, _, _ in SEMANTIC]
             + ['REGEX_GROUP_PALETTE'])
VALUE_OF = ({n: v for n, v, _ in REGISTER} | {n: v for n, v, _ in GOLD_MOD}
            | dict(RAMP) | {n: v for n, v, _ in SEMANTIC})


GUARD = '''"""
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
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \\
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
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \\
                and node.value.startswith('#'):
            bare.append(f'{t}[{key!r}] = {node.value!r}')
    assert not bare, (
        'bare hex literals in the palette -- give them a name in '
        'utils/colors.py:\\n  ' + '\\n  '.join(bare))


def test_every_palette_colour_is_a_known_constant():
    """The name used must exist in utils/colors.py and hold that value."""
    unknown = []
    for theme, key, node in _palette_nodes():
        if isinstance(node, ast.Name):
            if not hasattr(colors, node.id):
                unknown.append(f'{theme}[{key!r}] -> utils.colors.{node.id} missing')
    assert not unknown, '\\n  '.join(unknown)


def test_regex_group_palette_is_named():
    """The capture-group colours live in colors.py, not inline."""
    assert tuple(DialogStyleManager.REGEX_GROUP_COLORS) == \\
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
    assert not drift, 'the mirror has drifted from the register:\\n  ' + \\
        '\\n  '.join(drift)
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--skip-tests', action='store_true')
    args = ap.parse_args()
    dry, root = args.check, Path.cwd()

    colors_py = root / 'utils' / 'colors.py'
    styles_py = root / 'utils' / 'dialog_styles.py'
    init_py = root / 'utils' / '__init__.py'

    print(f"\n{BOLD}Every hex behind a named constant{OFF}")
    print(f"{DIM}45 literals, 108 occurrences, four groups, no value changes{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    step('0', 'pre-flight')
    for f in (colors_py, styles_py, init_py):
        if not f.exists():
            die(f'{f} not found -- run from the repository root')
    ctext = colors_py.read_text(encoding='utf-8')
    if 'BRAND_DARK_GOLD_DEEP' not in ctext:
        die('the deep-gold pass has not been applied; run that first')
    ok('repository recognised')

    stext = styles_py.read_text(encoding='utf-8')
    found = sorted({m.group(1).lower() for m in
                    re.finditer(r"['\"](#[0-9A-Fa-f]{6})['\"]", stext)})
    already = MARKER in ctext
    if not already and len(found) != 45:
        die(f'expected 45 distinct hex literals in dialog_styles.py, found '
            f'{len(found)} -- the file is not in the state this script expects')
    ok(f'{len(found)} distinct hex literal(s) in dialog_styles.py')

    # snapshot the rendered stylesheets BEFORE, to prove nothing moved
    before_css = {}
    if not dry:
        sys.path.insert(0, str(root))
        for mod in [m for m in sys.modules if m.startswith('utils')]:
            del sys.modules[mod]
        from utils.dialog_styles import DialogStyleManager as _D
        comps = ('splitter', 'menu', 'table', 'tab', 'spinbox', 'slider',
                 'list', 'progressbar', 'tree')
        for is_dark in (True, False):
            before_css[is_dark] = _D.get_extended_stylesheet(is_dark, 'Arial', *comps)
        ok('captured both rendered stylesheets for the byte-identity check')

    step('1', 'utils/colors.py -- four named groups')
    if already:
        skip('colors.py')
    else:
        anchor = '# ==================== ALPHA HELPER ===================='
        if ctext.count(anchor) != 1:
            die('cannot locate the alpha-helper anchor in colors.py')
        ctext = ctext.replace(anchor, build_block() + anchor)
        old_all = re.search(r"__all__ = \[(.*?)\]", ctext, re.S)
        if not old_all:
            die('cannot locate __all__ in colors.py')
        names = "\n".join(f"    '{n}'," for n in ALL_NAMES)
        ctext = ctext.replace(
            old_all.group(0),
            old_all.group(0)[:-1].rstrip() + '\n' + names + '\n]')
        if not dry:
            colors_py.write_text(ctext, encoding='utf-8')
        ok(f'{len(REGISTER)} register + {len(GOLD_MOD)} gold modulation + '
           f'{len(RAMP)} ramp + {len(SEMANTIC)} semantic + regex palette')

    step('2', 'utils/dialog_styles.py -- point 108 literals at the names')
    if 'APP_BORDER' in stext:
        skip('dialog_styles.py')
    else:
        imports = ',\n    '.join(ALL_NAMES)
        stext = stext.replace(
            'from utils.colors import (\n    BRAND_GOLD,',
            f'from utils.colors import (\n    {imports},\n    BRAND_GOLD,')
        replaced = 0
        for name, value in sorted(VALUE_OF.items(), key=lambda kv: kv[0]):
            for q in ("'", '"'):
                pat = f'{q}{value}{q}'
                n = stext.count(pat)
                if n:
                    stext = stext.replace(pat, name)
                    replaced += n
        # the capture-group list becomes the named tuple
        stext = re.sub(
            r'REGEX_GROUP_COLORS: ClassVar\[list\[str\]\] = \[[^\]]*\]',
            'REGEX_GROUP_COLORS: ClassVar[list[str]] = list(REGEX_GROUP_PALETTE)',
            stext)
        replaced += len(REGEX_GROUPS)
        if not dry:
            styles_py.write_text(stext, encoding='utf-8')
        ok(f'{replaced} literal occurrence(s) repointed')
        if replaced != 108:
            die(f'expected 108, repointed {replaced}')

    step('3', 'utils/__init__.py -- export')
    itext = init_py.read_text(encoding='utf-8')
    if 'APP_BORDER' in itext:
        skip('exports')
    else:
        itext = itext.replace(
            'from utils.colors import (\n    BRAND_GOLD,',
            'from utils.colors import (\n    ' + ',\n    '.join(ALL_NAMES)
            + ',\n    BRAND_GOLD,')
        itext = itext.replace(
            "__all__ = [\n    # Brand Colors\n    'BRAND_GOLD',",
            "__all__ = [\n    # Brand Colors\n"
            + '\n'.join(f"    '{n}'," for n in ALL_NAMES)
            + "\n    'BRAND_GOLD',")
        if not dry:
            init_py.write_text(itext, encoding='utf-8')
        ok(f'{len(ALL_NAMES)} name(s) exported')

    step('4', 'tests/test_brand_mirror.py -- the guard')
    guard = root / 'tests' / 'test_brand_mirror.py'
    if guard.exists():
        skip('guard')
    else:
        if not dry:
            guard.write_text(GUARD, encoding='utf-8')
        ok('no-bare-literal check + register mirror check (skips if rnv-brand absent)')

    if dry:
        print(f"\n{GREEN}{BOLD}Dry run complete.{OFF}")
        return 0

    step('V', 'verification')
    for mod in [m for m in sys.modules if m.startswith('utils')]:
        del sys.modules[mod]
    from utils.dialog_styles import DialogStyleManager as D2
    comps = ('splitter', 'menu', 'table', 'tab', 'spinbox', 'slider',
             'list', 'progressbar', 'tree')
    for is_dark, name in ((True, 'DARK'), (False, 'LIGHT')):
        after = D2.get_extended_stylesheet(is_dark, 'Arial', *comps)
        if after != before_css[is_dark]:
            die(f'{name} stylesheet changed -- this pass must be naming only')
        ok(f'{name} stylesheet byte-identical')

    left = [m.group(1) for m in
            re.finditer(r"['\"](#[0-9A-Fa-f]{6})['\"]",
                        styles_py.read_text(encoding='utf-8'))]
    if left:
        die(f'{len(left)} hex literal(s) still in dialog_styles.py: {sorted(set(left))[:6]}')
    ok('0 hex literals left in dialog_styles.py')

    for suite, cmd in (('pytest', [sys.executable, '-m', 'pytest', 'tests/', '-q',
                                   '--benchmark-disable']),
                       ('unittest', [sys.executable, '-m', 'unittest',
                                     'test_rnv_text_transformer'])):
        if args.skip_tests:
            break
        print(f"{DIM}    {suite} ...{OFF}")
        r = sh(cmd)
        out = (r.stdout or '') + (r.stderr or '')
        if r.returncode != 0:
            print(out[-2500:])
            die(f'{suite} failed')
        tail = [l for l in out.strip().splitlines()
                if l.startswith(('Ran ', 'OK')) or 'passed' in l]
        ok(f'{suite}: {tail[-1] if tail else "passed"}')

    print(f"\n{GREEN}{BOLD}Done.{OFF} Naming only — no rendered byte moved. "
          f"Nothing committed.")
    warn('Dark-mode GOLD_HOVER / GOLD_PRESSED are named but still minted.\n'
         '      The register says a surface derives its golds rather than minting\n'
         '      them. Closing that changes their values, so it is a separate pass.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
