"""
tests/test_workers.py
=====================
Phase 4 — Worker thread tests with QSignalSpy and qtbot.waitSignal.

Validates the threading paths the GUI uses in production:

    FileLoaderThread       (utils/async_workers.py — QThread)
    TextTransformThread    (utils/async_workers.py — QThread)
    BatchWorkerThread      (ui/batch_dialog.py — QThread, wraps BatchProcessor)
    FolderWatcher          (core/folder_watcher.py — Python threading + watchdog,
                            uses CALLBACKS not Qt signals)

Test patterns:

  - For QThread workers:
      * `qtbot.waitSignal(worker.finished, timeout=2000)` to capture signal payloads
      * `QSignalSpy(worker.progress)` to count and order progress emissions
      * Synchronous `.run()` (not `.start()`) for cancellation pre-condition tests
        where we want to assert "the signal did NOT fire"

  - For FolderWatcher (callback-based):
      * Pass a recording callable via `set_event_callback`
      * Poll for invocation with a deadline, since watchdog event timing varies
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from PyQt6.QtTest import QSignalSpy

from utils.async_workers import (
    FileLoaderThread,
    TextTransformThread,
    LARGE_TEXT_THRESHOLD,
    should_use_thread_for_transform,
)


# ════════════════════════════════════════════════════════════════════════════
# 1. FileLoaderThread — 5 tests
# ════════════════════════════════════════════════════════════════════════════

class TestFileLoaderThread:
    """Tests for the QThread that loads files in the background."""

    def test_file_loader_finished_on_valid_file(self, qtbot, tmp_path):
        """Reading a valid file emits `finished` with (content, filename)."""
        fpath = tmp_path / "sample.txt"
        fpath.write_text("hello world", encoding="utf-8")

        worker = FileLoaderThread(str(fpath))
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.start()
        worker.wait()  # ensure thread cleanup

        content, filename = blocker.args
        assert content == "hello world"
        assert filename == "sample.txt"

    def test_file_loader_emits_progress_in_order(self, qtbot, tmp_path):
        """Progress signal fires multiple times, monotonically non-decreasing."""
        fpath = tmp_path / "data.txt"
        fpath.write_text("x" * 1000, encoding="utf-8")

        worker = FileLoaderThread(str(fpath))
        progress_spy = QSignalSpy(worker.progress)
        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.start()
        worker.wait()

        progress_values = [args[0] for args in progress_spy]
        # FileLoaderThread.run emits 10 (start), 90 (almost done), 100 (final)
        assert 10 in progress_values
        assert 100 in progress_values
        # Monotonically non-decreasing
        assert progress_values == sorted(progress_values)

    def test_file_loader_error_on_missing_file(self, qtbot, tmp_path):
        """Loading a nonexistent file emits `error` with a non-empty message."""
        fpath = tmp_path / "does_not_exist.txt"
        worker = FileLoaderThread(str(fpath))

        with qtbot.waitSignal(worker.error, timeout=2000) as blocker:
            worker.start()
        worker.wait()

        (msg,) = blocker.args
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_file_loader_cancel_before_run_suppresses_signals(self, tmp_path):
        """
        With cancel() called before run(), the worker exits at the top of
        run() without emitting any signals. Run synchronously (.run() not
        .start()) because asserting "no signal fires" via qtbot.waitSignal
        requires waiting the full timeout.
        """
        fpath = tmp_path / "anything.txt"
        fpath.write_text("data", encoding="utf-8")
        worker = FileLoaderThread(str(fpath))
        finished_spy = QSignalSpy(worker.finished)
        error_spy = QSignalSpy(worker.error)

        worker.cancel()  # sets _cancelled = True
        worker.run()  # synchronous; should return immediately at line 60

        assert len(finished_spy) == 0
        assert len(error_spy) == 0

    def test_file_loader_finished_payload_filename_is_basename(self, qtbot, tmp_path):
        """The filename in the finished payload is the basename only, not full path."""
        fpath = tmp_path / "deep" / "nested" / "report.txt"
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text("report content", encoding="utf-8")

        worker = FileLoaderThread(str(fpath))
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.start()
        worker.wait()

        _content, filename = blocker.args
        assert filename == "report.txt"
        assert "/" not in filename and "\\" not in filename


# ════════════════════════════════════════════════════════════════════════════
# 2. TextTransformThread — 4 tests
# ════════════════════════════════════════════════════════════════════════════

class TestTextTransformThread:
    """Tests for the QThread that transforms large text in the background."""

    def test_text_transform_finished_uppercase(self, qtbot):
        """UPPERCASE transform emits `finished` with the upper-cased text."""
        worker = TextTransformThread("hello world", "UPPERCASE")
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.start()
        worker.wait()

        (result,) = blocker.args
        assert result == "HELLO WORLD"

    def test_text_transform_emits_progress(self, qtbot):
        """Progress signal includes 20 (start) and 100 (final)."""
        worker = TextTransformThread("some text", "lowercase")
        progress_spy = QSignalSpy(worker.progress)
        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.start()
        worker.wait()

        progress_values = [args[0] for args in progress_spy]
        assert 20 in progress_values
        assert 100 in progress_values

    def test_text_transform_cancel_before_run_suppresses_finished(self):
        """Synchronous cancellation: cancel() blocks all signal emission."""
        worker = TextTransformThread("hello", "UPPERCASE")
        finished_spy = QSignalSpy(worker.finished)
        error_spy = QSignalSpy(worker.error)

        worker.cancel()  # sets _cancelled = True
        worker.run()

        assert len(finished_spy) == 0
        assert len(error_spy) == 0

    def test_text_transform_unknown_mode_returns_unchanged(self, qtbot):
        """
        TextTransformer.transform_text returns unchanged text for unknown modes
        (not an exception). The worker therefore emits `finished` with the
        original text, not `error`. This validates the safe-fallback behavior.
        """
        worker = TextTransformThread("untouched", "ThisIsNotARealMode")
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.start()
        worker.wait()

        (result,) = blocker.args
        assert result == "untouched"


# ════════════════════════════════════════════════════════════════════════════
# 3. should_use_thread_for_transform helper — 1 test
# ════════════════════════════════════════════════════════════════════════════

class TestShouldUseThreadForTransform:
    """Tests for the threshold helper function."""

    def test_should_use_thread_threshold_boundary(self):
        """Below threshold returns False; above returns True."""
        assert should_use_thread_for_transform("a" * (LARGE_TEXT_THRESHOLD - 1)) is False
        assert should_use_thread_for_transform("a" * (LARGE_TEXT_THRESHOLD + 1)) is True
        # Exactly at threshold — strict > means False
        assert should_use_thread_for_transform("a" * LARGE_TEXT_THRESHOLD) is False


# ════════════════════════════════════════════════════════════════════════════
# 4. BatchWorkerThread — 4 tests
# ════════════════════════════════════════════════════════════════════════════

class TestBatchWorkerThread:
    """Tests for the QThread wrapping BatchProcessor in BatchDialog."""

    def test_batch_worker_finished_on_empty_folder(self, qtbot, tmp_workdir):
        """An empty folder produces a finished_processing signal with []."""
        from core.batch_processor import BatchProcessor
        from ui.batch_dialog import BatchWorkerThread

        processor = BatchProcessor(transform_mode="UPPERCASE",
                                   output_folder=tmp_workdir)
        worker = BatchWorkerThread(processor, tmp_workdir)

        with qtbot.waitSignal(worker.finished_processing, timeout=3000) as blocker:
            worker.start()
        worker.wait()

        (results,) = blocker.args
        assert results == []

    def test_batch_worker_processes_three_files(self, qtbot, watch_supported_files):
        """Three .txt files in the folder → three results."""
        from core.batch_processor import BatchProcessor
        from ui.batch_dialog import BatchWorkerThread

        out_dir = watch_supported_files / "_out"
        out_dir.mkdir(exist_ok=True)
        processor = BatchProcessor(transform_mode="UPPERCASE",
                                   output_folder=out_dir)
        worker = BatchWorkerThread(processor, watch_supported_files)

        with qtbot.waitSignal(worker.finished_processing, timeout=5000) as blocker:
            worker.start()
        worker.wait()

        (results,) = blocker.args
        assert len(results) == 3

    def test_batch_worker_emits_progress_for_each_file(self, qtbot, watch_supported_files):
        """progress_update fires at least three times — once per file."""
        from core.batch_processor import BatchProcessor
        from ui.batch_dialog import BatchWorkerThread

        out_dir = watch_supported_files / "_out2"
        out_dir.mkdir(exist_ok=True)
        processor = BatchProcessor(transform_mode="lowercase",
                                   output_folder=out_dir)
        worker = BatchWorkerThread(processor, watch_supported_files)
        progress_spy = QSignalSpy(worker.progress_update)

        with qtbot.waitSignal(worker.finished_processing, timeout=5000):
            worker.start()
        worker.wait()

        # 3 files → at least 3 progress emissions
        assert len(progress_spy) >= 3

    def test_batch_worker_cancel_marks_all_files_cancelled(
        self, qtbot, watch_supported_files
    ):
        """
        Pre-cancellation: calling cancel() on the processor BEFORE the worker
        starts means every file becomes a cancelled-marker BatchResult
        (success=False, message containing "Cancelled").

        This deterministically covers the cancellation branch in
        BatchProcessor.process_folder (lines 130-138). Mid-flight cancel via
        a connected slot is non-deterministic on fast machines because Qt's
        queued connections deliver the cancel after the worker has already
        finished.
        """
        from core.batch_processor import BatchProcessor
        from ui.batch_dialog import BatchWorkerThread

        out_dir = watch_supported_files / "_out_cancel"
        out_dir.mkdir(exist_ok=True)
        processor = BatchProcessor(transform_mode="UPPERCASE",
                                   output_folder=out_dir)
        worker = BatchWorkerThread(processor, watch_supported_files)

        # Pre-cancel: cancellation flag is set before any work begins
        processor.cancel()

        with qtbot.waitSignal(worker.finished_processing, timeout=3000) as blocker:
            worker.start()
        worker.wait()

        (results,) = blocker.args
        # Three .txt files in watch_supported_files; all should be cancelled
        assert len(results) == 3
        assert all(r.success is False for r in results)
        assert all("Cancelled" in r.message or "cancelled" in r.message
                   for r in results)


# ════════════════════════════════════════════════════════════════════════════
# 5. FolderWatcher — 4 tests (uses callback recording, not Qt signals)
# ════════════════════════════════════════════════════════════════════════════

class TestFolderWatcher:
    """
    Tests for the watchdog-based folder watcher.

    FolderWatcher is NOT a QThread. It uses Python's threading module + the
    watchdog library and exposes a callback API instead of Qt signals.
    """

    def test_folder_watcher_is_available_returns_bool(self):
        """is_available() returns a bool — pure check, no skip needed."""
        from core.folder_watcher import FolderWatcher
        result = FolderWatcher.is_available()
        assert isinstance(result, bool)

    def test_folder_watcher_add_rule_valid_folder(
        self, folder_watcher_unavailable_skip, tmp_workdir
    ):
        """Adding a rule with a valid folder returns True and stores it."""
        from core.folder_watcher import FolderWatcher, WatchRule

        watcher = FolderWatcher()
        rule = WatchRule(
            id="test_rule_1",
            input_folder=tmp_workdir,
            output_folder=tmp_workdir,
            file_patterns=["*.txt"],
            transform_mode="UPPERCASE",
            enabled=True,
        )
        try:
            assert watcher.add_rule(rule) is True
            stored = watcher.get_rules()
            assert any(r.id == "test_rule_1" for r in stored)
        finally:
            watcher.stop()

    def test_folder_watcher_add_rule_nonexistent_folder(
        self, folder_watcher_unavailable_skip, tmp_workdir
    ):
        """Adding a rule whose input folder doesn't exist returns False."""
        from core.folder_watcher import FolderWatcher, WatchRule

        watcher = FolderWatcher()
        rule = WatchRule(
            id="test_rule_bad",
            input_folder=tmp_workdir / "does_not_exist",
            output_folder=tmp_workdir,
            file_patterns=["*.txt"],
            transform_mode="UPPERCASE",
            enabled=True,
        )
        try:
            assert watcher.add_rule(rule) is False
        finally:
            watcher.stop()

    def test_folder_watcher_callback_fires_on_file_creation(
        self, folder_watcher_unavailable_skip, tmp_workdir
    ):
        """
        Start the watcher, create a .txt file in the watched folder, and
        verify the callback receives a WatchEvent within 3 seconds.
        """
        from core.folder_watcher import FolderWatcher, WatchRule

        received: list = []
        watcher = FolderWatcher()
        watcher.set_event_callback(lambda evt: received.append(evt))

        rule = WatchRule(
            id="cb_test",
            input_folder=tmp_workdir,
            output_folder=tmp_workdir,
            file_patterns=["*.txt"],
            transform_mode="UPPERCASE",
            enabled=True,
        )
        watcher.add_rule(rule)
        try:
            assert watcher.start() is True
            # Give the observer a moment to start watching, then create a file
            time.sleep(0.2)
            (tmp_workdir / "trigger.txt").write_text("hi", encoding="utf-8")

            # Poll for callback delivery
            deadline = time.time() + 3.0
            while time.time() < deadline and not received:
                time.sleep(0.05)

            assert received, "FolderWatcher did not deliver a WatchEvent within 3s"
        finally:
            watcher.stop()
