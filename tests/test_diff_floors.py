"""RNV-DIFF-FLOORS -- a highlight nobody can see is not a highlight.

Installed 2026-09-13, after two of the six diff values were found to fail in
ways no contrast check would ever have reported.

WHAT WENT WRONG, TWICE, AND WHY THIS FILE MEASURES THE WAY IT DOES

  1. SEMANTIC_DIFF_REMOVED was '#4d1a1a'. Under achromatopsia it collapses to
     #292929, on a panel that collapses to #191919 -- CIEDE2000 **5.03**,
     under the 8.40 bar. A deleted line carried a band too faint to read as a
     highlight. Its light partner '#f8d7da' failed the same way at **4.27**.
     Contrast against the TEXT was 10.4591 and had been checked; the fill had
     never been measured against the GROUND under a simulation, because the
     pairs were and it read as though everything had been.

     THOSE FOUR FIGURES WERE WRONG HERE FOR A DAY. This paragraph gave 0.31,
     #181818, 15.87 and 12.97 -- all of them '#2e0f10', a candidate derived
     in the same round and rejected. Nothing checked them, so they read as
     measured. RETIRED_FILLS below now pins every figure this file prints
     about a retired value, and test_the_instrument_can_fail asserts them.

  2. The first re-derivation measured pair separation in dE76 and read it
     against 8.40, which this fleet's register publishes in CIEDE2000. On the
     binding pair the two metrics read 10.43 and 8.08. The looser number was
     over the bar and the real one was under it.

So this guard measures three floors, each under five kinds of vision, and it
validates its own instrument before it trusts a single figure.

  text     WCAG 2.1, fill against the ink actually drawn on it      >= 4.5
  ground   CIEDE2000, fill against the pane it sits on              >= 8.40
  pair     CIEDE2000, between two roles that can share a widget     >= 8.40

RNV-REGEX-FLOOR (2026-09-13) widened the first two rules past the diff three.
SEMANTIC_REGEX_MATCH_LIGHT '#ffff99' had the same defect as the diff red and
was one line below it in the same file, and the round that fixed the three
walked past it: 23.83 from the test pane in normal vision, 0.41 under
achromatopsia. A rule that names the values it covers will always be one
value behind the file, so the ground and ink rules now sweep every fill this
application paints behind text -- the diff three, plus whatever the Regex
Builder is found to draw.

THE GROUND IS READ FROM THE PALETTE THE WIDGET USES, NOT THE ONE THAT SOUNDS
RIGHT. LIGHT['input_bg'] is #ffffff and LIGHT['bg'] is #f5f5f5; the compare
panes take the latter, which a rendered frame shows and the palette does not.
Derived against white, SEMANTIC_DIFF_CHANGED_LIGHT cleared the real ground by
3% -- inside the bar, and the wrong bar.

WHICH PAIRS ARE OWED IS DERIVED, NOT LISTED. A hard-coded pair list is a
statement about ui/compare_dialog.py that stops being true the moment someone
re-wires which pane paints what, and stays green while it stops being true.
So this file reads that function's own `match` statement and follows every
chain to its end:

    role  <-  palette key  <-  ClassVar  <-  local name  <-  the widget

Two roles that reach the same widget owe each other the pair floor. Today
that makes DELETE+REPLACE on the left pane and INSERT+REPLACE on the right,
so added and removed owe each other nothing in the dialog -- they cannot be
on screen together.

core/diff_engine.py is the exception, and it is why LIGHT owes all three. It
builds one HTML document from DialogStyleManager.LIGHT in BOTH themes, and
puts .diff-delete and .diff-insert in the two columns of a single row.

8.40 IS THE REGISTER'S OWN BAR, not a number chosen here: BRAND_GOLD to
#b49e75 is its published walk into "perceptible at a glance" at 8.4035, and
test_the_instrument_is_ciede2000 reproduces exactly that figure before any
other test in this file is allowed to mean anything.
"""
from __future__ import annotations

import ast
import math
from pathlib import Path

from utils.dialog_styles import DialogStyleManager

