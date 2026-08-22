#!/usr/bin/env python3
"""rnv-text-transformer -- the ruled light error red, a theme bypass, and deps.

WHAT THIS CHANGES

1. A LIGHT-MODE ERROR RED, DERIVED

       STATUS_ERROR        '#dc3545'                       register
       STATUS_ERROR_LIGHT  lighten(STATUS_ERROR, -20)      -> #c82131

   The LIGHT dialog palette's 'error' moves from STATUS_ERROR to
   STATUS_ERROR_LIGHT: 4.1528 -> 5.1811 on this app's #f5f5f5 dialog ground.
   It clears 4.5:1 down to #e8e8e8, the same coverage boundary
   BRAND_DARK_GOLD_DEEP publishes.

   Uniform per-channel holds hue at 354.25 degrees, for red as for gold.

2. A HARDCODED-DARK BYPASS, WHICH THIS CHANGE WOULD OTHERWISE TURN INTO A BUG

   ui/preset_dialog.py:115 paints the delete button with
   `DialogStyleManager.DARK['error']` -- the DARK palette, unconditionally,
   in both modes. It is the only colour access in StepEditorWidget, and the
   widget had no idea what theme it was in.

   Today that renders the same value in both modes, so nothing looks wrong.
   The moment light gets its own error red it becomes a real defect: light
   mode would paint #dc3545 on #f5f5f5 at 4.1528, the exact shortfall this
   pass exists to remove, on the one control that skipped the palette.

   StepEditorWidget now takes is_dark and reads get_colors(is_dark). The
   default is True, so the four existing tests that construct it directly
   keep the behaviour they assert.

3. DARK IS SHORT, AND SAYS SO

   Dark error text reads 3.8441 on #1a1a1a and 3.1703 on #2a2a2a. Per the
   ruling, dark keeps its value -- the other apps' dark reds pass and are not
   worth replacing for uniformity. This app's does not, so the shortfall is
   recorded as a TWO-WAY exemption: the test fails if it regresses AND fails
   if it ever clears, so whoever fixes it is told to delete the exemption
   rather than leave a standing note about a solved problem.

   That shape is not decorative. It is exactly how rnv-color-picker's light
   shortfall got retired in this same pass instead of being forgotten.

4. TEST DEPENDENCIES MOVE

       requirements-dev.txt  ->  tests/requirements-dev.txt

USE VS MENTION

   tests/test_logic_gap_fill.py says "(it is in requirements-dev)" as prose,
   with no path. It is not rewritten, and the sweep is scoped to the filename
   with its extension so prose like that cannot trip it.

USAGE

    python up.py --check     # dry run; every pass runs, nothing written
    python up.py             # apply
    python up.py --finish    # delete this script

Runs from the repository root. Safe to run twice.
"""

from __future__ import annotations

import os
import subprocess
import sys

COLORS = "utils/colors.py"
STYLES = "utils/dialog_styles.py"
PRESET = "ui/preset_dialog.py"
OLD_DEPS = "requirements-dev.txt"
NEW_DEPS = "tests/requirements-dev.txt"


# --------------------------------------------------------------------------
# 1. The colour
# --------------------------------------------------------------------------

ANCHOR = """#: engine/brand.py STATUS["error"]
STATUS_ERROR: Final[str] = '#dc3545'
"""

NEW_CONSTANT = '''
#: Derived. Error TEXT on a light dialog ground.
#:
#: No red carries text at 4.5:1 on a real light panel: STATUS_ERROR clears
#: only pure white, at 4.5275, and reads 4.1528 on this app's #f5f5f5 dialog
#: background. Light therefore spends a derivative on TEXT for exactly the
#: reason the gold does -- the fill and text jobs occupy non-overlapping
#: luminance bands.
#:
#: 5.1811 on #f5f5f5, 4.8685 on #eeeeee, 4.6100 on #e8e8e8 -- the same
#: coverage boundary BRAND_DARK_GOLD_DEEP publishes. Below #e8e8e8 red does
#: not carry text, which is a ruling rather than a gap.
#:
#: Derived, not written down, so it cannot orphan the way #c4a458 did when
#: the gold it was a tint of was retired. A uniform per-channel step holds
#: hue at 354.25 degrees, identical to STATUS_ERROR.
#:
#: DARK is deliberately not given one. See test_dark_error_text_is_short,
#: which records the shortfall in both directions.
STATUS_ERROR_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)   # -> #c82131
'''

