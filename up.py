#!/usr/bin/env python3
"""
RNV-NAMING-TOOL-DO-NOT-SWEEP

A constant names a COLOUR. A key names a ROLE. Apply that to the twenty
values this application owns outright.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

Chris, reading the colour tree on 2026-09-02:

    "_DRAG_HIGHLIGHT_GOLD reads as a constant but it should read as a key --
     the constant should denote the colour, as that is what will change to
     affect the rest of the app elements, not the keys."

That is the naming half of rule 1. Rule 1 says every literal lives in one
file and everything else wires through a constant; this says what the
constant is allowed to be CALLED. A name that answers both questions at once
is a role frozen to a colour, and a future brand swap cannot flow through it,
because the thing that should change and the thing that should not are the
same identifier.

THE RULING ON THIS APPLICATION'S TWENTY (2026-09-02)

The diff and regex colours have no brand name, because the brand has no
greens or purples. Two patterns were rendered side by side and Chris ruled:

    A  hue + shade      GREEN_DEEP, GREEN_PALE ...
    B  meaning          SEMANTIC_DIFF_ADDED, SEMANTIC_DIFF_ADDED_LIGHT   <-- ruled

These are not decorative colours that happen to be green. They carry MEANING:
added, removed, changed, current, matched. If a future RNV app puts purple
where gold sits, its "removed" is still red -- the accent swap must not reach
them. The register already names exactly this category by meaning rather than
hue (STATUS = success / warning / error) and already handles the two grounds
the same way: STATUS_ERROR is the base, STATUS_ERROR_LIGHT the light variant.
This file's own PROVENANCE map has classified all of them 'app-semantic'
since the mirror was built. The category existed in the code; it had no name.

So the _DARK suffix goes (the register writes the base unsuffixed), _LIGHT
stays, and SEMANTIC_ says which category it is:

    DIFF_ADDED_DARK       ->  SEMANTIC_DIFF_ADDED
    DIFF_REMOVED_DARK     ->  SEMANTIC_DIFF_REMOVED
    DIFF_CHANGED_DARK     ->  SEMANTIC_DIFF_CHANGED
    DIFF_CURRENT_DARK     ->  SEMANTIC_DIFF_CURRENT
    DIFF_ADDED_LIGHT      ->  SEMANTIC_DIFF_ADDED_LIGHT
    DIFF_REMOVED_LIGHT    ->  SEMANTIC_DIFF_REMOVED_LIGHT
    DIFF_CHANGED_LIGHT    ->  SEMANTIC_DIFF_CHANGED_LIGHT
    DIFF_CURRENT_LIGHT    ->  SEMANTIC_DIFF_CURRENT_LIGHT
    REGEX_MATCH_DARK      ->  SEMANTIC_REGEX_MATCH
    REGEX_MATCH_LIGHT     ->  SEMANTIC_REGEX_MATCH_LIGHT
    REGEX_GROUP_PALETTE   ->  SEMANTIC_REGEX_GROUPS

NO PIXEL MOVES. Every value is unchanged and the guard pins all twenty. This
is a rename plus one literal moved into the palette.

ALSO HERE -- the class C member, and one stray literal

    _DRAG_HIGHLIGHT_GOLD  ->  _DRAG_HIGHLIGHT     (ui/drag_drop_text_edit.py)

The derivation stays exactly as it is -- with_alpha(BRAND_GOLD, 0xBF) -- so
the colour still comes from the constant. Only the name stops naming it, and
a purple brand can now flow through the same line. The guard reads the
assignment with ast and asserts it is still a call to with_alpha on
BRAND_GOLD, so a later hand-edit to a literal fails rather than passes.

Two lines below it, the same style block wrote color: #000000 as a raw
literal -- the one rule-1 stray left in this application. It becomes
TRUE_BLACK in the same pass.
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
DESCRIPTION = "rename the app-semantic constants and free the drag highlight"
SENTINEL_FILE = "utils/colors.py"
SENTINEL = "RNV-SEMANTIC-NAMING"
GUARD = "tests/test_semantic_naming.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]

RENAMES = [('DIFF_ADDED_DARK', 'SEMANTIC_DIFF_ADDED'), ('DIFF_REMOVED_DARK', 'SEMANTIC_DIFF_REMOVED'), ('DIFF_CHANGED_DARK', 'SEMANTIC_DIFF_CHANGED'), ('DIFF_CURRENT_DARK', 'SEMANTIC_DIFF_CURRENT'), ('DIFF_ADDED_LIGHT', 'SEMANTIC_DIFF_ADDED_LIGHT'), ('DIFF_REMOVED_LIGHT', 'SEMANTIC_DIFF_REMOVED_LIGHT'), ('DIFF_CHANGED_LIGHT', 'SEMANTIC_DIFF_CHANGED_LIGHT'), ('DIFF_CURRENT_LIGHT', 'SEMANTIC_DIFF_CURRENT_LIGHT'), ('REGEX_MATCH_DARK', 'SEMANTIC_REGEX_MATCH'), ('REGEX_MATCH_LIGHT', 'SEMANTIC_REGEX_MATCH_LIGHT'), ('REGEX_GROUP_PALETTE', 'SEMANTIC_REGEX_GROUPS')]
SWEEP = ('utils/colors.py', 'utils/__init__.py', 'utils/dialog_styles.py', 'tests/test_brand_mirror.py')
VALUES = {'SEMANTIC_DIFF_ADDED': '#1a4d1a', 'SEMANTIC_DIFF_REMOVED': '#4d1a1a', 'SEMANTIC_DIFF_CHANGED': '#4d4d1a', 'SEMANTIC_DIFF_CURRENT': '#4d1a4d', 'SEMANTIC_DIFF_ADDED_LIGHT': '#d4edda', 'SEMANTIC_DIFF_REMOVED_LIGHT': '#f8d7da', 'SEMANTIC_DIFF_CHANGED_LIGHT': '#fff3cd', 'SEMANTIC_DIFF_CURRENT_LIGHT': '#e2d4f0', 'SEMANTIC_REGEX_MATCH': '#4a4a00', 'SEMANTIC_REGEX_MATCH_LIGHT': '#ffff99'}
GROUPS = ('#3d5c5c', '#5c3d5c', '#5c5c3d', '#3d5c3d', '#5c3d3d', '#3d3d5c', '#5c4d3d', '#3d5c4d')

DRAG_FILE = "ui/drag_drop_text_edit.py"

OLD_DRAG = """\
    # Drag highlight gold -- Qt #AARRGGBB, primary brand gold at 75% alpha.
    # Not a six-digit hex: the alpha channel comes first, so a plain
    # #[0-9a-f]{6} search will neither find it nor safely rewrite it.
    _DRAG_HIGHLIGHT_GOLD: str = with_alpha(BRAND_GOLD, 0xBF)
