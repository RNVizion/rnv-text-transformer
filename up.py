#!/usr/bin/env python3
"""
Trailing blank line loss in TextCleaner -> rnv-text-transformer
================================================================

Found by hypothesis during the gold alignment run:

    tests/test_properties.py::TestTextCleanerProperties
        ::test_sort_lines_reverse_idempotent

Pre-existing, unrelated to colour, and larger than the failing test showed.

The bug
-------
Four operations follow the pattern

    lines = text.splitlines()
    ... operate ...
    return _preserve_trailing_newline(text, '\\n'.join(lines))

`'\\n'.join()` is not a round trip when the final line is empty. A trailing
'\\n' is a TERMINATOR to splitlines(), not a separator:

    ['0', '', '']  -> join '0\\n\\n'  -> splitlines ['0', '']    one line short
    ['a', '']      -> join 'a\\n'    -> splitlines ['a']        one line short

`_preserve_trailing_newline` handles the *input* side of this asymmetry. Nothing
handled the output side, so a blank final line is dropped on every pass:

    remove_leading_spaces('a\\n\\n')   -> 'a\\n'      blank line deleted
    remove_trailing_spaces('a\\n\\n')  -> 'a\\n'      blank line deleted
    sort_lines('a\\n\\n')              -> '\\na\\n'    blank line deleted
    sort_lines_reverse('a\\n\\n')      -> 'a\\n'      blank line deleted

That is silent data loss on ordinary text, and it is also why the operations
are not idempotent: each pass eats one more blank line until none are left.
The hypothesis counterexample was '\\r\\r0', which reaches the same place via
'\\r' being a splitlines() boundary.

The fix
-------
One helper, `_join_lines`, used by all four callers. When the final line is
empty it emits one extra terminator so the output reads back as the exact line
list that produced it. `_preserve_trailing_newline` is kept and still applies --
it covers the input side, which is a different asymmetry.

Also affected and fixed by the same change: \\v \\f \\x1c \\x1d \\x1e \\x85
\\u2028 \\u2029, all of which splitlines() treats as boundaries.

Run from the repository root:

    python3 fix_line_join.py            # apply and verify
    python3 fix_line_join.py --check    # dry run

Idempotent. Nothing is committed. Touches core/text_cleaner.py only.
"""

from __future__ import annotations

import argparse
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


HELPER = '''    @staticmethod
    def _join_lines(original: str, lines: list[str]) -> str:
        """
        Join lines with '\\\\n' so that ``splitlines()`` reads back exactly
        ``lines``, then restore any trailing separator from ``original``.

        ``'\\\\n'.join()`` is not a round trip when the final line is empty,
        because a trailing '\\\\n' is a TERMINATOR to ``splitlines()`` rather
        than a separator::

            ['0', '', '']  -> '0\\\\n\\\\n'  -> ['0', '']    one line short
            ['a', '']      -> 'a\\\\n'     -> ['a']        one line short

        Left unhandled, every pass silently drops the final blank line --
        which is both data loss on ordinary text and the reason the affected
        operations were not idempotent.

        An empty final line therefore needs one extra terminator to survive
        the round trip. ``_preserve_trailing_newline`` is still applied after:
        it covers the *input* side of the same asymmetry, which is separate.

        Args:
            original: The text the operation received
            lines: The processed lines, in output order

        Returns:
            Text that splits back into exactly ``lines``
        """
        result = '\\n'.join(lines)
        if lines and lines[-1] == '':
            result += '\\n'
        return TextCleaner._preserve_trailing_newline(original, result)

'''

# (label, exact old text, exact new text)
CALLERS = [
    ("remove_duplicate_lines (both branches)",
     "            result = '\\n'.join(unique)\n"
     "        else:\n"
     "            result = '\\n'.join(sorted(set(lines)))\n\n"
     "        return TextCleaner._preserve_trailing_newline(text, result)",
     "            result = unique\n"
     "        else:\n"
     "            result = sorted(set(lines))\n\n"
     "        return TextCleaner._join_lines(text, result)"),
    ("sort_lines",
     "        result = '\\n'.join(sorted(lines, key=key_func, reverse=reverse))\n"
     "        return TextCleaner._preserve_trailing_newline(text, result)",
     "        return TextCleaner._join_lines(\n"
     "            text, sorted(lines, key=key_func, reverse=reverse))"),
    ("remove_leading_spaces",
     "        result = '\\n'.join(line.lstrip() for line in lines)\n"
     "        return TextCleaner._preserve_trailing_newline(text, result)",
     "        return TextCleaner._join_lines(text, [line.lstrip() for line in lines])"),
    ("remove_trailing_spaces",
     "        result = '\\n'.join(line.rstrip() for line in lines)\n"
     "        return TextCleaner._preserve_trailing_newline(text, result)",
     "        return TextCleaner._join_lines(text, [line.rstrip() for line in lines])"),
]

