"""
RNV Text Transformer - Diff Engine Module
Advanced text diff and merge functionality.

Python 3.13 Optimized:
- Modern type hints with dataclasses
- Enum for change types
- Efficient line-based diff computation
- Multiple output formats (unified, HTML, side-by-side)

"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar
from html import escape as html_escape

from utils.dialog_styles import DialogStyleManager


class ChangeType(StrEnum):
    """Types of changes detected in diff."""
    EQUAL = "equal"         # Line unchanged
    INSERT = "insert"       # Line added in right/modified
    DELETE = "delete"       # Line removed from left/original
    REPLACE = "replace"     # Line modified (delete + insert pair)


@dataclass
class DiffChange:
    """
    Represents a single change in the diff.
    
    Attributes:
        change_type: Type of change (equal, insert, delete, replace)
        left_line_num: Line number in original text (None for inserts)
        right_line_num: Line number in modified text (None for deletes)
        left_text: Text from original (empty for inserts)
        right_text: Text from modified (empty for deletes)
        accepted: Whether this change has been accepted for merge
    """
    change_type: ChangeType
    left_line_num: int | None
    right_line_num: int | None
    left_text: str
    right_text: str
    accepted: bool | None = None  # None = not decided, True = accept, False = reject
    
    def is_change(self) -> bool:
        """Check if this represents an actual change (not equal)."""
        return self.change_type != ChangeType.EQUAL
    
    def get_display_text(self) -> str:
        """Get text for display purposes."""
        match self.change_type:
            case ChangeType.EQUAL:
                return self.left_text
            case ChangeType.INSERT:
                return f"+ {self.right_text}"
            case ChangeType.DELETE:
                return f"- {self.left_text}"
            case ChangeType.REPLACE:
                return f"- {self.left_text}\n+ {self.right_text}"
            case _:
                return ""
    
    def get_merged_text(self, use_modified: bool = True) -> str:
        """
        Get the text to use in merged result.
        
        Args:
            use_modified: If True, prefer modified text; else prefer original
            
        Returns:
            Text to include in merged output
        """
        # If explicitly accepted/rejected
        if self.accepted is True:
            # Accept the change (use modified/right version)
            if self.change_type == ChangeType.DELETE:
                return ""  # Delete accepted = line removed
            return self.right_text
        elif self.accepted is False:
            # Reject the change (keep original/left version)
            if self.change_type == ChangeType.INSERT:
                return ""  # Insert rejected = don't add line
            return self.left_text
        
        # Not yet decided - use default behavior
        match self.change_type:
            case ChangeType.EQUAL:
                return self.left_text
            case ChangeType.INSERT:
                return self.right_text if use_modified else ""
            case ChangeType.DELETE:
                return "" if use_modified else self.left_text
            case ChangeType.REPLACE:
                return self.right_text if use_modified else self.left_text
            case _:
                return ""


@dataclass
class DiffResult:
    """
    Complete diff result with all changes and statistics.
    
    Attributes:
        changes: List of all DiffChange objects
        left_text: Original text
        right_text: Modified text
    """
    changes: list[DiffChange] = field(default_factory=list)
    left_text: str = ""
    right_text: str = ""
    
    @property
    def total_changes(self) -> int:
        """Count of actual changes (non-equal lines)."""
        return sum(1 for c in self.changes if c.is_change())
    
    @property
    def insertions(self) -> int:
        """Count of inserted lines."""
        return sum(1 for c in self.changes if c.change_type == ChangeType.INSERT)
    
    @property
    def deletions(self) -> int:
        """Count of deleted lines."""
        return sum(1 for c in self.changes if c.change_type == ChangeType.DELETE)
    
    @property
    def replacements(self) -> int:
        """Count of replaced lines."""
        return sum(1 for c in self.changes if c.change_type == ChangeType.REPLACE)
    
    @property
    def accepted_count(self) -> int:
        """Count of accepted changes."""
        return sum(1 for c in self.changes if c.is_change() and c.accepted is True)
    
    @property
    def rejected_count(self) -> int:
        """Count of rejected changes."""
        return sum(1 for c in self.changes if c.is_change() and c.accepted is False)
    
    @property
    def pending_count(self) -> int:
        """Count of undecided changes."""
        return sum(1 for c in self.changes if c.is_change() and c.accepted is None)
    
    def get_change_indices(self) -> list[int]:
        """Get indices of actual changes (for navigation)."""
        return [i for i, c in enumerate(self.changes) if c.is_change()]
    
    def accept_change(self, index: int) -> bool:
        """Accept a change at given index."""
        if 0 <= index < len(self.changes) and self.changes[index].is_change():
            self.changes[index].accepted = True
            return True
        return False
    
    def reject_change(self, index: int) -> bool:
        """Reject a change at given index."""
        if 0 <= index < len(self.changes) and self.changes[index].is_change():
            self.changes[index].accepted = False
            return True
        return False
    
    def accept_all(self) -> None:
        """Accept all changes."""
        for change in self.changes:
            if change.is_change():
                change.accepted = True
    
    def reject_all(self) -> None:
        """Reject all changes."""
        for change in self.changes:
            if change.is_change():
                change.accepted = False
    
    def reset_all(self) -> None:
        """Reset all changes to undecided."""
        for change in self.changes:
            if change.is_change():
                change.accepted = None
    
    def get_merged_text(self, use_modified_for_pending: bool = True) -> str:
        """
        Generate merged text based on accept/reject decisions.
        
        Args:
            use_modified_for_pending: For undecided changes, use modified version
            
        Returns:
            Merged text string
        """
        lines: list[str] = []
        for change in self.changes:
            text = change.get_merged_text(use_modified_for_pending)
            if text:  # Don't add empty strings (deleted/rejected lines)
                lines.append(text)
        return '\n'.join(lines)


class DiffEngine:
    """
    Engine for computing text differences and generating various diff formats.
    
    Features:
    - Line-based diff computation
    - Structured change tracking
    - Unified diff format output
    - HTML diff output
    - Side-by-side text output
    - Merge conflict markers
    """
    
    _HTML_FOOTER: ClassVar[str] = """</body>
