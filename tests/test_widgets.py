"""
tests/test_widgets.py
=====================
Phase 3 — Custom widget smoke tests.

Covers:
  ImageButton           (ui/image_button.py, 204 stmts)
  DragDropTextEdit      (ui/drag_drop_text_edit.py, 142 stmts)

Each test instantiates the widget, registers it with qtbot for cleanup,
and verifies one specific behavior (state, signal availability, or
interaction). No deep interaction flows.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtBoundSignal


# ════════════════════════════════════════════════════════════════════════════
# ImageButton — 5 tests
# ════════════════════════════════════════════════════════════════════════════

class TestImageButton:
    """Smoke tests for the ImageButton custom widget."""

    def test_imagebutton_instantiates(self, qtbot):
        """Constructor runs without exception with valid arguments."""
        from ui.image_button import ImageButton
        btn = ImageButton("save", "Save File")
        qtbot.addWidget(btn)
        assert btn is not None

    def test_imagebutton_loads_pixmaps_or_falls_back(self, qtbot):
        """
        ImageButton calls ResourceLoader.load_button_image for base/hover/pressed.
        In a headless test env, these may return None if image files are not
        on the search path. Either outcome (loaded or all-None) is acceptable —
        what matters is that construction doesn't raise.
        """
        from ui.image_button import ImageButton
        btn = ImageButton("save", "Save File")
        qtbot.addWidget(btn)
        # Each pixmap is either a QPixmap or None — never raises
        assert btn.base_pixmap is None or hasattr(btn.base_pixmap, "isNull")
        assert btn.hover_pixmap is None or hasattr(btn.hover_pixmap, "isNull")
        assert btn.pressed_pixmap is None or hasattr(btn.pressed_pixmap, "isNull")

    def test_imagebutton_label_text_set(self, qtbot):
        """The label_text attribute is stored as given."""
        from ui.image_button import ImageButton
        btn = ImageButton("save", "Save File")
        qtbot.addWidget(btn)
        assert btn.label_text == "Save File"
        assert btn.button_name == "save"

    def test_imagebutton_click_emits_clicked(self, qtbot):
        """Clicking the button emits Qt's standard `clicked` signal."""
        from ui.image_button import ImageButton
        btn = ImageButton("save", "Save File")
        qtbot.addWidget(btn)
        btn.show()
        with qtbot.waitSignal(btn.clicked, timeout=1000):
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

    def test_imagebutton_set_theme_manager_applies(self, qtbot, theme_manager_dark):
        """set_theme_manager() stores the manager and triggers apply_style()."""
        from ui.image_button import ImageButton
        btn = ImageButton("save", "Save File")
        qtbot.addWidget(btn)
        btn.set_theme_manager(theme_manager_dark)
        assert btn.theme_manager is theme_manager_dark


# ════════════════════════════════════════════════════════════════════════════
# DragDropTextEdit — 3 tests
# ════════════════════════════════════════════════════════════════════════════

class TestDragDropTextEdit:
    """Smoke tests for the drag-drop-aware text editor."""

    def test_dragdroptextedit_instantiates(self, qtbot):
        from ui.drag_drop_text_edit import DragDropTextEdit
        edit = DragDropTextEdit()
        qtbot.addWidget(edit)
        assert edit is not None

    def test_dragdroptextedit_signals_defined(self, qtbot):
        """All four custom signals are present and reachable."""
        from ui.drag_drop_text_edit import DragDropTextEdit
        edit = DragDropTextEdit()
        qtbot.addWidget(edit)
        for sig_name in ("fileDropped", "loadFileRequested",
                         "saveFileRequested", "clearRequested"):
            assert hasattr(edit, sig_name), f"Missing signal: {sig_name}"
            assert isinstance(getattr(edit, sig_name), pyqtBoundSignal)

    def test_dragdroptextedit_accepts_drops(self, qtbot):
        """acceptDrops() returns True after construction (drag-drop is enabled)."""
        from ui.drag_drop_text_edit import DragDropTextEdit
        edit = DragDropTextEdit()
        qtbot.addWidget(edit)
        assert edit.acceptDrops() is True
