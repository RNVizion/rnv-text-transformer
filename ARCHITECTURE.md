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
├── core/     Business logic. No PyQt6 dependency except where unavoidable
│             (e.g. ThemeManager needs QPixmap for background image caching).
│
├── ui/       PyQt6 widgets, dialogs, and the main window. Depends on core
│             and utils.
│
├── utils/    Cross-cutting services (config, logging, settings persistence,
│             file I/O, error handling, threading primitives, dialog styles).
│             Depends only on PyQt6 and the standard library.
│
├── cli/      Command-line interface. Imports from core and utils, never ui.
```

The layout follows a strict layering rule: **upper layers may import from lower layers, never the reverse.**

---

## Dependency Rules

```
┌─────────────────┐         ┌─────────────────┐
│       ui        │◄────────│      cli        │
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

- `utils` imports only from PyQt6 and stdlib. It is the foundation.
- `core` imports from `utils` and PyQt6 (reluctantly — only for `QPixmap`/`QByteArray`).
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
 1. Python version check (>= 3.10)
      └─▶ Exit with message if Python is too old
 2. Initialize Logger
 3. QApplication(sys.argv)
 4. app.setStyle("Fusion")
      └─▶ Critical: prevents Windows native tooltip frames from
          overriding Qt CSS styling. See Known Constraints.
 5. FontManager.load_embedded_font()
      └─▶ Loads Montserrat-Black from embedded base64 or file,
          falls back to Arial. Cached as ClassVar.
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

Steps 4 and 7 are particularly important. Without the Fusion style, custom tooltip CSS is silently ignored on Windows. Without stylesheet pre-warming, the first dialog open can stutter noticeably on cold start.

---

## Threading Model

The UI thread must never block. Two worker threads handle expensive operations.

### `FileLoaderThread`

Defined in `utils/async_workers.py`. Handles loading of `.docx`, `.pdf`, `.rtf`, and any text file above a size threshold.

```
MainWindow              FileLoaderThread
     │                        │
     │ ── start(path) ───────▶│
     │                        │ [reads file off UI thread]
     │ ◄── progress(50) ──────│
     │ ◄── finished(text) ────│
     │                        │ [thread terminates]
```

### `TextTransformThread`

For transforms applied to very large buffers. Most transforms are fast enough to run synchronously; the helper `should_use_thread_for_transform(text)` in `utils/async_workers.py` decides based on content length.

### `FolderWatcher`

Not a `QThread` — uses the `watchdog` library's observer thread. Emits signals that MainWindow handles on the main thread. See `core/folder_watcher.py`.

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

Holds *palettes and stylesheets*. Has no state — it is a pure function of `(is_dark, font_family)`.

```python
DialogStyleManager.DARK   # dict[str, str] — complete dark palette
DialogStyleManager.LIGHT  # dict[str, str] — complete light palette
DialogStyleManager.get_colors(is_dark) -> dict[str, str]
DialogStyleManager.get_dialog_stylesheet(is_dark, font_family) -> str
```

### Why separate them?

`ThemeManager` answers "what mode are we in?" — it's mutable and belongs to the application session. `DialogStyleManager` answers "what does dark/light look like?" — it's static and describes the design system. Mixing these would make the static color definitions appear to depend on runtime state, which is misleading.

### How Image Mode works

Image Mode is Dark Mode with semi-transparent overlays and a custom background pixmap painted by `MainWindow.paintEvent()`. Dialogs in Image Mode use the `image_overlay_*` keys from the DARK palette (rgba values instead of solid hex), which is why `DialogStyleManager.DARK` is the only palette consulted when `image_mode_active` is true.

---

## Dialog Styling & the BaseDialog Pattern

Every dialog in the app inherits from `BaseDialog` (defined in `ui/base_dialog.py`). The pattern looks like this:

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

This means no dialog manually constructs a stylesheet. No dialog stores colors. No dialog hardcodes window flags. The design system is the default, and overriding it requires explicit effort.

---

## Signal Flow

Qt's signal/slot system is used extensively to decouple components. The key flows:

### Settings changes

```
SettingsDialog                MainWindow
     │                             │
     │ theme_changed(str) ────────▶│ applies theme
     │ auto_transform_changed(b) ─▶│ enables/disables
     │ stats_position_changed(s) ─▶│ repositions stats
     │ undo_requested() ──────────▶│ restores prior output
     │ redo_requested() ──────────▶│ replays output
     │ cleanup_requested(str) ────▶│ runs cleanup op
     │ split_join_requested(str) ─▶│ runs split/join
     │ export_requested() ────────▶│ opens export dialog
```

Settings dialogs never directly manipulate main window state. They emit signals; MainWindow owns the handlers. This is the same pattern as an undo history dialog or a preferences pane in any large Qt app.

### File loading

```
User drops file
     │
     ▼
DragDropTextEdit.dropEvent()
     │
     ▼ emits file_dropped(path)
MainWindow._on_file_dropped()
     │
     ├─── small text file ──▶ FileHandler.read() (sync)
     │
     └─── large or binary ──▶ FileLoaderThread.start(path)
                                       │
                                       ▼ emits finished(text)
                               MainWindow._on_file_loaded()
```

### Folder watching

```
watchdog observer thread
     │
     ▼ (file landed matching rule)
FolderWatcher emits processed(src, dst)
     │
     ▼ (Qt queues signal onto main thread)
MainWindow handler updates status bar
```

---

## Caching Strategy

Three distinct caches, each with a different lifetime and invalidation model:

### Stylesheet cache (`DialogStyleManager._cache`)

