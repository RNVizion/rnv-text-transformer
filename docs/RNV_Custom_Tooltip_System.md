# RNV Custom Themed Tooltip System

## PyQt6 Implementation Guide

**Version:** 1.0  
**Tested With:** Python 3.13, PyQt6, Windows 10/11  
**Applications:** RNV Text Transformer, RNV ICO Builder (integration target)

---

## Why This Exists

Qt's built-in `QToolTip` on Windows creates a **native OS popup window** with its own frame. This frame:

- Ignores all CSS `border-radius` styling (always draws square corners)
- Cannot be removed via CSS properties (`opacity`, `background`, etc.)
- Is visible in Light and Image theme modes (blends into Dark Mode by coincidence)
- Persists regardless of `QApplication.setStyleSheet()`, `widget.setStyleSheet()`, or `app.setStyle("Fusion")`

Every CSS-based approach was attempted and failed:

| Approach | Result |
|----------|--------|
| `self.setStyleSheet("QToolTip { ... }")` on QMainWindow | No effect — tooltips are top-level windows, not children |
| `QApplication.setStyleSheet("QToolTip { ... }")` | Partially works but overrides the global app font |
| `opacity: 255` | Qt treats 255 as "use platform default" — no change |
| `opacity: 254` | Forces Qt rendering but square corners persist on first show |
| `app.setStyle("Fusion")` | Helps general rendering but doesn't fix tooltip frame |
| All of the above combined | Square frame still visible in Light/Image modes |

The only reliable solution is to **bypass `QToolTip` entirely** with a custom `QLabel`-based popup that we control at the pixel level.

---

## Architecture Overview

The system has three components:

```
┌─────────────────────────────────────────────────────────────┐
│                    _ThemedToolTip (QLabel)                   │
│  • Singleton instance                                       │
│  • FramelessWindowHint + WA_TranslucentBackground           │
│  • Custom paintEvent() draws rounded rect background        │
│  • Stylesheet only controls text color, padding, font       │
│  • Screen-edge detection keeps tooltip visible              │
│  • Auto-hide timer (5 seconds)                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ show_tip() / hide_tip()
                            │
┌─────────────────────────────────────────────────────────────┐
│              MainWindow.eventFilter()                        │
│  • Installed on QApplication (catches ALL tooltip events)    │
│  • QEvent.Type.ToolTip → show custom tooltip, return True   │
│  • Leave/Click/Deactivate/Wheel → hide custom tooltip       │
│  • Passes theme colors + font family on each show           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ installEventFilter(self)
                            │
┌─────────────────────────────────────────────────────────────┐
│              MainWindow.__init__()                            │
│  • Installs event filter at end of __init__                  │
│  • closeEvent() removes filter + hides tooltip               │
└─────────────────────────────────────────────────────────────┘
```

Widgets still use the standard `widget.setToolTip("text")` API — no changes needed to individual tooltip assignments. The event filter intercepts the tooltip event before the native system processes it.

---

## Complete Implementation

### Required Imports

Add these to your main window file's import block:

```python
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QEvent, QPoint
from PyQt6.QtGui import QCursor, QPainter, QPen, QPainterPath, QColor
```

### The `_ThemedToolTip` Class

Place this **before** your main window class definition. It is a module-level private class — not imported elsewhere.

