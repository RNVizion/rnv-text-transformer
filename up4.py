"""every colour named, and every name used: the text transformer's unread palette keys and constants go

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-text-transformer, derived against a fresh clone at the live head (d101615 with up_tt_extra_selections.py, up_tt_find_target.py and up_tt_register_wiring.py applied).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-04, items 6 to 9 of decisions-pending-2026-09-29.md:

  "As long as a color exist in the app it should be named and used no
   hardcoded or pointless literals should exist, only literals with a
   purpose, like data or comparison are allowed. Colors are name for swap
   ability and alignment."

USED. One palette key no mode read goes from both palettes:
scrollbar_handle_hover. Every scroll bar's hover is painted from the mode's
accent; this key held the gold in dark and a grey in light, and no
stylesheet read it. Fifteen more were each read from one palette only, by
name. The diff export is a standalone page, always light, and reads its
seven diff_html_ keys from LIGHT; image mode reads its eight image_ overlay
keys from DARK. Each stays in the palette that is read and leaves the other,
where it was a copy nothing looked up. Three constants nothing in the
application read go: STATUS_SUCCESS, STATUS_WARNING and STATUS_ERROR, the
status family's fills. This application draws status as text.

NAMED. The grey of an exported PDF's footer was the colour name 'gray'; it
is SEMANTIC_EXPORT_FOOTER, at that value. The alpha of Find's highlight was
the number 80 where it is set; it is FIND_HIGHLIGHT_ALPHA.

THE ROOT SUITE. test_dark_and_light_have_same_keys required the palettes to
hold the same keys. It now states the fifteen by which they differ. Two
lists of required keys named the hover no stylesheet read. Ruled: "for the
locked key test if we don't use these values we Can fix the test and remove
unused values". Every test stays.

PROVEN BEFORE BUILDING. No line of the application looks up the hover key.
Every lookup of the fifteen is on the palette that keeps it, by name. And
every window, tab and combo in every mode draws what it drew.

This script builds on up_tt_extra_selections.py, up_tt_find_target.py and
up_tt_register_wiring.py, and refuses without them.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-text-transformer'
SENTINEL = 'RNV-NAMED-AND-USED'
SENTINEL_FILE = 'utils/colors.py'
GUARD = 'tests/test_named_and_used.py'
GUARD_FILES = ['tests/test_named_and_used.py', 'tests/test_derived_values.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_register_wiring.py', 'tests/test_snapshots.py', 'tests/test_status_family.py', 'tests/test_brand_mirror.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_named_and_used.py', 'tests/test_derived_values.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_register_wiring.py', 'tests/test_snapshots.py', 'tests/test_status_family.py', 'tests/test_brand_mirror.py']
DESCRIPTION = "every colour named, and every name used: the text transformer's unread palette keys and constants go"

_COV = [sys.executable, "-m", "coverage", "run", "--source=core,utils,ui,cli",
        "--branch"]
SUITES = [
    ("CI step 1: unittest test_rnv_text_transformer",
     _COV[:4] + ["--data-file=.coverage.unittest"] + _COV[4:]
     + ["-m", "unittest", "test_rnv_text_transformer"]),
    ("CI step 2: pytest tests/ --benchmark-disable",
     _COV[:4] + ["--data-file=.coverage.pytest"] + _COV[4:]
     + ["-m", "pytest", "tests/", "--benchmark-disable"]),
]

#: The environment the workflow sets for both steps.
CI_ENV = {"QT_QPA_PLATFORM": "offscreen"}


def post_write() -> None:
    """CI's environment: both test steps run with QT_QPA_PLATFORM=offscreen."""
    os.environ.update(CI_ENV)
    print("CI environment: " + ", ".join(f"{k}={v}" for k, v in CI_ENV.items()))

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests.yml': '22c4f261f69cda029e0801f148e9b061e3bd65b5c9472b1bf321fc998b5a0434'}

SHADOWS = {"colors.py", "conftest.py", "dialog_styles.py", "export_manager.py", "find_replace_dialog.py", "test_rnv_text_transformer.py"}

