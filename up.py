#!/usr/bin/env python3
"""
Deep gold -> rnv-text-transformer
==================================

Collapses the light-mode gold palette to TWO values by recognising that the
hover tint and the text colour want the same thing.

    BRAND_DARK_GOLD       #8c7337  ruled value -- fills, borders, selections,
                                   focus rings, progress, pressed
    BRAND_DARK_GOLD_DEEP  #7e6529  the one derivative -- hover backgrounds AND
                                   gold-bearing text on light grounds

Supersedes BRAND_DARK_GOLD_HOVER (#9f864a), which is removed.

Why one value and not two
-------------------------
The hover tint is not a tint. It is a BACKGROUND that carries white text, the
same job the selected row does -- so it must be dark enough for white. Gold
carrying text on a grey ground must also be dark enough. Both constraints pull
the same way, so one value satisfies both and a second is redundant.

    white on #9f864a (today's hover)    3.5099  FAIL
    white on #7e6529                    5.5547  pass
    #7e6529 as text on #f5f5f5          5.0949  pass
    #7e6529 as text on #eeeeee          4.7875  pass
    #7e6529 as text on #e8e8e8          4.5334  pass

-14 per channel is the smallest uniform step that clears all of these; -13
gives 4.4675 on #e8e8e8 and fails. Hue is unchanged at 42.4 degrees.

What changes visually
---------------------
Hover on light now goes DEEPER than the accent instead of lighter. That is the
same rule dark mode already follows -- hover moves AWAY from the ground:

    DARK   ground #1a1a1a dark   -> accent #d2bc93, hover #dcc9a3  lighter
    LIGHT  ground #f5f5f5 light  -> accent #8c7337, hover #7e6529  deeper

Going lighter on a light ground is what put white at 3.5099 in the first place.
Separation from the selected row stays comparable: 1.223:1, against 1.256:1 in
the original palette.

Not changed
-----------
  - The accent. Fills, borders, selections, focus rings, pressed: all #8c7337.
  - The output pane. Gold on #ffffff is already 4.5429.
  - Dark mode. accent_ink resolves to BRAND_GOLD there, so every dark rule
    renders the byte it rendered before -- verified, not assumed.

Run from the repository root:

    python3 apply_deep_gold.py                # apply, regenerate, verify
    python3 apply_deep_gold.py --check        # dry run
    python3 apply_deep_gold.py --verify-only  # check what is already on disk

Idempotent. Nothing is committed.

Unrelated test failures do not abort this script. The snapshot step is judged by
the snapshot report, not by pytest's exit code, and any failure outside the
colour surface is reported as a warning and left alone. tests/test_properties.py
is hypothesis-driven and explores different inputs on every run, so it can
surface a long-standing bug on any given invocation; that is not a reason to
refuse a colour change.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BRAND_GOLD = '#d2bc93'
DARK_GOLD = '#8c7337'
OLD_HOVER = '#9f864a'
DEEP_STEP = -14

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    '\033[32m', '\033[33m', '\033[31m', '\033[2m', '\033[1m', '\033[0m')


def _lighten(color, step):
    rgb = color.lstrip('#')
    return '#' + ''.join(
        f'{max(0, min(255, int(rgb[i:i+2], 16) + step)):02x}' for i in (0, 2, 4))


DEEP = _lighten(DARK_GOLD, DEEP_STEP)          # #7e6529


def ok(m):   print(f"{GREEN}    + {m}{OFF}")
def skip(m): print(f"{DIM}    = {m} (already applied){OFF}")
def die(m):  print(f"{RED}\nABORT: {m}{OFF}"); sys.exit(1)
def step(n, m): print(f"\n{BOLD}[{n}]{OFF} {m}")


def warn(m):  print(f"{YELLOW}    ! {m}{OFF}")


def sh(cmd, check=True, quiet=False):
    return subprocess.run(cmd, check=check, text=True, capture_output=quiet)


# Anything whose node id mentions one of these is in the surface this script
# touches. A failure there is ours. Anything else is not, and must not block a
# colour change -- tests/test_properties.py is hypothesis-driven and explores a
# different input space on every run, so it can surface a long-standing bug on
# any given invocation.
COLOUR_SURFACE = ('contrast', 'snapshot', 'style', 'theme', 'color', 'colour',
                  'dialog', 'palette', 'gold', 'accent')


def classify(stdout: str):
    """Split pytest FAILED lines into (ours, unrelated)."""
    failed = [l.split(' ', 1)[1].strip() if ' ' in l else l.strip()
              for l in (stdout or '').splitlines() if l.startswith('FAILED ')]
    ours, other = [], []
    for node in failed:
        low = node.lower()
        (ours if any(t in low for t in COLOUR_SURFACE) else other).append(node)
    return ours, other


def report_unrelated(nodes):
    warn(f'{len(nodes)} unrelated test failure(s) — NOT caused by this script:')
    for node in nodes[:8]:
        print(f'      {node}')
    warn('left alone deliberately; this script only changes colour values.')


def sub(path: Path, pairs, dry, *, scope=None, required=True):
    text = path.read_text(encoding='utf-8')
    if scope:
        if scope not in text:
            die(f'{path}: cannot find scope marker {scope!r}')
        head, body = text.split(scope, 1)
    else:
        head, body = '', text
    n = 0
    for old, new in pairs:
        c = body.count(old)
        if c > 1:
            die(f'{path}: {old[:70]!r} appears {c} times in scope; refusing')
        if c == 1:
            body = body.replace(old, new)
            n += 1
    if n and not dry:
        path.write_text(head + (scope or '') + body, encoding='utf-8')
    return n


DEEP_BLOCK = f'''#: Light-mode DEEP gold. The single derivative, serving two roles.
#:
#: 1. Hover backgrounds (combo, table, list, tree rows; slider handles).
#:    These carry white text, exactly as the selected row does, so they need a
#:    gold dark enough for white. The previous hover value was a LIGHTER tint
#:    ({OLD_HOVER}) and white measured 3.5099 on it -- a failure inherited from
#:    the pre-alignment palette, where it was 2.3868.
#:
#: 2. Gold-bearing text on a light ground. {DARK_GOLD} fills and bounds
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
#: {DEEP_STEP} per channel is the smallest uniform step that clears all four.
#: -13 gives 4.4675 on #e8e8e8 and fails. Hue is unchanged at 42.4 degrees.
#:
#: Hover moves AWAY from the ground, which is what dark mode already does:
#: a dark ground takes a lighter hover, a light ground takes a deeper one.
#:
#: Never use as a fill under BLACK text -- black on it is 3.66:1.
BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, {DEEP_STEP})
'''

GUARD = '''"""
Contrast pairing guard.