ROOT = Path(__file__).resolve().parent.parent
DIALOG = ROOT / "ui" / "compare_dialog.py"
EXPORT = ROOT / "core" / "diff_engine.py"
REGEX = ROOT / "ui" / "regex_builder_dialog.py"

TEXT_FLOOR = 4.5
DE_FLOOR = 8.40

#: The pane's ground and the ink drawn on it, per mode, by palette KEY --
#: so a palette that re-points the key is followed rather than second-guessed.
GROUND_KEY, INK_KEY = "bg", "text"

#: rnv-color-picker's ColorAccessibility.COLORBLIND_MATRICES, verbatim, so
#: that a colour graded acceptable here is graded acceptable by the tool in
#: the next repository along. Achromatopsia is its 601 luma with int()
#: truncation, which is the same code path.
MATRICES = {
    "protanopia":   ((0.567, 0.433, 0.000), (0.558, 0.442, 0.000),
                     (0.000, 0.242, 0.758)),
    "deuteranopia": ((0.625, 0.375, 0.000), (0.700, 0.300, 0.000),
                     (0.000, 0.300, 0.700)),
    "tritanopia":   ((0.950, 0.050, 0.000), (0.000, 0.433, 0.567),
                     (0.000, 0.475, 0.525)),
}
VISION = ("normal", "protanopia", "deuteranopia", "tritanopia", "achromatopsia")


# ----------------------------------------------------------------- the instrument
def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def contrast(a: str, b: str) -> float:
    """WCAG 2.1, truncated to four places the way the register publishes."""
    def lum(c):
        def f(v):
            v /= 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, bl = c
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(bl)
    la, lb = lum(_rgb(a)), lum(_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return math.floor((hi + 0.05) / (lo + 0.05) * 10000) / 10000


def simulate(hex_: str, kind: str) -> str:
    if kind == "normal":
        return hex_.lower()
    r, g, b = _rgb(hex_)
    if kind == "achromatopsia":
        y = int(0.299 * r + 0.587 * g + 0.114 * b)
        return _hex((y, y, y))
    m = MATRICES[kind]
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    return _hex(tuple(int(max(0.0, min(1.0, row[0] * rf + row[1] * gf
                                       + row[2] * bf)) * 255) for row in m))


def _lab(hex_: str) -> tuple[float, float, float]:
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in _rgb(hex_))
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = (0.2126729 * r + 0.7151522 * g + 0.0721750 * b)
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def g_(t):
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
    fx, fy, fz = g_(x), g_(y), g_(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def ciede2000(one: str, two: str) -> float:
    """CIEDE2000. NOT dE76 -- the difference is what this round is about."""
    l1, a1, b1 = _lab(one)
    l2, a2, b2 = _lab(two)
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    cb = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(cb ** 7 / (cb ** 7 + 25 ** 7))) if cb else 0.5
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dlp, dcp = l2 - l1, c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    else:
        d = h2p - h1p
        dhp = d - 360 if d > 180 else (d + 360 if d < -180 else d)
    dhp2 = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp) / 2)
    lbp, cbp = (l1 + l2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hbp = h1p + h2p
    else:
        s = h1p + h2p
        hbp = ((s + 360) / 2 if s < 360 else (s - 360) / 2) \
            if abs(h1p - h2p) > 180 else s / 2
    t = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    rc = 2 * math.sqrt(cbp ** 7 / (cbp ** 7 + 25 ** 7)) if cbp else 0.0
    sl = 1 + (0.015 * (lbp - 50) ** 2) / math.sqrt(20 + (lbp - 50) ** 2)
    sc, sh = 1 + 0.045 * cbp, 1 + 0.015 * cbp * t
    rt = -math.sin(math.radians(2 * dth)) * rc
    return math.sqrt((dlp / sl) ** 2 + (dcp / sc) ** 2 + (dhp2 / sh) ** 2
                     + rt * (dcp / sc) * (dhp2 / sh))


def worst(one: str, two: str) -> tuple[float, str]:
    """The closest these two ever get, and the eye that gets them there."""
    return min(((ciede2000(simulate(one, v), simulate(two, v)), v)
                for v in VISION), key=lambda p: p[0])


# ------------------------------------------------------- what shares a widget
def _dialog_tree() -> ast.Module:
    return _tree(DIALOG)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), str(path))