LEFT_ALONE = ['line_number_bg, line_number_fg, line_number_current_bg and line_number_current_fg: read only by a line-number gutter nothing in the application creates. They go only if that widget goes, which is a ruling of its own.', "the example the Hex Color pattern is shown with: text shown to the person, listed with its reason in the guard's DATA table.", "clear: 'transparent', alpha 0 and Qt's transparent are how a widget is told to paint nothing, and are left as written.", 'the stay-removed tests of earlier rounds: each restricts a name that was ruled away, and is not a list of what is unused.', "the register's three fills as VALUES in tests/test_status_family.py: what a status key must never be painted with, held there under the register's own names. A restriction, not a list of what is unused."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # This round builds on up_tt_extra_selections.py: its anchors are that round's text.
    # Without it they would all be "missing", which says the wrong thing.
    if 'RNV-EXTRA-SELECTIONS' not in tree.read('ui/base_dialog.py'):
        raise Stop("this round builds on up_tt_extra_selections.py, which has not been applied here: ui/base_dialog.py has no 'RNV-EXTRA-SELECTIONS'.\nRun that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    # This round builds on up_tt_find_target.py: its anchors are that round's text.
    # Without it they would all be "missing", which says the wrong thing.
    if 'RNV-FIND-TARGET' not in tree.read('ui/find_replace_dialog.py'):
        raise Stop("this round builds on up_tt_find_target.py, which has not been applied here: ui/find_replace_dialog.py has no 'RNV-FIND-TARGET'.\nRun that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    # This round builds on up_tt_register_wiring.py: its anchors are that round's text.
    # Without it they would all be "missing", which says the wrong thing.
    if 'RNV-REGISTER-WIRING-GUARD' not in tree.read('tests/test_tt_register.py'):
        raise Stop("this round builds on up_tt_register_wiring.py, which has not been applied here: tests/test_tt_register.py has no 'RNV-REGISTER-WIRING-GUARD'.\nRun that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tree.sub('utils/dialog_styles.py',
             "    DARK: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        'bg': BRAND_BLACK,\n        'bg_secondary': APP_CARD,\n        'bg_tertiary': APP_BORDER,\n        'bg_hover': APP_PANEL_HOVER,\n        \n        # Text\n        'text': APP_TEXT,\n        'text_muted': GREY_88,\n        'text_disabled': GREY_55,\n        \n        # Borders\n        'border': APP_BORDER,\n        'border_light': GREY_44,\n        'border_focus': BRAND_GOLD,\n        \n        # Accent colors\n        'accent': BRAND_GOLD,\n        'accent_hover': BRAND_GOLD_HOVER,\n        'accent_pressed': BRAND_GOLD_PRESSED,\n        'accent_ink': BRAND_GOLD,  # Accent when it carries text\n        'accent_text': TRUE_BLACK,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: these three keys are read in fourteen\n        # places and every one is a `color:` declaration, so they\n        # carry the TEXT variants rather than the fills. The fills\n        # sit at L* 48-59 and cannot reach 4.5:1 on either ground.\n        'success': STATUS_SUCCESS_TEXT,\n        'error': STATUS_ERROR_TEXT,\n        'warning': STATUS_WARNING_TEXT,\n        'info': BRAND_GOLD,\n        \n        # Special\n        'selection_bg': BRAND_GOLD,\n        'selection_text': TRUE_BLACK,\n        'scrollbar_bg': APP_CARD,\n        'scrollbar_handle': GREY_44,\n        'scrollbar_handle_hover': BRAND_GOLD,\n        'scrollbar_handle_main': GREY_44,\n        'tooltip_border': BRAND_GOLD,\n        \n        # Checkbox indicator\n        'checkbox_indicator_bg': BRAND_BLACK,\n        'checkbox_border': GREY_55,\n        \n        # Dropdown / list hover\n        'list_hover_bg': WHITE,\n        'list_hover_text': TRUE_BLACK,\n        \n        # MainWindow-specific (pure black background, distinct from dialog bg)\n        'window_bg': TRUE_BLACK,\n        'main_btn_bg': BRAND_BLACK,\n        'main_btn_text': APP_TEXT,\n        'main_btn_hover_bg': APP_BORDER,\n        'main_btn_pressed_bg': GREY_44,\n        'main_btn_pressed_text': TRUE_BLACK,\n        'input_bg': BRAND_BLACK,\n        'input_text': APP_TEXT,\n        'input_border': APP_BORDER,\n        'label_bg': TRUE_BLACK,\n        'label_text': APP_TEXT,\n        'output_text_color': BRAND_GOLD,\n        'border_color': APP_BORDER,\n        'text_color': APP_TEXT,\n        \n        # Line number gutter widget\n        'line_number_bg': BRAND_BLACK,\n        'line_number_fg': GREY_88,\n        'line_number_current_bg': APP_CARD,\n        'line_number_current_fg': BRAND_GOLD,\n\n        # Diff / compare semantic highlight colors\n        'diff_added_bg':   SEMANTIC_DIFF_ADDED,\n        'diff_removed_bg': SEMANTIC_DIFF_REMOVED,\n        'diff_changed_bg': SEMANTIC_DIFF_CHANGED,\n\n        # Diff HTML export colors (standalone document — always light-styled)\n        'diff_html_equal_bg':  WHITE,\n        'diff_html_insert_bg': SEMANTIC_DIFF_ADDED_LIGHT,\n        'diff_html_delete_bg': SEMANTIC_DIFF_REMOVED_LIGHT,\n        'diff_html_header_bg': GREY_EE,\n        'diff_html_line_num':  GREY_88,\n        'diff_html_border':    GREY_DD,\n        'diff_html_stats_text':GREY_66,\n\n        # Regex builder match highlight\n        'regex_match_bg': SEMANTIC_REGEX_MATCH,\n\n        # Image mode semi-transparent overlay values -- used only in image\n        # mode. DERIVED: a named colour at a declared alpha, so a register\n        # move reaches them (RNV-DERIVE-ALPHA, 2026-09-25).\n        'image_overlay_bg':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        'image_overlay_bg_dark':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        'image_overlay_checkbox':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        'image_scrollbar_border':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GREY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        'image_scrollbar_handle':      with_alpha(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n        # The image scrollbar hovers from DARK's 'accent'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n        'image_dropdown_bg':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        'image_dropdown_selection':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        'image_dropdown_border':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n    }\n    \n",
             "    DARK: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        'bg': BRAND_BLACK,\n        'bg_secondary': APP_CARD,\n        'bg_tertiary': APP_BORDER,\n        'bg_hover': APP_PANEL_HOVER,\n        \n        # Text\n        'text': APP_TEXT,\n        'text_muted': GREY_88,\n        'text_disabled': GREY_55,\n        \n        # Borders\n        'border': APP_BORDER,\n        'border_light': GREY_44,\n        'border_focus': BRAND_GOLD,\n        \n        # Accent colors\n        'accent': BRAND_GOLD,\n        'accent_hover': BRAND_GOLD_HOVER,\n        'accent_pressed': BRAND_GOLD_PRESSED,\n        'accent_ink': BRAND_GOLD,  # Accent when it carries text\n        'accent_text': TRUE_BLACK,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: these three keys are read in fourteen\n        # places and every one is a `color:` declaration, so they\n        # carry the TEXT variants rather than the fills. The fills\n        # sit at L* 48-59 and cannot reach 4.5:1 on either ground.\n        'success': STATUS_SUCCESS_TEXT,\n        'error': STATUS_ERROR_TEXT,\n        'warning': STATUS_WARNING_TEXT,\n        'info': BRAND_GOLD,\n        \n        # Special\n        'selection_bg': BRAND_GOLD,\n        'selection_text': TRUE_BLACK,\n        'scrollbar_bg': APP_CARD,\n        'scrollbar_handle': GREY_44,\n        'scrollbar_handle_main': GREY_44,\n        'tooltip_border': BRAND_GOLD,\n        \n        # Checkbox indicator\n        'checkbox_indicator_bg': BRAND_BLACK,\n        'checkbox_border': GREY_55,\n        \n        # Dropdown / list hover\n        'list_hover_bg': WHITE,\n        'list_hover_text': TRUE_BLACK,\n        \n        # MainWindow-specific (pure black background, distinct from dialog bg)\n        'window_bg': TRUE_BLACK,\n        'main_btn_bg': BRAND_BLACK,\n        'main_btn_text': APP_TEXT,\n        'main_btn_hover_bg': APP_BORDER,\n        'main_btn_pressed_bg': GREY_44,\n        'main_btn_pressed_text': TRUE_BLACK,\n        'input_bg': BRAND_BLACK,\n        'input_text': APP_TEXT,\n        'input_border': APP_BORDER,\n        'label_bg': TRUE_BLACK,\n        'label_text': APP_TEXT,\n        'output_text_color': BRAND_GOLD,\n        'border_color': APP_BORDER,\n        'text_color': APP_TEXT,\n        \n        # Line number gutter widget\n        'line_number_bg': BRAND_BLACK,\n        'line_number_fg': GREY_88,\n        'line_number_current_bg': APP_CARD,\n        'line_number_current_fg': BRAND_GOLD,\n\n        # Diff / compare semantic highlight colors\n        'diff_added_bg':   SEMANTIC_DIFF_ADDED,\n        'diff_removed_bg': SEMANTIC_DIFF_REMOVED,\n        'diff_changed_bg': SEMANTIC_DIFF_CHANGED,\n\n        # RNV-NAMED-AND-USED (2026-10-04): the diff export's seven colours\n        # stood here too. The export is a standalone page, always light,\n        # and reads them from LIGHT by name; this copy was looked up by\n        # nothing. They are in LIGHT alone.\n\n        # Regex builder match highlight\n        'regex_match_bg': SEMANTIC_REGEX_MATCH,\n\n        # Image mode semi-transparent overlay values -- used only in image\n        # mode. DERIVED: a named colour at a declared alpha, so a register\n        # move reaches them (RNV-DERIVE-ALPHA, 2026-09-25).\n        'image_overlay_bg':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        'image_overlay_bg_dark':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        'image_overlay_checkbox':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        'image_scrollbar_border':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GREY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        'image_scrollbar_handle':      with_alpha(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n        # The image scrollbar hovers from DARK's 'accent'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n        'image_dropdown_bg':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        'image_dropdown_selection':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        'image_dropdown_border':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n    }\n    \n")
    tree.sub('utils/dialog_styles.py',
             "    LIGHT: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        'bg': APP_SURFACE_LIGHT_3,\n        'bg_secondary': WHITE,\n        'bg_tertiary': GOLD_TEXT_GROUND_FLOOR,\n        'bg_hover': APP_HOVER_LIGHT,\n        \n        # Text\n        'text': TRUE_BLACK,\n        'text_muted': GREY_66,\n        'text_disabled': APP_TEXT_DIM,\n        \n        # Borders\n        'border': GREY_CC,\n        'border_light': GREY_DD,\n        'border_focus': BRAND_DARK_GOLD,\n        \n        # Accent colors\n        'accent': BRAND_DARK_GOLD,\n        'accent_hover': BRAND_DARK_GOLD_DEEP,\n        'accent_pressed': BRAND_DARK_GOLD_PRESSED,\n        'accent_ink': BRAND_DARK_GOLD_DEEP,  # Accent when it carries text\n        'accent_text': WHITE,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: light's siblings. success and warning\n        # had no light variant before this and read 2.87 and 1.50\n        # on #f5f5f5 -- illegal as text, live, and unnoticed because\n        # the only boundary test in this repo covered the red.\n        'success': STATUS_SUCCESS_TEXT_LIGHT,\n        'error': STATUS_ERROR_TEXT_LIGHT,\n        'warning': STATUS_WARNING_TEXT_LIGHT,\n        'info': BRAND_DARK_GOLD_DEEP,\n        \n        # Special\n        'selection_bg': BRAND_DARK_GOLD,\n        'selection_text': WHITE,\n        'scrollbar_bg': GREY_E0,\n        'scrollbar_handle': APP_TEXT_DIM,\n        'scrollbar_handle_hover': GREY_88,\n        'scrollbar_handle_main': APP_TEXT_DIM,\n        'tooltip_border': BRAND_DARK_GOLD,\n        \n        # Checkbox indicator\n        'checkbox_indicator_bg': WHITE,\n        'checkbox_border': APP_TEXT_DIM,\n        \n        # Dropdown / list hover\n        'list_hover_bg': BRAND_BLACK,\n        'list_hover_text': WHITE,\n        \n        # MainWindow-specific\n        'window_bg': APP_SURFACE_LIGHT_3,\n        'main_btn_bg': WHITE,\n        'main_btn_text': TRUE_BLACK,\n        'main_btn_hover_bg': APP_BORDER,\n        'main_btn_pressed_bg': GREY_44,\n        'main_btn_pressed_text': WHITE,\n        'input_bg': WHITE,\n        'input_text': TRUE_BLACK,\n        'input_border': GREY_CC,\n        'label_bg': APP_SURFACE_LIGHT_3,\n        'label_text': TRUE_BLACK,\n        'output_text_color': BRAND_DARK_GOLD,\n        'border_color': GREY_CC,\n        'text_color': TRUE_BLACK,\n        \n        # Line number gutter widget\n        'line_number_bg': GREY_EE,\n        'line_number_fg': GREY_66,\n        'line_number_current_bg': GOLD_TEXT_GROUND_FLOOR,\n        'line_number_current_fg': BRAND_DARK_GOLD_DEEP,\n\n        # Diff / compare semantic highlight colors\n        'diff_added_bg':   SEMANTIC_DIFF_ADDED_LIGHT,\n        'diff_removed_bg': SEMANTIC_DIFF_REMOVED_LIGHT,\n        'diff_changed_bg': SEMANTIC_DIFF_CHANGED_LIGHT,\n\n        # Diff HTML export colors (standalone document — always light-styled)\n        'diff_html_equal_bg':  WHITE,\n        'diff_html_insert_bg': SEMANTIC_DIFF_ADDED_LIGHT,\n        'diff_html_delete_bg': SEMANTIC_DIFF_REMOVED_LIGHT,\n        'diff_html_header_bg': GREY_EE,\n        'diff_html_line_num':  GREY_88,\n        'diff_html_border':    GREY_DD,\n        'diff_html_stats_text':GREY_66,\n\n        # Regex builder match highlight\n        'regex_match_bg': SEMANTIC_REGEX_MATCH_LIGHT,\n\n        # Image mode semi-transparent overlay values -- used only in image\n        # mode. Same derivations as DARK since image mode always uses\n        # dark-based overlays; image mode reads DARK, so nothing reads these.\n        'image_overlay_bg':            with_alpha(TRUE_BLACK, IMAGE_FIELD_ALPHA),\n        'image_overlay_bg_dark':       with_alpha(BRAND_BLACK, IMAGE_LABEL_ALPHA),\n        'image_overlay_checkbox':      with_alpha(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA),\n        'image_scrollbar_border':      with_alpha(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n        # RNV-COLLAPSE-505050, closed here 2026-09-25: this was\n        # rgba(80, 80, 80, 150), the value ruled onto GREY_44 on\n        # 2026-09-02 and left behind because nothing decoded rgba().\n        'image_scrollbar_handle':      with_alpha(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n        # The image scrollbar hovers from DARK's 'accent'. It has no key of\n        # its own: the unused one was removed, RNV-HOVER-KEY-GONE.\n        'image_dropdown_bg':           with_alpha(TRUE_BLACK, DROPDOWN_BG_ALPHA),\n        'image_dropdown_selection':    with_alpha(APP_BORDER, DROPDOWN_SELECTION_ALPHA),\n        'image_dropdown_border':       with_alpha(APP_BORDER, DROPDOWN_BORDER_ALPHA),\n    }\n    \n",
             '    LIGHT: ClassVar[dict[str, str]] = {\n        # Backgrounds\n        \'bg\': APP_SURFACE_LIGHT_3,\n        \'bg_secondary\': WHITE,\n        \'bg_tertiary\': GOLD_TEXT_GROUND_FLOOR,\n        \'bg_hover\': APP_HOVER_LIGHT,\n        \n        # Text\n        \'text\': TRUE_BLACK,\n        \'text_muted\': GREY_66,\n        \'text_disabled\': APP_TEXT_DIM,\n        \n        # Borders\n        \'border\': GREY_CC,\n        \'border_light\': GREY_DD,\n        \'border_focus\': BRAND_DARK_GOLD,\n        \n        # Accent colors\n        \'accent\': BRAND_DARK_GOLD,\n        \'accent_hover\': BRAND_DARK_GOLD_DEEP,\n        \'accent_pressed\': BRAND_DARK_GOLD_PRESSED,\n        \'accent_ink\': BRAND_DARK_GOLD_DEEP,  # Accent when it carries text\n        \'accent_text\': WHITE,  # Text on accent background\n        \n        # Semantic colors\n        # RNV-STATUS-FAMILY: light\'s siblings. success and warning\n        # had no light variant before this and read 2.87 and 1.50\n        # on #f5f5f5 -- illegal as text, live, and unnoticed because\n        # the only boundary test in this repo covered the red.\n        \'success\': STATUS_SUCCESS_TEXT_LIGHT,\n        \'error\': STATUS_ERROR_TEXT_LIGHT,\n        \'warning\': STATUS_WARNING_TEXT_LIGHT,\n        \'info\': BRAND_DARK_GOLD_DEEP,\n        \n        # Special\n        \'selection_bg\': BRAND_DARK_GOLD,\n        \'selection_text\': WHITE,\n        \'scrollbar_bg\': GREY_E0,\n        \'scrollbar_handle\': APP_TEXT_DIM,\n        \'scrollbar_handle_main\': APP_TEXT_DIM,\n        \'tooltip_border\': BRAND_DARK_GOLD,\n        \n        # Checkbox indicator\n        \'checkbox_indicator_bg\': WHITE,\n        \'checkbox_border\': APP_TEXT_DIM,\n        \n        # Dropdown / list hover\n        \'list_hover_bg\': BRAND_BLACK,\n        \'list_hover_text\': WHITE,\n        \n        # MainWindow-specific\n        \'window_bg\': APP_SURFACE_LIGHT_3,\n        \'main_btn_bg\': WHITE,\n        \'main_btn_text\': TRUE_BLACK,\n        \'main_btn_hover_bg\': APP_BORDER,\n        \'main_btn_pressed_bg\': GREY_44,\n        \'main_btn_pressed_text\': WHITE,\n        \'input_bg\': WHITE,\n        \'input_text\': TRUE_BLACK,\n        \'input_border\': GREY_CC,\n        \'label_bg\': APP_SURFACE_LIGHT_3,\n        \'label_text\': TRUE_BLACK,\n        \'output_text_color\': BRAND_DARK_GOLD,\n        \'border_color\': GREY_CC,\n        \'text_color\': TRUE_BLACK,\n        \n        # Line number gutter widget\n        \'line_number_bg\': GREY_EE,\n        \'line_number_fg\': GREY_66,\n        \'line_number_current_bg\': GOLD_TEXT_GROUND_FLOOR,\n        \'line_number_current_fg\': BRAND_DARK_GOLD_DEEP,\n\n        # Diff / compare semantic highlight colors\n        \'diff_added_bg\':   SEMANTIC_DIFF_ADDED_LIGHT,\n        \'diff_removed_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n        \'diff_changed_bg\': SEMANTIC_DIFF_CHANGED_LIGHT,\n\n        # Diff HTML export colors (standalone document — always light-styled)\n        \'diff_html_equal_bg\':  WHITE,\n        \'diff_html_insert_bg\': SEMANTIC_DIFF_ADDED_LIGHT,\n        \'diff_html_delete_bg\': SEMANTIC_DIFF_REMOVED_LIGHT,\n        \'diff_html_header_bg\': GREY_EE,\n        \'diff_html_line_num\':  GREY_88,\n        \'diff_html_border\':    GREY_DD,\n        \'diff_html_stats_text\':GREY_66,\n\n        # Regex builder match highlight\n        \'regex_match_bg\': SEMANTIC_REGEX_MATCH_LIGHT,\n\n        # RNV-NAMED-AND-USED (2026-10-04): the image overlays\' eight values\n        # stood here too, the same derivations as DARK. Image mode reads\n        # them from DARK by name, as the note that stood with them said:\n        # "nothing reads these". They are in DARK alone.\n    }\n    \n')
    tree.sub('utils/colors.py',
             '#: engine/brand.py STATUS["success"] -- RNV-STATUS-FAMILY (2026-09-03)\n#:\n#: A FILL. Badges, boundaries, filled bars. It is not text: every fill in this\n#: family sits in the L* 48-59 band, which is precisely what lets ONE value\n#: work on a dark AND a light ground, and a mid-tone cannot carry text on\n#: either side. 3.92 on #1a1a1a, 3.23 on #2a2a2a -- above the 3:1 fill floor\n#: and below the 4.5:1 text floor, by design rather than by accident.\n#:\n#: Was #28a745, Bootstrap\'s green. Retired because it and the Bootstrap red\n#: sat about 4 apart under deuteranopia -- one olive -- and success and error\n#: are the two most consequential colours in an interface.\nSTATUS_SUCCESS: Final[str] = \'#926c89\'\n\n#: engine/brand.py STATUS["warning"] -- a FILL. Was #ffc107.\n#:\n#: Retired on arithmetic rather than taste: #ffc107 read 1.63 on #ffffff and\n#: 1.49 on #f5f5f5 against a 3:1 fill floor. It could not legally carry a\n#: boundary on a light ground at all.\nSTATUS_WARNING: Final[str] = \'#a2703c\'\n\n#: engine/brand.py STATUS["error"] -- a FILL. Was #dc3545.\nSTATUS_ERROR: Final[str] = \'#c75b64\'\n\n',
             '#: RNV-NAMED-AND-USED (2026-10-04): the family\'s three fills stood here --\n#: STATUS["success"], STATUS["warning"] and STATUS["error"]. This application\n#: draws status as TEXT, in fourteen places, and no fill; nothing read the\n#: three, so it carries none. The register holds them.\n\n')
    tree.sub('utils/colors.py',
             '#: The fills above cannot carry text. These can: 4.55, 4.60 and 4.52 on APP\n#: card #2a2a2a, the worst dark ground this application paints on. That is why\n#: the family has nine values and not three.\n',
             "#: The family's fills cannot carry text. These can: 4.55, 4.60 and 4.52 on APP\n#: card #2a2a2a, the worst dark ground this application paints on. That is why\n#: the family has nine values and not three.\n")
    tree.sub('utils/colors.py',
             "    'STATUS_SUCCESS': 'register',\n    'STATUS_WARNING': 'register',\n    'STATUS_ERROR': 'register',\n",
             '')
    tree.sub('utils/colors.py',
             "    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_ERROR',\n",
             '')
    tree.sub('utils/colors.py',
             'DRAG_HIGHLIGHT_ALPHA: Final[int] = 0xBF\n"""191, 75%. The drop-target highlight on a text pane (BRAND_GOLD). The one\ncomposite this application already derived; its byte was written in place."""\n',
             'DRAG_HIGHLIGHT_ALPHA: Final[int] = 0xBF\n"""191, 75%. The drop-target highlight on a text pane (BRAND_GOLD). The one\ncomposite this application already derived; its byte was written in place."""\n\nFIND_HIGHLIGHT_ALPHA: Final[int] = 0x50\n"""80. Find\'s highlight on a match: the mode\'s accent at this alpha.\nRNV-NAMED-AND-USED (2026-10-04): was setAlpha(80), written out in the\nFind dialog; the same byte."""\n\n\n# ==================== COLOURS THE CODE SPELLED OUT ====================\n#\n# RNV-NAMED-AND-USED (2026-10-04). Ruled: "As long as a color exist in the\n# app it should be named and used no hardcoded or pointless literals should\n# exist". Named here at the value it had: NO PIXEL MOVES.\n\nSEMANTIC_EXPORT_FOOTER: Final[str] = \'#808080\'\n"""The "Generated by" footer of an exported PDF. Was the colour name\n`gray`, which is this value. App-owned, so named for what it means, as\nthe ruling of 2026-09-02 asks of every value this application owns."""\n')
    tree.sub('utils/colors.py',
             "    'DRAG_HIGHLIGHT_ALPHA',\n",
             "    'DRAG_HIGHLIGHT_ALPHA',\n    'FIND_HIGHLIGHT_ALPHA',\n    'SEMANTIC_EXPORT_FOOTER',\n")
    tree.sub('utils/colors.py',
             '#   app-semantic  neither brand nor ramp -- diff and regex highlighting\n',
             "#   app-semantic  neither brand nor ramp -- diff and regex highlighting,\n#                 and the grey of an exported PDF's footer\n")
    tree.sub('utils/colors.py',
             "    'SEMANTIC_REGEX_MATCH_LIGHT': 'app-semantic',\n}\n",
             "    'SEMANTIC_REGEX_MATCH_LIGHT': 'app-semantic',\n    'SEMANTIC_EXPORT_FOOTER': 'app-semantic',\n}\n")
    tree.sub('utils/__init__.py',
             '    APP_TEXT_DIM,\n    STATUS_SUCCESS,\n    STATUS_WARNING,\n    STATUS_ERROR,\n',
             '    APP_TEXT_DIM,\n')
    tree.sub('utils/__init__.py',
             "    'APP_TEXT_DIM',\n    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_ERROR',\n",
             "    'APP_TEXT_DIM',\n")
    tree.sub('core/export_manager.py',
             'from utils.dialog_styles import DialogStyleManager\n',
             'from utils.dialog_styles import DialogStyleManager\nfrom utils.colors import SEMANTIC_EXPORT_FOOTER\n')
    tree.sub('core/export_manager.py',
             "                textColor='gray'\n",
             "                # RNV-NAMED-AND-USED (2026-10-04): was the colour name 'gray'.\n                textColor=SEMANTIC_EXPORT_FOOTER\n")
    tree.sub('ui/find_replace_dialog.py',
             'from utils.dialog_styles import DialogStyleManager\n',
             'from utils.dialog_styles import DialogStyleManager\nfrom utils.colors import FIND_HIGHLIGHT_ALPHA\n')
    tree.sub('ui/find_replace_dialog.py',
             "        The colour matches are highlighted in: the mode's accent, at alpha 80.\n",
             "        The colour matches are highlighted in: the mode's accent, at\n        FIND_HIGHLIGHT_ALPHA (80).\n")
    tree.sub('ui/find_replace_dialog.py',
             '        highlight_color.setAlpha(80)  # Semi-transparent\n',
             '        highlight_color.setAlpha(FIND_HIGHLIGHT_ALPHA)  # Semi-transparent\n')
    tree.sub('test_rnv_text_transformer.py',
             '    def test_dark_and_light_have_same_keys(self):\n        self.assertEqual(set(DialogStyleManager.DARK.keys()), set(DialogStyleManager.LIGHT.keys()))\n',
             '    def test_dark_and_light_have_same_keys(self):\n        # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED): "for the locked\n        # key test if we don\'t use these values we can fix the test and remove\n        # unused values". A key only one mode reads is in that mode\'s palette\n        # alone; its other half was a value nothing showed. Image mode reads\n        # its eight overlay values from DARK by name, and the diff export, a\n        # page that is always light, reads its seven from LIGHT by name.\n        dark, light = set(DialogStyleManager.DARK), set(DialogStyleManager.LIGHT)\n        self.assertEqual(dark - light, {\n            "image_overlay_bg", "image_overlay_bg_dark", "image_overlay_checkbox",\n            "image_scrollbar_border", "image_scrollbar_handle", "image_dropdown_bg",\n            "image_dropdown_selection", "image_dropdown_border"})\n        self.assertEqual(light - dark, {\n            "diff_html_equal_bg", "diff_html_insert_bg", "diff_html_delete_bg",\n            "diff_html_header_bg", "diff_html_line_num", "diff_html_border",\n            "diff_html_stats_text"})\n')
    tree.sub('test_rnv_text_transformer.py',
             '            "scrollbar_bg", "scrollbar_handle", "scrollbar_handle_hover",\n',
             '            # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED):\n            # scrollbar_handle_hover stood here. No stylesheet read it.\n            "scrollbar_bg", "scrollbar_handle",\n')
    tree.sub('test_rnv_text_transformer.py',
             '            "scrollbar_bg", "scrollbar_handle_main", "scrollbar_handle_hover",\n',
             '            # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED):\n            # scrollbar_handle_hover stood here, and the main window never\n            # referenced it.\n            "scrollbar_bg", "scrollbar_handle_main",\n')
    tree.sub('tests/test_derived_values.py',
             'PALETTES = {"DARK": DialogStyleManager.DARK, "LIGHT": DialogStyleManager.LIGHT}\n',
             'PALETTES = {"DARK": DialogStyleManager.DARK, "LIGHT": DialogStyleManager.LIGHT}\n#: RNV-NAMED-AND-USED, 2026-10-04: the palette that holds the image values.\n#: LIGHT held the same eight, made the same way, and nothing read them --\n#: image mode reads its overlays from DARK by name. They are in DARK alone.\nIMAGE_PALETTES = {"DARK": DialogStyleManager.DARK}\n')
    tree.sub('tests/test_derived_values.py',
             '    want = {f"{p}[{k!r}]" for p in PALETTES for k in MADE_OF}\n',
             '    want = {f"{p}[{k!r}]" for p in IMAGE_PALETTES for k in MADE_OF}\n')
    tree.sub('tests/test_derived_values.py',
             '    for mode, palette in PALETTES.items():\n        assert decompose(palette["image_scrollbar_handle"]) == (\n',
             '    for mode, palette in IMAGE_PALETTES.items():\n        assert decompose(palette["image_scrollbar_handle"]) == (\n')
    tree.sub('tests/test_derived_values.py',
             '    for mode, palette in PALETTES.items():\n        for key, (base, alpha) in MADE_OF.items():\n',
             '    for mode, palette in IMAGE_PALETTES.items():\n        for key, (base, alpha) in MADE_OF.items():\n')
    tree.sub('tests/test_derived_values.py',
             '#: Found when this was written; below the floor, the sweep has gone blind.\nLOWER8_FLOOR = 12\n',
             '#: Found when this was written; below the floor, the sweep has gone blind.\n#: 9 since RNV-NAMED-AND-USED, 2026-10-04: the image values are in DARK\n#: alone, eight of them, and the drag highlight is the ninth.\nLOWER8_FLOOR = 9\n')
    tree.sub('tests/test_error_red.py',
             '"""The RNV status family, as this application uses it.\n\n    STATUS_SUCCESS / _WARNING / _ERROR               fills, L* 48-59\n    STATUS_*_TEXT         #ad85a3 #bc8752 #dd6f77    text on a dark ground\n    STATUS_*_TEXT_LIGHT   #825d79 #8e5e2b #ae4650    text on a light ground\n',
             '"""The RNV status family, as this application uses it.\n\n    STATUS_*_TEXT         #ad85a3 #bc8752 #dd6f77    text on a dark ground\n    STATUS_*_TEXT_LIGHT   #825d79 #8e5e2b #ae4650    text on a light ground\n\nRNV-NAMED-AND-USED, 2026-10-04: the family\'s three fills stood here too, with\ntwo tests on their arithmetic. This application draws status as text and no\nfill; nothing read the three, so it carries none, and those tests went with\nthem. The register holds the fills.\n')
    tree.sub('tests/test_error_red.py',
             'TEXT_FLOOR = 4.5\nFILL_FLOOR = 3.0\n',
             'TEXT_FLOOR = 4.5\n')
    tree.sub('tests/test_error_red.py',
             'LIGHT_GROUNDS = ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8")\nALL_GROUNDS = DARK_GROUNDS + LIGHT_GROUNDS\n\nFILLS = ("STATUS_SUCCESS", "STATUS_WARNING", "STATUS_ERROR")\n',
             'LIGHT_GROUNDS = ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8")\n\n')
    tree.sub('tests/test_error_red.py',
             'REGISTERED = {\n    "STATUS_SUCCESS": "#926c89",\n    "STATUS_WARNING": "#a2703c",\n    "STATUS_ERROR": "#c75b64",\n',
             'REGISTERED = {\n')
    tree.sub('tests/test_error_red.py',
             'def test_the_nine_values_are_the_registered_ones(name, value):\n    """Pinned by value, not by relationship.\n\n    A test asserting only that these differ from each other would pass on nine\n    wrong colours. The register publishes nine hexes and this repository\n    mirrors them; if the register moves one, this is the line that says so.\n    """\n',
             'def test_the_six_values_are_the_registered_ones(name, value):\n    """Pinned by value, not by relationship.\n\n    A test asserting only that these differ from each other would pass on six\n    wrong colours. The register publishes nine hexes and this repository\n    mirrors the six it draws; if the register moves one, this is the line\n    that says so.\n    """\n')
    tree.sub('tests/test_error_red.py',
             '# ------------------------------------------------------------- the fills\n@pytest.mark.parametrize("name", FILLS)\n@pytest.mark.parametrize("ground", ALL_GROUNDS)\ndef test_a_fill_clears_the_fill_floor_on_every_ground(name, ground):\n    """One value, four grounds. That is what a fill has to do, and it is why\n    all three sit in the L* 48-59 band."""\n    ratio = contrast(getattr(colors, name), ground)\n    assert ratio >= FILL_FLOOR, f"{name} on {ground} = {ratio:.4f}"\n\n\n@pytest.mark.parametrize("name", FILLS)\n@pytest.mark.parametrize("ground", ALL_GROUNDS)\ndef test_a_fill_is_not_usable_as_text(name, ground):\n    """The other half of the fill band, asserted rather than assumed.\n\n    This is the test that would have caught the wrong migration. Swapping the\n    value while a key still means "text" leaves every status message below the\n    text floor; if someone later points a `color:` declaration at a fill, this\n    records that the fill was never able to do that job.\n    """\n    ratio = contrast(getattr(colors, name), ground)\n    assert ratio < TEXT_FLOOR, (\n        f"{name} now reads {ratio:.4f} on {ground} and CLEARS the text floor. "\n        f"Either the register moved it out of the fill band, or this test is "\n        f"measuring the wrong constant. Do not relax it -- find out which.")\n\n\n',
             "# ------------------------------------------------------------- the fills\n# RNV-NAMED-AND-USED, 2026-10-04: two tests stood here on the arithmetic of\n# the three fills -- that each clears 3:1 on every ground and 4.5:1 on none.\n# This application draws no fill and no longer carries them; the arithmetic\n# is the register's, where the fills are.\n\n\n")
    tree.sub('tests/test_status_family.py',
             'SOURCES = SWEPT = ("utils/colors.py", "utils/dialog_styles.py")\nLIVE_VALUE = "#926c89"\n',
             'SOURCES = SWEPT = ("utils/colors.py", "utils/dialog_styles.py")\n# the success text: a value utils/colors.py holds. It was the success fill\'s\n# until RNV-NAMED-AND-USED, 2026-10-04, when the fill went.\nLIVE_VALUE = "#ad85a3"\n\n#: The register\'s three status fills: STATUS["success"], ["warning"] and\n#: ["error"] in engine/brand.py. RNV-NAMED-AND-USED, 2026-10-04: this\n#: application drew none of them and no longer carries them, so they are held\n#: here, under the names the register gives them, as what a status key must\n#: never be painted with.\nREGISTER_FILLS = {"success": "#926c89", "warning": "#a2703c", "error": "#c75b64"}\n')
    tree.sub('tests/test_status_family.py',
             '    to six. If someone repoints these keys at STATUS_SUCCESS / _WARNING /\n    _ERROR, this is the line that stops it.\n    """\n    fills = {colors.STATUS_SUCCESS, colors.STATUS_WARNING, colors.STATUS_ERROR}\n',
             '    to six. If someone repoints these keys at the register\'s fills, this is\n    the line that stops it.\n    """\n    fills = set(REGISTER_FILLS.values())\n')
    tree.sub('tests/test_register_wiring.py',
             "    'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8',\n    'STATUS_SUCCESS': '#926c89', 'STATUS_WARNING': '#a2703c', 'STATUS_ERROR': '#c75b64',\n",
             "    'GOLD_TEXT_GROUND_FLOOR': '#e8e8e8',\n    # RNV-NAMED-AND-USED, 2026-10-04: the three status fills stood here. The\n    # application carried them unread, and no longer does.\n")
    tree.sub('tests/test_ladder_and_plate.py',
             '#: What the split leaves behind: the ramp step, and the three static surfaces\n#: that keep it. If this list ever empties, the split has collapsed.\n',
             "#: What the split leaves behind: the ramp step, and the static surfaces that\n#: keep it -- two since RNV-NAMED-AND-USED, 2026-10-04, when the dark\n#: palette's copy of diff_html_header_bg, which nothing read, went. If this\n#: list ever empties, the split has collapsed.\n")
    tree.sub('tests/test_ladder_and_plate.py',
             "        f'step; if the grounds moved too, three surfaces are now claiming to '\n",
             "        f'step; if the grounds moved too, static surfaces are now claiming to '\n")
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "diff_changed_bg": "#403f00",\n    "diff_html_border": "#dddddd",\n    "diff_html_delete_bg": "#a17877",\n    "diff_html_equal_bg": "#ffffff",\n    "diff_html_header_bg": "#eeeeee",\n    "diff_html_insert_bg": "#8eafa0",\n    "diff_html_line_num": "#888888",\n    "diff_html_stats_text": "#666666",\n    "diff_removed_bg": "#704a4a",\n',
             '    "diff_changed_bg": "#403f00",\n    "diff_removed_bg": "#704a4a",\n')
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "scrollbar_handle": "#444444",\n    "scrollbar_handle_hover": "#d2bc93",\n',
             '    "scrollbar_handle": "#444444",\n')
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "error": "#ae4650",\n    "image_dropdown_bg": "#83000000",\n    "image_dropdown_border": "#96333333",\n    "image_dropdown_selection": "#c8333333",\n    "image_overlay_bg": "#ab000000",\n    "image_overlay_bg_dark": "#bf1a1a1a",\n    "image_overlay_checkbox": "#64000000",\n    "image_scrollbar_border": "#64333333",\n    "image_scrollbar_handle": "#96444444",\n    "info": "#7e6529",\n',
             '    "error": "#ae4650",\n    "info": "#7e6529",\n')
    tree.sub('tests/__snapshots__/test_snapshots.ambr',
             '    "scrollbar_handle": "#aaaaaa",\n    "scrollbar_handle_hover": "#888888",\n',
             '    "scrollbar_handle": "#aaaaaa",\n')
    if (tree.root / 'tests/test_named_and_used.py').exists():
        raise Stop('tests/test_named_and_used.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_named_and_used.py', '"""\ntests/test_named_and_used.py\n============================\nRNV-NAMED-AND-USED, 2026-10-04. Every colour in the application is named,\nand every name is used.\n\nRuled 2026-10-04: "As long as a color exist in the app it should be named\nand used no hardcoded or pointless literals should exist, only literals with\na purpose, like data or comparison are allowed. Colors are name for swap\nability and alignment."\n\nIn this application that removed a scrollbar hover key no mode read; kept\nthe diff export\'s seven keys in LIGHT alone and the image overlays\' eight in\nDARK alone, each the one palette they are read from; removed the status\nfamily\'s three fills, which nothing read; and it named the exported PDF\'s\nfooter grey and the alpha of Find\'s highlight.\n\nThree sweeps hold it, each over the application\'s own source:\n\n1. NAMED. No colour is written out in the code. Every spelling is read: hex,\n   rgb() and rgba(), a CSS colour name, QColor built from numbers, a Qt\n   global colour, a tuple or a list of channels, an alpha set as a number.\n   A colour is written once, in the colour module, under a name; everything\n   else reads the name. What stays written is DATA, each entry with its\n   reason, and the sweep fails for an entry that no longer matches anything.\n2. USED, the palettes. Every colour a palette holds is looked up by key\n   somewhere in the application.\n3. USED, the constants. Every colour the colour module names is read\n   somewhere in the application: by the palettes, by another constant, or by\n   the code.\n\nClear is not a colour: \'transparent\', alpha 0 and Qt\'s transparent are how a\nwidget is told to paint nothing, and are left as written.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport importlib\nimport pathlib\nimport re\n\nimport pytest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: Where this application writes its colours: the one place a literal belongs.\nCOLOUR_MODULES = ("utils/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("utils/dialog_styles.py",)\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom utils.dialog_styles import DialogStyleManager  # noqa: E402\n\nPALETTES = {"DARK": DialogStyleManager.DARK, "LIGHT": DialogStyleManager.LIGHT}\n\n#: Below these a sweep has gone blind.\nMIN_FILES = 30\nMIN_ENTRIES = 100\nMIN_CONSTANTS = 30\n\n#: What stays written, and why: (file, literal) -> the reason. An example shown\n#: to the person is text, not the application\'s look.\nDATA = {\n    ("core/regex_patterns.py", "#FF5733"):\n        "the example the Hex Color pattern is shown with: text shown to the person",\n}\n\nCSS_NAMES = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue\nblueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue\ndarkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid\ndarkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink\ndeepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold\ngoldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush\nlawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey\nlightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime\nlimegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen\nmediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin\nnavajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise\npalevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue\nsaddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow\nspringgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow\nyellowgreen""".split())\nQT_GLOBAL = frozenset({"white", "black", "red", "darkRed", "green", "darkGreen", "blue", "darkBlue", "cyan",\n                       "darkCyan", "magenta", "darkMagenta", "yellow", "darkYellow", "gray", "darkGray",\n                       "lightGray"})\nHEX = re.compile(r"(?<![\\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])")\nFUNC = re.compile(r"\\b(?:rgba?|hsla?|hsva?)\\(\\s*[0-9.]+%?\\s*,[^)]*\\)", re.I)\nPROP = re.compile(r"(?:^|[;{\\s\\"\'])((?:[a-z-]*color|background(?:-color)?|border(?:-[a-z]+)*|outline(?:-[a-z]+)*|"\n                  r"fill|stroke))\\s*[:=]\\s*([^;{}<>]*)", re.I)\nWORD = re.compile(r"(?<![\\w#.-])([a-z]+)(?![\\w(-])", re.I)\nNOT_A_COLOUR = re.compile(r"margin|padding|spacing|size|offset|geometry|rect|pos|range|version|ratio|weight", re.I)\nA_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})|rgba?\\([^)]*\\)")\n\n\ndef _sources():\n    """(repo-relative path, text) of every file of the application: not the\n    tests, not a delivery script, not what a build leaves behind."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT).as_posix()\n        parts = rel.split("/")\n        if any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1]):\n            continue\n        if len(parts) == 1 and (parts[0].startswith(("test_", "up", "conftest", "run_tests"))):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, text\n\n\ndef _prose(tree) -> set:\n    """ids of the strings that are prose: docstrings and bare string statements."""\n    return {id(n.value) for n in ast.walk(tree)\n            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}\n\n\ndef _clear(literal: str) -> bool:\n    """rgba(..., 0) and QColor(..., 0): clear, not a colour."""\n    nums = re.findall(r"[0-9.]+", literal)\n    return len(nums) == 4 and float(nums[3]) == 0\n\n\ndef _written(rel: str, text: str) -> list:\n    """(line, kind, literal) for every colour this file writes out."""\n    tree = ast.parse(text)\n    prose, out = _prose(tree), []\n    parent = {}\n    for node in ast.walk(tree):\n        for child in ast.iter_child_nodes(node):\n            parent[id(child)] = node\n\n    def named_like(node) -> str:\n        """The name a value is given: its assignment target, keyword or parameter."""\n        up = parent.get(id(node))\n        while isinstance(up, (ast.IfExp, ast.BoolOp, ast.Tuple, ast.List)):\n            node, up = up, parent.get(id(up))\n        if isinstance(up, ast.keyword):\n            return up.arg or ""\n        if isinstance(up, (ast.Assign, ast.AnnAssign)):\n            target = up.targets[0] if isinstance(up, ast.Assign) else up.target\n            return ast.unparse(target)\n        if isinstance(up, ast.arguments):\n            both = up.posonlyargs + up.args\n            if node in up.defaults:\n                return both[len(both) - len(up.defaults) + up.defaults.index(node)].arg\n            if node in up.kw_defaults:\n                return up.kwonlyargs[up.kw_defaults.index(node)].arg\n        return ""\n\n    def a_name_on_its_own(node, up) -> bool:\n        """A CSS colour name that is the whole string, where a colour is given:\n        handed to a call, chosen by an if, assigned, returned, a default or a\n        value in a table. A key, an index and a comparison are not a colour\n        given to anything."""\n        s = node.value\n        if isinstance(up, (ast.Call, ast.keyword, ast.IfExp)):\n            return s.lower() in CSS_NAMES              # Qt and PIL read a name in any case\n        if s not in CSS_NAMES:\n            return False\n        if isinstance(up, ast.Dict):\n            return any(v is node for v in up.values)\n        if isinstance(up, ast.arguments):\n            return node in up.defaults or node in up.kw_defaults\n        return isinstance(up, (ast.Assign, ast.AnnAssign, ast.Return)) and up.value is node\n\n    for node in ast.walk(tree):\n        up = parent.get(id(node))\n        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in prose:\n            s = node.value\n            for m in HEX.finditer(s):\n                out.append((node.lineno, "hex", m.group(0)))\n            for m in FUNC.finditer(s):\n                if not _clear(m.group(0)):\n                    out.append((node.lineno, "func", " ".join(m.group(0).split())))\n            for m in PROP.finditer(s):\n                for w in WORD.finditer(m.group(2)):\n                    if w.group(1).lower() in CSS_NAMES:\n                        out.append((node.lineno, "name", f"{m.group(1).lower()}: {w.group(1)}"))\n            # a colour name on its own: QColor("yellow"), fill="white", ink = "black"\n            if a_name_on_its_own(node, up):\n                out.append((node.lineno, "name", s))\n        elif isinstance(node, ast.Call):\n            name = getattr(node.func, "id", getattr(node.func, "attr", None))\n            if name in ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba") and node.args \\\n                    and all(isinstance(a, ast.Constant) and not isinstance(a.value, str) for a in node.args):\n                literal = ast.unparse(node)\n                if not _clear(literal):\n                    out.append((node.lineno, "qcolor", literal))\n            # an alpha set as a number: colour.setAlpha(171). Clear and solid are not a choice of alpha.\n            elif name in ("setAlpha", "setAlphaF") and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) \\\n                    and type(node.args[0].value) in (int, float) \\\n                    and node.args[0].value not in ((0, 255) if name == "setAlpha" else (0, 1)):\n                out.append((node.lineno, "alpha", f"{name}({node.args[0].value!r})"))\n        elif isinstance(node, ast.Attribute) and node.attr in QT_GLOBAL \\\n                and ast.unparse(node.value) in ("Qt.GlobalColor", "Qt", "QtCore.Qt.GlobalColor", "QtCore.Qt"):\n            out.append((node.lineno, "global", ast.unparse(node)))\n        elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4) and all(\n                isinstance(e, ast.Constant) and type(e.value) is int and 0 <= e.value <= 255 for e in node.elts):\n            if (isinstance(up, (ast.comprehension, ast.For)) and up.iter is node) \\\n                    or isinstance(up, (ast.Compare, ast.Subscript)):\n                continue                                   # an index, a membership or a comparison\n            if isinstance(up, ast.Call) and getattr(up.func, "id", getattr(up.func, "attr", "")) in QCOLOR_CALLS:\n                continue                                   # counted with its QColor(...)\n            if len(node.elts) == 4 and node.elts[3].value == 0:\n                continue                                   # clear\n            if NOT_A_COLOUR.search(named_like(node)):\n                continue\n            out.append((node.lineno, "list" if isinstance(node, ast.List) else "tuple", ast.unparse(node)))\n    return out\n\n\nQCOLOR_CALLS = ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba")\n\n\ndef _all_written() -> list:\n    """(rel, line, kind, literal) outside the colour module."""\n    out = []\n    for rel, text in _sources():\n        if rel in COLOUR_MODULES:\n            continue\n        out += [(rel, line, kind, literal) for line, kind, literal in _written(rel, text)]\n    return out\n\n\ndef _data(rel: str, literal: str):\n    """The DATA entry that covers this literal, or None."""\n    for (where, what) in DATA:\n        if where == rel and what in ("*", literal):\n            return (where, what)\n    return None\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_sweep_reads_the_application():\n    files = [rel for rel, _text in _sources()]\n    assert len(files) >= MIN_FILES, f"only {len(files)} files swept: the sweep has gone blind"\n    for rel in COLOUR_MODULES:\n        assert rel in files, f"{rel} is not among the files swept"\n    assert not [f for f in files if f.startswith("tests/")], "the sweep reads the tests"\n\n\ndef test_the_sweep_reads_every_spelling():\n    """Each spelling of a colour, in a line of the kind the application\n    writes, is seen; clear, an index and a margin are not."""\n    seen = {(kind, literal) for _line, kind, literal in _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background-color: #ffcccc; border: 2px solid red;\'\\n"\n        "b = f\'color: rgba(255, 255, 255, 230); padding: {4}px\'\\n"\n        "c = QColor(128, 128, 128)\\n"\n        "d = Qt.GlobalColor.darkGreen\\n"\n        "e = QColor(\'yellow\')\\n"\n        "text_color = (0, 0, 0) if a else (255, 255, 255)\\n"\n        "f = saved.get(\'color\', [200, 200, 200])\\n"\n        "ink = \'white\'\\n"\n        "g = {\'ground\': \'black\'}\\n"\n        "h = Image.new(\'RGB\', (8, 8), \'Gray\')\\n"\n        "c.setAlpha(171)\\n"))}\n    assert seen == {("hex", "#ffcccc"), ("name", "border: red"), ("func", "rgba(255, 255, 255, 230)"),\n                    ("qcolor", "QColor(128, 128, 128)"), ("global", "Qt.GlobalColor.darkGreen"),\n                    ("name", "yellow"), ("tuple", "(0, 0, 0)"), ("tuple", "(255, 255, 255)"),\n                    ("list", "[200, 200, 200]"), ("name", "white"), ("name", "black"), ("name", "Gray"),\n                    ("alpha", "setAlpha(171)")}, seen\n    quiet = _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background: transparent; border: none; color: rgba(0, 0, 0, 0);\'\\n"\n        "b = QColor(0, 0, 0, 0)\\n"\n        "b.setAlpha(0)\\n"\n        "b.setAlpha(255)\\n"\n        "c = Qt.GlobalColor.transparent\\n"\n        "d = [int(h[i:i + 2], 16) for i in (0, 2, 4)]\\n"\n        "margins = (10, 10, 10, 10)\\n"\n        "sizes = [16, 32, 48]\\n"\n        "\'\'\'a bare string is prose: color: red, #ffcccc\'\'\'\\n"\n        "if d in (5, 10, 20) or d == (0, 0, 0) or a == \'red\':\\n"\n        "    pass\\n"\n        "for size in [16, 32, 48]:\\n"\n        "    e = {\'red\': 1}[\'red\']\\n"))\n    assert quiet == [], quiet\n\n\n# ----------------------------------------------------------------- 1. named\n\ndef test_no_colour_is_written_out_in_the_code():\n    stray = [f"{rel}:{line}  {literal}" for rel, line, _kind, literal in _all_written()\n             if _data(rel, literal) is None]\n    assert not stray, (\n        "a colour is written out where a name belongs. Name it in "\n        f"{COLOUR_MODULES[0]} and read the name; or, if it is data, add it to DATA "\n        "with its reason:\\n  " + "\\n  ".join(stray))\n\n\ndef test_every_data_entry_still_covers_something():\n    """An exemption that outlives what it excused is a licence for the next\n    literal written in that file."""\n    used = {_data(rel, literal) for rel, _line, _kind, literal in _all_written()}\n    stale = [f"{where}: {what}" for (where, what) in DATA if (where, what) not in used]\n    assert not stale, "DATA entries that match nothing now:\\n  " + "\\n  ".join(stale)\n    assert all(reason.strip() for reason in DATA.values()), "a DATA entry has no reason"\n\n\n# ---------------------------------------------------- 2. used: the palettes\n\ndef _strings_the_application_reads() -> set:\n    """Every string the code holds outside the palettes\' own keys: what a\n    lookup by key, or a table of keys, is written with. A module\'s __all__\n    is a list of the names it exports, not of keys, and is left out: a\n    function called warning() does not look up a palette\'s \'warning\'."""\n    out = set()\n    for rel, text in _sources():\n        tree = ast.parse(text)\n        not_keys = _prose(tree)\n        if rel in PALETTE_MODULES:\n            for node in ast.walk(tree):\n                if isinstance(node, ast.Dict):\n                    not_keys |= {id(k) for k in node.keys if k is not None}\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == "__all__" and node.value is not None:\n                not_keys |= {id(n) for n in ast.walk(node.value)}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in not_keys:\n                out.add(node.value)\n    return out\n\n\ndef test_every_colour_a_palette_holds_is_looked_up():\n    read = _strings_the_application_reads()\n    unread = sorted({f"{name}[{key!r}]" for name, palette in PALETTES.items() for key, value in palette.items()\n                     if isinstance(value, str) and (A_COLOUR.fullmatch(value) or value == "transparent")\n                     and key not in read})\n    assert not unread, (\n        "palette entries nothing in the application looks up. A colour is kept "\n        "for what uses it:\\n  " + "\\n  ".join(unread))\n    assert sum(len(p) for p in PALETTES.values()) >= MIN_ENTRIES, "the palettes have gone missing"\n\n\n# --------------------------------------------------- 3. used: the constants\n\ndef _colour_constants() -> dict:\n    """NAME -> where it is defined, for every module-level constant of the\n    colour module whose value is a colour: a hex string, an rgb() string, or\n    channels under a name that says so."""\n    out = {}\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if not isinstance(target, ast.Name) or not target.id.isupper():\n                continue\n            value = getattr(module, target.id, None)\n            if isinstance(value, str) and A_COLOUR.fullmatch(value):\n                out[target.id] = rel\n            elif isinstance(value, tuple) and len(value) in (3, 4) and all(type(v) is int for v in value) \\\n                    and re.search(r"RGB|COLOR|COLOUR|OVERLAY", target.id):\n                out[target.id] = rel\n    return out\n\n\ndef _names_the_application_reads() -> dict:\n    """NAME -> how many times the code reads it: as a name or as an attribute."""\n    counts: dict[str, int] = {}\n    for _rel, text in _sources():\n        for node in ast.walk(ast.parse(text)):\n            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):\n                counts[node.id] = counts.get(node.id, 0) + 1\n            elif isinstance(node, ast.Attribute):\n                counts[node.attr] = counts.get(node.attr, 0) + 1\n    return counts\n\n\ndef test_every_colour_constant_is_read():\n    constants = _colour_constants()\n    assert len(constants) >= MIN_CONSTANTS, f"only {len(constants)} colour constants found"\n    reads = _names_the_application_reads()\n    unread = sorted(name for name in constants if not reads.get(name))\n    assert not unread, (\n        "colour constants nothing in the application reads. A name is kept for "\n        "what uses it:\\n  " + "\\n  ".join(f"{name}  ({constants[name]})" for name in unread))\n\n\ndef test_every_exported_name_exists():\n    """__all__ names what the colour module offers. A name it lists and does\n    not define makes `from module import *` fail."""\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        missing = [n for n in getattr(module, "__all__", []) if not hasattr(module, n)]\n        assert not missing, f"{rel} exports names it does not define: {missing}"\n\n\n# ------------------------------------------- the keys one mode alone holds\n\n#: A key one mode alone reads is in that mode\'s palette alone, and is read\n#: from that palette BY NAME: key -> (the palette that holds it, how the code\n#: spells that palette). Read through "the palette in force" it would be a\n#: KeyError in the mode that does not hold it.\nMODE_ONLY = {\n    \'diff_html_equal_bg\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_insert_bg\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_delete_bg\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_header_bg\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_line_num\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_border\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'diff_html_stats_text\': (\'LIGHT\', \'DialogStyleManager.LIGHT\'),\n    \'image_overlay_bg\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_overlay_bg_dark\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_overlay_checkbox\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_scrollbar_border\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_scrollbar_handle\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_dropdown_bg\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_dropdown_selection\': (\'DARK\', \'DialogStyleManager.DARK\'),\n    \'image_dropdown_border\': (\'DARK\', \'DialogStyleManager.DARK\'),\n}\n\n\ndef _lookups_of(key: str) -> list:\n    """(rel, line, what the receiver is) for every lookup of key outside the\n    palettes\' own modules. A receiver that is a name stands for everything\n    that name is assigned in the function the lookup is in."""\n    out = []\n    for rel, text in _sources():\n        if rel in PALETTE_MODULES:\n            continue\n        tree = ast.parse(text)\n        owner = {}\n        for fn in ast.walk(tree):                  # outer functions first, so the innermost is kept\n            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):\n                for node in ast.walk(fn):\n                    owner[id(node)] = fn\n        for node in ast.walk(tree):\n            receiver = None\n            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == key:\n                receiver = node.value\n            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get" and node.args \\\n                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:\n                receiver = node.func.value\n            if receiver is None:\n                continue\n            if isinstance(receiver, ast.Name):\n                is_a = {ast.unparse(n.value) for n in ast.walk(owner.get(id(node), tree))\n                        if isinstance(n, ast.Assign) and len(n.targets) == 1\n                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == receiver.id}\n            else:\n                is_a = {ast.unparse(receiver)}\n            out.append((rel, node.lineno, is_a))\n    return out\n\n\n@pytest.mark.parametrize("key", sorted(MODE_ONLY))\ndef test_a_key_one_mode_holds_is_read_from_that_palette_by_name(key):\n    palette, spelled = MODE_ONLY[key]\n    assert key in PALETTES[palette], f"{palette} does not hold {key!r}"\n    lookups = _lookups_of(key)\n    assert lookups, f"nothing looks up {key!r}"\n    astray = [f"{rel}:{line}  read from {sorted(is_a) or \'a receiver this test cannot follow\'}"\n              for rel, line, is_a in lookups if is_a != {spelled}]\n    assert not astray, (\n        f"{key!r} is in {palette} alone. Read from anything but {spelled} it is a "\n        "KeyError in the mode that does not hold it:\\n  " + "\\n  ".join(astray))\n\n\ndef test_the_palettes_differ_only_by_the_keys_one_mode_reads():\n    """Dark and light hold the same keys but for MODE_ONLY: a lookup through\n    the palette in force cannot miss in either."""\n    dark, light = PALETTES["DARK"], PALETTES["LIGHT"]\n    assert set(dark) ^ set(light) == set(MODE_ONLY), sorted((set(dark) ^ set(light)) ^ set(MODE_ONLY))\n    assert {k for k, (palette, _spelled) in MODE_ONLY.items() if palette == "DARK"} == set(dark) - set(light)\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    import json
    CFG, STYLES = "utils/colors.py", "utils/dialog_styles.py"
    ROOT_SUITE, SNAPSHOTS = "test_rnv_text_transformer.py", "tests/__snapshots__/test_snapshots.ambr"
    KEYS_GONE = ('scrollbar_handle_hover',)
    LIGHT_ONLY = ('diff_html_equal_bg', 'diff_html_insert_bg', 'diff_html_delete_bg', 'diff_html_header_bg', 'diff_html_line_num', 'diff_html_border', 'diff_html_stats_text')
    DARK_ONLY = ('image_overlay_bg', 'image_overlay_bg_dark', 'image_overlay_checkbox', 'image_scrollbar_border', 'image_scrollbar_handle', 'image_dropdown_bg', 'image_dropdown_selection', 'image_dropdown_border')
    NAMES_GONE = ('STATUS_SUCCESS', 'STATUS_WARNING', 'STATUS_ERROR')
    NEW_VALUES = {'SEMANTIC_EXPORT_FOOTER': "'#808080'", 'FIND_HIGHLIGHT_ALPHA': '0x50'}
    NAMED = {'core/export_manager.py': [('from utils.dialog_styles import DialogStyleManager\n', 'from utils.dialog_styles import DialogStyleManager\nfrom utils.colors import SEMANTIC_EXPORT_FOOTER\n', 1), ("textColor='gray'", 'textColor=SEMANTIC_EXPORT_FOOTER', 1)], 'ui/find_replace_dialog.py': [('from utils.dialog_styles import DialogStyleManager\n', 'from utils.dialog_styles import DialogStyleManager\nfrom utils.colors import FIND_HIGHLIGHT_ALPHA\n', 1), ("the mode's accent, at alpha 80.\n", "the mode's accent, at\n        FIND_HIGHLIGHT_ALPHA (80).\n", 1), ('highlight_color.setAlpha(80)', 'highlight_color.setAlpha(FIND_HIGHLIGHT_ALPHA)', 1)], 'utils/__init__.py': [('APP_TEXT_DIM, STATUS_SUCCESS, STATUS_WARNING, STATUS_ERROR, STATUS_SUCCESS_TEXT,', 'APP_TEXT_DIM, STATUS_SUCCESS_TEXT,', 1), ("'APP_TEXT_DIM', 'STATUS_SUCCESS', 'STATUS_WARNING', 'STATUS_ERROR', 'STATUS_SUCCESS_TEXT',", "'APP_TEXT_DIM', 'STATUS_SUCCESS_TEXT',", 1)], 'test_rnv_text_transformer.py': [('        self.assertEqual(set(DialogStyleManager.DARK.keys()), set(DialogStyleManager.LIGHT.keys()))\n', "        dark, light = (set(DialogStyleManager.DARK), set(DialogStyleManager.LIGHT))\n        self.assertEqual(dark - light, {'image_overlay_bg', 'image_overlay_bg_dark', 'image_overlay_checkbox', 'image_scrollbar_border', 'image_scrollbar_handle', 'image_dropdown_bg', 'image_dropdown_selection', 'image_dropdown_border'})\n        self.assertEqual(light - dark, {'diff_html_equal_bg', 'diff_html_insert_bg', 'diff_html_delete_bg', 'diff_html_header_bg', 'diff_html_line_num', 'diff_html_border', 'diff_html_stats_text'})\n", 1), ("'scrollbar_bg', 'scrollbar_handle', 'scrollbar_handle_hover', ", "'scrollbar_bg', 'scrollbar_handle', ", 1), ("'scrollbar_bg', 'scrollbar_handle_main', 'scrollbar_handle_hover', ", "'scrollbar_bg', 'scrollbar_handle_main', ", 1)]}
    LOST = {'tests/test_error_red.py': ['test_a_fill_clears_the_fill_floor_on_every_ground', 'test_a_fill_is_not_usable_as_text', 'test_the_nine_values_are_the_registered_ones']}
    old_cfg, new_cfg = _original(tree, CFG), tree.read(CFG)
    old_styles, new_styles = _original(tree, STYLES), tree.read(STYLES)

    def value(expr):
        return ast.dump(ast.parse(expr, mode="eval").body)

    def assigned(src, name):
        for node in ast.parse(src).body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) == name:
                return node.value
        raise AssertionError(f"no {name}")

    def styles(src):
        """DialogStyleManager's two palettes -> their entries, and the module without them."""
        mod = ast.parse(src)
        cls = next(n for n in mod.body if isinstance(n, ast.ClassDef) and n.name == "DialogStyleManager")
        held = dict()
        for node in cls.body:
            name = getattr(getattr(node, "target", None), "id", None)
            if name in ("DARK", "LIGHT"):
                held[name] = _entries(node.value)
        cls.body = [n for n in cls.body if getattr(getattr(n, "target", None), "id", None) not in held]
        assert sorted(held) == ["DARK", "LIGHT"], sorted(held)
        return held, ast.dump(mod)

    def app_sources():
        for p in sorted(tree.root.rglob("*.py")):
            rel = p.relative_to(tree.root).as_posix()
            parts = rel.split("/")
            if any(q in ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__")
                   or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "up", "conftest", "run_tests")):
                continue
            text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
            if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def lookups(mod):
        """(key, line, what the receiver is) for each lookup by a written key.
        A receiver that is a name stands for everything that name is assigned
        in the function the lookup is in, and for itself where it is assigned
        nothing there."""
        owner = dict()
        for fn in ast.walk(mod):                   # outer functions first, so the innermost is kept
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(fn):
                    owner[id(node)] = fn
        for node in ast.walk(mod):
            key = receiver = None
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                key, receiver = node.slice.value, node.value
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("get", "pop", "setdefault") \
                    and node.args and isinstance(node.args[0], ast.Constant):
                key, receiver = node.args[0].value, node.func.value
            if not isinstance(key, str):
                continue
            is_a = set([ast.unparse(receiver)])
            if isinstance(receiver, ast.Name):
                is_a = set(ast.unparse(n.value) for n in ast.walk(owner.get(id(node), mod))
                           if isinstance(n, ast.Assign) and len(n.targets) == 1
                           and isinstance(n.targets[0], ast.Name) and n.targets[0].id == receiver.id) or is_a
            yield key, node.lineno, is_a

    # ---- the palettes: the hover out of both; each mode's own keys out of the other; nothing else moves
    (before, rest_b), (after, rest_a) = styles(old_styles), styles(new_styles)
    assert rest_b == rest_a, f"{STYLES} moved beyond its two palettes"
    for name, own in (("DARK", LIGHT_ONLY), ("LIGHT", DARK_ONLY)):
        gone = set(KEYS_GONE) | set(own)
        assert set(before[name]) - set(after[name]) == gone, f"{name} lost {sorted(set(before[name]) - set(after[name]))}"
        assert after[name] == {k: v for k, v in before[name].items() if k not in gone}, \
            f"{name} moved beyond the keys removed"
    assert set(after["DARK"]) ^ set(after["LIGHT"]) == set(LIGHT_ONLY) | set(DARK_ONLY), \
        "the palettes differ by more than the keys one mode reads"

    # ---- the module: three names go, two come at the values the code had, and nothing else moves
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(old_top) - set(new_top) == set(NAMES_GONE), sorted(set(old_top) - set(new_top))
    assert set(new_top) - set(old_top) == set(NEW_VALUES), sorted(set(new_top) - set(old_top))
    for name, expr in NEW_VALUES.items():
        assert new_top[name] == value(expr), f"{name} is not {expr}"
    moved = sorted(n for n in new_top if n in old_top and old_top[n] != new_top[n])
    assert moved == ["PROVENANCE", "__all__"], f"{CFG}: these names moved: {moved}"
    was, now = ast.literal_eval(assigned(old_cfg, "PROVENANCE")), ast.literal_eval(assigned(new_cfg, "PROVENANCE"))
    kept = {k: v for k, v in was.items() if k not in NAMES_GONE}
    assert now == {**kept, "SEMANTIC_EXPORT_FOOTER": "app-semantic"} and set(was) - set(now) == set(NAMES_GONE), \
        "PROVENANCE moved beyond the three names removed and the one added"
    was, now = ast.literal_eval(assigned(old_cfg, "__all__")), ast.literal_eval(assigned(new_cfg, "__all__"))
    assert [n for n in now if n not in NEW_VALUES] == [n for n in was if n not in NAMES_GONE] \
        and sorted(set(now) - set(was)) == sorted(NEW_VALUES), "__all__ moved beyond the names removed and the two added"

    def defined(src):
        return {n.name: ast.dump(n) for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert defined(old_cfg) == defined(new_cfg), f"{CFG}: a function moved"
    missing = [n for n in now if n not in set(new_top) | set(defined(new_cfg))]
    assert not missing, f"__all__ names what is not defined: {missing}"

    # ---- derived, over the whole application: nothing reads what went, and a mode's own key is read by name
    by_name = set()
    for rel, text in app_sources():
        mod = ast.parse(text)
        for node in ast.walk(mod):
            names = []
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                names = [node.id]
            elif isinstance(node, ast.Attribute):
                names = [node.attr]
            elif isinstance(node, ast.ImportFrom):
                names = [a.name for a in node.names]
            for n in names:
                assert n not in NAMES_GONE, f"{rel}:{node.lineno} still names {n}, which this round removes"
        for key, line, is_a in lookups(mod):
            assert key not in KEYS_GONE, f"{rel}:{line} looks up {key!r}, a key this round removes"
            if rel == STYLES:
                continue
            for keys, palette in ((LIGHT_ONLY, "DialogStyleManager.LIGHT"), (DARK_ONLY, "DialogStyleManager.DARK")):
                if key in keys:
                    by_name.add(key)
                    assert is_a == set([palette]), \
                        f"{rel}:{line} reads {key!r} from {sorted(is_a)}: it is in {palette} alone"
    unread = sorted((set(LIGHT_ONLY) | set(DARK_ONLY)) - by_name)
    assert not unread, f"nothing looks up {unread} by name: the palette that keeps them is not read either"

    # ---- the code, the package and the root suite: each moves by what is named, and by nothing else
    for rel, pairs in NAMED.items():
        want, now_u = ast.unparse(ast.parse(_original(tree, rel))), ast.unparse(ast.parse(tree.read(rel)))
        for old, new, times in pairs:
            assert want.count(old) == times, f"{rel}: {old.strip()!r} is written {want.count(old)} times, not {times}"
            want = want.replace(old, new)
        assert now_u == want, f"{rel}: moved beyond naming what it wrote out"

    # ---- the tests: the root suite keeps every test; the two palette snapshots lose the keys; each guard loses what named what went
    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert tests_in(_original(tree, ROOT_SUITE)) == tests_in(tree.read(ROOT_SUITE)), "the root suite gained or lost a test"

    def snapshots(text):
        """The two palette snapshots as the keys and values they hold, and the file without them."""
        held = dict()
        for name in ("test_get_colors_dark", "test_get_colors_light"):
            head = f"# name: TestDialogStyleSnapshots.{name}\n  \'\'\'\n"
            assert text.count(head) == 1, f"{SNAPSHOTS}: no snapshot of {name}"
            start = text.index(head) + len(head)
            end = text.index("\n  \'\'\'\n", start)
            held[name] = json.loads(text[start:end])
            text = text[:start] + text[end:]
        return held, text
    (snap_b, rest_b), (snap_a, rest_a) = snapshots(_original(tree, SNAPSHOTS)), snapshots(tree.read(SNAPSHOTS))
    assert rest_b == rest_a, f"{SNAPSHOTS}: moved beyond the two palette snapshots"
    for name, own in (("test_get_colors_dark", LIGHT_ONLY), ("test_get_colors_light", DARK_ONLY)):
        gone = set(KEYS_GONE) | set(own)
        assert snap_a[name] == {k: v for k, v in snap_b[name].items() if k not in gone} \
            and set(snap_b[name]) - set(snap_a[name]) == gone, f"{SNAPSHOTS}: {name} moved beyond the keys removed"
    assert tests_in(tree.read(GUARD)) == ['test_the_sweep_reads_the_application', 'test_the_sweep_reads_every_spelling', 'test_no_colour_is_written_out_in_the_code', 'test_every_data_entry_still_covers_something', 'test_every_colour_a_palette_holds_is_looked_up', 'test_every_colour_constant_is_read', 'test_every_exported_name_exists', 'test_a_key_one_mode_holds_is_read_from_that_palette_by_name', 'test_the_palettes_differ_only_by_the_keys_one_mode_reads'], f"{GUARD}: its tests are {tests_in(tree.read(GUARD))}"
    for rel in GUARD_FILES[1:]:
        lost = sorted(set(tests_in(_original(tree, rel))) - set(tests_in(tree.read(rel))))
        assert lost == LOST.get(rel, []), f"{rel} lost {lost}"
    assert SENTINEL in new_cfg and SENTINEL in tree.read(GUARD), "the sentinel is not in the palette and its guard"
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""

KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
