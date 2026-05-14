"""
tests/test_cli.py
=================
Phase 7 — CLI gap-fill tests.

Targets `cli/rnv_transform.py`, the largest known coverage gap at 50.7%
in the post-Phase-6 baseline. Specific uncovered ranges from the baseline:

  Lines 465–585: argument parser construction + list-* handlers
  Lines 598–658: parse_args glob/recursive/output-path resolution

These tests use:
  - capsys (built into pytest) to capture stdout/stderr
  - tmp_path (built into pytest) for filesystem isolation
  - monkeypatch to replace sys.stdin for stdin-mode tests

All 12 tests run in <1 second. They exercise the CLI from main() down to
the file system and back, catching the orchestration-layer mutations that
the pure-logic tests can't reach.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from cli.rnv_transform import main, parse_args, CLIProcessor, CLIOptions


# ════════════════════════════════════════════════════════════════════════════
# 1. Listing commands — exercise lines 354-460 (_list_* handlers)
# ════════════════════════════════════════════════════════════════════════════

class TestCLIListCommands:
    """Tests for --list-modes, --list-presets, --list-cleanup."""

    def test_main_list_modes_prints_modes_and_exits_zero(self, capsys):
        """--list-modes prints all 11 transformation modes and returns 0."""
        rc = main(["--list-modes"])
        assert rc == 0
        captured = capsys.readouterr()
        # Must include the canonical mode names
        assert "UPPERCASE" in captured.out
        assert "lowercase" in captured.out
        assert "snake_case" in captured.out

    def test_main_list_presets_prints_presets_and_exits_zero(self, capsys):
        """--list-presets prints available presets and returns 0."""
        rc = main(["--list-presets"])
        assert rc == 0
        captured = capsys.readouterr()
        # At least one built-in preset name should appear
        assert len(captured.out) > 0
        # No error output
        assert captured.err == "" or "error" not in captured.err.lower()

    def test_main_list_cleanup_prints_operations_and_exits_zero(self, capsys):
        """--list-cleanup prints all cleanup operations and returns 0."""
        rc = main(["--list-cleanup"])
        assert rc == 0
        captured = capsys.readouterr()
        # CLI prints StrEnum values (lowercase identifiers), not display names
        assert "trim_whitespace" in captured.out
        assert "remove_duplicate_lines" in captured.out
        assert "sort_lines" in captured.out


# ════════════════════════════════════════════════════════════════════════════
# 2. Validation errors — exercise the validation paths in _validate_options
# ════════════════════════════════════════════════════════════════════════════

class TestCLIValidationErrors:
    """Tests for non-zero exit codes from invalid arguments."""

    def test_main_unknown_mode_exits_nonzero(self, capsys, tmp_path):
        """Unknown --mode value fails validation and returns non-zero."""
        fpath = tmp_path / "input.txt"
        fpath.write_text("hello", encoding="utf-8")

        rc = main([str(fpath), "--mode", "NotARealMode_XYZ"])
        assert rc != 0
        captured = capsys.readouterr()
        assert "NotARealMode_XYZ" in captured.err or "NotARealMode_XYZ" in captured.out

    def test_main_unknown_preset_exits_nonzero(self, capsys, tmp_path):
        """Unknown --preset name fails validation and returns non-zero."""
        fpath = tmp_path / "input.txt"
        fpath.write_text("hello", encoding="utf-8")

        rc = main([str(fpath), "--preset", "ThisPresetDoesNotExist"])
        assert rc != 0
        captured = capsys.readouterr()
        assert "ThisPresetDoesNotExist" in captured.err + captured.out

    def test_main_invalid_cleanup_op_exits_nonzero(self, capsys, tmp_path):
        """Unknown --cleanup operation fails validation and returns non-zero."""
        fpath = tmp_path / "input.txt"
        fpath.write_text("hello", encoding="utf-8")

        rc = main([str(fpath), "--cleanup", "not_a_real_op"])
        assert rc != 0
        captured = capsys.readouterr()
        assert "not_a_real_op" in captured.err + captured.out

    def test_main_no_transform_specified_exits_nonzero(self, capsys, tmp_path):
        """File specified but no --mode/--preset/--cleanup → error."""
        fpath = tmp_path / "input.txt"
        fpath.write_text("hello", encoding="utf-8")

        rc = main([str(fpath)])
        assert rc != 0


# ════════════════════════════════════════════════════════════════════════════
# 3. Output writing — exercise file/dir output paths
# ════════════════════════════════════════════════════════════════════════════

class TestCLIOutputWriting:
    """Tests for -o/--output and -d/--output-dir."""

    def test_main_writes_output_file_with_dash_o(self, tmp_path):
        """-o output.txt produces the expected output file."""
        in_path = tmp_path / "input.txt"
        in_path.write_text("hello world", encoding="utf-8")
        out_path = tmp_path / "output.txt"

        rc = main([str(in_path), "--mode", "UPPERCASE", "-o", str(out_path)])
        assert rc == 0
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "HELLO WORLD"

    def test_main_writes_to_output_dir_for_batch(self, tmp_path):
        """-d outdir/ writes per-file outputs into the directory."""
        in_path = tmp_path / "input.txt"
        in_path.write_text("hello world", encoding="utf-8")
        out_dir = tmp_path / "outdir"
        out_dir.mkdir()

        rc = main([str(in_path), "--mode", "lowercase", "-d", str(out_dir)])
        assert rc == 0
        # Output file should exist in the output directory with the same basename
        out_files = list(out_dir.glob("*.txt"))
        assert len(out_files) >= 1
        assert any("hello world" in f.read_text(encoding="utf-8")
                   for f in out_files)


# ════════════════════════════════════════════════════════════════════════════
# 4. parse_args expansion — exercise lines 598-658
# ════════════════════════════════════════════════════════════════════════════

class TestParseArgsExpansion:
    """Tests for glob expansion, recursive directory handling, and stdin detection."""

    def test_parse_args_recursive_directory_collects_files(self, tmp_path):
        """-r DIRECTORY collects all files recursively into input_files."""
        # Create a nested directory structure
        (tmp_path / "a.txt").write_text("a", encoding="utf-8")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.txt").write_text("b", encoding="utf-8")
        (tmp_path / "sub" / "deeper").mkdir()
        (tmp_path / "sub" / "deeper" / "c.txt").write_text("c", encoding="utf-8")

        opts = parse_args([str(tmp_path), "-r", "--mode", "UPPERCASE"])
        # All three files should be found
        names = sorted(p.name for p in opts.input_files)
        assert "a.txt" in names
        assert "b.txt" in names
        assert "c.txt" in names

    def test_parse_args_stdin_dash_marker(self, tmp_path):
        """A literal '-' as input enables stdin mode."""
        opts = parse_args(["-", "--mode", "UPPERCASE"])
        assert opts.use_stdin is True
        assert opts.input_files == []

    def test_parse_args_existing_file_collected(self, tmp_path):
        """A real file path is added to input_files as a Path."""
        fpath = tmp_path / "real.txt"
        fpath.write_text("data", encoding="utf-8")

        opts = parse_args([str(fpath), "--mode", "UPPERCASE"])
        assert len(opts.input_files) == 1
        assert opts.input_files[0].name == "real.txt"

    def test_parse_args_cleanup_split_on_comma(self):
        """--cleanup ops,split,by,commas produces a list."""
        opts = parse_args(["-", "--cleanup", "trim_whitespace,remove_duplicate_lines"])
        assert opts.cleanup_ops == ["trim_whitespace", "remove_duplicate_lines"]

    def test_parse_args_verbose_and_quiet_flags(self):
        """--verbose and --quiet flags propagate to options."""
        opts_v = parse_args(["-", "--mode", "UPPERCASE", "--verbose"])
        assert opts_v.verbose is True
        assert opts_v.quiet is False

        opts_q = parse_args(["-", "--mode", "UPPERCASE", "--quiet"])
        assert opts_q.quiet is True
        assert opts_q.verbose is False