COLOUR_EDITS = (
    (COLORS, ANCHOR, ANCHOR + NEW_CONSTANT, 1,
     "the derived light error red, beside the registered one"),
    (COLORS,
     "    'STATUS_ERROR': 'register',\n    # -- derived\n",
     "    'STATUS_ERROR': 'register',\n    # -- derived\n"
     "    'STATUS_ERROR_LIGHT': 'derived',\n", 1,
     "PROVENANCE -- test_brand_mirror asserts this covers every constant, "
     "in both directions"),
    (COLORS,
     "    'STATUS_ERROR',\n    'GOLD_HOVER',",
     "    'STATUS_ERROR',\n    'STATUS_ERROR_LIGHT',\n    'GOLD_HOVER',", 1,
     "__all__"),
)

# utils/dialog_styles.py -- DARK and LIGHT both read `'error': STATUS_ERROR`.
# Only the LIGHT one moves, and the two are distinguished by the line that
# follows: DARK's 'info' is BRAND_GOLD, LIGHT's is BRAND_DARK_GOLD_DEEP.
# Anchoring on that neighbour is what stops this rewriting both.
STYLE_EDIT = (
    STYLES,
    "        'error': STATUS_ERROR,\n"
    "        'warning': STATUS_WARNING,\n"
    "        'info': BRAND_DARK_GOLD_DEEP,",
    "        'error': STATUS_ERROR_LIGHT,\n"
    "        'warning': STATUS_WARNING,\n"
    "        'info': BRAND_DARK_GOLD_DEEP,",
    1,
    "LIGHT dialog palette -- anchored on the 'info' line beneath it, because "
    "the 'error' line alone is identical in both palettes",
)

# "STATUS_ERROR," appears three times in this file: once in the import block
# and once in each palette. Anchoring on the import's NEIGHBOURS is what keeps
# this from rewriting a palette entry -- the same class of mistake that once
# turned "color: X" into a match inside "background-color: X".
STYLE_IMPORT = (
    STYLES,
    "    STATUS_WARNING,\n    STATUS_ERROR,\n    GOLD_HOVER,",
    "    STATUS_WARNING,\n    STATUS_ERROR,\n    STATUS_ERROR_LIGHT,\n    GOLD_HOVER,",
    1,
    "import the new constant, anchored on the names either side of it",
)


# --------------------------------------------------------------------------
# 2. The theme bypass
# --------------------------------------------------------------------------

BYPASS_EDITS = (
    (PRESET,
     "    def __init__(self, step: PresetStep, parent: QWidget | None = None) -> None:\n"
     "        super().__init__(parent)\n"
     "        self.step = step\n",
     "    def __init__(self, step: PresetStep, parent: QWidget | None = None,\n"
     "                 *, is_dark: bool = True) -> None:\n"
     "        super().__init__(parent)\n"
     "        self.step = step\n"
     "        # Defaults to True so the existing callers and tests that build\n"
     "        # this widget directly keep the dark styling they assert. The\n"
     "        # dialog that owns it passes its own mode.\n"
     "        self._is_dark = is_dark\n", 1,
     "StepEditorWidget learns what theme it is in"),
    (PRESET,
     '        delete_btn.setStyleSheet(f"color: {DialogStyleManager.DARK[\'error\']};")',
     '        delete_btn.setStyleSheet(\n'
     '            f"color: {DialogStyleManager.get_colors(self._is_dark)[\'error\']};")',
     1,
     "the bypass reads the palette for its own mode"),
    (PRESET,
     "        widget = StepEditorWidget(step)",
     "        widget = StepEditorWidget(step, is_dark=self._is_dark)", 1,
     "PresetDialog hands down the mode it already knows"),
)