"""

NEW_DRAG = """\
    # RNV-SEMANTIC-NAMING (2026-09-02): this name used to end in the name of
    # the colour that fills it. A constant names a colour and a key names a
    # role; this is a role, so it no longer says which colour it holds. The
    # colour still arrives from BRAND_GOLD -- keep the derivation, drop the
    # claim -- so a brand that is not gold flows through this line unchanged.
    #
    # Qt #AARRGGBB, primary brand at 75% alpha. Not a six-digit hex: the
    # alpha channel comes first, so a plain #[0-9a-f]{6} search will neither
    # find it nor safely rewrite it.
    _DRAG_HIGHLIGHT: str = with_alpha(BRAND_GOLD, 0xBF)
"""

OLD_STYLE = """\
            border: 2px dashed {_DRAG_HIGHLIGHT_GOLD};
            background-color: {_DRAG_HIGHLIGHT_GOLD};
            color: #000000;
"""

NEW_STYLE = """\
            border: 2px dashed {_DRAG_HIGHLIGHT};
            background-color: {_DRAG_HIGHLIGHT};
            color: {TRUE_BLACK};
"""

OLD_IMPORT = "from utils.colors import BRAND_GOLD, with_alpha\n"
NEW_IMPORT = "from utils.colors import BRAND_GOLD, TRUE_BLACK, with_alpha\n"

NOTE = """\
# ============ APP SEMANTICS ============
#
# Neither brand values nor ramp steps, and named for what they MEAN rather
# than what hue they are -- the way the register names STATUS.
#
# RNV-SEMANTIC-NAMING (2026-09-02): the _DARK suffix is gone because the base
# carries the dark value, exactly as STATUS_ERROR / STATUS_ERROR_LIGHT do
# upstream. The accent swap must never reach these: a purple brand still
# deletes in red.
#
# Diff highlighting borrows the Bootstrap alert palette; the regex colours
# are this app alone.
"""

OLD_NOTE = """\
# ============ APP SEMANTICS ============
#
# Neither brand values nor ramp steps. Diff highlighting borrows the
# Bootstrap alert palette; the regex colours are this app alone.
"""


def _token_sub(text: str) -> tuple[str, int]:
    """One pass, longest name first, whole tokens only.

    Sequential passes would be wrong the moment one new name contains an old
    one. Word boundaries make the quoted forms in __all__ and PROVENANCE
    rename themselves, which is what makes those two maps stay complete.
    """
    pairs = sorted(RENAMES, key=lambda p: -len(p[0]))
    lookup = dict(pairs)
    pattern = re.compile(r"\b(%s)\b" % "|".join(re.escape(o) for o, _ in pairs))
    n = 0

    def swap(m):
        nonlocal n
        n += 1
        return lookup[m.group(1)]

    return pattern.sub(swap, text), n


def edits(tree) -> None:
    total = 0
    for rel in SWEEP:
        text = tree.read(rel)
        new, n = _token_sub(text)
        if n == 0:
            raise SystemExit(f"{rel} mentions none of the eleven names")
        tree.write(rel, new)
        total += n
        print(f"  {rel}: {n} occurrence(s) renamed")
    print(f"  {total} occurrence(s) across {len(SWEEP)} file(s)")

    tree.sub(SENTINEL_FILE, OLD_NOTE, NOTE, 1)
    tree.sub(DRAG_FILE, OLD_IMPORT, NEW_IMPORT, 1)
    tree.sub(DRAG_FILE, OLD_DRAG, NEW_DRAG, 1)
    tree.sub(DRAG_FILE, OLD_STYLE, NEW_STYLE, 1)
    print("  drag highlight freed, #000000 wired through TRUE_BLACK")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count(SENTINEL) != 1:
        raise SystemExit("the ruling note did not land exactly once")

    # Every old name gone from every file in the repository, not just the four
    # swept -- a name that survives somewhere unswept is an ImportError at run
    # time that no unit test necessarily reaches.
    root = Path(tree.root)
    strays = []
    for path in sorted(root.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"}
               for p in path.parts):
            continue
        if path.name in ("up.py", "up1.py", "up2.py"):
            continue
        # The buffered text where there is one -- otherwise --check would
        # read the untouched disk and report every rename as a failure.
        rel = str(path.relative_to(root))
        text = tree.files.get(rel)
        if text is None:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text or "RNV-SEMANTIC-GUARD" in text:
            continue
        for old, _ in RENAMES:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{path.relative_to(root)}: {old}")
    if strays:
        raise SystemExit("old names survived:\n  " + "\n  ".join(strays))

    # Values unchanged. Read them out of the source rather than importing, so
    # this runs before the suites do.
    tree_ast = ast.parse(src)
    found = {}
    for node in tree_ast.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                    found[t.id] = node.value.value
    for name, want in VALUES.items():
        if found.get(name) != want:
            raise SystemExit(f"{name} is {found.get(name)!r}, expected {want!r}")

    drag = tree.read(DRAG_FILE)
    if "_DRAG_HIGHLIGHT_GOLD" in drag:
        raise SystemExit("the old drag-highlight name survived")
    if "#000000" in drag:
        raise SystemExit("the raw black literal survived in " + DRAG_FILE)

    print(f"  guards: {len(RENAMES)} names renamed, "
          f"{len(VALUES)} values unmoved, drag highlight freed")


GUARD_SOURCE = r'''"""A constant names a colour; a key names a role. RNV-SEMANTIC-GUARD

