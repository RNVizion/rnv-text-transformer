"""The coverage report stays in CI. Nothing here sends it to Codecov.

RNV-COVERAGE-STAYS-IN-CI, 2026-10-05.

WHAT WAS THERE. Each job ended with two steps more than it has now. One
wrote the coverage report out as coverage.xml. The other handed that file to
Codecov, through codecov/codecov-action@v4. Nothing else read the file.

WHAT HAPPENED. On 2026-10-05 Codecov's hosts were refusing TLS handshakes.
The upload step failed, and with it a job whose tests had all passed. The
step said `fail_ci_if_error: false`, and that did not help: version 4 of
the action reads the input only once it has downloaded its uploader, and it
was the download that was refused.

RULED 2026-10-05: "we should remove code cov it's not needed".

WHAT IS TRUE NOW. Both jobs end with `coverage report`, which prints the
figures into the job's own log. The XML step went with the upload, because
its file had no other reader, and so did the .gitignore entry for that file.

WHAT THIS GUARD HOLDS. The name does not come back, in any form: a workflow
step, a line of script that calls an uploader, a badge, a configuration
file, a requirement, a secret. It is a sweep for the word in every text file
of the repository and in every file's name, whatever the case. A comment
counts too: a comment that names a service is how the next step for it gets
written.

THIS FILE MENTIONS THE NAME in order to forbid it, and is the one file the
sweep leaves out: the use/mention distinction, as in
tests/test_dependency_file_placement.py. A delivery script is left out as
well, because it names what it retires. That means a .py file at the
repository root that carries the fleet's marker, and nothing else: three
guards under tests/ spell the marker out in order to honour it, and they are
source like any other.

WHAT IT DOES NOT HOLD. That coverage is measured. `coverage report` is a
step like any other, and CI fails if it does. This guard is about where the
report goes.
"""
from __future__ import annotations

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]

#: What may not come back, compared in lower case.
WORD = "codecov"

#: The one file that names it, to forbid it.
MENTION_ONLY = {pathlib.Path(__file__).name}

#: The fleet's delivery marker. A script at the repository root that carries
#: it is a tool, not source.
DELIVERY_MARK = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"

#: Directories that hold what a build, a run or a tool leaves behind.
SKIP_DIRS = {"build", "dist", "__pycache__", "venv", "env", "node_modules",
             "htmlcov", "coverage_html"}

#: A dot-directory is skipped (.git, .venv, a tool's cache) unless it is one
#: the repository writes in.
KEPT_DOT_DIRS = {".github"}

#: What the sweep must see, or it is not looking. Each named a coverage
#: service once, or is where one would be asked for.
MUST_SEE = (".github/workflows/tests.yml", ".gitignore", "README.md",
            "requirements.txt", "tests/requirements-dev.txt")

#: Fewer text files than this and the walk has gone blind. It read 118 on
#: the day this file was added, this file among them.
FLOOR = 50

#: What the sweep must flag, or it has stopped working: the line both jobs
#: used to carry, and a configuration file known by its name alone.
SAMPLE = ("sample.yml", "        uses: CodeCov/codecov-action@v4\n")
SAMPLE_NAME = (".codecov.yml", "coverage:\n  status: off\n")


def _skipped(path: pathlib.Path) -> bool:
    parts = path.relative_to(REPO).parts
    for part in parts[:-1]:
        if part in SKIP_DIRS:
            return True
        if part.startswith(".") and part not in KEPT_DOT_DIRS:
            return True
    return False


def _texts():
    """(repository-relative path, text) for every text file the sweep reads."""
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or _skipped(path):
            continue
        raw = path.read_bytes()
        if b"\x00" in raw:
            continue                                 # an image, an icon, a font
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        yield path.relative_to(REPO).as_posix(), text


def _is_delivery_script(rel: str, text: str) -> bool:
    return "/" not in rel and rel.endswith(".py") and DELIVERY_MARK in text


def _hits(pairs) -> list:
    """Every place the word is: a line of a file, or a file's own name."""
    found = []
    for rel, text in pairs:
        name = pathlib.PurePosixPath(rel).name
        if name in MENTION_ONLY or _is_delivery_script(rel, text):
            continue
        if WORD in rel.lower():
            found.append(f"{rel}: the file's name")
        for number, line in enumerate(text.splitlines(), 1):
            if WORD in line.lower():
                found.append(f"{rel}:{number}: {line.strip()}")
    return found


def test_nothing_in_the_repository_names_codecov():
    """Not a step, not a script line, not a badge, not a file."""
    hits = _hits(_texts())
    assert not hits, (
        "Codecov is named again:\n  " + "\n  ".join(hits)
        + "\n\nIt was removed on 2026-10-05, ruled as not needed, after its "
          "upload step failed a job whose tests had all passed. Both jobs "
          "print the coverage report into their own log. If it is wanted "
          "back, that is a new ruling, and this guard goes with it.")


def test_that_sweep_is_actually_looking():
    """A sweep that reads nothing, or matches nothing, passes the test above."""
    walked = {rel for rel, _text in _texts()}
    assert len(walked) > FLOOR, f"the sweep only found {len(walked)} text files"
    missing = [rel for rel in MUST_SEE if rel not in walked]
    assert not missing, f"the sweep is not reading {missing}"

    assert _hits([SAMPLE]), (
        "the sweep no longer flags the line the workflow used to carry: "
        f"{SAMPLE[1].strip()!r}")
    assert _hits([SAMPLE_NAME]), (
        f"the sweep no longer flags a file called {SAMPLE_NAME[0]}")


def test_the_mention_exemption_is_load_bearing():
    """Both directions. An exemption for a file that no longer names it is a
    licence waiting for a future defect."""
    here = pathlib.Path(__file__)
    assert MENTION_ONLY == {here.name}, (
        f"the sweep leaves out {sorted(MENTION_ONLY)}; it may leave out this "
        f"file alone")
    text = here.read_text(encoding="utf-8")
    assert _hits([("tests/another_name.py", text)]), (
        "this file no longer mentions the name: drop the exemption")
