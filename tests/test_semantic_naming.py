"""A constant names a colour; a key names a role. RNV-SEMANTIC-GUARD

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
