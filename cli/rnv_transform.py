#!/usr/bin/env python3
"""
RNV Text Transformer - Command Line Interface
Provides command-line access to text transformation features

Python 3.13 Optimized:
- argparse for argument parsing
- Rich output formatting (optional)
- Batch processing support
- Preset integration
- Stdin/stdout piping

Usage:
    # Basic usage
    rnv-transform input.txt --mode uppercase --output result.txt
    
    # Batch processing
    rnv-transform *.txt --mode snake_case --output-dir ./converted/
    
    # Apply preset
    rnv-transform input.txt --preset "Code Variable Cleanup" --output clean.txt
    
    # Pipeline (stdin/stdout)
    cat input.txt | rnv-transform --mode lowercase > output.txt
    
    # List available options
    rnv-transform --list-modes
    rnv-transform --list-presets
    rnv-transform --list-cleanup

"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import ClassVar, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

# Add parent directory to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.text_transformer import TextTransformer
from core.text_cleaner import TextCleaner, CleanupOperation, CLEANUP_ALIASES
from core.preset_manager import PresetManager, PresetExecutor
from utils.config import APP_NAME, APP_VERSION
from utils.file_handler import FileHandler, FileReadError


class OutputFormat(StrEnum):
    """Output format options."""
    TEXT = "text"
    JSON = "json"
    QUIET = "quiet"


@dataclass
class CLIOptions:
    """Container for CLI options."""
    # Input/Output
    input_files: list[Path] = field(default_factory=list)
    output_file: Path | None = None
    output_dir: Path | None = None
    
    # Transformation
    mode: str | None = None
    preset: str | None = None
    cleanup_ops: list[str] = field(default_factory=list)
    
    # Processing options
    encoding: str = "utf-8"
    recursive: bool = False
    force: bool = False
    
    # Output options
    verbose: bool = False
    quiet: bool = False
    format: OutputFormat = OutputFormat.TEXT
    
    # Special actions
    list_modes: bool = False
    list_presets: bool = False
    list_cleanup: bool = False
    
    # Stdin flag
    use_stdin: bool = False


class CLIProcessor:
    """
    Command-line processor for text transformations.
    
    Handles:
    - Single file transformation
    - Batch processing
    - Preset application
    - Cleanup operations
    - Stdin/stdout piping
    """
    
    __slots__ = ('options', 'preset_manager', '_verbose_output')
    
    def __init__(self, options: CLIOptions) -> None:
        """
        Initialize CLI processor.
        
        Args:
            options: CLI options
        """
        self.options = options
        self.preset_manager = PresetManager()
        self._verbose_output: list[str] = []
    
    def run(self) -> int:
        """
        Execute the CLI command.
        
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        # Handle list commands first
        if self.options.list_modes:
            self._list_modes()
            return 0
        
        if self.options.list_presets:
            self._list_presets()
            return 0
        
        if self.options.list_cleanup:
            self._list_cleanup()
            return 0
        
        # Validate options
        if not self._validate_options():
            return 1
        
        # Process input
        try:
            if self.options.use_stdin:
                return self._process_stdin()
            else:
                return self._process_files()
        except KeyboardInterrupt:
            self._error("\nOperation cancelled by user")
            return 130
        except Exception as e:
            self._error(f"Unexpected error: {e}")
            return 1
    
    def _validate_options(self) -> bool:
        """Validate CLI options."""
        # Must have either mode, preset, or cleanup ops
        if not self.options.mode and not self.options.preset and not self.options.cleanup_ops:
            if not self.options.use_stdin and not self.options.input_files:
                self._error("No input specified. Use --help for usage information.")
                return False
            self._error("Must specify --mode, --preset, or --cleanup")
            return False
        
        # Validate mode if specified
        if self.options.mode:
            available_modes = TextTransformer.get_available_modes()
            if self.options.mode not in available_modes:
                self._error(f"Unknown mode: {self.options.mode}")
                self._info(f"Available modes: {', '.join(available_modes)}")
                return False
        
        # Validate preset if specified
        if self.options.preset:
            presets = self.preset_manager.get_preset_names()
            if self.options.preset not in presets:
                self._error(f"Unknown preset: {self.options.preset}")
                self._info(f"Available presets: {', '.join(presets)}")
                return False
        
        # Validate cleanup ops if specified
        if self.options.cleanup_ops:
            # The names --list-cleanup prints, their display names, or an older alias
            valid_ops = [TextCleaner.operation_key(op) for op in CleanupOperation]
            for op in self.options.cleanup_ops:
                if TextCleaner.resolve_operation(op) is None:
                    self._error(f"Unknown cleanup operation: {op}")
                    self._info(f"Available operations: {', '.join(valid_ops)}")
                    return False
        
        # Validate input files exist
        for input_file in self.options.input_files:
            if not input_file.exists():
                self._error(f"Input file not found: {input_file}")
                return False
        
        # Validate output directory exists (create if needed)
        if self.options.output_dir:
            self.options.output_dir.mkdir(parents=True, exist_ok=True)
        
        return True
    
    def _process_stdin(self) -> int:
        """Process input from stdin."""
        self._verbose("Reading from stdin...")
        
        try:
            text = sys.stdin.read()
        except Exception as e:
            self._error(f"Error reading stdin: {e}")
            return 1
        
        # Transform text
        result = self._transform_text(text)
        if result is None:
            return 1
        
        # Output result
        if self.options.output_file:
            return self._write_file(self.options.output_file, result)
        else:
            sys.stdout.write(result)
            return 0
    
    def _process_files(self) -> int:
        """Process input files."""
        total_files = len(self.options.input_files)
        processed = 0
        errors = 0
        
        for i, input_file in enumerate(self.options.input_files, 1):
            self._verbose(f"Processing [{i}/{total_files}]: {input_file.name}")
            
            # Read input
            try:
                text = FileHandler.read_file_content(input_file)
                if text is None:
                    self._error(f"Could not read: {input_file}")
                    errors += 1
                    continue
            except FileReadError as e:
                self._error(f"Read error ({input_file}): {e}")
                errors += 1
                continue
            
            # Transform text
            result = self._transform_text(text)
            if result is None:
                errors += 1
                continue
            
            # Determine output path
            output_path = self._get_output_path(input_file)
            
            # Check if output exists
            if output_path.exists() and not self.options.force:
                if output_path != input_file:  # Don't warn about in-place
                    self._warning(f"Output exists (use --force to overwrite): {output_path}")
                    errors += 1
                    continue
            
            # Write output
            if self._write_file(output_path, result) == 0:
                processed += 1
                self._verbose(f"  → {output_path}")
            else:
                errors += 1
        
        # Summary
        if not self.options.quiet:
            if total_files > 1:
                self._info(f"Processed: {processed}/{total_files} files")
                if errors > 0:
                    self._warning(f"Errors: {errors}")
        
        return 0 if errors == 0 else 1
    
    def _transform_text(self, text: str) -> str | None:
        """
        Transform text using specified options.
        
        Args:
            text: Input text
            
        Returns:
            Transformed text or None on error
        """
        result = text
        
        try:
            # Apply cleanup operations first
            if self.options.cleanup_ops:
                for op_name in self.options.cleanup_ops:
                    op = TextCleaner.resolve_operation(op_name)
                    if op is None:
                        raise ValueError(f"Unknown cleanup operation: {op_name}")
                    result = TextCleaner.cleanup(result, op)
                    self._verbose(f"  Applied cleanup: {op_name}")
            
            # Apply preset
            if self.options.preset:
                preset = self.preset_manager.get_preset(self.options.preset)
                if preset:
                    # (#92 A) Called the way the GUI calls it: no arguments, then execute_preset(text, preset).
                    executor = PresetExecutor()
                    result, _applied = executor.execute_preset(result, preset)
                    self._verbose(f"  Applied preset: {self.options.preset}")
            
            # Apply transform mode
            if self.options.mode:
                result = TextTransformer.transform_text(result, self.options.mode)
                self._verbose(f"  Applied mode: {self.options.mode}")
            
            return result
            
        except Exception as e:
            self._error(f"Transform error: {e}")
            return None
    
    def _get_output_path(self, input_file: Path) -> Path:
        """
        Determine output path for a file.
        
        Args:
            input_file: Input file path
            
        Returns:
            Output file path
        """
        # Explicit output file (only for single file)
        if self.options.output_file and len(self.options.input_files) == 1:
            return self.options.output_file
        
        # Output directory specified
        if self.options.output_dir:
            return self.options.output_dir / input_file.name
        
        # Default: in-place (same file)
        return input_file
    
    def _write_file(self, path: Path, content: str) -> int:
        """
        Write content to file.
        
        Args:
            path: Output file path
            content: Content to write
            
        Returns:
            0 for success, 1 for error
        """
        try:
            path.write_text(content, encoding=self.options.encoding)
            return 0
        except Exception as e:
            self._error(f"Write error ({path}): {e}")
            return 1
    
    def _list_modes(self) -> None:
        """List available transformation modes."""
        print(f"\n{APP_NAME} - Available Transformation Modes\n")
        print("-" * 50)
        
        # Original modes
        print("\nBasic Modes:")
        for mode in TextTransformer.get_original_modes():
            print(f"  • {mode}")
        
        # Developer modes
        print("\nDeveloper Modes:")
        for mode in TextTransformer.get_developer_modes():
            print(f"  • {mode}")
        
        print("\nUsage: rnv-transform input.txt --mode \"UPPERCASE\"")
        print()
    
    def _list_presets(self) -> None:
        """List available presets."""
        print(f"\n{APP_NAME} - Available Presets\n")
        print("-" * 50)
        
        presets = self.preset_manager.get_all_presets()
        
        if not presets:
            print("\nNo presets available.")
            print("Create presets in the GUI (Ctrl+P) to use them here.")
        else:
            # Group by category
            categories: dict[str, list] = {}
            for preset in presets:
                cat = preset.category or "Uncategorized"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(preset)
            
            for category, cat_presets in sorted(categories.items()):
                print(f"\n{category}:")
                for preset in cat_presets:
                    steps = len(preset.steps)
                    print(f"  • {preset.name} ({steps} step{'s' if steps != 1 else ''})")
                    if preset.description:
                        print(f"      {preset.description}")
        
        print("\nUsage: rnv-transform input.txt --preset \"Preset Name\"")
        print()
    
    # What --list-cleanup prints for each operation, by group. Every
    # CleanupOperation is listed once; --cleanup accepts each name shown.
    _CLEANUP_GROUPS: ClassVar[list[tuple[str, list[tuple[CleanupOperation, str]]]]] = [
        ("Whitespace Operations", [
            (CleanupOperation.TRIM_WHITESPACE, "Remove leading/trailing whitespace from the whole text"),
            (CleanupOperation.REMOVE_EXTRA_SPACES, "Replace runs of spaces and tabs with one space"),
            (CleanupOperation.REMOVE_LEADING_SPACES, "Remove leading whitespace from each line"),
            (CleanupOperation.REMOVE_TRAILING_SPACES, "Remove trailing whitespace from each line"),
            (CleanupOperation.REMOVE_EXTRA_LINES, "Collapse three or more line breaks into one blank line"),
            (CleanupOperation.REMOVE_ALL_BLANK_LINES, "Remove empty/blank lines"),
            (CleanupOperation.FIX_LINE_ENDINGS_UNIX, "Convert line endings to LF"),
            (CleanupOperation.FIX_LINE_ENDINGS_WINDOWS, "Convert line endings to CRLF"),
        ]),
        ("Line Operations", [
            (CleanupOperation.REMOVE_DUPLICATE_LINES, "Remove duplicate lines, keeping the first"),
            (CleanupOperation.SORT_LINES, "Sort lines alphabetically (A-Z)"),
            (CleanupOperation.SORT_LINES_REVERSE, "Sort lines in reverse (Z-A)"),
        ]),
        ("Character Operations", [
            (CleanupOperation.STRIP_HTML_TAGS, "Remove HTML tags"),
            (CleanupOperation.REMOVE_NON_PRINTABLE, "Remove control characters"),
            (CleanupOperation.NORMALIZE_UNICODE, "Normalize Unicode (NFC)"),
        ]),
    ]
    
    def _list_cleanup(self) -> None:
        """List available cleanup operations."""
        print(f"\n{APP_NAME} - Available Cleanup Operations\n")
        print("-" * 50)
        
        for group, ops in self._CLEANUP_GROUPS:
            print(f"\n{group}:")
            for op, desc in ops:
                aliases = [a for a, target in CLEANUP_ALIASES.items() if target is op]
                also = f" (also: {', '.join(aliases)})" if aliases else ""
                print(f"  • {TextCleaner.operation_key(op)}{also}")
                print(f"      {desc} [\"{op.value}\"]")
        
        print("\nUsage: rnv-transform input.txt --cleanup trim_whitespace,remove_blank_lines")
        print("The name in brackets, as the GUI shows it, is accepted too.")
        print()
    
    def _verbose(self, message: str) -> None:
        """Print verbose message."""
        if self.options.verbose and not self.options.quiet:
            print(f"[INFO] {message}", file=sys.stderr)
    
    def _info(self, message: str) -> None:
        """Print info message."""
        if not self.options.quiet:
            print(message, file=sys.stderr)
    
    def _warning(self, message: str) -> None:
        """Print warning message."""
        if not self.options.quiet:
            print(f"[WARNING] {message}", file=sys.stderr)
    
    def _error(self, message: str) -> None:
        """Print error message."""
        print(f"[ERROR] {message}", file=sys.stderr)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="rnv-transform",
        description=f"{APP_NAME} - Command Line Text Transformer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transform a file to uppercase
  rnv-transform input.txt --mode UPPERCASE --output result.txt

  # Batch convert all .txt files to snake_case
  rnv-transform *.txt --mode snake_case --output-dir ./converted/

  # Apply a preset
  rnv-transform input.txt --preset "Code Variable Cleanup" --output clean.txt

  # Apply cleanup operations
  rnv-transform input.txt --cleanup trim_whitespace,remove_blank_lines

  # Pipeline (stdin/stdout)
  cat input.txt | rnv-transform --mode lowercase > output.txt

  # List available options
  rnv-transform --list-modes
  rnv-transform --list-presets
  rnv-transform --list-cleanup
