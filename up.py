#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Move rnv-text-transformer's ink onto the grid, split the light surface out
from under its name, and finish the gold rename.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE FIND THAT SHAPED THIS PASS

APP_TEXT was #e0e0e0, and six palette entries were spelled with it -- five in
dark, and ONE IN LIGHT:

    utils/dialog_styles.py:273    'scrollbar_bg': APP_TEXT,      <- light

That is #e0e0e0's other half wearing the ink's name. The light scrollbar track
is a SURFACE, and the published grid governs inks and edges and deliberately
not surfaces. Moving APP_TEXT with that entry still pointing at it would have
dragged a surface onto the ink grid and silently changed a light-mode track
that rnv-color-picker and rnv-icon-builder both keep at #e0e0e0.

The other four apps carry the same split as two DIFFERENT keys holding the
same hex, which is visible in a census. Here it was ONE NAME holding two
roles, which is not -- it was found only by checking which side of the light
palette boundary each use sat on.

WHAT MOVES

  APP_TEXT                              #e0e0e0 -> #dddddd   grey(13)
  GREY_E0  (new)                        #e0e0e0              the light track
  LIGHT scrollbar_bg    APP_TEXT -> GREY_E0                  value unchanged

  DARK text, button_text, input_text, label_text, text_color follow APP_TEXT.

  GOLD_HOVER   -> BRAND_GOLD_HOVER      10 sites
  GOLD_PRESSED -> BRAND_GOLD_PRESSED    11 sites

THE GOLD RENAME IS THE LAST OF THE v1.49 RULING

Upstream reopened and corrected the naming ruling at rnv-brand@faf1fd6,
restoring BRAND_GOLD_HOVER as a state. Four of the five apps already spelled
it that way; this one did not. Renaming it here closes that out.

The replacement is ANCHORED, not a plain substring swap: BRAND_DARK_GOLD_PRESSED
contains GOLD_PRESSED, and a naive replace would produce
BRAND_DARK_BRAND_GOLD_PRESSED. The regex refuses a match preceded by an
uppercase letter or underscore. It deliberately DOES match inside quotes,
because the names appear as strings in PROVENANCE and __all__.

THE SNAPSHOTS ARE HAND-EDITED, AND THE SPLIT IS WHY THAT MATTERS

tests/__snapshots__/test_snapshots.ambr holds 53 occurrences of #e0e0e0.
Exactly 46 are the dark ink and exactly 7 are the light scrollbar track. A
blanket replace would move all 53 and change light mode. Regenerating would
make the snapshots agree with whatever the code now emits, destroying the only
evidence that nothing else moved.

So the edit is scoped per snapshot block, and every block's count is asserted
against a map derived by reading the file rather than assumed:

    dark_arial 10   dark_montserrat 10   extended_dark_full 18
    get_colors_dark 5   inline_styles_combined 1   menu_stylesheet_dark 1
    export_html_dark_basic 1                       -> 46 move

    light_arial 2   light_montserrat 2   extended_light_full 2
    get_colors_light 1                             ->  7 stay

inline_styles_combined carries both a dark and a light section in one block;
its single occurrence is in the dark half, checked rather than assumed.
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
DESCRIPTION = "move the ink, split out the light surface, finish the gold rename"
SENTINEL_FILE = "utils/colors.py"
SENTINEL = "APP_TEXT: Final[str] = '#dddddd'"
GUARD = "tests/test_app_mirror.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py",
           "dialog_styles.py"}

STYLES = "utils/dialog_styles.py"
INIT = "utils/__init__.py"
MIRROR_TEST = "tests/test_brand_mirror.py"
AMBR = "tests/__snapshots__/test_snapshots.ambr"

