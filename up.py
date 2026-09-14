#!/usr/bin/env python3
"""
RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP

Correct four figures that described one colour using another colour's
measurements, and pin every such figure in an assertion so it cannot go wrong
quietly again.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

RNV-DIFF-FLOORS retired SEMANTIC_DIFF_REMOVED '#4d1a1a' and explained why with
four numbers:

    collapses to #181818, on a panel that collapses to #191919 -- CIEDE2000 0.31
    reads 15.87 from the panel in normal vision
    contrast against the TEXT was 12.97

**Every one of them belongs to '#2e0f10'** -- a candidate derived during that
same round and rejected when a metric error was found in it. The substitution
was of the whole measurement, not of one digit. Nothing checked it, so it read
as measured and travelled into utils/colors.py, three places in
tests/test_diff_floors.py, two delivery scripts and two project notes.

The true readings for '#4d1a1a':

    collapses to #292929 on #191919            CIEDE2000  5.03   (floor 8.40)
    normal vision                                        20.85
    contrast against #dddddd                            10.4591

THE DEFECT WAS REAL AND WAS OVERSTATED. 5.03 is under the bar, so retiring the
value was right and every replacement stands. But 5.03 is a band too faint to
read as a highlight; 0.31 is an absent one. The round claimed the stronger
thing on the strength of a figure it did not own.

AND IT MISSED THE SECOND INSTANCE. '#f8d7da', the light half of the same role,
fails the same rule at **4.27** and was never mentioned. So the round cited
the wrong evidence for its case and walked past the right evidence beside it.

WHAT CHANGES

Nothing that renders. No value moves, no rule changes, no palette key is added
or removed. This is one comment block, two docstrings, and one test body.

THE TEST BODY IS THE POINT. tests/test_diff_floors.py gains RETIRED_FILLS --
every figure the file prints about a retired value: the collapse hex, the
worst distance from its own pane, the normal-vision distance, and the contrast
against the ink. test_the_instrument_can_fail asserts all of them against the
instrument the file ships, so a figure in a docstring is now a figure a test
agrees with.

It also asserts the table holds TWO entries, because the original round
described one mode and never measured the other.

FALSIFIED SIX WAYS, and the first tamper is the original mistake re-made:
0.31 put back for '#4d1a1a'. Also the wrong collapse hex, the wrong text
contrast, the wrong normal-vision reading, dropping the light half the way the
original round dropped it, and describing a retired value as clearing the
floor it was retired for. All six land red in test_the_instrument_can_fail.
"""
from __future__ import annotations