def _classvar_keys(path: Path = None) -> dict[str, tuple[str, str]]:
    """_ADDED_COLOR_DARK -> ('DARK', 'diff_added_bg'), read off the class.

    Takes a path because the Regex Builder declares its own fill the same way
    and this guard now measures that one too.
    """
    out = {}
    for node in ast.walk(_tree(path or DIALOG)):
        if not isinstance(node, ast.AnnAssign) or not node.value:
            continue
        if not isinstance(node.target, ast.Name):
            continue
        v = node.value
        if (isinstance(v, ast.Subscript)
                and isinstance(v.value, ast.Attribute)
                and getattr(v.value.value, "id", "") == "DialogStyleManager"
                and isinstance(v.slice, ast.Constant)):
            out[node.target.id] = (v.value.attr, v.slice.value)
    return out


def _highlight_fn() -> ast.FunctionDef:
    for node in ast.walk(_dialog_tree()):
        if (isinstance(node, ast.FunctionDef)
                and node.name == "_highlight_differences"):
            return node
    raise AssertionError(
        "ui/compare_dialog.py has no _highlight_differences. This guard "
        "derives which roles can share a widget from that function; if it "
        "was renamed, point this at the new one rather than hard-coding a "
        "pair list, which is what it exists to avoid.")


def _locals_to_classvars(fn: ast.FunctionDef) -> dict[str, dict[str, str]]:
    """{'DARK': {'added_color': '_ADDED_COLOR_DARK', ...}, 'LIGHT': {...}}

    The function picks its three QColors inside `if is_dark: ... else: ...`,
    so the branch says which palette the names belong to.
    """
    def harvest(stmts):
        found = {}
        for stmt in stmts:
            for node in ast.walk(stmt):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                target = node.targets[0]
                call = node.value
                if not isinstance(target, ast.Name):
                    continue
                if (isinstance(call, ast.Call)
                        and getattr(call.func, "id", "") == "QColor"
                        and call.args
                        and isinstance(call.args[0], ast.Attribute)):
                    found[target.id] = call.args[0].attr
        return found

    for node in fn.body:
        if isinstance(node, ast.If):
            dark, light = harvest(node.body), harvest(node.orelse)
            if dark and light:
                return {"DARK": dark, "LIGHT": light}
    raise AssertionError(
        "could not find the dark/light branch in _highlight_differences")


def _widget_colours(fn: ast.FunctionDef) -> dict[str, set[str]]:
    """{'input_edit': {'removed_color', 'changed_color'}, ...}

    Every _highlight_range call, keyed by the widget it paints. Two colours
    under one key can be on screen at the same moment.
    """
    out: dict[str, set[str]] = {}
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Call)
                and getattr(node.func, "attr", "") == "_highlight_range"):
            continue
        args = node.args
        if len(args) < 4:
            continue
        widget, colour = args[0], args[-1]
        if isinstance(widget, ast.Attribute) and isinstance(colour, ast.Name):
            out.setdefault(widget.attr, set()).add(colour.id)
    return out


def covisible_keys(mode: str) -> set[frozenset]:
    """Palette-key pairs that can be on screen together, in this mode."""
    fn = _highlight_fn()
    names = _locals_to_classvars(fn)[mode]
    keys = _classvar_keys()
    pairs = set()
    for colours in _widget_colours(fn).values():
        resolved = {keys[names[c]][1] for c in colours
                    if c in names and names[c] in keys}
        for one in resolved:
            for two in resolved:
                if one != two:
                    pairs.add(frozenset((one, two)))
    return pairs


def export_keys() -> set[frozenset]:
    """The HTML export puts delete and insert in one row, always light."""
    src = EXPORT.read_text(encoding="utf-8")
    if ".diff-insert" not in src or ".diff-delete" not in src:
        return set()
    if "DialogStyleManager.LIGHT" not in src:
        return set()
    return {frozenset(("diff_html_insert_bg", "diff_html_delete_bg"))}


