#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Move three rnv-text-transformer ramp steps into the register mirror, and split
one hex that was doing two jobs under one name.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES: NOTHING. Not one rendered pixel.

Three values this app owned are now the register's, so they stop being ramp
steps and become mirrors:

    GREY_3A  #3a3a3a  ->  APP_PANEL_HOVER          APP["panel-hover"]  rev 22
    GREY_E8  #e8e8e8  ->  GOLD_TEXT_GROUND_FLOOR   module constant     rev 24
    GREY_EE  #eeeeee  ->  APP_HOVER_LIGHT          APP["hover-light"]  rev 23
                          ... for ONE of its four uses. See below.

THE LATENT FAILURE THIS CLOSES

tests/test_brand_mirror.py has test_app_owned_values_are_not_register_values,
which fails when something classified app-owned turns out to BE a register
value. It skips where rnv-brand is not importable, and CI here does not have
it, so all three of these have been silently misclassified since the register
ruled them. Running the suite with the brand on the path is the proving run,
and it is red today. This makes it green honestly rather than by widening an
exemption.

GREY_EE IS SPLIT, NOT RENAMED

Four entries hold #eeeeee, and only one of them is the register's role:

    bg_hover              light dialog palette   -> APP_HOVER_LIGHT
    diff_html_header_bg   dark and light         -> stays GREY_EE
    line_number_bg        light gutter, at rest  -> stays GREY_EE

An interaction plate is not a resting ground. Wiring all four would claim a
role for three surfaces on the strength of a shared hex -- which is the mistake
the register warned about when it registered #e8e8e8, pointed the other way.
So GREY_EE survives as a ramp step for the three, and the coincidence between
it and APP["hover-light"] is recorded in COINCIDENT and asserted in both
directions: one that stops coinciding fails, and so does one that turns out to
be mirrored after all. This is the same shape as GREY_DD and APP["text"],
already in that table.

WHY #e8e8e8 GOT A REGISTER ENTRY AT ALL, AND WHY THIS FILE CAUSED IT

BRAND_DARK_GOLD_DEEP is defined in utils/colors.py as the smallest uniform
per-channel step that clears #e8e8e8: -14 gives 4.5334, and -13 gives 4.4675
and fails. That derivative is published, checked, mirrored and pinned in five
repositories -- and its INPUT was app-owned, so nothing anywhere could mirror
the constraint the whole derivation rests on. The register named it
GOLD_TEXT_GROUND_FLOOR on 2026-08-30 and added an import-time guard coupling
the two.

A MISPLACED COMMENT, MOVED

The `#:` block describing "the LIGHT scrollbar track ... held by APP_TEXT until
2026-08-28" sat directly above GREY_E8, so it documented GREY_E8 while
describing GREY_E0 -- the track is #e0e0e0 (dialog_styles 'scrollbar_bg'), and
#e0e0e0 is what APP["text"] held before the ink moved. Harmless while both were
anonymous ramp steps; not harmless when one of them becomes a register mirror,
because a wrong fact then acquires the authority of a checked one. This
programme has already shipped one guard whose docstring described a different
app's history and passed every test, since nothing checks prose. The comment
moves up one constant.

WHAT THIS SCRIPT DOES NOT DO

It does not touch ui/about_dialog.py. Confirming what bg_tertiary paints turned
up a separate defect -- gold-family text drawn in c['accent'] where the palette
defines c['accent_ink'] for text, failing the 4.5 floor in light mode at more
than one site. That is a value change of a different kind and it gets its own
script, so that this diff stays readable as what it is: a provenance pass.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import io
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

REPO = "rnv-text-transformer"
DESCRIPTION = "move three ramp steps into the register mirror"
SENTINEL_FILE = "utils/colors.py"
SENTINEL = "GOLD_TEXT_GROUND_FLOOR: Final[str]"
STYLES = "utils/dialog_styles.py"
INIT = "utils/__init__.py"
BRAND_MIRROR = "tests/test_brand_mirror.py"
GUARD = "tests/test_ladder_and_plate.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]