# --------------------------------------------------------------------------
# 3. Dependencies
# --------------------------------------------------------------------------

DEP_REWRITES = (
    (".github/workflows/tests.yml",
     "pip install -r requirements-dev.txt",
     "pip install -r tests/requirements-dev.txt", 2,
     "LIVE -- two jobs install it; both fail without this"),
    ("requirements.txt",
     "# For development and testing dependencies, see requirements-dev.txt",
     "# For development and testing dependencies, see tests/requirements-dev.txt",
     1, "DOCS"),
    ("README.md",
     "├── requirements.txt\n├── requirements-dev.txt\n",
     "├── requirements.txt\n", 1,
     "DOCS -- drop the root entry; the tree already lists tests/ below"),
    ("README.md",
     "├── tests/                         # Pytest suite\n"
     "│   ├── conftest.py                # Shared fixtures\n",
     "├── tests/                         # Pytest suite\n"
     "│   ├── requirements-dev.txt       # Test dependencies\n"
     "│   ├── conftest.py                # Shared fixtures\n", 1,
     "DOCS -- and list it where it now lives"),
)

SELF_REWRITES = (
    ("# Install with: pip install -r requirements-dev.txt",
     "# Install with: pip install -r tests/requirements-dev.txt",
     "its own install line would otherwise name a path that no longer exists"),
)

# This repository's dependency file carries no `-r` include. Recorded as a
# number rather than assumed, because a file that HAD one and silently lost
# it would make the resolve-check below pass vacuously.
EXPECTED_INCLUDES = 0

DEP_EXEMPT = {
    "tests/test_dependency_file_placement.py":
        "the guard; its job is to name the retired path",
}

# A tree diagram names a file by its basename and supplies the directory
# through indentation, so `│   ├── requirements-dev.txt` nested under `tests/`
# is CORRECT and must not be rewritten to `tests/requirements-dev.txt` -- that
# would render as tests/tests/requirements-dev.txt to a reader.
#
# Rather than loosening the sweep to let all such lines through, the one
# legitimate line is named here and asserted to exist. A blanket rule would
# also have let a genuine stale reference past.
DIAGRAM_LINES = {
    "README.md": "│   ├── requirements-dev.txt       # Test dependencies",
}


# --------------------------------------------------------------------------
# 3a. Snapshots -- re-baselined by hand, deliberately not regenerated
# --------------------------------------------------------------------------
#
# tests/__snapshots__/test_snapshots.ambr holds `#dc3545` FOUR times: twice
# in the dark snapshots, which must not move, and twice in the light ones,
# which must. `pytest --snapshot-update` would resolve all four at once and
# accept any OTHER drift that had crept in alongside -- which is the whole
# reason a snapshot exists.
#
# So each light occurrence is rewritten by hand, anchored on a neighbour that
# differs between the two palettes:
#
#   get_colors_light        `diff_removed_bg` is #f8d7da in light, #4d1a1a in dark
#   inline_styles_combined  `status(muted)` is #666666 in light, #888888 in dark
#
# If a dark value ever moves, these anchors stop matching and the run halts
# instead of quietly rewriting the wrong half.

SNAPSHOT = "tests/__snapshots__/test_snapshots.ambr"

SNAPSHOT_EDITS = (
    (SNAPSHOT,
     '    "diff_removed_bg": "#f8d7da",\n    "error": "#dc3545",',
     '    "diff_removed_bg": "#f8d7da",\n    "error": "#c82131",', 1,
     "get_colors_light -- anchored on the light-only diff_removed_bg above it"),
    (SNAPSHOT,
     "  status(error): color: #dc3545;\n"
     "  status(warning): color: #ffc107;\n"
     "  status(muted): color: #666666;",
     "  status(error): color: #c82131;\n"
     "  status(warning): color: #ffc107;\n"
     "  status(muted): color: #666666;", 1,
     "inline_styles_combined, light half -- anchored on the light-only "
     "status(muted) beneath it"),
)


