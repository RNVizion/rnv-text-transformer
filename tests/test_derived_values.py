"""Derived values: a colour that is a named colour AT AN ALPHA.

Image mode draws its chrome translucent, and until 2026-09-25 every one of
those values was written out: 'rgba(26, 26, 26, 191)' beside BRAND_BLACK, with
nothing relating the two. A change to BRAND_BLACK would have reached every
opaque use of it and none of these. Each is now with_alpha(BASE, ALPHA) -- the
helper this application already had, and already used for the drag highlight
-- so the register row carries every alpha form of its colour.

WHAT MOVES A PIXEL: ONE THING, BY RULING. The image-mode scrollbar handle
leaves #505050 for GREY_44, closing RNV-COLLAPSE-505050 here; its alpha stays
at 150. Everything else keeps its colour and its alpha byte, respelled from
rgba() to #AARRGGBB -- the same pixels, in the one spelling QColor() can also
read. test_nothing_moved_that_was_not_ruled holds that to the byte.

AND ONE KEY THAT NOTHING READS, LEFT AS IT IS. image_scrollbar_handle_hover
holds rgba(100, 100, 100, 200), a grey on no register row, while the image
scrollbar's hover is painted from DARK's 'accent' -- BRAND_GOLD, ruled
2026-09-12. It is not derived, because there is no row for it to follow; and
it cannot simply take the painted gold, because LIGHT carries the same image
keys and a BRAND_GOLD there is a third gold in a mode the brand allows two.
A test pins that nothing reads it.
"""
from __future__ import annotations

import ast
import pathlib
import re

from utils import colors
from utils.colors import with_alpha
from utils.dialog_styles import DialogStyleManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLES = ROOT / "utils" / "dialog_styles.py"
DRAG = ROOT / "ui" / "drag_drop_text_edit.py"
PALETTES = {"DARK": DialogStyleManager.DARK, "LIGHT": DialogStyleManager.LIGHT}

#: constant -> the byte. Every one is the integer alpha the rgba() literal it
#: replaced already carried: nothing was fractional, so nothing was measured
#: and nothing rounds.
ALPHAS = {
    "IMAGE_FIELD_ALPHA": 0xAB,
    "IMAGE_LABEL_ALPHA": 0xBF,
    "IMAGE_CHECKBOX_ALPHA": 0x64,
    "SCROLLBAR_BORDER_ALPHA": 0x64,
    "SCROLLBAR_HANDLE_ALPHA": 0x96,
    "DROPDOWN_BG_ALPHA": 0x83,
    "DROPDOWN_SELECTION_ALPHA": 0xC8,
    "DROPDOWN_BORDER_ALPHA": 0x96,
    "DRAG_HIGHLIGHT_ALPHA": 0xBF,
}

#: What each image value is MADE OF: the constant its colour comes from, and its
#: alpha byte -- the byte its rgba() literal already carried, and the colour
#: that literal spelled, except the scrollbar handle's, which was ruled.
#: By NAME, not by hex: see test_nothing_moved_that_was_not_ruled.
MADE_OF = {
    "image_overlay_bg": ("TRUE_BLACK", 171),
    "image_overlay_bg_dark": ("BRAND_BLACK", 191),
    "image_overlay_checkbox": ("TRUE_BLACK", 100),
    "image_scrollbar_border": ("APP_BORDER", 100),
    "image_scrollbar_handle": ("GREY_44", 150),     # was #505050, ruled
    "image_dropdown_bg": ("TRUE_BLACK", 131),
    "image_dropdown_selection": ("APP_BORDER", 200),
    "image_dropdown_border": ("APP_BORDER", 150),
}
UNREAD = "image_scrollbar_handle_hover"

_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")
_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\b|\brgba\(\s*\d{1,3}\s*,\s*\d{1,3}"
                       r"\s*,\s*\d{1,3}\s*,\s*[0-9]*\.?[0-9]+\s*\)")
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_FUNC = re.compile(r"\brgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
                   r"\s*(?:,\s*[0-9]*\.?[0-9]+\s*)?\)")
SKIP_DIRS = {".git", "tests", "build", "dist", ".venv", "venv", "__pycache__"}


def decompose(value: str) -> tuple[str, int] | None:
    """(base '#rrggbb', alpha byte) -- taken apart, never rebuilt, so a fault
    in with_alpha() cannot also be a fault here."""
    m = _HEX8.match(value)
    if m:
        return "#" + m.group(2).lower(), int(m.group(1), 16)
    return None


def _parts_of(spelled: str) -> tuple[str, int]:
    """(base, alpha byte) for any composed spelling, with Qt's own reading of a
    fractional alpha: it TRUNCATES, so 0.3 is 76."""
    if spelled.startswith("#"):
        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)
    numbers = re.findall(r"[0-9]*\.?[0-9]+", spelled)
    r, g, b = (int(x) for x in numbers[:3])
    a = numbers[3]
    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a
                                         else int(a))