NEW_CONSTANTS = '\n#: engine/brand.py APP["panel-hover"]. The dark interaction plate, and the n=+2\n#: rung of the dark surface ladder BRAND_BLACK + n*0x10, n in -1..+2:\n#: #0a0a0a canvas, #1a1a1a panel, #2a2a2a card, #3a3a3a panel-hover.\n#:\n#: WAS GREY_3A, A RAMP STEP, until rnv-brand rev 22 registered it on\n#: 2026-08-29. The register had called the ladder "two-thirds specified"\n#: because APP_BORDER #333333 is not #3a3a3a and so looked like a missing rung.\n#: It is not a rung at all: #333333 is grey(3) on the INK grid, which governs\n#: inks and EDGES, and a border is an edge. Two families compared to each\n#: other. The ladder was complete the whole time.\nAPP_PANEL_HOVER: Final[str] = \'#3a3a3a\'\n\n#: engine/brand.py APP["hover-light"]. grey(14). The light interaction plate --\n#: bg_hover in the light dialog palette.\n#:\n#: Registered 2026-08-29 as #e8e8e8 and moved here on 2026-08-30 in rev 23,\n#: before any app had been wired to it. #e8e8e8 is the ground\n#: BRAND_DARK_GOLD_DEEP is calibrated against -- see GOLD_TEXT_GROUND_FLOOR\n#: below -- so a hover plate on that value clears the 4.5 text floor by 0.0334\n#: and fails the moment the gold moves one step. This clears by 0.2875.\n#: A boundary is not a plate.\n#:\n#: GREY_EE HOLDS THE SAME HEX AND IS NOT THIS. Three static surfaces still use\n#: the ramp step; only the hover plate is the register\'s. Recorded as a\n#: coincidence in tests/test_brand_mirror.py and asserted in both directions.\nAPP_HOVER_LIGHT: Final[str] = \'#eeeeee\'\n\n#: engine/brand.py GOLD_TEXT_GROUND_FLOOR. The darkest light ground on which\n#: the gold family carries text.\n#:\n#: WAS GREY_E8, A RAMP STEP, until rnv-brand rev 24 registered it on\n#: 2026-08-30 -- and it was registered because this file showed it was doing\n#: register work with no register entry. BRAND_DARK_GOLD_DEEP is defined above\n#: as the smallest uniform step that clears #e8e8e8: -14 gives 4.5334, and -13\n#: gives 4.4675 and fails. That derivative is published, checked, mirrored and\n#: pinned in five repositories. Its INPUT was app-owned, so nothing could\n#: mirror the constraint the whole derivation rests on.\n#:\n#: Both uses here are grounds the gold family draws on: bg_tertiary, which\n#: carries the About dialog\'s tab labels, and line_number_current_bg, whose\n#: foreground is BRAND_DARK_GOLD_DEEP itself.\nGOLD_TEXT_GROUND_FLOOR: Final[str] = \'#e8e8e8\'\n'
OLD_RAMP_TAIL = "GREY_E0: Final[str] = '#e0e0e0'\n#: The LIGHT scrollbar track. Held by APP_TEXT until 2026-08-28, when the ink\n#: moved to grey(13) and this did not follow -- it is a surface, and the\n#: published grid governs inks and edges only. rnv-color-picker and\n#: rnv-icon-builder both carry this same track at this same value.\nGREY_E8: Final[str] = '#e8e8e8'\nGREY_EE: Final[str] = '#eeeeee'"
NEW_RAMP_TAIL = '#: The LIGHT scrollbar track. Held by APP_TEXT until 2026-08-28, when the ink\n#: moved to grey(13) and this did not follow -- it is a surface, and the\n#: published grid governs inks and edges only. rnv-color-picker and\n#: rnv-icon-builder both carry this same track at this same value.\n#:\n#: THIS COMMENT SAT ONE CONSTANT LOWER until 2026-08-30, where it documented\n#: GREY_E8 while describing GREY_E0\'s job: the scrollbar track is #e0e0e0\n#: (utils/dialog_styles.py \'scrollbar_bg\'), and #e0e0e0 is what APP["text"]\n#: held before the ink moved. Moved when GREY_E8 became a register mirror --\n#: carrying a docstring that describes a different value into a mirror is how\n#: a wrong fact acquires the authority of a checked one.\nGREY_E0: Final[str] = \'#e0e0e0\'\n#: grey(14). Three STATIC surfaces: the diff export header in both modes, and\n#: the line number gutter\'s resting ground. NOT the light hover plate, which is\n#: APP_HOVER_LIGHT and holds this same hex -- one value, two roles, and only\n#: one of them is the register\'s. See COINCIDENT in tests/test_brand_mirror.py.\nGREY_EE: Final[str] = \'#eeeeee\''
OLD_COINCIDENT_TAIL = "        'rather than mirrored.'),\n}"
NEW_COINCIDENT_TAIL = '        \'rather than mirrored.\'),\n    \'GREY_EE\': (\n        \'APP["hover-light"]\',\n        \'grey(14) does two jobs here, the same way grey(13) does. In the \'\n        \'register it is the LIGHT INTERACTION PLATE -- what a control hovers \'\n        \'to in light mode, which this app mirrors as APP_HOVER_LIGHT. This \'\n        \'ramp step is three STATIC surfaces: the diff export header in both \'\n        \'modes, and the line number gutter at rest. A resting ground is not \'\n        \'an interaction state. If APP["hover-light"] moves off grey(14) these \'\n        \'three must NOT follow it, which is exactly why the hex is spelled by \'\n        \'two names rather than one.\'),\n}'
EDITS = [('utils/colors.py', "    'GREY_3A': 'app-ramp',\n", '', 1), ('utils/colors.py', "    'GREY_E8': 'app-ramp',\n", '', 1), ('utils/colors.py', "    'APP_TEXT_DIM': 'register',\n", "    'APP_TEXT_DIM': 'register',\n    'APP_PANEL_HOVER': 'register',\n    'APP_HOVER_LIGHT': 'register',\n    'GOLD_TEXT_GROUND_FLOOR': 'register',\n", 1), ('utils/colors.py', "    'GREY_3A',\n", '', 1), ('utils/colors.py', "    'GREY_E8',\n", '', 1), ('utils/colors.py', "    'APP_TEXT_DIM',\n", "    'APP_TEXT_DIM',\n    'APP_PANEL_HOVER',\n    'APP_HOVER_LIGHT',\n    'GOLD_TEXT_GROUND_FLOOR',\n", 1), ('utils/colors.py', "GREY_3A: Final[str] = '#3a3a3a'\n", '', 1), ('utils/__init__.py', '    GREY_3A,\n', '', 1), ('utils/__init__.py', '    GREY_E8,\n', '', 1), ('utils/__init__.py', '    GREY_EE,\n', '    GREY_EE,\n    APP_PANEL_HOVER,\n    APP_HOVER_LIGHT,\n    GOLD_TEXT_GROUND_FLOOR,\n', 1), ('utils/__init__.py', "    'GREY_3A',\n", '', 1), ('utils/__init__.py', "    'GREY_E8',\n", '', 1), ('utils/__init__.py', "    'GREY_EE',\n", "    'GREY_EE',\n    'APP_PANEL_HOVER',\n    'APP_HOVER_LIGHT',\n    'GOLD_TEXT_GROUND_FLOOR',\n", 1), ('utils/dialog_styles.py', '    GREY_3A,\n', '', 1), ('utils/dialog_styles.py', '    GREY_E8,\n', '', 1), ('utils/dialog_styles.py', '    GREY_EE,\n', '    GREY_EE,\n    APP_PANEL_HOVER,\n    APP_HOVER_LIGHT,\n    GOLD_TEXT_GROUND_FLOOR,\n', 1), ('utils/dialog_styles.py', "        'bg_hover': GREY_3A,", "        'bg_hover': APP_PANEL_HOVER,", 1), ('utils/dialog_styles.py', "        'bg_tertiary': GREY_E8,", "        'bg_tertiary': GOLD_TEXT_GROUND_FLOOR,", 1), ('utils/dialog_styles.py', "        'bg_hover': GREY_EE,", "        'bg_hover': APP_HOVER_LIGHT,", 1), ('utils/dialog_styles.py', "        'line_number_current_bg': GREY_E8,", "        'line_number_current_bg': GOLD_TEXT_GROUND_FLOOR,", 1), ('tests/test_brand_mirror.py', 'import ast\nimport pathlib\n', 'import ast\nimport pathlib\nimport re\n', 1), ('tests/test_brand_mirror.py', 'def _register_values(brand) -> dict:\n    """Every value the register holds, hex -> where it is held."""\n    named = {}\n    for attr in (\'BRAND_GOLD\', \'BRAND_DARK_GOLD\', \'BRAND_BLACK\',\n                 \'TRUE_BLACK\', \'WHITE\', \'WEB_BLACK\'):\n        named[getattr(brand, attr).lower()] = attr\n    for dict_name in (\'APP\', \'STATUS\'):\n        for key, value in getattr(brand, dict_name).items():\n            if isinstance(value, str) and value.startswith(\'#\'):\n                named.setdefault(value.lower(), f\'{dict_name}["{key}"]\')\n    return named', 'HEX = re.compile(r\'#[0-9a-fA-F]{6}$\')\n\n\ndef _register_values(brand) -> dict:\n    """Every value the register holds, hex -> where it is held.\n\n    ENUMERATED, NOT LISTED. Until 2026-08-30 this read six attribute names and\n    two dicts, written down. A value the register added afterwards was\n    therefore invisible to the test below, which is the only thing standing\n    between an app-owned label and a register value wearing it.\n\n    That is not hypothetical. rev 24 added GOLD_TEXT_GROUND_FLOOR #e8e8e8 as a\n    module constant, and this app held #e8e8e8 as GREY_E8, marked app-ramp. The\n    check ran, found nothing, and reported clean -- because the name of the\n    thing it needed to look at was not on its list. A list of what to check\n    goes stale behind the thing it checks; walking the module does not.\n    """\n    named = {}\n    for attr in sorted(dir(brand)):\n        if attr.startswith(\'_\'):\n            continue\n        value = getattr(brand, attr)\n        if isinstance(value, str) and HEX.match(value):\n            named.setdefault(value.lower(), attr)\n        elif isinstance(value, dict):\n            for key, item in value.items():\n                if isinstance(item, str) and HEX.match(item):\n                    named.setdefault(item.lower(), f\'{attr}["{key}"]\')\n    return named\n\n\ndef test_the_register_enumeration_is_not_empty():\n    """Guard the guard. Every misclassification check below asks whether a\n    value is in this map. An empty map answers no to everything and passes."""\n    brand = pytest.importorskip(\'engine.brand\', reason=\'rnv-brand not importable\')\n    named = _register_values(brand)\n    assert len(named) >= 20, (\n        f\'only {len(named)} register values enumerated. The sweeps that read \'\n        f\'this map pass trivially when it is small.\')\n    for expected in (brand.BRAND_GOLD, brand.APP[\'text\'],\n                     brand.GOLD_TEXT_GROUND_FLOOR):\n        assert expected.lower() in named, f\'{expected} is not enumerated\' ', 1)]