# --------------------------------------------------------------------------
# 4. Guards
# --------------------------------------------------------------------------

GUARD_PATH = "tests/test_dependency_file_placement.py"

GUARD_SOURCE = r'''"""Test dependencies live at tests/requirements-dev.txt.

All six RNV repositories converge on that path. This file MENTIONS the
retired root-level path and is excluded from the sweep that forbids it --
the use/mention distinction.
"""

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
WANTED = REPO / "tests" / "requirements-dev.txt"
RETIRED_AT_ROOT = REPO / "requirements-dev.txt"

# Measured, not assumed. A file that had an include and silently lost it
# would make test_every_include_resolves pass vacuously.
EXPECTED_INCLUDES = 0

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".pytest_cache",
             "htmlcov", "scripts", ".benchmarks", ".hypothesis"}
MENTION_ONLY = {pathlib.Path(__file__).name}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                 ".cfg", ".sh", ".bat"}


def _is_delivery_script(path):
    if "scripts" in path.parts:
        return True
    return path.parent == REPO and path.name.startswith("up")


def _files():
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in MENTION_ONLY or _is_delivery_script(path):
            continue
        yield path


def test_the_dependency_file_is_where_it_belongs():
    assert WANTED.is_file(), f"{WANTED} is missing"
    assert not RETIRED_AT_ROOT.exists(), \
        "requirements-dev.txt is still at the repository root"


def test_the_moved_file_still_has_content():
    lines = [ln.strip() for ln in WANTED.read_text(encoding="utf-8").splitlines()]
    packages = [ln for ln in lines if ln and not ln.startswith("#")]
    assert len(packages) >= 3, f"only {len(packages)} requirements found"


def test_every_include_resolves():
    """pip resolves a `-r` include RELATIVE TO THE FILE THAT CONTAINS IT.

    A file moved from the root into tests/ with `-r requirements.txt` intact
    starts asking for tests/requirements.txt -- a file nobody ever wrote. No
    path assertion catches it; CI dies at pip-install time naming a file that
    appears nowhere in the repository. This happened in rnv-color-picker
    during the same pass.

    This repository's file has no include today, which is asserted as a
    number so the loop cannot go quietly empty.
    """
    includes = [ln.strip().split(None, 1)[1].strip()
                for ln in WANTED.read_text(encoding="utf-8").splitlines()
                if ln.strip().startswith("-r ")]
    for include in includes:
        target = (WANTED.parent / include).resolve()
        assert target.is_file(), (
            f"{WANTED.name} includes {include!r}, which resolves to {target} "
            f"and does not exist")
    assert len(includes) == EXPECTED_INCLUDES, (
        f"the file now has {len(includes)} -r include(s), not "
        f"{EXPECTED_INCLUDES}. If that is intended, update the constant -- "
        f"the loop above already checks each one resolves.")


# A tree diagram names a file by basename and supplies the directory through
# indentation, so this line -- nested under `tests/` -- is correct as written.
# Rewriting it to tests/requirements-dev.txt would read as tests/tests/... to
# anyone looking at the diagram. Named explicitly rather than waved through by
# a looser rule, and asserted to still exist below.
DIAGRAM_LINES = {
    "README.md": "│   ├── requirements-dev.txt       # Test dependencies",
}


def test_nothing_still_points_at_the_root_path():
    """Scoped to the filename WITH its extension, so prose that mentions
    'requirements-dev' without a path does not trip it."""
    needle = "requirements-dev.txt"
    offenders = []
    for path in _files():
        allowed = DIAGRAM_LINES.get(path.relative_to(REPO).as_posix())
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if needle not in line or "tests/" + needle in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            offenders.append(
                f"{path.relative_to(REPO).as_posix()}: {line.strip()}")
    assert not offenders, \
        "these still name the root path:\n  " + "\n  ".join(offenders)


def test_the_diagram_exemption_is_load_bearing():
    """Both directions. An exemption for a line that no longer exists is dead
    weight, and dead weight is a licence waiting for a future defect."""
    for rel, line in DIAGRAM_LINES.items():
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        assert line in text, (
            f"{rel} no longer contains the exempted diagram line "
            f"{line.strip()!r} -- remove it from DIAGRAM_LINES")


def test_that_sweep_is_actually_looking():
    walked = {p.relative_to(REPO).as_posix() for p in _files()}
    assert len(walked) > 20, f"the sweep only found {len(walked)} files"
    for required in ("README.md", "requirements.txt",
                     ".github/workflows/tests.yml"):
        assert required in walked, f"{required} is not being swept"


def test_the_mention_exemption_is_load_bearing():
    here = pathlib.Path(__file__)
    assert here.name in MENTION_ONLY
    assert "requirements-dev.txt" in here.read_text(encoding="utf-8"), \
        "this file no longer mentions the path -- drop the exemption"


def test_both_workflow_jobs_install_from_the_new_path():
    text = (REPO / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8")
    assert text.count("pip install -r tests/requirements-dev.txt") == 2, (
        "both jobs must install from the new path; one of them was missed")
'''


