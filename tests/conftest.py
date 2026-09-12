# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the
# mode's gold: BRAND_GOLD in dark and image, BRAND_DARK_GOLD in light. The
# extras were always allowed it; this extends the same treatment to the
# surface, which already used it on the mixer's combo box. Two ramp steps
# lost their last consumer on the way and are retired.
# RNV-FLEET-FLOOR, 2026-09-11 -- tests/test_fleet_floor.py holds this
# application to the fleet's Python floor (3.13, declared and run), the
# PyQt6 major-version ceiling, and the dev tooling every repository must
# declare rather than merely agree about.
# RNV-NO-VACUOUS-TESTS, 2026-09-10 -- tests/test_no_vacuous_tests.py
# sweeps this repository for tests that cannot fail: assertions true
# whatever the code does, bodies that are only `pass`, tests with no
# assertion that swallow everything they call, and self-skips on a
# name that never existed. It deliberately permits a test with no
# assertion at all -- those assert by not raising.
"""
tests/conftest.py
=================
Shared fixtures for the new pytest-based test suite (pytest discovers
this file automatically when collecting from `tests/`).

The frozen test_rnv_text_transformer.py at the project root does NOT
use this file — it has its own setUp/tearDown machinery via unittest
and is run separately via `python -m unittest test_rnv_text_transformer`
(see run_tests.py).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# ── Headless Qt + sys.path bootstrap ───────────────────────────────────────────
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ── QApplication singleton (session-scoped) ────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def _qapplication_singleton():
    """Ensure a single QApplication instance exists for the whole session."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1])
            app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
        yield app
    except ImportError:
        yield None


# ── Working directories ────────────────────────────────────────────────────────
@pytest.fixture
def tmp_workdir():
    """Throwaway scratch directory; cleaned up automatically."""
    p = Path(tempfile.mkdtemp(prefix="rnv_test_"))
    try:
        yield p
    finally:
        shutil.rmtree(p, ignore_errors=True)


# ── Settings isolation ─────────────────────────────────────────────────────────
@pytest.fixture
def tmp_settings():
    """SettingsManager scoped to a unique organization."""
    from utils.settings_manager import SettingsManager
    original_org = SettingsManager._ORGANIZATION
    SettingsManager._ORGANIZATION = f"RNV_TEST_{os.getpid()}"
    sm = SettingsManager()
    try:
        yield sm
    finally:
        SettingsManager().clear_all()
        SettingsManager._ORGANIZATION = original_org


# ── Sample text inputs ─────────────────────────────────────────────────────────
@pytest.fixture
def sample_short_text():
    return "Hello World"


@pytest.fixture
def sample_long_text():
    return ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            * 18000)


# ── Themes ─────────────────────────────────────────────────────────────────────
@pytest.fixture
def dark_theme():
    from core.theme_manager import ThemeManager
    tm = ThemeManager()
    tm.set_theme("dark")
    return tm


@pytest.fixture
def light_theme():
    from core.theme_manager import ThemeManager
    tm = ThemeManager()
    tm.set_theme("light")
    return tm


# ── Snapshot test inputs (Phase 2) ─────────────────────────────────────────────
@pytest.fixture(scope="session")
def snap_simple_text():
    return "Hello World\nLine 2\nLine 3"


@pytest.fixture(scope="session")
def snap_unicode_text():
    return "Café résumé — \u201csmart quotes\u201d — 日本語 — 🎨 emoji"


@pytest.fixture(scope="session")
def snap_diff_input_pair():
    left = "alpha\nbeta\ngamma\ndelta"
    right = "alpha\nBETA\ngamma\ndelta\nepsilon"
    return left, right


# ── Phase 3 widget/dialog fixtures ─────────────────────────────────────────────
@pytest.fixture
def theme_manager_dark(dark_theme):
    return dark_theme


@pytest.fixture
def theme_manager_light(light_theme):
    return light_theme


@pytest.fixture
def preset_manager_empty(tmp_workdir):
    from core.preset_manager import PresetManager
    return PresetManager(presets_dir=tmp_workdir)


@pytest.fixture
def main_window(qtbot, tmp_settings):
    from ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    return win


# ── Phase 4 worker-thread fixtures ─────────────────────────────────────────────
@pytest.fixture
def watch_supported_files(tmp_workdir):
    """Three small .txt files in a temp directory for BatchWorkerThread tests."""
    (tmp_workdir / "alpha.txt").write_text("hello world\n", encoding="utf-8")
    (tmp_workdir / "beta.txt").write_text("foo bar baz\n", encoding="utf-8")
    (tmp_workdir / "gamma.txt").write_text("one two three\n", encoding="utf-8")
    return tmp_workdir


@pytest.fixture
def folder_watcher_unavailable_skip():
    """Skip the calling test if watchdog is not installed."""
    from core.folder_watcher import FolderWatcher
    if not FolderWatcher.is_available():
        pytest.skip("watchdog package not installed")