def palette(mode: str) -> dict:
    return DialogStyleManager.DARK if mode == "DARK" else DialogStyleManager.LIGHT


DIFF_KEYS = ("diff_added_bg", "diff_removed_bg", "diff_changed_bg")


def regex_keys() -> tuple[str, ...]:
    """The palette keys ui/regex_builder_dialog.py paints into its test pane.

    Derived rather than listed, for the same reason the diff pairs are: this
    dialog used to declare a second family of eight capture-group fills, and
    they were retired only after a render proved nothing drew them. If a
    second fill is ever wired back in, the blindness test below says so
    rather than this guard quietly measuring one of two.

    ANY reference counts, not only one inside a setBackground call. The
    first version looked in setBackground first and fell back to the whole
    file only when that found nothing -- two branches, mutually exclusive, so
    a dialog painting one fill through a local and another directly reported
    just the direct one. A tamper that wired a second fill in stayed green on
    that version. Under-reporting is the one direction a blindness check must
    not fail in, so this counts every reference and accepts that a declared
    colour nobody draws with would be measured too; a fill that clears the
    floors and is never painted costs nothing.

    The retired names are not spelled here. tests/test_semantic_naming.py
    owns that rule and sweeps raw text, so a guard that names what it is glad
    to be rid of lands red in it -- which this docstring did, one round after
    the paragraph in this same file explaining that exact trap.
    """
    keys = _classvar_keys(REGEX)
    used = {keys[n.attr][1] for n in ast.walk(_tree(REGEX))
            if isinstance(n, ast.Attribute) and n.attr in keys}
    return tuple(sorted(used))


def highlight_keys() -> tuple[str, ...]:
    """Every semantic fill this application draws behind text.

    The diff three plus whatever the Regex Builder paints. They share the
    ground and the ink floors and nothing else -- a match has no co-visible
    partner, because after RNV-DIFF-FLOORS its pane holds exactly one fill.
    """
    return DIFF_KEYS + regex_keys()


# ------------------------------------------------------------------- the tests
def test_the_instrument_is_ciede2000():
    """Before any figure here means anything, the metric has to be the one
    the bar is published in.

    BRAND_GOLD #d2bc93 walked -30 to #b49e75 is the register's own step into
    "perceptible at a glance", published at 8.4035. dE76 for the same pair is
    11.0877 -- which is exactly the substitution that let a pair reading 8.08
    be reported as 10.43 and shipped.
    """
    got = ciede2000("#d2bc93", "#b49e75")
    assert abs(got - 8.4035) < 0.0005, (
        f"CIEDE2000(#d2bc93, #b49e75) = {got:.4f}, and the register publishes "
        f"8.4035. Either the arithmetic changed or this is no longer "
        f"CIEDE2000 -- dE76 for this pair is 11.0877.")

    l1, l2 = _lab("#d2bc93"), _lab("#b49e75")
    de76 = math.sqrt(sum((x - y) ** 2 for x, y in zip(l1, l2)))
    assert abs(de76 - got) > 2.0, (
        "CIEDE2000 and dE76 are returning the same number for a pair where "
        "they differ by 2.68. One of them is not what it claims to be.")


#: The fills RNV-DIFF-FLOORS retired, and every figure this file prints about
#: them: mode, what it collapses to under achromatopsia, its worst distance
#: from its own pane, its distance in normal vision, and its contrast against
#: the ink. RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN.
#:
#: PINNED RATHER THAN NARRATED, and the reason is this table's own history.
#: The first version of this guard described '#4d1a1a' with four figures that
#: all belonged to a different hex -- a candidate derived during the same
#: round and rejected. Prose cannot be wrong loudly. An assertion can.
RETIRED_FILLS = {
    "#4d1a1a": ("DARK", "#292929", 5.03, 20.85, 10.4591),
    "#f8d7da": ("LIGHT", "#e1e1e1", 4.27, 13.69, 15.7238),
}


