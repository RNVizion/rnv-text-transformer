#!/usr/bin/env python3
"""
Palette consolidation -> rnv-text-transformer
==============================================

RUN apply_color_constants.py FIRST. That pass is naming only and asserts both
stylesheets are byte-identical; this pass changes values. Keeping them apart is
what lets the first one prove it moved nothing -- fold them together and a
botched rename hides inside an intended colour change.

Two things, both value changes.

1. FOUR REDUNDANT GREYS MERGED
   Of 22 greys in the palette, 7 are named by the register and 15 are the app's
   own. Only four are genuinely redundant; the rest carry a distinction --
   five per theme are the depth ramp (window / panel / card / tertiary /
   hover), and flattening those costs the UI its layering.

     DARK  scrollbar_handle_main  GREY_50 -> GREY_44   LIGHT already merged
                                                       these two (#aaaaaa)
     DARK  scrollbar_bg           GREY_25 -> APP_CARD  ratio 1.068; a track
                                                       between panel and card
     LIGHT line_number_fg         GREY_99 -> GREY_66   sole user of #999999
           ...and gutter contrast goes 2.50 -> 4.95
     BOTH  gutter/header ground   GREY_F0 -> GREY_EE   ratio 1.018, and the
                                                       two never share a surface

   Riding along, no value removed: DARK line_number_fg GREY_66 -> GREY_88, the
   theme's own text_muted. Gutter contrast 3.03 -> 4.91.

2. THE TWO DARK GOLDS DERIVED RATHER THAN MINTED
   The register: "Values between and beyond the two are modulations, and none
   of them is promoted... A surface that needs a lighter or darker gold derives
   it; it doesn't mint one." Light mode already derives. Dark was still minting.

     GOLD_HOVER    #dcc9a3 -> lighten(BRAND_GOLD, +13)  #dfc9a0
     GOLD_PRESSED  #b7a480 -> lighten(BRAND_GOLD, -23)  #bba57c

   The steps were chosen to land closest to the hand-picked values, not for
   symmetry: RGB distance 2.4 and 3.3 out of 255. Separation from the accent
   holds (1.145 vs 1.138; 1.292 vs 1.315) and hue snaps back to BRAND_GOLD's
   39.0 degrees exactly, where the minted pair had drifted to 40.0 and 39.3.

   +19 would have matched light's perceptual separation more neatly. Fidelity
   won: the brief was to derive, not to restyle.

Snapshots move -- deliberately, for nine palette entries (seven grey
repoints plus the two golds). Nothing else may move, and that
is asserted.

    python3 apply_palette_consolidation.py            # apply and verify
    python3 apply_palette_consolidation.py --check    # dry run

Idempotent. Nothing is committed.
"""

from __future__ import annotations

import argparse
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


def _lighten(color, n):
    rgb = color.lstrip('#')
    return '#' + ''.join(
        f'{max(0, min(255, int(rgb[i:i+2], 16) + n)):02x}' for i in (0, 2, 4))


BRAND_GOLD = '#d2bc93'
HOVER_STEP, PRESSED_STEP = 13, -23
NEW_HOVER = _lighten(BRAND_GOLD, HOVER_STEP)      # #dfc9a0
NEW_PRESSED = _lighten(BRAND_GOLD, PRESSED_STEP)  # #bba57c

RETIRED = ['GREY_25', 'GREY_50', 'GREY_99', 'GREY_F0']

# (label, scope marker or None, old, new)
REPOINTS = [
    ('DARK scrollbar_bg -> APP_CARD', '    DARK: ClassVar',
     "'scrollbar_bg': GREY_25,", "'scrollbar_bg': APP_CARD,"),
    ('DARK scrollbar_handle_main -> GREY_44', '    DARK: ClassVar',
     "'scrollbar_handle_main': GREY_50,", "'scrollbar_handle_main': GREY_44,"),
    ('DARK line_number_fg -> GREY_88 (text_muted)', '    DARK: ClassVar',
     "'line_number_fg': GREY_66,", "'line_number_fg': GREY_88,"),
    ('LIGHT line_number_fg -> GREY_66 (text_muted)', '    LIGHT: ClassVar',
     "'line_number_fg': GREY_99,", "'line_number_fg': GREY_66,"),
    ('LIGHT line_number_bg -> GREY_EE', '    LIGHT: ClassVar',
     "'line_number_bg': GREY_F0,", "'line_number_bg': GREY_EE,"),
]

