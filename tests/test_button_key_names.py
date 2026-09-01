"""The button keys say where the button lives.

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