ERROR_GUARD_PATH = "tests/test_error_red.py"

ERROR_GUARD_SOURCE = r'''"""The error red: one registered value, one derivative, and an honest gap.

    STATUS_ERROR        #dc3545   register -- fills, borders, dark text
    STATUS_ERROR_LIGHT  #c82131   derived  -- text on a light dialog ground

Dark is SHORT and is not fixed here. That is a decision, and the test which
records it fails in both directions so it cannot outlive the problem.
"""

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

TEXT_FLOOR = 4.5


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
             for x in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def test_the_light_error_red_is_derived_not_written():
    """A written-down derivative orphans the moment its base moves -- which
    is what happened to #c4a458 when the gold it tinted was retired."""
    assert colors.STATUS_ERROR_LIGHT == colors.lighten(colors.STATUS_ERROR, -20)
    assert colors.STATUS_ERROR_LIGHT != colors.STATUS_ERROR


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])
def test_light_error_text_carries_to_the_published_boundary(ground):
    """#e8e8e8 is where the gold stops carrying text. The red is derived to
    the same boundary so the two rules need not be remembered separately."""
    ratio = contrast(colors.STATUS_ERROR_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_LIGHT} on {ground} = {ratio:.4f}"


def test_the_light_dialog_palette_uses_the_derivative():
    light = DialogStyleManager.get_colors(False)
    assert light["error"] == colors.STATUS_ERROR_LIGHT
    assert contrast(light["error"], light["bg"]) >= TEXT_FLOOR


def test_the_dark_dialog_palette_still_uses_the_register_value():
    """Dark is not touched by this pass. Asserted so a later change cannot
    move it quietly while nobody is looking at dark."""
    dark = DialogStyleManager.get_colors(True)
    assert dark["error"] == colors.STATUS_ERROR


def test_dark_error_text_is_short_and_that_is_recorded():
    """A TWO-WAY exemption.

    Dark error text reads 3.8441 on #1a1a1a and 3.1703 on #2a2a2a. The ruling
    of this pass left dark alone: the other apps' dark reds pass on their
    grounds and replacing a colour that is not broken to buy uniformity is a
    bigger change than the problem justifies. This app's dark red does NOT
    pass, so the gap is written down rather than left to be rediscovered.

    The second assertion is the important half. If a dark derivative is ever
    ruled -- lighten(STATUS_ERROR, +32) = #fc5565 is the natural candidate,
    5.4918 on #1a1a1a and 4.5291 on #2a2a2a -- this test goes red and tells
    whoever did it to delete the exemption. An exemption that outlives its
    problem is a licence waiting for a future defect.
    """
    dark = DialogStyleManager.get_colors(True)
    for ground, measured in (("#1a1a1a", 3.8441), ("#2a2a2a", 3.1703)):
        ratio = contrast(dark["error"], ground)
        assert ratio >= measured - 0.0001, (
            f"dark error text regressed to {ratio:.4f} on {ground}, below the "
            f"{measured} recorded when this exemption was written")
        assert ratio < TEXT_FLOOR, (
            f"dark error text now measures {ratio:.4f} on {ground} and CLEARS "
            f"the floor. A dark error red has presumably been ruled -- delete "
            f"this test and its exemption rather than leaving a standing note "
            f"about a problem that no longer exists.")


def test_the_delete_button_reads_the_palette_for_its_own_mode(qtbot):
    """The bypass this pass removed.

    ui/preset_dialog.py painted the delete button from DialogStyleManager.DARK
    unconditionally. It rendered the same value in both modes only because
    light and dark shared one error red; giving light its own turned it into
    a real defect on the one control that skipped the palette.
    """
    from core.preset_manager import PresetStep
    from ui.preset_dialog import StepEditorWidget

    step = PresetStep(action="uppercase")
    for is_dark, expected in ((True, colors.STATUS_ERROR),
                              (False, colors.STATUS_ERROR_LIGHT)):
        widget = StepEditorWidget(step, is_dark=is_dark)
        qtbot.addWidget(widget)
        sheets = [child.styleSheet() for child in widget.findChildren(object)
                  if hasattr(child, "styleSheet")]
        assert any(expected in sheet for sheet in sheets), (
            f"is_dark={is_dark}: no child carries {expected}")
'''


