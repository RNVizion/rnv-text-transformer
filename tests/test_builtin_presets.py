"""
tests/test_builtin_presets.py
=============================
The built-in presets' cleanup steps do what they say (#94 A).

Every cleanup step in the six built-ins named an operation that does not
exist ('trim_whitespace', 'collapse_whitespace', 'strip_html', ...).
TextCleaner.cleanup() matches on CleanupOperation values, so each of those
steps returned the text unchanged: "Markdown Cleanup" and "Plain Text
Export", which are nothing but cleanup steps, did nothing at all.

The built-ins now name real operations, and a preset saved with the old
names (a duplicate of a built-in, or an export) is read as the operation
each old name stands for.
"""
from __future__ import annotations

import json

import pytest

from core.preset_manager import ActionType, PresetManager
from core.text_cleaner import CleanupOperation


def _cleanup_steps(preset):
    return [s for s in preset.steps if s.action == ActionType.CLEANUP]


class TestBuiltinPresets:

    def test_every_builtin_cleanup_step_names_a_real_operation(self, tmp_path):
        manager = PresetManager(presets_dir=tmp_path)
        builtins = [p for p in manager.get_all_presets() if p.is_builtin]
        assert len(builtins) == 6
        valid = {op.value for op in CleanupOperation}
        for preset in builtins:
            for step in _cleanup_steps(preset):
                assert step.params["operation"] in valid, (preset.name, step.params)

    @pytest.mark.parametrize("name, text, expected", [
        ("Markdown Cleanup", "# Title  \r\n\r\n\r\n\r\nBody\t\r\n", "# Title\n\nBody\n"),
        ("Plain Text Export", "  <p>Café</p>  ", "Café"),
        ("Code Variable Cleanup", "  Hello   World  ", "hello_world"),
        ("Constant Name Generator", "max   retry count", "MAX_RETRY_COUNT"),
        ("URL Slug Generator", "Hello\x07 World", "hello-world"),
    ])
    def test_builtin_preset_changes_the_text(self, tmp_path, name, text, expected):
        manager = PresetManager(presets_dir=tmp_path)
        result, applied = manager.execute_preset(text, name)
        assert not [a for a in applied if a.startswith("[ERROR]")]
        assert result == expected


class TestSavedPresetsWithOldNames:

    OLD_STEPS = [
        {"action": "cleanup", "params": {"operation": "normalize_line_endings"}},
        {"action": "cleanup", "params": {"operation": "remove_trailing_whitespace"}},
        {"action": "cleanup", "params": {"operation": "collapse_blank_lines"}},
        {"action": "cleanup", "params": {"operation": "strip_html"}},
        {"action": "cleanup", "params": {"operation": "collapse_whitespace"}},
        {"action": "cleanup", "params": {"operation": "trim_whitespace"}},
    ]

    def _write(self, folder, steps):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "presets.json").write_text(json.dumps({"presets": [{
            "name": "Markdown Cleanup (Copy)",
            "category": "Writing",
            "is_builtin": False,
            "steps": steps,
        }]}), encoding="utf-8")

    def test_old_names_load_as_the_operations_they_stand_for(self, tmp_path):
        self._write(tmp_path, self.OLD_STEPS)
        preset = PresetManager(presets_dir=tmp_path).get_preset("Markdown Cleanup (Copy)")
        assert [s.params["operation"] for s in preset.steps] == [
            CleanupOperation.FIX_LINE_ENDINGS_UNIX.value,
            CleanupOperation.REMOVE_TRAILING_SPACES.value,
            CleanupOperation.REMOVE_EXTRA_LINES.value,
            CleanupOperation.STRIP_HTML_TAGS.value,
            CleanupOperation.REMOVE_EXTRA_SPACES.value,
            CleanupOperation.TRIM_WHITESPACE.value,
        ]

    def test_saved_copy_with_old_names_cleans_the_text(self, tmp_path):
        self._write(tmp_path, self.OLD_STEPS)
        manager = PresetManager(presets_dir=tmp_path)
        result, _ = manager.execute_preset(
            "  <b>a</b>   b  \r\n\r\n\r\n\r\nc  ", "Markdown Cleanup (Copy)")
        assert result == "a b\n\nc"

    def test_unknown_operation_is_kept_as_it_was(self, tmp_path):
        """A name that matches nothing is left alone, and the step stays a no-op."""
        self._write(tmp_path, [{"action": "cleanup", "params": {"operation": "no_such_op"}}])
        manager = PresetManager(presets_dir=tmp_path)
        preset = manager.get_preset("Markdown Cleanup (Copy)")
        assert preset.steps[0].params["operation"] == "no_such_op"
        assert manager.execute_preset(" x ", preset.name)[0] == " x "
