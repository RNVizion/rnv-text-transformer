#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Replace tests/test_button_key_names.py. One test in it was wrong.

    python up.py             # replace the guard, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE RENAME IS FINE. THE GUARD WAS NOT.

The button key rename landed correctly -- every file was written and the other
six tests passed. What failed was test_the_marker_exemption_covers_only_the_two
_tools, and it failed on the state of the checkout rather than on anything in
the application.

That test counted the files carrying a DO-NOT-SWEEP marker and allowed two:
the guard itself, and the delivery script. A working tree holding a second
copy of the delivery script -- an old up.py kept around, a renamed spare, the
script saved twice -- puts a third marked file in the repository and the count
fails. Nothing about the application is wrong when that happens.

WHAT IT SHOULD HAVE ASSERTED

Not how many files are exempt, but WHICH. The sweep skips marked files so that
a guard listing the old names in order to forbid them does not report itself.
The risk that creates is an application file gaining a marker and going quiet.
So the test now checks that every marked file other than this guard is a
delivery script, identified by the tool marker in its own header. Any number
of those may be lying in the tree; none of them is application source.

This is the ninth use-versus-mention failure this programme has recorded, and
the first where the fix was to stop counting and start naming.

WHAT THIS SCRIPT DOES

Rewrites tests/test_button_key_names.py and nothing else. It refuses to run
unless the rename already landed, so it cannot be mistaken for the pass itself.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-text-transformer"
DESCRIPTION = "replace the button-naming guard's exemption test"
GUARD = "tests/test_button_key_names.py"
SENTINEL_FILE = GUARD
SENTINEL = "test_no_application_file_is_exempt_from_the_sweep"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

MISSING_HELP = """\
tests/test_button_key_names.py is not here, so the button key rename has not
run in this checkout yet.

This script only replaces that guard. Run the rename script first -- the one
whose header begins "Rename the five main-window button keys from button_* to
main_btn_*" -- and then run this one. There is no filename to look for: every
script arrives as an attachment and is saved as up.py.
"""

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]


def edits(tree) -> None:
    styles = tree.read("utils/dialog_styles.py")
    if "'main_btn_bg'" not in styles:
        raise SystemExit(
            "utils/dialog_styles.py does not carry 'main_btn_bg', so the "
            "rename has not landed. This script replaces the guard only; run "
            "the rename first.")
    old = tree.read(GUARD)
    if "test_the_marker_exemption_covers_only_the_two_tools" not in old:
        raise SystemExit(
            "the guard in this checkout is not the one this script fixes -- "
            "it does not contain test_the_marker_exemption_covers_only_the_"
            "two_tools. Nothing was written.")
    print("  rename confirmed present; replacing the guard")


def checks(tree) -> None:
    new = tree.read(GUARD)
    if "test_the_marker_exemption_covers_only_the_two_tools" in new:
        raise SystemExit("the old exemption test survived the replacement")
    if SENTINEL not in new:
        raise SystemExit("the replacement guard is missing its new test")
    for keep in ("test_no_old_button_key_name_survives",
                 "test_both_palettes_carry_the_new_names",
                 "test_the_rename_moved_no_value",
                 "test_the_dialog_stylesheet_still_owns_its_own_button_colours",
                 "test_the_main_window_reads_the_main_family",
                 "test_every_snapshot_block_is_still_sorted"):
        if keep not in new:
            raise SystemExit(
                f"{keep} is missing. This replaces one test; a replacement "
                f"that quietly dropped the other six would be a regression "
                f"wearing the shape of a fix.")
    print("  guards: the six passing tests are still there, the failing one "
          "is replaced")


