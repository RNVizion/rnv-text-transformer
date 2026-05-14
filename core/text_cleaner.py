"""
RNV Text Transformer - Text Cleaner Module
Handles text cleanup and split/join operations

Python 3.13 Optimized:
- Pre-compiled regex patterns for performance
- StrEnum for operation modes
- Type hints throughout
- Efficient string operations

"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from typing import ClassVar, Pattern


class CleanupOperation(StrEnum):
    """Available text cleanup operations."""
    TRIM_WHITESPACE = "Trim Whitespace"
    REMOVE_EXTRA_SPACES = "Remove Extra Spaces"
    REMOVE_EXTRA_LINES = "Remove Extra Blank Lines"
    REMOVE_ALL_BLANK_LINES = "Remove All Blank Lines"
    FIX_LINE_ENDINGS_UNIX = "Fix Line Endings (→ LF)"
    FIX_LINE_ENDINGS_WINDOWS = "Fix Line Endings (→ CRLF)"
    REMOVE_DUPLICATE_LINES = "Remove Duplicate Lines"
    SORT_LINES = "Sort Lines (A-Z)"
    SORT_LINES_REVERSE = "Sort Lines (Z-A)"
    STRIP_HTML_TAGS = "Strip HTML Tags"
    REMOVE_NON_PRINTABLE = "Remove Non-Printable"
    NORMALIZE_UNICODE = "Normalize Unicode"
    REMOVE_LEADING_SPACES = "Remove Leading Spaces"
    REMOVE_TRAILING_SPACES = "Remove Trailing Spaces"


class SplitJoinOperation(StrEnum):
    """Available split/join operations."""
    SPLIT_BY_COMMA = "Split by Comma"
    SPLIT_BY_SEMICOLON = "Split by Semicolon"
    SPLIT_BY_TAB = "Split by Tab"
    SPLIT_BY_SPACE = "Split by Space"
    SPLIT_BY_NEWLINE = "Split by Newline"
    JOIN_WITH_COMMA = "Join with Comma"
    JOIN_WITH_SEMICOLON = "Join with Semicolon"
    JOIN_WITH_TAB = "Join with Tab"
    JOIN_WITH_SPACE = "Join with Space"
    JOIN_WITH_NEWLINE = "Join with Newline"
    JOIN_LINES_COMMA = "Join Lines with Comma"
    JOIN_LINES_SPACE = "Join Lines with Space"


class TextCleaner:
    """
    Handles text cleanup and split/join operations.
    
    All methods are static for easy use without instantiation.
    Uses pre-compiled regex patterns for performance.
    """
    
    __slots__ = ()
    
    # Pre-compiled regex patterns
    _EXTRA_SPACES: ClassVar[Pattern[str]] = re.compile(r'[ \t]+')
    _EXTRA_BLANK_LINES: ClassVar[Pattern[str]] = re.compile(r'\n\s*\n\s*\n+')
    _ALL_BLANK_LINES: ClassVar[Pattern[str]] = re.compile(r'^\s*$\n?', re.MULTILINE)
    _HTML_TAGS: ClassVar[Pattern[str]] = re.compile(r'<[^>]+>')
    _NON_PRINTABLE: ClassVar[Pattern[str]] = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
    _CRLF: ClassVar[Pattern[str]] = re.compile(r'\r\n')
    _CR_ONLY: ClassVar[Pattern[str]] = re.compile(r'\r(?!\n)')
    _LF: ClassVar[Pattern[str]] = re.compile(r'(?<!\r)\n')
    
    # ==================== CLEANUP OPERATIONS ====================
    
    @staticmethod
    def cleanup(text: str, operation: str) -> str:
        """
        Apply a cleanup operation to text.
        
        Args:
            text: Input text to clean
            operation: CleanupOperation value
            
        Returns:
            Cleaned text
        """
        match operation:
            case CleanupOperation.TRIM_WHITESPACE:
                return TextCleaner.trim_whitespace(text)
            case CleanupOperation.REMOVE_EXTRA_SPACES:
                return TextCleaner.remove_extra_spaces(text)
            case CleanupOperation.REMOVE_EXTRA_LINES:
                return TextCleaner.remove_extra_blank_lines(text)
            case CleanupOperation.REMOVE_ALL_BLANK_LINES:
                return TextCleaner.remove_all_blank_lines(text)
            case CleanupOperation.FIX_LINE_ENDINGS_UNIX:
                return TextCleaner.fix_line_endings_unix(text)
            case CleanupOperation.FIX_LINE_ENDINGS_WINDOWS:
                return TextCleaner.fix_line_endings_windows(text)
            case CleanupOperation.REMOVE_DUPLICATE_LINES:
                return TextCleaner.remove_duplicate_lines(text)
            case CleanupOperation.SORT_LINES:
                return TextCleaner.sort_lines(text)
            case CleanupOperation.SORT_LINES_REVERSE:
                return TextCleaner.sort_lines(text, reverse=True)
            case CleanupOperation.STRIP_HTML_TAGS:
                return TextCleaner.strip_html_tags(text)
            case CleanupOperation.REMOVE_NON_PRINTABLE:
                return TextCleaner.remove_non_printable(text)
            case CleanupOperation.NORMALIZE_UNICODE:
                return TextCleaner.normalize_unicode(text)
            case CleanupOperation.REMOVE_LEADING_SPACES:
                return TextCleaner.remove_leading_spaces(text)
            case CleanupOperation.REMOVE_TRAILING_SPACES:
                return TextCleaner.remove_trailing_spaces(text)
            case _:
                return text
    
    @staticmethod
    def trim_whitespace(text: str) -> str:
        """
        Trim leading and trailing whitespace from entire text.
        
        Args:
            text: Input text
            
        Returns:
            Trimmed text
        """
        return text.strip()
    
    @staticmethod
    def remove_extra_spaces(text: str) -> str:
        """
        Replace multiple consecutive spaces/tabs with single space.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized spaces
        """
        return TextCleaner._EXTRA_SPACES.sub(' ', text)
    
    @staticmethod
    def remove_extra_blank_lines(text: str) -> str:
        """
        Replace 3+ consecutive newlines with 2 (keeping paragraph breaks).
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized blank lines
        """
        return TextCleaner._EXTRA_BLANK_LINES.sub('\n\n', text)
    
    @staticmethod
    def remove_all_blank_lines(text: str) -> str:
        """
        Remove all blank lines from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without blank lines
        """
        lines = text.splitlines()
        non_blank = [line for line in lines if line.strip()]
        return '\n'.join(non_blank)
    
    @staticmethod
    def fix_line_endings_unix(text: str) -> str:
        """
        Convert all line endings to Unix style (LF).
        
        Args:
            text: Input text
            
        Returns:
            Text with LF line endings
        """
        # Replace CRLF first, then lone CR
        result = TextCleaner._CRLF.sub('\n', text)
        return TextCleaner._CR_ONLY.sub('\n', result)
    
    @staticmethod
    def fix_line_endings_windows(text: str) -> str:
        """
        Convert all line endings to Windows style (CRLF).
        
        Args:
            text: Input text
            
        Returns:
            Text with CRLF line endings
        """
        # First normalize to LF, then convert to CRLF
        normalized = TextCleaner.fix_line_endings_unix(text)
        return normalized.replace('\n', '\r\n')
    
    @staticmethod
    def _preserve_trailing_newline(original: str, result: str) -> str:
        """
        Restore a trailing '\\n' to result if the original input ended in any
        recognized line separator.

        Many cleanup operations follow the pattern:
            lines = text.splitlines()
            ... operate on lines ...
            return '\\n'.join(result_lines)

        This pattern is asymmetric about trailing line separators. `splitlines()`
        consumes the trailing terminator but keeps an empty element if there's
        content after one (e.g. "a\\r" -> ["a", ""]). The first call may
        produce output ending in '\\n'; the second call's `splitlines()`
        consumes that '\\n', producing different output. Result:
        cleanup(cleanup(x, op), op) != cleanup(x, op).

        Wrapping the join result with this helper preserves idempotence for
        any input containing '\\n', '\\r', or any of the other line separators
        Python's str.splitlines() recognizes.

        Note: the result may be empty even when the original ended in a
        separator (e.g. sort_lines("\\x1e\\r") -> "\\n", whose second pass
        sorts the single empty line back to ""). In that case we still
        append '\\n' so the output is canonical.
        """
        if not original.endswith(("\n", "\r")):
            return result
        if result.endswith("\n"):
            return result
        return result + "\n"

    @staticmethod
    def remove_duplicate_lines(text: str, preserve_order: bool = True) -> str:
        """
        Remove duplicate lines from text.
        
        Args:
            text: Input text
            preserve_order: If True, keep first occurrence; if False, sort result
            
        Returns:
            Text with duplicates removed
        """
        if not text:
            return text

        lines = text.splitlines()

        if preserve_order:
            seen: set[str] = set()
            unique: list[str] = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique.append(line)
            result = '\n'.join(unique)
        else:
            result = '\n'.join(sorted(set(lines)))

        return TextCleaner._preserve_trailing_newline(text, result)
    
    @staticmethod
    def sort_lines(text: str, reverse: bool = False, case_insensitive: bool = True) -> str:
        """
        Sort lines alphabetically.
        
        Args:
            text: Input text
            reverse: If True, sort Z-A
            case_insensitive: If True, ignore case when sorting
            
        Returns:
            Sorted text
        """
        lines = text.splitlines()
        key_func = str.lower if case_insensitive else None
        result = '\n'.join(sorted(lines, key=key_func, reverse=reverse))
        return TextCleaner._preserve_trailing_newline(text, result)
    
    @staticmethod
    def strip_html_tags(text: str) -> str:
        """
        Remove HTML/XML tags from text.
        
        Args:
            text: Input text with HTML tags
            
        Returns:
            Plain text without tags
        """
        return TextCleaner._HTML_TAGS.sub('', text)
    
    @staticmethod
    def remove_non_printable(text: str) -> str:
        """
        Remove non-printable control characters.
        
        Preserves newlines, tabs, and standard whitespace.
        
        Args:
            text: Input text
            
        Returns:
            Text with control characters removed
        """
        return TextCleaner._NON_PRINTABLE.sub('', text)
    
    @staticmethod
    def normalize_unicode(text: str, form: str = 'NFC') -> str:
        """
        Normalize Unicode text to specified form.
        
        Args:
            text: Input text
            form: Normalization form ('NFC', 'NFD', 'NFKC', 'NFKD')
            
        Returns:
            Normalized text
        """
        return unicodedata.normalize(form, text)
    
    @staticmethod
    def remove_leading_spaces(text: str) -> str:
        """
        Remove leading whitespace from each line.
        
        Args:
            text: Input text
            
        Returns:
            Text with leading spaces removed from each line
        """
        lines = text.splitlines()
        result = '\n'.join(line.lstrip() for line in lines)
        return TextCleaner._preserve_trailing_newline(text, result)
    
    @staticmethod
    def remove_trailing_spaces(text: str) -> str:
        """
        Remove trailing whitespace from each line.
        
        Args:
            text: Input text
            
        Returns:
            Text with trailing spaces removed from each line
        """
        lines = text.splitlines()
        result = '\n'.join(line.rstrip() for line in lines)
        return TextCleaner._preserve_trailing_newline(text, result)
    
    # ==================== SPLIT/JOIN OPERATIONS ====================
    
    @staticmethod
    def split_join(text: str, operation: str, custom_delimiter: str = '') -> str:
        """
        Apply a split/join operation to text.
        
        Args:
            text: Input text
            operation: SplitJoinOperation value
            custom_delimiter: Optional custom delimiter
            
        Returns:
            Processed text
        """
        match operation:
            case SplitJoinOperation.SPLIT_BY_COMMA:
                return TextCleaner.split_to_lines(text, ',')
            case SplitJoinOperation.SPLIT_BY_SEMICOLON:
                return TextCleaner.split_to_lines(text, ';')
            case SplitJoinOperation.SPLIT_BY_TAB:
                return TextCleaner.split_to_lines(text, '\t')
            case SplitJoinOperation.SPLIT_BY_SPACE:
                return TextCleaner.split_to_lines(text, ' ')
            case SplitJoinOperation.SPLIT_BY_NEWLINE:
                return text  # Already split by newlines
            case SplitJoinOperation.JOIN_WITH_COMMA:
                return TextCleaner.join_lines(text, ', ')
            case SplitJoinOperation.JOIN_WITH_SEMICOLON:
                return TextCleaner.join_lines(text, '; ')
            case SplitJoinOperation.JOIN_WITH_TAB:
                return TextCleaner.join_lines(text, '\t')
            case SplitJoinOperation.JOIN_WITH_SPACE:
                return TextCleaner.join_lines(text, ' ')
            case SplitJoinOperation.JOIN_WITH_NEWLINE:
                return text  # Already joined by newlines
            case SplitJoinOperation.JOIN_LINES_COMMA:
                return TextCleaner.join_lines(text, ', ')
            case SplitJoinOperation.JOIN_LINES_SPACE:
                return TextCleaner.join_lines(text, ' ')
            case _:
                return text
    
    @staticmethod
    def split_to_lines(text: str, delimiter: str) -> str:
        """
        Split text by delimiter and put each part on a new line.
        
        Args:
            text: Input text
            delimiter: Delimiter to split on
            
        Returns:
            Text with parts on separate lines
        """
        parts = text.split(delimiter)
        # Strip whitespace from each part
        parts = [part.strip() for part in parts if part.strip()]
        return '\n'.join(parts)
    
    @staticmethod
    def join_lines(text: str, delimiter: str) -> str:
        """
        Join lines with specified delimiter.
        
        Args:
            text: Input text (multiline)
            delimiter: Delimiter to join with
            
        Returns:
            Single line with parts joined
        """
        lines = text.splitlines()
        # Strip whitespace from each line
        lines = [line.strip() for line in lines if line.strip()]
        return delimiter.join(lines)
    
    @staticmethod
    def split_into_chunks(text: str, chunk_size: int) -> str:
        """
        Split text into chunks of specified size.
        
        Args:
            text: Input text
            chunk_size: Number of characters per chunk
            
        Returns:
            Text split into chunks on separate lines
        """
        if chunk_size <= 0:
            return text
        
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        return '\n'.join(chunks)
    
    @staticmethod
    def wrap_text(text: str, width: int = 80) -> str:
        """
        Wrap text to specified width.
        
        Args:
            text: Input text
            width: Maximum line width
            
        Returns:
            Wrapped text
        """
        import textwrap
        return textwrap.fill(text, width=width)
    
    @staticmethod
    def unwrap_text(text: str) -> str:
        """
        Unwrap text by joining lines within paragraphs.
        
        Paragraphs are separated by blank lines.
        
        Args:
            text: Input wrapped text
            
        Returns:
            Unwrapped text
        """
        paragraphs = text.split('\n\n')
        unwrapped = []
        for para in paragraphs:
            # Join lines within paragraph
            lines = para.splitlines()
            unwrapped.append(' '.join(line.strip() for line in lines if line.strip()))
        return '\n\n'.join(unwrapped)
    
    # ==================== UTILITY METHODS ====================
    
    @staticmethod
    def get_cleanup_operations() -> list[str]:
        """
        Get list of available cleanup operations.
        
        Returns:
            List of operation display names
        """
        return [op.value for op in CleanupOperation]
    
    @staticmethod
    def get_split_join_operations() -> list[str]:
        """
        Get list of available split/join operations.
        
        Returns:
            List of operation display names
        """
        return [op.value for op in SplitJoinOperation]
    
    @staticmethod
    def apply_multiple_cleanups(text: str, operations: list[str]) -> str:
        """
        Apply multiple cleanup operations in sequence.
        
        Args:
            text: Input text
            operations: List of CleanupOperation values
            
        Returns:
            Text after all operations applied
        """
        result = text
        for op in operations:
            result = TextCleaner.cleanup(result, op)
        return result