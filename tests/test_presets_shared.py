"""
tests/test_presets_shared.py
============================
The GUI and the CLI keep presets in one folder (#94 A).

PresetManager asks Qt for its AppDataLocation. In the GUI that path ends
in the QApplication's name (``<AppData>/RNV_Text_Transformer.py/RNV/...``
when the GUI is started from its script); the CLI has no QApplication, so
Qt left the name out and the CLI read ``<AppData>/RNV/...``. A preset made
in the GUI was never listed by ``rnv-transform --list-presets``.

Both now use the GUI's folder. The CLI's old folder is still read and
merged on load, and never written or deleted.

The two processes run as subprocesses with a temporary HOME and
XDG_DATA_HOME, so nothing touches the real user folders. Those variables
move Qt's folders on Linux only, so the subprocess tests run there.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

linux_only = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="HOME and XDG_DATA_HOME move Qt's AppDataLocation on Linux only",
)

# What the GUI does: a QApplication named as the GUI script names it, then
# PresetManager() with no folder given.
GUI_SAVE = """
import sys
sys.path.insert(0, sys.argv[1])
from PyQt6.QtWidgets import QApplication
app = QApplication([sys.argv[1] + "/RNV_Text_Transformer.py"])
from core.preset_manager import PresetManager, TransformPreset, create_transform_step
manager = PresetManager()
assert manager.add_preset(TransformPreset(
    name=sys.argv[2], category="Shared",
    steps=[create_transform_step("UPPERCASE")]))
print(manager._presets_path)
"""

GUI_LIST = """
import sys
sys.path.insert(0, sys.argv[1])
from PyQt6.QtWidgets import QApplication
app = QApplication([sys.argv[1] + "/RNV_Text_Transformer.py"])
from core.preset_manager import PresetManager
print("\\n".join(PresetManager().get_preset_names()))
"""


def _env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(HOME=str(home), XDG_DATA_HOME=str(home / "data"),
               XDG_CONFIG_HOME=str(home / "config"), QT_QPA_PLATFORM="offscreen")
    return env


def _run(args: list[str], home: Path) -> str:
    done = subprocess.run([sys.executable, *args], cwd=REPO, env=_env(home),
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return done.stdout


def _cli_list(home: Path) -> str:
    return _run(["-m", "cli.rnv_transform", "--list-presets"], home)


@linux_only
class TestOneFolder:

    def test_preset_saved_by_the_gui_is_listed_by_the_cli(self, tmp_path):
        saved_at = Path(_run(["-c", GUI_SAVE, str(REPO), "Made In The GUI"], tmp_path).strip())
        assert saved_at.is_relative_to(tmp_path)
        assert saved_at.parts[-4:] == ("RNV_Text_Transformer.py", "RNV", "TextTransformer",
                                       "presets.json")
        assert "Made In The GUI" in _cli_list(tmp_path)

    def test_cli_preset_runs_the_gui_preset(self, tmp_path):
        _run(["-c", GUI_SAVE, str(REPO), "Shout"], tmp_path)
        done = subprocess.run(
            [sys.executable, "-m", "cli.rnv_transform", "--preset", "Shout", "-"],
            cwd=REPO, env=_env(tmp_path), input="quiet", capture_output=True,
            text=True, timeout=60)
        assert done.returncode == 0, done.stderr
        assert done.stdout == "QUIET"


@linux_only
class TestOldCliFolder:

    def _write_old(self, home: Path, presets: list[dict]) -> Path:
        old = home / "data" / "RNV" / "TextTransformer" / "presets.json"
        old.parent.mkdir(parents=True)
        old.write_text(json.dumps({"presets": presets}), encoding="utf-8")
        return old

    def test_both_folders_are_read_and_the_old_one_is_left_as_it_was(self, tmp_path):
        old = self._write_old(tmp_path, [{"name": "Kept From The CLI Folder", "steps": []}])
        before = old.read_bytes()

        _run(["-c", GUI_SAVE, str(REPO), "Made In The GUI"], tmp_path)
        cli_listing = _cli_list(tmp_path)
        gui_listing = _run(["-c", GUI_LIST, str(REPO)], tmp_path)

        for listing in (cli_listing, gui_listing):
            assert "Made In The GUI" in listing
            assert "Kept From The CLI Folder" in listing
        assert old.read_bytes() == before

    def test_same_name_different_preset_keeps_both(self, tmp_path):
        _run(["-c", GUI_SAVE, str(REPO), "Clash"], tmp_path)
        self._write_old(tmp_path, [{
            "name": "Clash", "steps": [{"action": "transform", "params": {"mode": "lowercase"}}],
        }])
        listing = _run(["-c", GUI_LIST, str(REPO)], tmp_path).splitlines()
        assert "Clash" in listing
        assert "Clash (1)" in listing


class TestDefaultFolder:

    def test_gui_folder_is_the_app_data_location_as_before(self, qapp):
        """With a QApplication, the folder is the one the GUI has always used."""
        from PyQt6.QtCore import QStandardPaths
        from core.preset_manager import default_presets_dirs

        primary, legacy = default_presets_dirs()
        app_data = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation))
        assert primary == app_data / "RNV" / "TextTransformer"
        assert legacy and all(p != primary for p in legacy)

    @pytest.mark.skipif(sys.platform != "win32", reason="Qt names a Windows app after its .exe")
    def test_without_an_app_the_name_is_the_one_qt_gives_the_gui_on_windows(self, qapp):
        """The test session's QApplication runs in the same python.exe the GUI does."""
        from core.preset_manager import _gui_application_name
        assert _gui_application_name() == qapp.applicationName()

    def test_explicit_folder_reads_no_other(self, tmp_path):
        from core.preset_manager import PresetManager
        assert PresetManager(presets_dir=tmp_path)._legacy_paths == []