"""
    )
    
    # Positional arguments
    parser.add_argument(
        "input",
        nargs="*",
        help="Input file(s) or - for stdin"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output file (default: in-place or stdout for stdin)"
    )
    output_group.add_argument(
        "-d", "--output-dir",
        metavar="DIR",
        help="Output directory for batch processing"
    )
    
    # Transformation options
    transform_group = parser.add_argument_group("Transformation Options")
    transform_group.add_argument(
        "-m", "--mode",
        metavar="MODE",
        help="Transformation mode (e.g., UPPERCASE, snake_case)"
    )
    transform_group.add_argument(
        "-p", "--preset",
        metavar="NAME",
        help="Apply named preset"
    )
    transform_group.add_argument(
        "-c", "--cleanup",
        metavar="OPS",
        help="Cleanup operations (comma-separated)"
    )
    
    # Processing options
    process_group = parser.add_argument_group("Processing Options")
    process_group.add_argument(
        "-e", "--encoding",
        default="utf-8",
        help="Output encoding (default: utf-8)"
    )
    process_group.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process directories recursively"
    )
    process_group.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files"
    )
    
    # Output control
    verbosity_group = parser.add_argument_group("Verbosity")
    verbosity_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    verbosity_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    # List commands
    list_group = parser.add_argument_group("Information")
    list_group.add_argument(
        "--list-modes",
        action="store_true",
        help="List available transformation modes"
    )
    list_group.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets"
    )
    list_group.add_argument(
        "--list-cleanup",
        action="store_true",
        help="List cleanup operations"
    )
    list_group.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} v{APP_VERSION}"
    )
    
    return parser


def parse_args(args: Sequence[str] | None = None) -> CLIOptions:
    """
    Parse command line arguments.
    
    Args:
        args: Arguments to parse (default: sys.argv)
        
    Returns:
        CLIOptions object
    """
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    options = CLIOptions()
    
    # List commands
    options.list_modes = parsed.list_modes
    options.list_presets = parsed.list_presets
    options.list_cleanup = parsed.list_cleanup
    
    # Input files
    if parsed.input:
        for input_path in parsed.input:
            if input_path == "-":
                options.use_stdin = True
            else:
                # Handle glob patterns
                path = Path(input_path)
                if "*" in input_path or "?" in input_path:
                    # Expand glob
                    import glob
                    for match in glob.glob(input_path, recursive=parsed.recursive):
                        options.input_files.append(Path(match))
                elif path.is_dir() and parsed.recursive:
                    # Recursively find files
                    for file in path.rglob("*"):
                        if file.is_file():
                            options.input_files.append(file)
                elif path.is_file():
                    options.input_files.append(path)
                else:
                    # Might not exist - validation will catch it
                    options.input_files.append(path)
    
    # Check for stdin from pipe
    if not options.input_files and not options.list_modes and not options.list_presets and not options.list_cleanup:
        if not sys.stdin.isatty():
            options.use_stdin = True
    
    # Output
    if parsed.output:
        options.output_file = Path(parsed.output)
    if parsed.output_dir:
        options.output_dir = Path(parsed.output_dir)
    
    # Transformation
    options.mode = parsed.mode
    options.preset = parsed.preset
    if parsed.cleanup:
        options.cleanup_ops = [op.strip() for op in parsed.cleanup.split(",")]
    
    # Processing
    options.encoding = parsed.encoding
    options.recursive = parsed.recursive
    options.force = parsed.force
    
    # Verbosity
    options.verbose = parsed.verbose
    options.quiet = parsed.quiet
    
    return options


def main(args: Sequence[str] | None = None) -> int:
    """
    Main entry point for CLI.
    
    Args:
        args: Command line arguments (default: sys.argv)
        
    Returns:
        Exit code
    """
    options = parse_args(args)
    processor = CLIProcessor(options)
    return processor.run()


if __name__ == "__main__":
    sys.exit(main())