"""The text transformer: its two palettes live in utils/colors.py

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (02647b1).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #64 A, under #63 A. Every app keeps its colors in
utils/colors.py. This app's color file was already there, but its two
palettes, DARK and LIGHT, were class attributes of DialogStyleManager in
utils/dialog_styles.py. They move to utils/colors.py under the same names.
DialogStyleManager keeps DARK and LIGHT, pointing at the same two dicts, so
everything that reads DialogStyleManager.DARK reads what it read.

WHAT LANDS.
  utils/colors.py: the two palettes, as they were, with their comments,
      after the colors they name; its docstring and __all__ name them.
  utils/dialog_styles.py: DialogStyleManager's DARK and LIGHT point at them.
  12 more files: the tests that read the palettes from the source read
      utils/colors.py, and brand_map.json, README.md and ARCHITECTURE.md
      name the new place.

JUDGMENT CALLS, each reported:
  - In utils/colors.py the two palettes keep the names they had, DARK and
    LIGHT. So DialogStyleManager.DARK is colors.DARK, and COLORS.md's chart
    heads its columns Dark and Light, as it did.
  - utils/dialog_styles.py imported 48 names from utils/colors.py, every one
    of them for the palettes and none for the stylesheets. It imports the
    module, which the two pointers read.
  - utils/colors.py's __all__ lists DARK and LIGHT. Its docstring's usage
    example built a DARK and a LIGHT of its own; it reads the module's now.
  - Tests that read the palettes from the source read utils/colors.py. Reads
    of the stylesheet code, and sweeps of both files, stay as they are.
    Where a test held the path to utils/dialog_styles.py only for those
    reads, the path goes. One test picked the palettes as the file's long
    dicts; it picks them by name, since PROVENANCE beside them is as long.
  - The README's tree lists utils/colors.py, which it did not.
  - A note in tests/test_gold_as_text.py, the same in every app, quotes the
    palette manager's import of its colors. It names utils.colors, as the
    other four apps' copies now do.

NO VALUE MOVES. Every value utils/colors.py defined is what it was, and
DialogStyleManager serves the same DARK and LIGHT, key for key.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-text-transformer'
SENTINEL = '"dict": "DARK"'   # brand_map.json names the palette where it lives now
SENTINEL_FILE = 'brand_map.json'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_colors_in_sync.py', 'tests/test_named_and_used.py', 'tests/test_register_wiring.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The text transformer: its two palettes live in utils/colors.py"

_COV = [sys.executable, "-m", "coverage", "run", "--source=core,utils,ui,cli",
        "--branch"]
SUITES = [
    ("CI step 1: unittest test_rnv_text_transformer",
     _COV[:4] + ["--data-file=.coverage.unittest"] + _COV[4:]
     + ["-m", "unittest", "test_rnv_text_transformer"]),
    ("CI step 2: pytest tests/ --benchmark-disable",
     _COV[:4] + ["--data-file=.coverage.pytest"] + _COV[4:]
     + ["-m", "pytest", "tests/", "--benchmark-disable"]),
]

#: The environment the workflow sets for both steps.
CI_ENV = {"QT_QPA_PLATFORM": "offscreen"}


def post_write() -> None:
    """CI's environment: both test steps run with QT_QPA_PLATFORM=offscreen."""
    os.environ.update(CI_ENV)
    print("CI environment: " + ", ".join(f"{k}={v}" for k, v in CI_ENV.items()))

#: The workflows SUITES mirrors, by content hash, as this round leaves them.
CI_MIRRORS = {'.github/workflows/tests.yml': 'bd7e8e60c462b76f374f1f0d9e4b1a8e880d929e06b58a22467f094583b43af9'}

SHADOWS = ['colors.py', 'config.py', 'conftest.py', 'dialog_styles.py', 'run_tests.py', 'sync_colors.py', 'test_colors_in_sync.py', 'test_named_and_used.py', 'test_register_wiring.py', 'test_rnv_text_transformer.py']

LEFT_ALONE = ['every color value, and every key and value of the two palettes.', "DialogStyleManager's stylesheets, its cache and every reader of DialogStyleManager.DARK and .LIGHT, which read the same two dicts.", "tests/README.md's coverage figures, a record of a run.", 'rnv-brand, which the brand chat keeps.']

# ======================================================================== this round

COLOR_FILE = 'utils/colors.py'
STYLES_FILE = 'utils/dialog_styles.py'
PALETTES = ('DARK', 'LIGHT')

#: sha256 of each file the round reaches, as the head holds it
BASE_SHAS = {'ARCHITECTURE.md': '919a045f483d765e75eab0ca9f240e783512121275b4f1cfbd81b945d137560e', 'README.md': '74e90ca1a2ebc53469d7625555be86977c4a8c7fbcc09218b560ec6dca9d2628', 'brand_map.json': 'e627830867641b5c0121499153e37b91076d5dbf277d5752e5daee0cb62bfccb', 'tests/test_app_mirror.py': '9ea49515335ef13be3ebb9b8140bfe8e634e4ab45f7897b7f97d1085478a5ebf', 'tests/test_brand_mirror.py': '7f2142267a86106c2f528664801035c14490786a2defca89b6dc089ac93d6c08', 'tests/test_button_key_names.py': '970e211d038ab547334826f0c675f473b05d6c26fb822b2340dbc42da212820d', 'tests/test_derived_values.py': '7a8c1404d2f51b085d1ef12006722d3014fcf0c6248a58b1237e8ede5256885f', 'tests/test_gold_as_text.py': '0ec38048a2d11eeaba2ffd611e58bf262fd8542fb01cb25dbc627a4fc388f399', 'tests/test_ladder_and_plate.py': '2b5670a3414fae636c1ad8dd2c18c9e4ba0a75253176e935b59702180316b597', 'tests/test_named_and_used.py': '5d45d2c68293d6499c3d5db4ab2bede24227808ea362999ba365304b477d87e3', 'tests/test_register_wiring.py': 'd3ea97accf26f5b7e0f57357a4019d5f7005b6336ac5638cdc64632b5225cfd4', 'tests/test_tt_register.py': 'd212201567b262ffd5384021d24e10f44c081d525d4e0c71e4a4d5b7d195f932', 'utils/colors.py': 'b6f08507aa069304f89828de189210b487f9261613cf371117182adbcde2042c', 'utils/dialog_styles.py': '0fc74d6d32a8e224f5a908c81ad43f8a07dfc5ed34cdc17a2cbe25d70606e1e4'}

