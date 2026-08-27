#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Move rnv-text-transformer's pressed state into the stylesheet, where every
press path can reach it.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE APP ALREADY HAD A PRESS STATE. THIS IS NOT ABOUT ADDING ONE.

`_on_press` rewrites the label colour in Python, and image mode swaps to a
dedicated pressed pixmap. Under a mouse it looks right, and it is right. What
was wrong is how the appearance was assembled, and it is reachable two ways:

1. THE GROUND CAME FROM `:hover`. Pressed and hovered are different states
   that merely coincide under a mouse. Press the button any other way -- Space
   or Enter on a focused button, a programmatic click(), or holding the mouse
   down and dragging off the button -- and `:hover` stops matching while the
   label stays flipped. Measured on this palette:

       DARK   #000000 on #1a1a1a = 1.21:1
       LIGHT  #ffffff on #ffffff = 1.00:1   -- white on white

2. A RESIZE WHILE HELD REVERTED THE LABEL. `resizeEvent` calls
   `update_text_font_size`, which rebuilds the stylesheet with no text_color
   argument, so the label falls back to resting while `is_pressed_state` is
   still True. Reproduced: held #000000 -> after a resize #e0e0e0 with
   is_pressed_state still True. The image-mode branch of that same method
   checks `is_pressed_state`; the text branch does not.

Both disappear once `QPushButton:pressed` carries the ground AND the label.
Qt applies that rule to the sunken state however the press arrived -- checked
against setDown(True), which is the path keyboard activation takes -- and
being declarative it survives every stylesheet rebuild.

WHAT MOVES

  utils/dialog_styles.py     a button_pressed_bg key in both palettes, set to
                             GREY_44 -- the ramp step already named in
                             utils/colors.py, so no new constant is minted
  ui/image_button.py         a QPushButton:pressed rule carrying both the
                             plate and the label
  ui/main_window.py          the same on the theme button, in both the
                             dark/light and the image-mode branch
  tests/__snapshots__/       the two get_colors snapshots gain one key each,
                             hand-edited into sorted position rather than
                             regenerated, so nothing else can move unnoticed
  tests/test_button_press_step.py    new, nine tests

WHAT DOES NOT MOVE

Image mode. `apply_style` gives it `border: none; background: transparent` and
drives the whole appearance through pixmaps, so `_build_text_mode_stylesheet`
never runs there and nothing in this change can reach it.

`_update_text_mode_pressed` still runs and still sets the same label colour.
It is now reinforcement rather than the mechanism. Leaving it costs nothing
and removing it would be a second change riding along with this one.

WHY THE ORDER MATTERS

`:pressed` is emitted AFTER `:hover`. They have equal specificity in Qt's
cascade, so the later rule wins while both match -- which is exactly the state
a real mouse press is in. Emitted first, the plate would never step. The
script asserts the ordering rather than trusting it.

THE GUARD PROVES ITSELF

Checked in both directions on a scratch tree: with the rule in place all nine
pass; with it removed, four fail, and two of those fail by RENDERING the button
while down-but-not-hovered and finding no label pixels distinguishable from the
plate. That is the defect above, photographed rather than computed.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-text-transformer"
DESCRIPTION = "move the pressed state into the stylesheet"
SENTINEL_FILE = "utils/dialog_styles.py"
SENTINEL = "button_pressed_bg"
GUARD = "tests/test_button_press_step.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "dialog_styles.py"}

STYLES = "utils/dialog_styles.py"
IMAGE_BUTTON = "ui/image_button.py"
MAIN_WINDOW = "ui/main_window.py"
SNAPSHOT = "tests/__snapshots__/test_snapshots.ambr"

# Run them the way .github/workflows/tests.yml runs them.
SUITES = [
    ("pytest tests/ (about 4 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "--benchmark-disable", "-q",
      "-p", "no:cacheprovider"]),
    ("unittest suite",
     [sys.executable, "-m", "unittest", "test_rnv_text_transformer"]),
]

PRESSED_IMAGE_BUTTON = (
    "            QPushButton:pressed {{\n"
    "                background-color: {theme['button_pressed_bg']};\n"
    "                color: {theme['button_pressed_text']};\n"
    "            }}\n")
PRESSED_MAIN_WINDOW = (
    "            QPushButton:pressed {{\n"
    "                background-color: {pressed_bg};\n"
    "                color: {pressed_color};\n"
    "            }}\n")