</html>
"""

    @classmethod
    def _get_html_header(cls, title: str = "Text Diff Report") -> str:
        """Build the HTML header block using colors from DialogStyleManager."""
        c = DialogStyleManager.LIGHT
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{html_escape(title)}</title>
<style>
body {{ font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; margin: 20px; }}
.diff-table {{ border-collapse: collapse; width: 100%; }}
.diff-table td {{ padding: 2px 8px; vertical-align: top; white-space: pre-wrap; word-wrap: break-word; }}
.diff-table .line-num {{ color: {c['diff_html_line_num']}; text-align: right; width: 40px; border-right: 1px solid {c['diff_html_border']}; }}
.diff-equal {{ background-color: {c['diff_html_equal_bg']}; }}
.diff-insert {{ background-color: {c['diff_html_insert_bg']}; }}
.diff-delete {{ background-color: {c['diff_html_delete_bg']}; }}
.diff-replace-left {{ background-color: {c['diff_html_delete_bg']}; }}
.diff-replace-right {{ background-color: {c['diff_html_insert_bg']}; }}
.header {{ background-color: {c['diff_html_header_bg']}; font-weight: bold; padding: 10px; margin-bottom: 10px; }}
.stats {{ margin-bottom: 20px; color: {c['diff_html_stats_text']}; }}
</style>
</head>
<body>
"""
    
    __slots__ = ()
    
    @staticmethod
    def compute_diff(left_text: str, right_text: str) -> DiffResult:
        """
        Compute line-by-line diff between two texts.
        
        Args:
            left_text: Original text
            right_text: Modified text
            
        Returns:
            DiffResult with all changes
        """
        result = DiffResult(left_text=left_text, right_text=right_text)
        
        # Split into lines (preserve line content without newlines for comparison)
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()
        
        # Use SequenceMatcher for efficient diff
        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            match tag:
                case 'equal':
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        result.changes.append(DiffChange(
                            change_type=ChangeType.EQUAL,
                            left_line_num=i + 1,
                            right_line_num=j + 1,
                            left_text=left_lines[i],
                            right_text=right_lines[j]
                        ))
                
                case 'replace':
                    # Handle replace as paired changes
                    left_count = i2 - i1
                    right_count = j2 - j1
                    
                    # Pair up lines where possible
                    for k in range(max(left_count, right_count)):
                        left_idx = i1 + k if k < left_count else None
                        right_idx = j1 + k if k < right_count else None
                        
                        if left_idx is not None and right_idx is not None:
                            # Both sides have a line - it's a replace
                            result.changes.append(DiffChange(
                                change_type=ChangeType.REPLACE,
                                left_line_num=left_idx + 1,
                                right_line_num=right_idx + 1,
                                left_text=left_lines[left_idx],
                                right_text=right_lines[right_idx]
                            ))
                        elif left_idx is not None:
                            # Only left side - it's a delete
                            result.changes.append(DiffChange(
                                change_type=ChangeType.DELETE,
                                left_line_num=left_idx + 1,
                                right_line_num=None,
                                left_text=left_lines[left_idx],
                                right_text=""
                            ))
                        else:
                            # Only right side - it's an insert
                            result.changes.append(DiffChange(
                                change_type=ChangeType.INSERT,
                                left_line_num=None,
                                right_line_num=right_idx + 1,
                                left_text="",
                                right_text=right_lines[right_idx]
                            ))
                
                case 'delete':
                    for i in range(i1, i2):
                        result.changes.append(DiffChange(
                            change_type=ChangeType.DELETE,
                            left_line_num=i + 1,
                            right_line_num=None,
                            left_text=left_lines[i],
                            right_text=""
                        ))
                
                case 'insert':
                    for j in range(j1, j2):
                        result.changes.append(DiffChange(
                            change_type=ChangeType.INSERT,
                            left_line_num=None,
                            right_line_num=j + 1,
                            left_text="",
                            right_text=right_lines[j]
                        ))
        
        return result
    
    @staticmethod
    def compute_unified_diff(
        left_text: str,
        right_text: str,
        left_label: str = "original",
        right_label: str = "modified",
        context_lines: int = 3
    ) -> str:
        """
        Generate unified diff format output.
        
        Args:
            left_text: Original text
            right_text: Modified text
            left_label: Label for original file
            right_label: Label for modified file
            context_lines: Number of context lines around changes
            
        Returns:
            Unified diff format string
        """
        left_lines = left_text.splitlines(keepends=True)
        right_lines = right_text.splitlines(keepends=True)
        
        # Ensure last lines have newlines for proper diff format
        if left_lines and not left_lines[-1].endswith('\n'):
            left_lines[-1] += '\n'
        if right_lines and not right_lines[-1].endswith('\n'):
            right_lines[-1] += '\n'
        
        diff = difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_label,
            tofile=right_label,
            n=context_lines
        )
        
        return ''.join(diff)
    
    @classmethod
    def compute_html_diff(
        cls,
        left_text: str,
        right_text: str,
        title: str = "Text Diff Report"
    ) -> str:
        """
        Generate HTML diff report.
        
        Args:
            left_text: Original text
            right_text: Modified text
            title: Report title
            
        Returns:
            Complete HTML document string
        """
        result = cls.compute_diff(left_text, right_text)

        html_parts = [cls._get_html_header(title)]
        
        # Header
        html_parts.append(f'<div class="header">{html_escape(title)}</div>')
        
        # Statistics
        html_parts.append(f'''<div class="stats">
Total changes: {result.total_changes} 
(+{result.insertions} insertions, -{result.deletions} deletions, ~{result.replacements} replacements)
</div>''')
        
        # Diff table
        html_parts.append('<table class="diff-table">')
        html_parts.append('<tr><th class="line-num">Left</th><th>Original</th>'
                         '<th class="line-num">Right</th><th>Modified</th></tr>')
        
        for change in result.changes:
            left_num = str(change.left_line_num) if change.left_line_num else ""
            right_num = str(change.right_line_num) if change.right_line_num else ""
            left_content = html_escape(change.left_text)
            right_content = html_escape(change.right_text)
            
            match change.change_type:
                case ChangeType.EQUAL:
                    row_class = "diff-equal"
                    html_parts.append(
                        f'<tr class="{row_class}">'
                        f'<td class="line-num">{left_num}</td>'
                        f'<td>{left_content}</td>'
                        f'<td class="line-num">{right_num}</td>'
                        f'<td>{right_content}</td>'
                        f'</tr>'
                    )
                case ChangeType.INSERT:
                    html_parts.append(
                        f'<tr class="diff-insert">'
                        f'<td class="line-num"></td>'
                        f'<td></td>'
                        f'<td class="line-num">{right_num}</td>'
                        f'<td>{right_content}</td>'
                        f'</tr>'
                    )
                case ChangeType.DELETE:
                    html_parts.append(
                        f'<tr class="diff-delete">'
                        f'<td class="line-num">{left_num}</td>'
                        f'<td>{left_content}</td>'
                        f'<td class="line-num"></td>'
                        f'<td></td>'
                        f'</tr>'
                    )
                case ChangeType.REPLACE:
                    html_parts.append(
                        f'<tr class="diff-replace-left">'
                        f'<td class="line-num">{left_num}</td>'
                        f'<td>{left_content}</td>'
                        f'<td class="line-num">{right_num}</td>'
                        f'<td class="diff-replace-right">{right_content}</td>'
                        f'</tr>'
                    )
        
        html_parts.append('</table>')
        html_parts.append(cls._HTML_FOOTER)
        
        return '\n'.join(html_parts)
    
    @staticmethod
    def compute_side_by_side(
        left_text: str,
        right_text: str,
        separator: str = " | ",
        line_width: int = 40
    ) -> str:
        """
        Generate side-by-side text diff.
        
        Args:
            left_text: Original text
            right_text: Modified text
            separator: Separator between columns
            line_width: Width of each column
            
        Returns:
            Side-by-side text representation
        """
        result = DiffEngine.compute_diff(left_text, right_text)
        lines: list[str] = []
        
        # Header
        left_header = "Original".center(line_width)
        right_header = "Modified".center(line_width)
        lines.append(f"{left_header}{separator}{right_header}")
        lines.append("-" * line_width + separator.replace(" ", "-") + "-" * line_width)
        
        for change in result.changes:
            left_content = change.left_text[:line_width].ljust(line_width)
            right_content = change.right_text[:line_width].ljust(line_width)
            
            # Add change indicator
            match change.change_type:
                case ChangeType.EQUAL:
                    indicator = "   "
                case ChangeType.INSERT:
                    indicator = " + "
                    left_content = " " * line_width
                case ChangeType.DELETE:
                    indicator = " - "
                    right_content = " " * line_width
                case ChangeType.REPLACE:
                    indicator = " ~ "
                case _:
                    indicator = "   "
            
            lines.append(f"{left_content}{indicator}{right_content}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate_conflict_markers(
        left_text: str,
        right_text: str,
        left_label: str = "ORIGINAL",
        right_label: str = "MODIFIED"
    ) -> str:
        """
        Generate text with Git-style conflict markers.
        
        Args:
            left_text: Original text
            right_text: Modified text
            left_label: Label for original version
            right_label: Label for modified version
            
        Returns:
            Text with conflict markers around differences
        """
        result = DiffEngine.compute_diff(left_text, right_text)
        output_lines: list[str] = []
        
        # Track consecutive changes for grouping
        i = 0
        while i < len(result.changes):
            change = result.changes[i]
            
            if change.change_type == ChangeType.EQUAL:
                output_lines.append(change.left_text)
                i += 1
            else:
                # Collect consecutive changes
                left_lines: list[str] = []
                right_lines: list[str] = []
                
                while i < len(result.changes) and result.changes[i].change_type != ChangeType.EQUAL:
                    c = result.changes[i]
                    if c.left_text:
                        left_lines.append(c.left_text)
                    if c.right_text:
                        right_lines.append(c.right_text)
                    i += 1
                
                # Output conflict block
                output_lines.append(f"<<<<<<< {left_label}")
                output_lines.extend(left_lines)
                output_lines.append("=======")
                output_lines.extend(right_lines)
                output_lines.append(f">>>>>>> {right_label}")
        
        return '\n'.join(output_lines)
    
    @staticmethod
    def compute_similarity(left_text: str, right_text: str) -> float:
        """
        Compute similarity ratio between two texts.
        
        Args:
            left_text: First text
            right_text: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        if not left_text and not right_text:
            return 1.0
        if not left_text or not right_text:
            return 0.0
        
        return difflib.SequenceMatcher(None, left_text, right_text).ratio()
    
    @staticmethod
    def get_change_summary(result: DiffResult) -> str:
        """
        Get a human-readable summary of changes.
        
        Args:
            result: DiffResult to summarize
            
        Returns:
            Summary string
        """
        parts = []
        
        if result.insertions > 0:
            parts.append(f"+{result.insertions} added")
        if result.deletions > 0:
            parts.append(f"-{result.deletions} removed")
        if result.replacements > 0:
            parts.append(f"~{result.replacements} modified")
        
        if not parts:
            return "No changes"
        
        return ", ".join(parts)