TESTS = '''
# ════════════════════════════════════════════════════════════════════════════
# Trailing blank line preservation
#
# Regression guard for the splitlines()/join() round-trip bug: joining a line
# list whose final entry is empty produced a string that read back one line
# short, so every pass silently deleted a trailing blank line.
# ════════════════════════════════════════════════════════════════════════════
class TestTrailingBlankLines:
    """core/text_cleaner.py -- _join_lines round trip."""

    OPS = [
        CleanupOperation.REMOVE_LEADING_SPACES,
        CleanupOperation.REMOVE_TRAILING_SPACES,
        CleanupOperation.SORT_LINES,
        CleanupOperation.SORT_LINES_REVERSE,
    ]

    @pytest.mark.parametrize('op', OPS)
    @pytest.mark.parametrize('text', ['a\\n\\n', 'a\\nb\\n\\n', '\\n\\n', 'a\\n\\n\\n'])
    def test_trailing_blank_lines_survive(self, op, text):
        """A blank final line must not be eaten."""
        before = len(text.splitlines())
        after = len(TextCleaner.cleanup(text, op).splitlines())
        assert after == before, (
            f'{op} turned {before} lines into {after} for {text!r}')

    @pytest.mark.parametrize('op', OPS)
    @pytest.mark.parametrize('text', ['\\r\\r0', 'a\\n\\n', '\\x850', 'a\\x0b\\x0b',
                                     '\\u2028\\u2028z', '\\n\\n', 'b\\na\\n\\n'])
    def test_idempotent_on_boundary_characters(self, op, text):
        """Every splitlines() boundary, not just '\\n' and '\\r'."""
        once = TextCleaner.cleanup(text, op)
        twice = TextCleaner.cleanup(once, op)
        assert once == twice, f'{op} not idempotent for {text!r}'

    def test_join_lines_round_trips(self):
        """The helper's contract: splitlines(_join_lines(x, L)) == L."""
        for lines in ([], [''], ['', ''], ['a', ''], ['0', '', ''], ['a', 'b']):
            joined = TextCleaner._join_lines('', lines)
            assert joined.splitlines() == lines, f'{lines} did not round trip'
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    dry, root = args.check, Path.cwd()

    print(f"\n{BOLD}Trailing blank line loss in TextCleaner{OFF}")
    print(f"{DIM}four operations delete a blank final line on every pass{OFF}")
    if dry:
        print(f"{YELLOW}DRY RUN{OFF}")

    src = root / 'core' / 'text_cleaner.py'
    tests = root / 'tests' / 'test_properties.py'

    step('0', 'pre-flight')
    if not src.exists():
        die('core/text_cleaner.py not found -- run from the repository root')
    text = src.read_text(encoding='utf-8')
    if '_preserve_trailing_newline' not in text:
        die('_preserve_trailing_newline not present; file is not as expected')
    ok('core/text_cleaner.py recognised')

    step('1', 'core/text_cleaner.py -- add _join_lines')
    if '_join_lines' in text:
        skip('_join_lines')
    else:
        anchor = "    @staticmethod\n    def remove_duplicate_lines("
        if text.count(anchor) != 1:
            die('cannot locate the insertion point for _join_lines')
        text = text.replace(anchor, HELPER + anchor)
        ok('_join_lines added below _preserve_trailing_newline')

    step('2', 'core/text_cleaner.py -- route the four callers through it')
    applied = 0
    for label, old, new in CALLERS:
        c = text.count(old)
        if c > 1:
            die(f'{label}: pattern appears {c} times; refusing ambiguous edit')
        if c == 1:
            text = text.replace(old, new)
            applied += 1
            ok(label)
    if applied == 0:
        skip('callers')
    elif applied != len(CALLERS):
        die(f'expected {len(CALLERS)} callers, matched {applied}')

    if not dry:
        src.write_text(text, encoding='utf-8')

    step('3', 'tests/test_properties.py -- regression guards')
    ttext = tests.read_text(encoding='utf-8')
    if 'TestTrailingBlankLines' in ttext:
        skip('regression tests')
    else:
        # this module imports hypothesis but not pytest
        if 'import pytest' not in ttext:
            anchor = 'from hypothesis import'
            if ttext.count(anchor) != 1:
                die('cannot place the pytest import')
            ttext = ttext.replace(anchor, 'import pytest\n\n' + anchor, 1)
            ok('import pytest added')
        if not dry:
            tests.write_text(ttext.rstrip('\n') + '\n' + TESTS, encoding='utf-8')
        ok('3 guards added (blank-line survival, boundary idempotence, round trip)')

    if dry:
        print(f"\n{GREEN}{BOLD}Dry run complete.{OFF}")
        return 0

    step('V', 'verification')
    sys.path.insert(0, str(root))
    for mod in [m for m in sys.modules if m.startswith('core')]:
        del sys.modules[mod]
    from core.text_cleaner import TextCleaner, CleanupOperation as OP

    ops = [OP.REMOVE_LEADING_SPACES, OP.REMOVE_TRAILING_SPACES,
           OP.SORT_LINES, OP.SORT_LINES_REVERSE, OP.REMOVE_DUPLICATE_LINES]
    cases = ['\r\r0', 'a\n\n', '\x850', 'a\x0b\x0b', '\u2028\u2028z', '\n\n',
             'b\na\n\n', 'a\nb\n', 'a\nb', '', '\n', '00', 'a\na', '0']
    bad = []
    for op in ops:
        for t in cases:
            once = TextCleaner.cleanup(t, op)
            if TextCleaner.cleanup(once, op) != once:
                bad.append((op, t))
    if bad:
        die(f'still not idempotent: {bad[:6]}')
    ok(f'{len(ops) * len(cases)} op/input pairs idempotent')

    # a bare string passed where a line list belongs joins per CHARACTER;
    # cheap to assert, and it is the mistake this script made first time.
    for op in ops:
        for t in ('00', 'abc', '0'):
            out = TextCleaner.cleanup(t, op)
            if '\n' in out and '\n' not in t:
                die(f'{op} introduced a newline into {t!r} -> {out!r} '
                    f'(a string reached _join_lines where a list belongs)')
    ok('no operation splits a single line into characters')

    # REMOVE_DUPLICATE_LINES is excluded: collapsing duplicate blank lines is
    # its job, so a reduced line count there is correct, not loss.
    preserving = [o for o in ops if o is not OP.REMOVE_DUPLICATE_LINES]
    lost = [(op, t) for op in preserving for t in ('a\n\n', 'a\nb\n\n', '\n\n')
            if len(TextCleaner.cleanup(t, op).splitlines()) != len(t.splitlines())]
    if lost:
        die(f'still losing lines: {lost[:6]}')
    ok(f'no trailing blank line lost across {len(preserving)} line-preserving ops')

    print(f"{DIM}    hypothesis, 12 seeds on the property suite ...{OFF}")
    fails = []
    for seed in range(12):
        r = sh([sys.executable, '-m', 'pytest', 'tests/test_properties.py',
                '-q', '--benchmark-disable', f'--hypothesis-seed={seed}'])
        if r.returncode != 0:
            fails.append(seed)
    if fails:
        die(f'property suite still fails on seed(s) {fails}')
    ok('12/12 seeds pass (seed 0 was the original failure)')

    print(f"{DIM}    full pytest ...{OFF}")
    r = sh([sys.executable, '-m', 'pytest', 'tests/', '-q', '--benchmark-disable'])
    if r.returncode != 0:
        print((r.stdout or '')[-2500:])
        die('pytest failed')
    ok(f"pytest: {(r.stdout or '').strip().splitlines()[-1]}")

    print(f"{DIM}    unittest ...{OFF}")
    r = sh([sys.executable, '-m', 'unittest', 'test_rnv_text_transformer'])
    if r.returncode != 0:
        print((r.stderr or '')[-2500:])
        die('unittest failed')
    line = [l for l in (r.stderr or '').splitlines() if l.startswith('Ran ')]
    ok(f"unittest: {line[0] if line else 'passed'} -- OK")

    print(f"\n{GREEN}{BOLD}Done.{OFF} Nothing committed — review with `git diff`.")
    warn('This changes OUTPUT for text with trailing blank lines: they are now '
         'kept.\n      That is the fix, but it is a behaviour change — worth its '
         'own commit,\n      separate from the colour work.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