def edits(tree) -> None:
    tree.sub(STYLES,
             "        'button_hover_bg': APP_BORDER,\n"
             "        'button_pressed_text': TRUE_BLACK,",
             "        'button_hover_bg': APP_BORDER,\n"
             "        'button_pressed_bg': GREY_44,\n"
             "        'button_pressed_text': TRUE_BLACK,")
    tree.sub(STYLES,
             "        'button_hover_bg': APP_BORDER,\n"
             "        'button_pressed_text': WHITE,",
             "        'button_hover_bg': APP_BORDER,\n"
             "        'button_pressed_bg': GREY_44,\n"
             "        'button_pressed_text': WHITE,")

    tree.sub(IMAGE_BUTTON,
             "            QPushButton:hover {{\n"
             "                background-color: {theme['button_hover_bg']};\n"
             "            }}\n        \"\"\"",
             "            QPushButton:hover {{\n"
             "                background-color: {theme['button_hover_bg']};\n"
             "            }}\n" + PRESSED_IMAGE_BUTTON + "        \"\"\"")

    tree.sub(MAIN_WINDOW,
             "            border = _d['border']\n"
             "            hover_color = color",
             "            border = _d['border']\n"
             "            hover_color = color\n"
             "            pressed_bg = _d['button_pressed_bg']\n"
             "            pressed_color = _d['button_pressed_text']")
    tree.sub(MAIN_WINDOW,
             "            else:\n"
             "                color = theme['button_text']\n"
             "                hover_color = theme['button_text']\n        ",
             "            else:\n"
             "                color = theme['button_text']\n"
             "                hover_color = theme['button_text']\n"
             "            pressed_bg = theme['button_pressed_bg']\n"
             "            pressed_color = theme['button_pressed_text']\n        ")
    tree.sub(MAIN_WINDOW,
             "            QPushButton:hover {{\n"
             "                background-color: {hover_bg};\n"
             "                color: {hover_color};\n"
             "            }}\n        \"\"\"",
             "            QPushButton:hover {{\n"
             "                background-color: {hover_bg};\n"
             "                color: {hover_color};\n"
             "            }}\n" + PRESSED_MAIN_WINDOW + "        \"\"\"")

    # Sorted keys: button_pressed_bg sorts immediately before
    # button_pressed_text, so each insertion goes in front of it.
    tree.sub(SNAPSHOT,
             '    "button_pressed_text": "#000000",',
             '    "button_pressed_bg": "#444444",\n'
             '    "button_pressed_text": "#000000",')
    tree.sub(SNAPSHOT,
             '    "button_pressed_text": "#ffffff",',
             '    "button_pressed_bg": "#444444",\n'
             '    "button_pressed_text": "#ffffff",')


def checks(tree) -> None:
    styles = tree.read(STYLES)
    if styles.count("'button_pressed_bg': GREY_44,") != 2:
        raise SystemExit("expected the pressed plate in exactly two palettes")
    if "    GREY_44," not in styles:
        raise SystemExit(f"GREY_44 is not imported into {STYLES}")

    for rel in (IMAGE_BUTTON, MAIN_WINDOW):
        src = tree.read(rel)
        if "QPushButton:pressed" not in src:
            raise SystemExit(f"{rel}: no pressed rule was added")
        block = src[src.index("QPushButton:pressed"):]
        block = block[:block.index("}}")]
        if "background-color" not in block or "color:" not in block:
            raise SystemExit(
                f"{rel}: the pressed rule must carry BOTH the plate and the "
                f"label. Splitting them is what let a keyboard press render "
                f"the label on the resting plate.")
        if src.index("QPushButton:pressed") < src.index("QPushButton:hover"):
            raise SystemExit(
                f"{rel}: the pressed rule is emitted before the hover rule. "
                f"Equal specificity means the later one wins, so the plate "
                f"would never step.")

    snap = tree.read(SNAPSHOT)
    if snap.count('"button_pressed_bg": "#444444",') != 2:
        raise SystemExit("expected the new key in exactly two snapshots")