def test_the_instrument_can_fail():
    """A floor nothing can breach is decoration.

    Every figure in RETIRED_FILLS is checked here against the instrument this
    file ships, so a number quoted in a docstring is a number a test agrees
    with. If the ground rule cannot still see why these two were retired, it
    cannot see anything.
    """
    for fill, (mode, collapse, want_worst, want_normal, want_text) in \
            RETIRED_FILLS.items():
        pal = palette(mode)
        ground, ink = pal[GROUND_KEY], pal[INK_KEY]

        assert simulate(fill, "achromatopsia") == collapse, (
            f"{fill} collapses to {simulate(fill, 'achromatopsia')} under "
            f"achromatopsia, not {collapse} as this file says. A figure "
            f"describing one value with another value's measurement is the "
            f"defect this table exists to stop.")

        distance, eye = worst(fill, ground)
        assert eye == "achromatopsia", (
            f"{fill} is closest to its pane under {eye}, not achromatopsia. "
            f"The simulation set has changed shape.")
        assert abs(distance - want_worst) < 0.005, (
            f"{fill} reads {distance:.2f} from {ground} at its worst, and "
            f"this file says {want_worst}. One of them is stale.")
        assert distance < DE_FLOOR, (
            f"{fill} reads {distance:.2f} from {ground}, over the floor -- "
            f"so the ground rule is not measuring what it was written to "
            f"measure.")

        assert abs(ciede2000(fill, ground) - want_normal) < 0.005, (
            f"{fill} reads {ciede2000(fill, ground):.2f} from {ground} in "
            f"normal vision, and this file says {want_normal}.")
        assert abs(contrast(fill, ink) - want_text) < 0.00005, (
            f"{fill} reads {contrast(fill, ink):.4f} against {ink}, and this "
            f"file says {want_text}. That figure is the one the original "
            f"round cited to show the fill had been checked; it was the "
            f"wrong value's.")

    assert len(RETIRED_FILLS) == 2, (
        "RETIRED_FILLS should hold both halves of the pair that failed. One "
        "entry means a mode is being described and not measured -- the "
        "original round cited only the dark half and never noticed the light "
        "one failed too.")


def test_every_fill_clears_the_ink_drawn_on_it():
    """WCAG 4.5 against the ink, per mode."""
    bad = []
    for mode in ("DARK", "LIGHT"):
        pal = palette(mode)
        ink = pal[INK_KEY]
        for key in highlight_keys():
            ratio = contrast(pal[key], ink)
            if ratio < TEXT_FLOOR:
                bad.append(f"{mode}[{key}] {pal[key]} on ink {ink}: "
                           f"{ratio:.4f} < {TEXT_FLOOR}")
    assert not bad, "text does not clear its fill:\n  " + "\n  ".join(bad)


def test_every_fill_is_visible_against_its_own_pane():
    """The rule the old dark red failed at 5.03, and its light partner at 4.27.

    Measured under all five, because the failure is invisible under four of
    them: '#4d1a1a' reads 20.85 from the panel in normal vision and 5.03 at
    its worst. The figures are pinned in RETIRED_FILLS above.
    """
    bad = []
    for mode in ("DARK", "LIGHT"):
        pal = palette(mode)
        ground = pal[GROUND_KEY]
        for key in highlight_keys():
            distance, eye = worst(pal[key], ground)
            if distance < DE_FLOOR:
                bad.append(f"{mode}[{key}] {pal[key]} against {ground}: "
                           f"{distance:.2f} < {DE_FLOOR} under {eye}")
    assert not bad, (
        "these highlights disappear into the pane behind them:\n  "
        + "\n  ".join(bad)
        + "\n\nA fill that matches its ground is not a highlight, whatever "
          "its contrast against the text reads.")


