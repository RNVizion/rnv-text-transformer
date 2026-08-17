#!/usr/bin/env python3
"""
Revert the out-of-scope colour changes from the gold alignment pass
===================================================================

The gold alignment was scoped to one thing: change the VALUE of the dark gold
(and name the constants). It was not scoped to change any other colour, or how
the colours interact.

Three changes overstepped that. All three are reverted here.

  utils/dialog_styles.py  LIGHT accent_text     #000000 -> #ffffff
  utils/dialog_styles.py  LIGHT selection_text  #000000 -> #ffffff
  docs/...Color_System.md dialog button pressed text row, likewise

Why they were wrong, not just out of scope:

  White on the retired #b19145 measured 2.9976 and genuinely failed, which is
  what the change was reacting to. But moving the value to #8c7337 ALREADY
  fixed it -- white now measures 4.5429 and passes AA. The text colour was
  changed to solve a problem the value change had already solved, and doing so
  flattened the dialog button's gold/white inversion: pressed stopped being the
  mirror of hover.

  The stated reason for holding selection_text at #000000 -- that white fails
  on the accent_hover tint -- does not survive checking either. That condition
  is PRE-EXISTING (white on the old #c4a458 was 2.3868) and the gold change
  IMPROVED it to 3.5099. It is a real finding and it is reported, but it was
  never this pass's to fix.

Run from the repository root:

    python3 revert_out_of_scope.py            # revert, regenerate, verify
    python3 revert_out_of_scope.py --check    # dry run

Idempotent. Nothing is committed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    '\033[32m', '\033[33m', '\033[31m', '\033[2m', '\033[1m', '\033[0m'
)


def ok(m):    print(f"{GREEN}    + {m}{OFF}")
def skip(m):  print(f"{DIM}    = {m} (already reverted){OFF}")
def warn(m):  print(f"{YELLOW}    ! {m}{OFF}")
def die(m):   print(f"{RED}\nABORT: {m}{OFF}"); sys.exit(1)
def step(n, m): print(f"\n{BOLD}[{n}]{OFF} {m}")


def edit(path: Path, pairs, dry: bool) -> int:
    text = path.read_text(encoding='utf-8')
    original = text
    n = 0
    for old, new in pairs:
        c = text.count(old)
        if c > 1:
            die(f"{path}: {old[:60]!r} appears {c} times; refusing ambiguous edit")
        if c == 1:
            text = text.replace(old, new)
            n += 1
    if text != original and not dry:
        path.write_text(text, encoding='utf-8')
    return n


def sh(cmd, check=True, quiet=False):
    return subprocess.run(cmd, check=check, text=True, capture_output=quiet)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--skip-verify', action='store_true')
    args = ap.parse_args()
    root = Path.cwd()
    dry = args.check

    print(f"\n{BOLD}Revert out-of-scope colour changes{OFF}")
    print(f"{DIM}the gold value stays #8c7337; only the two text keys go back{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    step('0', 'pre-flight')
    ds = root / 'utils' / 'dialog_styles.py'
    doc = root / 'docs' / 'RNV_Brand_Color_System.md'
    for f in (ds, doc):
        if not f.exists():
            die(f'{f} not found -- run from the repository root')
    if "BRAND_DARK_GOLD" not in ds.read_text(encoding='utf-8'):
        die('gold alignment does not appear to be applied; nothing to revert')
    ok('repository recognised, gold alignment present')

    step('1', 'utils/dialog_styles.py -- restore the two LIGHT text keys')
    # DARK carries byte-identical lines for both keys, so a whole-file match is
    # ambiguous by construction. Edit inside the LIGHT block only.
    text = ds.read_text(encoding='utf-8')
    marker = '    LIGHT: ClassVar'
    if marker not in text:
        die('cannot locate the LIGHT palette block')
    head, light = text.split(marker, 1)
    n = 0
    for key in ('accent_text', 'selection_text'):
        old = f"'{key}': '#000000',"
        new = f"'{key}': '#ffffff',"
        c = light.count(old)
        if c > 1:
            die(f"{key} appears {c} times inside LIGHT; refusing ambiguous edit")
        if c == 1:
            light = light.replace(old, new)
            n += 1
    if n and not dry:
        ds.write_text(head + marker + light, encoding='utf-8')
    if n:
        ok(f'{n} key(s) restored to #ffffff (LIGHT block only; DARK not opened)')
    else:
        skip('dialog_styles.py')

    step('2', 'docs/RNV_Brand_Color_System.md -- the pressed row and the rule note')
    n = edit(doc, [
        ("| Pressed | **`#8c7337`** | `#000000` | `#8c7337` |",
         "| Pressed | **`#8c7337`** | `#FFFFFF` | `#8c7337` |"),
        ("**Text on gold is `#000000`.** At `#8c7337` black measures 4.6226:1 "
         "and white 4.5429:1.",
         "**Text on gold.** The register rules `#000000`. At `#8c7337` both clear "
         "the 4.5 floor — black 4.6226:1, white 4.5429:1 — so the dialog buttons' "
         "gold/white inversion, which puts `#FFFFFF` on the pressed state as the "
         "mirror of hover, is compliant at this value. It was not at `#b19145`, "
         "where white measured 2.9976:1. Worth a ruling from Brand Infrastructure "
         "rather than a silent choice either way."),
    ], dry)
    ok(f'{n} passage(s) corrected') if n else skip('brand doc')

    step('3', 'snapshots')
    if dry:
        ok('would regenerate')
    else:
        r = sh([sys.executable, '-m', 'pytest', 'tests/', '--snapshot-update', '-q',
                '--benchmark-disable'], check=False, quiet=True)
        if r.returncode != 0:
            print((r.stdout or '')[-1500:])
            die('snapshot regeneration failed')
        ok('regenerated')

    if not dry and not args.skip_verify:
        step('V', 'verification')
        ds_text = ds.read_text(encoding='utf-8')
        light = ds_text.split('LIGHT: ClassVar')[1]
        for key in ('accent_text', 'selection_text'):
            line = [l for l in light.splitlines() if f"'{key}'" in l][0]
            if '#ffffff' not in line:
                die(f'LIGHT {key} did not revert: {line.strip()}')
        ok('LIGHT accent_text and selection_text are #ffffff')

        dark = ds_text.split('DARK: ClassVar')[1].split('LIGHT: ClassVar')[0]
        for key in ('accent_text', 'selection_text'):
            line = [l for l in dark.splitlines() if f"'{key}'" in l][0]
            if '#000000' not in line:
                die(f'DARK {key} was disturbed: {line.strip()}')
        ok('DARK accent_text and selection_text still #000000 (untouched)')

        if '#8c7337' not in ds_text and 'BRAND_DARK_GOLD' not in ds_text:
            die('the gold value was disturbed')
        ok('gold value unchanged')

        print(f"{DIM}    running pytest ...{OFF}")
        r = sh([sys.executable, '-m', 'pytest', 'tests/', '-q', '--benchmark-disable'],
               check=False, quiet=True)
        if r.returncode != 0:
            print((r.stdout or '')[-2000:]); die('pytest failed')
        ok(f"pytest: {(r.stdout or '').strip().splitlines()[-1]}")

        print(f"{DIM}    running unittest ...{OFF}")
        r = sh([sys.executable, '-m', 'unittest', 'test_rnv_text_transformer'],
               check=False, quiet=True)
        if r.returncode != 0:
            print((r.stderr or '')[-2000:]); die('unittest failed')
        line = [l for l in (r.stderr or '').splitlines() if l.startswith('Ran ')]
        ok(f"unittest: {line[0] if line else 'passed'} -- OK")

    print(f"\n{GREEN}{BOLD}Done.{OFF} Nothing committed — review with `git diff`.")
    print(f"\n{YELLOW}Reported, NOT fixed — pre-existing, not this pass's business:{OFF}")
    print("  White on the accent_hover tint fails: 3.5099:1 on #9f864a.")
    print("  It was 2.3868:1 on the old #c4a458, so the gold change improved it.")
    print("  Affects hovered rows in combo/table/list/tree. Needs its own decision.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
