#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Rename the five main-window button keys from button_* to main_btn_*.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

NOT ONE PIXEL MOVES. This is a rename and nothing else.

Across the five desktop applications, `button_*` means two different things.
In rnv-icon-builder and rnv-color-picker it holds the GOLD DIALOG scheme, and
a second family, main_btn_*, holds the black-and-white main-window scheme. In
this application, in rnv-color-palette-manager and in rnv-color-mixer the same
name holds the MAIN scheme instead. One name, two schemes, decided by which
repository you happen to have open.

In this application the split is already clean -- it is only the name that is
wrong. These five keys are read in exactly two places, ui/main_window.py and
ui/image_button.py, both main-window code:

    button_bg  button_text  button_hover_bg  button_pressed_bg  button_pressed_text

and the dialog stylesheet in utils/dialog_styles.py never touches them. Its
buttons draw from bg_secondary / text / bg_hover / accent / accent_ink /
accent_text. So this application does not need a dialog button family invented
for it; it needs the family it has to say what it is.

WHAT MOVES

Sixty-nine quoted occurrences in nine files, plus the prose that names them:
the palette definitions, the two consumers, four test modules, the syrupy
snapshot, one docstring in utils/dialog_styles.py, one comment in
core/theme_manager.py, and docs/RNV_Brand_Color_System.md, which already
describes these keys as "Main window button background" and will now agree
with itself.

THE SNAPSHOT IS RESORTED, NOT HAND-EDITED

tests/__snapshots__/test_snapshots.ambr records each palette as a sorted key
list. main_btn_* does not sort where button_* sorted -- the five lines move
from below "border_light" to below "list_hover_text" -- so a rename that only
substituted text would leave the file out of order and the next snapshot run
would fail with a diff that looks like a regression. This script re-sorts each
block it touches and asserts the block was sorted before it started, which is
the only way to tell "I sorted it correctly" from "it was never sorted".

WHAT THE GUARD ASSERTS

tests/test_button_key_names.py fails if any old name comes back, if either
palette loses a new one, and -- the one that matters -- if any of the ten
values changed. The rename is only safe because the values are pinned; without
that assertion this script and a script that quietly restyled every button
would look identical in review.

FOUND WHILE DOING THIS, NOT FIXED HERE

docs/RNV_Brand_Color_System.md carries stale values for these keys: it says
button_text is #E0E0E0 in dark where the palette holds #dddddd, and annotates
button_pressed_text as "on gold bg" where the pressed plate is #444444. Both
predate this pass. A rename is the wrong place to correct documented colour
values, so the names are updated and the numbers are left exactly as found.
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
DESCRIPTION = "rename the main-window button keys to main_btn_*"
SENTINEL_FILE = "utils/dialog_styles.py"
SENTINEL = "'main_btn_bg'"
GUARD = "tests/test_button_key_names.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]

RENAME = {
    "button_bg": "main_btn_bg",
    "button_text": "main_btn_text",
    "button_hover_bg": "main_btn_hover_bg",
    "button_pressed_bg": "main_btn_pressed_bg",
    "button_pressed_text": "main_btn_pressed_text",
}

#: path -> how many QUOTED occurrences that file holds. Written down so the
#: script refuses to run against a tree that has moved under it.
QUOTED = {
    "utils/dialog_styles.py": 10,
    "ui/main_window.py": 15,
    "ui/image_button.py": 7,
    "test_rnv_text_transformer.py": 7,
    "tests/test_button_press_step.py": 11,
    "tests/test_app_mirror.py": 1,
    "tests/__snapshots__/test_snapshots.ambr": 10,
    "docs/RNV_Brand_Color_System.md": 8,
}

#: The ten values, pinned. A rename that changes one of these is not a rename.
PINNED = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#444444",
             "main_btn_pressed_text": "#000000"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#444444",
              "main_btn_pressed_text": "#ffffff"},
}

#: Prose that names the keys. Renamed so the documentation stays true.
PROSE = [
    ("utils/dialog_styles.py",
     "    - button_bg/button_text/button_hover_bg/button_pressed_text: Button colors",
     "    - main_btn_bg/main_btn_text/main_btn_hover_bg/main_btn_pressed_text: Button colors",
     1),
    ("core/theme_manager.py",
     "keys (window_bg, button_bg, input_bg, output_text_color, etc.).",
     "keys (window_bg, main_btn_bg, input_bg, output_text_color, etc.).",
     1),
]

_QUOTED_RE = re.compile(r"(['\"])(" + "|".join(sorted(RENAME, key=len, reverse=True))
                        + r")\1")
_ENTRY_RE = re.compile(r'^(\s*)"([A-Za-z0-9_]+)": (.*?)(,?)$')


def _rename_quoted(text: str) -> tuple[str, int]:
    hits = 0

    def swap(m: re.Match) -> str:
        nonlocal hits
        hits += 1
        return f"{m.group(1)}{RENAME[m.group(2)]}{m.group(1)}"

    return _QUOTED_RE.sub(swap, text), hits