GUARD_SOURCE = r'''"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. This application has only the first family; its dialog buttons draw
from the shared surface and accent keys, not from a button family, and that is
recorded here so a later pass does not "restore" a button_* name on the
strength of the other repositories having one.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OLD = ("button_bg", "button_text", "button_hover_bg", "button_pressed_bg",
       "button_pressed_text")
NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)

PINNED = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#444444",
             "main_btn_pressed_text": "#000000"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#444444",
              "main_btn_pressed_text": "#ffffff"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE of that name from a MENTION of it, and
#: the two files most certain to mention it are this guard -- which lists the
#: old names in order to forbid them -- and the delivery script that performs
#: the rename. Both carry a marker for exactly this reason, and a file is
#: skipped by its marker rather than by its filename, because the delivery
#: script arrives under whatever name it is saved as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")


def _sources():
    for path in sorted(ROOT.rglob("*")):
        # Prose is not swept. docs/ is updated in one pass after alignment
        # settles, so it names the old keys until then, and a guard that
        # failed on that would be failing on a decision rather than a defect.
        if path.is_dir() or path.suffix not in (".py", ".ambr"):
            continue
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def _palettes():
    src = (ROOT / "utils" / "dialog_styles.py").read_text(encoding="utf-8-sig")
    module = ast.parse(src)
    # The palette values are NAMES imported from utils/colors.py. A resolver
    # that reads only dialog_styles.py resolves all of them to None, and then
    # compares None with None and passes. Read the constants module too.
    consts = {}
    for source in ((ROOT / "utils" / "colors.py").read_text(encoding="utf-8-sig"),
                   src):
        for node in ast.walk(ast.parse(source)):
            target = value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                target, value = node.targets[0].id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target, value = node.target.id, node.value
            if target and isinstance(value, ast.Constant) \
                    and isinstance(value.value, str):
                consts.setdefault(target, value.value)
    out = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Dict):
            continue
        pairs = {}
        for k, v in zip(node.keys, node.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                pairs[k.value] = v.value
            elif isinstance(v, ast.Name):
                pairs[k.value] = consts.get(v.id)
            elif isinstance(v, ast.Attribute):
                pairs[k.value] = consts.get(v.attr)
        if "main_btn_bg" in pairs:
            out.append(pairs)
    return out


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these are main-window button keys and must be named main_btn_*:\n  "
        + "\n  ".join(offenders))


TOOL_MARKER = "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP"


def test_no_application_file_is_exempt_from_the_sweep():
    """The exemption is by marker, and the marker is how a file could hide.

    An earlier version of this counted marked files and allowed two. That
    failed in a working tree holding a second copy of the delivery script --
    a guard failing on the state of somebody's checkout rather than on a
    defect in the application, which is the wrong thing to fail on.

    What actually matters is that no APPLICATION file is exempt. This guard
    may carry a marker; it lists the old names in order to forbid them.
    Everything else must be a delivery script, identified by the tool marker
    in its own header -- those arrive under whatever name they are saved as,
    there can be several of them lying around, and none is application source.
    """
    here = Path(__file__).resolve()
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if not any(marker in text for marker in MARKERS):
            continue
        if path.resolve() == here or TOOL_MARKER in text:
            continue
        strays.append(str(path.relative_to(ROOT)))
    assert not strays, (
        "these files are skipped by the name sweep but are not a delivery "
        f"script: {strays}")
    assert MARKERS[0] in here.read_text(encoding="utf-8-sig"), (
        "this guard lost its own marker and is now sweeping itself")


def test_both_palettes_carry_the_new_names():
    palettes = _palettes()
    assert len(palettes) == 2, f"expected 2 palettes, found {len(palettes)}"
    for palette in palettes:
        missing = [n for n in NEW if n not in palette]
        assert not missing, f"palette missing {missing}"


def test_the_rename_moved_no_value():
    palettes = _palettes()
    actual = [{k: p.get(k) for k in PINNED["dark"]} for p in palettes]
    assert not any(v is None for a in actual for v in a.values()), (
        f"a value would not resolve: {actual}. Two unresolved palettes compare "
        "equal, so this assertion has to fail loudly rather than pass quietly.")
    for mode, pins in PINNED.items():
        assert pins in actual, (
            f"the {mode} palette no longer holds its pinned values.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_dialog_stylesheet_still_owns_its_own_button_colours():
    """This app's dialogs never read the main family, and must not start.

    If a later pass wires the dialog stylesheet to main_btn_*, the two schemes
    fuse and the naming stops meaning anything. The dialog QSS draws from
    bg_secondary / bg_hover / accent, and that is asserted rather than assumed.
    """
    src = (ROOT / "utils" / "dialog_styles.py").read_text(encoding="utf-8-sig")
    start = src.index("/* ===== PUSH BUTTON ===== */")
    block = src[start:start + 900]
    assert "c['bg_secondary']" in block
    assert "c['bg_hover']" in block
    for name in NEW:
        assert name not in block, (
            f"the dialog button rule now reads {name}. Dialog buttons and main"
            " window buttons are different schemes; wire dialogs to a"
            " dialog_btn_* family instead.")


def test_the_main_window_reads_the_main_family():
    src = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8-sig")
    for name in NEW:
        assert f"'{name}'" in src, f"ui/main_window.py no longer reads {name}"


@pytest.mark.parametrize("rel", ["tests/__snapshots__/test_snapshots.ambr"])
def test_every_snapshot_block_is_still_sorted(rel):
    """The rename moves five lines; if it left them where they were, the next
    snapshot run fails with a diff that reads like a regression."""
    entry = re.compile(r'^(\s*)"([A-Za-z0-9_]+)": ')
    lines = (ROOT / rel).read_text(encoding="utf-8").split("\n")
    i = 0
    unsorted = []
    while i < len(lines):
        m = entry.match(lines[i])
        if not m:
            i += 1
            continue
        indent, block = m.group(1), []
        while i < len(lines):
            m2 = entry.match(lines[i])
            if not m2 or m2.group(1) != indent:
                break
            block.append(m2.group(2))
            i += 1
        if len(block) > 1 and block != sorted(block):
            unsorted.append(block[:6])
    assert not unsorted, f"unsorted snapshot block(s): {unsorted}"
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