GOLD_BLOCK = f'''#: dark-mode hover. DERIVED, not minted -- the register rules that a surface
#: needing a lighter or darker gold derives it. Held closest to the value it
#: replaces (#dcc9a3, RGB distance 2.4) rather than to a tidy step, because the
#: brief was to change the provenance and not the appearance. Hue snaps back to
#: BRAND_GOLD's 39.0 degrees exactly; the minted value had drifted to 40.0.
GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, {HOVER_STEP})

#: dark-mode pressed. Same derivation, same reasoning (replaces #b7a480,
#: RGB distance 3.3, hue drift 39.3 -> 39.0). Dark mode has room for a distinct
#: pressed state; light mode does not, which is why BRAND_DARK_GOLD_PRESSED is
#: the accent itself and this is not.
GOLD_PRESSED: Final[str] = lighten(BRAND_GOLD, {PRESSED_STEP})'''


def scoped_sub(path, marker, old, new, dry):
    text = path.read_text(encoding='utf-8')
    if marker:
        if marker not in text:
            die(f'{path}: scope marker {marker!r} not found')
        head, body = text.split(marker, 1)
    else:
        head, body = '', text
    n = body.count(old)
    if n > 1:
        die(f'{path}: {old!r} appears {n} times in scope; refusing')
    if n == 0:
        return False
    body = body.replace(old, new)
    if not dry:
        path.write_text(head + (marker or '') + body, encoding='utf-8')
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--skip-tests', action='store_true')
    args = ap.parse_args()
    dry, root = args.check, Path.cwd()

    colors_py = root / 'utils' / 'colors.py'
    styles_py = root / 'utils' / 'dialog_styles.py'
    init_py = root / 'utils' / '__init__.py'

    print(f"\n{BOLD}Palette consolidation — nine entries move, nothing else{OFF}")
    print(f"{DIM}4 greys merged, 2 dark golds derived{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    step('0', 'pre-flight')
    for f in (colors_py, styles_py, init_py):
        if not f.exists():
            die(f'{f} not found -- run from the repository root')
    ctext = colors_py.read_text(encoding='utf-8')
    if 'GREY_F5' not in ctext:
        die('apply_color_constants.py has not been run -- run that first.\n'
            '  It is naming-only and asserts the stylesheets are byte-identical;\n'
            '  this pass changes values and needs that proof to stand separately.')
    ok('constants pass detected')

    before = {}
    if not dry:
        sys.path.insert(0, str(root))
        for m in [m for m in sys.modules if m.startswith('utils')]:
            del sys.modules[m]
        from utils.dialog_styles import DialogStyleManager as _D
        for t in ('DARK', 'LIGHT'):
            before[t] = dict(getattr(_D, t))
        ok('captured both palettes for the "only these six" check')

    step('1', 'utils/colors.py -- retire four greys, derive two golds')
    if 'lighten(BRAND_GOLD, 13)' in ctext:
        skip('colors.py')
    else:
        for name in RETIRED:
            pat = re.compile(rf"^{name}: Final\[str\] = '#[0-9a-f]{{6}}'\n", re.M)
            if not pat.search(ctext):
                die(f'{name} definition not found in colors.py')
            ctext = pat.sub('', ctext)
            ctext = re.sub(rf"^    '{name}',\n", '', ctext, flags=re.M)
        ok(f'{len(RETIRED)} retired: {", ".join(RETIRED)}')

        old_gold = re.search(
            r"#: dark-mode hover.*?GOLD_PRESSED: Final\[str\] = '#[0-9a-f]{6}'",
            ctext, re.S)
        if not old_gold:
            die('cannot locate the GOLD_HOVER / GOLD_PRESSED block')
        ctext = ctext.replace(old_gold.group(0), GOLD_BLOCK)
        ok(f'GOLD_HOVER -> lighten(BRAND_GOLD, {HOVER_STEP})  = {NEW_HOVER}')
        ok(f'GOLD_PRESSED -> lighten(BRAND_GOLD, {PRESSED_STEP}) = {NEW_PRESSED}')
        if not dry:
            colors_py.write_text(ctext, encoding='utf-8')

    step('2', 'utils/dialog_styles.py -- repoint the merged keys')
    applied = 0
    for label, marker, old, new in REPOINTS:
        if scoped_sub(styles_py, marker, old, new, dry):
            ok(label)
            applied += 1
    # diff_html_header_bg is GREY_F0 in BOTH palettes and both go to GREY_EE
    stext = styles_py.read_text(encoding='utf-8')
    n = stext.count("'diff_html_header_bg': GREY_F0,")
    if n:
        stext = stext.replace("'diff_html_header_bg': GREY_F0,",
                              "'diff_html_header_bg': GREY_EE,")
        applied += n
        ok(f'diff_html_header_bg -> GREY_EE ({n} palettes)')
    for name in RETIRED:
        stext = re.sub(rf'^    {name},\n', '', stext, flags=re.M)
    if not dry:
        styles_py.write_text(stext, encoding='utf-8')
    if applied == 0:
        skip('dialog_styles.py')

    step('3', 'utils/__init__.py')
    itext = init_py.read_text(encoding='utf-8')
    hits = sum(len(re.findall(rf"^    '?{n}'?,\n", itext, re.M)) for n in RETIRED)
    if hits:
        for name in RETIRED:
            itext = re.sub(rf"^    '?{name}'?,\n", '', itext, flags=re.M)
        if not dry:
            init_py.write_text(itext, encoding='utf-8')
        ok(f'{hits} reference(s) removed')
    else:
        skip('exports')

    if dry:
        print(f"\n{GREEN}{BOLD}Dry run complete.{OFF}")
        return 0

    step('4', 'snapshots')
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '--snapshot-update', '-q',
            '--benchmark-disable'])
    rep = [l.strip() for l in (r.stdout or '').splitlines()
           if 'snapshot' in l.lower() and ('updated' in l or 'passed' in l)]
    failed = [l for l in (r.stdout or '').splitlines() if l.startswith('FAILED ')]
    ours = [f for f in failed if any(t in f.lower() for t in
            ('contrast', 'snapshot', 'style', 'colour', 'color', 'brand', 'mirror'))]
    if ours:
        print((r.stdout or '')[-2000:]); die(f'colour tests failed: {ours}')
    if not rep:
        print((r.stdout or '')[-1500:]); die('no snapshot report -- regeneration did not run')
    ok(f'regenerated — {rep[0]}')
    if failed:
        warn(f'{len(failed)} unrelated failure(s), left alone')

    step('V', 'verification')
    for m in [m for m in sys.modules if m.startswith('utils')]:
        del sys.modules[m]
    from utils.dialog_styles import DialogStyleManager as D2
    from utils import colors as C

    def lum(h):
        c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def cr(a, b):
        la, lb = lum(a), lum(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    moved = []
    for t in ('DARK', 'LIGHT'):
        after = getattr(D2, t)
        for k, v in before[t].items():
            if after[k] != v:
                moved.append(f'{t}.{k}  {v} -> {after[k]}')
    # 7 grey repoints (diff_html_header_bg is in BOTH palettes) + 2 golds.
    EXPECTED = 9
    print(f'{DIM}    palette entries that moved:{OFF}')
    for m in moved:
        print(f'      {m}')
    if len(moved) != EXPECTED:
        die(f'expected {EXPECTED} palette entries to move, {len(moved)} did')
    ok(f'exactly {EXPECTED} entries moved, as designed')

    if C.GOLD_HOVER != NEW_HOVER or C.GOLD_PRESSED != NEW_PRESSED:
        die(f'gold derivation wrong: {C.GOLD_HOVER} / {C.GOLD_PRESSED}')
    ok(f'golds derived: {C.GOLD_HOVER} / {C.GOLD_PRESSED}')
    for name in RETIRED:
        if hasattr(C, name):
            die(f'{name} still defined in colors.py')
    ok(f'{len(RETIRED)} retired constants gone')

    L, K = D2.get_colors(False), D2.get_colors(True)
    checks = [
        ('LIGHT gutter number', L['line_number_fg'], L['line_number_bg'], 2.50),
        ('DARK  gutter number', K['line_number_fg'], K['line_number_bg'], 3.03),
    ]
    for label, fg, bg, was in checks:
        now = cr(fg, bg)
        ok(f'{label}: {was:.2f} -> {now:.2f} {"PASS" if now >= 4.5 else "still below 4.5"}')

    if args.skip_tests:
        return 0
    for suite, cmd in (('pytest', [sys.executable, '-m', 'pytest', 'tests/', '-q',
                                   '--benchmark-disable']),
                       ('unittest', [sys.executable, '-m', 'unittest',
                                     'test_rnv_text_transformer'])):
        print(f'{DIM}    {suite} ...{OFF}')
        r = sh(cmd)
        out = (r.stdout or '') + (r.stderr or '')
        if r.returncode != 0:
            print(out[-2500:]); die(f'{suite} failed')
        tail = [l for l in out.strip().splitlines()
                if l.startswith(('Ran ', 'OK')) or 'passed' in l]
        ok(f'{suite}: {tail[-1] if tail else "passed"}')

    print(f"\n{GREEN}{BOLD}Done.{OFF} Nothing committed — review with `git diff`.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