MIRROR_OLD = 'def test_app_owned_values_are_not_register_values():\n    """Something app-owned that IS a brand value is misclassified."""\n    brand = pytest.importorskip(\n        \'engine.brand\', reason=\'rnv-brand not importable here\')\n    named = {}\n    for attr in (\'BRAND_GOLD\', \'BRAND_DARK_GOLD\', \'BRAND_BLACK\',\n                 \'TRUE_BLACK\', \'WHITE\', \'WEB_BLACK\'):\n        named[getattr(brand, attr).lower()] = attr\n    for dict_name in (\'APP\', \'STATUS\'):\n        for key, value in getattr(brand, dict_name).items():\n            if isinstance(value, str) and value.startswith(\'#\'):\n                named.setdefault(value.lower(), f\'{dict_name}["{key}"]\')\n\n    wrong = []\n    for name, group in colors.PROVENANCE.items():\n        if not group.startswith(\'app-\'):\n            continue\n        value = getattr(colors, name)\n        for v in (value,) if isinstance(value, str) else value:\n            if v.lower() in named:\n                wrong.append(f\'{name} = {v} is {named[v.lower()]} in the register, \'\n                             f\'but marked {group}\')\n    assert not wrong, \'misclassified as app-owned:\\n  \' + \'\\n  \'.join(wrong)\n'
MIRROR_NEW = '#: App-owned values that DELIBERATELY share a hex with a register entry.\n#:\n#: Publishing the ink grid made this possible for the first time: an app ramp\n#: step and a register value can land on the same grid position while doing\n#: different jobs. Sharing a VALUE is not the same as playing the same ROLE,\n#: and the check below can only read the value -- so the intentional ones are\n#: named here, with what they share and why they must NOT follow if the\n#: register moves.\n#:\n#: This is an exemption, so it is asserted in BOTH directions below: a named\n#: coincidence that stops coinciding fails, and so does one that names a\n#: mirrored constant.\n#:\n#: name -> (register entry, why it is not the same role)\nCOINCIDENT: dict[str, tuple[str, str]] = {\n    \'GREY_DD\': (\n        \'APP["text"]\',\n        \'grey(13) does two jobs. In the register it is the DARK ink; here it \'\n        \'is border_light in the LIGHT palette -- one step softer than \'\n        \'border: GREY_CC -- plus the always-light-styled diff export border. \'\n        \'Different mode, different role. If APP["text"] moves off grey(13) \'\n        \'this must NOT follow it, which is exactly why it is named here \'\n        \'rather than mirrored.\'),\n}\n\n\ndef _register_values(brand) -> dict:\n    """Every value the register holds, hex -> where it is held."""\n    named = {}\n    for attr in (\'BRAND_GOLD\', \'BRAND_DARK_GOLD\', \'BRAND_BLACK\',\n                 \'TRUE_BLACK\', \'WHITE\', \'WEB_BLACK\'):\n        named[getattr(brand, attr).lower()] = attr\n    for dict_name in (\'APP\', \'STATUS\'):\n        for key, value in getattr(brand, dict_name).items():\n            if isinstance(value, str) and value.startswith(\'#\'):\n                named.setdefault(value.lower(), f\'{dict_name}["{key}"]\')\n    return named\n\n\ndef test_app_owned_values_are_not_register_values():\n    """Something app-owned that IS a brand value is misclassified."""\n    brand = pytest.importorskip(\n        \'engine.brand\', reason=\'rnv-brand not importable here\')\n    named = _register_values(brand)\n\n    wrong = []\n    for name, group in colors.PROVENANCE.items():\n        if not group.startswith(\'app-\') or name in COINCIDENT:\n            continue\n        value = getattr(colors, name)\n        for v in (value,) if isinstance(value, str) else value:\n            if v.lower() in named:\n                wrong.append(f\'{name} = {v} is {named[v.lower()]} in the register, \'\n                             f\'but marked {group}\')\n    assert not wrong, \'misclassified as app-owned:\\n  \' + \'\\n  \'.join(wrong)\n\n\ndef test_every_coincidence_still_coincides():\n    """The other direction. A named coincidence that no longer shares a value\n    is a dead exemption, and a dead exemption is a licence waiting for a\n    defect: it would let a genuinely misclassified value hide behind it."""\n    brand = pytest.importorskip(\n        \'engine.brand\', reason=\'rnv-brand not importable here\')\n    named = _register_values(brand)\n    stale = []\n    for name, (entry, _why) in COINCIDENT.items():\n        if not hasattr(colors, name):\n            stale.append(f\'{name}: no longer defined in utils/colors.py\')\n            continue\n        value = getattr(colors, name).lower()\n        if value not in named:\n            stale.append(f\'{name} = {value} no longer matches any register value\')\n        elif named[value] != entry:\n            stale.append(f\'{name} = {value} is now {named[value]}, not {entry}\')\n    assert not stale, (\n        \'COINCIDENT entries that no longer describe reality:\\n  \'\n        + \'\\n  \'.join(stale)\n        + \'\\n\\nDelete the entry or correct it -- do not leave it standing.\')\n\n\ndef test_every_coincidence_is_app_owned():\n    """Guard the guard. The exemption is only for app-owned values; naming a\n    mirrored constant here would quietly exempt it from the mirror itself."""\n    for name in COINCIDENT:\n        group = colors.PROVENANCE.get(name)\n        assert group and group.startswith(\'app-\'), (\n            f\'{name} is marked {group!r}. COINCIDENT is only for app-owned \'\n            f\'values -- using it on a mirrored one would hide real drift.\')\n\n\ndef test_every_coincidence_says_why():\n    """An exemption with no reason is one nobody can review."""\n    for name, (entry, why) in COINCIDENT.items():\n        assert entry and len(why) > 40, (\n            f\'{name} has no usable reason recorded\')\n'