#: The four palette entries that must resolve to exactly what they resolved to
#: before. This pass renames the constants holding them; if a rename landed on
#: the wrong name the value changes, and this is what says so.
PINNED_ENTRIES = {
    ("DARK", "bg_hover"): "#3a3a3a",
    ("LIGHT", "bg_hover"): "#eeeeee",
    ("LIGHT", "bg_tertiary"): "#e8e8e8",
    ("LIGHT", "line_number_current_bg"): "#e8e8e8",
}

#: Names that must NOT survive anywhere, and names that must appear.
GONE = ("GREY_3A", "GREY_E8")
ARRIVED = ("APP_PANEL_HOVER", "APP_HOVER_LIGHT", "GOLD_TEXT_GROUND_FLOOR")


def edits(tree) -> None:
    # The three new constants, in the register section beside the others.
    tree.sub(SENTINEL_FILE, "APP_TEXT_DIM: Final[str] = '#aaaaaa'\n",
             "APP_TEXT_DIM: Final[str] = '#aaaaaa'\n" + NEW_CONSTANTS)
    # The ramp tail: GREY_E8 leaves, and the comment that was documenting it
    # while describing GREY_E0 moves up to the constant it is about.
    tree.sub(SENTINEL_FILE, OLD_RAMP_TAIL, NEW_RAMP_TAIL)
    tree.sub(BRAND_MIRROR, OLD_COINCIDENT_TAIL, NEW_COINCIDENT_TAIL)
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    print(f"  applied {len(EDITS) + 3} anchored edits across 4 files")


