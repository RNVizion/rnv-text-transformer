"""
tests/test_properties.py
========================
Phase 5 — Property-based tests using hypothesis.

Hypothesis generates 100 random-but-shrinkable inputs per property by default.
When a property fails, hypothesis shrinks the failing input down to a minimal
counter-example. This catches edge-case bugs the example-based tests miss.

Targets:
  TextTransformer    (core/text_transformer.py)
  TextCleaner        (core/text_cleaner.py)
  DiffEngine         (core/diff_engine.py)
  TextStatistics     (core/text_statistics.py)

Property categories:
  - Idempotence:    f(f(x)) == f(x)
  - Self-inverse:   f(f(x)) == x  (only for true involutions)
  - Length / membership invariants
  - Symmetry:       f(x, y) == f(y, x)
  - Identity:       f(x, x) == known constant
  - Bounded output: 0 <= result <= 1, or "all chars are printable", etc.
"""
from __future__ import annotations

import string

from hypothesis import given, settings, strategies as st

from core.text_transformer import TextTransformer
from core.text_cleaner import TextCleaner, CleanupOperation
from core.diff_engine import DiffEngine, ChangeType
from core.text_statistics import TextStatistics, TextStats


# ── Hypothesis strategies ──────────────────────────────────────────────────────
# Defined locally rather than imported from tests.conftest because
# `from tests.conftest import ...` is unreliable across pytest/Python/OS
# combinations (works on Linux Python 3.12, fails on Windows Python 3.13).
# These are simple enough that a single-file definition is the right choice.

# ASCII-only text. Used for properties that don't hold under Unicode case
# folding (e.g. swapcase is not involutive on ß or ligatures).
ASCII_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " \t\n.,!?",
    max_size=200,
)

# Text from any printable Unicode. Default for most properties.
# Excludes:
#   - Cs (surrogate code points): not valid in well-formed UTF-8
#   - \x00 (null byte): rejected by Windows file paths and other I/O
PRINTABLE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),
        blacklist_characters="\x00",
    ),
    max_size=200,
)


# Reasonable per-property example budget. 100 is hypothesis's default. We
# bump to 200 for the cheap pure-string properties to get more coverage of
# edge cases without slowing the suite.
_DEFAULT_EXAMPLES = 100
_FAST_PROPERTY = settings(max_examples=200, deadline=2000)
_NORMAL_PROPERTY = settings(max_examples=_DEFAULT_EXAMPLES, deadline=2000)


# ════════════════════════════════════════════════════════════════════════════
# 1. TextTransformer — 7 properties
# ════════════════════════════════════════════════════════════════════════════

class TestTextTransformerProperties:
    """
    Properties for the case-conversion engine. Most properties hold for
    ALL inputs; a few require ASCII due to Unicode case-folding edge cases
    like ß → SS (which is not invertible).
    """

    @given(text=PRINTABLE_TEXT)
    @_FAST_PROPERTY
    def test_uppercase_idempotent(self, text):
        """upper(upper(x)) == upper(x)."""
        once = TextTransformer.transform_text(text, "UPPERCASE")
        twice = TextTransformer.transform_text(once, "UPPERCASE")
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_FAST_PROPERTY
    def test_lowercase_idempotent(self, text):
        """lower(lower(x)) == lower(x)."""
        once = TextTransformer.transform_text(text, "lowercase")
        twice = TextTransformer.transform_text(once, "lowercase")
        assert once == twice

    @given(text=ASCII_TEXT)
    @_NORMAL_PROPERTY
    def test_uppercase_then_lowercase_equals_lowercase_for_ascii(self, text):
        """
        lower(upper(x)) == lower(x) for ASCII text.

        This does NOT hold for arbitrary Unicode because of edge cases like
        ß → SS where upper() expands the string. Restricted to ASCII.
        """
        upper_then_lower = TextTransformer.transform_text(
            TextTransformer.transform_text(text, "UPPERCASE"), "lowercase"
        )
        just_lower = TextTransformer.transform_text(text, "lowercase")
        assert upper_then_lower == just_lower

    @given(text=ASCII_TEXT)
    @_NORMAL_PROPERTY
    def test_inverted_case_self_inverse_for_ascii(self, text):
        """
        inverted(inverted(x)) == x for ASCII text.

        ASCII letters are perfectly involutive under swapcase. Non-ASCII like
        ß or ﬃ break this — `swapcase` expands them, e.g. ß → SS → ss.
        """
        once = TextTransformer.transform_text(text, "iNVERTED cASE")
        twice = TextTransformer.transform_text(once, "iNVERTED cASE")
        assert twice == text

    @given(text=ASCII_TEXT)
    @_NORMAL_PROPERTY
    def test_uppercase_preserves_length_for_ascii(self, text):
        """len(upper(x)) == len(x) for ASCII. Catches char-dropping bugs."""
        upper = TextTransformer.transform_text(text, "UPPERCASE")
        assert len(upper) == len(text)

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_unknown_mode_preserves_text(self, text):
        """Unknown mode returns the input unchanged (safe-fallback behavior)."""
        result = TextTransformer.transform_text(text, "ThisIsNotARealMode_XYZ")
        assert result == text

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_snake_case_idempotent_on_already_converted(self, text):
        """
        snake_case(snake_case(x)) == snake_case(x).

        Once converted, the output is already in snake_case form, so a second
        application should be a no-op. Same principle for any case-conversion
        mode — converting twice should equal converting once.
        """
        once = TextTransformer.transform_text(text, "snake_case")
        twice = TextTransformer.transform_text(once, "snake_case")
        assert once == twice


# ════════════════════════════════════════════════════════════════════════════
# 2. TextCleaner — 7 properties (all idempotence)
# ════════════════════════════════════════════════════════════════════════════