#: (file, anchor, replacement), applied in order; each anchor is found exactly once
SUBS = [('ARCHITECTURE.md', '\nHolds *palettes and stylesheets*. Has no state — it is a pure function of `(is_dark, font_family)`.\n\n', '\nHolds the *stylesheets*, and serves the palettes, which live in `utils/colors.py`. Has no state — it is a pure function of `(is_dark, font_family)`.\n\n'), ('ARCHITECTURE.md', '\n- **Lives in:** `utils/dialog_styles.py` as `DialogStyleManager.DARK` and `LIGHT`\n- **Accessed via:** `DialogStyleManager.get_colors(is_dark)` — returns the class-level dict by reference\n', '\n- **Lives in:** `utils/colors.py` as `DARK` and `LIGHT`, which `DialogStyleManager.DARK` and `.LIGHT` serve\n- **Accessed via:** `DialogStyleManager.get_colors(is_dark)` — returns the class-level dict by reference\n'), ('README.md', '├── utils/                         # Cross-cutting utilities\n│   ├── config.py                  # Single source of truth for version, paths, constants\n│   ├── dialog_styles.py           # Single source of truth for all colors and stylesheets\n│   ├── file_handler.py            # Multi-format file I/O\n', '├── utils/                         # Cross-cutting utilities\n│   ├── colors.py                  # Single source of truth for colors, the two palettes among them\n│   ├── config.py                  # Single source of truth for version, paths, constants\n│   ├── dialog_styles.py           # The dialog stylesheets, drawn from those palettes\n│   ├── file_handler.py            # Multi-format file I/O\n'), ('README.md', '\n- **Single source of truth.** All colors live in `utils/dialog_styles.py` (`DARK` and `LIGHT` dicts). The version string lives only in `utils/config.py`. No duplication.\n- **Centralized styling.** Every dialog inherits from `BaseDialog`, which delegates appearance to `DialogStyleManager` — a single stylesheet generator with LRU caching for performance.\n', '\n- **Single source of truth.** All colors live in `utils/colors.py`, the `DARK` and `LIGHT` palettes among them. The version string lives only in `utils/config.py`. No duplication.\n- **Centralized styling.** Every dialog inherits from `BaseDialog`, which delegates appearance to `DialogStyleManager` — a single stylesheet generator with LRU caching for performance.\n'), ('brand_map.json', '    {\n      "file": "utils/dialog_styles.py",\n      "dict": "DialogStyleManager.DARK"\n    },\n    {\n      "file": "utils/dialog_styles.py",\n      "dict": "DialogStyleManager.LIGHT"\n    }\n', '    {\n      "file": "utils/colors.py",\n      "dict": "DARK"\n    },\n    {\n      "file": "utils/colors.py",\n      "dict": "LIGHT"\n    }\n'), ('tests/test_app_mirror.py', '    the next ink move silently, which is what this pass existed to stop."""\n    source = STYLES.read_text(encoding=\'utf-8\')\n    assert "\'scrollbar_bg\': APP_TEXT," not in source, (\n', '    the next ink move silently, which is what this pass existed to stop."""\n    source = COLORS.read_text(encoding=\'utf-8\')\n    assert "\'scrollbar_bg\': APP_TEXT," not in source, (\n'), ('tests/test_brand_mirror.py', "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSTYLES = ROOT / 'utils' / 'dialog_styles.py'\nCOLORS = ROOT / 'utils' / 'colors.py'\n", "ROOT = pathlib.Path(__file__).resolve().parents[1]\nCOLORS = ROOT / 'utils' / 'colors.py'\n"), ('tests/test_brand_mirror.py', "def _palette_nodes():\n    tree = ast.parse(STYLES.read_text(encoding='utf-8'))\n    cls = next(n for n in ast.walk(tree)\n               if isinstance(n, ast.ClassDef) and n.name == 'DialogStyleManager')\n    for node in cls.body:\n        target = None\n", "def _palette_nodes():\n    # Module-level in utils/colors.py since #64 A (2026-10-18); they were\n    # DialogStyleManager's class attributes.\n    tree = ast.parse(COLORS.read_text(encoding='utf-8'))\n    for node in tree.body:\n        target = None\n"), ('tests/test_brand_mirror.py', 'def _theme_dicts() -> dict[str, dict]:\n    """The two theme dicts, resolved from source.\n\n    Read through the AST rather than imported because the dicts are built\n    inline in dialog_styles and there is no accessor that hands them over.\n    """\n    src = STYLES.read_text(encoding=\'utf-8\')\n    out = {}\n    for node in ast.walk(ast.parse(src)):\n        if not isinstance(node, ast.Dict) or len(node.keys) <= 30:\n            continue\n', 'def _theme_dicts() -> dict[str, dict]:\n    """The two theme dicts, resolved from source: utils/colors.py, where they\n    are since #64 A (2026-10-18). They were built inline in dialog_styles.\n    """\n    src = COLORS.read_text(encoding=\'utf-8\')\n    out = {}\n    # The two palettes, by name: PROVENANCE beside them is a dict as long.\n    for node in [n.value for n in ast.parse(src).body\n                 if isinstance(n, (ast.Assign, ast.AnnAssign)) and isinstance(n.value, ast.Dict)\n                 and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, \'id\', None)\n                 in (\'DARK\', \'LIGHT\')]:\n        if len(node.keys) <= 30:\n            continue\n'), ('tests/test_brand_mirror.py', '    """\n    src = STYLES.read_text(encoding=\'utf-8\')\n    dupes = []\n    for node in ast.walk(ast.parse(src)):\n        if not isinstance(node, ast.Dict):\n            continue\n        keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]\n        for k in sorted({k for k in keys if keys.count(k) > 1}):\n            dupes.append(f\'utils/dialog_styles.py:{node.lineno}: \'\n                         f\'{k!r} defined {keys.count(k)} times\')\n', '    """\n    src = COLORS.read_text(encoding=\'utf-8\')\n    dupes = []\n    for node in ast.walk(ast.parse(src)):\n        if not isinstance(node, ast.Dict):\n            continue\n        keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]\n        for k in sorted({k for k in keys if keys.count(k) > 1}):\n            dupes.append(f\'utils/colors.py:{node.lineno}: \'\n                         f\'{k!r} defined {keys.count(k)} times\')\n'), ('tests/test_button_key_names.py', 'def _palettes():\n    src = (ROOT / "utils" / "dialog_styles.py").read_text(encoding="utf-8-sig")\n    module = ast.parse(src)\n    # The palette values are NAMES imported from utils/colors.py. A resolver\n    # that reads only dialog_styles.py resolves all of them to None, and then\n    # compares None with None and passes. Read the constants module too.\n    consts = {}\n    for source in ((ROOT / "utils" / "colors.py").read_text(encoding="utf-8-sig"),\n                   src):\n        for node in ast.walk(ast.parse(source)):\n', 'def _palettes():\n    src = (ROOT / "utils" / "colors.py").read_text(encoding="utf-8-sig")\n    module = ast.parse(src)\n    # The palette values are NAMES of the constants beside them in\n    # utils/colors.py, where the palettes are since #64 A (2026-10-18). A\n    # resolver that read the palettes and not the constants would resolve\n    # all of them to None, and then compare None with None and pass. So the\n    # constants are read too.\n    consts = {}\n    for source in (src,):\n        for node in ast.walk(ast.parse(source)):\n'), ('tests/test_derived_values.py', 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSTYLES = ROOT / "utils" / "dialog_styles.py"\nDRAG = ROOT / "ui" / "drag_drop_text_edit.py"\n', 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nCOLORS = ROOT / "utils" / "colors.py"\nDRAG = ROOT / "ui" / "drag_drop_text_edit.py"\n'), ('tests/test_derived_values.py', '    out = []\n    tree = ast.parse(STYLES.read_text(encoding="utf-8-sig"))\n    cls = next(n for n in tree.body\n               if isinstance(n, ast.ClassDef) and n.name == "DialogStyleManager")\n    for node in cls.body:\n        if not isinstance(node, (ast.Assign, ast.AnnAssign)):\n', '    out = []\n    tree = ast.parse(COLORS.read_text(encoding="utf-8-sig"))\n    for node in tree.body:\n        if not isinstance(node, (ast.Assign, ast.AnnAssign)):\n'), ('tests/test_derived_values.py', '    sources = list(_sources())\n    assert any(rel.as_posix() == "utils/dialog_styles.py" for rel, _ in sources), (\n        "the sweep cannot see the palettes, so it proves nothing")\n', '    sources = list(_sources())\n    assert any(rel.as_posix() == "utils/colors.py" for rel, _ in sources), (\n        "the sweep cannot see the palettes, so it proves nothing")\n'), ('tests/test_gold_as_text.py', '            #: its palette with a lazy import inside each style function --\n            #: `from ui.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n', '            #: its palette with a lazy import inside each style function --\n            #: `from utils.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n'), ('tests/test_ladder_and_plate.py', '    dict gives values; only the source says which constant was used."""\n    tree = ast.parse(STYLES.read_text(encoding=\'utf-8\'))\n    for node in ast.walk(tree):\n', '    dict gives values; only the source says which constant was used."""\n    tree = ast.parse(COLORS.read_text(encoding=\'utf-8\'))\n    for node in ast.walk(tree):\n'), ('tests/test_ladder_and_plate.py', "        return out\n    raise AssertionError(f'{name} is not a dict in utils/dialog_styles.py')\n\n", "        return out\n    raise AssertionError(f'{name} is not a dict in utils/colors.py')\n\n"), ('tests/test_named_and_used.py', '#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("utils/dialog_styles.py",)\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n', '#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("utils/colors.py",)\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n'), ('tests/test_register_wiring.py', '\nWHAT IS DIFFERENT HERE. This app has two palettes, DARK and LIGHT, both class\nattributes of DialogStyleManager; image mode reads DARK. Both were wired at\nthe same time, so both halves are swept for literals, and the light allowlist\nis what the light palette names today, every entry of which has been through\na ruling (the light wiring, the gold rounds, the 2026-09-07 correction).\nEight entries in each palette are with_alpha(NAME, ALPHA) calls, so the\nsweep looks inside a value, not only at it.\n"""\n', '\nWHAT IS DIFFERENT HERE. This app has two palettes, DARK and LIGHT. They are\nin utils/colors.py since #64 A (2026-10-18), and DialogStyleManager serves\nthem; image mode reads DARK. Both were wired at the same time, so both halves\nare swept for literals, and the light allowlist is what the light palette\nnames today, every entry of which has been through a ruling (the light\nwiring, the gold rounds, the 2026-09-07 correction). Eight entries in each\npalette are with_alpha(NAME, ALPHA) calls, so the sweep looks inside a\nvalue, not only at it.\n"""\n'), ('tests/test_register_wiring.py', "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/dialog_styles.py'\n\n", "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/colors.py'\n\n"), ('tests/test_tt_register.py', "COLORS = ROOT / 'utils/colors.py'\nSTYLES = ROOT / 'utils/dialog_styles.py'\n\n", "COLORS = ROOT / 'utils/colors.py'\n\n"), ('tests/test_tt_register.py', '    follow rev 27\'s ladder the next time it moves."""\n    src = STYLES.read_text(encoding=\'utf-8\')\n    assert f"\'{key}\': APP_SURFACE_LIGHT_3," in src, (\n', '    follow rev 27\'s ladder the next time it moves."""\n    src = COLORS.read_text(encoding=\'utf-8\')\n    assert f"\'{key}\': APP_SURFACE_LIGHT_3," in src, (\n'), ('tests/test_tt_register.py', '    assert LIGHT[\'scrollbar_bg\'] == colors.GRAY_E0\n    src = STYLES.read_text(encoding=\'utf-8\')\n    assert "\'scrollbar_bg\': GRAY_E0," in src\n', '    assert LIGHT[\'scrollbar_bg\'] == colors.GRAY_E0\n    src = COLORS.read_text(encoding=\'utf-8\')\n    assert "\'scrollbar_bg\': GRAY_E0," in src\n'), ('tests/test_tt_register.py', 'def test_this_guard_can_see_what_it_checks():\n    """Guard the guard. Every assertion above walks these two files and the\n    two resolved palettes; if any of them stopped resolving, the rest would\n    pass over nothing."""\n    assert COLORS.exists() and STYLES.exists()\n    assert len(LIGHT) > 20 and len(DARK) > 20\n', 'def test_this_guard_can_see_what_it_checks():\n    """Guard the guard. Every assertion above walks utils/colors.py, where the\n    palettes are written since #64 A (2026-10-18), and the two resolved\n    palettes; if any of them stopped resolving, the rest would pass over\n    nothing."""\n    assert COLORS.exists()\n    assert len(LIGHT) > 20 and len(DARK) > 20\n'), ('utils/colors.py', "\nUsage\n-----\n    from utils.colors import BRAND_GOLD, BRAND_DARK_GOLD, with_alpha\n\n    DARK  = {'accent': BRAND_GOLD}\n    LIGHT = {'accent': BRAND_DARK_GOLD}\n\n", "\nPalettes\n--------\nDARK and LIGHT, the two theme palettes, are defined here too: every key a\ndialog, the main window or an export looks up, and the named color it takes\nin that mode. DialogStyleManager serves them under the same names; they were\nits class attributes until #64 A (2026-10-18).\n\n\nUsage\n-----\n    from utils.colors import BRAND_GOLD, DARK, LIGHT, with_alpha\n\n    DARK['accent']    # BRAND_GOLD\n    LIGHT['accent']   # BRAND_DARK_GOLD\n\n"), ('utils/colors.py', '#: GRAY_E8 while describing GRAY_E0\'s job: the scrollbar track is #e0e0e0\n#: (utils/dialog_styles.py \'scrollbar_bg\'), and #e0e0e0 is what APP["text"]\n#: held before the ink moved. Moved when GRAY_E8 became a register mirror --\n', '#: GRAY_E8 while describing GRAY_E0\'s job: the scrollbar track is #e0e0e0\n#: (LIGHT[\'scrollbar_bg\'], below), and #e0e0e0 is what APP["text"]\n#: held before the ink moved. Moved when GRAY_E8 became a register mirror --\n'), ('utils/colors.py', '\n# ==================== PROVENANCE ====================\n', '\n# ==================== PALETTES ====================\n#\n# The two theme palettes: each key a dialog, the main window or an export\n# looks up, and the named color it takes in that mode. Image mode reads DARK.\n# DialogStyleManager serves them under the same names, the same two dicts;\n# they were its class attributes until #64 A (2026-10-18).\n\nDARK: Final[dict[str, str]] = {\n    # Backgrounds\n    \'bg\': BRAND_BLACK,\n    \'bg_secondary\': APP_CARD,\n    \'bg_tertiary\': APP_BORDER,\n    \'bg_hover\': APP_PANEL_HOVER,\n\n    # Text\n    \'text\': APP_TEXT,\n    \'text_muted\': GRAY_88,\n    \'text_disabled\': GRAY_55,\n\n    # Borders\n    \'border\': APP_BORDER,\n    \'border_light\': GRAY_44,\n    \'border_focus\': BRAND_GOLD,\n\n    # Accent colors\n    \'accent\': BRAND_GOLD,\n    \'accent_hover\': BRAND_GOLD_HOVER,\n    \'accent_pressed\': BRAND_GOLD_PRESSED,\n    \'accent_ink\': BRAND_GOLD,  # Accent when it carries text\n    \'accent_text\': TRUE_BLACK,  # Text on accent background\n\n    # Semantic colors\n    # RNV-STATUS-FAMILY: these three keys are read in fourteen\n    # places and every one is a `color:` declaration, so they\n    # carry the TEXT variants rather than the fills. The fills\n    # sit at L* 48-59 and cannot reach 4.5:1 on either ground.\n    \'success\': STATUS_SUCCESS_TEXT,\n    \'error\': STATUS_ERROR_TEXT,\n    \'warning\': STATUS_WARNING_TEXT,\n    \'info\': BRAND_GOLD,\n\n    # Special\n    \'selection_bg\': BRAND_GOLD,\n    \'selection_text\': TRUE_BLACK,\n    \'scrollbar_bg\': APP_CARD,\n    \'scrollbar_handle\': GRAY_44,\n    \'scrollbar_handle_main\': GRAY_44,\n    \'tooltip_border\': BRAND_GOLD,\n\n    # Checkbox indicator\n    \'checkbox_indicator_bg\': BRAND_BLACK,\n    \'checkbox_border\': GRAY_55,\n\n    # Dropdown / list hover\n    \'list_hover_bg\': WHITE,\n    \'list_hover_text\': TRUE_BLACK,\n\n    # MainWindow-specific (pure black background, distinct from dialog bg)\n    \'window_bg\': TRUE_BLACK,\n    \'main_btn_bg\': BRAND_BLACK,\n    \'main_btn_text\': APP_TEXT,\n    \'main_btn_hover_bg\': APP_BORDER,\n    \'main_btn_pressed_bg\': GRAY_44,\n    \'main_btn_pressed_text\': TRUE_BLACK,\n    \'input_bg\': BRAND_BLACK,\n    \'input_text\': APP_TEXT,\n    \'input_border\': APP_BORDER,\n    \'label_bg\': TRUE_BLACK,\n    \'label_text\': APP_TEXT,\n    \'output_text_color\': BRAND_GOLD,\n    \'border_color\': APP_BORDER,\n    \'text_color\': APP_TEXT,\n\n    # Diff / compare semantic highlight colors\n    \'diff_added_bg\':   SEMANTIC_DIFF_ADDED,\n    \'diff_removed_bg\': SEMANTIC_DIFF_REMOVED,\n    \'diff_changed_bg\': SEMANTIC_DIFF_CHANGED,\n\n    # RNV-NAMED-AND-USED (2026-10-04): the diff export\'s seven colors\n    # stood here too. The export is a standalone page, always light,\n    # and reads them from LIGHT by name; this copy was looked up by\n    # nothing. They are in LIGHT alone.\n\n    # Regex builder match highlight\n    \'regex_match_bg\': SEMANTIC_REGEX_MATCH,\n\n    # Image mode semi-transparent overlay values -- used only in image\n    # mode. DERIVED: a named color at a declared alpha, so a register\n    # move reaches them (RNV-DERIVE-ALPHA, 2026-09-25).\n    \'image_overlay_bg\':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n    \'image_overlay_bg_dark\':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n    \'image_overlay_checkbox\':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n    \'image_scrollbar_border\':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n    # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n    # rgba(80, 80, 80, 150), the value ruled onto GRAY_44 on\n    # 2026-09-02 and left behind because nothing decoded rgba().\n    \'image_scrollbar_handle\':      with_alpha(GRAY_44, SCROLLBAR_HANDLE_ALPHA),\n    # The image scrollbar hovers from DARK\'s \'accent\'. It has no key of\n    # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n    \'image_dropdown_bg\':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n    \'image_dropdown_selection\':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n    \'image_dropdown_border\':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n}\n\nLIGHT: Final[dict[str, str]] = {\n    # Backgrounds\n    \'bg\': APP_SURFACE_LIGHT_3,\n    \'bg_secondary\': WHITE,\n    \'bg_tertiary\': GOLD_TEXT_GROUND_FLOOR,\n    \'bg_hover\': APP_HOVER_LIGHT,\n\n    # Text\n    \'text\': TRUE_BLACK,\n    \'text_muted\': GRAY_66,\n    \'text_disabled\': APP_TEXT_DIM,\n\n    # Borders\n    \'border\': GRAY_CC,\n    \'border_light\': GRAY_DD,\n    \'border_focus\': BRAND_DARK_GOLD,\n\n    # Accent colors\n    \'accent\': BRAND_DARK_GOLD,\n    \'accent_hover\': BRAND_DARK_GOLD_DEEP,\n    \'accent_pressed\': BRAND_DARK_GOLD_PRESSED,\n    \'accent_ink\': BRAND_DARK_GOLD_DEEP,  # Accent when it carries text\n    \'accent_text\': WHITE,  # Text on accent background\n\n    # Semantic colors\n    # RNV-STATUS-FAMILY: light\'s siblings. success and warning\n    # had no light variant before this and read 2.87 and 1.50\n    # on #f5f5f5 -- illegal as text, live, and unnoticed because\n    # the only boundary test in this repo covered the red.\n    \'success\': STATUS_SUCCESS_TEXT_LIGHT,\n    \'error\': STATUS_ERROR_TEXT_LIGHT,\n    \'warning\': STATUS_WARNING_TEXT_LIGHT,\n    \'info\': BRAND_DARK_GOLD_DEEP,\n\n    # Special\n    \'selection_bg\': BRAND_DARK_GOLD,\n    \'selection_text\': WHITE,\n    \'scrollbar_bg\': GRAY_E0,\n    \'scrollbar_handle\': APP_TEXT_DIM,\n    \'scrollbar_handle_main\': APP_TEXT_DIM,\n    \'tooltip_border\': BRAND_DARK_GOLD,\n\n    # Checkbox indicator\n    \'checkbox_indicator_bg\': WHITE,\n    \'checkbox_border\': APP_TEXT_DIM,\n\n    # Dropdown / list hover\n    \'list_hover_bg\': BRAND_BLACK,\n    \'list_hover_text\': WHITE,\n\n    # MainWindow-specific\n    \'window_bg\': APP_SURFACE_LIGHT_3,\n    \'main_btn_bg\': WHITE,\n    \'main_btn_text\': TRUE_BLACK,\n    \'main_btn_hover_bg\': APP_BORDER,\n    \'main_btn_pressed_bg\': GRAY_44,\n    \'main_btn_pressed_text\': WHITE,\n    \'input_bg\': WHITE,\n    \'input_text\': TRUE_BLACK,\n    \'input_border\': GRAY_CC,\n    \'label_bg\': APP_SURFACE_LIGHT_3,\n    \'label_text\': TRUE_BLACK,\n    \'output_text_color\': BRAND_DARK_GOLD,\n    \'border_color\': GRAY_CC,\n    \'text_color\': TRUE_BLACK,\n\n    # Diff / compare semantic highlight colors\n    \'diff_added_bg\':   SEMANTIC_DIFF_ADDED_LIGHT,\n    \'diff_removed_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n    \'diff_changed_bg\': SEMANTIC_DIFF_CHANGED_LIGHT,\n\n    # Diff HTML export colors (standalone document — always light-styled)\n    \'diff_html_equal_bg\':  WHITE,\n    \'diff_html_insert_bg\': SEMANTIC_DIFF_ADDED_LIGHT,\n    \'diff_html_delete_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n    \'diff_html_header_bg\': GRAY_EE,\n    \'diff_html_line_num\':  GRAY_88,\n    \'diff_html_border\':    GRAY_DD,\n    \'diff_html_stats_text\':GRAY_66,\n\n    # Regex builder match highlight\n    \'regex_match_bg\': SEMANTIC_REGEX_MATCH_LIGHT,\n\n    # RNV-NAMED-AND-USED (2026-10-04): the image overlays\' eight values\n    # stood here too, the same derivations as DARK. Image mode reads\n    # them from DARK by name, as the note that stood with them said:\n    # "nothing reads these". They are in DARK alone.\n}\n\n\n# ==================== PROVENANCE ====================\n'), ('utils/colors.py', "    'PROVENANCE',\n    'BRAND_GOLD',\n", "    'PROVENANCE',\n    'DARK',\n    'LIGHT',\n    'BRAND_GOLD',\n"), ('utils/dialog_styles.py', '\nfrom utils.colors import (\n    TRUE_BLACK,\n    WHITE,\n    BRAND_BLACK,\n    APP_CARD,\n    APP_BORDER,\n    APP_TEXT,\n    APP_TEXT_DIM,\n    STATUS_SUCCESS_TEXT,\n    STATUS_WARNING_TEXT,\n    STATUS_ERROR_TEXT,\n    STATUS_SUCCESS_TEXT_LIGHT,\n    STATUS_WARNING_TEXT_LIGHT,\n    STATUS_ERROR_TEXT_LIGHT,\n    BRAND_GOLD_HOVER,\n    BRAND_GOLD_PRESSED,\n    GRAY_44,\n    GRAY_55,\n    GRAY_66,\n    GRAY_88,\n    GRAY_CC,\n    GRAY_DD,\n    GRAY_E0,\n    GRAY_EE,\n    APP_PANEL_HOVER,\n    APP_HOVER_LIGHT,\n    APP_SURFACE_LIGHT_3,\n    GOLD_TEXT_GROUND_FLOOR,\n    SEMANTIC_DIFF_ADDED,\n    SEMANTIC_DIFF_REMOVED,\n    SEMANTIC_DIFF_CHANGED,\n    SEMANTIC_DIFF_ADDED_LIGHT,\n    SEMANTIC_DIFF_REMOVED_LIGHT,\n    SEMANTIC_DIFF_CHANGED_LIGHT,\n    SEMANTIC_REGEX_MATCH,\n    SEMANTIC_REGEX_MATCH_LIGHT,\n    BRAND_GOLD,\n    BRAND_DARK_GOLD,\n    BRAND_DARK_GOLD_DEEP,\n    BRAND_DARK_GOLD_PRESSED,\n    with_alpha,\n    IMAGE_FIELD_ALPHA,\n    IMAGE_LABEL_ALPHA,\n    IMAGE_CHECKBOX_ALPHA,\n    SCROLLBAR_BORDER_ALPHA,\n    SCROLLBAR_HANDLE_ALPHA,\n    DROPDOWN_BG_ALPHA,\n    DROPDOWN_SELECTION_ALPHA,\n    DROPDOWN_BORDER_ALPHA,\n)\n\n', '\nfrom utils import colors\n\n'), ('utils/dialog_styles.py', '    \n    DARK: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        \'bg\': BRAND_BLACK,\n        \'bg_secondary\': APP_CARD,\n        \'bg_tertiary\': APP_BORDER,\n        \'bg_hover\': APP_PANEL_HOVER,\n        \n        # Text\n        \'text\': APP_TEXT,\n        \'text_muted\': GRAY_88,\n        \'text_disabled\': GRAY_55,\n        \n        # Borders\n        \'border\': APP_BORDER,\n        \'border_light\': GRAY_44,\n        \'border_focus\': BRAND_GOLD,\n        \n        # Accent colors\n        \'accent\': BRAND_GOLD,\n        \'accent_hover\': BRAND_GOLD_HOVER,\n        \'accent_pressed\': BRAND_GOLD_PRESSED,\n        \'accent_ink\': BRAND_GOLD,  # Accent when it carries text\n        \'accent_text\': TRUE_BLACK,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: these three keys are read in fourteen\n        # places and every one is a `color:` declaration, so they\n        # carry the TEXT variants rather than the fills. The fills\n        # sit at L* 48-59 and cannot reach 4.5:1 on either ground.\n        \'success\': STATUS_SUCCESS_TEXT,\n        \'error\': STATUS_ERROR_TEXT,\n        \'warning\': STATUS_WARNING_TEXT,\n        \'info\': BRAND_GOLD,\n        \n        # Special\n        \'selection_bg\': BRAND_GOLD,\n        \'selection_text\': TRUE_BLACK,\n        \'scrollbar_bg\': APP_CARD,\n        \'scrollbar_handle\': GRAY_44,\n        \'scrollbar_handle_main\': GRAY_44,\n        \'tooltip_border\': BRAND_GOLD,\n        \n        # Checkbox indicator\n        \'checkbox_indicator_bg\': BRAND_BLACK,\n        \'checkbox_border\': GRAY_55,\n        \n        # Dropdown / list hover\n        \'list_hover_bg\': WHITE,\n        \'list_hover_text\': TRUE_BLACK,\n        \n        # MainWindow-specific (pure black background, distinct from dialog bg)\n        \'window_bg\': TRUE_BLACK,\n        \'main_btn_bg\': BRAND_BLACK,\n        \'main_btn_text\': APP_TEXT,\n        \'main_btn_hover_bg\': APP_BORDER,\n        \'main_btn_pressed_bg\': GRAY_44,\n        \'main_btn_pressed_text\': TRUE_BLACK,\n        \'input_bg\': BRAND_BLACK,\n        \'input_text\': APP_TEXT,\n        \'input_border\': APP_BORDER,\n        \'label_bg\': TRUE_BLACK,\n        \'label_text\': APP_TEXT,\n        \'output_text_color\': BRAND_GOLD,\n        \'border_color\': APP_BORDER,\n        \'text_color\': APP_TEXT,\n        \n        # Diff / compare semantic highlight colors\n        \'diff_added_bg\':   SEMANTIC_DIFF_ADDED,\n        \'diff_removed_bg\': SEMANTIC_DIFF_REMOVED,\n        \'diff_changed_bg\': SEMANTIC_DIFF_CHANGED,\n\n        # RNV-NAMED-AND-USED (2026-10-04): the diff export\'s seven colors\n        # stood here too. The export is a standalone page, always light,\n        # and reads them from LIGHT by name; this copy was looked up by\n        # nothing. They are in LIGHT alone.\n\n        # Regex builder match highlight\n        \'regex_match_bg\': SEMANTIC_REGEX_MATCH,\n\n        # Image mode semi-transparent overlay values -- used only in image\n        # mode. DERIVED: a named color at a declared alpha, so a register\n        # move reaches them (RNV-DERIVE-ALPHA, 2026-09-25).\n        \'image_overlay_bg\':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        \'image_overlay_bg_dark\':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        \'image_overlay_checkbox\':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        \'image_scrollbar_border\':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GRAY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        \'image_scrollbar_handle\':      with_alpha(GRAY_44, SCROLLBAR_HANDLE_ALPHA),\n        # The image scrollbar hovers from DARK\'s \'accent\'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n        \'image_dropdown_bg\':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        \'image_dropdown_selection\':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        \'image_dropdown_border\':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n    }\n    \n    LIGHT: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        \'bg\': APP_SURFACE_LIGHT_3,\n        \'bg_secondary\': WHITE,\n        \'bg_tertiary\': GOLD_TEXT_GROUND_FLOOR,\n        \'bg_hover\': APP_HOVER_LIGHT,\n        \n        # Text\n        \'text\': TRUE_BLACK,\n        \'text_muted\': GRAY_66,\n        \'text_disabled\': APP_TEXT_DIM,\n        \n        # Borders\n        \'border\': GRAY_CC,\n        \'border_light\': GRAY_DD,\n        \'border_focus\': BRAND_DARK_GOLD,\n        \n        # Accent colors\n        \'accent\': BRAND_DARK_GOLD,\n        \'accent_hover\': BRAND_DARK_GOLD_DEEP,\n        \'accent_pressed\': BRAND_DARK_GOLD_PRESSED,\n        \'accent_ink\': BRAND_DARK_GOLD_DEEP,  # Accent when it carries text\n        \'accent_text\': WHITE,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: light\'s siblings. success and warning\n        # had no light variant before this and read 2.87 and 1.50\n        # on #f5f5f5 -- illegal as text, live, and unnoticed because\n        # the only boundary test in this repo covered the red.\n        \'success\': STATUS_SUCCESS_TEXT_LIGHT,\n        \'error\': STATUS_ERROR_TEXT_LIGHT,\n        \'warning\': STATUS_WARNING_TEXT_LIGHT,\n        \'info\': BRAND_DARK_GOLD_DEEP,\n        \n        # Special\n        \'selection_bg\': BRAND_DARK_GOLD,\n        \'selection_text\': WHITE,\n        \'scrollbar_bg\': GRAY_E0,\n        \'scrollbar_handle\': APP_TEXT_DIM,\n        \'scrollbar_handle_main\': APP_TEXT_DIM,\n        \'tooltip_border\': BRAND_DARK_GOLD,\n        \n        # Checkbox indicator\n        \'checkbox_indicator_bg\': WHITE,\n        \'checkbox_border\': APP_TEXT_DIM,\n        \n        # Dropdown / list hover\n        \'list_hover_bg\': BRAND_BLACK,\n        \'list_hover_text\': WHITE,\n        \n        # MainWindow-specific\n        \'window_bg\': APP_SURFACE_LIGHT_3,\n        \'main_btn_bg\': WHITE,\n        \'main_btn_text\': TRUE_BLACK,\n        \'main_btn_hover_bg\': APP_BORDER,\n        \'main_btn_pressed_bg\': GRAY_44,\n        \'main_btn_pressed_text\': WHITE,\n        \'input_bg\': WHITE,\n        \'input_text\': TRUE_BLACK,\n        \'input_border\': GRAY_CC,\n        \'label_bg\': APP_SURFACE_LIGHT_3,\n        \'label_text\': TRUE_BLACK,\n        \'output_text_color\': BRAND_DARK_GOLD,\n        \'border_color\': GRAY_CC,\n        \'text_color\': TRUE_BLACK,\n        \n        # Diff / compare semantic highlight colors\n        \'diff_added_bg\':   SEMANTIC_DIFF_ADDED_LIGHT,\n        \'diff_removed_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n        \'diff_changed_bg\': SEMANTIC_DIFF_CHANGED_LIGHT,\n\n        # Diff HTML export colors (standalone document — always light-styled)\n        \'diff_html_equal_bg\':  WHITE,\n        \'diff_html_insert_bg\': SEMANTIC_DIFF_ADDED_LIGHT,\n        \'diff_html_delete_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n        \'diff_html_header_bg\': GRAY_EE,\n        \'diff_html_line_num\':  GRAY_88,\n        \'diff_html_border\':    GRAY_DD,\n        \'diff_html_stats_text\':GRAY_66,\n\n        # Regex builder match highlight\n        \'regex_match_bg\': SEMANTIC_REGEX_MATCH_LIGHT,\n\n        # RNV-NAMED-AND-USED (2026-10-04): the image overlays\' eight values\n        # stood here too, the same derivations as DARK. Image mode reads\n        # them from DARK by name, as the note that stood with them said:\n        # "nothing reads these". They are in DARK alone.\n    }\n    \n', '    \n    # The two palettes live in utils/colors.py (#64 A, 2026-10-18), under the\n    # same names; these are the same two dicts, so everything that reads\n    # DialogStyleManager.DARK reads what it read.\n    DARK: ClassVar[dict[str, str]] = colors.DARK\n    LIGHT: ClassVar[dict[str, str]] = colors.LIGHT\n    \n')]