Ruled by Chris on 2026-09-02, on the twenty values this application owns
outright, after seeing them rendered in situ: name them by MEANING, the way
the register names STATUS, not by hue. So SEMANTIC_DIFF_ADDED rather than
GREEN_DEEP, and the base carries the dark value with _LIGHT for the other
ground -- STATUS_ERROR / STATUS_ERROR_LIGHT upstream, exactly.

This guard pins three things that are easy to lose in a later pass:

  * the values did not move when the names did,
  * the old names cannot come back,
  * the drag highlight still DERIVES from BRAND_GOLD rather than repeating
    a gold literal, so a brand swap still flows through it.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from utils import colors

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ROOT / "utils" / "colors.py"
DRAG = ROOT / "ui" / "drag_drop_text_edit.py"

VALUES = {'SEMANTIC_DIFF_ADDED': '#1a4d1a', 'SEMANTIC_DIFF_REMOVED': '#4d1a1a', 'SEMANTIC_DIFF_CHANGED': '#4d4d1a', 'SEMANTIC_DIFF_CURRENT': '#4d1a4d', 'SEMANTIC_DIFF_ADDED_LIGHT': '#d4edda', 'SEMANTIC_DIFF_REMOVED_LIGHT': '#f8d7da', 'SEMANTIC_DIFF_CHANGED_LIGHT': '#fff3cd', 'SEMANTIC_DIFF_CURRENT_LIGHT': '#e2d4f0', 'SEMANTIC_REGEX_MATCH': '#4a4a00', 'SEMANTIC_REGEX_MATCH_LIGHT': '#ffff99'}
GROUPS = ('#3d5c5c', '#5c3d5c', '#5c5c3d', '#3d5c3d', '#5c3d3d', '#3d3d5c', '#5c4d3d', '#3d5c4d')
RETIRED = ('DIFF_ADDED_DARK', 'DIFF_REMOVED_DARK', 'DIFF_CHANGED_DARK', 'DIFF_CURRENT_DARK', 'DIFF_ADDED_LIGHT', 'DIFF_REMOVED_LIGHT', 'DIFF_CHANGED_LIGHT', 'DIFF_CURRENT_LIGHT', 'REGEX_MATCH_DARK', 'REGEX_MATCH_LIGHT', 'REGEX_GROUP_PALETTE', '_DRAG_HIGHLIGHT_GOLD')