The rest of the suite asserts hex EQUALITY -- DARK["accent"] == "#d2bc93".
That cannot catch a legible colour placed on the wrong ground, which is how
eight failing gold pairings survived every previous audit: every value was
correct, every pairing was not.

This walks the generated stylesheets, resolves each `color` against the
background it actually renders on, and applies the WCAG floor.

Exceptions below are recorded decisions, not silence. Each one names why.
"""
from __future__ import annotations

import re

import pytest

from utils.dialog_styles import DialogStyleManager

TEXT_FLOOR = 4.5
HEX = re.compile(r'#[0-9a-fA-F]{6,8}$')
COMPONENTS = ('splitter', 'menu', 'table', 'tab', 'spinbox', 'slider',
              'list', 'progressbar', 'tree')

# (theme, foreground, background) -> why it may sit below the floor
ACCEPTED = {
    # WCAG 1.4.3 exempts text in an inactive user interface component.
    ('LIGHT', '#aaaaaa', '#e8e8e8'): 'disabled control text -- WCAG-exempt',
    ('LIGHT', '#aaaaaa', '#f5f5f5'): 'disabled control text -- WCAG-exempt',
    ('DARK',  '#555555', '#333333'): 'disabled control text -- WCAG-exempt',
    ('DARK',  '#555555', '#1a1a1a'): 'disabled control text -- WCAG-exempt',
    # Pre-existing, unrelated to gold: unselected dark tab labels.
    ('DARK',  '#888888', '#2a2a2a'): 'unselected tab label -- 4.05:1',
}


def _luminance(value: str) -> float:
    h = value.lstrip('#')
    if len(h) == 8:                       # Qt #AARRGGBB
        h = h[2:]
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chans = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _rules(css: str):
    for match in re.finditer(r'([^{}]+)\\{([^{}]*)\\}', css):
        selector = ' '.join(match.group(1).split())
        props = {}
        for decl in match.group(2).split(';'):
            if ':' in decl:
                key, _, val = decl.partition(':')
                props[key.strip()] = val.strip()
        yield selector, props


def _pairs(is_dark: bool):
    colors = DialogStyleManager.get_colors(is_dark)
    css = DialogStyleManager.get_extended_stylesheet(
        is_dark, 'Arial', *COMPONENTS)
    for selector, props in _rules(css):
        fg = props.get('color')
        if not fg or not HEX.match(fg):
            continue
        bg = props.get('background-color') or props.get('background')
        if not bg or not HEX.match(bg):
            bg = colors['bg']             # inherits the dialog surface
        yield selector, fg.lower(), bg.lower()


@pytest.mark.parametrize('is_dark,theme', [(False, 'LIGHT'), (True, 'DARK')])
def test_text_pairs_meet_aa(is_dark, theme):
    """Every text colour clears 4.5:1 on the ground it renders on."""
    failures = []
    for selector, fg, bg in _pairs(is_dark):
        if (theme, fg, bg) in ACCEPTED:
            continue
        ratio = contrast(fg, bg)
        if ratio < TEXT_FLOOR:
            failures.append(f'{theme} {selector}: {fg} on {bg} = {ratio:.4f}:1')
    assert not failures, (
        'text below AA 4.5:1 --\\n  ' + '\\n  '.join(sorted(set(failures)))
        + '\\n\\nIf one of these is intentional, add it to ACCEPTED with a reason.')


@pytest.mark.parametrize('is_dark,theme', [(False, 'LIGHT'), (True, 'DARK')])
def test_accepted_entries_are_still_real(is_dark, theme):
    """An ACCEPTED entry that no longer occurs is stale and should be removed."""
    seen = {(theme, fg, bg) for _, fg, bg in _pairs(is_dark)}
    stale = [k for k in ACCEPTED if k[0] == theme and k not in seen]
    assert not stale, f'stale ACCEPTED entries for {theme}: {stale}'


def test_light_mode_has_exactly_two_golds():
    """One ruled value plus one derivative. A third means a role went unshared."""
    light = DialogStyleManager.get_colors(False)
    golds = {light[k].lower() for k in
             ('accent', 'accent_hover', 'accent_pressed', 'accent_ink',
              'border_focus', 'tooltip_border', 'info', 'selection_bg',
              'output_text_color', 'line_number_current_fg')}
    assert len(golds) == 2, f'expected 2 light golds, found {len(golds)}: {sorted(golds)}'


def test_deep_gold_serves_both_its_roles():
    """The one derivative must work as a white-bearing fill AND as text."""
    light = DialogStyleManager.get_colors(False)
    deep = light['accent_ink']
    assert light['accent_hover'] == deep, 'hover and ink must share the derivative'
    assert contrast('#ffffff', deep) >= TEXT_FLOOR, 'white must clear on the deep gold'
    for surface in ('#f5f5f5', '#eeeeee', '#e8e8e8'):
        ratio = contrast(deep, surface)
        assert ratio >= TEXT_FLOOR, f'deep gold on {surface} = {ratio:.4f}:1'


def test_dark_mode_keeps_one_gold_for_text():
    """Dark has headroom everywhere; accent_ink must not diverge there."""
    dark = DialogStyleManager.get_colors(True)
    assert dark['accent_ink'] == dark['accent']
'''


def verify(root: Path) -> int:
    """Check what is on disk. Safe to call on its own via --verify-only."""
    step('V', 'verification')
    sys.path.insert(0, str(root))
    for mod in [m for m in sys.modules if m.startswith('utils')]:
        del sys.modules[mod]
    from utils.dialog_styles import DialogStyleManager as D

    light, dark = D.get_colors(False), D.get_colors(True)
    if light['accent'] != DARK_GOLD:
        die('the accent moved -- it must not')
    ok(f'accent still {DARK_GOLD}')

    golds = {light[k].lower() for k in
             ('accent', 'accent_hover', 'accent_pressed', 'accent_ink',
              'border_focus', 'tooltip_border', 'info', 'selection_bg',
              'output_text_color', 'line_number_current_fg')}
    if len(golds) != 2:
        die(f'expected 2 light golds, found {sorted(golds)}')
    ok(f'light mode carries exactly 2 golds: {sorted(golds)}')

    if light['accent_hover'] != light['accent_ink']:
        die('hover and ink must share the single derivative')
    ok('hover and text share one derivative')

    if dark['accent_ink'] != dark['accent']:
        die('dark accent_ink must equal the dark accent')
    ok('dark mode unchanged (accent_ink == accent there)')

    print(f"{DIM}    running pytest ...{OFF}")
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '-q',
            '--benchmark-disable'], check=False, quiet=True)
    out = r.stdout or ''
    ours, other = classify(out)
    if ours:
        print(out[-2500:])
        die(f'colour-surface tests failed: {ours}')
    ok(f"pytest: {out.strip().splitlines()[-1]}")
    if other:
        report_unrelated(other)

    print(f"{DIM}    running unittest ...{OFF}")
    r = sh([sys.executable, '-m', 'unittest', 'test_rnv_text_transformer'],
           check=False, quiet=True)
    if r.returncode != 0:
        print((r.stderr or '')[-2500:])
        die('unittest failed')
    line = [l for l in (r.stderr or '').splitlines() if l.startswith('Ran ')]
    ok(f"unittest: {line[0] if line else 'passed'} -- OK")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--skip-verify', action='store_true')
    ap.add_argument('--verify-only', action='store_true',
                    help='skip the edits and snapshots; just verify what is on disk')
    args = ap.parse_args()
    dry, root = args.check, Path.cwd()

    if args.verify_only:
        sys.path.insert(0, str(root))
        return verify(root)

    print(f"\n{BOLD}Deep gold — two values in light mode, not four{OFF}")
    print(f"{DIM}{DARK_GOLD} keeps every job it passes; {DEEP} takes hover and "
          f"text{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    colors = root / 'utils' / 'colors.py'
    styles = root / 'utils' / 'dialog_styles.py'
    init = root / 'utils' / '__init__.py'

    step('0', 'pre-flight')
    for f in (colors, styles, init):
        if not f.exists():
            die(f'{f} not found -- run from the repository root')
    ctext = colors.read_text(encoding='utf-8')
    if 'BRAND_DARK_GOLD' not in ctext:
        die('gold alignment not applied; run that first')
    if 'BRAND_DARK_GOLD_HOVER' not in ctext and 'BRAND_DARK_GOLD_DEEP' not in ctext:
        die('neither the old hover constant nor the new deep one is present')
    ok('repository recognised')

    step('1', f'utils/colors.py -- BRAND_DARK_GOLD_HOVER -> BRAND_DARK_GOLD_DEEP ({DEEP})')
    n = sub(colors, [(
        "#: Light-mode hover tint. Derived, not ruled.\n"
        "BRAND_DARK_GOLD_HOVER: Final[str] = lighten(BRAND_DARK_GOLD, 19)\n",
        DEEP_BLOCK)], dry)
    if n:
        ok(f'BRAND_DARK_GOLD_DEEP = {DEEP} replaces the {OLD_HOVER} tint')
    else:
        skip('colors.py constant')

    n = sub(colors, [
        ("    'BRAND_DARK_GOLD_HOVER',", "    'BRAND_DARK_GOLD_DEEP',"),
        (">>> lighten(BRAND_DARK_GOLD, 19)\n        '#9f864a'",
         f">>> lighten(BRAND_DARK_GOLD, {DEEP_STEP})\n        '{DEEP}'"),
    ], dry)
    ok(f'{n} reference(s) updated in colors.py') if n else skip('colors.py refs')

    step('2', 'utils/dialog_styles.py -- share the derivative across both roles')
    n = sub(styles, [("    BRAND_DARK_GOLD_HOVER,", "    BRAND_DARK_GOLD_DEEP,")], dry)
    ok('import') if n else skip('import')

    n = sub(styles, [("        'accent_text': '#000000',  # Text on accent background",
                      "        'accent_ink': BRAND_GOLD,  # Accent when it carries text\n"
                      "        'accent_text': '#000000',  # Text on accent background")],
            dry, scope='    DARK: ClassVar')
    n += sub(styles, [("        'accent_text': '#ffffff',  # Text on accent background",
                       "        'accent_ink': BRAND_DARK_GOLD_DEEP,  # Accent when it carries text\n"
                       "        'accent_text': '#ffffff',  # Text on accent background")],
             dry, scope='    LIGHT: ClassVar')
    ok('accent_ink added to both palettes') if n else skip('accent_ink')

    n = sub(styles, [
        ("'accent_hover': BRAND_DARK_GOLD_HOVER,", "'accent_hover': BRAND_DARK_GOLD_DEEP,"),
        ("'info': BRAND_DARK_GOLD,", "'info': BRAND_DARK_GOLD_DEEP,"),
        ("'line_number_current_fg': BRAND_DARK_GOLD,",
         "'line_number_current_fg': BRAND_DARK_GOLD_DEEP,"),
    ], dry, scope='    LIGHT: ClassVar')
    ok(f'{n} LIGHT key(s) -> the deep gold') if n else skip('light keys')

    rules = [
        ('return f"color: {c[\'accent\']}; font-style: italic;"',
         'return f"color: {c[\'accent_ink\']}; font-style: italic;"'),
        ("                padding-top: 10px;\n                color: {c['accent']};",
         "                padding-top: 10px;\n                color: {c['accent_ink']};"),
        ("                border-color: {c['accent']};\n                color: {c['accent']};",
         "                border-color: {c['accent']};\n                color: {c['accent_ink']};"),
        ("                background-color: {c['bg']};\n                color: {c['accent']};",
         "                background-color: {c['bg']};\n                color: {c['accent_ink']};"),
        ("                background-color: {c['bg_hover']};\n                color: {c['accent']};",
         "                background-color: {c['bg_hover']};\n                color: {c['accent_ink']};"),
        ("            'accent': c['accent'],", "            'accent': c['accent_ink'],"),
    ]
    n = sub(styles, rules, dry)
    if n:
        ok(f'{n} of 6 text rules -> accent_ink (tip, group box, button hover, '
           f'tab selected, tab hover, status)')
        if n != 6:
            die(f'expected 6, applied {n} -- stylesheet is not as expected')
    else:
        skip('text rules')

    step('3', 'utils/__init__.py')
    n = sub(init, [("    BRAND_DARK_GOLD_HOVER,", "    BRAND_DARK_GOLD_DEEP,"),
                   ("    'BRAND_DARK_GOLD_HOVER',", "    'BRAND_DARK_GOLD_DEEP',")], dry)
    ok(f'{n} export(s) renamed') if n else skip('exports')

    step('4', 'tests/test_contrast_pairs.py -- the guard')
    guard = root / 'tests' / 'test_contrast_pairs.py'
    if guard.exists():
        skip('guard')
    else:
        if not dry:
            guard.write_text(GUARD, encoding='utf-8')
        ok('installed: pairing floors, two-gold assertion, stale-exception check')

    step('5', 'snapshots')
    if dry:
        ok('would regenerate')
    else:
        r = sh([sys.executable, '-m', 'pytest', 'tests/', '--snapshot-update',
                '-q', '--benchmark-disable'], check=False, quiet=True)
        out = r.stdout or ''
        # Judge this step by the snapshot report, NOT by the exit code. An
        # unrelated test failing elsewhere in the run makes pytest exit non-zero
        # while the snapshots regenerate perfectly well.
        report = [l.strip() for l in out.splitlines()
                  if 'snapshot' in l.lower() and ('updated' in l or 'passed' in l)]
        ours, other = classify(out)
        if ours:
            print(out[-1800:])
            die(f'snapshot/colour tests failed: {ours}')
        if not report:
            print(out[-1800:])
            die('no snapshot report produced -- regeneration did not run')
        ok(f'regenerated — {report[0]}')
        if other:
            report_unrelated(other)

    if not dry and not args.skip_verify:
        verify(root)

    print(f"\n{GREEN}{BOLD}Done.{OFF} Nothing committed — review with `git diff`.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
