"""remove the unused image_scrollbar_handle_hover key

    python up.py             # apply, then run the guard and CI's two commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (c58779d).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-25 (ruling 2): render it first, then remove it.
image_scrollbar_handle_hover held rgba(100, 100, 100, 200) in DARK and
LIGHT, and nothing read it. The render set it to #ff00ff, then deleted it:
neither changed a pixel in 159 captures of the main window and twelve
dialogs, in all three modes, sixty scrollbars under the pointer. A control
that changed DARK's 'accent' changed 65. The key goes from both dicts, its
two snapshot lines go, and the guard's unread pin becomes a gone pin.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-text-transformer'
SENTINEL = 'RNV-HOVER-KEY-GONE'
SENTINEL_FILE = 'tests/test_derived_values.py'
GUARD = 'tests/test_derived_values.py'
DESCRIPTION = 'remove the unused image_scrollbar_handle_hover key'
KEY = 'image_scrollbar_handle_hover'

#: EXACTLY WHAT CI RUNS, both steps, under coverage as the workflow does. The
#: first is the locked root suite, which `pytest tests/` never reaches.
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
    "LIGHT's other eight image keys. Image mode reads DARK, so nothing reads "
    "them either; they stay because the locked suite requires DARK and LIGHT "
    "to carry the same keys.",
    "scrollbar_handle_hover, the key without the image_ prefix. Nothing reads "
    "it either -- every scrollbar hover in this application reads 'accent' -- "
    "but the locked suite requires it in DARK and LIGHT, so it stays. LIGHT's "
    "holds #888888 while light mode paints #8c7337; a dead key, noted, not "
    "changed.",
    "with_alpha()'s spelling, '#BF1a1a1a'. Ruling 4 (eight-digit hex in lower "
    "case) is a round of its own.",
]

STYLES_OLD = "        # NOT CONSUMED -- the image scrollbar hovers from DARK's 'accent'.\n        # Left as written: #646464 is on no register row, so there is\n        # nothing to derive it from. See tests/test_derived_values.py.\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n"
STYLES_NEW = "        # The image scrollbar hovers from DARK's 'accent'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n"
AMBR_OLD = '    "image_scrollbar_handle_hover": "rgba(100, 100, 100, 200)",\n'


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('utils/dialog_styles.py',
             "        # NOT CONSUMED -- the image scrollbar hovers from DARK's 'accent'.\n        # Left as written: #646464 is on no register row, so there is\n        # nothing to derive it from. See tests/test_derived_values.py.\n        'image_scrollbar_handle_hover':'rgba(100, 100, 100, 200)',\n",
             "        # The image scrollbar hovers from DARK's 'accent'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n", times=2)
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "image_scrollbar_handle_hover": "rgba(100, 100, 100, 200)",\n',
             '', times=2)
    tree.sub('tests/test_derived_values.py',
             "AND ONE KEY THAT NOTHING READS, LEFT AS IT IS. image_scrollbar_handle_hover\nholds rgba(100, 100, 100, 200), a grey on no register row, while the image\nscrollbar's hover is painted from DARK's 'accent' -- BRAND_GOLD, ruled\n2026-09-12. It is not derived, because there is no row for it to follow; and\nit cannot simply take the painted gold, because LIGHT carries the same image\nkeys and a BRAND_GOLD there is a third gold in a mode the brand allows two.\nA test pins that nothing reads it.\n",
             "AND ONE KEY THAT NOTHING READ, REMOVED. image_scrollbar_handle_hover held\nrgba(100, 100, 100, 200), a grey on no register row, while the image\nscrollbar's hover is painted from DARK's 'accent' -- BRAND_GOLD, ruled\n2026-09-12. It could not be derived, having no row to follow, and it could\nnot take the painted gold, because LIGHT carries the same image keys and a\nBRAND_GOLD there is a third gold in a mode the brand allows two. Ruled\n2026-09-25: render it first, then remove it. A test pins that it stays gone.\n")
    tree.sub('tests/test_derived_values.py',
             'UNREAD = "image_scrollbar_handle_hover"\n',
             '#: Removed 2026-09-25 (RNV-HOVER-KEY-GONE). Named here only so the test\n#: below can say it is gone; tests/ is not application source.\nREMOVED = "image_scrollbar_handle_hover"\n')
    tree.sub('tests/test_derived_values.py',
             'def test_the_unread_hover_key_stays_unread():\n    """image_scrollbar_handle_hover is read by nothing: the image scrollbar\n    hovers from DARK\'s \'accent\', BRAND_GOLD, ruled 2026-09-12. It still holds\n    rgba(100, 100, 100, 200) -- a grey on no register row, left because there\n    is nothing to derive it from and the gold would be a third gold in LIGHT.\n\n    If anything starts reading it, this fails: the value would then be a grey\n    hover on screen, against the gold ruling, and it has to be decided rather\n    than inherited."""\n    assert DialogStyleManager.DARK["accent"] == colors.BRAND_GOLD\n    readers, keys = [], 0\n    for rel, tree in _sources():\n        # the dict KEYS that declare it are not reads; anything else is,\n        # including a lookup inside dialog_styles.py itself\n        declared = {id(k) for node in ast.walk(tree) if isinstance(node, ast.Dict)\n                    for k in node.keys if k is not None}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and node.value == UNREAD:\n                if id(node) in declared:\n                    keys += 1\n                else:\n                    readers.append(f"{rel}:{node.lineno}")\n    assert keys == 2, f"expected the key declared in DARK and LIGHT, found {keys}"\n    assert not readers, f"{UNREAD} is read now: {readers}"\n\n\n',
             'def test_the_unused_hover_key_stays_removed():\n    """RNV-HOVER-KEY-GONE, 2026-09-25. image_scrollbar_handle_hover painted\n    nothing. A render set it to #ff00ff, and then deleted it, and neither\n    changed one pixel across the main window and twelve dialogs in all three\n    modes, sixty scrollbars under the pointer among them. A control that\n    changed DARK\'s \'accent\' instead changed 65 of the same 159 captures. The\n    image scrollbar hovers from DARK\'s \'accent\', BRAND_GOLD.\n\n    Gone from both palettes and named nowhere in the application. A key\n    brought back would be a grey hover on no register row, against the gold\n    ruling, and it has to be decided rather than inherited."""\n    assert DialogStyleManager.DARK["accent"] == colors.BRAND_GOLD\n    for mode, palette in PALETTES.items():\n        assert REMOVED not in palette, f"{mode} declares {REMOVED} again"\n    sources = list(_sources())\n    assert any(rel.as_posix() == "utils/dialog_styles.py" for rel, _ in sources), (\n        "the sweep cannot see the palettes, so it proves nothing")\n    named = [f"{rel}:{node.lineno}" for rel, tree in sources\n             for node in ast.walk(tree)\n             if isinstance(node, ast.Constant) and node.value == REMOVED]\n    assert not named, f"{REMOVED} is named again: {named}"\n\n\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _palettes(src: str) -> dict:
    """DARK and LIGHT as (key -> ast.dump of the value), from the class body."""
    cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef)
               and n.name == "DialogStyleManager")
    out = {}
    for node in cls.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None) in ("DARK", "LIGHT") and isinstance(node.value, ast.Dict):
                out[t.id] = {k.value: ast.dump(v) for k, v in zip(node.value.keys, node.value.values)}
    return out


