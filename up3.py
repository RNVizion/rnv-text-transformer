"""the register-wiring guard, tests/test_register_wiring.py, for rnv-text-transformer

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (d101615).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-30: "Yes do this" -- item 5 of decisions-pending-2026-09-29.md.

The picker, the mixer, the palette manager and the icon builder each carry
tests/test_register_wiring.py: no register value written as a literal in a
palette, every name a palette uses resolving to the register, and the light
palette naming only what the register has ruled. This app never had it. Its
palettes were wired to utils/colors.py before the fleet's wiring rounds, and
the 2026-09-07 register correction added test_tt_register.py for two light
values only.

The guard is derived for this app's two palettes, DARK and LIGHT (image mode
reads DARK). Both already pass: every entry is a name, or a with_alpha() of a
name, so the sweep looks inside a value as well as at it. REGISTERED is every
name utils/colors.py classes as the register's, at its value; LIGHT_RULED is
what the light palette names today, each of which has been through a ruling.
No application code moves, and no value.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-text-transformer'
SENTINEL = 'RNV-REGISTER-WIRING-GUARD'
SENTINEL_FILE = 'tests/test_tt_register.py'
GUARD = 'tests/test_register_wiring.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_register_wiring.py', 'tests/test_tt_register.py']
DESCRIPTION = 'the register-wiring guard, tests/test_register_wiring.py, for rnv-text-transformer'

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

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests.yml': '22c4f261f69cda029e0801f148e9b061e3bd65b5c9472b1bf321fc998b5a0434'}

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "base_dialog.py", "test_rnv_text_transformer.py", "test_register_wiring.py", "test_tt_register.py"}

LEFT_ALONE = ['utils/colors.py and utils/dialog_styles.py: nothing in them changes. The guard holds what is already true.', "test_tt_register.py's tests: unchanged. Its docstring gains one sentence pointing to the new guard, which is where this round's marker lives.", 'the derived names (BRAND_GOLD_HOVER, BRAND_DARK_GOLD_DEEP ...) and the ramp: not register values, so the sweep does not look for them.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('tests/test_tt_register.py',
             'whole failure mode was a check that only runs somewhere else.\n"""\n',
             'whole failure mode was a check that only runs somewhere else.\n\nRNV-REGISTER-WIRING-GUARD (2026-09-30): the fleet\'s wiring guard, which\nsweeps both palettes for any register value written as a literal, is\ntest_register_wiring.py. This file keeps the two light values it was\nwritten for.\n"""\n')
    if (tree.root / 'tests/test_register_wiring.py').exists():
        raise Stop('tests/test_register_wiring.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_register_wiring.py', '"""\nEvery registered value in the palettes spelled as a NAME.\n\nRNV-REGISTER-WIRING-GUARD, 2026-09-30. The picker, the mixer, the palette\nmanager and the icon builder each carry this test. This app never had it:\nits palettes were wired to utils/colors.py before the fleet\'s wiring rounds,\nand the register correction of 2026-09-07 (test_tt_register.py) covered two\nlight values only. Ruled 2026-09-30 that this app gets the same guard.\n\nNOTHING MOVED. Both palettes already pass: every entry is a name, or a\nwith_alpha() of a name. This holds that in place.\n\nTHE POINT OF IT. A literal cannot follow its base. APP["text"] moved on\n2026-08-28 and an app that had written the value down would have kept the\nold one silently. Every registered value in the palettes is a name, so the\nnext register move carries.\n\nWHAT IS DIFFERENT HERE. This app has two palettes, DARK and LIGHT, both class\nattributes of DialogStyleManager; image mode reads DARK. Both were wired at\nthe same time, so both halves are swept for literals, and the light allowlist\nis what the light palette names today, every entry of which has been through\na ruling (the light wiring, the gold rounds, the 2026-09-07 correction).\nEight entries in each palette are with_alpha(NAME, ALPHA) calls, so the\nsweep looks inside a value, not only at it.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom utils import colors\nfrom utils.dialog_styles import DialogStyleManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'utils/dialog_styles.py\'\n\n#: The register, as this app mirrors it: every name utils/colors.py classes\n#: as \'register\' in PROVENANCE, with the value it held when this was written.\n#: Value-keyed, because a literal is found by its value: any entry holding one\n#: of these must name it.\nREGISTERED = {\n    \'BRAND_GOLD\': \'#d2bc93\', \'BRAND_DARK_GOLD\': \'#8c7337\',\n    \'TRUE_BLACK\': \'#000000\', \'WHITE\': \'#ffffff\',\n    \'BRAND_BLACK\': \'#1a1a1a\', \'APP_CARD\': \'#2a2a2a\', \'APP_BORDER\': \'#333333\',\n    \'APP_TEXT\': \'#dddddd\', \'APP_TEXT_DIM\': \'#aaaaaa\', \'APP_PANEL_HOVER\': \'#3a3a3a\',\n    \'APP_HOVER_LIGHT\': \'#eeeeee\', \'APP_SURFACE_LIGHT_3\': \'#f5f5f5\',\n    \'GOLD_TEXT_GROUND_FLOOR\': \'#e8e8e8\',\n    \'STATUS_SUCCESS\': \'#926c89\', \'STATUS_WARNING\': \'#a2703c\', \'STATUS_ERROR\': \'#c75b64\',\n    \'STATUS_SUCCESS_TEXT\': \'#ad85a3\', \'STATUS_WARNING_TEXT\': \'#bc8752\',\n    \'STATUS_ERROR_TEXT\': \'#dd6f77\',\n    \'STATUS_SUCCESS_TEXT_LIGHT\': \'#825d79\', \'STATUS_WARNING_TEXT_LIGHT\': \'#8e5e2b\',\n    \'STATUS_ERROR_TEXT_LIGHT\': \'#ae4650\',\n}\n\nDARK_DICTS = (\'DARK\',)\nLIGHT_DICTS = (\'LIGHT\',)\n\n#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a\n#: per-mode difference gets checked against the other mode\'s value and passes.\nPALETTES = {\'DARK\': DialogStyleManager.DARK, \'LIGHT\': DialogStyleManager.LIGHT}\n\n#: The register\'s dark surface ladder and ink. The dark palette must name\n#: every one of these: a sweep that finds no literal because the palette\n#: stopped referencing the register would pass for the wrong reason.\nDARK_LADDER = (\'TRUE_BLACK\', \'BRAND_BLACK\', \'APP_CARD\', \'APP_BORDER\', \'APP_PANEL_HOVER\', \'APP_TEXT\')\n\n\ndef _dicts(names):\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    out = {}\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            name = getattr(target, \'id\', None)\n            if name in names and isinstance(node.value, ast.Dict):\n                out[name] = node.value\n    missing = set(names) - set(out)\n    assert not missing, f\'these palettes are no longer dict literals: {missing}\'\n    return out\n\n\ndef _names_in(value):\n    """Every NAME inside a palette value: the value itself, or the arguments\n    of a call such as with_alpha(NAME, ALPHA)."""\n    return {n.id for n in ast.walk(value) if isinstance(n, ast.Name)}\n\n\ndef _strings_in(value):\n    """Every string literal inside a palette value, however deep."""\n    return [n.value for n in ast.walk(value)\n            if isinstance(n, ast.Constant) and isinstance(n.value, str)]\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_palettes_this_file_reads_still_exist():\n    """Every assertion below walks these. If one is renamed or stops being a\n    dict literal, this fails loudly instead of the rest passing over nothing."""\n    assert _dicts(DARK_DICTS)\n    assert _dicts(LIGHT_DICTS)\n\n\ndef test_the_register_map_is_not_empty():\n    """A sweep with nothing to look for passes forever. The map is every name\n    PROVENANCE classes as the register\'s, at the value the module holds."""\n    assert len(REGISTERED) >= 4\n    for name, value in REGISTERED.items():\n        assert getattr(colors, name) == value, (\n            f\'{name} is {getattr(colors, name)}, not {value} -- the map this \'\n            f\'file sweeps for has gone stale against the constants\')\n    registered = {n for n, kind in colors.PROVENANCE.items() if kind == \'register\'}\n    assert set(REGISTERED) == registered, (\n        f\'PROVENANCE classes {sorted(registered - set(REGISTERED))} as the register\\\'s \'\n        f\'and this map does not; {sorted(set(REGISTERED) - registered)} the other way\')\n\n\n# ------------------------------------------------------------ the substitution\n\n@pytest.mark.parametrize(\'half\', [\'dark\', \'light\'])\ndef test_no_registered_value_is_spelled_as_a_literal(half):\n    """The completeness half. A literal cannot follow its base, so there must\n    not be one -- at the top of an entry or inside a with_alpha() call."""\n    by_value = {v: k for k, v in REGISTERED.items()}\n    literals = []\n    for dict_name, node in _dicts(DARK_DICTS if half == \'dark\' else LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if not isinstance(key, ast.Constant):\n                continue\n            for s in _strings_in(value):\n                if s.lower() in by_value:\n                    literals.append(f\'{dict_name}[{key.value!r}] holds {s} \'\n                                    f\'(should read {by_value[s.lower()]})\')\n    assert not literals, (\n        f\'registered values written as literals in the {half} palette:\\n  \'\n        + \'\\n  \'.join(literals))\n\n\ndef test_every_dark_entry_that_names_a_constant_resolves_to_the_register():\n    """The other half. A name is only worth having if it holds the right\n    value. An entry that is a with_alpha() of a name is checked on the name."""\n    wrong = []\n    for dict_name, node in _dicts(DARK_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id in REGISTERED:\n                actual = PALETTES[dict_name].get(key.value)\n                if actual != REGISTERED[value.id]:\n                    wrong.append(f\'{dict_name}[{key.value!r}] -> {value.id} \'\n                                 f\'resolves to {actual}\')\n    assert not wrong, \'names resolving wrongly:\\n  \' + \'\\n  \'.join(wrong)\n\n\ndef test_the_dark_palette_names_the_register_s_ladder():\n    """Guard the guard, again. If the palette stopped referencing the register\n    entirely, the sweep above would find no literals and pass -- for the wrong\n    reason. The register\'s dark surfaces and ink are anchored by name, not by\n    a count that fails when things get better."""\n    used = set()\n    for node in _dicts(DARK_DICTS).values():\n        for value in node.values:\n            used |= _names_in(value) & set(REGISTERED)\n    missing = set(DARK_LADDER) - used\n    assert not missing, (\n        f\'the dark palette no longer names {sorted(missing)} of the register\\\'s \'\n        f\'ladder; it names {sorted(used)}\')\n\n\n# --------------------------------------------------------------- the light half\n\n#: What the light palette may name from the register. Every entry has been\n#: through a ruling: the light surface #f5f5f5 and the light hover #eeeeee\n#: (rnv-brand rev 23 and 27, the 2026-09-07 correction), light ink and edges\n#: (TRUE_BLACK, APP_BORDER), the dark gold and the ground it is held to\n#: (BRAND_DARK_GOLD, GOLD_TEXT_GROUND_FLOOR, the gold rounds), the light\n#: status inks, WHITE, APP_TEXT_DIM and the one BRAND_BLACK the light list\n#: hover paints. A later pass extends this ON PURPOSE, in the commit that\n#: wires the value.\nLIGHT_RULED = (\n    \'APP_BORDER\', \'APP_HOVER_LIGHT\', \'APP_SURFACE_LIGHT_3\', \'APP_TEXT_DIM\',\n    \'BRAND_BLACK\', \'BRAND_DARK_GOLD\', \'GOLD_TEXT_GROUND_FLOOR\',\n    \'STATUS_ERROR_TEXT_LIGHT\', \'STATUS_SUCCESS_TEXT_LIGHT\', \'STATUS_WARNING_TEXT_LIGHT\',\n    \'TRUE_BLACK\', \'WHITE\',\n)\n\n\ndef test_the_light_palette_references_only_what_the_register_has_ruled():\n    """An allowlist, not a prohibition: the light palette names the register,\n    and each name it uses is one a ruling put there. A new one is added to\n    LIGHT_RULED in the same commit that wires it, or it is not wired."""\n    named = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            for name in sorted(_names_in(value) & set(REGISTERED)):\n                if name not in LIGHT_RULED:\n                    named.append(f\'{dict_name}[{key.value!r}] -> {name}\')\n    assert not named, (\n        \'the light palette references register values that are not ruled \'\n        \'for light:\\n  \' + \'\\n  \'.join(named)\n        + \'\\n\\nAdd the name to LIGHT_RULED in the same commit that wires it, \'\n          \'or do not wire it.\')\n\n\ndef test_the_ruled_light_values_are_actually_wired():\n    """The allowlist permits; this requires. An allowlist entry nothing uses is\n    a licence with no subject -- the same shape as a dead exemption."""\n    used = set()\n    for node in _dicts(LIGHT_DICTS).values():\n        for value in node.values:\n            used |= _names_in(value) & set(LIGHT_RULED)\n    assert used == set(LIGHT_RULED), (\n        f\'LIGHT_RULED lists {sorted(set(LIGHT_RULED) - used)} that the light \'\n        f\'palette does not use\')\n\n\ndef test_every_light_entry_that_names_a_constant_resolves_to_the_register():\n    """The light half of the resolution check, since both halves are wired."""\n    wrong = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id in REGISTERED:\n                actual = PALETTES[dict_name].get(key.value)\n                if actual != REGISTERED[value.id]:\n                    wrong.append(f\'{dict_name}[{key.value!r}] -> {value.id} \'\n                                 f\'resolves to {actual}\')\n    assert not wrong, \'names resolving wrongly:\\n  \' + \'\\n  \'.join(wrong)\n')


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


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    # ---- what the guard will hold, checked here first: this round adds a
    # guard to palettes that already pass it, and changes no value
    styles = ast.parse(tree.read("utils/dialog_styles.py"))
    palettes = {}
    for node in ast.walk(styles):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) in ("DARK", "LIGHT") \
                and isinstance(node.value, ast.Dict):
            palettes[node.target.id] = node.value
    assert set(palettes) == {"DARK", "LIGHT"}, f"the palettes are not the two dict literals: {sorted(palettes)}"
    colours = tree.read("utils/colors.py")
    prov = next(n for n in ast.parse(colours).body if isinstance(n, (ast.Assign, ast.AnnAssign))
                and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, "id", None) == "PROVENANCE")
    registered = {k.value for k, v in zip(prov.value.keys, prov.value.values) if v.value == "register"}
    assert registered == {'STATUS_SUCCESS_TEXT', 'APP_BORDER', 'BRAND_GOLD', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_SUCCESS', 'STATUS_WARNING_TEXT_LIGHT', 'TRUE_BLACK', 'STATUS_WARNING_TEXT', 'STATUS_ERROR', 'BRAND_BLACK', 'WHITE', 'BRAND_DARK_GOLD', 'APP_PANEL_HOVER', 'STATUS_ERROR_TEXT_LIGHT', 'GOLD_TEXT_GROUND_FLOOR', 'APP_SURFACE_LIGHT_3', 'APP_CARD', 'APP_HOVER_LIGHT', 'STATUS_WARNING', 'STATUS_ERROR_TEXT', 'APP_TEXT_DIM', 'APP_TEXT'}, \
        f"PROVENANCE's register names moved: {sorted(registered ^ {'STATUS_SUCCESS_TEXT', 'APP_BORDER', 'BRAND_GOLD', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_SUCCESS', 'STATUS_WARNING_TEXT_LIGHT', 'TRUE_BLACK', 'STATUS_WARNING_TEXT', 'STATUS_ERROR', 'BRAND_BLACK', 'WHITE', 'BRAND_DARK_GOLD', 'APP_PANEL_HOVER', 'STATUS_ERROR_TEXT_LIGHT', 'GOLD_TEXT_GROUND_FLOOR', 'APP_SURFACE_LIGHT_3', 'APP_CARD', 'APP_HOVER_LIGHT', 'STATUS_WARNING', 'STATUS_ERROR_TEXT', 'APP_TEXT_DIM', 'APP_TEXT'})}"
    values = {}
    for node in ast.parse(colours).body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id in registered and isinstance(node.value, ast.Constant):
            values[node.target.id] = node.value.value
    assert values == {'BRAND_GOLD': '#d2bc93', 'BRAND_DARK_GOLD': '#8c7337', 'TRUE_BLACK': '#000000', 'WHITE': '#ffffff', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333', 'APP_TEXT': '#dddddd', 'APP_TEXT_DIM': '#aaaaaa', 'APP_PANEL_HOVER': '#3a3a3a', 'APP_HOVER_LIGHT': '#eeeeee', 'APP_SURFACE_LIGHT_3': '#f5f5f5', 'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8', 'STATUS_SUCCESS': '#926c89', 'STATUS_WARNING': '#a2703c', 'STATUS_ERROR': '#c75b64', 'STATUS_SUCCESS_TEXT': '#ad85a3', 'STATUS_WARNING_TEXT': '#bc8752', 'STATUS_ERROR_TEXT': '#dd6f77', 'STATUS_SUCCESS_TEXT_LIGHT': '#825d79', 'STATUS_WARNING_TEXT_LIGHT': '#8e5e2b', 'STATUS_ERROR_TEXT_LIGHT': '#ae4650'}, "a register value in utils/colors.py is not the one the guard holds"
    by_value = {v: k for k, v in values.items()}
    for name, d in palettes.items():
        for k, v in zip(d.keys, d.values):
            for s in (n.value for n in ast.walk(v) if isinstance(n, ast.Constant) and isinstance(n.value, str)):
                assert s.lower() not in by_value, \
                    f"{name}[{k.value!r}] writes {s}, a register value, as a literal: the guard " \
                    f"would fail; wire it (as {by_value[s.lower()]}) before adding the guard"
    def names_in(d):
        return {n.id for v in d.values for n in ast.walk(v) if isinstance(n, ast.Name)} & registered
    assert {'APP_CARD', 'BRAND_BLACK', 'APP_BORDER', 'TRUE_BLACK', 'APP_PANEL_HOVER', 'APP_TEXT'} <= names_in(palettes["DARK"]), "the dark palette no longer names the register's ladder"
    assert names_in(palettes["LIGHT"]) == {'BRAND_BLACK', 'APP_BORDER', 'WHITE', 'BRAND_DARK_GOLD', 'STATUS_ERROR_TEXT_LIGHT', 'GOLD_TEXT_GROUND_FLOOR', 'APP_SURFACE_LIGHT_3', 'APP_HOVER_LIGHT', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_WARNING_TEXT_LIGHT', 'TRUE_BLACK', 'APP_TEXT_DIM'}, \
        f"the light palette names {sorted(names_in(palettes['LIGHT']))} of the register; " \
        f"LIGHT_RULED was derived as {sorted({'BRAND_BLACK', 'APP_BORDER', 'WHITE', 'BRAND_DARK_GOLD', 'STATUS_ERROR_TEXT_LIGHT', 'GOLD_TEXT_GROUND_FLOOR', 'APP_SURFACE_LIGHT_3', 'APP_HOVER_LIGHT', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_WARNING_TEXT_LIGHT', 'TRUE_BLACK', 'APP_TEXT_DIM'})}"

    # ---- the guard is the one derived, and the note is one sentence
    guard = tree.read(GUARD)
    g = ast.parse(guard)
    tests = [n.name for n in g.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert tests == ['test_the_palettes_this_file_reads_still_exist', 'test_the_register_map_is_not_empty', 'test_no_registered_value_is_spelled_as_a_literal', 'test_every_dark_entry_that_names_a_constant_resolves_to_the_register', 'test_the_dark_palette_names_the_register_s_ladder', 'test_the_light_palette_references_only_what_the_register_has_ruled', 'test_the_ruled_light_values_are_actually_wired', 'test_every_light_entry_that_names_a_constant_resolves_to_the_register'], f"the guard's tests moved: {tests}"
    def lit(name):
        for node in g.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
                return ast.literal_eval(node.value)
        raise AssertionError(f"the guard lost {name}")
    assert lit("REGISTERED") == {'BRAND_GOLD': '#d2bc93', 'BRAND_DARK_GOLD': '#8c7337', 'TRUE_BLACK': '#000000', 'WHITE': '#ffffff', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333', 'APP_TEXT': '#dddddd', 'APP_TEXT_DIM': '#aaaaaa', 'APP_PANEL_HOVER': '#3a3a3a', 'APP_HOVER_LIGHT': '#eeeeee', 'APP_SURFACE_LIGHT_3': '#f5f5f5', 'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8', 'STATUS_SUCCESS': '#926c89', 'STATUS_WARNING': '#a2703c', 'STATUS_ERROR': '#c75b64', 'STATUS_SUCCESS_TEXT': '#ad85a3', 'STATUS_WARNING_TEXT': '#bc8752', 'STATUS_ERROR_TEXT': '#dd6f77', 'STATUS_SUCCESS_TEXT_LIGHT': '#825d79', 'STATUS_WARNING_TEXT_LIGHT': '#8e5e2b', 'STATUS_ERROR_TEXT_LIGHT': '#ae4650'}, "the guard's REGISTERED is not the derived map"
    assert set(lit("LIGHT_RULED")) == {'BRAND_BLACK', 'APP_BORDER', 'WHITE', 'BRAND_DARK_GOLD', 'STATUS_ERROR_TEXT_LIGHT', 'GOLD_TEXT_GROUND_FLOOR', 'APP_SURFACE_LIGHT_3', 'APP_HOVER_LIGHT', 'STATUS_SUCCESS_TEXT_LIGHT', 'STATUS_WARNING_TEXT_LIGHT', 'TRUE_BLACK', 'APP_TEXT_DIM'}, "the guard's LIGHT_RULED is not the derived set"
    assert set(lit("DARK_LADDER")) == {'APP_CARD', 'BRAND_BLACK', 'APP_BORDER', 'TRUE_BLACK', 'APP_PANEL_HOVER', 'APP_TEXT'}, "the guard's DARK_LADDER moved"
    assert SENTINEL in guard, "the guard is not the one this round writes"
    old_note, new_note = _original(tree, "tests/test_tt_register.py"), tree.read("tests/test_tt_register.py")
    def sans_doc(src):
        mod = ast.parse(src)
        if mod.body and isinstance(mod.body[0], ast.Expr) and isinstance(mod.body[0].value, ast.Constant):
            mod.body = mod.body[1:]
        return ast.dump(mod)
    assert sans_doc(old_note) == sans_doc(new_note), "test_tt_register.py changed beyond its docstring"
    assert SENTINEL in ast.get_docstring(ast.parse(new_note)), "the note does not carry the sentinel"
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
