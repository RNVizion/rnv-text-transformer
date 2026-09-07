#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-text-transformer: correct the two values rnv-brand rev 27 registered
underneath this application while nobody was looking.

    python up.py             # apply, then verify
    python up.py --check     # rehearse: compose every edit, run every guard,
                             #           write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

HOW THIS WAS FOUND. Not by reading the file. Every application carries a
hand-written PINNED mirror of the register, and every test that would compare
that mirror against the real thing is guarded with

    pytest.importorskip('engine.brand')

rnv-brand ships no pyproject.toml, so it is not installable, so all 22 of
those checks across the five applications skip. Making it importable takes
about ninety seconds; doing that produces, immediately:

    FAILED  tests/test_brand_mirror.py::test_app_owned_values_are_not_register_values
        GREY_E0 = #e0e0e0 is APP["pressed-light"] in the register, but marked app-ramp
        GREY_F5 = #f5f5f5 is APP["surface-light-3"] in the register, but marked app-ramp

This application's light half was wired BEFORE rev 27 registered the light
surface ladder. The other four were wired against rev 31 this week and are
clean. The check that says so has never once run.

THE TWO NEED OPPOSITE ANSWERS. That is the substance of this script, and both
answers come from rulings this repository already carries.

  #f5f5f5 is painted by three keys -- 'bg', 'window_bg', 'label_bg' -- and
  every one is a light window, panel or label ground. That IS what
  APP["surface-light-3"] is. So GREY_F5 is RENAMED to APP_SURFACE_LIGHT_3 and
  reclassified as a register mirror, which is the same call rnv-color-picker,
  rnv-color-palette-manager and rnv-icon-builder all made this week.

  #e0e0e0 is painted by ONE key: the light scrollbar track. The register's
  pressed-light is an INTERACTION STATE and a groove is a resting surface, so
  the ramp name GREY_E0 is CORRECT and only the classification was wrong. It
  becomes a declared coincidence. utils/colors.py already carries exactly this
  ruling for GREY_EE, four lines above GREY_E0: "one value, two roles, and
  only one of them is the register's."

NO PIXEL MOVES. Every value stays where it is. What changes is which name
points at it and which column of the provenance map it sits in -- and
therefore whether the next move of the light ladder reaches this application
or is silently ignored by it.

ONE TEST IS CORRECTED RATHER THAN DELETED. tests/test_app_mirror.py has

    def test_the_new_step_is_classified():
        assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp', (
            '... it is a ramp step, not a register value -- #e0e0e0 is no
            longer what the brand holds.')

The ASSERTION is still right and does not change. The REASON is now false:
rev 27 put #e0e0e0 back in the register as pressed-light, so the brand does
hold it. The classification survives on a different and better ground -- the
role, not the value -- and the message is rewritten to say so.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-text-transformer"
SENTINEL_FILE = "utils/colors.py"
SENTINEL = "RNV-TT-REGISTER"
GUARD = "tests/test_tt_register.py"
DESCRIPTION = "correct the two values rev 27 registered under this app"
SUITES = [("pytest tests/",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("the root unittest file",
           [sys.executable, "-m", "pytest", "test_rnv_text_transformer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=180"])]

#: Basenames this script must never be run AS -- copying it over one of these
#: shadows the module it is meant to edit.
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py",
           "dialog_styles.py"}