def _palettes(source: str, colors: str) -> dict:
    """DialogStyleManager's DARK and LIGHT, resolved to plain values through
    the module constants, so a rename that lands on the wrong name shows up as
    a value change rather than as a name this reader does not recognise.

    The constants come from the EDITED colors.py, not the one on disk. Reading
    disk here resolved every new name to nothing and reported four false
    failures -- the edits live in the tree until the guards pass, which is the
    whole point of rehearsing before writing."""
    consts = {}
    for node in ast.parse(colors.lstrip("\ufeff")).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                consts[target.id] = node.value.value
    out = {}
    for node in ast.walk(ast.parse(source.lstrip("\ufeff"))):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        name = getattr(target, "id", None)
        if name not in ("DARK", "LIGHT") or not isinstance(node.value, ast.Dict):
            continue
        palette = {}
        for key, value in zip(node.value.keys, node.value.values):
            if not isinstance(key, ast.Constant):
                continue
            if isinstance(value, ast.Constant):
                palette[key.value] = value.value
            elif isinstance(value, ast.Name):
                palette[key.value] = consts.get(value.id, f"<{value.id}>")
            else:
                palette[key.value] = ast.unparse(value)
        out[name] = palette
    return out


def _identifiers(source: str) -> set:
    """Every identifier a file actually USES, plus every string literal.

    Read from the token stream so comments are excluded. A regex cannot tell a
    use from a mention, and the comment this script writes to explain a rename
    contains the very name it is checking has gone.
    """
    names = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME:
            names.add(token.string)
        elif token.type == tokenize.STRING:
            names.add(token.string.strip("\"'"))
    return names