# --------------------------------------------------------------------------
# Machinery
# --------------------------------------------------------------------------

class Halt(SystemExit):
    pass


def _this_script() -> str:
    return os.path.relpath(os.path.realpath(__file__),
                           os.path.realpath(os.getcwd())).replace(os.sep, "/")


class Tree:
    SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "scripts",
                 ".pytest_cache", "htmlcov", ".benchmarks", ".hypothesis"}
    TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                     ".cfg", ".sh", ".bat"}

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.dirty: set[str] = set()

    def get(self, path: str) -> str:
        if path not in self.files:
            with open(path, "r", encoding="utf-8") as handle:
                self.files[path] = handle.read()
        return self.files[path]

    def sweep_text(self, path: str) -> str:
        if path in self.files:
            return self.files[path]
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def set(self, path: str, text: str) -> None:
        self.files[path] = text
        self.dirty.add(path)

    def texts(self):
        me = _this_script()
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for name in sorted(names):
                if os.path.splitext(name)[1] not in self.TEXT_SUFFIXES:
                    continue
                path = os.path.relpath(os.path.join(root, name),
                                       ".").replace(os.sep, "/")
                if path != me:
                    yield path

    def flush(self) -> int:
        for path in sorted(self.dirty):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.files[path])
        return len(self.dirty)