import argparse
import ast
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-text-transformer"
SENTINEL_FILE = "tests/conftest.py"
SENTINEL = "RNV-FIGURE-PIN"
GUARD = "tests/test_diff_floors.py"
DESCRIPTION = "correct four misattributed figures and pin them in an assertion"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p",
            "no:cacheprovider"]),
          ("\"the LOCKED file\"",
           [sys.executable, "-m", "pytest", "test_rnv_text_transformer.py",
            "-q", "-p", "no:cacheprovider", "--timeout=120"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

MISSING_HELP = (
    "run this from the root of a rnv-text-transformer checkout "
    "(no tests/conftest.py here).\n\n"
    "This round corrects figures installed by RNV-DIFF-FLOORS and widened by "
    "RNV-REGEX-FLOOR; both must have landed first.")

#: The figures this round writes, and what they describe:
#:   fill -> (mode, achromatopsia collapse, worst dE, normal dE, text contrast)
#: checks() re-derives every one against the tree it is about to write. A
#: round whose entire subject is a number nobody checked has no business
#: taking its own numbers on trust.
WANT_FILLS = {
    "#4d1a1a": ("DARK", "#292929", 5.03, 20.85, 10.4591),
    "#f8d7da": ("LIGHT", "#e1e1e1", 4.27, 13.69, 15.7238),
}


EDITS = [('tests/conftest.py', "# RNV-REGEX-FLOOR, 2026-09-13 -- SEMANTIC_REGEX_MATCH_LIGHT was '#ffff99',\n# which collapsed onto the #f5f5f5 test pane under achromatopsia at CIEDE2000\n", "# RNV-FIGURE-PIN, 2026-09-13 -- four figures describing the retired\n# SEMANTIC_DIFF_REMOVED '#4d1a1a' belonged to a different hex: a candidate\n# derived during RNV-DIFF-FLOORS and rejected. 0.31, #181818, 15.87 and a\n# text contrast of 12.97 are all '#2e0f10'. The true readings are 5.03,\n# #292929, 20.85 and 10.4591, and the defect was real but overstated -- a\n# faint band, not an absent one. Its light partner '#f8d7da' failed the same\n# rule at 4.27 and went unmentioned. tests/test_diff_floors.py now pins every\n# figure it prints about a retired value in RETIRED_FILLS and asserts them,\n# because prose cannot be wrong loudly and an assertion can.\n# RNV-REGEX-FLOOR, 2026-09-13 -- SEMANTIC_REGEX_MATCH_LIGHT was '#ffff99',\n# which collapsed onto the #f5f5f5 test pane under achromatopsia at CIEDE2000\n", 1), ('utils/colors.py', "# WHAT WAS WRONG WITH THE OLD SIX. '#4d1a1a' collapsed to #181818 under\n# achromatopsia, on a panel that collapses to #191919: CIEDE2000 0.31, so a\n# deleted line carried no visible highlight at all. The added/changed pair\n# read 8.08 dark and 7.81 light, both under the bar. A first re-derivation\n# missed both, because it measured pairs in dE76 and read them against a bar\n# published in CIEDE2000, and never measured a fill against its ground under\n# any simulation at all.\n", "# WHAT WAS WRONG WITH THE OLD SIX. Two of them failed the ground rule under\n# achromatopsia, where every colour collapses to luma:\n#\n#   '#4d1a1a' dark    -> #292929 on a #191919 panel   CIEDE2000 5.03\n#   '#f8d7da' light   -> #e1e1e1 on a #f5f5f5 pane    CIEDE2000 4.27\n#\n# Both under the 8.40 bar, so both were genuinely too near the surface they\n# sat on -- a faint band rather than a highlight. Neither was invisible; the\n# values that were are in the pinned table in tests/test_diff_floors.py.\n#\n# The added/changed pair read 8.08 dark and 7.81 light, both under the bar. A\n# first re-derivation missed all of it, because it measured pairs in dE76 and\n# read them against a bar published in CIEDE2000, and never measured a fill\n# against its ground under any simulation at all.\n#\n# THIS PARAGRAPH WAS ITSELF WRONG FOR A DAY, 2026-09-13 (RNV-FIGURE-PIN). It\n# described '#4d1a1a' with four figures -- 0.31, #181818, 15.87, and a text\n# contrast of 12.97 -- every one of which belonged to '#2e0f10', a candidate\n# derived during the same round and rejected. The substitution was of the\n# whole measurement, not of one digit, and nothing checked it, so it read as\n# measured and travelled into two delivery scripts and two project notes. It\n# also overstated the defect: 5.03 is faint, 0.31 is absent. The figures now\n# live in an assertion; see RETIRED_FILLS in the guard.\n", 1), ('tests/test_diff_floors.py', "  1. SEMANTIC_DIFF_REMOVED was '#4d1a1a'. Under achromatopsia it collapses to\n     #181818, on a panel that collapses to #191919 -- CIEDE2000 **0.31**. A\n     deleted line carried no visible highlight at all. Contrast against the\n     TEXT was 12.97 and had been checked; the fill had never been measured\n     against the GROUND under a simulation, because the pairs were and it\n     read as though everything had been.\n", "  1. SEMANTIC_DIFF_REMOVED was '#4d1a1a'. Under achromatopsia it collapses to\n     #292929, on a panel that collapses to #191919 -- CIEDE2000 **5.03**,\n     under the 8.40 bar. A deleted line carried a band too faint to read as a\n     highlight. Its light partner '#f8d7da' failed the same way at **4.27**.\n     Contrast against the TEXT was 10.4591 and had been checked; the fill had\n     never been measured against the GROUND under a simulation, because the\n     pairs were and it read as though everything had been.\n\n     THOSE FOUR FIGURES WERE WRONG HERE FOR A DAY. This paragraph gave 0.31,\n     #181818, 15.87 and 12.97 -- all of them '#2e0f10', a candidate derived\n     in the same round and rejected. Nothing checked them, so they read as\n     measured. RETIRED_FILLS below now pins every figure this file prints\n     about a retired value, and test_the_instrument_can_fail asserts them.\n", 1), ('tests/test_diff_floors.py', 'def test_the_instrument_can_fail():\n    """A floor nothing can breach is decoration.\n\n    \'#4d1a1a\' is the value this round retired, and the reason: under\n    achromatopsia it is #181818 against a #191919 panel. If the ground rule\n    below cannot see that, it cannot see anything.\n    """\n    ground = palette("DARK")[GROUND_KEY]\n    distance, eye = worst("#4d1a1a", ground)\n    assert distance < DE_FLOOR, (\n        f"the retired dark red reads {distance:.2f} from {ground} at its "\n        f"worst ({eye}), which is over the floor -- so the ground rule is "\n        f"not measuring what it was written to measure.")\n    assert eye == "achromatopsia", (\n        f"the retired dark red is closest to the panel under {eye}, not "\n        f"achromatopsia. The simulation set has changed shape.")\n', '#: The fills RNV-DIFF-FLOORS retired, and every figure this file prints about\n#: them: mode, what it collapses to under achromatopsia, its worst distance\n#: from its own pane, its distance in normal vision, and its contrast against\n#: the ink. RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN.\n#:\n#: PINNED RATHER THAN NARRATED, and the reason is this table\'s own history.\n#: The first version of this guard described \'#4d1a1a\' with four figures that\n#: all belonged to a different hex -- a candidate derived during the same\n#: round and rejected. Prose cannot be wrong loudly. An assertion can.\nRETIRED_FILLS = {\n    "#4d1a1a": ("DARK", "#292929", 5.03, 20.85, 10.4591),\n    "#f8d7da": ("LIGHT", "#e1e1e1", 4.27, 13.69, 15.7238),\n}\n\n\ndef test_the_instrument_can_fail():\n    """A floor nothing can breach is decoration.\n\n    Every figure in RETIRED_FILLS is checked here against the instrument this\n    file ships, so a number quoted in a docstring is a number a test agrees\n    with. If the ground rule cannot still see why these two were retired, it\n    cannot see anything.\n    """\n    for fill, (mode, collapse, want_worst, want_normal, want_text) in \\\n            RETIRED_FILLS.items():\n        pal = palette(mode)\n        ground, ink = pal[GROUND_KEY], pal[INK_KEY]\n\n        assert simulate(fill, "achromatopsia") == collapse, (\n            f"{fill} collapses to {simulate(fill, \'achromatopsia\')} under "\n            f"achromatopsia, not {collapse} as this file says. A figure "\n            f"describing one value with another value\'s measurement is the "\n            f"defect this table exists to stop.")\n\n        distance, eye = worst(fill, ground)\n        assert eye == "achromatopsia", (\n            f"{fill} is closest to its pane under {eye}, not achromatopsia. "\n            f"The simulation set has changed shape.")\n        assert abs(distance - want_worst) < 0.005, (\n            f"{fill} reads {distance:.2f} from {ground} at its worst, and "\n            f"this file says {want_worst}. One of them is stale.")\n        assert distance < DE_FLOOR, (\n            f"{fill} reads {distance:.2f} from {ground}, over the floor -- "\n            f"so the ground rule is not measuring what it was written to "\n            f"measure.")\n\n        assert abs(ciede2000(fill, ground) - want_normal) < 0.005, (\n            f"{fill} reads {ciede2000(fill, ground):.2f} from {ground} in "\n            f"normal vision, and this file says {want_normal}.")\n        assert abs(contrast(fill, ink) - want_text) < 0.00005, (\n            f"{fill} reads {contrast(fill, ink):.4f} against {ink}, and this "\n            f"file says {want_text}. That figure is the one the original "\n            f"round cited to show the fill had been checked; it was the "\n            f"wrong value\'s.")\n\n    assert len(RETIRED_FILLS) == 2, (\n        "RETIRED_FILLS should hold both halves of the pair that failed. One "\n        "entry means a mode is being described and not measured -- the "\n        "original round cited only the dark half and never noticed the light "\n        "one failed too.")\n', 1), ('tests/test_diff_floors.py', 'def test_every_fill_is_visible_against_its_own_pane():\n    """The rule the old dark red failed at 0.31.\n\n    Measured under all five, because the failure was invisible under four of\n    them: \'#4d1a1a\' reads 15.87 from the panel in normal vision.\n    """\n', 'def test_every_fill_is_visible_against_its_own_pane():\n    """The rule the old dark red failed at 5.03, and its light partner at 4.27.\n\n    Measured under all five, because the failure is invisible under four of\n    them: \'#4d1a1a\' reads 20.85 from the panel in normal vision and 5.03 at\n    its worst. The figures are pinned in RETIRED_FILLS above.\n    """\n', 1)]


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))