def checks(tree) -> None:
    edited_colors = tree.read(SENTINEL_FILE)
    edited_styles = tree.read(STYLES)

    # SHAPE. A rename that ate a line ending leaves every value identical and
    # every test green while the file is quietly reflowed.
    #
    # The expected delta is COMPUTED FROM THE EDIT TABLE rather than written
    # down. A hand-counted total is a second source of truth that goes stale
    # the moment an edit is added, and it went wrong once while this script was
    # being written.
    expected = {}
    for rel, old, new, times in EDITS:
        expected[rel] = expected.get(rel, 0) + times * (
            new.count("\n") - old.count("\n"))
    expected[SENTINEL_FILE] = expected.get(SENTINEL_FILE, 0) + (
        NEW_CONSTANTS.count("\n")
        + NEW_RAMP_TAIL.count("\n") - OLD_RAMP_TAIL.count("\n"))
    expected[BRAND_MIRROR] = expected.get(BRAND_MIRROR, 0) + (
        NEW_COINCIDENT_TAIL.count("\n") - OLD_COINCIDENT_TAIL.count("\n"))
    for rel, want in sorted(expected.items()):
        before = (Path.cwd() / rel).read_text(encoding="utf-8-sig")
        delta = tree.read(rel).count("\n") - before.count("\n")
        if delta != want:
            raise SystemExit(
                f"{rel} changed shape by {delta} lines; the edit table adds up "
                f"to exactly {want}.")

    # The four entries must resolve to exactly what they resolved to before.
    # This is what makes "nothing moved" checkable across a RENAME, where a
    # value comparison alone would be reading the new name's value twice.
    after = _palettes(edited_styles, edited_colors)
    wrong = []
    for (mode, key), want in PINNED_ENTRIES.items():
        got = after.get(mode, {}).get(key)
        if got != want:
            wrong.append(f"{mode}[{key!r}] resolves to {got}, not {want}")
    if wrong:
        raise SystemExit("a rename landed on the wrong value:\n  " + "\n  ".join(wrong))

    # Both directions, so a half-applied rename cannot pass -- and read from
    # the TOKEN STREAM, not with a regex.
    #
    # A regex sweep for GREY_3A matches the `#:` comment this very script
    # writes, which says "WAS GREY_3A, A RAMP STEP". That is a mention, not a
    # use, and it failed the first time this check ran. Comments are skipped;
    # NAME tokens are uses and STRING tokens catch the __all__ entries, which
    # are the one place a name lives as a literal.
    for rel in (SENTINEL_FILE, STYLES, INIT):
        used = _identifiers(tree.read(rel))
        for name in GONE:
            if name in used:
                raise SystemExit(
                    f"{rel} still uses {name}. A rename is finished when the "
                    f"old name is gone from every file, not merely unused in "
                    f"one.")
    defined = _identifiers(edited_colors)
    for name in ARRIVED:
        if name not in defined:
            raise SystemExit(f"{name} was never defined in {SENTINEL_FILE}")

    # GREY_EE survives, and it must: three static surfaces still use it, and
    # the whole point of the split is that they are not the plate.
    if not re.search(r"\bGREY_EE\b", edited_styles):
        raise SystemExit(
            "GREY_EE has no consumers left in the styles. This pass splits one "
            "hex into two names; if every use moved to APP_HOVER_LIGHT, the "
            "split did not happen and three static surfaces are now claiming "
            "to be an interaction plate.")

    # The comment that described the wrong constant must now sit above the
    # right one, and it must still exist. A move that deleted it would pass a
    # check that only looked for its absence from the old position.
    track = "The LIGHT scrollbar track"
    if track not in edited_colors:
        raise SystemExit("the scrollbar-track comment was lost in the move")
    where = edited_colors.index(track)
    e0 = edited_colors.index("GREY_E0: Final[str]")
    if not where < e0:
        raise SystemExit(
            "the scrollbar-track comment is still below GREY_E0, so it is "
            "still documenting the wrong constant.")

    if SENTINEL not in edited_colors:
        raise SystemExit(f"expected {SENTINEL!r} in the edited file")