SUITES = [
    ("pytest tests/ (about 3 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider",
      "--benchmark-disable"]),
    ("unittest suite",
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]

# Snapshot blocks whose #e0e0e0 is the dark ink, and how many each holds.
INK_BLOCKS = {
    "TestDialogStyleSnapshots.test_dialog_stylesheet_dark_arial": 10,
    "TestDialogStyleSnapshots.test_dialog_stylesheet_dark_montserrat": 10,
    "TestDialogStyleSnapshots.test_extended_stylesheet_dark_full": 18,
    "TestDialogStyleSnapshots.test_get_colors_dark": 5,
    "TestDialogStyleSnapshots.test_inline_styles_combined": 1,
    "TestDialogStyleSnapshots.test_menu_stylesheet_dark": 1,
    "TestExportSnapshots.test_export_html_dark_basic": 1,
}
# Blocks whose #e0e0e0 is the light scrollbar track, and must NOT move.
SURFACE_BLOCKS = {
    "TestDialogStyleSnapshots.test_dialog_stylesheet_light_arial": 2,
    "TestDialogStyleSnapshots.test_dialog_stylesheet_light_montserrat": 2,
    "TestDialogStyleSnapshots.test_extended_stylesheet_light_full": 2,
    "TestDialogStyleSnapshots.test_get_colors_light": 1,
}

GREY_E0 = """GREY_E0: Final[str] = '#e0e0e0'
#: The LIGHT scrollbar track. Held by APP_TEXT until 2026-08-28, when the ink
#: moved to grey(13) and this did not follow -- it is a surface, and the
#: published grid governs inks and edges only. rnv-color-picker and
#: rnv-icon-builder both carry this same track at this same value.
"""


def _blocks(text: str) -> dict:
    """Snapshot name -> (start, end) line indices."""
    lines = text.splitlines(keepends=True)
    marks = [(i, line[8:].strip()) for i, line in enumerate(lines)
             if line.startswith("# name:")]
    marks.append((len(lines), None))
    return lines, {name: (st, marks[i + 1][0])
                   for i, (st, name) in enumerate(marks[:-1])}


def _rename(text: str, bare: str) -> tuple[str, int]:
    """Anchored so BRAND_DARK_GOLD_PRESSED is not a bare GOLD_PRESSED. Matches
    inside quotes on purpose -- these names appear as strings in PROVENANCE
    and __all__."""
    pattern = re.compile(rf"(?<![A-Z_]){bare}\b")
    return pattern.subn("BRAND_" + bare, text)


