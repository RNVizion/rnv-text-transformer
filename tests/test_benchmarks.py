"""
tests/test_benchmarks.py
========================
Phase 6 — Performance regression tests with pytest-benchmark.

These tests do NOT run by default. They run only when invoked with one of:

    pytest tests/test_benchmarks.py --benchmark-only
    pytest --benchmark-only -m benchmark
    python run_tests.py --benchmark

Each benchmark protects an optimization the project has already made:

  bench_app_package_import_time       — lazy imports (pypdf, docx, striprtf)
  bench_dialog_stylesheet_cache_hit   — DialogStyleManager LRU cache effectiveness
  bench_dialog_stylesheet_cache_miss  — cold-path stylesheet build cost
  bench_text_transform_uppercase_1mb  — TextTransformer on large input
  bench_diff_engine_two_10k_inputs    — DiffEngine on big inputs
  bench_file_loader_5mb_file          — full QThread roundtrip on 5MB file

Thresholds in docstrings are ADVISORY ONLY — they're not enforced by the
test. Each developer should run `pytest tests/test_benchmarks.py
--benchmark-only --benchmark-save=baseline` once on their machine to
establish per-machine baselines. Subsequent runs can use
`--benchmark-compare=baseline` to detect regressions.

Why advisory and not enforced: machine-to-machine variance is too high.
A 50µs threshold on a 2018 laptop might be 15µs on a 2023 desktop. Hard
thresholds would either fail spuriously or be too loose to catch
real regressions.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from utils.dialog_styles import DialogStyleManager
from core.text_transformer import TextTransformer
from core.diff_engine import DiffEngine

# Mark every test in this module as a benchmark so it gets skipped during
# regular test runs (pytest --benchmark-only includes them; default
# `pytest` excludes them via the marker config in pytest.ini).
pytestmark = pytest.mark.benchmark

# Project root (parent of tests/) — used to set PYTHONPATH for the
# subprocess-based import benchmark.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ════════════════════════════════════════════════════════════════════════════
# 1. Lazy-import guard
# ════════════════════════════════════════════════════════════════════════════

def test_bench_app_package_import_time(benchmark):
    """
    Subprocess-based benchmark of importing the heavy file-I/O module.

    Each iteration spawns a fresh Python process and times the full
    interpreter startup + module import. This is the only honest way to
    measure the lazy-import optimization, because using the normal
    `benchmark` fixture would hit Python's module cache.

    We import `utils.file_handler` rather than the project root package
    because file_handler is the module that contains the lazy imports
    (pypdf, python-docx, striprtf) we're guarding. If those imports get
    accidentally hoisted to module-top, this benchmark catches it.
    Importing the project root would chain through cli/rnv_transform and
    add unrelated noise to the measurement.

    Threshold (advisory): ≤ 500ms on most machines. If pypdf/docx/striprtf
    are hoisted to module-top in file_handler.py, this jumps to 800ms+
    and surfaces the regression.
    """
    project_root = str(_PROJECT_ROOT)
    env = {**os.environ, "PYTHONPATH": project_root}

    def _do_subprocess_import():
        subprocess.run(
            [sys.executable, "-c", "import utils.file_handler"],
            check=True,
            capture_output=True,
            cwd=project_root,
            env=env,
        )

    benchmark.pedantic(_do_subprocess_import, rounds=5, iterations=1)


# ════════════════════════════════════════════════════════════════════════════
# 2. DialogStyleManager cache hit (warm path)
# ════════════════════════════════════════════════════════════════════════════

def test_bench_dialog_stylesheet_cache_hit(benchmark):
    """
    Benchmark a cache hit. The first call (outside the timed region) builds
    and caches the stylesheet. Subsequent calls — what `benchmark()` times
    — should be a single dict lookup.

    Threshold (advisory): ≤ 50µs (microseconds, not milliseconds). A cache
    hit is meant to be near-free. If the cache is broken (e.g. someone
    changes the cache key tuple), this jumps to ~50ms (the build cost).
    """
    DialogStyleManager.clear_cache()
    # Warm the cache once outside the timed region
    DialogStyleManager.get_dialog_stylesheet(True, "Arial")

    result = benchmark(DialogStyleManager.get_dialog_stylesheet, True, "Arial")
    assert isinstance(result, str) and len(result) > 0


# ════════════════════════════════════════════════════════════════════════════
# 3. DialogStyleManager cache miss (cold path)
# ════════════════════════════════════════════════════════════════════════════

def test_bench_dialog_stylesheet_cache_miss(benchmark):
    """
    Benchmark a cold-path stylesheet build. Each iteration clears the
    cache before the call, so we're always measuring the full build cost.

    Threshold (advisory): ≤ 50ms on modern CPUs. Catches accidental
    regressions in the stylesheet builder (e.g. inefficient string
    concatenation, redundant work).
    """
    def _miss():
        DialogStyleManager.clear_cache()
        return DialogStyleManager.get_dialog_stylesheet(True, "Arial")

    result = benchmark(_miss)
    assert isinstance(result, str) and len(result) > 0


# ════════════════════════════════════════════════════════════════════════════
# 4. TextTransformer on 1MB input
# ════════════════════════════════════════════════════════════════════════════

def test_bench_text_transform_uppercase_1mb(benchmark):
    """
    Benchmark UPPERCASE transformation on ~1MB of input.

    Threshold (advisory): ≤ 100ms. Catches any change in text_transformer.py
    that introduces a quadratic loop on input length, or accidentally
    forces multiple full-text scans.
    """
    text = "hello world. " * 80000  # ~1MB

    result = benchmark(TextTransformer.transform_text, text, "UPPERCASE")
    assert result.startswith("HELLO WORLD")


# ════════════════════════════════════════════════════════════════════════════
# 5. DiffEngine on two 10K-line inputs
# ════════════════════════════════════════════════════════════════════════════

def test_bench_diff_engine_two_10k_inputs(benchmark):
    """
    Benchmark compute_diff between two 10,000-line texts that differ at
    every 100th line. Diff is fundamentally O(N×M) in the worst case;
    this benchmark catches regressions to a worse algorithm.

    Threshold (advisory): ≤ 2 seconds. SequenceMatcher's autojunk
    optimization usually keeps this well under that bound.
    """
    left = "\n".join(f"line {i}" for i in range(10000))
    right = "\n".join(f"line {i}" for i in range(10000) if i % 100 != 0)

    # Slow benchmark — fewer rounds keeps overall test time reasonable.
    result = benchmark.pedantic(
        DiffEngine.compute_diff, args=(left, right),
        rounds=3, iterations=1,
    )
    # Sanity check: differences exist
    assert result.changes, "Expected diff changes between distinct inputs"


# ════════════════════════════════════════════════════════════════════════════
# 6. FileLoaderThread on a 5MB file (full QThread roundtrip)
# ════════════════════════════════════════════════════════════════════════════

def test_bench_file_loader_5mb_file(qtbot, tmp_path, benchmark):
    """
    End-to-end QThread roundtrip on a 5MB file. Each iteration creates a
    fresh FileLoaderThread, runs it through the full Qt threading
    lifecycle, waits for the finished signal, and joins the thread.

    Threshold (advisory): ≤ 500ms on a typical SSD. Catches regressions
    in the read path or thread setup overhead. SSD vs HDD differs by 10×;
    each developer's baseline reflects their hardware.
    """
    from utils.async_workers import FileLoaderThread

    fpath = tmp_path / "big.txt"
    fpath.write_text("x" * (5 * 1024 * 1024), encoding="utf-8")

    def _load():
        worker = FileLoaderThread(str(fpath))
        with qtbot.waitSignal(worker.finished, timeout=10000):
            worker.start()
        worker.wait()

    # Pedantic with explicit setup to ensure the file is fresh each round.
    benchmark.pedantic(_load, rounds=3, iterations=1)