```python
class _ThemedToolTip(QLabel):
    """
    Custom tooltip that bypasses native Windows tooltip rendering.

    Native QToolTip on Windows creates an OS-level popup window with its own
    frame that cannot be styled via CSS. This class creates a frameless Qt
    widget with WA_TranslucentBackground and paints its own rounded-rect
    background, giving pixel-perfect themed tooltips in all modes.
    """

    _instance: '_ThemedToolTip | None' = None
    _OFFSET_X: int = 16
    _OFFSET_Y: int = 20
    _HIDE_DELAY_MS: int = 5000
    _MAX_WIDTH: int = 400
    _BORDER_RADIUS: int = 4

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(self._MAX_WIDTH)
        self.hide()

        # Colors for paintEvent (updated on each show)
        self._bg_color = QColor("#2A2A2A")
        self._border_color = QColor("#d2bc93")

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    @classmethod
    def instance(cls) -> '_ThemedToolTip':
        """Get or create the singleton tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def paintEvent(self, event) -> None:
        """Paint rounded-rect background and border manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw filled rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                           float(rect.width()), float(rect.height()),
                           self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.fillPath(path, self._bg_color)

        # Draw border
        painter.setPen(QPen(self._border_color, 1.0))
        painter.drawPath(path)
        painter.end()

        # Let QLabel paint the text on top
        super().paintEvent(event)

    def show_tip(self, global_pos: QPoint, text: str,
                 colors: dict, font_family: str) -> None:
        """Show themed tooltip at the given global position."""
        # Store colors for paintEvent
        self._bg_color = QColor(colors['bg_secondary'])
        self._border_color = QColor(colors['tooltip_border'])

        # Title case the tooltip text
        self.setText(text.title())

        # Stylesheet for text only (background/border painted in paintEvent)
        self.setStyleSheet(
            f"color: {colors['text']};"
            f"padding: 4px 8px;"
            f"font-family: '{font_family}';"
            f"background: transparent;"
        )
        self.adjustSize()

        # Position below-right of cursor
        x = global_pos.x() + self._OFFSET_X
        y = global_pos.y() + self._OFFSET_Y

        # Keep tooltip on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            rect = screen.availableGeometry()
            if x + self.width() > rect.right():
                x = global_pos.x() - self.width() - 4
            if y + self.height() > rect.bottom():
                y = global_pos.y() - self.height() - 4

        self.move(x, y)
        self.show()
        self._hide_timer.start(self._HIDE_DELAY_MS)

    def hide_tip(self) -> None:
        """Hide the tooltip and cancel auto-hide timer."""
        self._hide_timer.stop()
        self.hide()
```

### Main Window Integration

#### 1. Install the Event Filter (end of `__init__`)

```python
def __init__(self) -> None:
    super().__init__()

    # ... all your existing init code ...

    # Install application-level event filter for custom themed tooltips
    # (bypasses native Windows tooltip rendering that ignores CSS border-radius)
    QApplication.instance().installEventFilter(self)
```

#### 2. Add the Event Filter Method

Place this method in your main window class (near `resizeEvent`/`closeEvent`):

```python
def eventFilter(self, obj, event) -> bool:
    """
    Application-level event filter for custom themed tooltips.

    Intercepts QEvent.ToolTip to show our custom _ThemedToolTip
    instead of the native OS tooltip (which ignores CSS border-radius
    on Windows Light/Image modes).
    """
    event_type = event.type()

    if event_type == QEvent.Type.ToolTip:
        if isinstance(obj, QWidget) and obj.toolTip():
            _ThemedToolTip.instance().show_tip(
                QCursor.pos(),
                obj.toolTip(),
                self.theme_manager.colors,  # ← your theme color dict
                self.font_family            # ← your font family string
            )
            return True  # Consume event — prevent native tooltip
    elif event_type in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                        QEvent.Type.WindowDeactivate, QEvent.Type.Wheel):
        _ThemedToolTip.instance().hide_tip()

    return super().eventFilter(obj, event)
```

#### 3. Clean Up in `closeEvent`

```python
def closeEvent(self, event) -> None:
    # Remove event filter and hide tooltip
    QApplication.instance().removeEventFilter(self)
    _ThemedToolTip.instance().hide_tip()

    # ... rest of your existing closeEvent code ...
    super().closeEvent(event)
```

---

## Color Dictionary Requirements

The `show_tip()` method expects a `colors` dict with these three keys:

| Key | Purpose | Dark/Image Mode | Light Mode |
|-----|---------|-----------------|------------|
| `bg_secondary` | Tooltip background | `#2A2A2A` | `#FFFFFF` |
| `text` | Text color | `#E0E0E0` | `#000000` |
| `tooltip_border` | Border color | `#d2bc93` (brand gold) | `#b19145` (dark gold) |

Your theme manager's color dictionary must include these keys. If your app uses different key names, update the references in `show_tip()` accordingly.

---

## How It Works (Layer by Layer)

Understanding the rendering stack explains why each piece is necessary:

```
Layer 1: OS Window (transparent)
├── WA_TranslucentBackground makes the OS draw nothing
├── FramelessWindowHint removes the native window frame
└── WindowType.ToolTip gives it tooltip z-order behavior

Layer 2: paintEvent() (our background)
├── QPainterPath creates a rounded rectangle
├── fillPath() fills it with the theme background color
└── drawPath() strokes the border with the theme border color

Layer 3: QLabel text rendering (super().paintEvent)
├── Stylesheet sets color, padding, font
├── "background: transparent" prevents QLabel from painting over Layer 2
└── Text renders on top of our custom background
```

Why each piece is critical:

- **Without `WA_TranslucentBackground`**: The OS fills a solid rectangle behind the widget. Corners of this rectangle are visible when the tooltip overlaps different-colored surfaces.
- **Without custom `paintEvent()`**: `WA_TranslucentBackground` makes the widget fully transparent — no background at all. The `paintEvent` draws the background ourselves with proper rounded corners.
- **Without `background: transparent` in stylesheet**: QLabel's default stylesheet rendering paints a solid rectangle over our rounded background, re-creating the square corner problem.
- **Without `FramelessWindowHint`**: The OS adds its own title bar and frame to the window.
- **Without `WindowType.ToolTip`**: The window doesn't get tooltip z-ordering (always on top, doesn't steal focus).

---

## App Entry Point

Add `app.setStyle("Fusion")` in your application entry point for general rendering consistency:

```python
def main() -> None:
    app = QApplication(sys.argv)

    # Use Fusion style for consistent cross-platform rendering
    app.setStyle("Fusion")

    # ... rest of your app setup ...
```

This is **not** what fixes the tooltip (the custom class does that), but it helps with consistent widget rendering across Windows versions.

---

## Important: Remove All QToolTip CSS

Since the custom tooltip class handles all rendering, **remove** any `QToolTip { }` CSS blocks from:

- Main window stylesheets (`self.setStyleSheet(...)`)
- Dialog base stylesheets
- `QApplication.setStyleSheet(...)` calls

Leaving them in won't break anything, but they serve no purpose and could cause confusion.

---

## Existing Tooltip Assignments (No Changes Needed)

Widgets still use standard PyQt6 tooltip API. No changes required:

```python
# These all work unchanged — the event filter intercepts them
self.transform_btn.setToolTip("Transform text (Ctrl+T)")
self.copy_btn.setToolTip("Copy output to clipboard (Ctrl+Shift+C)")
self.mode_combo.setToolTip("Select text transformation mode")
```

The event filter reads `obj.toolTip()` from any widget and passes the text to `_ThemedToolTip.show_tip()`, which applies `.title()` case formatting before display.

---

## Customization Reference

| Constant | Default | Purpose |
|----------|---------|---------|
| `_OFFSET_X` | `16` | Horizontal offset from cursor (pixels) |
| `_OFFSET_Y` | `20` | Vertical offset from cursor (pixels) |
| `_HIDE_DELAY_MS` | `5000` | Auto-hide after 5 seconds |
| `_MAX_WIDTH` | `400` | Maximum tooltip width before word wrap |
| `_BORDER_RADIUS` | `4` | Corner radius for rounded rectangle |

To change text formatting from Title Case to something else, modify this line in `show_tip()`:

```python
self.setText(text.title())      # Title Case (current)
self.setText(text)              # Keep original case
self.setText(text.upper())      # UPPERCASE
```

---

## Integration Checklist

When adding this system to a new application:

1. **Add imports**: `QEvent`, `QPoint`, `QCursor`, `QPainter`, `QPen`, `QPainterPath`, `QColor`
2. **Add `_ThemedToolTip` class** before your main window class
3. **Add `installEventFilter`** at end of `MainWindow.__init__()`
4. **Add `eventFilter()` method** to MainWindow — update `self.theme_manager.colors` and `self.font_family` references to match your app's API
5. **Add cleanup** to `closeEvent()` — `removeEventFilter` + `hide_tip()`
6. **Ensure color dict** has `bg_secondary`, `text`, and `tooltip_border` keys
7. **Remove all `QToolTip { }` CSS blocks** from stylesheets
8. **Add `app.setStyle("Fusion")`** to app entry point
9. **Test all three theme modes** — Dark, Light, Image