GUARD_SOURCE = r'''"""RNV-TT-REGISTER-GUARD -- the two values rev 27 registered under this app.

Installed 2026-09-07. It exists because of how the fault it fixes was found:
not by anybody reading the file, but by making `engine.brand` importable and
letting a test that had never run say what it had always been going to say.

    GREY_E0 = #e0e0e0 is APP["pressed-light"] in the register, but marked app-ramp
    GREY_F5 = #f5f5f5 is APP["surface-light-3"] in the register, but marked app-ramp

Both values were app-owned neutrals when this application's light half was
wired. rnv-brand rev 27 registered the light surface ladder underneath them
and nothing here noticed, because the only check that compares this app to the
register is guarded with importorskip and rnv-brand is not installable.

The two need OPPOSITE answers, and that is the whole point of this guard:

  * #f5f5f5 is painted by three keys and every one of them is a light window,
    panel or label ground -- which IS what APP["surface-light-3"] is. So the
    constant becomes a register mirror under the register's name.

  * #e0e0e0 is painted by ONE key, the light scrollbar track. The register's
    pressed-light is an INTERACTION STATE and a groove is a resting surface,
    so the ramp name is right and only the classification was wrong. It is a
    declared coincidence, not a mirror -- the same ruling this file already
    carries for GREY_EE / APP_HOVER_LIGHT four lines above it.

These tests do NOT need rnv-brand to be importable. That is deliberate: the
whole failure mode was a check that only runs somewhere else.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = Path(__file__).resolve().parent.parent
COLORS = ROOT / 'utils/colors.py'
STYLES = ROOT / 'utils/dialog_styles.py'
LIGHT = DialogStyleManager.LIGHT
DARK = DialogStyleManager.DARK


def test_the_light_ground_is_a_register_mirror_now():
    """#f5f5f5 under the register's own key, classified as the register's."""
    assert colors.APP_SURFACE_LIGHT_3 == '#f5f5f5'
    assert colors.PROVENANCE.get('APP_SURFACE_LIGHT_3') == 'register', (
        'APP_SURFACE_LIGHT_3 is not classified as a register value. It is '
        'APP["surface-light-3"], registered by rnv-brand rev 27.')


def test_the_retired_ramp_name_is_gone():
    """GREY_F5 was the same value under a name that said this app owned it.
    A rename that leaves the old name behind has renamed nothing."""
    src = COLORS.read_text(encoding='utf-8')
    code = '\n'.join(l for l in src.splitlines() if not l.lstrip().startswith('#'))
    assert 'GREY_F5' not in code, 'GREY_F5 still exists in utils/colors.py'
    assert not hasattr(colors, 'GREY_F5')
    assert 'GREY_F5' not in colors.PROVENANCE
    assert 'GREY_F5' not in colors.__all__


@pytest.mark.parametrize('key', ['bg', 'window_bg', 'label_bg'])
def test_every_light_ground_reads_the_register_name(key):
    """Spelling, not only value. A literal or a retired name here cannot
    follow rev 27's ladder the next time it moves."""
    src = STYLES.read_text(encoding='utf-8')
    assert f"'{key}': APP_SURFACE_LIGHT_3," in src, (
        f'{key} does not read APP_SURFACE_LIGHT_3')
    assert LIGHT[key] == '#f5f5f5'


def test_the_light_track_keeps_the_ramp_name():
    """The other half, and the opposite answer. #e0e0e0 IS a register value
    now -- APP["pressed-light"] -- but this key is not a pressed state, so it
    keeps the ramp step. Wiring it to the register's name would claim an
    interaction role for a groove on the strength of a shared byte."""
    assert colors.GREY_E0 == '#e0e0e0'
    assert LIGHT['scrollbar_bg'] == colors.GREY_E0
    src = STYLES.read_text(encoding='utf-8')
    assert "'scrollbar_bg': GREY_E0," in src
    assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp'


def test_the_coincidence_is_declared_with_its_reason():
    """An exemption with no stated reason is indistinguishable from an
    oversight, and the next audit re-litigates it. This asserts the entry
    exists AND that it names the register role it coincides with."""
    from tests import test_brand_mirror as tbm
    assert 'GREY_E0' in tbm.COINCIDENT, (
        'GREY_E0 shares #e0e0e0 with APP["pressed-light"] and is deliberately '
        'NOT mirrored. Undeclared, that reads as a misclassification.')
    entry, why = tbm.COINCIDENT['GREY_E0']
    assert entry == 'APP["pressed-light"]'
    assert len(why) > 80, 'the reason is too short to be a reason'


def test_no_dark_entry_took_either_light_value():
    """Both values belong to the light half. A dark key holding one of them
    would be a mode leak, and this is cheap to assert while we are here."""
    strays = {k: v for k, v in DARK.items()
              if v in ('#f5f5f5', '#e0e0e0')}
    assert not strays, f'dark entries carrying a light surface: {strays}'


def test_the_ramp_is_still_ordered_by_byte():
    """This app names ramp steps by their byte so the ramp reads in order.
    Removing GREY_F5 must not have disturbed the rest."""
    names = re.findall(r'^(GREY_[0-9A-F]{2}): Final',
                       COLORS.read_text(encoding='utf-8'), re.M)
    values = [int(n[5:], 16) for n in names]
    assert values == sorted(values), f'the ramp is out of order: {names}'
    assert 'GREY_F5' not in names


def test_this_guard_can_see_what_it_checks():
    """Guard the guard. Every assertion above walks these two files and the
    two resolved palettes; if any of them stopped resolving, the rest would
    pass over nothing."""
    assert COLORS.exists() and STYLES.exists()
    assert len(LIGHT) > 20 and len(DARK) > 20
    assert len(colors.PROVENANCE) > 20
'''