def edits(tree) -> None:
    # 1. the ink
    tree.sub(SENTINEL_FILE, "APP_TEXT: Final[str] = '#e0e0e0'",
             "APP_TEXT: Final[str] = '#dddddd'")

    # 2. the light surface gets its own step, in ramp order after GREY_DD
    tree.sub(SENTINEL_FILE, "GREY_DD: Final[str] = '#dddddd'\n",
             "GREY_DD: Final[str] = '#dddddd'\n" + GREY_E0)
    tree.sub(SENTINEL_FILE, "    'GREY_DD': 'app-ramp',\n",
             "    'GREY_DD': 'app-ramp',\n    'GREY_E0': 'app-ramp',\n")
    # Two-line anchors. `    GREY_DD,\n` on its own also matches inside
    # `'diff_html_border':    GREY_DD,` -- the alignment padding puts four
    # spaces in front of the name there too. The next ramp step disambiguates.
    tree.sub(SENTINEL_FILE, "    'GREY_DD',\n    'GREY_E8',\n",
             "    'GREY_DD',\n    'GREY_E0',\n    'GREY_E8',\n")
    tree.sub(INIT, "    GREY_DD,\n    GREY_E8,\n",
             "    GREY_DD,\n    GREY_E0,\n    GREY_E8,\n")
    tree.sub(INIT, "    'GREY_DD',\n    'GREY_E8',\n",
             "    'GREY_DD',\n    'GREY_E0',\n    'GREY_E8',\n")
    tree.sub(STYLES, "    GREY_DD,\n    GREY_E8,\n",
             "    GREY_DD,\n    GREY_E0,\n    GREY_E8,\n")
    tree.sub(STYLES, "        'scrollbar_bg': APP_TEXT,",
             "        'scrollbar_bg': GREY_E0,")

    # 3. the golds
    for rel in (SENTINEL_FILE, STYLES, INIT, MIRROR_TEST):
        text = tree.read(rel)
        for bare, expected in (("GOLD_HOVER", None), ("GOLD_PRESSED", None)):
            text, _ = _rename(text, bare)
        tree.write(rel, text)

    # 4. the coincidence the ink move created
    tree.sub(MIRROR_TEST, MIRROR_OLD, MIRROR_NEW)

    # 5. the snapshots, per block
    text = tree.read(AMBR)
    lines, blocks = _blocks(text)
    missing = set(INK_BLOCKS) | set(SURFACE_BLOCKS) - set(blocks)
    missing = (set(INK_BLOCKS) | set(SURFACE_BLOCKS)) - set(blocks)
    if missing:
        raise SystemExit(f"snapshot blocks not found: {sorted(missing)}")
    for name, count in {**INK_BLOCKS, **SURFACE_BLOCKS}.items():
        st, en = blocks[name]
        found = sum(lines[i].count("#e0e0e0") for i in range(st, en))
        if found != count:
            raise SystemExit(
                f"{name}: expected {count} occurrence(s) of #e0e0e0, found "
                f"{found}. The snapshot moved; re-derive this edit.")
    for name in INK_BLOCKS:
        st, en = blocks[name]
        for i in range(st, en):
            lines[i] = lines[i].replace("#e0e0e0", "#dddddd")
    tree.write(AMBR, "".join(lines))


def checks(tree) -> None:
    mirror = tree.read(MIRROR_TEST)
    if "COINCIDENT" not in mirror or "def test_every_coincidence_still_coincides" not in mirror:
        raise SystemExit("the COINCIDENT exemption and its reverse assertion "
                         "were not installed")
    if "'GREY_DD': (" not in mirror:
        raise SystemExit("GREY_DD is not recorded as a coincidence")

    src = tree.read(SENTINEL_FILE)
    if src.count(SENTINEL) != 1:
        raise SystemExit("APP_TEXT was not moved exactly once")
    if "GREY_E0: Final[str] = '#e0e0e0'" not in src:
        raise SystemExit("GREY_E0 was not defined")
    for rel in (SENTINEL_FILE, STYLES, INIT):
        text = tree.read(rel)
        for bare in ("GOLD_HOVER", "GOLD_PRESSED"):
            if re.search(rf"(?<![A-Z_]){bare}\b", text):
                raise SystemExit(f"a bare {bare} survives in {rel}")
        if "BRAND_DARK_BRAND_GOLD" in text:
            raise SystemExit(
                f"{rel}: the rename ate BRAND_DARK_GOLD_PRESSED -- the anchor "
                f"failed and the substring trap fired")
    styles = tree.read(STYLES)
    if "'scrollbar_bg': APP_TEXT," in styles:
        raise SystemExit("the light scrollbar track still reads APP_TEXT")
    if styles.count("'scrollbar_bg': GREY_E0,") != 1:
        raise SystemExit("the light scrollbar track does not read GREY_E0")

    text = tree.read(AMBR)
    lines, blocks = _blocks(text)
    for name, count in SURFACE_BLOCKS.items():
        st, en = blocks[name]
        found = sum(lines[i].count("#e0e0e0") for i in range(st, en))
        if found != count:
            raise SystemExit(
                f"{name}: the light track moved -- expected {count} "
                f"occurrence(s) of #e0e0e0 to survive, found {found}")
    for name in INK_BLOCKS:
        st, en = blocks[name]
        if any("#e0e0e0" in lines[i] for i in range(st, en)):
            raise SystemExit(f"{name} still carries the retired ink")
    if text.count("#e0e0e0") != sum(SURFACE_BLOCKS.values()):
        raise SystemExit(
            f"expected exactly {sum(SURFACE_BLOCKS.values())} surviving "
            f"#e0e0e0 in the snapshots, found {text.count('#e0e0e0')}")