#: sha256 of every file as this round writes it
WANT = {'ARCHITECTURE.md': '65805409681ebff01bc9736468865bbc3f731131dc6a3070f5831c2ef4235c03', 'README.md': '81d57e8b8c868fdfb72a9bf67c912c63975ed1448edef43b1b4f9a52c626dbdd', 'brand_map.json': 'f206b6b17a9bff3de9179654e74e9bf653a590dbc97c0f445e75fd177684ac0c', 'tests/test_app_mirror.py': '6cd23f1f88cbae891bc311e1294877bf232b40af5babd9912cef108677f4c8ef', 'tests/test_brand_mirror.py': '299eb6886c043f8ebb716744c60589c393775bc8e3c24049e1752c011eb33038', 'tests/test_button_key_names.py': 'd9eaffe7f4f0f3e09f83945c8f5cbcb180f6ae7eaf243dde6538c52555471efa', 'tests/test_derived_values.py': '8c723f8f172d24c8cfbb4e98144eeb418fec02fcb258c043b4441bcfc3e9294f', 'tests/test_gold_as_text.py': '2bde09684a0511710a28f6085cdbdd7137b95f7e1d7392b8aa37615e05044098', 'tests/test_ladder_and_plate.py': '6995c9f340b08274716931ffd7454486acecff436bafb907c567439314ce066a', 'tests/test_named_and_used.py': '584b19e0db9a3e6c743914543bcad775b063578d5f7e3afc2de1f6d73a06dbab', 'tests/test_register_wiring.py': '49dd35b5df671ae4cd2618d6ea2df4b9437d54d1fc2399d8a90b76dc35959066', 'tests/test_tt_register.py': '1c1daf140185f552dbf5338f09628e53e333da900655b83010b93625102253fc', 'utils/colors.py': 'b0c1390266221927bc2480d7cd8064d17a8f86429b255889bcbc2153de7fd10f', 'utils/dialog_styles.py': '39464b3a23bb61b21dd6b4df0008006981dc926ca08da3b1f4ec2204bfb57d9c'}


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)


