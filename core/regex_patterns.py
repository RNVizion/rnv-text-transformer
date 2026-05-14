"""
RNV Text Transformer - Regex Patterns Module
Common regex patterns library for the Regex Builder

Python 3.13 Optimized:
- Pre-compiled patterns for performance
- Organized by category
- Pattern metadata for UI display

"""

from __future__ import annotations

import re
from typing import ClassVar, Pattern, NamedTuple
from dataclasses import dataclass

from utils.logger import get_module_logger

_logger = get_module_logger("RegexPatterns")


class PatternInfo(NamedTuple):
    """Information about a regex pattern."""
    name: str
    pattern: str
    description: str
    example_match: str
    category: str
    flags: int = 0


@dataclass
class PatternMatch:
    """Result of a pattern match."""
    start: int
    end: int
    text: str
    groups: tuple[str, ...]
    group_dict: dict[str, str]


class RegexPatterns:
    """
    Library of common regex patterns organized by category.
    
    Categories:
    - Web: URLs, emails, domains
    - Identity: Phone numbers, SSN, addresses
    - Data: Numbers, dates, times
    - Code: Variables, strings, comments
    - Text: Words, sentences, whitespace
    """
    
    # ==================== WEB PATTERNS ====================
    
    EMAIL = PatternInfo(
        name="Email Address",
        pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        description="Matches standard email addresses",
        example_match="user@example.com",
        category="Web"
    )
    
    URL = PatternInfo(
        name="URL",
        pattern=r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        description="Matches HTTP/HTTPS URLs",
        example_match="https://www.example.com/path?query=1",
        category="Web"
    )
    
    DOMAIN = PatternInfo(
        name="Domain Name",
        pattern=r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
        description="Matches domain names",
        example_match="www.example.com",
        category="Web"
    )
    
    IP_ADDRESS = PatternInfo(
        name="IPv4 Address",
        pattern=r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        description="Matches IPv4 addresses",
        example_match="192.168.1.1",
        category="Web"
    )
    
    IPV6_ADDRESS = PatternInfo(
        name="IPv6 Address",
        pattern=r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}",
        description="Matches IPv6 addresses",
        example_match="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        category="Web"
    )
    
    # ==================== IDENTITY PATTERNS ====================
    
    US_PHONE = PatternInfo(
        name="US Phone Number",
        pattern=r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        description="Matches US phone numbers in various formats",
        example_match="(555) 123-4567",
        category="Identity"
    )
    
    INTL_PHONE = PatternInfo(
        name="International Phone",
        pattern=r"\+?[0-9]{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        description="Matches international phone numbers",
        example_match="+44 20 7946 0958",
        category="Identity"
    )
    
    US_SSN = PatternInfo(
        name="US Social Security Number",
        pattern=r"\b\d{3}-\d{2}-\d{4}\b",
        description="Matches US SSN format (XXX-XX-XXXX)",
        example_match="123-45-6789",
        category="Identity"
    )
    
    US_ZIP = PatternInfo(
        name="US ZIP Code",
        pattern=r"\b\d{5}(?:-\d{4})?\b",
        description="Matches US ZIP codes (5 or 9 digit)",
        example_match="12345-6789",
        category="Identity"
    )
    
    CREDIT_CARD = PatternInfo(
        name="Credit Card Number",
        pattern=r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        description="Matches credit card numbers (with/without separators)",
        example_match="4111-1111-1111-1111",
        category="Identity"
    )
    
    # ==================== DATA PATTERNS ====================
    
    INTEGER = PatternInfo(
        name="Integer",
        pattern=r"-?\b\d+\b",
        description="Matches positive and negative integers",
        example_match="-42",
        category="Data"
    )
    
    DECIMAL = PatternInfo(
        name="Decimal Number",
        pattern=r"-?\b\d+\.\d+\b",
        description="Matches decimal numbers",
        example_match="3.14159",
        category="Data"
    )
    
    SCIENTIFIC = PatternInfo(
        name="Scientific Notation",
        pattern=r"-?\d+\.?\d*[eE][+-]?\d+",
        description="Matches numbers in scientific notation",
        example_match="6.022e23",
        category="Data"
    )
    
    PERCENTAGE = PatternInfo(
        name="Percentage",
        pattern=r"-?\d+(?:\.\d+)?%",
        description="Matches percentage values",
        example_match="99.9%",
        category="Data"
    )
    
    CURRENCY_USD = PatternInfo(
        name="USD Currency",
        pattern=r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
        description="Matches US dollar amounts",
        example_match="$1,234.56",
        category="Data"
    )
    
    HEX_COLOR = PatternInfo(
        name="Hex Color",
        pattern=r"#(?:[0-9a-fA-F]{3}){1,2}\b",
        description="Matches hex color codes",
        example_match="#FF5733",
        category="Data"
    )
    
    # ==================== DATE/TIME PATTERNS ====================
    
    DATE_ISO = PatternInfo(
        name="ISO Date (YYYY-MM-DD)",
        pattern=r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b",
        description="Matches ISO 8601 date format",
        example_match="2024-12-31",
        category="Date/Time"
    )
    
    DATE_US = PatternInfo(
        name="US Date (MM/DD/YYYY)",
        pattern=r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/\d{4}\b",
        description="Matches US date format",
        example_match="12/31/2024",
        category="Date/Time"
    )
    
    DATE_EU = PatternInfo(
        name="EU Date (DD/MM/YYYY)",
        pattern=r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])/\d{4}\b",
        description="Matches European date format",
        example_match="31/12/2024",
        category="Date/Time"
    )
    
    TIME_24H = PatternInfo(
        name="24-Hour Time",
        pattern=r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b",
        description="Matches 24-hour time format",
        example_match="23:59:59",
        category="Date/Time"
    )
    
    TIME_12H = PatternInfo(
        name="12-Hour Time",
        pattern=r"\b(?:0?[1-9]|1[0-2]):[0-5]\d(?::[0-5]\d)?\s*[AaPp][Mm]\b",
        description="Matches 12-hour time with AM/PM",
        example_match="11:59 PM",
        category="Date/Time"
    )
    
    TIMESTAMP_ISO = PatternInfo(
        name="ISO Timestamp",
        pattern=r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
        description="Matches ISO 8601 timestamps",
        example_match="2024-12-31T23:59:59Z",
        category="Date/Time"
    )
    
    # ==================== CODE PATTERNS ====================
    
    VARIABLE_CAMEL = PatternInfo(
        name="camelCase Variable",
        pattern=r"\b[a-z][a-zA-Z0-9]*\b",
        description="Matches camelCase identifiers",
        example_match="myVariableName",
        category="Code"
    )
    
    VARIABLE_SNAKE = PatternInfo(
        name="snake_case Variable",
        pattern=r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b",
        description="Matches snake_case identifiers",
        example_match="my_variable_name",
        category="Code"
    )
    
    VARIABLE_PASCAL = PatternInfo(
        name="PascalCase Variable",
        pattern=r"\b[A-Z][a-zA-Z0-9]*\b",
        description="Matches PascalCase identifiers",
        example_match="MyClassName",
        category="Code"
    )
    
    CONSTANT = PatternInfo(
        name="CONSTANT_CASE",
        pattern=r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\b",
        description="Matches CONSTANT_CASE identifiers",
        example_match="MAX_VALUE",
        category="Code"
    )
    
    STRING_DOUBLE = PatternInfo(
        name="Double-Quoted String",
        pattern=r'"(?:[^"\\]|\\.)*"',
        description="Matches double-quoted strings with escapes",
        example_match='"Hello, World!"',
        category="Code"
    )
    
    STRING_SINGLE = PatternInfo(
        name="Single-Quoted String",
        pattern=r"'(?:[^'\\]|\\.)*'",
        description="Matches single-quoted strings with escapes",
        example_match="'Hello'",
        category="Code"
    )
    
    COMMENT_LINE = PatternInfo(
        name="Line Comment (// or #)",
        pattern=r"(?://|#).*$",
        description="Matches single-line comments",
        example_match="// This is a comment",
        category="Code",
        flags=re.MULTILINE
    )
    
    COMMENT_BLOCK = PatternInfo(
        name="Block Comment (/* */)",
        pattern=r"/\*[\s\S]*?\*/",
        description="Matches block comments",
        example_match="/* multi\nline */",
        category="Code"
    )
    
    # ==================== TEXT PATTERNS ====================
    
    WORD = PatternInfo(
        name="Word",
        pattern=r"\b\w+\b",
        description="Matches individual words",
        example_match="Hello",
        category="Text"
    )
    
    WORD_CAPITALIZED = PatternInfo(
        name="Capitalized Word",
        pattern=r"\b[A-Z][a-z]*\b",
        description="Matches words starting with uppercase",
        example_match="Hello",
        category="Text"
    )
    
    SENTENCE = PatternInfo(
        name="Sentence",
        pattern=r"[A-Z][^.!?]*[.!?]",
        description="Matches sentences ending with punctuation",
        example_match="This is a sentence.",
        category="Text"
    )
    
    WHITESPACE_EXCESS = PatternInfo(
        name="Excess Whitespace",
        pattern=r"[ \t]{2,}",
        description="Matches multiple consecutive spaces/tabs",
        example_match="   ",
        category="Text"
    )
    
    BLANK_LINES = PatternInfo(
        name="Blank Lines",
        pattern=r"\n\s*\n",
        description="Matches blank lines",
        example_match="\n\n",
        category="Text"
    )
    
    LEADING_WHITESPACE = PatternInfo(
        name="Leading Whitespace",
        pattern=r"^[ \t]+",
        description="Matches whitespace at start of lines",
        example_match="    ",
        category="Text",
        flags=re.MULTILINE
    )
    
    TRAILING_WHITESPACE = PatternInfo(
        name="Trailing Whitespace",
        pattern=r"[ \t]+$",
        description="Matches whitespace at end of lines",
        example_match="    ",
        category="Text",
        flags=re.MULTILINE
    )
    
    # ==================== HTML/XML PATTERNS ====================
    
    HTML_TAG = PatternInfo(
        name="HTML Tag",
        pattern=r"<[^>]+>",
        description="Matches HTML/XML tags",
        example_match="<div class='test'>",
        category="Markup"
    )
    
    HTML_COMMENT = PatternInfo(
        name="HTML Comment",
        pattern=r"<!--[\s\S]*?-->",
        description="Matches HTML comments",
        example_match="<!-- comment -->",
        category="Markup"
    )
    
    HTML_ENTITY = PatternInfo(
        name="HTML Entity",
        pattern=r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);",
        description="Matches HTML entities",
        example_match="&amp;",
        category="Markup"
    )
    
    # Pattern dictionary for easy lookup by name
    _ALL_PATTERNS: ClassVar[dict[str, PatternInfo]] = {}
    
    @classmethod
    def get_all_patterns(cls) -> dict[str, PatternInfo]:
        """Get all patterns as a dictionary."""
        if not cls._ALL_PATTERNS:
            # Build from class attributes
            for name in dir(cls):
                attr = getattr(cls, name)
                if isinstance(attr, PatternInfo):
                    cls._ALL_PATTERNS[name] = attr
        return cls._ALL_PATTERNS
    
    @classmethod
    def get_patterns_by_category(cls) -> dict[str, list[PatternInfo]]:
        """Get patterns organized by category."""
        patterns = cls.get_all_patterns()
        by_category: dict[str, list[PatternInfo]] = {}
        
        for pattern_info in patterns.values():
            category = pattern_info.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pattern_info)
        
        # Sort patterns within each category
        for category in by_category:
            by_category[category].sort(key=lambda p: p.name)
        
        return by_category
    
    @classmethod
    def get_categories(cls) -> list[str]:
        """Get list of all categories."""
        patterns = cls.get_all_patterns()
        categories = sorted(set(p.category for p in patterns.values()))
        return categories
    
    @classmethod
    def get_pattern_by_name(cls, name: str) -> PatternInfo | None:
        """Get a pattern by its attribute name."""
        patterns = cls.get_all_patterns()
        return patterns.get(name)
    
    @classmethod
    def compile_pattern(cls, pattern_info: PatternInfo) -> Pattern[str]:
        """Compile a pattern with its flags."""
        return re.compile(pattern_info.pattern, pattern_info.flags)