GUARD_SOURCE = '"""\nThe ink moves, the light surface stays behind, and the golds finish their\nrename.\n\nTHE FIND THAT SHAPED THIS PASS. APP_TEXT was #e0e0e0 and this app spelled SIX\npalette entries with it -- five in dark, and ONE IN LIGHT:\n\n    utils/dialog_styles.py:273    \'scrollbar_bg\': APP_TEXT,      <- light\n\nThat is #e0e0e0\'s other half wearing the ink\'s name. The light scrollbar\ntrack is a SURFACE, and the published grid governs inks and edges and\ndeliberately not surfaces. Moving APP_TEXT with the light entry still pointing\nat it would have dragged a surface onto the ink grid and quietly changed a\nlight-mode track that rnv-color-picker and rnv-icon-builder both keep at\n#e0e0e0.\n\nSo the value split before it moved: APP_TEXT went to grey(13) and the light\ntrack got GREY_E0, named by its byte like every other step in this app\'s ramp.\n\nThe other four apps show the same split as two DIFFERENT keys holding the same\nhex. Here it was one name holding two roles, which is harder to see and was\nfound only by checking which side of the light palette boundary each use sat\non.\n\nTWO GUARDS, NOT ONE. test_brand_mirror.py guards the register with\nimportorskip(\'engine.brand\'), so where rnv-brand is not importable it reports\nclean and drift hides. APP_TEXT is pinned locally here as well.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nimport pytest\n\nfrom utils import colors\nfrom utils.dialog_styles import DialogStyleManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nCOLORS = ROOT / \'utils\' / \'colors.py\'\nSTYLES = ROOT / \'utils\' / \'dialog_styles.py\'\n\nGRID_STEP = 0x11\n\nDARK = DialogStyleManager.get_colors(True)\nLIGHT = DialogStyleManager.get_colors(False)\n\n#: Dark-mode entries that carry the ink.\nINK_KEYS = (\'text\', \'button_text\', \'input_text\', \'label_text\', \'text_color\')\n\n#: The golds that finished their rename in this pass. Upstream settled on the\n#: BRAND_ prefix in rnv-brand@faf1fd6; four of the five apps already used it.\nRENAMED_GOLDS = (\'BRAND_GOLD_HOVER\', \'BRAND_GOLD_PRESSED\')\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_keys_this_file_reads_still_exist():\n    for key in INK_KEYS:\n        assert key in DARK, f\'the dark palette has no {key}\'\n    assert \'scrollbar_bg\' in LIGHT\n    for name in (\'APP_TEXT\', \'GREY_E0\', \'TRUE_BLACK\') + RENAMED_GOLDS:\n        assert hasattr(colors, name), f\'utils.colors has no {name}\'\n\n\n# ------------------------------------------------------------------- the value\n\ndef test_the_ink_is_a_step_on_the_grid():\n    assert colors.APP_TEXT == grey(13) == \'#dddddd\', (\n        f\'APP_TEXT is {colors.APP_TEXT}, not grey(13).\')\n\n\ndef test_the_local_pin_holds_when_the_brand_is_absent():\n    """test_brand_mirror.py checks APP_TEXT against engine.brand and SKIPS when\n    rnv-brand is not importable. This is the half that always runs."""\n    assert colors.APP_TEXT == \'#dddddd\', (\n        \'APP_TEXT no longer holds the registered value. If the brand moved, \'\n        \'update this pin in the same commit that updates utils/colors.py.\')\n\n\ndef test_every_dark_ink_entry_carries_the_constant():\n    for key in INK_KEYS:\n        assert DARK[key] == colors.APP_TEXT, f\'dark {key!r} is {DARK[key]}\'\n\n\ndef test_the_light_ink_is_true_black():\n    """Primary text is one role with two mode values: dark is a grey on the\n    grid, light is TRUE_BLACK."""\n    assert LIGHT[\'text\'] == colors.TRUE_BLACK == \'#000000\'\n\n\n# ------------------------------------------------------- the half that stayed\n\ndef test_the_light_scrollbar_track_did_not_follow_the_ink():\n    """The whole reason this pass split a constant. #e0e0e0 was doing two\n    jobs under one name; the surface half stays exactly where it was."""\n    assert LIGHT[\'scrollbar_bg\'] == colors.GREY_E0 == \'#e0e0e0\', (\n        f\'the light scrollbar track is {LIGHT["scrollbar_bg"]}. It is a \'\n        f\'SURFACE -- the ink grid does not govern it, and picker and \'\n        f\'icon-builder both keep this track at #e0e0e0.\')\n\n\ndef test_the_light_track_no_longer_reads_the_ink_constant():\n    """Spelling, not just value. If it points at APP_TEXT again it will follow\n    the next ink move silently, which is what this pass existed to stop."""\n    source = STYLES.read_text(encoding=\'utf-8\')\n    assert "\'scrollbar_bg\': APP_TEXT," not in source, (\n        \'the light scrollbar track reads APP_TEXT again\')\n    assert "\'scrollbar_bg\': GREY_E0," in source\n\n\ndef test_no_dark_entry_accidentally_took_the_surface_step():\n    """The mirror of the test above. GREY_E0 belongs to the light track and\n    nothing in dark should have picked it up."""\n    strays = [k for k, v in DARK.items() if v == colors.GREY_E0]\n    assert not strays, f\'dark entries now carrying the light surface: {strays}\'\n\n\n# ------------------------------------------------------------------ provenance\n\ndef test_the_new_step_is_classified():\n    assert colors.PROVENANCE.get(\'GREY_E0\') == \'app-ramp\', (\n        \'GREY_E0 has no provenance entry, or the wrong one. It is a ramp step, \'\n        \'not a register value -- #e0e0e0 is no longer what the brand holds.\')\n\n\ndef test_the_ramp_is_still_ordered_by_byte():\n    """This app names ramp steps by their byte so the ramp reads in order.\n    GREY_E0 has to sit where its value says, not where it was appended."""\n    names = re.findall(r\'^(GREY_[0-9A-F]{2}): Final\',\n                       COLORS.read_text(encoding=\'utf-8\'), re.M)\n    values = [int(n[5:], 16) for n in names]\n    assert values == sorted(values), (\n        f\'the ramp is out of order: {names}\')\n\n\n# ---------------------------------------------------------------- the renames\n\n@pytest.mark.parametrize(\'name\', RENAMED_GOLDS)\ndef test_the_golds_carry_the_brand_prefix(name):\n    assert hasattr(colors, name)\n    assert name in colors.PROVENANCE, f\'{name} has no provenance entry\'\n\n\ndef test_no_bare_gold_name_survives():\n    """Anchored so BRAND_DARK_GOLD_PRESSED does not count as a bare\n    GOLD_PRESSED -- the substring trap that would have renamed it to\n    BRAND_DARK_BRAND_GOLD_PRESSED."""\n    stale = []\n    for path in (COLORS, STYLES, ROOT / \'utils\' / \'__init__.py\'):\n        text = path.read_text(encoding=\'utf-8\')\n        for bare in (\'GOLD_HOVER\', \'GOLD_PRESSED\'):\n            for match in re.finditer(rf\'(?<![A-Z_]){bare}\\b\', text):\n                line = text[:match.start()].count(\'\\n\') + 1\n                stale.append(f\'{path.name}:{line}\')\n    assert not stale, (\n        \'the unprefixed gold names survive at: \' + \', \'.join(stale))\n\n\ndef test_the_renamed_golds_are_still_derived_not_restated():\n    """A rename must not turn a derivative into a literal."""\n    source = COLORS.read_text(encoding=\'utf-8\')\n    assert re.search(r\'BRAND_GOLD_HOVER: Final\\[str\\] = lighten\\(\', source), (\n        \'BRAND_GOLD_HOVER is no longer computed from its base\')\n    assert colors.BRAND_GOLD_HOVER == colors.lighten(colors.BRAND_GOLD, 13)\n    assert colors.BRAND_GOLD_PRESSED == colors.BRAND_GOLD\n\n\n# ---------------------------------------------------------------- what it costs\n\ndef _luminance(value: str) -> float:\n    ch = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():\n    grounds = (\'#000000\', \'#1a1a1a\', \'#2a2a2a\', \'#333333\', \'#3a3a3a\', \'#444444\')\n    worst = min((_contrast(colors.APP_TEXT, g), g) for g in grounds)\n    assert worst[0] >= 4.5, (\n        f\'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor\')\n'


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