class _Modules:
    """Run module text as a module of this checkout, standing in for the one on
    disk: the round's own files are not on disk yet. A module registered here is
    also its package's attribute, as an import makes it, so `from utils import
    colors` finds it; both are put back on the way out."""

    def __init__(self, tree) -> None:
        self.tree = tree
        self.saved = []

    def __enter__(self):
        self.added = str(self.tree.root) not in sys.path
        if self.added:
            sys.path.insert(0, str(self.tree.root))
        return self

    def load(self, rel: str, text: str, register: bool = False):
        name = rel[:-3].replace("/", ".")
        module = types.ModuleType(name)
        module.__file__ = str(self.tree.root / rel)
        if register:
            parent_name, _, child = name.rpartition(".")
            parent = sys.modules.get(parent_name)
            self.saved.append((name, sys.modules.get(name), parent, child,
                               getattr(parent, child, None) if parent is not None else None))
            sys.modules[name] = module
            if parent is not None:
                setattr(parent, child, module)
        exec(compile(text, rel, "exec"), module.__dict__)
        return module

    def __exit__(self, *exc) -> None:
        for name, was, parent, child, attr in reversed(self.saved):
            if was is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = was
            if parent is not None:
                if attr is None:
                    if hasattr(parent, child):
                        delattr(parent, child)
                else:
                    setattr(parent, child, attr)
        if self.added:
            sys.path.remove(str(self.tree.root))


