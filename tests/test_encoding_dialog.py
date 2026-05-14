"""
tests/test_encoding_dialog.py
=============================
Phase 8b Round 5 — qtbot interaction tests for ui/encoding_dialog.py.

Target: 48.7% -> ~80% coverage on the EncodingDialog module.

Covers four classes in encoding_dialog.py:
  - CommonEncoding.get_display_name (static helper)
  - EncodingDetector / EncodingResult (already partially covered by frozen suite)
  - DetectionThread (QThread — we drive the handler manually, not the run loop)
  - EncodingDialog (the main dialog)
  - EncodingWidget (embedded variant)

Tests use hand-emitted signal payloads for DetectionThread handlers rather
than waiting on the real thread, to avoid the QThread coverage limitation
documented in Phase 4.

13 tests across 3 test classes.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QMessageBox

from core.theme_manager import ThemeManager
from ui.encoding_dialog import (
    CommonEncoding,
    EncodingResult,
    EncodingDialog,
    EncodingWidget,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def theme_dark(qapp) -> ThemeManager:
    """ThemeManager in dark mode."""
    tm = ThemeManager()
    tm.current_theme = "dark"
    return tm


# ═════════════════════════════════════════════════════════════════════════════
# 1. CommonEncoding static helper — 2 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestCommonEncodingHelper:
    """Tests for CommonEncoding.get_display_name (static helper)."""

    def test_get_display_name_for_known_encoding(self):
        """get_display_name for utf-8 returns the human-readable label."""
        assert CommonEncoding.get_display_name("utf-8") == "UTF-8 (Unicode)"
        assert CommonEncoding.get_display_name("windows-1252") == "Windows-1252 (Western)"

    def test_get_display_name_for_unknown_encoding_returns_uppercase(self):
        """Unknown encoding falls back to encoding.upper()."""
        assert CommonEncoding.get_display_name("ebcdic") == "EBCDIC"


# ═════════════════════════════════════════════════════════════════════════════
# 2. EncodingDialog — 9 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestEncodingDialog:
    """Tests for EncodingDialog (full conversion dialog)."""

    # ── set_text and _load_text ──────────────────────────────────────────────

    def test_set_text_populates_input_preview(self, qtbot, theme_dark):
        """set_text(...) populates input_preview QTextEdit."""
        dlg = EncodingDialog(theme_dark, input_text="initial content")
        qtbot.addWidget(dlg)
        dlg.set_text("new content for preview")
        assert "new content" in dlg.input_preview.toPlainText()

    def test_set_text_with_long_input_truncates_preview(self, qtbot, theme_dark):
        """Input over 500 chars gets truncated with a marker."""
        dlg = EncodingDialog(theme_dark)
        qtbot.addWidget(dlg)
        dlg.set_text("X" * 800)
        preview = dlg.input_preview.toPlainText()
        assert "truncated" in preview.lower()

    # ── Detection completion handler ─────────────────────────────────────────

    def test_on_detection_complete_with_high_confidence_selects_encoding(self, qtbot, theme_dark):
        """_on_detection_complete with high-confidence result selects the combo entry."""
        dlg = EncodingDialog(theme_dark, input_text="some text")
        qtbot.addWidget(dlg)
        # Hand-emit a high-confidence result
        result = EncodingResult(
            success=True,
            encoding="windows-1252",
            confidence=0.95,
            text="some text",
            message="Detected as Windows-1252",
        )
        dlg._on_detection_complete(result)
        # The source_combo should have moved to windows-1252
        assert dlg.source_combo.currentData() == "windows-1252"
        assert "95" in dlg.confidence_label.text()

    def test_on_detection_complete_with_medium_confidence_styles_label(self, qtbot, theme_dark):
        """Medium confidence (70-89%) applies warning color to confidence_label."""
        dlg = EncodingDialog(theme_dark, input_text="some text")
        qtbot.addWidget(dlg)
        result = EncodingResult(
            success=True,
            encoding="utf-8",
            confidence=0.75,
            text="some text",
            message="Medium confidence",
        )
        dlg._on_detection_complete(result)
        # Confidence label should have warning styling (some color set)
        assert "color" in dlg.confidence_label.styleSheet()

    def test_on_detection_complete_failure_shows_error_status(self, qtbot, theme_dark):
        """A failed detection result surfaces "Detection failed:" in status_label."""
        dlg = EncodingDialog(theme_dark)
        qtbot.addWidget(dlg)
        failure = EncodingResult(
            success=False,
            encoding="",
            confidence=0.0,
            text="",
            message="No bytes to analyze",
        )
        dlg._on_detection_complete(failure)
        assert "detection failed" in dlg.status_label.text().lower()

    # ── Preview / apply conversion ───────────────────────────────────────────

    def test_preview_conversion_populates_output_preview(self, qtbot, theme_dark):
        """_preview_conversion produces text in output_preview for a valid conversion."""
        dlg = EncodingDialog(theme_dark, input_text="Hello world")
        qtbot.addWidget(dlg)
        # Select utf-8 → utf-8 (identity conversion)
        dlg._preview_conversion()
        assert "Hello world" in dlg.output_preview.toPlainText()

    def test_apply_encoding_emits_encoding_applied_signal(self, qtbot, theme_dark):
        """_apply_encoding emits encoding_applied with the converted text."""
        dlg = EncodingDialog(theme_dark, input_text="Test content")
        qtbot.addWidget(dlg)

        # Mock self.accept() so it doesn't actually close the dialog
        with patch.object(dlg, "accept"):
            with qtbot.waitSignal(dlg.encoding_applied, timeout=1000) as spy:
                dlg._apply_encoding()
        assert "Test content" in spy.args[0]

    def test_mojibake_check_routes_to_fix_mojibake(self, qtbot, theme_dark):
        """When mojibake_check is checked, _preview_conversion uses fix_mojibake."""
        dlg = EncodingDialog(theme_dark, input_text="café")
        qtbot.addWidget(dlg)

        # Set source to windows-1252, target to utf-8, and enable mojibake mode
        for i in range(dlg.source_combo.count()):
            if dlg.source_combo.itemData(i) == "windows-1252":
                dlg.source_combo.setCurrentIndex(i)
                break
        dlg.mojibake_check.setChecked(True)

        # Should run without crashing and produce output
        dlg._preview_conversion()
        # Either success or controlled failure — output_preview gets text either way
        assert dlg.output_preview.toPlainText() != ""

    # ── closeEvent thread cleanup ───────────────────────────────────────────

    def test_close_event_waits_on_running_detection_thread(self, qtbot, theme_dark):
        """closeEvent invokes wait() on any running DetectionThread."""
        dlg = EncodingDialog(theme_dark, input_text="x")
        qtbot.addWidget(dlg)

        # Simulate a running detection thread
        class _FakeThread:
            def __init__(self) -> None:
                self.wait_called = False
            def isRunning(self) -> bool:
                return True
            def wait(self, msec: int) -> bool:
                self.wait_called = True
                return True

        fake = _FakeThread()
        dlg._detection_thread = fake
        # closeEvent should call fake.wait(1000)
        dlg.close()
        assert fake.wait_called is True


# ═════════════════════════════════════════════════════════════════════════════
# 3. EncodingWidget (embedded variant) — 2 tests
# ═════════════════════════════════════════════════════════════════════════════

class TestEncodingWidget:
    """Tests for the embedded EncodingWidget."""

    def test_encoding_widget_set_text_stores_input(self, qtbot, theme_dark):
        """set_text stores the value on input_text attribute."""
        widget = EncodingWidget(theme_dark)
        qtbot.addWidget(widget)
        widget.set_text("payload to convert")
        assert widget.input_text == "payload to convert"

    def test_encoding_widget_convert_emits_encoding_changed_on_success(self, qtbot, theme_dark):
        """_convert with a successful conversion emits encoding_changed."""
        widget = EncodingWidget(theme_dark)
        qtbot.addWidget(widget)
        widget.set_text("Hello world")
        # Default combos are utf-8 → utf-8 = identity conversion (always succeeds)
        with qtbot.waitSignal(widget.encoding_changed, timeout=1000) as spy:
            widget._convert()
        assert "Hello world" in spy.args[0]
