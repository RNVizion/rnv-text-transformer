# Architecture

This document describes the internal structure of RNV Text Transformer — its package layout, the design decisions behind it, how data and signals flow between components, and where to extend it.

It complements the high-level feature overview in [README.md](README.md) and the subsystem deep-dives listed in [Subsystem Documentation](#subsystem-documentation).

---

## Contents

- [Design Goals](#design-goals)
- [Package Layout](#package-layout)
- [Dependency Rules](#dependency-rules)
- [Startup Sequence](#startup-sequence)
- [Threading Model](#threading-model)
- [Theming System](#theming-system)
- [Dialog Styling & the BaseDialog Pattern](#dialog-styling--the-basedialog-pattern)
- [Signal Flow](#signal-flow)
- [Caching Strategy](#caching-strategy)
- [Single Source of Truth](#single-source-of-truth)
- [Performance Techniques](#performance-techniques)
- [Extension Points](#extension-points)
- [Known Constraints](#known-constraints)
- [Subsystem Documentation](#subsystem-documentation)

---

## Design Goals

Four principles guide the codebase:

1. **Separation of concerns.** Business logic, UI, utilities, and CLI live in distinct packages with one-way dependencies.
2. **Single source of truth.** No duplicated constants, colors, or version strings. Every piece of configuration has exactly one home.
3. **Performance where it matters.** The UI must never block. Startup must be fast. First-click latency must be minimal.
4. **Consistent appearance.** All dialogs share a unified style system. Theme switches apply everywhere simultaneously.

Every architectural decision below flows from one of these principles.

---

## Package Layout

```
rnv-text-transformer/
├── RNV_Text_Transformer.py     # GUI entry point
│
├── core/     Business logic. Uses PyQt6 where it must: ThemeManager and
│             ResourceLoader hold QPixmaps, PresetManager asks QStandardPaths
│             where to keep presets (the GUI's folder, which the CLI reads
│             too), and the watch rules live in QSettings.
│
├── ui/       PyQt6 widgets, dialogs, and the main window. Depends on core
│             and utils.
│
├── utils/    Cross-cutting services (colors, config, logging, settings
│             persistence, file I/O, atomic writes, error handling, threading
│             primitives, dialog styles). Depends on PyQt6 and the standard
│             library, and in one place on core: the transform worker in
│             async_workers.py runs TextTransformer.
│
├── cli/      Command-line interface. Imports from core and utils, never ui.
│
├── tools/    sync_colors.py and accent_images.py, run by hand and by the tests.
```

The layout follows a layering rule: **upper layers import from lower layers.** `ui` and `cli` sit on top and do not import each other. Below them, `core` imports from `utils`, and `utils` imports from `core` in one place, listed below.

---

## Dependency Rules

```
┌─────────────────┐         ┌─────────────────┐
│       ui        │         │      cli        │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └──────────┬────────────────┘
                    ▼
         ┌─────────────────┐
         │      core       │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │     utils       │
         └─────────────────┘
```

- `utils` imports from PyQt6 and stdlib. It is the foundation, with one exception: `utils/async_workers.py` imports `core.text_transformer` for `TextTransformThread`.
- `core` imports from `utils` and PyQt6 (`QPixmap`, `QIcon`, `QStandardPaths`, `QSettings`).
- `ui` imports from `core`, `utils`, and PyQt6. Full freedom.
- `cli` imports from `core` and `utils`. **Never from `ui`** — the CLI must work headless.

This invariant is worth preserving. It means:

- The CLI can run in environments without a display server.
- Core logic is testable without instantiating a `QApplication`.
- Future refactors (e.g. swapping the GUI framework) would touch only `ui/`.

---

## Startup Sequence

When the user launches the app, `RNV_Text_Transformer.py::main()` runs the following steps in order:

```
 1. Python version check (>= 3.13)
      └─▶ Exit with message if Python is too old
 2. Initialize Logger
 3. QApplication(sys.argv)
 4. app.setStyle("Fusion")
      └─▶ Consistent widget rendering across platforms. It does not
          fix tooltips; see Known Constraints.
 5. FontManager.load_embedded_font()
      └─▶ Loads Montserrat-Black from embedded base64 if there is any
          (the slot holds a placeholder), else from
          resources/fonts/, else falls back to Arial. Cached as ClassVar.
 6. app.setFont(custom_font)
      └─▶ Sets the application-wide default font
 7. DialogStyleManager.prewarm_cache(font_family)
      └─▶ Pre-generates stylesheets for both themes so the first
          dialog opens without stylesheet computation latency.
 8. ResourceLoader.preload_button_images([...])
      └─▶ Pre-loads and caches transform/copy/load/save images
          so the first click in Image Mode is instant.
 9. MainWindow() + window.show()
10. app.exec()
```

Step 7 is particularly important: without stylesheet pre-warming, the first dialog open can stutter noticeably on cold start. Inside `MainWindow()`, the saved settings are applied once the widgets exist: the statistics bar's position, *Show button tooltips*, and *Maximum recent files*, which trims the recent files list. The last step installs the application-wide event filter that draws the themed tooltips.

---

## Threading Model

The UI thread must never block. Two worker threads handle expensive operations.

### `FileLoaderThread`

Defined in `utils/async_workers.py`. Every file the main window loads goes through it: Load, a recent file, and a dropped file.

```
MainWindow              FileLoaderThread
     │                        │
     │ ── start() ───────────▶│
     │                        │ [reads file off UI thread]
     │                        │ progress(10/90/100), which nothing connects
     │ ◄── finished(text, name)│
     │ ◄── error(message) ────│  (instead, on failure)
     │                        │ [thread terminates]
```

### `TextTransformThread`

For transforms applied to very large buffers. Most transforms are fast enough to run synchronously; the helper `should_use_thread_for_transform(text)` in `utils/async_workers.py` decides based on content length (`LARGE_TEXT_THRESHOLD`).

### `FolderWatcher`

Not a `QThread` — uses the `watchdog` library's observer thread and a processing thread of its own. It reports through a callback, not a Qt signal: `WatchFolderDialog` sets it with `set_event_callback()` and shows each event in its activity log. The watcher runs only while that dialog is open; closing it stops the watcher. See `core/folder_watcher.py`.

---

## Theming System

Three modes: `Dark`, `Light`, `Image`. Managed by two collaborating classes:

### `ThemeManager` (in `core/theme_manager.py`)

Holds *state*: which mode is active, whether image-mode resources exist, the loaded background pixmap.

```python
class ThemeManager:
    current_theme: str          # 'dark' | 'light' | 'image'
    image_mode_available: bool  # Set by detect_image_resources()
    image_mode_active: bool
    background_pixmap: QPixmap | None
```

### `DialogStyleManager` (in `utils/dialog_styles.py`)

Holds the *stylesheets*, and serves the palettes, which live in `utils/colors.py`. Has no state — it is a pure function of `(is_dark, font_family)`.

```python
DialogStyleManager.DARK   # dict[str, str] — complete dark palette
DialogStyleManager.LIGHT  # dict[str, str] — complete light palette
DialogStyleManager.get_colors(is_dark) -> dict[str, str]
DialogStyleManager.get_dialog_stylesheet(is_dark, font_family) -> str
```

### Why separate them?

`ThemeManager` answers "what mode are we in?" — it's mutable and belongs to the application session. `DialogStyleManager` answers "what does dark/light look like?" — it's static and describes the design system. Mixing these would make the static color definitions appear to depend on runtime state, which is misleading.

### How Image Mode works

Image Mode is Dark Mode with semi-transparent overlays and a custom background image, shown in a `QLabel` (`background_label`) under the main window's widgets and sized to the window on every resize. The main window's stylesheets use the `image_*` keys of the DARK palette (colors with an alpha channel) for its panes, labels, list and scroll bars. Dialogs in Image Mode take the plain DARK palette, so `DialogStyleManager.DARK` is the only palette consulted when `image_mode_active` is true.

---

## Dialog Styling & the BaseDialog Pattern

Every dialog in the app but `AboutDialog` inherits from `BaseDialog` (defined in `ui/base_dialog.py`). `AboutDialog` is a plain `QDialog` with its own stylesheet, built from the same palette keys. The pattern looks like this:

```python
class MyDialog(BaseDialog):
    _DIALOG_WIDTH: ClassVar[int] = 600
    _DIALOG_HEIGHT: ClassVar[int] = 400
    _DIALOG_TITLE: ClassVar[str] = "My Dialog"

    def __init__(self, theme_manager, font_family="Arial", parent=None):
        super().__init__(theme_manager, font_family, parent)
        self._setup_ui()
        self.apply_base_styling()
```

`BaseDialog` handles:

- Window flags and modality
- Title, size, and positioning
- Theme detection (`_is_dark` from `theme_manager`)
- Calling `DialogStyleManager.get_dialog_stylesheet()` with the correct parameters
- Providing helpers: `_create_close_button()`, `_create_button_row()`, `_create_main_layout()`

This means no `BaseDialog` dialog manually constructs its base stylesheet, stores colors, or hardcodes window flags. The design system is the default, and overriding it requires explicit effort. `refresh_theme()` builds a dialog's sheet again after a theme switch; the main window calls it on every open non-modal dialog.

---

## Signal Flow

Qt's signal/slot system is used extensively to decouple components. The key flows:

### Settings changes

```
SettingsDialog                        MainWindow
     │                                     │
     │ theme_change_requested(str) ───────▶│ _apply_theme_from_settings
     │ settings_changed() ────────────────▶│ _on_settings_changed (tooltips)
     │ stats_position_changed(str) ───────▶│ _update_stats_position
     │ undo_requested() ──────────────────▶│ _undo_output
     │ redo_requested() ──────────────────▶│ _redo_output
     │ open_recent_file_requested(str) ───▶│ _open_recent_file
     │ cleanup_requested(str) ────────────▶│ _apply_cleanup
     │ split_join_requested(str) ─────────▶│ _apply_split_join
     │ export_requested() ────────────────▶│ _open_export_dialog
```

Auto-transform is not a signal: the dialog saves it, and the main window reads it from `SettingsManager` each time the input changes. Most of the dialog's actions are signals that MainWindow handles. Two are not: Clear All and Swap call the parent window's `_clear_all()` and `_swap_input_output()` directly.

### File loading

```
User drops file
     │
     ▼
DragDropTextEdit.dropEvent()
     │
     ▼ emits fileDropped(path)
MainWindow._handle_dropped_file()
     │
     └──▶ FileLoaderThread(path).start()      (every file, any size)
                │
                ├─ finished(text, name) ──▶ MainWindow._on_file_loaded_dragdrop()
                │                            sets the input, then transforms
                └─ error(message) ────────▶ MainWindow._on_file_error()
```

Load (`Ctrl+O`) and a recent file take the same thread, ending in `MainWindow._on_file_loaded()`.

### Folder watching

```
watchdog observer thread
     │
     ▼ (file landed matching a rule)
FolderWatcher processing thread
     │
     ▼ WatchEvent passed to the callback set by set_event_callback()
WatchFolderDialog._on_watch_event()
     │
     ▼ (queued; a timer on the main thread drains it)
the dialog's activity log
```

---

## Caching Strategy

Four distinct caches, each with a different lifetime and invalidation model:

### Stylesheet cache (`DialogStyleManager._cache`)

- **Key:** `(is_dark: bool, font_family: str)`; a second cache, `_component_cache`, adds the extra components a dialog asks for
- **Value:** complete stylesheet string
- **Invalidation:** the oldest entry goes when a cache is full (`_MAX_BASE_CACHE_SIZE`, `_MAX_COMPONENT_CACHE_SIZE`); `DialogStyleManager.clear_cache()` empties both. Stylesheets depend only on theme and font, both of which are stable after startup.
- **Pre-warming:** called at startup for both themes

### Color palette access

- **Key:** `is_dark` (boolean)
- **Value:** the `DARK` or `LIGHT` class-level dict returned by reference
- **Invalidation:** never (palettes are class constants)
- Direct reference return is intentional — no copying, immutable by convention. The docstring explicitly warns "Do not modify the returned dictionary."

### Resource cache (`ResourceLoader`)

- **Key:** image name
- **Value:** loaded `QPixmap`
- **Invalidation:** the oldest entry goes when the cache is full (`_MAX_CACHE_SIZE`); otherwise app-lifetime
- **Pre-warming:** `preload_button_images(['transform', 'copy', 'load', 'save'])` at startup

### Font cache (`FontManager`)

- **Key:** (none — singleton)
- **Value:** loaded `QFont` instance
- **Invalidation:** `FontManager.clear_cache()` (only used in tests)

All four use `ClassVar` storage so they're shared across all instances and survive Qt object lifecycle events.

---

## Single Source of Truth

The project enforces single-source-of-truth for two critical values:

### Version string

- **Lives in:** `utils/config.py` as `APP_VERSION`
- **Read by:** `RNV_Text_Transformer.py` (startup banner), `ui/about_dialog.py` (display), `cli/rnv_transform.py` (`--version`), `pyproject.toml` (via regex extraction at build time)
- **Not written anywhere else**, the README included. No test holds this; `test_rnv_text_transformer.py` checks only that the string has the form `X.Y.Z`.

### Color palette

- **Lives in:** `utils/colors.py` as `DARK` and `LIGHT`, which `DialogStyleManager.DARK` and `.LIGHT` serve. Their keys name constants in the same file.
- **Values come from:** `brand_map.json`, which names each constant's source: a name in rnv-brand at the commit `tests/requirements-dev.txt` pins, or a value the app owns, with the reason. `python tools/sync_colors.py` writes the values into `utils/colors.py` and writes `COLORS.md`; `tests/test_colors_in_sync.py` fails when either is out of date, so a value typed into `utils/colors.py` by hand does not last. Derived steps (`lighten()`, `with_alpha()`) stay code and follow their base. See *Changing a color* in the README.
- **Accessed via:** `DialogStyleManager.get_colors(is_dark)` — returns the class-level dict by reference
- **Every component** that needs a color — main window, every dialog, diff highlighting, regex match coloring, scrollbar styling, exports — reads from this one place
- **No component** ever constructs its own colors

This discipline has real value. When a brand color moves, the change is a new pin and one run of the sync, and the diff of `utils/colors.py` shows exactly what moved. The images do not follow: `ACCENT_IMAGES.md` lists the ones with the gold drawn into their pixels.

---

## Performance Techniques

Specific techniques used throughout:

### `__slots__` on data classes

Every class that holds primarily data (not lots of Python methods) declares `__slots__`. This reduces memory overhead per instance and prevents attribute typos from silently creating new attributes.

```python
class ThemeManager:
    __slots__ = (
        'current_theme',
        'image_mode_available',
        'image_mode_active',
        'background_pixmap',
    )
```

### Lazy imports for heavy modules

`python-docx`, `pypdf`, `striprtf`, and `reportlab` are imported only inside the functions that need them. This shaves noticeable time off cold startup.

```python
def _export_pdf(self, ...):
    from reportlab.lib.pagesizes import letter, A4
    # ... rest of PDF export logic
```

### `frozenset` for O(1) extension lookup

```python
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(SUPPORTED_FORMATS['all'])
```

Checking `path.suffix in SUPPORTED_EXTENSIONS` is constant-time regardless of how many formats are supported.

### `ClassVar` for class-level caches

Ensures caches are shared across instances and don't get caught up in per-instance lifecycle, garbage collection, or copy-on-write semantics.

### Pre-warming at startup

Stylesheet cache and button image cache are populated eagerly during `main()`, trading a small amount of startup time for zero latency on first user interaction.

### Debounced auto-transform

When auto-transform is enabled, transforms run after a 500ms idle timer rather than on every keystroke, preventing UI churn during typing.

---

## Extension Points

The architecture is designed to make common extensions straightforward. Each extension touches a minimal number of files.

### Adding a new transformation mode

1. Add a new variant to the `TransformMode` enum in `core/text_transformer.py`
2. Add the transformation logic (either a new method or a new branch in an existing `match` statement)
3. The mode appears automatically in the main window dropdown, the batch dialog, the watch folder rules, the preset editor, and the CLI's `--mode` check, all of which read `TextTransformer.get_available_modes()`. The CLI's `--list-modes` output is the exception: it prints two hand-kept lists, `get_original_modes()` and `get_developer_modes()`, so add the mode to one of them

### Adding a new export format

1. Add a new variant to the `ExportFormat` enum in `core/export_manager.py`
2. Add a private `_export_<format>()` method
3. Dispatch from the public `export()` method, and, if it needs a library, add a branch to `ExportManager.check_format_dependencies()`
4. The format appears by itself in the `ExportDialog`'s format list, which is built from `ExportFormat`. The list of formats on Settings > Export is written by hand in `ui/settings_dialog.py`

### Adding a new cleanup operation

1. Add a variant to `CleanupOperation` in `core/text_cleaner.py`
2. Implement the operation in `TextCleaner.cleanup()`
3. The new operation appears automatically in the Settings Adjustments tab and the preset editor's Cleanup step (both populated from `TextCleaner.get_cleanup_operations()`). The CLI's `--cleanup` takes it at once, by its snake_case member name (`TextCleaner.operation_key()`) or its value. Its `--list-cleanup` text is written by hand in `CLIProcessor._CLEANUP_GROUPS` (`cli/rnv_transform.py`): add a line there, or `tests/test_cli.py` fails.

### Adding a new dialog

1. Create a new file in `ui/` that subclasses `BaseDialog`
2. Override the `_DIALOG_WIDTH`, `_DIALOG_HEIGHT`, `_DIALOG_TITLE` class constants
3. Build UI in `_setup_ui()`, then call `self.apply_base_styling()`
4. Theme support, window flags, and font are handled automatically. If the dialog is non-modal, open it through `MainWindow._track_open_dialog()` so it follows a theme switch

### Adding a new preset action type

1. Add a variant to `ActionType` in `core/preset_manager.py`
2. Add a branch to `PresetExecutor.execute_step()` match statement, and, for a readable step name, one to `PresetStep.get_display_name()`
3. Presets that already hold the new action (a file imported or edited by hand) execute it at once. To build it in the preset editor, add it to the action list and the parameter widgets in `StepEditorWidget` (`ui/preset_dialog.py`), which are written by hand

---

## Known Constraints

### Windows native tooltip rendering

PyQt6 tooltips on Windows are rendered by the native OS tooltip system, which creates a top-level window with an OS-provided frame that cannot be styled through Qt stylesheets. This is a platform limitation, not a bug.

The workaround is the **custom `_ThemedToolTip` class** in `ui/main_window.py`, which bypasses `QToolTip` entirely. `MainWindow` installs an event filter on the `QApplication`, so it catches the tooltip event of every widget in the app, dialogs included, and shows a frameless `QLabel` with a manual `paintEvent()` that renders a fully themed rounded rectangle. `app.setStyle("Fusion")` does not fix the native frame; the app sets it for consistent widget rendering only.

See [docs/RNV_Custom_Tooltip_System.md](docs/RNV_Custom_Tooltip_System.md) for details.

### Resize events during construction

`MainWindow.__init__()` restores the saved geometry, and may maximize the window, before `_setup_ui()` has built the widgets, so Qt fires `resizeEvent` while some attributes do not exist yet. The handler guards each widget it touches with `hasattr()`:

```python
def resizeEvent(self, event: QResizeEvent) -> None:
    super().resizeEvent(event)
    ...
    if hasattr(self, 'background_label') and self.background_label.isVisible():
        self.background_label.setGeometry(0, 0, w, h)
    if hasattr(self, 'theme_button'):
        ...  # keep it in the bottom-right corner
```

`_setup_theme_button()` positions the button itself when it is made, for the case where that early resize came before it existed. It's defensive, not elegant, but it's the cheapest correct fix.

### Double-encoded UTF-8 ("mojibake")

When text containing special characters (✔, ✘, →, ──) is copied from certain Windows sources, it may arrive as cp1252 bytes interpreted as UTF-8 (or vice versa). Nothing repairs it automatically. The Encoding Converter (`Ctrl+Shift+E`) has an opt-in *Fix mojibake* option, `EncodingDetector.fix_mojibake()` in `ui/encoding_dialog.py`, which encodes the text with the wrong encoding and decodes it with the right one. This is platform-dependent and cannot be fully solved at the application layer.

### Main window decomposition is deferred

`ui/main_window.py` is a large file. Splitting it further (into a window + controller + view orchestrator) was considered and declined — the refactoring risk outweighed the readability gain at this project scale. If the app grows significantly, this decision should be revisited.

---

## Subsystem Documentation

More detailed write-ups, the first two under `docs/`:

- **[docs/RNV_Custom_Tooltip_System.md](docs/RNV_Custom_Tooltip_System.md)** — why Qt's native tooltips are insufficient on Windows, the `_ThemedToolTip` class, singleton coordination, paint logic
- **[docs/RNV_Brand_Color_System.md](docs/RNV_Brand_Color_System.md)** — why there are two golds, which palette key each widget and state takes, the font, and the integration checklist
- **[COLORS.md](COLORS.md)** — every color value, written by `tools/sync_colors.py`

Together with this document, they form the complete architectural record of the project.