def colours_in(text: str) -> set[str]:
    """Every colour in a string, as #rrggbb. #AARRGGBB is alpha FIRST."""
    found = set()
    for m in _HEX.finditer(text):
        h = m.group(0)[1:].lower()
        h = h[2:] if len(h) == 8 else ("".join(c * 2 for c in h) if len(h) == 3 else h)
        found.add("#" + h)
    for m in _FUNC.finditer(text):
        channels = [int(g) for g in m.groups()]
        if all(c <= 255 for c in channels):
            found.add("#%02x%02x%02x" % tuple(channels))
    return found


def _sources():
    """Application source: not tests, not a root test suite, not a delivery
    script. Yields (relative path, parsed tree)."""
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        yield rel, ast.parse(text)


def _bare_strings(tree: ast.AST) -> set[int]:
    """Docstrings and every other string nobody evaluates -- mentions."""
    bare = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for st in body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                    bare.add(id(st.value))
    return bare


def _derived():
    """(where, call node, resolved value) for every with_alpha() call in the
    palettes and in the drag highlight."""
    out = []
    tree = ast.parse(STYLES.read_text(encoding="utf-8-sig"))
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "DialogStyleManager")
    for node in cls.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        name = getattr(target, "id", None)
        if name in PALETTES and isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(v, ast.Call) and getattr(v.func, "id", None) == "with_alpha":
                    out.append((f"{name}[{k.value!r}]", v, PALETTES[name][k.value]))
    drag = ast.parse(DRAG.read_text(encoding="utf-8-sig"))
    for node in ast.walk(drag):
        if (isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None)
                == "_DRAG_HIGHLIGHT" and isinstance(node.value, ast.Call)):
            from ui.drag_drop_text_edit import DragDropTextEdit
            out.append(("DragDropTextEdit._DRAG_HIGHLIGHT", node.value,
                        DragDropTextEdit._DRAG_HIGHLIGHT))
    return out


# ------------------------------------------------------------ guard the guard