- **Key:** `(is_dark: bool, font_family: str)`
- **Value:** complete stylesheet string
- **Invalidation:** never (stylesheets depend only on theme and font, both of which are stable after startup)
- **Pre-warming:** called at startup for both themes

### Color palette access

- **Key:** `is_dark` (boolean)
- **Value:** the `DARK` or `LIGHT` class-level dict returned by reference
- **Invalidation:** never (palettes are class constants)
- Direct reference return is intentional — no copying, immutable by convention. The docstring explicitly warns "Do not modify the returned dictionary."

### Resource cache (`ResourceLoader`)

- **Key:** image name
- **Value:** loaded `QPixmap`
- **Invalidation:** never (resources are app-lifetime)
- **Pre-warming:** `preload_button_images(['transform', 'copy', 'load', 'save'])` at startup

### Font cache (`FontManager`)

- **Key:** (none — singleton)
- **Value:** loaded `QFont` instance
- **Invalidation:** `FontManager.clear_cache()` (only used in tests)

All four caches use `ClassVar` storage so they're shared across all instances and survive Qt object lifecycle events.

---

## Single Source of Truth

The project enforces single-source-of-truth for two critical values:

### Version string

- **Lives in:** `utils/config.py` as `APP_VERSION`
- **Read by:** `RNV_Text_Transformer.py` (startup banner), `ui/about_dialog.py` (display), `pyproject.toml` (via regex extraction at build time)
- **Never duplicated.** Tests enforce this.

### Color palette

- **Lives in:** `utils/dialog_styles.py` as `DialogStyleManager.DARK` and `LIGHT`
- **Accessed via:** `DialogStyleManager.get_colors(is_dark)` — returns the class-level dict by reference
- **Every component** that needs a color — main window, every dialog, diff highlighting, regex match coloring, line number gutters, scrollbar styling — reads from this one place
- **No component** ever constructs its own colors

This discipline has real value. When the brand gold accent changed during development, it was a one-line edit. Had colors been scattered across 20+ files, the same change would have been a days-long audit.

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
3. The mode appears automatically in the main window dropdown, the batch dialog, the watch folder rules, and the CLI's `--list-modes` output — none of those need modification

### Adding a new export format

1. Add a new variant to the `ExportFormat` enum in `core/export_manager.py`
2. Add a private `_export_<format>()` method
3. Dispatch from the public `export()` method
4. Add the option to the `ExportDialog` combo box

### Adding a new cleanup operation

1. Add a variant to `CleanupOperation` in `core/text_cleaner.py`
2. Implement the operation in `TextCleaner.cleanup()`
3. The new operation appears automatically in the Settings Adjustments tab (populated from `TextCleaner.get_cleanup_operations()`)

### Adding a new dialog

1. Create a new file in `ui/` that subclasses `BaseDialog`
2. Override the `_DIALOG_WIDTH`, `_DIALOG_HEIGHT`, `_DIALOG_TITLE` class constants
3. Build UI in `_setup_ui()`, then call `self.apply_base_styling()`
4. Theme support, window flags, and font are handled automatically

### Adding a new preset action type

1. Add a variant to `ActionType` in `core/preset_manager.py`
2. Add a branch to `PresetExecutor.execute_step()` match statement
3. Presets using the new action appear and execute immediately

---

## Known Constraints

### Windows native tooltip rendering

PyQt6 tooltips on Windows are rendered by the native OS tooltip system, which creates a top-level window with an OS-provided frame that cannot be styled through Qt stylesheets. This is a platform limitation, not a bug.

Two workarounds are used:

1. **`app.setStyle("Fusion")`** in startup prevents *some* native styling from leaking through.
2. **Custom `_ThemedToolTip` class** in `ui/main_window.py` bypasses `QToolTip` entirely for the main button bar. It uses a frameless `QLabel` with a manual `paintEvent()` to render a fully themed rounded rectangle.

See [RNV_Custom_Tooltip_System.md](RNV_Custom_Tooltip_System.md) for details.

### Resize event ordering during Fusion style application

Qt fires `resizeEvent` on child widgets before their `__init__` has completed when `setStyle("Fusion")` triggers a style recalculation. Affected handlers use a `hasattr()` guard:

```python
def resizeEvent(self, event):
    if not hasattr(self, '_font_metrics_cache'):
        return
    # ... rest of the handler
```

This prevents AttributeError crashes during early startup. It's defensive, not elegant, but it's the cheapest correct fix.

### Double-encoded UTF-8 ("mojibake")

When text containing special characters (✔, ✘, →, ──) is copied from certain Windows sources, it may arrive as cp1252 bytes interpreted as UTF-8 (or vice versa). Byte-level pattern replacement in `TextCleaner` normalizes the most common cases. This is platform-dependent and cannot be fully solved at the application layer.

### Main window decomposition is deferred

`ui/main_window.py` is a large file. Splitting it further (into a window + controller + view orchestrator) was considered and declined — the refactoring risk outweighed the readability gain at this project scale. If the app grows significantly, this decision should be revisited.

---

## Subsystem Documentation

More detailed write-ups live alongside this file:

- **[RNV_Custom_Tooltip_System.md](RNV_Custom_Tooltip_System.md)** — why Qt's native tooltips are insufficient on Windows, the `_ThemedToolTip` class, singleton coordination, paint logic
- **[RNV_Brand_Color_System.md](RNV_Brand_Color_System.md)** — the dual-gold brand palette, accessibility considerations, how `DARK` and `LIGHT` maintain structural parity

Together with this document, they form the complete architectural record of the project.