GUARD_SOURCE = '"""Three ramp steps become register mirrors, and one hex is split in two.\n\nWHAT THIS PASS DID. rnv-brand registered three values this app had been\ncarrying as anonymous ramp steps:\n\n    GREY_3A  #3a3a3a  ->  APP_PANEL_HOVER          APP["panel-hover"]  rev 22\n    GREY_EE  #eeeeee  ->  APP_HOVER_LIGHT          APP["hover-light"]  rev 23\n    GREY_E8  #e8e8e8  ->  GOLD_TEXT_GROUND_FLOOR   module constant     rev 24\n\nTHE LATENT FAILURE THIS CLOSES. test_app_owned_values_are_not_register_values\nin tests/test_brand_mirror.py fails when something classified app-owned is in\nfact a register value. It skips where rnv-brand is not importable, and CI does\nnot have it -- so all three sat misclassified from the day the register ruled\nthem, with the suite reporting clean. The proving run is the one with the brand\non the path.\n\nGREY_EE IS SPLIT, NOT RENAMED. Four entries hold #eeeeee and only one plays the\nregister\'s role: bg_hover in the light dialog palette. The other three --\ndiff_html_header_bg in both modes, and line_number_bg -- are STATIC surfaces. A\nresting ground is not an interaction state, and wiring all four would claim a\nrole for three of them on the strength of a shared hex. GREY_EE therefore\nsurvives as a ramp step, and the coincidence is recorded in COINCIDENT beside\nGREY_DD / APP["text"], which is the same shape.\n\nWHY #e8e8e8 IS REGISTERED AT ALL, AND WHY THIS FILE\'S APP CAUSED IT.\nBRAND_DARK_GOLD_DEEP is defined in utils/colors.py as the smallest uniform\nper-channel step that clears #e8e8e8: -14 gives 4.5334, -13 gives 4.4675 and\nfails. That derivative is published, checked, mirrored and pinned in five\nrepositories, and its INPUT was app-owned -- so nothing could mirror the\nconstraint the derivation rests on. The coupling is asserted below, both ways,\nmirroring the guard the register now runs at import.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport io\nimport pathlib\nimport re\nimport tokenize\n\nimport pytest\n\nfrom utils import colors\nfrom utils.dialog_styles import DialogStyleManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nCOLORS = ROOT / \'utils\' / \'colors.py\'\nSTYLES = ROOT / \'utils\' / \'dialog_styles.py\'\n\nGRID_STEP = 0x11\nLADDER_STEP = 0x10\nTEXT_FLOOR = 4.5\n\n#: Constant -> the value it must hold. Resolution to rnv-brand is by the\n#: convention tests/test_brand_mirror.py already uses: APP_<KEY> -> APP["key"],\n#: anything else -> the module attribute of the same name.\nNEW = {\n    \'APP_PANEL_HOVER\': \'#3a3a3a\',\n    \'APP_HOVER_LIGHT\': \'#eeeeee\',\n    \'GOLD_TEXT_GROUND_FLOOR\': \'#e8e8e8\',\n}\n\n#: The names this pass removes. A rename is only finished when the old name is\n#: gone from every file, not merely unused in one.\nGONE = (\'GREY_3A\', \'GREY_E8\')\n\n#: What the split leaves behind: the ramp step, and the three static surfaces\n#: that keep it. If this list ever empties, the split has collapsed.\nSTATIC_EE_KEYS = (\'diff_html_header_bg\', \'line_number_bg\')\n\n#: Palette entries and what they must resolve to. Written as VALUES, because\n#: this pass renames the constants that hold them -- a check that read the new\n#: name\'s value would be reading the rename twice and proving nothing.\nPINNED_ENTRIES = {\n    (\'DARK\', \'bg_hover\'): \'#3a3a3a\',\n    (\'LIGHT\', \'bg_hover\'): \'#eeeeee\',\n    (\'LIGHT\', \'bg_tertiary\'): \'#e8e8e8\',\n    (\'LIGHT\', \'line_number_current_bg\'): \'#e8e8e8\',\n}\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef _shift(value: str, step: int) -> str:\n    parts = [max(0, min(255, int(value.lstrip(\'#\')[i:i + 2], 16) + step))\n             for i in (0, 2, 4)]\n    return \'#%02x%02x%02x\' % tuple(parts)\n\n\ndef _palette_names(name: str) -> dict:\n    """key -> the NAME each entry is written as, read from the source. The live\n    dict gives values; only the source says which constant was used."""\n    tree = ast.parse(STYLES.read_text(encoding=\'utf-8\'))\n    for node in ast.walk(tree):\n        if not isinstance(node, (ast.Assign, ast.AnnAssign)):\n            continue\n        target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n        if getattr(target, \'id\', None) != name or not isinstance(node.value, ast.Dict):\n            continue\n        out = {}\n        for k, v in zip(node.value.keys, node.value.values):\n            if isinstance(k, ast.Constant) and isinstance(v, ast.Name):\n                out[k.value] = v.id\n        return out\n    raise AssertionError(f\'{name} is not a dict in utils/dialog_styles.py\')\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_everything_this_file_reads_still_exists():\n    for name in NEW:\n        assert hasattr(colors, name), f\'utils.colors has no {name}\'\n    assert hasattr(colors, \'GREY_EE\'), \'the ramp step survived the split\'\n    for mode, key in PINNED_ENTRIES:\n        live = getattr(DialogStyleManager, mode)\n        assert key in live, f\'{mode} has no {key!r}\'\n\n\ndef test_the_maps_this_file_iterates_are_not_empty():\n    """Every sweep below iterates one of these. An empty map passes all."""\n    assert len(NEW) == 3 and len(PINNED_ENTRIES) == 4 and STATIC_EE_KEYS\n\n\n# ------------------------------------------------------------------ the values\n\ndef test_the_new_constants_hold_the_registered_values():\n    """The local half. Runs everywhere, including where engine.brand is not\n    importable -- which is exactly the case that let these three sit\n    misclassified for two days."""\n    drift = {n: getattr(colors, n) for n, v in NEW.items()\n             if getattr(colors, n) != v}\n    assert not drift, f\'these no longer hold their registered values: {drift}\'\n\n\ndef test_the_new_constants_match_rnv_brand():\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local values are doing the work\')\n    drift = []\n    for name in NEW:\n        theirs = (brand.APP[name[4:].lower().replace(\'_\', \'-\')]\n                  if name.startswith(\'APP_\') else getattr(brand, name))\n        mine = getattr(colors, name)\n        if mine.lower() != theirs.lower():\n            drift.append(f\'{name}: ours {mine}, theirs {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\ndef test_all_three_are_classified_register():\n    for name in NEW:\n        assert colors.PROVENANCE.get(name) == \'register\', (\n            f\'{name} is not classified register. The reclassification IS this \'\n            f\'pass; a constant in the register section with an app-ramp label \'\n            f\'is the misclassification it exists to fix.\')\n\n\ndef _identifiers(source: str) -> set:\n    """Every identifier a file actually USES, plus every string literal.\n\n    Read from the token stream so COMMENTS ARE EXCLUDED. A regex cannot tell a\n    use from a mention, and the comment beside APP_PANEL_HOVER says "WAS\n    GREY_3A, A RAMP STEP" -- explaining the rename, in the file the rename\n    happened in. A word-anchored regex flags that and reports the rename as\n    incomplete, which is exactly what it did the first time this ran.\n    """\n    names = set()\n    for token in tokenize.generate_tokens(io.StringIO(source).readline):\n        if token.type == tokenize.NAME:\n            names.add(token.string)\n        elif token.type == tokenize.STRING:\n            names.add(token.string.strip(\'\\\'"\'))\n    return names\n\n\ndef test_the_old_names_are_gone_everywhere():\n    """A rename is finished when the old name is absent from every file, not\n    merely unused in one. NAME tokens are uses, STRING tokens catch the\n    __all__ entries, and comments -- where the rename is explained -- are\n    neither."""\n    stale = []\n    for path in (COLORS, STYLES, ROOT / \'utils\' / \'__init__.py\'):\n        used = _identifiers(path.read_text(encoding=\'utf-8\'))\n        for name in GONE:\n            if name in used:\n                stale.append(f\'{path.name}: {name}\')\n    assert not stale, f\'renamed constants still used: {stale}\'\n\n\ndef test_the_rename_is_still_explained_where_it_happened():\n    """Guard the guard, from the other side. The sweep above deliberately\n    cannot see comments, so passing it proves nothing about whether the note\n    explaining the rename survived -- and that note is the only thing telling\n    the next reader why GREY_3A vanished."""\n    text = COLORS.read_text(encoding=\'utf-8\')\n    for name in GONE:\n        assert re.search(rf\'WAS {name}\\b\', text), (\n            f\'the comment recording that {name} was renamed is gone. The \'\n            f\'token-stream sweep cannot see comments, so nothing else would \'\n            f\'notice it went.\')\n\n\n# --------------------------------------------------------------------- the split\n\ndef test_the_ramp_step_survived_and_is_still_app_owned():\n    """GREY_EE is NOT the register\'s. Three static surfaces keep it, and if it\n    ever became a mirror those three would start following an interaction\n    plate they have nothing to do with."""\n    assert colors.GREY_EE == \'#eeeeee\'\n    assert colors.PROVENANCE.get(\'GREY_EE\') == \'app-ramp\'\n\n\ndef test_the_static_surfaces_still_use_the_ramp_step():\n    """The half of the split that a sweep for \'no old name survives\' cannot\n    see: if every use had moved to APP_HOVER_LIGHT the rename would look\n    complete and the distinction would be gone."""\n    names = {}\n    for mode in (\'DARK\', \'LIGHT\'):\n        names.update(_palette_names(mode))\n    using = [k for k in STATIC_EE_KEYS if names.get(k) == \'GREY_EE\']\n    assert len(using) == len(STATIC_EE_KEYS), (\n        f\'only {using} still name GREY_EE. The split puts the interaction \'\n        f\'plate on APP_HOVER_LIGHT and leaves the static grounds on the ramp \'\n        f\'step; if the grounds moved too, three surfaces are now claiming to \'\n        f\'be a hover state.\')\n\n\ndef test_the_hover_plate_names_the_register_constant():\n    """And the other half: the one entry that IS the plate."""\n    assert _palette_names(\'LIGHT\').get(\'bg_hover\') == \'APP_HOVER_LIGHT\'\n    assert _palette_names(\'DARK\').get(\'bg_hover\') == \'APP_PANEL_HOVER\'\n\n\ndef test_the_coincidence_is_recorded():\n    """A shared hex with two roles has to be named, or the next value check\n    reads the sharing as a misclassification and the next person reads it as a\n    mistake."""\n    mirror = pathlib.Path(__file__).with_name(\'test_brand_mirror.py\')\n    text = mirror.read_text(encoding=\'utf-8\')\n    assert "\'GREY_EE\': (" in text, (\n        \'GREY_EE shares #eeeeee with APP["hover-light"] and is not in \'\n        \'COINCIDENT. The exemption is what keeps the sharing deliberate.\')\n\n\n# ------------------------------------------------------------------ the ladder\n\ndef test_the_dark_rung_is_an_exact_step_on_the_ladder():\n    """BRAND_BLACK + n * 0x10. This was app-owned on the argument that the\n    ladder might not be real."""\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    want = base + 2 * (LADDER_STEP * 0x010101)\n    assert int(colors.APP_PANEL_HOVER.lstrip(\'#\'), 16) == want\n\n\ndef test_the_border_is_an_edge_and_not_a_rung():\n    """The distinction that made the ladder look incomplete. #333333 is grey(3)\n    on the ink grid, which governs inks and edges; it was never a surface."""\n    assert colors.APP_BORDER == grey(3)\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}\n    assert int(colors.APP_BORDER.lstrip(\'#\'), 16) not in rungs\n\n\n# --------------------------------------------------- the floor and the plate\n\ndef test_the_plate_is_a_step_on_the_ink_grid():\n    assert colors.APP_HOVER_LIGHT == grey(14) == \'#eeeeee\'\n\n\ndef test_the_deep_gold_is_calibrated_against_the_floor():\n    """The coupling the register now guards at import, asserted here too\n    because this is the file the derivation is written in. One step less must\n    FAIL -- a check that only proved the current value clears would pass on any\n    darker gold and say nothing about why -14 is the number."""\n    gold = colors.BRAND_DARK_GOLD_DEEP\n    floor = colors.GOLD_TEXT_GROUND_FLOOR\n    assert _contrast(gold, floor) >= TEXT_FLOOR, (\n        f\'{gold} reads {_contrast(gold, floor):.4f} on {floor}\')\n    softer = _shift(colors.BRAND_DARK_GOLD, -13)\n    assert _contrast(softer, floor) < TEXT_FLOOR, (\n        f\'one step less than the published -14 still clears the floor at \'\n        f\'{_contrast(softer, floor):.4f}, so -14 is no longer the SMALLEST \'\n        f\'step that clears it and the derivation note is stale.\')\n\n\ndef test_the_plate_is_not_the_floor():\n    """Both clear the 4.5 floor. Only one clears it by enough to survive the\n    gold moving, and the other is the value the gold is calibrated against."""\n    gold = colors.BRAND_DARK_GOLD_DEEP\n    here = _contrast(gold, colors.APP_HOVER_LIGHT)\n    edge = _contrast(gold, colors.GOLD_TEXT_GROUND_FLOOR)\n    assert colors.APP_HOVER_LIGHT != colors.GOLD_TEXT_GROUND_FLOOR\n    assert here - TEXT_FLOOR >= 0.2, (\n        f\'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The \'\n        f\'register moved APP["hover-light"] here for margin, not for a pass.\')\n    assert edge - TEXT_FLOOR < 0.05\n\n\n# ------------------------------------------------------- nothing moved at all\n\ndef test_every_renamed_entry_resolves_to_what_it_resolved_to_before():\n    """The values are written down rather than read from the new constants. A\n    check that compared an entry against the name it now uses would be reading\n    the rename twice and proving nothing about it."""\n    wrong = []\n    for (mode, key), want in PINNED_ENTRIES.items():\n        got = getattr(DialogStyleManager, mode)[key]\n        if got != want:\n            wrong.append(f\'{mode}[{key!r}] is {got}, not {want}\')\n    assert not wrong, \'a rename landed on the wrong value:\\n  \' + \'\\n  \'.join(wrong)\n'


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
        raise SystemExit(f"run this from the root of a {REPO} checkout "
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