def _resort_blocks(text: str) -> str:
    """Re-sort every run of `"key": value` lines the rename disturbed.

    A block is a maximal run of sibling entry lines at one indent. Each is
    checked to have been sorted BEFORE the rename -- a block that was not
    sorted to begin with is not ours to reorder, and silently sorting it would
    be an unrelated change hidden inside this one.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = _ENTRY_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        indent = m.group(1)
        block = []
        while i < len(lines):
            m2 = _ENTRY_RE.match(lines[i])
            if not m2 or m2.group(1) != indent:
                break
            block.append((m2.group(2), lines[i]))
            i += 1
        keys = [k for k, _ in block]
        if keys != sorted(keys):
            out.extend(line for _, line in block)
            continue
        renamed = [(RENAME.get(k, k), line) for k, line in block]
        renamed = [(k, _rename_quoted(line)[0]) for k, line in renamed]
        renamed.sort(key=lambda kv: kv[0])
        # the trailing entry of a block may or may not carry a comma; keep
        # whatever punctuation each line arrived with by not touching it.
        out.extend(line for _, line in renamed)
    return "\n".join(out)


def edits(tree) -> None:
    total = 0
    for rel, expected in QUOTED.items():
        src = tree.read(rel)
        if rel.endswith(".ambr"):
            before = len(_QUOTED_RE.findall(src))
            if before != expected:
                raise SystemExit(f"{rel}: expected {expected} quoted key(s), "
                                 f"found {before}")
            tree.write(rel, _resort_blocks(src))
            total += before
            continue
        new, hits = _rename_quoted(src)
        if hits != expected:
            raise SystemExit(f"{rel}: expected {expected} quoted key(s), "
                             f"found {hits}. The file moved; re-derive this "
                             f"edit before trusting the script.")
        tree.write(rel, new)
        total += hits
    for rel, old, new, times in PROSE:
        tree.sub(rel, old, new, times)
    print(f"  renamed {total} quoted keys in {len(QUOTED)} files, "
          f"{len(PROSE)} prose mentions")


def checks(tree) -> None:
    old_names = set(RENAME)
    for rel in list(QUOTED) + [rel for rel, *_ in PROSE]:
        text = tree.read(rel)
        for old in old_names:
            if re.search(r"(['\"])" + old + r"\1", text):
                raise SystemExit(f"{rel}: {old!r} survived the rename")

    styles = tree.read("utils/dialog_styles.py")
    for mode, values in PINNED.items():
        for key, value in values.items():
            if f"'{key}'" not in styles:
                raise SystemExit(f"utils/dialog_styles.py: {key!r} missing")

    # The values are the point. Resolve both palettes out of the edited source
    # and compare against the pins rather than trusting the substitution.
    import ast
    module = ast.parse(styles)
    # The palette values are NAMES imported from utils/colors.py, so a resolver
    # that reads only this file resolves every one of them to None -- and then
    # compares None to None and passes. The constants module is read too.
    consts = {}
    for source in (tree.read("utils/colors.py"), styles):
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

    found = []
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
            found.append({k: pairs.get(k) for k in PINNED["dark"]})
    if len(found) != 2:
        raise SystemExit(f"expected 2 palettes carrying the renamed keys, "
                         f"found {len(found)}")
    if any(v is None for palette in found for v in palette.values()):
        raise SystemExit(f"a value would not resolve: {found}. A comparison "
                         f"between two unresolved palettes passes by accident.")
    for pins in PINNED.values():
        if pins not in found:
            raise SystemExit(f"a palette no longer matches its pinned values.\n"
                             f"  wanted {pins}\n  found  {found}")

    ambr = tree.read("tests/__snapshots__/test_snapshots.ambr")
    if ambr.count('"main_btn_') != QUOTED["tests/__snapshots__/test_snapshots.ambr"]:
        raise SystemExit("the snapshot did not gain the renamed keys")
    for block_start in ("    \"main_btn_bg\"",):
        if block_start not in ambr:
            raise SystemExit("the snapshot lost its indentation shape")
    print("  guards: no old name survives, both palettes hold their pinned "
          "values, snapshot re-sorted")

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
        if path.is_dir() or path.suffix not in (".py", ".ambr", ".md"):
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


def test_the_marker_exemption_covers_only_the_two_tools():
    """An exemption that grows silently is how a guard stops guarding.

    Only this guard and the delivery script may carry a marker. If a third
    file gains one -- or if application source starts quoting the markers --
    the sweep above would go quiet without anyone noticing.
    """
    marked = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            marked.append(path.relative_to(ROOT))
    assert len(marked) <= 2, f"unexpected marked file(s): {marked}"
    assert Path(__file__).relative_to(ROOT) in marked


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
