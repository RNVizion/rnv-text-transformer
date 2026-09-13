#!/usr/bin/env python3
"""
RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP

Walk the light regex-match highlight off its pane, and widen the floors guard
so it stops naming the values it covers.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

SEMANTIC_REGEX_MATCH_LIGHT was '#ffff99'. Against the Regex Builder's test
pane it reads 23.83 in normal vision and 0.41 under achromatopsia -- the pale
highlighter collapses to #f3f3f3 and the pane to #f5f5f5, so a matched span
carries no visible highlight at all. It is the same failure as the diff red
RNV-DIFF-FLOORS retired this morning, it sits one line below the three values
that round moved, in the same file, and that round did not look at it.

The guard it installed could not have caught it. It swept a tuple named
DIFF_KEYS, and a rule that lists the values it covers is always one value
behind the file it lives in. So this round moves the value AND widens the
ground and ink rules to every fill this application paints behind text -- the
diff three, plus whatever the Regex Builder is found to draw, derived from the
dialog rather than listed beside it.

THE VALUE

    SEMANTIC_REGEX_MATCH_LIGHT   #ffff99 -> #cdcf6b

Walked down its own hue line -- hue held to 0.03 degrees, chroma to 0.4 -- to
the first point that clears the pane with real margin rather than by a
whisker: ground 11.37 against a floor of 8.40, which is 35% over, and text
12.7332 against black. The first value that merely cleared read 8.42.

SEMANTIC_REGEX_MATCH '#4a4a00', the dark half, was measured under the same
five eyes and does NOT have the defect -- text 6.8090, ground 12.75. It is
unchanged, and now carries its figures in a comment so the next reader does
not have to re-derive them to find that out.

WHAT THE GUARD DOES NOW

tests/test_diff_floors.py keeps its three floors and its two self-checks. The
ground and ink rules now iterate highlight_keys(), which is DIFF_KEYS plus
regex_keys() -- and regex_keys() reads ui/regex_builder_dialog.py for every
ClassVar that resolves to a DialogStyleManager key and is referenced anywhere
in the file. The pair rule is untouched: a match has no co-visible partner,
because that pane holds exactly one fill. A new assertion says so, and goes
red if a second one is ever wired in without a pair rule to go with it.

FALSIFIED FIVE WAYS, AND ONE CONTROL

Reverting the value, lightening it back toward the pane, pointing the
derivation at a dialog that paints nothing, painting a second fill into the
match pane, and moving the value without re-pinning it -- all five land red in
the named test.

The control matters more. Reverting the value AND narrowing the sweep back to
DIFF_KEYS stays GREEN, which is the evidence that the width of the sweep is
what catches this rather than something else that happened to be in the way.

Two things were found by that falsification rather than by inspection. A
tamper that only DECLARED a second ClassVar stayed green -- correctly, since a
ClassVar nothing reads paints nothing, which is exactly what the retired
capture-group palette was. And once the tamper actually painted with it, the
first derivation still stayed green: it looked inside setBackground calls
first and fell back to the whole file only when that found nothing, so a
dialog painting one fill through a local and another directly reported just
the direct one. Under-reporting is the one direction a blindness check must
not fail in. It now counts every reference.
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
SENTINEL = "RNV-REGEX-FLOOR"
GUARD = "tests/test_diff_floors.py"
DESCRIPTION = "walk the light regex match off its pane, and widen the guard"
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
    "This round builds on RNV-DIFF-FLOORS, which must have landed first -- it "
    "is the round that installed tests/test_diff_floors.py, and this one "
    "widens it.")

#: What must be true of the tree this script is about to write.
WANT = {"DARK": {"regex_match_bg": "#4a4a00"},
        "LIGHT": {"regex_match_bg": "#cdcf6b"}}


EDITS = [('tests/conftest.py', '# RNV-DIFF-FLOORS, 2026-09-13 -- tests/test_diff_floors.py holds the six diff\n# highlight values to three floors per mode: the ink on the fill clears WCAG\n', "# RNV-REGEX-FLOOR, 2026-09-13 -- SEMANTIC_REGEX_MATCH_LIGHT was '#ffff99',\n# which collapsed onto the #f5f5f5 test pane under achromatopsia at CIEDE2000\n# 0.41: a matched span carried no visible highlight at all. Same failure as\n# the diff red retired the same day, one line below it in utils/colors.py,\n# and that round did not look at it. tests/test_diff_floors.py now sweeps\n# EVERY fill this application draws behind text rather than the three it was\n# written for, and derives the Regex Builder's from the dialog itself.\n# RNV-DIFF-FLOORS, 2026-09-13 -- tests/test_diff_floors.py holds the six diff\n# highlight values to three floors per mode: the ink on the fill clears WCAG\n", 1), ('utils/colors.py', "SEMANTIC_REGEX_MATCH: Final[str] = '#4a4a00'\n\nSEMANTIC_REGEX_MATCH_LIGHT: Final[str] = '#ffff99'\n", "#: text 6.8090, ground 12.75. Checked under the same five eyes as the diff\n#: values and left alone -- this one never had the defect.\nSEMANTIC_REGEX_MATCH: Final[str] = '#4a4a00'\n\n#: RNV-REGEX-FLOOR (2026-09-13). Was '#ffff99', which read 23.83 from the\n#: test pane in normal vision and 0.41 under achromatopsia -- the pale\n#: highlighter and the #f5f5f5 pane collapse to #f3f3f3 and #f5f5f5, so a\n#: matched span carried no visible highlight at all. Same failure as the diff\n#: red that RNV-DIFF-FLOORS retired, one line below the three values that\n#: round moved, and that round did not look at it.\n#:\n#: Walked down its own hue line -- hue held to 0.03 degrees, chroma to 0.4 --\n#: until the pane cleared with margin rather than by a whisker.\n#: text 12.7332, ground 11.37, which is 35% over the floor.\nSEMANTIC_REGEX_MATCH_LIGHT: Final[str] = '#cdcf6b'\n", 1), ('tests/test_semantic_naming.py', "'SEMANTIC_REGEX_MATCH': '#4a4a00', 'SEMANTIC_REGEX_MATCH_LIGHT': '#ffff99'}", "'SEMANTIC_REGEX_MATCH': '#4a4a00', 'SEMANTIC_REGEX_MATCH_LIGHT': '#cdcf6b'}", 1), ('tests/__snapshots__/test_snapshots.ambr', '    "regex_match_bg": "#ffff99",\n', '    "regex_match_bg": "#cdcf6b",\n', 1), ('tests/test_diff_floors.py', '  text     WCAG 2.1, fill against the ink actually drawn on it      >= 4.5\n  ground   CIEDE2000, fill against the pane it sits on              >= 8.40\n  pair     CIEDE2000, between two roles that can share a widget     >= 8.40\n', "  text     WCAG 2.1, fill against the ink actually drawn on it      >= 4.5\n  ground   CIEDE2000, fill against the pane it sits on              >= 8.40\n  pair     CIEDE2000, between two roles that can share a widget     >= 8.40\n\nRNV-REGEX-FLOOR (2026-09-13) widened the first two rules past the diff three.\nSEMANTIC_REGEX_MATCH_LIGHT '#ffff99' had the same defect as the diff red and\nwas one line below it in the same file, and the round that fixed the three\nwalked past it: 23.83 from the test pane in normal vision, 0.41 under\nachromatopsia. A rule that names the values it covers will always be one\nvalue behind the file, so the ground and ink rules now sweep every fill this\napplication paints behind text -- the diff three, plus whatever the Regex\nBuilder is found to draw.\n", 1), ('tests/test_diff_floors.py', 'DIALOG = ROOT / "ui" / "compare_dialog.py"\nEXPORT = ROOT / "core" / "diff_engine.py"\n', 'DIALOG = ROOT / "ui" / "compare_dialog.py"\nEXPORT = ROOT / "core" / "diff_engine.py"\nREGEX = ROOT / "ui" / "regex_builder_dialog.py"\n', 1), ('tests/test_diff_floors.py', '    return ast.parse(DIALOG.read_text(encoding="utf-8"), str(DIALOG))\n\n\ndef _classvar_keys() -> dict[str, tuple[str, str]]:\n    """_ADDED_COLOR_DARK -> (\'DARK\', \'diff_added_bg\'), read off the class."""\n    out = {}\n    for node in ast.walk(_dialog_tree()):\n', '    return _tree(DIALOG)\n\n\ndef _tree(path: Path) -> ast.Module:\n    return ast.parse(path.read_text(encoding="utf-8"), str(path))\n\n\ndef _classvar_keys(path: Path = None) -> dict[str, tuple[str, str]]:\n    """_ADDED_COLOR_DARK -> (\'DARK\', \'diff_added_bg\'), read off the class.\n\n    Takes a path because the Regex Builder declares its own fill the same way\n    and this guard now measures that one too.\n    """\n    out = {}\n    for node in ast.walk(_tree(path or DIALOG)):\n', 1), ('tests/test_diff_floors.py', 'DIFF_KEYS = ("diff_added_bg", "diff_removed_bg", "diff_changed_bg")\n', 'DIFF_KEYS = ("diff_added_bg", "diff_removed_bg", "diff_changed_bg")\n\n\ndef regex_keys() -> tuple[str, ...]:\n    """The palette keys ui/regex_builder_dialog.py paints into its test pane.\n\n    Derived rather than listed, for the same reason the diff pairs are: this\n    dialog used to declare a second family of eight capture-group fills, and\n    they were retired only after a render proved nothing drew them. If a\n    second fill is ever wired back in, the blindness test below says so\n    rather than this guard quietly measuring one of two.\n\n    ANY reference counts, not only one inside a setBackground call. The\n    first version looked in setBackground first and fell back to the whole\n    file only when that found nothing -- two branches, mutually exclusive, so\n    a dialog painting one fill through a local and another directly reported\n    just the direct one. A tamper that wired a second fill in stayed green on\n    that version. Under-reporting is the one direction a blindness check must\n    not fail in, so this counts every reference and accepts that a declared\n    colour nobody draws with would be measured too; a fill that clears the\n    floors and is never painted costs nothing.\n\n    The retired names are not spelled here. tests/test_semantic_naming.py\n    owns that rule and sweeps raw text, so a guard that names what it is glad\n    to be rid of lands red in it -- which this docstring did, one round after\n    the paragraph in this same file explaining that exact trap.\n    """\n    keys = _classvar_keys(REGEX)\n    used = {keys[n.attr][1] for n in ast.walk(_tree(REGEX))\n            if isinstance(n, ast.Attribute) and n.attr in keys}\n    return tuple(sorted(used))\n\n\ndef highlight_keys() -> tuple[str, ...]:\n    """Every semantic fill this application draws behind text.\n\n    The diff three plus whatever the Regex Builder paints. They share the\n    ground and the ink floors and nothing else -- a match has no co-visible\n    partner, because after RNV-DIFF-FLOORS its pane holds exactly one fill.\n    """\n    return DIFF_KEYS + regex_keys()\n', 1), ('tests/test_diff_floors.py', '        ink = pal[INK_KEY]\n        for key in DIFF_KEYS:\n', '        ink = pal[INK_KEY]\n        for key in highlight_keys():\n', 1), ('tests/test_diff_floors.py', '        ground = pal[GROUND_KEY]\n        for key in DIFF_KEYS:\n', '        ground = pal[GROUND_KEY]\n        for key in highlight_keys():\n', 1), ('tests/test_diff_floors.py', '    assert export_keys(), (\n', '    matches = regex_keys()\n    assert len(matches) == 1, (\n        f"ui/regex_builder_dialog.py paints {len(matches)} fill(s) into its "\n        f"test pane: {matches}. This guard measures every one it finds "\n        f"against the ground and the ink, but it has no pair rule for them -- "\n        f"one fill in a pane owes nobody a separation. Two do. If a second "\n        f"family is back, give them a pair rule before landing it.")\n    assert matches[0] in palette("DARK") and matches[0] in palette("LIGHT"), (\n        f"{matches[0]} is not in both palettes, so one mode is unmeasured")\n\n    assert export_keys(), (\n', 1)]


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
    colors_txt = tree.files["utils/colors.py"]
    styles_txt = (tree.files.get("utils/dialog_styles.py")
                  or (Path.cwd() / "utils/dialog_styles.py").read_text(
                      encoding="utf-8"))
    consts = _constants(colors_txt)

    # 1. the value landed, and the palette points at it.
    for which, want in WANT.items():
        pal = _palette(styles_txt, which, consts)
        for key, value in want.items():
            if pal.get(key) != value:
                raise SystemExit(
                    f"{which}[{key}] resolves to {pal.get(key)}, not {value}")

    # 2. EVERY fill the guard will sweep clears both floors -- computed here
    #    against the tree about to be written, not the one on disk.
    guard_txt = tree.files[GUARD]
    keys = ["diff_added_bg", "diff_removed_bg", "diff_changed_bg",
            "regex_match_bg"]
    bad = []
    for which in ("DARK", "LIGHT"):
        pal = _palette(styles_txt, which, consts)
        ground, ink = pal["bg"], pal["text"]
        for key in keys:
            ratio = _contrast(pal[key], ink)
            if ratio < 4.5:
                bad.append(f"{which}[{key}] on ink {ink}: {ratio:.4f} < 4.5")
            distance, eye = _worst(pal[key], ground)
            if distance < 8.40:
                bad.append(f"{which}[{key}] against {ground}: "
                           f"{distance:.2f} < 8.40 under {eye}")
    if bad:
        raise SystemExit("the floors do not hold:\n  " + "\n  ".join(bad))

    # 3. the guard actually WIDENED. A round whose point is the width of a
    #    sweep has to check the width, or it is a value change with a story.
    if "highlight_keys()" not in guard_txt:
        raise SystemExit(f"{GUARD} does not call highlight_keys(); the sweep "
                         f"was not widened and the value change stands alone")
    if guard_txt.count("for key in DIFF_KEYS:") != 0:
        raise SystemExit(f"{GUARD} still iterates DIFF_KEYS in a floor rule")

    # 4. the instrument, before its figures are trusted.
    got = _de2000("#d2bc93", "#b49e75")
    if abs(got - 8.4035) >= 0.0005:
        raise SystemExit(f"CIEDE2000(#d2bc93, #b49e75) = {got:.4f}, and the "
                         f"register publishes 8.4035")

    # 5. the sentinel is in the file the already-applied check reads.
    if SENTINEL not in tree.files[SENTINEL_FILE]:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print(f"  guards: 4 fills clear both floors in both modes, the sweep is "
          f"widened, instrument reads {got:.4f}")



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