class TestTextCleanerProperties:
    """
    Cleanup operations should be idempotent — applying them twice produces
    the same result as applying once. This is the core safety guarantee.
    """

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_trim_whitespace_idempotent(self, text):
        once = TextCleaner.cleanup(text, CleanupOperation.TRIM_WHITESPACE)
        twice = TextCleaner.cleanup(once, CleanupOperation.TRIM_WHITESPACE)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_extra_spaces_idempotent(self, text):
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_EXTRA_SPACES)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_EXTRA_SPACES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_all_blank_lines_idempotent(self, text):
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_ALL_BLANK_LINES)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_ALL_BLANK_LINES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_duplicate_lines_idempotent(self, text):
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_DUPLICATE_LINES)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_DUPLICATE_LINES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_sort_lines_idempotent(self, text):
        once = TextCleaner.cleanup(text, CleanupOperation.SORT_LINES)
        twice = TextCleaner.cleanup(once, CleanupOperation.SORT_LINES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_sort_lines_reverse_idempotent(self, text):
        """Phase 6 regression guard — same trailing-separator bug pattern."""
        once = TextCleaner.cleanup(text, CleanupOperation.SORT_LINES_REVERSE)
        twice = TextCleaner.cleanup(once, CleanupOperation.SORT_LINES_REVERSE)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_leading_spaces_idempotent(self, text):
        """Phase 6 regression guard — same trailing-separator bug pattern."""
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_LEADING_SPACES)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_LEADING_SPACES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_trailing_spaces_idempotent(self, text):
        """Phase 6 regression guard — same trailing-separator bug pattern."""
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_TRAILING_SPACES)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_TRAILING_SPACES)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_normalize_unicode_idempotent(self, text):
        """NFC normalization is idempotent by Unicode standard."""
        once = TextCleaner.cleanup(text, CleanupOperation.NORMALIZE_UNICODE)
        twice = TextCleaner.cleanup(once, CleanupOperation.NORMALIZE_UNICODE)
        assert once == twice

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_remove_non_printable_idempotent(self, text):
        """Removing non-printable chars twice == once."""
        once = TextCleaner.cleanup(text, CleanupOperation.REMOVE_NON_PRINTABLE)
        twice = TextCleaner.cleanup(once, CleanupOperation.REMOVE_NON_PRINTABLE)
        assert once == twice


# ════════════════════════════════════════════════════════════════════════════
# 3. DiffEngine — 5 properties
# ════════════════════════════════════════════════════════════════════════════

class TestDiffEngineProperties:
    """Properties that must hold for any pair of inputs to the diff engine."""

    @given(text=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_diff_self_has_only_equal_changes(self, text):
        """
        compute_diff(x, x) produces only EQUAL changes — never INSERT, DELETE,
        or REPLACE. Identity comparison must produce identity diff.
        """
        result = DiffEngine.compute_diff(text, text)
        for change in result.changes:
            assert change.change_type == ChangeType.EQUAL

    @given(text=st.text(min_size=1, max_size=200))
    @_NORMAL_PROPERTY
    def test_similarity_of_self_is_one_for_nonempty(self, text):
        """compute_similarity(x, x) == 1.0 for non-empty x."""
        ratio = DiffEngine.compute_similarity(text, text)
        assert ratio == 1.0

    @given(left=PRINTABLE_TEXT, right=PRINTABLE_TEXT)
    @_NORMAL_PROPERTY
    def test_similarity_is_bounded_zero_to_one(self, left, right):
        """0.0 <= compute_similarity(x, y) <= 1.0 for any pair."""
        ratio = DiffEngine.compute_similarity(left, right)
        assert 0.0 <= ratio <= 1.0

    # NOTE: A symmetry property (compute_similarity(x, y) == compute_similarity(y, x))
    # was originally proposed but removed after sandbox validation revealed that
    # Python's difflib.SequenceMatcher.ratio() is documented as non-symmetric.
    # Example: ratio("21", "1201") = 0.667 but ratio("1201", "21") = 0.333.
    # Since DiffEngine.compute_similarity delegates to SequenceMatcher, it
    # inherits this asymmetry. This is documented difflib behavior, not a bug.

    @given(text=st.text(min_size=1, max_size=200))
    @_NORMAL_PROPERTY
    def test_similarity_one_empty_one_nonempty_is_zero(self, text):
        """compute_similarity(x, '') == 0.0 for non-empty x."""
        ratio_first_empty = DiffEngine.compute_similarity("", text)
        ratio_second_empty = DiffEngine.compute_similarity(text, "")
        assert ratio_first_empty == 0.0
        assert ratio_second_empty == 0.0


# ════════════════════════════════════════════════════════════════════════════
# 4. TextStatistics — 3 properties
# ════════════════════════════════════════════════════════════════════════════

class TestTextStatisticsProperties:
    """Properties for the statistics calculator."""

    @given(text=PRINTABLE_TEXT)
    @_FAST_PROPERTY
    def test_characters_equals_len(self, text):
        """characters count must equal len(text) by definition."""
        stats = TextStatistics.calculate(text)
        assert stats.characters == len(text)

    @given(text=PRINTABLE_TEXT)
    @_FAST_PROPERTY
    def test_characters_no_spaces_le_characters(self, text):
        """
        characters_no_spaces <= characters.

        Removing whitespace can only shrink the character count, never grow it.
        """
        stats = TextStatistics.calculate(text)
        assert stats.characters_no_spaces <= stats.characters

    def test_empty_string_returns_all_zeros(self):
        """calculate('') returns all-zero TextStats."""
        stats = TextStatistics.calculate("")
        assert stats == TextStats(
            characters=0,
            characters_no_spaces=0,
            words=0,
            lines=0,
            paragraphs=0,
        )
