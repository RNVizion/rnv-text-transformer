"""derive every image-mode alpha colour from its base

    python up.py             # apply, then run the guard and CI's two commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head.

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-24. Every image-mode colour written at an alpha becomes
with_alpha(BASE, ALPHA) -- this application's own helper -- so a change to a
base ripples to every alpha form of it. One pixel moves, by ruling: the
image scrollbar handle leaves #505050 for GREY_44 at the same alpha, 150.

One unread key is left as it is, and pinned unread. The snapshot is edited,
not regenerated: sixteen named lines, so anything else that moved still fails.
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
SENTINEL = 'RNV-DERIVE-ALPHA'
SENTINEL_FILE = "tests/conftest.py"
GUARD = "tests/test_derived_values.py"
DESCRIPTION = 'derive every image-mode alpha colour from its base'

#: EXACTLY WHAT CI RUNS, both steps, under coverage as the workflow does. The
#: first is the locked root suite, which `pytest tests/` never reaches -- the
#: icon-builder round went red in CI on exactly that.
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

#: The workflow SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests.yml': '22c4f261f69cda029e0801f148e9b061e3bd65b5c9472b1bf321fc998b5a0434'}

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py",
           "test_rnv_text_transformer.py"}

LEFT_ALONE = [
    "image_scrollbar_handle_hover, rgba(100, 100, 100, 200), in both dicts. "
    "Nothing reads it; the image scrollbar hovers from DARK's accent. It has "
    "no register row to follow, and the painted gold cannot go in LIGHT -- a "
    "third gold there breaks the two-golds rule. Remove it, or keep it: a "
    "ruling. A test now fails if anything starts reading it.",
    "LIGHT's nine image keys. Image mode reads DARK, so nothing reads them; "
    "they take the same derivations so the two dicts stay one statement.",
    "with_alpha()'s spelling -- alpha upper case, colour as given, "
    "'#BF1a1a1a'. It is this application's existing helper and output; "
    "whether eight-digit hex falls under the register's lower-case rule is "
    "a question for rnv-brand, and it has not ruled.",
    "the picker and the mixer, which each get their own round; the palette "
    "manager's round was delivered separately.",
    "the chart's element resolver, which must learn that a derived value is "
    "a call -- here with_alpha(), in the icon builder and the palette "
    "manager translucent().",
]

GUARD_SOURCE = '"""Derived values: a colour that is a named colour AT AN ALPHA.\n\nImage mode draws its chrome translucent, and until 2026-09-25 every one of\nthose values was written out: \'rgba(26, 26, 26, 191)\' beside BRAND_BLACK, with\nnothing relating the two. A change to BRAND_BLACK would have reached every\nopaque use of it and none of these. Each is now with_alpha(BASE, ALPHA) -- the\nhelper this application already had, and already used for the drag highlight\n-- so the register row carries every alpha form of its colour.\n\nWHAT MOVES A PIXEL: ONE THING, BY RULING. The image-mode scrollbar handle\nleaves #505050 for GREY_44, closing RNV-COLLAPSE-505050 here; its alpha stays\nat 150. Everything else keeps its colour and its alpha byte, respelled from\nrgba() to #AARRGGBB -- the same pixels, in the one spelling QColor() can also\nread. test_nothing_moved_that_was_not_ruled holds that to the byte.\n\nAND ONE KEY THAT NOTHING READS, LEFT AS IT IS. image_scrollbar_handle_hover\nholds rgba(100, 100, 100, 200), a grey on no register row, while the image\nscrollbar\'s hover is painted from DARK\'s \'accent\' -- BRAND_GOLD, ruled\n2026-09-12. It is not derived, because there is no row for it to follow; and\nit cannot simply take the painted gold, because LIGHT carries the same image\nkeys and a BRAND_GOLD there is a third gold in a mode the brand allows two.\nA test pins that nothing reads it.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nfrom utils import colors\nfrom utils.colors import with_alpha\nfrom utils.dialog_styles import DialogStyleManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSTYLES = ROOT / "utils" / "dialog_styles.py"\nDRAG = ROOT / "ui" / "drag_drop_text_edit.py"\nPALETTES = {"DARK": DialogStyleManager.DARK, "LIGHT": DialogStyleManager.LIGHT}\n\n#: constant -> the byte. Every one is the integer alpha the rgba() literal it\n#: replaced already carried: nothing was fractional, so nothing was measured\n#: and nothing rounds.\nALPHAS = {\n    "IMAGE_FIELD_ALPHA": 0xAB,\n    "IMAGE_LABEL_ALPHA": 0xBF,\n    "IMAGE_CHECKBOX_ALPHA": 0x64,\n    "SCROLLBAR_BORDER_ALPHA": 0x64,\n    "SCROLLBAR_HANDLE_ALPHA": 0x96,\n    "DROPDOWN_BG_ALPHA": 0x83,\n    "DROPDOWN_SELECTION_ALPHA": 0xC8,\n    "DROPDOWN_BORDER_ALPHA": 0x96,\n    "DRAG_HIGHLIGHT_ALPHA": 0xBF,\n}\n\n#: What each image value is MADE OF: the constant its colour comes from, and its\n#: alpha byte -- the byte its rgba() literal already carried, and the colour\n#: that literal spelled, except the scrollbar handle\'s, which was ruled.\n#: By NAME, not by hex: see test_nothing_moved_that_was_not_ruled.\nMADE_OF = {\n    "image_overlay_bg": ("TRUE_BLACK", 171),\n    "image_overlay_bg_dark": ("BRAND_BLACK", 191),\n    "image_overlay_checkbox": ("TRUE_BLACK", 100),\n    "image_scrollbar_border": ("APP_BORDER", 100),\n    "image_scrollbar_handle": ("GREY_44", 150),     # was #505050, ruled\n    "image_dropdown_bg": ("TRUE_BLACK", 131),\n    "image_dropdown_selection": ("APP_BORDER", 200),\n    "image_dropdown_border": ("APP_BORDER", 150),\n}\nUNREAD = "image_scrollbar_handle_hover"\n\n_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")\n_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\\b|\\brgba\\(\\s*\\d{1,3}\\s*,\\s*\\d{1,3}"\n                       r"\\s*,\\s*\\d{1,3}\\s*,\\s*[0-9]*\\.?[0-9]+\\s*\\)")\n_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\\b")\n_FUNC = re.compile(r"\\brgba?\\(\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})"\n                   r"\\s*(?:,\\s*[0-9]*\\.?[0-9]+\\s*)?\\)")\nSKIP_DIRS = {".git", "tests", "build", "dist", ".venv", "venv", "__pycache__"}\n\n\ndef decompose(value: str) -> tuple[str, int] | None:\n    """(base \'#rrggbb\', alpha byte) -- taken apart, never rebuilt, so a fault\n    in with_alpha() cannot also be a fault here."""\n    m = _HEX8.match(value)\n    if m:\n        return "#" + m.group(2).lower(), int(m.group(1), 16)\n    return None\n\n\ndef _parts_of(spelled: str) -> tuple[str, int]:\n    """(base, alpha byte) for any composed spelling, with Qt\'s own reading of a\n    fractional alpha: it TRUNCATES, so 0.3 is 76."""\n    if spelled.startswith("#"):\n        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)\n    numbers = re.findall(r"[0-9]*\\.?[0-9]+", spelled)\n    r, g, b = (int(x) for x in numbers[:3])\n    a = numbers[3]\n    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a\n                                         else int(a))\n\n\ndef colours_in(text: str) -> set[str]:\n    """Every colour in a string, as #rrggbb. #AARRGGBB is alpha FIRST."""\n    found = set()\n    for m in _HEX.finditer(text):\n        h = m.group(0)[1:].lower()\n        h = h[2:] if len(h) == 8 else ("".join(c * 2 for c in h) if len(h) == 3 else h)\n        found.add("#" + h)\n    for m in _FUNC.finditer(text):\n        channels = [int(g) for g in m.groups()]\n        if all(c <= 255 for c in channels):\n            found.add("#%02x%02x%02x" % tuple(channels))\n    return found\n\n\ndef _sources():\n    """Application source: not tests, not a root test suite, not a delivery\n    script. Yields (relative path, parsed tree)."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in SKIP_DIRS for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, ast.parse(text)\n\n\ndef _bare_strings(tree: ast.AST) -> set[int]:\n    """Docstrings and every other string nobody evaluates -- mentions."""\n    bare = set()\n    for node in ast.walk(tree):\n        body = getattr(node, "body", None)\n        if isinstance(body, list):\n            for st in body:\n                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):\n                    bare.add(id(st.value))\n    return bare\n\n\ndef _derived():\n    """(where, call node, resolved value) for every with_alpha() call in the\n    palettes and in the drag highlight."""\n    out = []\n    tree = ast.parse(STYLES.read_text(encoding="utf-8-sig"))\n    cls = next(n for n in tree.body\n               if isinstance(n, ast.ClassDef) and n.name == "DialogStyleManager")\n    for node in cls.body:\n        if not isinstance(node, (ast.Assign, ast.AnnAssign)):\n            continue\n        target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n        name = getattr(target, "id", None)\n        if name in PALETTES and isinstance(node.value, ast.Dict):\n            for k, v in zip(node.value.keys, node.value.values):\n                if isinstance(v, ast.Call) and getattr(v.func, "id", None) == "with_alpha":\n                    out.append((f"{name}[{k.value!r}]", v, PALETTES[name][k.value]))\n    drag = ast.parse(DRAG.read_text(encoding="utf-8-sig"))\n    for node in ast.walk(drag):\n        if (isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None)\n                == "_DRAG_HIGHLIGHT" and isinstance(node.value, ast.Call)):\n            from ui.drag_drop_text_edit import DragDropTextEdit\n            out.append(("DragDropTextEdit._DRAG_HIGHLIGHT", node.value,\n                        DragDropTextEdit._DRAG_HIGHLIGHT))\n    return out\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_with_alpha_composes_alpha_first():\n    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and\n    the wrong one, which is the failure that does not look like a failure."""\n    assert with_alpha("#1a1a1a", 0xBF) == "#BF1a1a1a"\n    assert decompose(with_alpha("#d2bc93", 0x33)) == ("#d2bc93", 0x33)\n    assert decompose(with_alpha("444444", 0x96)) == ("#444444", 0x96)\n\n\ndef test_the_alphas_are_the_declared_bytes():\n    for name, byte in ALPHAS.items():\n        assert hasattr(colors, name), f"utils.colors has no {name}"\n        value = getattr(colors, name)\n        assert type(value) is int, f"{name} is {value!r}, not an int byte"\n        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"\n\n\ndef test_the_derivation_sweep_is_looking():\n    """Every check below iterates _derived(). If it came back empty they\n    would all pass over nothing."""\n    where = {w for w, _c, _v in _derived()}\n    want = {f"{p}[{k!r}]" for p in PALETTES for k in MADE_OF}\n    want.add("DragDropTextEdit._DRAG_HIGHLIGHT")\n    assert want <= where, sorted(want - where)\n\n\n# ----------------------------------------------------------- the derivations\n\ndef test_every_derived_value_names_constants_that_exist():\n    """with_alpha(BASE, ALPHA) where both are names: a literal in either\n    position is the thing this round removed."""\n    bad = []\n    for where, call, _value in _derived():\n        if len(call.args) != 2 or call.keywords:\n            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA)")\n            continue\n        base, alpha = call.args\n        for pos, arg in (("base", base), ("alpha", alpha)):\n            if not isinstance(arg, ast.Name):\n                bad.append(f"{where}: the {pos} is {ast.unparse(arg)}, not a name")\n            elif not hasattr(colors, arg.id):\n                bad.append(f"{where}: the {pos} names {arg.id}, which "\n                           f"utils.colors does not define")\n        if isinstance(base, ast.Name) and hasattr(colors, base.id):\n            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(colors, base.id))):\n                bad.append(f"{where}: the base {base.id} is not a six-digit colour")\n        if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:\n            bad.append(f"{where}: the alpha {alpha.id} is not a declared "\n                       f"composite alpha")\n    assert not bad, "derived values that do not derive:\\n  " + "\\n  ".join(bad)\n\n\ndef test_every_derived_value_decomposes_to_its_base_and_its_alpha():\n    """TAKEN APART, not rebuilt -- the entry IS with_alpha()\'s output, so\n    recomputing it would compare the call with itself."""\n    wrong = []\n    for where, call, value in _derived():\n        base, alpha = call.args\n        parts = decompose(value)\n        want = (getattr(colors, base.id).lower(), getattr(colors, alpha.id))\n        if parts != want:\n            wrong.append(f"{where} is {value!r}, which takes apart to {parts}, "\n                         f"not {base.id}/{alpha.id} {want}")\n    assert not wrong, "derived values that do not match:\\n  " + "\\n  ".join(wrong)\n\n\ndef test_no_composed_literal_is_left_in_the_application():\n    """The completeness half. Every EVALUATED string in the application\'s own\n    source that spells a named colour at an alpha. Docstrings are mentions --\n    utils/colors.py shows \'#BFd2bc93\' as an example, and that is prose.\n    Alpha 0 is not a colour; a base no constant names has no row to follow."""\n    named = {v.lower() for n, v in vars(colors).items()\n             if n.isupper() and isinstance(v, str)\n             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}\n    strays, files = [], 0\n    for rel, tree in _sources():\n        files += 1\n        bare = _bare_strings(tree)\n        for node in ast.walk(tree):\n            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):\n                continue\n            if id(node) in bare:\n                continue\n            for spelled in _COMPOSED.findall(node.value):\n                base, alpha = _parts_of(spelled)\n                if alpha and base in named:\n                    strays.append(f"{rel}:{node.lineno}  {spelled}")\n    assert files >= 40, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, ("composed values still written out rather than "\n                        "derived:\\n  " + "\\n  ".join(strays))\n\n\n# --------------------------------------------------- what moved, and what not\n\ndef test_the_scrollbar_handle_is_grey_44_at_150():\n    """RNV-COLLAPSE-505050, closed here 2026-09-25. Ruled 2026-09-02, and\n    written out as rgba(80, 80, 80, 150) in both palettes until now."""\n    for mode, palette in PALETTES.items():\n        assert decompose(palette["image_scrollbar_handle"]) == (\n            colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA), mode\n    assert colors.SCROLLBAR_HANDLE_ALPHA == 150\n\n\ndef test_nothing_moved_that_was_not_ruled():\n    """Each image value, held to what it is MADE OF: the constant its colour\n    comes from and its alpha byte.\n\n    BY NAME, NOT BY HEX, and that is the point of the round. A register move\n    is meant to pass straight through these values; a test that pinned\n    \'#333333\' would fail the first time one did and ask a person to edit it\n    by hand -- the job derivation exists to remove. What this DOES catch is a\n    value quietly re-made from something else, which the decomposition check\n    accepts as long as source and value agree with each other.\n\n    The byte-for-byte before-and-after was checked once, by the delivery\n    script, against the edited module before it was written."""\n    for mode, palette in PALETTES.items():\n        for key, (base, alpha) in MADE_OF.items():\n            assert decompose(palette[key]) == (getattr(colors, base).lower(), alpha), (\n                f"{mode}[{key!r}] is {palette[key]}, which is not {base} at "\n                f"{alpha}")\n    from ui.drag_drop_text_edit import DragDropTextEdit\n    assert decompose(DragDropTextEdit._DRAG_HIGHLIGHT) == (colors.BRAND_GOLD, 0xBF)\n\n\ndef test_the_unread_hover_key_stays_unread():\n    """image_scrollbar_handle_hover is read by nothing: the image scrollbar\n    hovers from DARK\'s \'accent\', BRAND_GOLD, ruled 2026-09-12. It still holds\n    rgba(100, 100, 100, 200) -- a grey on no register row, left because there\n    is nothing to derive it from and the gold would be a third gold in LIGHT.\n\n    If anything starts reading it, this fails: the value would then be a grey\n    hover on screen, against the gold ruling, and it has to be decided rather\n    than inherited."""\n    assert DialogStyleManager.DARK["accent"] == colors.BRAND_GOLD\n    readers, keys = [], 0\n    for rel, tree in _sources():\n        # the dict KEYS that declare it are not reads; anything else is,\n        # including a lookup inside dialog_styles.py itself\n        declared = {id(k) for node in ast.walk(tree) if isinstance(node, ast.Dict)\n                    for k in node.keys if k is not None}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and node.value == UNREAD:\n                if id(node) in declared:\n                    keys += 1\n                else:\n                    readers.append(f"{rel}:{node.lineno}")\n    assert keys == 2, f"expected the key declared in DARK and LIGHT, found {keys}"\n    assert not readers, f"{UNREAD} is read now: {readers}"\n\n\ndef test_the_collapsed_value_is_gone_in_every_spelling():\n    """#505050 in any string spelling -- #rgb, #rrggbb, #aarrggbb, rgb(),\n    rgba() -- or as integers in a tuple or a QColor call. The sweeps that\n    reported it gone elsewhere compared quoted six-digit hex and nothing\n    else; that is how it survived three weeks after its ruling."""\n    found = []\n    for rel, tree in _sources():\n        bare = _bare_strings(tree)\n        for node in ast.walk(tree):\n            if (isinstance(node, ast.Constant) and isinstance(node.value, str)\n                    and id(node) not in bare and "#505050" in colours_in(node.value)):\n                found.append(f"{rel}:{node.lineno}  {node.value[:40]!r}")\n            values = None\n            if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):\n                values = node.elts\n            elif isinstance(node, ast.Call) and len(node.args) >= 3 and (\n                    getattr(node.func, "id", None) or getattr(node.func, "attr", None)\n                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):\n                values = node.args\n            if values:\n                ints = tuple(v.value for v in values[:3]\n                             if isinstance(v, ast.Constant) and type(v.value) is int)\n                if ints == (80, 80, 80):\n                    found.append(f"{rel}:{node.lineno}  (80, 80, 80)")\n    assert not found, "#505050 is still here:\\n  " + "\\n  ".join(found)\n    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"\n\n# RNV-DERIVE-ALPHA\n'


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact count before anything is written."""
    tree.sub('utils/colors.py',
             '    return f"#{alpha:02X}{rgb}"\n\n\n# ==================== PROVENANCE ====================\n',
             '    return f"#{alpha:02X}{rgb}"\n\n\n# ==================== COMPOSITE ALPHAS ====================\n#\n# A composite is a named colour AT AN ALPHA: with_alpha(BASE, ALPHA). The colour\n# half is a name, so a register move reaches it; the alpha half is one of these,\n# so the same move carries every alpha form of that colour with it. Until\n# 2026-09-25 image mode wrote all of them out as rgba() and nothing related\n# \'rgba(26, 26, 26, 191)\' to BRAND_BLACK.\n#\n# Each byte is the one the literal it replaced already carried. They were all\n# integers, so nothing was measured and nothing rounds.\n#\n# TWO BYTES APPEAR TWICE, UNDER DIFFERENT NAMES, ON PURPOSE. The scrollbar edge\n# and the checkbox ground are both 100; the scrollbar handle and the dropdown\n# edge are both 150. Identical numbers doing unrelated jobs stay separate, or\n# retuning one silently retunes the other.\n\nIMAGE_FIELD_ALPHA: Final[int] = 0xAB\n"""171. The input field, its label and the label bar, in image mode (TRUE_BLACK)."""\n\nIMAGE_LABEL_ALPHA: Final[int] = 0xBF\n"""191. The status, output and stats labels in image mode (BRAND_BLACK)."""\n\nIMAGE_CHECKBOX_ALPHA: Final[int] = 0x64\n"""100. The checkbox indicator\'s ground in image mode (TRUE_BLACK)."""\n\nSCROLLBAR_BORDER_ALPHA: Final[int] = 0x64\n"""100. The image-mode scrollbar edge (APP_BORDER)."""\n\nSCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96\n"""150. The image-mode scrollbar handle (GREY_44). The byte all five\napplications use; its colour was #505050 until 2026-09-25."""\n\nDROPDOWN_BG_ALPHA: Final[int] = 0x83\n"""131. The image-mode dropdown list\'s ground (TRUE_BLACK)."""\n\nDROPDOWN_SELECTION_ALPHA: Final[int] = 0xC8\n"""200. The image-mode dropdown selection (APP_BORDER)."""\n\nDROPDOWN_BORDER_ALPHA: Final[int] = 0x96\n"""150. The image-mode dropdown list\'s edge (APP_BORDER)."""\n\nDRAG_HIGHLIGHT_ALPHA: Final[int] = 0xBF\n"""191, 75%. The drop-target highlight on a text pane (BRAND_GOLD). The one\ncomposite this application already derived; its byte was written in place."""\n\n\n# ==================== PROVENANCE ====================\n', 1)
    tree.sub('utils/colors.py',
             "    'lighten',\n    'with_alpha',\n",
             "    'lighten',\n    'with_alpha',\n    'IMAGE_FIELD_ALPHA',\n    'IMAGE_LABEL_ALPHA',\n    'IMAGE_CHECKBOX_ALPHA',\n    'SCROLLBAR_BORDER_ALPHA',\n    'SCROLLBAR_HANDLE_ALPHA',\n    'DROPDOWN_BG_ALPHA',\n    'DROPDOWN_SELECTION_ALPHA',\n    'DROPDOWN_BORDER_ALPHA',\n    'DRAG_HIGHLIGHT_ALPHA',\n", 1)
    tree.sub('utils/dialog_styles.py',
             '    BRAND_DARK_GOLD_PRESSED,\n)\n',
             '    BRAND_DARK_GOLD_PRESSED,\n    with_alpha,\n    IMAGE_FIELD_ALPHA,\n    IMAGE_LABEL_ALPHA,\n    IMAGE_CHECKBOX_ALPHA,\n    SCROLLBAR_BORDER_ALPHA,\n    SCROLLBAR_HANDLE_ALPHA,\n    DROPDOWN_BG_ALPHA,\n    DROPDOWN_SELECTION_ALPHA,\n    DROPDOWN_BORDER_ALPHA,\n)\n', 1)
    tree.sub('utils/dialog_styles.py',
             "        # Image mode semi-transparent overlay values (rgba — used only in image mode)\n        'image_overlay_bg':            'rgba(0, 0, 0, 171)',\n        'image_overlay_bg_dark':       'rgba(26, 26, 26, 191)',\n        'image_overlay_checkbox':      'rgba(0, 0, 0, 100)',\n        'image_scrollbar_border':      'rgba(51, 51, 51, 100)',\n        'image_scrollbar_handle':      'rgba(80, 80, 80, 150)',\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n        'image_dropdown_bg':           'rgba(0, 0, 0, 131)',\n        'image_dropdown_selection':    'rgba(51, 51, 51, 200)',\n        'image_dropdown_border':       'rgba(51, 51, 51, 150)',\n    }\n    \n    LIGHT:",
             "        # Image mode semi-transparent overlay values -- used only in image\n        # mode. DERIVED: a named colour at a declared alpha, so a register\n        # move reaches them (RNV-DERIVE-ALPHA, 2026-09-25).\n        'image_overlay_bg':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        'image_overlay_bg_dark':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        'image_overlay_checkbox':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        'image_scrollbar_border':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GREY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        'image_scrollbar_handle':      with_alpha(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n        # NOT CONSUMED -- the image scrollbar hovers from DARK's 'accent'.\n        # Left as written: #646464 is on no register row, so there is\n        # nothing to derive it from. See tests/test_derived_values.py.\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n        'image_dropdown_bg':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        'image_dropdown_selection':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        'image_dropdown_border':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n    }\n    \n    LIGHT:", 1)
    tree.sub('utils/dialog_styles.py',
             "        # Image mode semi-transparent overlay values (rgba — used only in image mode)\n        # Same values as DARK since image mode always uses dark-based overlays\n        'image_overlay_bg':            'rgba(0, 0, 0, 171)',\n        'image_overlay_bg_dark':       'rgba(26, 26, 26, 191)',\n        'image_overlay_checkbox':      'rgba(0, 0, 0, 100)',\n        'image_scrollbar_border':      'rgba(51, 51, 51, 100)',\n        'image_scrollbar_handle':      'rgba(80, 80, 80, 150)',\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n        'image_dropdown_bg':           'rgba(0, 0, 0, 131)',\n        'image_dropdown_selection':    'rgba(51, 51, 51, 200)',\n        'image_dropdown_border':       'rgba(51, 51, 51, 150)',\n",
             "        # Image mode semi-transparent overlay values -- used only in image\n        # mode. Same derivations as DARK since image mode always uses\n        # dark-based overlays; image mode reads DARK, so nothing reads these.\n        'image_overlay_bg':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        'image_overlay_bg_dark':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        'image_overlay_checkbox':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        'image_scrollbar_border':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GREY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        'image_scrollbar_handle':      with_alpha(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n        # NOT CONSUMED -- the image scrollbar hovers from DARK's 'accent'.\n        # Left as written: #646464 is on no register row, so there is\n        # nothing to derive it from. See tests/test_derived_values.py.\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n        'image_dropdown_bg':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        'image_dropdown_selection':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        'image_dropdown_border':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n", 1)
    tree.sub('ui/drag_drop_text_edit.py',
             'from utils.colors import BRAND_GOLD, TRUE_BLACK, with_alpha\n',
             'from utils.colors import (BRAND_GOLD, DRAG_HIGHLIGHT_ALPHA, TRUE_BLACK,\n                          with_alpha)\n', 1)
    tree.sub('ui/drag_drop_text_edit.py',
             '    _DRAG_HIGHLIGHT: str = with_alpha(BRAND_GOLD, 0xBF)\n',
             '    _DRAG_HIGHLIGHT: str = with_alpha(BRAND_GOLD, DRAG_HIGHLIGHT_ALPHA)\n', 1)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_dropdown_bg": "rgba(0, 0, 0, 131)",\n',
             '    "image_dropdown_bg": "#83000000",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_dropdown_border": "rgba(51, 51, 51, 150)",\n',
             '    "image_dropdown_border": "#96333333",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_dropdown_selection": "rgba(51, 51, 51, 200)",\n',
             '    "image_dropdown_selection": "#C8333333",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_overlay_bg": "rgba(0, 0, 0, 171)",\n',
             '    "image_overlay_bg": "#AB000000",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_overlay_bg_dark": "rgba(26, 26, 26, 191)",\n',
             '    "image_overlay_bg_dark": "#BF1a1a1a",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_overlay_checkbox": "rgba(0, 0, 0, 100)",\n',
             '    "image_overlay_checkbox": "#64000000",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_scrollbar_border": "rgba(51, 51, 51, 100)",\n',
             '    "image_scrollbar_border": "#64333333",\n', 2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_scrollbar_handle": "rgba(80, 80, 80, 150)",\n',
             '    "image_scrollbar_handle": "#96444444",\n', 2)
    tree.sub('tests/conftest.py',
             '# RNV-FIGURE-PIN, 2026-09-13 -- four figures describing the retired\n',
             '# RNV-DERIVE-ALPHA, 2026-09-25 -- every image-mode colour written at an\n# alpha is DERIVED, with_alpha(BASE, ALPHA), so a change to a base reaches\n# every alpha form of it. The image scrollbar handle left #505050 for\n# GREY_44 at 150, by ruling, closing RNV-COLLAPSE-505050 here.\n# tests/test_derived_values.py holds the derivations.\n# RNV-FIGURE-PIN, 2026-09-13 -- four figures describing the retired\n', 1)


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    colours_src = tree.read('utils/colors.py')
    styles_src = tree.read('utils/dialog_styles.py')

    # THE VALUES, EVALUATED. utils/colors.py imports nothing but typing, so the
    # edited module runs here; each palette entry is then evaluated in its
    # namespace, which is every name dialog_styles imports from it.
    ns = {}
    exec(compile(colours_src, 'utils/colors.py (edited)', 'exec'), ns)
    module = ast.parse(styles_src)
    cls = next(n for n in module.body
               if isinstance(n, ast.ClassDef) and n.name == 'DialogStyleManager')
    palettes, calls = {}, 0
    for node in cls.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, 'id', None) in ('DARK', 'LIGHT'):
                live = {}
                for k, v in zip(node.value.keys, node.value.values):
                    live[k.value] = eval(compile(ast.Expression(v), 'entry', 'eval'), ns)
                    if isinstance(v, ast.Call) and getattr(v.func, 'id', None) == 'with_alpha':
                        calls += 1
                    if (isinstance(v, ast.Constant) and isinstance(v.value, str)
                            and k.value != 'image_scrollbar_handle_hover'):
                        assert 'rgba(' not in v.value, f'{t.id}[{k.value!r}] = {v.value}'
                palettes[t.id] = live
    assert calls == 16, f'expected 16 derived entries, found {calls}'

    want = {
        'image_overlay_bg': '#AB000000',
        'image_overlay_bg_dark': '#BF1a1a1a',
        'image_overlay_checkbox': '#64000000',
        'image_scrollbar_border': '#64333333',
        'image_scrollbar_handle': '#96444444',      # the ruled change
        'image_scrollbar_handle_hover': 'rgba(100, 100, 100, 200)',  # unread, left
        'image_dropdown_bg': '#83000000',
        'image_dropdown_selection': '#C8333333',
        'image_dropdown_border': '#96333333',
    }
    for mode, live in palettes.items():
        for key, value in want.items():
            assert live[key] == value, f'{mode}[{key!r}] = {live[key]}, want {value}'
        # the locked suite's own colour check, applied to every value
        for key, value in live.items():
            assert re.match(r'^#[0-9a-fA-F]{3,8}$', value) or \
                re.match(r'^rgba\(\d+,\s*\d+,\s*\d+,\s*\d+\)$', value), (mode, key, value)

    # the drag highlight keeps its value, now through a named alpha
    drag = tree.read('ui/drag_drop_text_edit.py')
    assert 'with_alpha(BRAND_GOLD, DRAG_HIGHLIGHT_ALPHA)' in drag
    assert eval("with_alpha(BRAND_GOLD, DRAG_HIGHLIGHT_ALPHA)", ns) == '#BFd2bc93'

    # the snapshot records the new values and none of the old
    snap = tree.read('tests/__snapshots__/test_snapshots.ambr')
    assert snap.count('rgba(') == 2 and snap.count(
        '"image_scrollbar_handle_hover": "rgba(100, 100, 100, 200)"') == 2, (
        'the snapshot records an rgba() value other than the unread hover key')
    assert snap.count('"image_scrollbar_handle": "#96444444"') == 2
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