def test_roles_that_share_a_widget_stay_apart():
    """The pair floor, on the pairs ui/compare_dialog.py actually creates."""
    bad = []
    for mode in ("DARK", "LIGHT"):
        pal = palette(mode)
        pairs = covisible_keys(mode)
        if mode == "LIGHT":
            pairs = pairs | export_keys()
        for pair in sorted(pairs, key=sorted):
            one, two = sorted(pair)
            distance, eye = worst(pal[one], pal[two])
            if distance < DE_FLOOR:
                bad.append(f"{mode} {one} {pal[one]} vs {two} {pal[two]}: "
                           f"{distance:.2f} < {DE_FLOOR} under {eye}")
    assert not bad, (
        "these two can be on screen together and are not far enough "
        "apart:\n  " + "\n  ".join(bad))


def test_the_pairs_were_derived_and_not_assumed():
    """A sweep that finds nothing passes every rule above.

    This is the check the image-budget round shipped without: a glob that
    matched no file in three of five repositories, and a green suite.
    """
    fn = _highlight_fn()
    widgets = _widget_colours(fn)
    assert len(widgets) >= 2, (
        f"_highlight_differences paints {len(widgets)} widget(s). It paints "
        f"two panes, so the walk is not reading the calls.")

    names = _locals_to_classvars(fn)
    for mode in ("DARK", "LIGHT"):
        assert len(names[mode]) == 3, (
            f"{mode} resolves {len(names[mode])} colours, not three. The "
            f"branch this reads has changed shape.")

    keys = _classvar_keys()
    assert all(v in keys for m in names.values() for v in m.values()), (
        "a local colour name resolves to a ClassVar this guard cannot find "
        "in the class body")

    for mode in ("DARK", "LIGHT"):
        pairs = covisible_keys(mode)
        assert pairs, f"{mode} yielded no co-visible pair at all"
        resolved = {k for pair in pairs for k in pair}
        assert resolved <= set(DIFF_KEYS), (
            f"{mode} co-visibility reached keys this guard does not measure: "
            f"{sorted(resolved - set(DIFF_KEYS))}")

    # The one asymmetry worth stating out loud, because it is the reason the
    # dark triple fits at all: DELETE paints one pane and INSERT the other.
    dark = covisible_keys("DARK")
    assert frozenset(("diff_added_bg", "diff_removed_bg")) not in dark, (
        "added and removed now share a widget. That is allowed, but the dark "
        "triple was derived on the basis that they do not -- with a "
        "#dddddd ink ceiling at grey 97 and an achromatopsia floor at grey "
        "52, a three-level ladder needs 50 steps and there are 45. Re-derive "
        "the dark three before landing this.")

    matches = regex_keys()
    assert len(matches) == 1, (
        f"ui/regex_builder_dialog.py paints {len(matches)} fill(s) into its "
        f"test pane: {matches}. This guard measures every one it finds "
        f"against the ground and the ink, but it has no pair rule for them -- "
        f"one fill in a pane owes nobody a separation. Two do. If a second "
        f"family is back, give them a pair rule before landing it.")
    assert matches[0] in palette("DARK") and matches[0] in palette("LIGHT"), (
        f"{matches[0]} is not in both palettes, so one mode is unmeasured")

    assert export_keys(), (
        "core/diff_engine.py no longer pairs .diff-insert with .diff-delete "
        "out of DialogStyleManager.LIGHT. If the export moved, the third "
        "light pair may no longer be owed -- check before relaxing it.")


# THE TEN RETIRED VALUES ARE NOT GUARDED HERE, DELIBERATELY.
#
# A draft of this file ended with a rule that spelled the four retired
# identifiers out in order to forbid them. It landed RED -- in
# tests/test_semantic_naming.py, whose own sweep for retired names found all
# four here and could not tell forbidding a name from using one. That guard
# already carries a marker convention for files that mention what they
# retire, and a fourth marker was available.
#
# This comment does not spell them either, for the same reason: prose is
# swept as readily as code, and the draft's first correction removed the rule
# and left the paragraph that explained it, which landed red all over again.
#
# Taking it would have been the wrong fix. tests/test_semantic_naming.py owns
# the retired-name rule for this repository, the eight names this round
# retires are now in its RETIRED tuple, and a second guard asserting the same
# thing is how a suite grows two checks that will one day disagree. The
# duplication was the defect; the marker would only have hidden it.
#
# So this file guards the floors, and that one guards the names.