# --------------------------------------------------------------- the rename
# GREY_F5 -> APP_SURFACE_LIGHT_3. The constant moves out of the ramp block and
# into the APP block, because it stops being a step this app owns and becomes
# a value the register owns. Anchored on APP_HOVER_LIGHT, its neighbour on the
# light ladder and the value it was registered beside.
APP_ANCHOR = "APP_HOVER_LIGHT: Final[str] = '#eeeeee'\n"

RAMP_LINE = "GREY_F5: Final[str] = '#f5f5f5'\n"

PROV_ANCHOR = "    'APP_HOVER_LIGHT': 'register',\n"
PROV_OLD = "    'GREY_F5': 'app-ramp',\n"
ALL_ANCHOR = "    'APP_HOVER_LIGHT',\n"
ALL_OLD = "    'GREY_F5',\n"

# --------------------------------------------------------- the GREY_E0 note
# Its docstring is not wrong, but it is out of date in a way that matters: it
# explains why #e0e0e0 stopped being APP["text"] and stops there, which reads
# as "the register does not hold this value" -- and since rev 27 it does.
E0_OLD = ("#: carrying a docstring that describes a different value into a "
          "mirror is how\n"
          "#: a wrong fact acquires the authority of a checked one.\n"
          "GREY_E0: Final[str] = '#e0e0e0'\n")
E0_NEW = ("#: carrying a docstring that describes a different value into a "
          "mirror is how\n"
          "#: a wrong fact acquires the authority of a checked one.\n"
          "#:\n"
          "#: RNV-TT-REGISTER (2026-09-07): THE REGISTER HOLDS #e0e0e0 AGAIN.\n"
          "#: rnv-brand rev 27 registered it as APP[\"pressed-light\"], and this\n"
          "#: constant STAYS a ramp step anyway. A pressed plate is an\n"
          "#: interaction state; this is a scrollbar track at rest, and one\n"
          "#: shared byte is not a shared role. Same ruling as GREY_EE two\n"
          "#: constants down. Declared in COINCIDENT in\n"
          "#: tests/test_brand_mirror.py, and asserted in both directions.\n"
          "GREY_E0: Final[str] = '#e0e0e0'\n")

# ------------------------------------------------------ the coincidence entry
COINCIDENT_ANCHOR = "COINCIDENT: dict[str, tuple[str, str]] = {\n"
COINCIDENT_ADD = (
    "    'GREY_E0': (\n"
    "        'APP[\"pressed-light\"]',\n"
    "        'grey(14) is not the only step doing two jobs. rnv-brand rev 27 '\n"
    "        'registered #e0e0e0 as the LIGHT PRESSED PLATE -- what a control '\n"
    "        'goes to while it is held down. This ramp step is one STATIC '\n"
    "        'surface: the light scrollbar track, which rnv-color-picker and '\n"
    "        'rnv-icon-builder both carry at the same value. A resting groove '\n"
    "        'is not an interaction state. If APP[\"pressed-light\"] moves this '\n"
    "        'must NOT follow it, which is why the hex is spelled by a ramp '\n"
    "        'name here rather than mirrored. FOUND 2026-09-07, by making '\n"
    "        'engine.brand importable and letting this file test itself.'),\n")

# ------------------------------------------- the test whose reason went stale
STALE_OLD = (
    "def test_the_new_step_is_classified():\n"
    "    assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp', (\n"
    "        'GREY_E0 has no provenance entry, or the wrong one. It is a ramp step, '\n"
    "        'not a register value -- #e0e0e0 is no longer what the brand holds.')\n")