# --------------------------------------------------- the arithmetic, again
# A second copy of what the guard holds, deliberately: checks() runs against
# the in-memory tree before utils/colors.py on disk carries the new value, so
# it cannot import the guard and ask it, and a check that read the old file
# would pass on the wrong number.
MATRICES = {
    "protanopia":   ((0.567, 0.433, 0.000), (0.558, 0.442, 0.000),
                     (0.000, 0.242, 0.758)),
    "deuteranopia": ((0.625, 0.375, 0.000), (0.700, 0.300, 0.000),
                     (0.000, 0.300, 0.700)),
    "tritanopia":   ((0.950, 0.050, 0.000), (0.000, 0.433, 0.567),
                     (0.000, 0.475, 0.525)),
}
VISION = ("normal", "protanopia", "deuteranopia", "tritanopia", "achromatopsia")


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hx(t):
    return "#%02x%02x%02x" % t


def _contrast(a, b):
    def lum(c):
        def f(v):
            v /= 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
    la, lb = lum(_rgb(a)), lum(_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return math.floor((hi + 0.05) / (lo + 0.05) * 10000) / 10000


def _sim(h, kind):
    if kind == "normal":
        return h.lower()
    r, g, b = _rgb(h)
    if kind == "achromatopsia":
        y = int(0.299 * r + 0.587 * g + 0.114 * b)
        return _hx((y, y, y))
    m = MATRICES[kind]
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    return _hx(tuple(int(max(0.0, min(1.0, row[0] * rf + row[1] * gf
                                      + row[2] * bf)) * 255) for row in m))


def _lab(h):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in _rgb(h))
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = (0.2126729 * r + 0.7151522 * g + 0.0721750 * b)
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def g_(t):
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
    fx, fy, fz = g_(x), g_(y), g_(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _de2000(one, two):
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


def _worst(one, two):
    return min((_de2000(_sim(one, v), _sim(two, v)), v) for v in VISION)


def _constants(text):
    out = {}
    for node in ast.walk(ast.parse(text)):
        if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and re.fullmatch(r"#[0-9a-fA-F]{6}", node.value.value)):
            out[node.target.id] = node.value.value.lower()
    return out


