"""
tests/test_snapshots.py
=======================
Phase 2 — Snapshot tests for byte-exact output validation.

Locks in the rendered output of three modules whose value lives entirely
in the strings they produce:

    DialogStyleManager (utils/dialog_styles.py)
        — every QSS the app renders for any dialog or component

    ExportManager      (core/export_manager.py)
        — every text-format export (TXT, HTML, Markdown, RTF)

    DiffEngine         (core/diff_engine.py)
        — every diff-rendering format (HTML, unified, side-by-side, conflict, summary)

A snapshot test does one thing: capture the function's output on a fixed
input the first time it runs, store it under tests/__snapshots__/, and then
on every subsequent run compare current output against the stored snapshot.
Any byte-level difference fails the test.

This is the test class that would have caught the cp1252 mojibake bug on
the first re-run after the regression was introduced.

────────────────────────────────────────────────────────────────────────────
First-run workflow (one time only):
    pytest tests/test_snapshots.py --snapshot-update
    # Creates tests/__snapshots__/test_snapshots.ambr
    # MANUALLY INSPECT the .ambr file before committing.

Subsequent runs (every later test invocation):
    pytest tests/test_snapshots.py
    # Compares actual output against stored snapshots.

After intentional code changes:
    pytest tests/test_snapshots.py --snapshot-update
    git diff tests/__snapshots__/   # review what changed
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json

import pytest

# Skip the entire module cleanly if syrupy isn't installed. The snapshot
# tests use the `snapshot` fixture provided by syrupy; without it pytest
# would error 27 times with "fixture 'snapshot' not found" instead of
# producing skipped-with-reason output. Install with: pip install syrupy
try:
    import syrupy as _syrupy  # noqa: F401
    _HAS_SYRUPY = True
except ImportError:
    _HAS_SYRUPY = False

pytestmark = pytest.mark.skipif(
    not _HAS_SYRUPY,
    reason="syrupy not installed — run: pip install syrupy",
)

from utils.dialog_styles import DialogStyleManager
from core.export_manager import ExportFormat, ExportManager, ExportOptions
from core.diff_engine import DiffEngine


# ════════════════════════════════════════════════════════════════════════════
# Determinism helpers
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _clear_caches():
    """
    Reset every cached state in DialogStyleManager before each test so cache
    state never leaks between snapshots.

    Two distinct caches must be cleared:
      1. DialogStyleManager._cache and _component_cache (the manual LRU dicts)
      2. The @lru_cache decorators on get_status_style / get_header_style /
         get_subtitle_style / get_description_style / get_tip_style
    """
    DialogStyleManager.clear_cache()

    # Clear any @lru_cache-decorated classmethods.
    for method_name in (
        "get_status_style",
        "get_header_style",
        "get_subtitle_style",
        "get_description_style",
        "get_tip_style",
    ):
        method = getattr(DialogStyleManager, method_name, None)
        if method is not None and hasattr(method, "cache_clear"):
            method.cache_clear()

    yield


def _read_export(path) -> str:
    """
    Read an exported file with normalized line endings.

    On Windows, Path.read_text() does not translate \\r\\n -> \\n by default,
    but explicit normalization is cheaper than discovering it later. Reading
    bytes and decoding manually also guarantees utf-8 regardless of platform
    locale.
    """
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


# ════════════════════════════════════════════════════════════════════════════
# 1. DialogStyleManager — 10 snapshots
# ════════════════════════════════════════════════════════════════════════════

class TestDialogStyleSnapshots:
    """Snapshots for every public DialogStyleManager method that returns text."""

    # ── Base dialog stylesheet × theme × font ──────────────────────────────────
    def test_dialog_stylesheet_dark_arial(self, snapshot):
        css = DialogStyleManager.get_dialog_stylesheet(True, "Arial")
        assert css == snapshot

    def test_dialog_stylesheet_light_arial(self, snapshot):
        css = DialogStyleManager.get_dialog_stylesheet(False, "Arial")
        assert css == snapshot

    def test_dialog_stylesheet_dark_montserrat(self, snapshot):
        css = DialogStyleManager.get_dialog_stylesheet(True, "Montserrat")
        assert css == snapshot

    def test_dialog_stylesheet_light_montserrat(self, snapshot):
        css = DialogStyleManager.get_dialog_stylesheet(False, "Montserrat")
        assert css == snapshot

    # ── Extended stylesheet with all components ────────────────────────────────
    # Component list covers every internal builder (_get_*_style) so the
    # rendered output is the maximum-surface case.
    _ALL_COMPONENTS = (
        "tab", "table", "list", "tree", "slider",
        "spinbox", "menu", "splitter", "progressbar",
    )

    def test_extended_stylesheet_dark_full(self, snapshot):
        css = DialogStyleManager.get_extended_stylesheet(
            True, "Arial", *self._ALL_COMPONENTS
        )
        assert css == snapshot

    def test_extended_stylesheet_light_full(self, snapshot):
        css = DialogStyleManager.get_extended_stylesheet(
            False, "Arial", *self._ALL_COMPONENTS
        )
        assert css == snapshot

    # ── Color dictionaries (serialized as JSON for stable comparison) ──────────
    def test_get_colors_dark(self, snapshot):
        colors = DialogStyleManager.get_colors(True)
        # JSON with sorted keys gives stable, diffable output regardless of
        # insertion order (insertion order is already deterministic, but
        # sort_keys makes the snapshot survive future dict reorderings that
        # don't actually change the contents).
        assert json.dumps(colors, sort_keys=True, indent=2) == snapshot

    def test_get_colors_light(self, snapshot):
        colors = DialogStyleManager.get_colors(False)
        assert json.dumps(colors, sort_keys=True, indent=2) == snapshot

    # ── Standalone QMenu stylesheet ────────────────────────────────────────────
    def test_menu_stylesheet_dark(self, snapshot):
        css = DialogStyleManager.get_menu_stylesheet(True)
        assert css == snapshot

    # ── All inline styles in a single combined snapshot ────────────────────────
    # 16 micro-snapshots would all look the same (one CSS line each), so we
    # consolidate them into a single multi-section snapshot. Any inline-style
    # regression still surfaces as a diff inside this one snapshot.
    def test_inline_styles_combined(self, snapshot):
        statuses = ("success", "error", "warning", "muted", "info", "accent")
        sections = []
        for is_dark in (True, False):
            theme_label = "dark" if is_dark else "light"
            sections.append(f"=== {theme_label} ===")
            sections.append(f"header:      {DialogStyleManager.get_header_style(is_dark)}")
            sections.append(f"subtitle:    {DialogStyleManager.get_subtitle_style(is_dark)}")
            sections.append(f"description: {DialogStyleManager.get_description_style(is_dark)}")
            sections.append(f"tip:         {DialogStyleManager.get_tip_style(is_dark)}")
            for status in statuses:
                sections.append(
                    f"status({status}): {DialogStyleManager.get_status_style(is_dark, status)}"
                )
            sections.append("")
        assert "\n".join(sections) == snapshot


# ════════════════════════════════════════════════════════════════════════════
# 2. ExportManager — 12 snapshots
# ════════════════════════════════════════════════════════════════════════════

class TestExportSnapshots:
    """Snapshots for every text-output export format and option variant."""

    @staticmethod
    def _opts(fmt: ExportFormat, **overrides) -> ExportOptions:
        """Build ExportOptions with deterministic defaults, plus any overrides."""
        return ExportOptions(format=fmt, **overrides)

    # ── TXT — basic, line numbers, unicode ─────────────────────────────────────
    def test_export_txt_basic(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.txt"
        em.export(snap_simple_text, path, self._opts(ExportFormat.TXT))
        assert _read_export(path) == snapshot

    def test_export_txt_line_numbers(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.txt"
        em.export(
            snap_simple_text, path,
            self._opts(ExportFormat.TXT, include_line_numbers=True),
        )
        assert _read_export(path) == snapshot

    def test_export_txt_unicode(self, tmp_workdir, snap_unicode_text, snapshot):
        """Encoding regression target — locks in utf-8 bytes for unicode + emoji."""
        em = ExportManager()
        path = tmp_workdir / "out.txt"
        em.export(snap_unicode_text, path, self._opts(ExportFormat.TXT))
        assert _read_export(path) == snapshot

    # ── HTML — light, dark, with metadata, special-chars escaping ──────────────
    def test_export_html_light_basic(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.html"
        em.export(snap_simple_text, path, self._opts(ExportFormat.HTML))
        assert _read_export(path) == snapshot

    def test_export_html_dark_basic(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.html"
        em.export(
            snap_simple_text, path,
            self._opts(ExportFormat.HTML, html_dark_theme=True),
        )
        assert _read_export(path) == snapshot

    def test_export_html_with_metadata(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.html"
        em.export(
            snap_simple_text, path,
            self._opts(
                ExportFormat.HTML,
                include_metadata=True,
                include_line_numbers=True,
            ),
        )
        assert _read_export(path) == snapshot

    def test_export_html_special_chars(self, tmp_workdir, snapshot):
        """HTML escaping regression target — locks in &lt;script&gt; encoding."""
        em = ExportManager()
        path = tmp_workdir / "out.html"
        em.export(
            "<script>alert('xss')</script>\n<b>bold</b> & \"quoted\"",
            path,
            self._opts(ExportFormat.HTML),
        )
        assert _read_export(path) == snapshot

    # ── Markdown — basic, line numbers, metadata ───────────────────────────────
    def test_export_markdown_basic(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.md"
        em.export(snap_simple_text, path, self._opts(ExportFormat.MARKDOWN))
        assert _read_export(path) == snapshot

    def test_export_markdown_line_numbers(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.md"
        em.export(
            snap_simple_text, path,
            self._opts(ExportFormat.MARKDOWN, include_line_numbers=True),
        )
        assert _read_export(path) == snapshot

    def test_export_markdown_metadata(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.md"
        em.export(
            snap_simple_text, path,
            self._opts(ExportFormat.MARKDOWN, include_metadata=True),
        )
        assert _read_export(path) == snapshot

    # ── RTF — basic, special-chars escaping ────────────────────────────────────
    def test_export_rtf_basic(self, tmp_workdir, snap_simple_text, snapshot):
        em = ExportManager()
        path = tmp_workdir / "out.rtf"
        em.export(snap_simple_text, path, self._opts(ExportFormat.RTF))
        assert _read_export(path) == snapshot

    def test_export_rtf_special_chars(self, tmp_workdir, snapshot):
        """RTF escaping regression target — locks in \\\\, {, } handling."""
        em = ExportManager()
        path = tmp_workdir / "out.rtf"
        em.export(
            "backslash: \\ open: { close: } and unicode: café",
            path,
            self._opts(ExportFormat.RTF),
        )
        assert _read_export(path) == snapshot


# ════════════════════════════════════════════════════════════════════════════
# 3. DiffEngine — 5 snapshots
# ════════════════════════════════════════════════════════════════════════════

class TestDiffSnapshots:
    """Snapshots for every public DiffEngine rendering method."""

    def test_compute_html_diff_render(self, snap_diff_input_pair, snapshot):
        """Highest-value diff snapshot — covers the ~80-line uncovered block."""
        left, right = snap_diff_input_pair
        html = DiffEngine.compute_html_diff(left, right, "Test Diff")
        assert html == snapshot

    def test_compute_unified_diff_render(self, snap_diff_input_pair, snapshot):
        left, right = snap_diff_input_pair
        unified = DiffEngine.compute_unified_diff(left, right)
        assert unified == snapshot

    def test_compute_side_by_side_render(self, snap_diff_input_pair, snapshot):
        left, right = snap_diff_input_pair
        sxs = DiffEngine.compute_side_by_side(left, right)
        assert sxs == snapshot

    def test_generate_conflict_markers_render(self, snap_diff_input_pair, snapshot):
        left, right = snap_diff_input_pair
        markers = DiffEngine.generate_conflict_markers(
            left, right, "ORIGINAL", "MODIFIED",
        )
        assert markers == snapshot

    def test_get_change_summary_render(self, snap_diff_input_pair, snapshot):
        left, right = snap_diff_input_pair
        result = DiffEngine.compute_diff(left, right)
        summary = DiffEngine.get_change_summary(result)
        assert summary == snapshot