def _snapshot_json(ambr: str) -> list:
    """Every JSON object in the snapshot file that carries image_ keys."""
    docs = []
    for block in ambr.split("# name: ")[1:]:
        body = block.split("\n", 1)[1]
        if '"image_scrollbar_handle"' not in body:
            continue
        inner = body.split("\'\'\'", 2)[1]
        text = "\n".join(line[2:] if line.startswith("  ") else line
                         for line in inner.strip("\n").splitlines())
        docs.append(json.loads(text))
    return docs


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    old_styles, new_styles = _original(tree, 'utils/dialog_styles.py'), tree.read('utils/dialog_styles.py')
    before, after = _palettes(old_styles), _palettes(new_styles)
    assert set(before) == set(after) == {"DARK", "LIGHT"}
    for mode in ("DARK", "LIGHT"):
        assert KEY in before[mode], f"{mode} never had {KEY}"
        assert KEY not in after[mode], f"{mode} still has {KEY}"
        # every other key keeps its value, to the AST
        assert after[mode] == {k: v for k, v in before[mode].items() if k != KEY}, mode
    assert set(after["DARK"]) == set(after["LIGHT"]), "the two key sets differ"
    assert new_styles == old_styles.replace(STYLES_OLD, STYLES_NEW), (
        "utils/dialog_styles.py changed outside the two blocks")

    # the snapshots: two lines gone, and the JSON they sat in still parses
    old_ambr, new_ambr = _original(tree, 'tests/__snapshots__/test_snapshots.ambr'), tree.read('tests/__snapshots__/test_snapshots.ambr')
    assert new_ambr == old_ambr.replace(AMBR_OLD, ""), "the snapshot moved elsewhere"
    old_docs, new_docs = _snapshot_json(old_ambr), _snapshot_json(new_ambr)
    assert len(old_docs) == len(new_docs) == 2, (len(old_docs), len(new_docs))
    for was, now in zip(old_docs, new_docs):
        assert KEY not in now
        assert now == {k: v for k, v in was.items() if k != KEY}

    # the guard: the unread pin is replaced by the gone pin, and parses
    guard = tree.read('tests/test_derived_values.py')
    ast.parse(guard)
    assert "def test_the_unused_hover_key_stays_removed" in guard
    assert "UNREAD" not in guard and "stays_unread" not in guard
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