def _palette(text, which, consts):
    out = {}
    for node in ast.walk(ast.parse(text)):
        if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.target.id == which and isinstance(node.value, ast.Dict)):
            for k, v in zip(node.value.keys, node.value.values):
                if not isinstance(k, ast.Constant):
                    continue
                if isinstance(v, ast.Name) and v.id in consts:
                    out[k.value] = consts[v.id]
                elif (isinstance(v, ast.Constant) and isinstance(v.value, str)
                      and re.fullmatch(r"#[0-9a-fA-F]{6}", v.value)):
                    out[k.value] = v.value.lower()
    return out



def checks(tree) -> None:
    guard_txt = tree.files[GUARD]
    colors_txt = tree.files["utils/colors.py"]
    styles_txt = (Path.cwd() / "utils" / "dialog_styles.py").read_text(
        encoding="utf-8")
    consts = _constants(colors_txt)

    # 1. the table landed, with both entries and the values this round means.
    pinned = {}
    for node in ast.walk(ast.parse(guard_txt)):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == "RETIRED_FILLS"
                and isinstance(node.value, ast.Dict)):
            for k, v in zip(node.value.keys, node.value.values):
                pinned[k.value] = tuple(e.value for e in v.elts)
    if pinned != WANT_FILLS:
        raise SystemExit(f"RETIRED_FILLS is {pinned}, not {WANT_FILLS}")

    # 2. every pinned figure re-derived from the palette, not trusted. This is
    #    the round: the last one published four numbers nothing re-derived.
    bad = []
    for fill, (mode, collapse, w_worst, w_normal, w_text) in pinned.items():
        pal = _palette(styles_txt, mode, consts)
        ground, ink = pal["bg"], pal["text"]
        got = _sim(fill, "achromatopsia")
        if got != collapse:
            bad.append(f"{fill} collapses to {got}, pinned {collapse}")
        d, eye = _worst(fill, ground)
        if eye != "achromatopsia":
            bad.append(f"{fill} closest to its pane under {eye}")
        if abs(d - w_worst) >= 0.005:
            bad.append(f"{fill} worst {d:.2f}, pinned {w_worst}")
        if d >= 8.40:
            bad.append(f"{fill} reads {d:.2f} -- over the floor it was "
                       f"retired for, so the story does not hold")
        n = _de2000(fill, ground)
        if abs(n - w_normal) >= 0.005:
            bad.append(f"{fill} normal {n:.2f}, pinned {w_normal}")
        t = _contrast(fill, ink)
        if abs(t - w_text) >= 0.00005:
            bad.append(f"{fill} text {t:.4f}, pinned {w_text}")
    if bad:
        raise SystemExit("pinned figures do not re-derive:\n  "
                         + "\n  ".join(bad))

    # 3. the six values that SHIP are untouched. This round corrects prose; if
    #    a rendered value moved, something went wrong in an anchor.
    for mode, keys in (("DARK", ("diff_added_bg", "diff_removed_bg",
                                 "diff_changed_bg", "regex_match_bg")),
                       ("LIGHT", ("diff_added_bg", "diff_removed_bg",
                                  "diff_changed_bg", "regex_match_bg"))):
        pal = _palette(styles_txt, mode, consts)
        for key in keys:
            if key not in pal:
                raise SystemExit(f"{mode}[{key}] vanished; this round should "
                                 f"not touch a palette")

    # 4. the instrument, before its figures are trusted.
    got = _de2000("#d2bc93", "#b49e75")
    if abs(got - 8.4035) >= 0.0005:
        raise SystemExit(f"CIEDE2000(#d2bc93, #b49e75) = {got:.4f}, and the "
                         f"register publishes 8.4035")

    # 5. the sentinel is in the file the already-applied check reads.
    if SENTINEL not in tree.files[SENTINEL_FILE]:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print(f"  guards: {len(pinned)} retired fills pinned and every figure "
          f"re-derived, 8 shipped values untouched, instrument reads {got:.4f}")



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
        self.deleted: set[str] = set()

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush().

        Added for the round that retired the last CI deselect: with no
        deselects left, tests/test_ci_deselects.py swept an empty set and
        would have passed over nothing. Its own failure message said to
        delete it in the commit that removed the last one, so the harness
        needed to be able to.
        """
        if not (self.root / rel).exists() and rel not in self.files:
            raise SystemExit(f"cannot delete {rel}: it is not in this checkout")
        self.files.pop(rel, None)
        self.deleted.add(rel)

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
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
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