def test_the_semantic_values_did_not_move():
    """A rename that changes a value is not a rename."""
    for name, want in VALUES.items():
        assert hasattr(colors, name), f"{name} is gone"
        assert getattr(colors, name).lower() == want, (
            f"{name} is {getattr(colors, name)}, was {want} before the rename")
    assert tuple(colors.SEMANTIC_REGEX_GROUPS) == GROUPS


def test_every_app_semantic_constant_says_so():
    """PROVENANCE is the classification; the name should agree with it.

    The point of the ruling is that the category is legible from the name.
    An 'app-semantic' constant called DIFF_ADDED_DARK told you its role and
    its mode and not its category."""
    wrong = [n for n, g in colors.PROVENANCE.items()
             if g == 'app-semantic' and not n.startswith('SEMANTIC_')]
    assert not wrong, f"app-semantic constants not named as such: {wrong}"


def test_nothing_semantic_carries_the_dark_suffix():
    """_DARK is the half of the pair the register does not write.

    Upstream holds STATUS_ERROR and STATUS_ERROR_LIGHT -- the base IS the
    dark value. A _DARK suffix here would mean this app disagreed with the
    register about what a base name means."""
    bad = [n for n, g in colors.PROVENANCE.items()
           if g == 'app-semantic' and n.endswith('_DARK')]
    assert not bad, f"the retired suffix came back on: {bad}"


def test_the_retired_names_are_gone_from_the_application():
    """Not a bare-token sweep of the whole tree: this guard and the delivery
    script both NAME the old names in order to forbid them, and a sweep that
    cannot tell a use from a mention fails on itself. Skip anything carrying
    either marker, and look at real source only."""
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"}
               for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-SEMANTIC-GUARD" in text or "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text:
            continue
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{path.relative_to(ROOT)}: {old}")
    assert not strays, "retired names are still in use:\n  " + "\n  ".join(strays)


def test_the_drag_highlight_is_a_role_wired_to_the_brand():
    """The class C member. Its name must not say gold, and its value must
    still be DERIVED from BRAND_GOLD rather than written out -- a later
    hand-edit to a literal would keep the name honest and break the swap,
    which is the failure this reads the syntax tree to catch."""
    tree = ast.parse(DRAG.read_text(encoding="utf-8-sig"))
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == "_DRAG_HIGHLIGHT":
            found = node.value
    assert found is not None, "_DRAG_HIGHLIGHT is not assigned in " + DRAG.name
    assert isinstance(found, ast.Call), "_DRAG_HIGHLIGHT is no longer derived"
    assert getattr(found.func, "id", None) == "with_alpha", (
        "_DRAG_HIGHLIGHT is not built with with_alpha any more")
    assert isinstance(found.args[0], ast.Name) and found.args[0].id == "BRAND_GOLD", (
        "_DRAG_HIGHLIGHT no longer takes its colour from BRAND_GOLD")


def test_the_drag_highlight_style_holds_no_literal():
    """rule 1, in the one place this application still broke it."""
    text = DRAG.read_text(encoding="utf-8-sig")
    hits = re.findall(r"#[0-9a-fA-F]{6}\b", text)
    assert not hits, f"{DRAG.name} writes colour literals: {hits}"
'''


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
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
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