GUARD_SOURCE = '"""\nThe main button\'s pressed state is declared in the stylesheet, not assembled\nin Python.\n\nRULED 2026-08-26.\n\nWHAT WAS WRONG, AND IT WAS NOT THE COLOURS\n\nThe app already had a press state: `_on_press` rewrote the base rule\'s label\ncolour, and image mode swapped to a dedicated pressed pixmap. Under the mouse\nit looked right. It was reached two ways that do not hold up:\n\n  1. THE GROUND CAME FROM `:hover`. Pressed and hovered are different states\n     that merely coincide under a mouse. Press the button any other way --\n     Space or Enter on a focused button, a programmatic click(), or holding\n     the mouse down and dragging off -- and `:hover` stops matching while the\n     label stays flipped. Measured on this palette:\n\n         DARK   #000000 on #1a1a1a = 1.21:1\n         LIGHT  #ffffff on #ffffff = 1.00:1   -- white on white\n\n  2. A RESIZE WHILE HELD REVERTED THE LABEL. `resizeEvent` calls\n     `update_text_font_size`, which rebuilds the stylesheet with no text_color\n     argument, so the label fell back to resting while `is_pressed_state` was\n     still True. The image-mode branch of the same method checks\n     `is_pressed_state`; the text branch did not.\n\nBoth disappear once `QPushButton:pressed` carries the ground AND the label.\nQt applies that rule to the sunken state however the press arrived -- verified\nagainst `setDown(True)`, which is the path keyboard activation takes -- and\nbeing declarative it survives every stylesheet rebuild.\n\n`_update_text_mode_pressed` still runs and still sets the same label colour.\nIt is now reinforcement rather than the mechanism, and the tests below hold\nthe stylesheet, which is the thing that has to be right.\n"""\nfrom __future__ import annotations\n\nimport collections\nimport re\n\nimport pytest\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QPixmap\n\nfrom utils.dialog_styles import DialogStyleManager\n\nTHEMES = {"DARK": True, "LIGHT": False}\n\n\ndef _lum(value: str) -> float:\n    h = value.lstrip("#")\n    if len(h) == 8:                      # Qt #AARRGGBB\n        h = h[2:]\n    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    la, lb = _lum(a), _lum(b)\n    hi, lo = max(la, lb), min(la, lb)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef test_both_palettes_carry_the_button_keys():\n    """Guard the guard. Every test below reads these; a rename that emptied\n    them would leave the rest passing while checking nothing."""\n    for name, is_dark in THEMES.items():\n        colors = DialogStyleManager.get_colors(is_dark)\n        for key in ("button_bg", "button_hover_bg", "button_pressed_bg",\n                    "button_text", "button_pressed_text"):\n            assert key in colors, f"{name} has no {key}"\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_plate_steps_on_press(name):\n    colors = DialogStyleManager.get_colors(THEMES[name])\n    hover, pressed = colors["button_hover_bg"], colors["button_pressed_bg"]\n    assert hover != pressed, (\n        f"{name}: the pressed plate is the hover plate, so a press changes "\n        f"only the label")\n    assert _lum(pressed) > _lum(hover), (\n        f"{name}: pressed plate {pressed} does not lift from hover {hover}")\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_label_inverts_on_press(name):\n    colors = DialogStyleManager.get_colors(THEMES[name])\n    resting, pressed = colors["button_text"], colors["button_pressed_text"]\n    assert (_lum(resting) > 0.5) != (_lum(pressed) > 0.5), (\n        f"{name}: {resting} -> {pressed} is not an inversion")\n\n\ndef _rule(css: str, selector: str) -> dict[str, str]:\n    match = re.search(re.escape(selector) + r"\\s*\\{([^}]*)\\}", css)\n    assert match, f"no {selector} rule in the rendered stylesheet"\n    return {k.strip(): v.strip()\n            for k, _, v in (d.partition(":") for d in match.group(1).split(";"))\n            if k.strip()}\n\n\ndef _button(qtbot, is_dark: bool):\n    from ui.image_button import ImageButton\n\n    colors = DialogStyleManager.get_colors(is_dark)\n\n    class _Stub:\n        def __init__(self, c): self.colors = c\n        def is_image_mode(self): return False\n\n    button = ImageButton("copy", "Export")\n    qtbot.addWidget(button)\n    button.theme_manager = _Stub(colors)\n    button.resize(180, 48)\n    button.apply_style()\n    return button, colors\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_pressed_rule_carries_the_ground_and_the_label(name, qtbot):\n    """The whole pressed appearance must live in one rule.\n\n    Splitting it -- ground from `:hover`, label from Python -- is what made a\n    keyboard press render white on white.\n    """\n    button, colors = _button(qtbot, THEMES[name])\n    rule = _rule(button.styleSheet(), "QPushButton:pressed")\n    assert rule.get("background-color") == colors["button_pressed_bg"], (\n        f"{name}: the pressed rule does not carry the pressed plate")\n    assert rule.get("color") == colors["button_pressed_text"], (\n        f"{name}: the pressed rule does not carry the pressed label, so the "\n        f"label depends on the Python path and any press without a hover "\n        f"renders it on the resting plate")\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_a_press_without_a_hover_is_still_legible(name, qtbot):\n    """The regression itself, rendered.\n\n    `setDown(True)` is the state keyboard activation puts the button in --\n    sunken, not hovered. Before the pressed rule existed this drew the flipped\n    label on the resting plate: 1.21:1 in dark, and white on white in light.\n    """\n    button, colors = _button(qtbot, THEMES[name])\n    button.show()\n    # Both halves of a real keyboard press: the app\'s own press handler runs\n    # (it flips the label in the base rule) and Qt sinks the button. What does\n    # NOT happen is a hover, and that was the load-bearing assumption.\n    button._on_press()\n    button.setDown(True)\n    button.style().unpolish(button)\n    button.style().polish(button)\n\n    pixmap = QPixmap(button.size())\n    pixmap.fill(Qt.GlobalColor.transparent)\n    button.render(pixmap)\n    image = pixmap.toImage()\n\n    seen = collections.Counter()\n    for y in range(6, button.height() - 6):\n        for x in range(6, button.width() - 6):\n            px = image.pixel(x, y)\n            seen[((px >> 16) & 255, (px >> 8) & 255, px & 255)] += 1\n    ordered = seen.most_common()\n    plate = ordered[0][0]\n    ink = next((c for c, _ in ordered[1:]\n                if abs(sum(c) - sum(plate)) > 90), None)\n    assert ink is not None, (\n        f"{name}: no label pixels distinguishable from the plate while the "\n        f"button is down -- the label is invisible")\n\n    as_hex = lambda c: "#%02x%02x%02x" % c\n    ratio = _contrast(as_hex(plate), as_hex(ink))\n    assert ratio > 2.0, (\n        f"{name}: label {as_hex(ink)} on plate {as_hex(plate)} = {ratio:.2f}:1 "\n        f"while down without a hover")\n'


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
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("press-step guard",
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