def git(*args: str) -> str:
    result = subprocess.run(("git",) + args, capture_output=True, text=True)
    if result.returncode:
        raise Halt(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def lighten(value: str, step: int) -> str:
    h = value.lstrip("#")
    channels = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return "#" + "".join(f"{max(0, min(255, c + step)):02x}" for c in channels)


def contrast(a: str, b: str) -> float:
    def lum(value: str) -> float:
        h = value.lstrip("#")
        parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
                 for x in parts]
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]
    first, second = sorted((lum(a), lum(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


ALL_EDITS = (COLOUR_EDITS + (STYLE_IMPORT, STYLE_EDIT) + BYPASS_EDITS
             + SNAPSHOT_EDITS + DEP_REWRITES)


def already_done() -> bool:
    if os.path.exists(COLORS) and "STATUS_ERROR_LIGHT" in open(
            COLORS, encoding="utf-8").read():
        print("Already applied -- utils/colors.py defines STATUS_ERROR_LIGHT.")
        print("Nothing to do. This is the idempotent exit, not an error.")
        return True
    return False


def check_fingerprint(tree: Tree) -> None:
    problems = []
    for path, old, _new, expected, why in ALL_EDITS:
        if not os.path.exists(path):
            problems.append(f"  {path} does not exist")
            continue
        count = tree.sweep_text(path).count(old)
        if count != expected:
            problems.append(
                f"  {path}: expected {expected} occurrence(s) of "
                f"{old.splitlines()[0].strip()[:58]!r}, found {count}\n"
                f"      ({why})")
    if not os.path.exists(OLD_DEPS):
        problems.append(f"  {OLD_DEPS} is not at the repository root")
    if os.path.exists(NEW_DEPS):
        problems.append(f"  {NEW_DEPS} already exists")
    if problems:
        raise Halt("This is not the tree this script was written against:\n"
                   + "\n".join(problems)
                   + "\n\nRun it from the root of a clean checkout of main.")


def apply_edits(tree: Tree, edits, heading: str) -> None:
    print(heading)
    for path, old, new, expected, why in edits:
        src = tree.get(path)
        tree.set(path, src.replace(old, new, expected))
        print(f"  {path}: {why}")


def assert_no_dep_reference_was_missed(tree: Tree) -> None:
    listed = {path for path, _o, _n, _c, _w in DEP_REWRITES}
    exempt = set(DEP_EXEMPT) | {OLD_DEPS, GUARD_PATH}
    unaccounted = []
    for path in tree.texts():
        if path in listed or path in exempt:
            continue
        for line in tree.sweep_text(path).splitlines():
            if "requirements-dev.txt" in line:
                unaccounted.append(f"{path}: {line.strip()}")
    if unaccounted:
        raise Halt(
            "These name the dependency file but are in neither the rewrite\n"
            "list nor the exemption list. Each is either a rewrite this\n"
            "script is missing or a deliberate exemption -- decide which:\n  "
            + "\n  ".join(unaccounted))
    print(f"  every file naming the dependency path is accounted for "
          f"({len(listed)} to rewrite)")


def move_the_deps(tree: Tree, dry: bool) -> None:
    body = tree.get(OLD_DEPS)
    includes = [ln for ln in body.splitlines() if ln.strip().startswith("-r ")]
    if len(includes) != EXPECTED_INCLUDES:
        raise Halt(
            f"{OLD_DEPS} has {len(includes)} `-r` include(s), expected "
            f"{EXPECTED_INCLUDES}. pip resolves an include relative to the "
            f"file that holds it, so each one needs a `../` prefix after this "
            f"move. Refusing to move it blind.")
    for old_line, new_line, why in SELF_REWRITES:
        if old_line not in body:
            raise Halt(f"{OLD_DEPS} does not contain {old_line!r}\n  ({why})")
        body = body.replace(old_line, new_line, 1)
    tree.set(NEW_DEPS, body)
    if not dry:
        git("mv", OLD_DEPS, NEW_DEPS)
    print(f"  {OLD_DEPS} -> {NEW_DEPS}  (git mv; {EXPECTED_INCLUDES} includes "
          f"to re-anchor)")


def install_guards(tree: Tree) -> None:
    tree.set(GUARD_PATH, GUARD_SOURCE)
    tree.set(ERROR_GUARD_PATH, ERROR_GUARD_SOURCE)
    print(f"  {GUARD_PATH}: {len(GUARD_SOURCE.splitlines())} lines")
    print(f"  {ERROR_GUARD_PATH}: {len(ERROR_GUARD_SOURCE.splitlines())} lines")


def verify(tree: Tree) -> None:
    problems = []
    derived = lighten("#dc3545", -20)
    if derived != "#c82131":
        problems.append(f"the derivation gives {derived}, expected #c82131")
    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
        ratio = contrast(derived, ground)
        if ratio < 4.5:
            problems.append(f"{derived} on {ground} = {ratio:.4f}")

    colours = tree.get(COLORS)
    if "STATUS_ERROR_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)" not in colours:
        problems.append("the derivative is not computed from the base")
    if "'STATUS_ERROR_LIGHT': 'derived'," not in colours:
        problems.append("PROVENANCE has no entry for the new constant")
    if colours.count("'STATUS_ERROR_LIGHT',") != 1:
        problems.append("__all__ does not export the new constant exactly once")

    styles = tree.get(STYLES)
    if styles.count("'error': STATUS_ERROR_LIGHT,") != 1:
        problems.append("exactly one palette must use the derivative")
    if styles.count("'error': STATUS_ERROR,") != 1:
        problems.append("dark must still use the registered value")

    snapshot = tree.get(SNAPSHOT)
    if snapshot.count("#c82131") != 2:
        problems.append(
            f"expected exactly 2 light snapshot values, found "
            f"{snapshot.count('#c82131')}")
    if snapshot.count("#dc3545") != 2:
        problems.append(
            f"expected the 2 DARK snapshot values to survive untouched, found "
            f"{snapshot.count('#dc3545')}")

    preset = tree.get(PRESET)
    if "DialogStyleManager.DARK['error']" in preset:
        problems.append("the hardcoded-dark bypass is still present")
    if "StepEditorWidget(step, is_dark=self._is_dark)" not in preset:
        problems.append("the dialog does not pass its mode down")

    swept = 0
    for path in tree.texts():
        if path in DEP_EXEMPT or path in (OLD_DEPS, NEW_DEPS):
            continue
        swept += 1
        allowed = DIAGRAM_LINES.get(path)
        for line in tree.sweep_text(path).splitlines():
            if "requirements-dev.txt" not in line:
                continue
            if "tests/requirements-dev.txt" in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            problems.append(f"{path} still names the root path: {line.strip()}")
    if swept < 20:
        problems.append(f"the sweep visited only {swept} files; it is not looking")

    # The diagram exemption asserted in the other direction: if the line it
    # protects is gone, the exemption protects nothing and is dead weight.
    for path, line in DIAGRAM_LINES.items():
        if line not in tree.get(path):
            problems.append(
                f"{path} no longer contains the exempted diagram line "
                f"{line.strip()!r}; remove it from DIAGRAM_LINES")

    body = tree.get(NEW_DEPS)
    packages = [ln for ln in (l.strip() for l in body.splitlines())
                if ln and not ln.startswith("#")]
    if len(packages) < 3:
        problems.append(f"the moved file holds only {len(packages)} requirements")

    if problems:
        raise Halt("VERIFY FAILED -- nothing was written:\n  "
                   + "\n  ".join(problems))
    print(f"  verify: {derived} clears 4.5 to #e8e8e8; dark untouched; bypass "
          f"gone;")
    print(f"    {swept} files swept; {len(packages)} requirements intact")


def finish() -> None:
    here = os.path.abspath(__file__)
    os.remove(here)
    print(f"Removed {here}")


def main() -> int:
    if "--finish" in sys.argv:
        finish()
        return 0

    dry = "--check" in sys.argv

    if not os.path.isdir(".git"):
        raise Halt("run this from the repository root (.git not found)")
    if already_done():
        return 0

    tree = Tree()
    check_fingerprint(tree)

    print("DRY RUN -- every pass runs, nothing is written\n" if dry
          else "Applying\n")

    apply_edits(tree, COLOUR_EDITS, "1. the derived light error red")
    apply_edits(tree, (STYLE_IMPORT, STYLE_EDIT),
                "\n2. the LIGHT dialog palette")
    apply_edits(tree, BYPASS_EDITS,
                "\n3. the hardcoded-dark bypass this change would have broken")
    apply_edits(tree, SNAPSHOT_EDITS,
                "\n3a. snapshots -- the two LIGHT occurrences only")

    print("\n4. dependencies")
    assert_no_dep_reference_was_missed(tree)
    move_the_deps(tree, dry)
    apply_edits(tree, DEP_REWRITES, "   references:")

    print("\n5. guards")
    install_guards(tree)

    print("\n6. verify the pending tree")
    verify(tree)

    if dry:
        print(f"\nDry run complete. {len(tree.dirty)} files would change; "
              f"none were written. The git mv did not run.")
        return 0

    written = tree.flush()
    print(f"\n7. wrote {written} files")

    print("\nDone. Now run, from the repository root:")
    print("    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q")
    print("    QT_QPA_PLATFORM=offscreen python -m unittest "
          "test_rnv_text_transformer")
    print(f"\nThen, once green:  python {_this_script()} --finish")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Halt as stop:
        print(f"\n{stop}", file=sys.stderr)
        sys.exit(1)
