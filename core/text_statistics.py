"""
RNV Text Transformer - Text Statistics Module
Calculates text statistics for display

Python 3.13 Optimized:
- Modern type hints
- Pre-compiled regex patterns for performance
- Efficient single-pass calculations where possible

"""

from __future__ import annotations

import re
from typing import ClassVar, Pattern, NamedTuple


class TextStats(NamedTuple):
    """Container for text statistics."""
    characters: int
    characters_no_spaces: int
    words: int
    lines: int
    paragraphs: int


class TextStatistics:
    """
    Calculates various statistics for text content.
    
    Uses pre-compiled patterns for optimal performance on large texts.
    """
    
    __slots__ = ()  # No instance attributes needed
    
    # Pre-compiled regex patterns
    _WORD_PATTERN: ClassVar[Pattern[str]] = re.compile(r'\b\w+\b')
    _PARAGRAPH_PATTERN: ClassVar[Pattern[str]] = re.compile(r'\n\s*\n')
    _WHITESPACE_PATTERN: ClassVar[Pattern[str]] = re.compile(r'\s')
    
    @classmethod
    def calculate(cls, text: str) -> TextStats:
        """
        Calculate all statistics for the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            TextStats named tuple with all statistics
        """
        if not text:
            return TextStats(
                characters=0,
                characters_no_spaces=0,
                words=0,
                lines=0,
                paragraphs=0
            )
        
        # Character counts
        characters = len(text)
        characters_no_spaces = len(cls._WHITESPACE_PATTERN.sub('', text))
        
        # Word count
        words = len(cls._WORD_PATTERN.findall(text))
        
        # Line count (number of newlines + 1, or 0 for empty)
        lines = text.count('\n') + 1 if text else 0
        
        # Paragraph count (separated by blank lines)
        paragraphs = cls._count_paragraphs(text)
        
        return TextStats(
            characters=characters,
            characters_no_spaces=characters_no_spaces,
            words=words,
            lines=lines,
            paragraphs=paragraphs
        )
    
    @classmethod
    def _count_paragraphs(cls, text: str) -> int:
        """
        Count paragraphs in text.
        
        A paragraph is defined as text separated by one or more blank lines.
        
        Args:
            text: Input text
            
        Returns:
            Number of paragraphs
        """
        if not text or not text.strip():
            return 0
        
        # Split by blank lines (one or more empty lines)
        paragraphs = cls._PARAGRAPH_PATTERN.split(text)
        
        # Count non-empty paragraphs
        return sum(1 for p in paragraphs if p.strip())
    
    @classmethod
    def format_stats(cls, stats: TextStats, compact: bool = True) -> str:
        """
        Format statistics for display.
        
        Args:
            stats: TextStats to format
            compact: If True, use compact format; otherwise verbose
            
        Returns:
            Formatted string
        """
        if compact:
            return (
                f"{stats.characters:,} chars | "
                f"{stats.words:,} words | "
                f"{stats.lines:,} lines"
            )
        else:
            return (
                f"Characters: {stats.characters:,} ({stats.characters_no_spaces:,} without spaces)\n"
                f"Words: {stats.words:,}\n"
                f"Lines: {stats.lines:,}\n"
                f"Paragraphs: {stats.paragraphs:,}"
            )
    
    @classmethod
    def format_comparison(cls, input_stats: TextStats, output_stats: TextStats) -> str:
        """
        Format statistics comparison between input and output.
        
        Args:
            input_stats: Statistics for input text
            output_stats: Statistics for output text
            
        Returns:
            Formatted comparison string
        """
        return (
            f"Input:  {input_stats.characters:,} chars | "
            f"{input_stats.words:,} words | "
            f"{input_stats.lines:,} lines\n"
            f"Output: {output_stats.characters:,} chars | "
            f"{output_stats.words:,} words | "
            f"{output_stats.lines:,} lines"
        )
