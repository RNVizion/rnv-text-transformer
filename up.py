"""Codecov out of the text transformer's CI: each job ends with its coverage report, and sends it nowhere

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (0faaa77).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-05, item 15 of decisions-pending-2026-10-04.md:

  "For 15 we should remove code cov it's not needed"

WHAT GOES. Each job of the workflow ended with two steps more than it needs.
One wrote the coverage report out as coverage.xml; the other handed that
file to Codecov. Both go, in both jobs. Nothing else read the file, so the
.gitignore entry for it goes too.

WHAT STAYS. Every other step, as it was. Both suites run under coverage, the
data is combined, and `coverage report` prints the figures into the job's
log.

WHY NOW. On 2026-10-05 Codecov's hosts were refusing connections, and the
upload step failed a job whose tests had all passed. That job's log also
shows the step was given no token.

THE GUARD. tests/test_coverage_stays_in_ci.py keeps the name out of the
repository: every text file and every file name, whatever the case. This
script runs it on the checkout as it is and as it will be before it writes
anything: nine lines named, then none.

THIS REPLACES up_tt_coverage_upload.py, sent earlier the same day and
withdrawn before it was run: it kept the upload. If that script was applied
here anyway, this one takes it back out first. Either way in, the result is
the same tree.

No file the application runs is touched.
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
SENTINEL = 'RNV-COVERAGE-STAYS-IN-CI'
SENTINEL_FILE = '.github/workflows/tests.yml'
GUARD = 'tests/test_coverage_stays_in_ci.py'
GUARD_FILES = ['tests/test_coverage_stays_in_ci.py']
WORKFLOW = '.github/workflows/tests.yml'

#: up_tt_coverage_upload.py was sent on 2026-10-05, kept the upload, and was
#: withdrawn the same day. Where it was applied anyway, this script takes it
#: back out first: for the workflow, each (what it wrote, what stood there
#: before), and the guard it added.
EARLIER_SENTINEL = 'RNV-COVERAGE-UPLOAD'
EARLIER_GUARD = 'tests/test_coverage_upload.py'
EARLIER_UNDO = [("      # RNV-COVERAGE-UPLOAD, 2026-10-05. Every test has passed by the time this\n      # step runs, so nothing it does may fail the job.\n      #   continue-on-error  a failed upload is not a failed job.\n      #                      fail_ci_if_error does not see to that alone:\n      #                      codecov-action@v4 reads it only once it has\n      #                      its uploader, and exits 1 when the download\n      #                      is refused.\n      #   timeout-minutes    a stalled upload is stopped here. Left to the\n      #                      job's own limit it would get the job cancelled.\n      # tests/test_coverage_upload.py holds both, and holds that no other\n      # step carries continue-on-error.\n      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        continue-on-error: true\n        timeout-minutes: 5\n        with:\n          files: ./coverage.xml\n          flags: linux\n", '      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        with:\n          files: ./coverage.xml\n          flags: linux\n'), ('      # RNV-COVERAGE-UPLOAD: as in the Linux job. The upload may fail or stall;\n      # the job may not fail because of it.\n      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        continue-on-error: true\n        timeout-minutes: 5\n        with:\n          files: ./coverage.xml\n          flags: windows\n', '      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        with:\n          files: ./coverage.xml\n          flags: windows\n')]


def _without_the_earlier_script(text: str) -> str:
    """The workflow as the live head has it, whether or not the withdrawn
    script was applied to it."""
    if EARLIER_SENTINEL not in text:
        return text
    for wrote, stood in EARLIER_UNDO:
        if text.count(wrote) != 1:
            first = wrote.splitlines()[0].strip()
            raise Stop(
                f"{WORKFLOW} carries up_tt_coverage_upload.py's marker, and what that "
                f"script wrote is not there as it wrote it ({first!r} is found "
                f"{text.count(wrote)} times).\nThe workflow was edited after it ran, so "
                f"this script cannot take it back out. Nothing was written.",
                EXIT_CANNOT_RUN)
        text = text.replace(wrote, stood)
    if EARLIER_SENTINEL in text:
        raise Stop(
            f"{WORKFLOW} still carries {EARLIER_SENTINEL!r} after up_tt_coverage_upload.py "
            f"was taken back out. Nothing was written.", EXIT_CANNOT_RUN)
    return text

#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_coverage_stays_in_ci.py']
DESCRIPTION = "Codecov out of the text transformer's CI: each job ends with its coverage report, and sends it nowhere"

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

SHADOWS = {"conftest.py", "test_coverage_stays_in_ci.py", "test_coverage_upload.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ['coverage is still measured and printed: both suites run under coverage, the data is combined, and `coverage report` ends each job. Only the two steps that made and sent the XML go.', 'a copy of the coverage kept with each run: the other four applications upload their coverage data or an HTML report as an artifact of the run (the mixer from its Linux job only). Not added here: it was not ruled.', "the workflow's other actions, actions/checkout@v4 and actions/setup-python@v5: built for Node 20, which GitHub removed from its runners on 2026-09-23. They run on Node 24 with a warning. Item 14 on the list of open decisions.", "the repository's settings on GitHub and the account at the coverage service: a script cannot reach either. The workflow no longer names the token secret; the run of 2026-10-05 was given none."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # THE WITHDRAWN SCRIPT. If up_tt_coverage_upload.py was applied here, take
    # it back out before anything else, so that both ways in end at one tree.
    if EARLIER_SENTINEL in tree.read(WORKFLOW):
        print("up_tt_coverage_upload.py was applied here. This script replaces it, "
              "and takes it back out first.\n")
        tree.write(WORKFLOW, _without_the_earlier_script(tree.read(WORKFLOW)))
        tree.delete(EARLIER_GUARD)
    elif (tree.root / EARLIER_GUARD).exists():
        raise Stop(
            f"{EARLIER_GUARD} is here and {WORKFLOW} does not carry the marker of the "
            f"script that adds it.\nThat is half of up_tt_coverage_upload.py, which "
            f"this script cannot take back out. Nothing was written.", EXIT_CANNOT_RUN)
    tree.sub('.github/workflows/tests.yml',
             '      - name: Generate coverage XML (for Codecov)\n        run: |\n          coverage xml -o coverage.xml\n\n      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        with:\n          files: ./coverage.xml\n          flags: linux\n          fail_ci_if_error: false\n          token: ${{ secrets.CODECOV_TOKEN }}\n',
             '      # RNV-COVERAGE-STAYS-IN-CI, 2026-10-05. The job ends with the report above.\n      # It used to hand a copy to an outside coverage service as well. On\n      # 2026-10-05 that service refused connections, and the step that\n      # called it failed a job whose tests had all passed. It was ruled out\n      # the same day as not needed. tests/test_coverage_stays_in_ci.py keeps\n      # it out.\n')
    tree.sub('.github/workflows/tests.yml',
             '      - name: Generate coverage XML (for Codecov)\n        run: |\n          coverage xml -o coverage.xml\n\n      - name: Upload coverage to Codecov\n        uses: codecov/codecov-action@v4\n        with:\n          files: ./coverage.xml\n          flags: windows\n          fail_ci_if_error: false\n          token: ${{ secrets.CODECOV_TOKEN }}\n',
             '      # RNV-COVERAGE-STAYS-IN-CI: as in the Linux job. The job ends with the\n      # report above.\n')
    tree.sub('.gitignore',
             'coverage_report.txt\n\n# CI-generated coverage XML uploaded to Codecov\ncoverage.xml\n\n',
             'coverage_report.txt\n\n')
    if (tree.root / 'tests/test_coverage_stays_in_ci.py').exists():
        raise Stop('tests/test_coverage_stays_in_ci.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_coverage_stays_in_ci.py', '"""The coverage report stays in CI. Nothing here sends it to Codecov.\n\nRNV-COVERAGE-STAYS-IN-CI, 2026-10-05.\n\nWHAT WAS THERE. Each job ended with two steps more than it has now. One\nwrote the coverage report out as coverage.xml. The other handed that file to\nCodecov, through codecov/codecov-action@v4. Nothing else read the file.\n\nWHAT HAPPENED. On 2026-10-05 Codecov\'s hosts were refusing TLS handshakes.\nThe upload step failed, and with it a job whose tests had all passed. The\nstep said `fail_ci_if_error: false`, and that did not help: version 4 of\nthe action reads the input only once it has downloaded its uploader, and it\nwas the download that was refused.\n\nRULED 2026-10-05: "we should remove code cov it\'s not needed".\n\nWHAT IS TRUE NOW. Both jobs end with `coverage report`, which prints the\nfigures into the job\'s own log. The XML step went with the upload, because\nits file had no other reader, and so did the .gitignore entry for that file.\n\nWHAT THIS GUARD HOLDS. The name does not come back, in any form: a workflow\nstep, a line of script that calls an uploader, a badge, a configuration\nfile, a requirement, a secret. It is a sweep for the word in every text file\nof the repository and in every file\'s name, whatever the case. A comment\ncounts too: a comment that names a service is how the next step for it gets\nwritten.\n\nTHIS FILE MENTIONS THE NAME in order to forbid it, and is the one file the\nsweep leaves out: the use/mention distinction, as in\ntests/test_dependency_file_placement.py. A delivery script is left out as\nwell, because it names what it retires. That means a .py file at the\nrepository root that carries the fleet\'s marker, and nothing else: three\nguards under tests/ spell the marker out in order to honour it, and they are\nsource like any other.\n\nWHAT IT DOES NOT HOLD. That coverage is measured. `coverage report` is a\nstep like any other, and CI fails if it does. This guard is about where the\nreport goes.\n"""\nfrom __future__ import annotations\n\nimport pathlib\n\nREPO = pathlib.Path(__file__).resolve().parents[1]\n\n#: What may not come back, compared in lower case.\nWORD = "codecov"\n\n#: The one file that names it, to forbid it.\nMENTION_ONLY = {pathlib.Path(__file__).name}\n\n#: The fleet\'s delivery marker. A script at the repository root that carries\n#: it is a tool, not source.\nDELIVERY_MARK = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"\n\n#: Directories that hold what a build, a run or a tool leaves behind.\nSKIP_DIRS = {"build", "dist", "__pycache__", "venv", "env", "node_modules",\n             "htmlcov", "coverage_html"}\n\n#: A dot-directory is skipped (.git, .venv, a tool\'s cache) unless it is one\n#: the repository writes in.\nKEPT_DOT_DIRS = {".github"}\n\n#: What the sweep must see, or it is not looking. Each named a coverage\n#: service once, or is where one would be asked for.\nMUST_SEE = (".github/workflows/tests.yml", ".gitignore", "README.md",\n            "requirements.txt", "tests/requirements-dev.txt")\n\n#: Fewer text files than this and the walk has gone blind. It read 118 on\n#: the day this file was added, this file among them.\nFLOOR = 50\n\n#: What the sweep must flag, or it has stopped working: the line both jobs\n#: used to carry, and a configuration file known by its name alone.\nSAMPLE = ("sample.yml", "        uses: CodeCov/codecov-action@v4\\n")\nSAMPLE_NAME = (".codecov.yml", "coverage:\\n  status: off\\n")\n\n\ndef _skipped(path: pathlib.Path) -> bool:\n    parts = path.relative_to(REPO).parts\n    for part in parts[:-1]:\n        if part in SKIP_DIRS:\n            return True\n        if part.startswith(".") and part not in KEPT_DOT_DIRS:\n            return True\n    return False\n\n\ndef _texts():\n    """(repository-relative path, text) for every text file the sweep reads."""\n    for path in sorted(REPO.rglob("*")):\n        if not path.is_file() or _skipped(path):\n            continue\n        raw = path.read_bytes()\n        if b"\\x00" in raw:\n            continue                                 # an image, an icon, a font\n        try:\n            text = raw.decode("utf-8-sig")\n        except UnicodeDecodeError:\n            continue\n        yield path.relative_to(REPO).as_posix(), text\n\n\ndef _is_delivery_script(rel: str, text: str) -> bool:\n    return "/" not in rel and rel.endswith(".py") and DELIVERY_MARK in text\n\n\ndef _hits(pairs) -> list:\n    """Every place the word is: a line of a file, or a file\'s own name."""\n    found = []\n    for rel, text in pairs:\n        name = pathlib.PurePosixPath(rel).name\n        if name in MENTION_ONLY or _is_delivery_script(rel, text):\n            continue\n        if WORD in rel.lower():\n            found.append(f"{rel}: the file\'s name")\n        for number, line in enumerate(text.splitlines(), 1):\n            if WORD in line.lower():\n                found.append(f"{rel}:{number}: {line.strip()}")\n    return found\n\n\ndef test_nothing_in_the_repository_names_codecov():\n    """Not a step, not a script line, not a badge, not a file."""\n    hits = _hits(_texts())\n    assert not hits, (\n        "Codecov is named again:\\n  " + "\\n  ".join(hits)\n        + "\\n\\nIt was removed on 2026-10-05, ruled as not needed, after its "\n          "upload step failed a job whose tests had all passed. Both jobs "\n          "print the coverage report into their own log. If it is wanted "\n          "back, that is a new ruling, and this guard goes with it.")\n\n\ndef test_that_sweep_is_actually_looking():\n    """A sweep that reads nothing, or matches nothing, passes the test above."""\n    walked = {rel for rel, _text in _texts()}\n    assert len(walked) > FLOOR, f"the sweep only found {len(walked)} text files"\n    missing = [rel for rel in MUST_SEE if rel not in walked]\n    assert not missing, f"the sweep is not reading {missing}"\n\n    assert _hits([SAMPLE]), (\n        "the sweep no longer flags the line the workflow used to carry: "\n        f"{SAMPLE[1].strip()!r}")\n    assert _hits([SAMPLE_NAME]), (\n        f"the sweep no longer flags a file called {SAMPLE_NAME[0]}")\n\n\ndef test_the_mention_exemption_is_load_bearing():\n    """Both directions. An exemption for a file that no longer names it is a\n    licence waiting for a future defect."""\n    here = pathlib.Path(__file__)\n    assert MENTION_ONLY == {here.name}, (\n        f"the sweep leaves out {sorted(MENTION_ONLY)}; it may leave out this "\n        f"file alone")\n    text = here.read_text(encoding="utf-8")\n    assert _hits([("tests/another_name.py", text)]), (\n        "this file no longer mentions the name: drop the exemption")\n')


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
    import collections
    WF, IGNORE = WORKFLOW, ".gitignore"
    GONE = ['      - name: Generate coverage XML (for Codecov)', '        run: |', '          coverage xml -o coverage.xml', '      - name: Upload coverage to Codecov', '        uses: codecov/codecov-action@v4', '        with:', '          files: ./coverage.xml', '          flags: linux', '          fail_ci_if_error: false', '          token: ${{ secrets.CODECOV_TOKEN }}', '      - name: Generate coverage XML (for Codecov)', '        run: |', '          coverage xml -o coverage.xml', '      - name: Upload coverage to Codecov', '        uses: codecov/codecov-action@v4', '        with:', '          files: ./coverage.xml', '          flags: windows', '          fail_ci_if_error: false', '          token: ${{ secrets.CODECOV_TOKEN }}']
    IGNORE_GONE = ['# CI-generated coverage XML uploaded to Codecov', 'coverage.xml']
    NOTES = ['      # RNV-COVERAGE-STAYS-IN-CI, 2026-10-05. The job ends with the report above.\n      # It used to hand a copy to an outside coverage service as well. On\n      # 2026-10-05 that service refused connections, and the step that\n      # called it failed a job whose tests had all passed. It was ruled out\n      # the same day as not needed. tests/test_coverage_stays_in_ci.py keeps\n      # it out.\n', '      # RNV-COVERAGE-STAYS-IN-CI: as in the Linux job. The job ends with the\n      # report above.\n']
    STAYS = [('coverage run --data-file=.coverage.unittest --source=core,utils,ui,cli --branch -m unittest test_rnv_text_transformer\n', 2), ('coverage run --data-file=.coverage.pytest --source=core,utils,ui,cli --branch -m pytest tests/ --benchmark-disable\n', 2), ('          coverage combine .coverage.unittest .coverage.pytest\n', 2), ('          coverage report\n', 2)]
    KNOWN = ['.github/workflows/tests.yml:83: - name: Generate coverage XML (for Codecov)', '.github/workflows/tests.yml:87: - name: Upload coverage to Codecov', '.github/workflows/tests.yml:88: uses: codecov/codecov-action@v4', '.github/workflows/tests.yml:93: token: ${{ secrets.CODECOV_TOKEN }}', '.github/workflows/tests.yml:139: - name: Generate coverage XML (for Codecov)', '.github/workflows/tests.yml:143: - name: Upload coverage to Codecov', '.github/workflows/tests.yml:144: uses: codecov/codecov-action@v4', '.github/workflows/tests.yml:149: token: ${{ secrets.CODECOV_TOKEN }}', '.gitignore:69: # CI-generated coverage XML uploaded to Codecov']
    TESTS = ['test_nothing_in_the_repository_names_codecov', 'test_that_sweep_is_actually_looking', 'test_the_mention_exemption_is_load_bearing']
    on_disk = _original(tree, WF)
    was, now = _without_the_earlier_script(on_disk), tree.read(WF)
    earlier_applied = on_disk != was
    if earlier_applied:
        assert EARLIER_GUARD in tree.deleted, f"{EARLIER_GUARD} is not marked for removal"

    def minus(longer, shorter, what):
        """What `longer` has and `shorter` has not, where `shorter` must be
        `longer` with lines taken out: nothing added, nothing moved."""
        rest = iter(longer)
        for line in shorter:
            if not any(line == other for other in rest):
                raise AssertionError(f"{what}: a line arrived or moved: {line.strip()!r}")
        left = collections.Counter(longer)
        left.subtract(shorter)
        return sorted(left.elements())

    def code(text):
        return [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]

    def comments(text):
        return [ln for ln in text.splitlines() if ln.lstrip().startswith("#")]

    # ---- the workflow: the twenty lines that made and sent the XML go, and nothing else does
    gone = minus(code(was), code(now), WF)
    assert gone == sorted(GONE), f"{WF}: moved by other than the four steps: {gone}"
    assert len(gone) == 20, f"{WF}: loses {len(gone)} lines of code, not 20"
    arrived = minus(comments(now), comments(was), WF)
    assert arrived == sorted(ln for note in NOTES for ln in note.splitlines()), \
        f"{WF}: its comments moved by other than the two notes: {arrived}"
    for text, times in STAYS:
        assert now.count(text) == times, \
            f"{WF}: {text.strip()!r} is written {now.count(text)} times, not {times}"

    # ---- the ignore file: the entry for the XML and its comment go
    was_i, now_i = _original(tree, IGNORE), tree.read(IGNORE)
    gone_i = minus([ln for ln in was_i.splitlines() if ln.strip()],
                   [ln for ln in now_i.splitlines() if ln.strip()], IGNORE)
    assert gone_i == sorted(IGNORE_GONE), f"{IGNORE}: moved by other than the two lines: {gone_i}"
    assert len(gone_i) == 2, f"{IGNORE}: loses {len(gone_i)} lines, not 2"

    # ---- the guard this script carries, loaded as it will be written
    guard = dict(__name__="coverage_stays_guard", __file__=str(tree.root / GUARD))
    exec(compile(tree.read(GUARD), GUARD, "exec"), guard)
    found = [n.name for n in ast.walk(ast.parse(tree.read(GUARD)))
             if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert found == TESTS, f"{GUARD}: its tests are {found}"
    assert guard["MENTION_ONLY"] == set([Path(GUARD).name]), \
        f"{GUARD} leaves out {sorted(guard['MENTION_ONLY'])}, not itself alone"
    assert guard["_hits"]([guard["SAMPLE"]]) and guard["_hits"]([guard["SAMPLE_NAME"]]), \
        f"{GUARD} does not flag its own samples"

    # ---- that guard on this checkout: as the live head has it, and as it will be written
    before = dict(guard["_texts"]())
    unread = [m for m in guard["MUST_SEE"] if m not in before]
    assert len(before) > guard["FLOOR"] and not unread, \
        f"the guard reads {len(before)} files here and not {unread}: it would not be looking"
    before[WF] = was
    if earlier_applied:
        before.pop(EARLIER_GUARD, None)
    after = dict(before)
    after[WF], after[IGNORE], after[GUARD] = now, now_i, tree.read(GUARD)
    named = guard["_hits"](sorted(before.items()))
    assert named == KNOWN, \
        f"the guard names {named} on this checkout, not the nine lines this round removes"
    still = guard["_hits"](sorted(after.items()))
    assert still == [], f"this checkout would still name it after the round: {still}"
    assert SENTINEL in now and SENTINEL in tree.read(GUARD), "the sentinel is not in the workflow and its guard"
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