def _comparable(value) -> bool:
    """A value that says what it is: compared by ==, not by identity or by repr."""
    if isinstance(value, (types.ModuleType, types.FunctionType, type)) or callable(value):
        return False
    return type(value).__eq__ is not object.__eq__


def _values(namespace) -> dict:
    return {k: v for k, v in vars(namespace).items() if not k.startswith("__") and _comparable(v)}


def _same(a, b) -> bool:
    return type(a) is type(b) and a == b


def checks(tree) -> None:
    # ---- no value moves: the head's two files, then the round's, each run as written
    with _Modules(tree) as m:
        was_colors = m.load(COLOR_FILE, _original(tree, COLOR_FILE), register=True)
        was_styles = m.load(STYLES_FILE, _original(tree, STYLES_FILE)).DialogStyleManager
        colors = m.load(COLOR_FILE, tree.read(COLOR_FILE), register=True)
        styles = m.load(STYLES_FILE, tree.read(STYLES_FILE)).DialogStyleManager
        was, now = _values(was_colors), _values(colors)
        moved = sorted(k for k in was if not _same(was[k], now.get(k)))
        assert not moved, f"a value moved: {moved}"
        added = sorted(set(now) - set(was))
        assert added == sorted(PALETTES), f"{COLOR_FILE} defines other new names: {added}"
        assert len(was) >= 40, f"only {len(was)} values compared -- the comparison is blind"
        for name in PALETTES:
            assert _same(getattr(was_styles, name), getattr(colors, name)), \
                f"{name} in {COLOR_FILE} is not the palette DialogStyleManager held"
            assert getattr(styles, name) is getattr(colors, name), \
                f"DialogStyleManager.{name} is not {COLOR_FILE}'s {name}"
            assert len(getattr(colors, name)) > 40, f"{name} has only {len(getattr(colors, name))} keys"
        held, holds = _values(was_styles), _values(styles)
        assert sorted(held) == sorted(holds), \
            f"DialogStyleManager holds other names: {sorted(set(held) ^ set(holds))}"
        other = sorted(k for k in held if not _same(held[k], holds[k]))
        assert not other, f"DialogStyleManager serves other values: {other}"
    # ---- nothing is left at the old place: no palette is written in the style module
    written = [f"{STYLES_FILE}:{n.lineno}" for n in ast.walk(ast.parse(tree.read(STYLES_FILE)))
               if isinstance(n, (ast.Assign, ast.AnnAssign)) and isinstance(n.value, ast.Dict)
               and any(isinstance(t, ast.Name) and t.id in PALETTES
                       for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
    assert not written, f"a palette is still written in the style module: {written}"
    # ---- the map names where the palettes are
    brand_map = json.loads(tree.read("brand_map.json"))
    assert brand_map["color_file"] == COLOR_FILE, brand_map["color_file"]
    assert brand_map["palettes"] == [{"file": COLOR_FILE, "dict": name} for name in PALETTES], \
        brand_map["palettes"]
    # ---- every file this round writes, as it writes it
    assert sorted(tree.files) == sorted(WANT), f"this round writes {sorted(tree.files)}"
    assert not tree.deleted, f"this round removes {sorted(tree.deleted)}"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"

def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

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
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


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
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