STALE_NEW = (
    "def test_the_new_step_is_classified():\n"
    "    \"\"\"RNV-TT-REGISTER (2026-09-07): the assertion is unchanged and still\n"
    "    right; its REASON was wrong and is corrected here.\n"
    "\n"
    "    It used to say GREY_E0 is app-owned because '#e0e0e0 is no longer what\n"
    "    the brand holds'. That was true when it was written and stopped being\n"
    "    true at rnv-brand rev 27, which registered #e0e0e0 as\n"
    "    APP[\"pressed-light\"]. The classification survives on better ground:\n"
    "    not because the register lacks the value, but because this key does\n"
    "    not play the register's ROLE. A scrollbar track is a resting surface\n"
    "    and pressed-light is an interaction state.\n"
    "\n"
    "    A test that passes for a reason that has quietly become false is worth\n"
    "    less than one that fails, because nobody re-reads a green test.\"\"\"\n"
    "    assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp', (\n"
    "        'GREY_E0 has no provenance entry, or the wrong one. The register '\n"
    "        'DOES hold #e0e0e0 -- APP[\"pressed-light\"] since rev 27 -- and this '\n"
    "        'is still a ramp step, because the light scrollbar track is a '\n"
    "        'resting surface and not a pressed state. Declared in COINCIDENT '\n"
    "        'in tests/test_brand_mirror.py.')\n")

DOC = ('#: engine/brand.py APP["surface-light-3"]. The light window, panel and\n'
       '#: label ground -- what a dialog sits on in light mode.\n'
       '#:\n'
       '#: RNV-TT-REGISTER (2026-09-07): WAS GREY_F5, A RAMP STEP. rnv-brand\n'
       '#: rev 27 registered the light surface ladder and this value with it,\n'
       '#: and this application did not follow, because the check that compares\n'
       '#: it to the register is guarded with importorskip and rnv-brand is not\n'
       '#: installable. It kept a name saying the app owned it for four\n'
       '#: revisions of the register owning it.\n'
       '#:\n'
       '#: Every key that reads it is a surface -- \'bg\', \'window_bg\',\n'
       '#: \'label_bg\' -- so unlike GREY_E0 below there is nothing to split.\n'
       'APP_SURFACE_LIGHT_3: Final[str] = \'#f5f5f5\'\n')