def test_with_alpha_composes_alpha_first():
    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and
    the wrong one, which is the failure that does not look like a failure."""
    assert with_alpha("#1a1a1a", 0xBF) == "#BF1a1a1a"
    assert decompose(with_alpha("#d2bc93", 0x33)) == ("#d2bc93", 0x33)
    assert decompose(with_alpha("444444", 0x96)) == ("#444444", 0x96)


def test_the_alphas_are_the_declared_bytes():
    for name, byte in ALPHAS.items():
        assert hasattr(colors, name), f"utils.colors has no {name}"
        value = getattr(colors, name)
        assert type(value) is int, f"{name} is {value!r}, not an int byte"
        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"


def test_the_derivation_sweep_is_looking():
    """Every check below iterates _derived(). If it came back empty they
    would all pass over nothing."""
    where = {w for w, _c, _v in _derived()}
    want = {f"{p}[{k!r}]" for p in PALETTES for k in MADE_OF}
    want.add("DragDropTextEdit._DRAG_HIGHLIGHT")
    assert want <= where, sorted(want - where)


# ----------------------------------------------------------- the derivations

def test_every_derived_value_names_constants_that_exist():
    """with_alpha(BASE, ALPHA) where both are names: a literal in either
    position is the thing this round removed."""
    bad = []
    for where, call, _value in _derived():
        if len(call.args) != 2 or call.keywords:
            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA)")
            continue
        base, alpha = call.args
        for pos, arg in (("base", base), ("alpha", alpha)):
            if not isinstance(arg, ast.Name):
                bad.append(f"{where}: the {pos} is {ast.unparse(arg)}, not a name")
            elif not hasattr(colors, arg.id):
                bad.append(f"{where}: the {pos} names {arg.id}, which "
                           f"utils.colors does not define")
        if isinstance(base, ast.Name) and hasattr(colors, base.id):
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(colors, base.id))):
                bad.append(f"{where}: the base {base.id} is not a six-digit colour")
        if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:
            bad.append(f"{where}: the alpha {alpha.id} is not a declared "
                       f"composite alpha")
    assert not bad, "derived values that do not derive:\n  " + "\n  ".join(bad)


def test_every_derived_value_decomposes_to_its_base_and_its_alpha():
    """TAKEN APART, not rebuilt -- the entry IS with_alpha()'s output, so
    recomputing it would compare the call with itself."""
    wrong = []
    for where, call, value in _derived():
        base, alpha = call.args
        parts = decompose(value)
        want = (getattr(colors, base.id).lower(), getattr(colors, alpha.id))
        if parts != want:
            wrong.append(f"{where} is {value!r}, which takes apart to {parts}, "
                         f"not {base.id}/{alpha.id} {want}")
    assert not wrong, "derived values that do not match:\n  " + "\n  ".join(wrong)


def test_no_composed_literal_is_left_in_the_application():
    """The completeness half. Every EVALUATED string in the application's own
    source that spells a named colour at an alpha. Docstrings are mentions --
    utils/colors.py shows '#BFd2bc93' as an example, and that is prose.
    Alpha 0 is not a colour; a base no constant names has no row to follow."""
    named = {v.lower() for n, v in vars(colors).items()
             if n.isupper() and isinstance(v, str)
             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}
    strays, files = [], 0
    for rel, tree in _sources():
        files += 1
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in bare:
                continue
            for spelled in _COMPOSED.findall(node.value):
                base, alpha = _parts_of(spelled)
                if alpha and base in named:
                    strays.append(f"{rel}:{node.lineno}  {spelled}")
    assert files >= 40, f"only {files} files swept -- the walk has gone blind"
    assert not strays, ("composed values still written out rather than "
                        "derived:\n  " + "\n  ".join(strays))


# --------------------------------------------------- what moved, and what not

def test_the_scrollbar_handle_is_grey_44_at_150():
    """RNV-COLLAPSE-505050, closed here 2026-09-25. Ruled 2026-09-02, and
    written out as rgba(80, 80, 80, 150) in both palettes until now."""
    for mode, palette in PALETTES.items():
        assert decompose(palette["image_scrollbar_handle"]) == (
            colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA), mode
    assert colors.SCROLLBAR_HANDLE_ALPHA == 150


def test_nothing_moved_that_was_not_ruled():
    """Each image value, held to what it is MADE OF: the constant its colour
    comes from and its alpha byte.

    BY NAME, NOT BY HEX, and that is the point of the round. A register move
    is meant to pass straight through these values; a test that pinned
    '#333333' would fail the first time one did and ask a person to edit it
    by hand -- the job derivation exists to remove. What this DOES catch is a
    value quietly re-made from something else, which the decomposition check
    accepts as long as source and value agree with each other.

    The byte-for-byte before-and-after was checked once, by the delivery
    script, against the edited module before it was written."""
    for mode, palette in PALETTES.items():
        for key, (base, alpha) in MADE_OF.items():
            assert decompose(palette[key]) == (getattr(colors, base).lower(), alpha), (
                f"{mode}[{key!r}] is {palette[key]}, which is not {base} at "
                f"{alpha}")
    from ui.drag_drop_text_edit import DragDropTextEdit
    assert decompose(DragDropTextEdit._DRAG_HIGHLIGHT) == (colors.BRAND_GOLD, 0xBF)


def test_the_unread_hover_key_stays_unread():
    """image_scrollbar_handle_hover is read by nothing: the image scrollbar
    hovers from DARK's 'accent', BRAND_GOLD, ruled 2026-09-12. It still holds
    rgba(100, 100, 100, 200) -- a grey on no register row, left because there
    is nothing to derive it from and the gold would be a third gold in LIGHT.

    If anything starts reading it, this fails: the value would then be a grey
    hover on screen, against the gold ruling, and it has to be decided rather
    than inherited."""
    assert DialogStyleManager.DARK["accent"] == colors.BRAND_GOLD
    readers, keys = [], 0
    for rel, tree in _sources():
        # the dict KEYS that declare it are not reads; anything else is,
        # including a lookup inside dialog_styles.py itself
        declared = {id(k) for node in ast.walk(tree) if isinstance(node, ast.Dict)
                    for k in node.keys if k is not None}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == UNREAD:
                if id(node) in declared:
                    keys += 1
                else:
                    readers.append(f"{rel}:{node.lineno}")
    assert keys == 2, f"expected the key declared in DARK and LIGHT, found {keys}"
    assert not readers, f"{UNREAD} is read now: {readers}"


def test_the_collapsed_value_is_gone_in_every_spelling():
    """#505050 in any string spelling -- #rgb, #rrggbb, #aarrggbb, rgb(),
    rgba() -- or as integers in a tuple or a QColor call. The sweeps that
    reported it gone elsewhere compared quoted six-digit hex and nothing
    else; that is how it survived three weeks after its ruling."""
    found = []
    for rel, tree in _sources():
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in bare and "#505050" in colours_in(node.value)):
                found.append(f"{rel}:{node.lineno}  {node.value[:40]!r}")
            values = None
            if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):
                values = node.elts
            elif isinstance(node, ast.Call) and len(node.args) >= 3 and (
                    getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):
                values = node.args
            if values:
                ints = tuple(v.value for v in values[:3]
                             if isinstance(v, ast.Constant) and type(v.value) is int)
                if ints == (80, 80, 80):
                    found.append(f"{rel}:{node.lineno}  (80, 80, 80)")
    assert not found, "#505050 is still here:\n  " + "\n  ".join(found)
    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"

# RNV-DERIVE-ALPHA
