"""
Unified test runner for RNV Text Transformer.

Runs both test sources under coverage with branch analysis, then merges
the data files into a single coverage report.

  Suite 1 — test_rnv_text_transformer.py    (398 unittest tests)
  Suite 2 — tests/                           (pytest-qt interaction tests)

Usage:
    python run_tests.py              # run everything, merge, show report
    python run_tests.py --report     # regenerate report from existing data
    python run_tests.py --summary    # report with --skip-covered (gaps only)
    python run_tests.py --no-merge   # debug: don't combine, leave both .coverage.* files
    python run_tests.py --benchmark  # ONLY run the Phase 6 benchmarks (no coverage)

Exit code is non-zero if either suite has failures.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Coverage source folders. RNV_Capitalizer_App.py (GUI entry point) is
# intentionally excluded until Phase 3 lands tests for it — adding it now
# would just inflate the denominator and make our progress numbers look
# worse than they are.
COVERAGE_SOURCE = "--source=core,utils,ui,cli"
COVERAGE_BRANCH = "--branch"

# Data file names so the two suites don't overwrite each other before merge.
UNITTEST_DATA = ".coverage.unittest"
PYTEST_DATA = ".coverage.pytest"


def _run(label, cmd):
    """Run a subprocess, stream its output, return its exit code."""
    print()
    print("=" * 72)
    print(f"  {label}")
    print("=" * 72)
    print(f"  $ {' '.join(cmd)}")
    print()
    return subprocess.call(cmd, cwd=ROOT)


def run_unittest_suite():
    return _run(
        "Suite 1 / 2 — unittest (test_rnv_text_transformer.py)",
        ["coverage", "run",
         f"--data-file={UNITTEST_DATA}",
         COVERAGE_SOURCE,
         COVERAGE_BRANCH,
         "-m", "unittest", "test_rnv_text_transformer"],
    )


def run_pytest_suite():
    if not (ROOT / "tests").is_dir():
        print("\n[skip] tests/ directory not found — pytest suite skipped.")
        return 0
    return _run(
        "Suite 2 / 2 — pytest (tests/)",
        ["coverage", "run",
         f"--data-file={PYTEST_DATA}",
         COVERAGE_SOURCE,
         COVERAGE_BRANCH,
         "-m", "pytest", "tests/", "-v",
         "--benchmark-disable"],  # exclude benchmarks from default run
    )


def run_benchmark_suite():
    """Run ONLY the Phase 6 benchmarks. No coverage measurement — benchmarks
    don't move % and the coverage tracer adds noise to timing data."""
    if not (ROOT / "tests" / "test_benchmarks.py").is_file():
        print("\n[skip] tests/test_benchmarks.py not found — benchmark suite skipped.")
        return 0
    return _run(
        "Phase 6 — benchmarks only (no coverage)",
        [sys.executable, "-m", "pytest",
         "tests/test_benchmarks.py",
         "--benchmark-only", "-v"],
    )


def merge_data_files():
    """Combine the two per-suite .coverage.* files into the canonical .coverage."""
    parts = [p for p in (UNITTEST_DATA, PYTEST_DATA) if (ROOT / p).exists()]
    if not parts:
        print("\n[error] no coverage data files found — cannot merge.")
        return 1
    # `coverage combine` deletes input files after a successful merge, so
    # the canonical .coverage ends up with the union of both runs.
    return subprocess.call(["coverage", "combine", *parts], cwd=ROOT)


def print_report(summary=False):
    """Print the combined coverage report. `summary=True` hides 100%-covered files."""
    print()
    print("=" * 72)
    print("  Coverage report" + ("  (--skip-covered)" if summary else ""))
    print("=" * 72)
    cmd = ["coverage", "report", "-m"]
    if summary:
        cmd.append("--skip-covered")
    rc = subprocess.call(cmd, cwd=ROOT)
    # Always also write the full report to disk for archiving.
    with open(ROOT / "coverage_report.txt", "w", encoding="utf-8") as f:
        subprocess.call(["coverage", "report", "-m"], cwd=ROOT, stdout=f)
    return rc


def main():
    args = set(sys.argv[1:])
    summary = "--summary" in args

    # Benchmark-only mode: skip both correctness suites, run benchmarks alone.
    # Mutually exclusive with the default run — benchmarks have their own
    # output format and coverage tracing skews timing.
    if "--benchmark" in args:
        return run_benchmark_suite()

    # Report-only mode: skip both suites, just regenerate from existing data.
    if "--report" in args:
        return print_report(summary=summary)

    rc1 = run_unittest_suite()
    rc2 = run_pytest_suite()

    if "--no-merge" not in args:
        merge_data_files()
        print_report(summary=summary)

    # Non-zero exit if either suite failed — useful for CI gates.
    return max(rc1, rc2)


if __name__ == "__main__":
    sys.exit(main())