# (file, old, new, count)
EDITS = [
    ("utils/__init__.py", "    GREY_F5,\n", "", 1),
    ("utils/__init__.py", "    APP_HOVER_LIGHT,\n",
     "    APP_HOVER_LIGHT,\n    APP_SURFACE_LIGHT_3,\n", 1),
    ("utils/__init__.py", "    'GREY_F5',\n", "", 1),
    ("utils/__init__.py", "    'APP_HOVER_LIGHT',\n",
     "    'APP_HOVER_LIGHT',\n    'APP_SURFACE_LIGHT_3',\n", 1),
    ("utils/dialog_styles.py", "    GREY_F5,\n", "", 1),
    ("utils/dialog_styles.py", "    APP_HOVER_LIGHT,\n",
     "    APP_HOVER_LIGHT,\n    APP_SURFACE_LIGHT_3,\n", 1),
    ("utils/dialog_styles.py", "'bg': GREY_F5,", "'bg': APP_SURFACE_LIGHT_3,", 1),
    ("utils/dialog_styles.py", "'window_bg': GREY_F5,",
     "'window_bg': APP_SURFACE_LIGHT_3,", 1),
    ("utils/dialog_styles.py", "'label_bg': GREY_F5,",
     "'label_bg': APP_SURFACE_LIGHT_3,", 1),
    ("tests/test_brand_mirror.py", COINCIDENT_ANCHOR,
     COINCIDENT_ANCHOR + COINCIDENT_ADD, 1),
    ("tests/test_app_mirror.py", STALE_OLD, STALE_NEW, 1),
]


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)

    # --- 1. the constant moves from the ramp block to the APP block.
    if src.count(RAMP_LINE) != 1 or src.count(APP_ANCHOR) != 1:
        raise SystemExit(f"{SENTINEL_FILE}: GREY_F5 or the APP_HOVER_LIGHT "
                         f"anchor is not where this script expects it")
    if re.search(r"^APP_SURFACE_LIGHT_3\b", src, re.M):
        raise SystemExit("APP_SURFACE_LIGHT_3 already exists")
    src = src.replace(RAMP_LINE, "", 1)
    src = src.replace(APP_ANCHOR, APP_ANCHOR + "\n" + DOC, 1)

    # --- 2. provenance: out of app-ramp, into register.
    for old in (PROV_OLD, ALL_OLD):
        if src.count(old) != 1:
            raise SystemExit(f"expected one {old.strip()!r}, found {src.count(old)}")
    src = src.replace(PROV_OLD, "", 1)
    src = src.replace(PROV_ANCHOR, PROV_ANCHOR
                      + "    'APP_SURFACE_LIGHT_3': 'register',\n", 1)
    src = src.replace(ALL_OLD, "", 1)
    src = src.replace(ALL_ANCHOR, ALL_ANCHOR + "    'APP_SURFACE_LIGHT_3',\n", 1)

    # --- 3. GREY_E0's docstring, which stopped being true at rev 27.
    if src.count(E0_OLD) != 1:
        raise SystemExit("the GREY_E0 docstring is not where this script expects it")
    src = src.replace(E0_OLD, E0_NEW, 1)

    tree.write(SENTINEL_FILE, src)

    # --- 4. the callers, the exports, the coincidence, the stale reason.
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)

    print("  GREY_F5 -> APP_SURFACE_LIGHT_3 (register mirror), 3 call sites")
    print("  GREY_E0 stays a ramp step, declared coincident with "
          "APP[\"pressed-light\"]")
    print("  one test's REASON corrected; its assertion unchanged")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)

    # the rename is complete, in code -- comments may still mention the old
    # name, and should, because they explain the move.
    code = "\n".join(l for l in src.splitlines()
                     if not l.lstrip().startswith("#"))
    if "GREY_F5" in code:
        raise SystemExit("GREY_F5 survives in code in utils/colors.py")
    if "APP_SURFACE_LIGHT_3: Final[str] = '#f5f5f5'" not in src:
        raise SystemExit("APP_SURFACE_LIGHT_3 did not land as #f5f5f5")

    # the ramp is still ordered by byte, which is what this app asserts about
    # its own ramp -- removing a step must not disturb the rest.
    names = re.findall(r"^(GREY_[0-9A-F]{2}): Final", src, re.M)
    values = [int(n[5:], 16) for n in names]
    if values != sorted(values):
        raise SystemExit(f"the ramp is out of order after the removal: {names}")

    # provenance says register, exactly once, and the old entry is gone
    if "'APP_SURFACE_LIGHT_3': 'register'," not in src:
        raise SystemExit("APP_SURFACE_LIGHT_3 is not classified as register")
    if "'GREY_F5'" in src:
        raise SystemExit("a GREY_F5 entry survives in PROVENANCE or __all__")

    # every caller moved
    styles = tree.read("utils/dialog_styles.py")
    for key in ("bg", "window_bg", "label_bg"):
        if f"'{key}': APP_SURFACE_LIGHT_3," not in styles:
            raise SystemExit(f"{key} does not read APP_SURFACE_LIGHT_3")
    if "GREY_F5" in styles:
        raise SystemExit("GREY_F5 survives in utils/dialog_styles.py")
    init = tree.read("utils/__init__.py")
    if "GREY_F5" in init:
        raise SystemExit("GREY_F5 survives in utils/__init__.py")
    for text, rel in ((styles, "utils/dialog_styles.py"), (init, "utils/__init__.py")):
        if "APP_SURFACE_LIGHT_3" not in text:
            raise SystemExit(f"{rel} does not import APP_SURFACE_LIGHT_3")

    # the scrollbar track did NOT move -- this is the half that stays
    if "'scrollbar_bg': GREY_E0," not in styles:
        raise SystemExit("the light scrollbar track no longer reads GREY_E0")

    # the coincidence is declared with a real reason
    mirror = tree.read("tests/test_brand_mirror.py")
    if "'GREY_E0': (" not in mirror or 'APP["pressed-light"]' not in mirror:
        raise SystemExit("GREY_E0 is not declared in COINCIDENT")

    # and the stale reason is gone
    app_mirror = tree.read("tests/test_app_mirror.py")
    if "#e0e0e0 is no longer what the brand holds" in app_mirror:
        raise SystemExit("the stale reason survives in tests/test_app_mirror.py")

    if SENTINEL not in src:
        raise SystemExit("the correction note did not land")
    print("  guards: rename complete, ramp still ordered, 3 call sites moved, "
          "track unmoved, coincidence declared, stale reason corrected")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""


KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
