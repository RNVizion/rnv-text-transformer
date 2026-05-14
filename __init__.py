"""
RNV Text Transformer

Python 3.13 Optimized

Version 3.1.0 - Phase 4 Consistency

Top-level project package. Re-exports the CLI entry points (main,
CLIProcessor) from the cli/ subpackage for convenient access via
`from RNV_Text_Transformer import main`.
"""

from __future__ import annotations

from .cli.rnv_transform import main, CLIProcessor

__all__ = [
    'main',
    'CLIProcessor',
]