class RegexHelper:
    """
    Helper class for regex operations.
    
    Provides methods for matching, replacing, and analyzing patterns.
    """
    
    @staticmethod
    def find_all_matches(
        text: str,
        pattern: str,
        flags: int = 0
    ) -> list[PatternMatch]:
        """
        Find all matches of a pattern in text.
        
        Args:
            text: Text to search
            pattern: Regex pattern
            flags: Regex flags
            
        Returns:
            List of PatternMatch objects
        """
        try:
            compiled = re.compile(pattern, flags)
            matches: list[PatternMatch] = []
            
            for match in compiled.finditer(text):
                matches.append(PatternMatch(
                    start=match.start(),
                    end=match.end(),
                    text=match.group(),
                    groups=match.groups(),
                    group_dict=match.groupdict() if match.groupdict() else {}
                ))
            
            return matches
            
        except re.error as e:
            if _logger:
                _logger.warning(f"Regex find_all error: {pattern}", details=str(e))
            return []
    
    @staticmethod
    def replace_all(
        text: str,
        pattern: str,
        replacement: str,
        flags: int = 0
    ) -> tuple[str, int]:
        """
        Replace all matches of a pattern.
        
        Args:
            text: Text to modify
            pattern: Regex pattern
            replacement: Replacement string (supports backreferences)
            flags: Regex flags
            
        Returns:
            Tuple of (modified_text, count)
        """
        try:
            compiled = re.compile(pattern, flags)
            result, count = compiled.subn(replacement, text)
            return result, count
        except re.error as e:
            if _logger:
                _logger.warning(f"Regex replace_all error: {pattern}", details=str(e))
            return text, 0
    
    @staticmethod
    def validate_pattern(pattern: str, flags: int = 0) -> tuple[bool, str]:
        """
        Validate a regex pattern.
        
        Args:
            pattern: Pattern to validate
            flags: Regex flags
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pattern:
            return False, "Pattern is empty"
        
        try:
            re.compile(pattern, flags)
            return True, ""
        except re.error as e:
            return False, str(e)
    
    @staticmethod
    def escape_pattern(text: str) -> str:
        """
        Escape special regex characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for literal matching
        """
        return re.escape(text)
    
    @staticmethod
    def get_flags_from_options(
        case_insensitive: bool = False,
        multiline: bool = False,
        dotall: bool = False,
        verbose: bool = False
    ) -> int:
        """
        Build regex flags from options.
        
        Args:
            case_insensitive: IGNORECASE flag
            multiline: MULTILINE flag
            dotall: DOTALL flag
            verbose: VERBOSE flag
            
        Returns:
            Combined flags integer
        """
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        if verbose:
            flags |= re.VERBOSE
        return flags
    
    @staticmethod
    def explain_flags(flags: int) -> list[str]:
        """
        Explain what flags are set.
        
        Args:
            flags: Combined flags integer
            
        Returns:
            List of flag descriptions
        """
        descriptions: list[str] = []
        
        if flags & re.IGNORECASE:
            descriptions.append("Case-insensitive matching")
        if flags & re.MULTILINE:
            descriptions.append("^ and $ match start/end of lines")
        if flags & re.DOTALL:
            descriptions.append(". matches newlines")
        if flags & re.VERBOSE:
            descriptions.append("Allow whitespace and comments")
        
        return descriptions if descriptions else ["No special flags"]
