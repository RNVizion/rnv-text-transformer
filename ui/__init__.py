"""
RNV Text Transformer - UI Package
User interface components and dialogs.
"""

from ui.base_dialog import BaseDialog

from ui.main_window import MainWindow

from ui.drag_drop_text_edit import DragDropTextEdit

from ui.image_button import ImageButton

from ui.line_number_text_edit import LineNumberTextEdit

from ui.settings_dialog import SettingsDialog

from ui.about_dialog import AboutDialog

from ui.batch_dialog import BatchDialog

from ui.compare_dialog import CompareDialog

from ui.encoding_dialog import EncodingDialog

from ui.export_dialog import ExportDialog

from ui.find_replace_dialog import FindReplaceDialog

from ui.preset_dialog import PresetDialog, PresetManagerDialog

from ui.regex_builder_dialog import RegexBuilderDialog

from ui.watch_folder_dialog import WatchFolderDialog


__all__ = [
    # Base
    'BaseDialog',
    # Main Window
    'MainWindow',
    # Widgets
    'DragDropTextEdit',
    'ImageButton',
    'LineNumberTextEdit',
    # Dialogs
    'SettingsDialog',
    'AboutDialog',
    'BatchDialog',
    'CompareDialog',
    'EncodingDialog',
    'ExportDialog',
    'FindReplaceDialog',
    'PresetDialog',
    'PresetManagerDialog',
    'RegexBuilderDialog',
    'WatchFolderDialog',
]
