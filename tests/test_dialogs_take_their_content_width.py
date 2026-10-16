"""Find, Find and Replace, and Settings' list of export formats give their text the room it asks for.

RNV-RULINGS-2026-10-15, items 12 and 35. Ruled 2026-10-15, after a look at
the dialogs on Chris's PC: "12 looks like it might need a little room" (A),
and "#35 A."

WHAT WAS THERE.
(12) Both Find dialogs were fixed at 450 pixels wide. Find and Replace's
     content asks for more: Find Next, Replace and Replace All were cut
     short, and Close ran past the dialog's edge. Find's asks for a little
     more, and Regular expression was cut in both.
(35) Settings > Export listed the formats with their names in a column
     fixed at 200 pixels. Two lost their closing bracket: "Word Document
     (.docx" and "HTML Document (.html".

WHAT IS THERE NOW.
(12) Each dialog takes the width its content asks for, and never less than
     450. It is worked out from the content as it is styled, each time the
     dialog is shown.
(35) The names sit in a grid column as wide as the longest of them.

WHAT THIS GUARD HOLDS.
1. In every mode the theme button reaches, each Find dialog, opened through
   the main window's own opener: every button, check box and radio button
   with text gets at least the width it asks for and ends inside the
   dialog; the dialog is never narrower than 450. The same for a dialog
   left open across each switch.
2. The width is worked out, not written: a button whose text grows is cut
   while the dialog stays as it is, and given its room when the dialog is
   next shown.
3. Settings > Export: every format's name and description gets the width
   its text needs, in its own font, and the measure sees a name that does
   not; and a longer name is given its room,
   so the column follows the names rather than a number. (Here the six fit
   in 200; on Chris's PC two did not. The second check is the one that
   holds the column, wherever it runs.)
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QAbstractButton, QApplication, QDialog, QGroupBox, QLabel

from ui.find_replace_dialog import FindReplaceDialog
from ui.settings_dialog import SettingsDialog
from utils.config import FontManager

FLOOR = 450
OPENERS = ("_open_find_dialog", "_open_replace_dialog")


@pytest.fixture
def window(qapp, main_window):
    """The main window, with the font main() gives the application: Montserrat
    at 10 points. Without it the dialogs are measured in another font, which
    asks for less room than the one the app draws in."""
    before = qapp.font()
    qapp.setFont(FontManager.load_embedded_font())
    yield main_window
    qapp.setFont(before)


def _settle() -> None:
    for _ in range(3):
        QApplication.processEvents()


def _mode(win) -> str:
    tm = win.theme_manager
    return "image" if tm.is_image_mode() else str(tm.current_theme)


def _each_mode(win):
    """Every mode the theme button reaches, once each, ending in the mode it began in."""
    start, seen = _mode(win), []
    while _mode(win) not in seen:
        seen.append(_mode(win))
        yield seen[-1]
        win.theme_button.click()
        _settle()
    assert _mode(win) == start, (start, _mode(win))


def _opened(win, opener: str) -> FindReplaceDialog:
    before = {id(d) for d in win.findChildren(FindReplaceDialog)}
    getattr(win, opener)()
    _settle()
    new = [d for d in win.findChildren(FindReplaceDialog) if id(d) not in before and d.isVisible()]
    assert len(new) == 1, (opener, len(new))
    return new[0]


def _cut(dialog) -> list:
    """Every control with text that gets less than it asks for, or ends past the dialog's edge."""
    out = []
    for w in dialog.findChildren(QAbstractButton):
        if not w.isVisible() or not w.text().strip():
            continue
        right = w.mapTo(dialog, w.rect().topRight()).x()
        if w.width() < w.sizeHint().width() or right > dialog.width() - 1:
            out.append((w.text(), w.width(), w.sizeHint().width(), right, dialog.width()))
    return out


def test_every_control_of_both_find_dialogs_gets_its_room(window):
    win = window
    looked = []
    for mode in _each_mode(win):
        for opener in OPENERS:
            dialog = _opened(win, opener)
            assert dialog.width() >= FLOOR, (mode, opener, dialog.width())
            assert not _cut(dialog), (mode, opener, _cut(dialog))
            looked.append((mode, opener, len(dialog.findChildren(QAbstractButton))))
            dialog.close()
            _settle()
    assert len({m for m, _o, _n in looked}) >= 2, f"the theme button reached only {looked}"
    assert all(n >= 6 for _m, _o, n in looked), looked


def test_a_dialog_left_open_keeps_its_room_across_a_switch(window):
    win = window
    dialog = _opened(win, "_open_replace_dialog")
    for mode in _each_mode(win):
        _settle()
        assert not _cut(dialog), (mode, _cut(dialog))
    dialog.close()


def test_the_width_is_worked_out_not_written(window):
    """A label that grows gets its room when the dialog is next shown."""
    win = window
    dialog = _opened(win, "_open_replace_dialog")
    first = dialog.width()
    dialog.replace_all_btn.setText(dialog.replace_all_btn.text() + " occurrences in the text")
    _settle()
    assert _cut(dialog), "a label grown in a dialog left as it is was not seen cut: the measure is blind"
    dialog.hide()
    dialog.show()
    _settle()
    assert not _cut(dialog), _cut(dialog)
    assert dialog.width() > first, (first, dialog.width())
    dialog.close()


@pytest.fixture
def settings_dialog(window, monkeypatch):
    """Settings, opened through the main window's own opener, shown rather than run."""
    monkeypatch.setattr(QDialog, "exec", lambda self: self.show() or 0)
    window._open_settings()
    _settle()
    shown = [d for d in window.findChildren(SettingsDialog) if d.isVisible()]
    assert len(shown) == 1, len(shown)
    yield shown[0]
    shown[0].close()


def _formats(dialog) -> list:
    tabs = dialog.tab_widget
    export = [i for i in range(tabs.count()) if "Export" in tabs.tabText(i)]
    assert len(export) == 1, [tabs.tabText(i) for i in range(tabs.count())]
    tabs.setCurrentIndex(export[0])
    _settle()
    group = [g for g in dialog.findChildren(QGroupBox) if g.title() == "Available Formats"]
    assert len(group) == 1, len(group)
    labels = group[0].findChildren(QLabel)
    assert len([lab for lab in labels if "(." in lab.text()]) == 6, [lab.text() for lab in labels]
    return labels


def _short(labels) -> list:
    """Every label whose text is wider than the room it is given. A label given a fixed width reports that
    width as the width it asks for, so the text is measured in the label's own font."""
    return [(lab.text(), lab.contentsRect().width(), lab.fontMetrics().horizontalAdvance(lab.text()))
            for lab in labels if lab.contentsRect().width() < lab.fontMetrics().horizontalAdvance(lab.text())]


def test_every_export_format_name_gets_its_room(settings_dialog):
    labels = _formats(settings_dialog)
    assert not _short(labels), _short(labels)


def test_the_measure_sees_a_cut_name(settings_dialog):
    labels = _formats(settings_dialog)
    name = [lab for lab in labels if "(." in lab.text()][0]
    name.setFixedWidth(name.fontMetrics().horizontalAdvance(name.text()) // 2)
    _settle()
    assert _short([name]), "a name squeezed to half its text was not seen cut: the measure is blind"


def test_a_longer_format_name_is_given_its_room(settings_dialog):
    labels = _formats(settings_dialog)
    name = max((lab for lab in labels if "(." in lab.text()),
               key=lambda lab: lab.fontMetrics().horizontalAdvance(lab.text()))
    name.setText(name.text() + " and .dotx")
    _settle()
    assert not _short(labels), _short(labels)
