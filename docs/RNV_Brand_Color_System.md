# RNV Brand Color System

## PyQt6 Theme Guide for RNV Applications

**Version:** 1.2  
**Brand:** RNV (Chris Vizirov)  
**Font:** Montserrat Black (fallback: Arial)  
**Framework:** Python 3.13 / PyQt6  
**Applications:** RNV Text Transformer, RNV ICO Builder, RNV Color Mixer

---

## Brand Identity Colors

The RNV brand uses a **gold accent on dark/neutral backgrounds** across all applications. Two gold values exist — a bright gold for dark surfaces and a deeper gold for light surfaces, ensuring proper contrast in both contexts.

| Role | Dark / Image Mode | Light Mode | Usage |
|------|-------------------|------------|-------|
| **Brand Gold (Primary)** | `#d2bc93` | `#b19145` | Accent, borders, selections, hover states |
| **Brand Gold (Hover)** | `#dcc9a3` | `#c4a458` | Lighter tint for hover feedback |
| **Brand Gold (Pressed)** | `#b7a480` | `#8a7236` | Darker shade for pressed/active states |

### Why Two Golds?

`#d2bc93` (bright gold) on a white background has poor contrast (fails WCAG AA). `#b19145` (dark gold) provides proper readability on light surfaces while maintaining the same gold identity. On dark backgrounds, `#d2bc93` reads clearly and feels premium.

### One Accent, Everywhere

Every interactive accent in the app uses brand gold — checkboxes, radio buttons, selections, focused borders, hover states, scrollbar hover, search highlights, line number indicators, info messages, and output text. There are no secondary accent colors. This creates a unified, instantly recognizable brand identity.

---

## Complete Color Dictionaries

### Dark Mode / Image Mode

Used when `theme_manager.current_theme` is `'dark'` or `'image'`. Image Mode shares the same colors but uses semi-transparent backgrounds over a background image.

```python
DARK = {
    # ── Backgrounds ──
    'bg':              '#1A1A1A',   # Primary surface (dialogs, panels)
    'bg_secondary':    '#2A2A2A',   # Cards, inputs, tooltips, elevated surfaces
    'bg_tertiary':     '#333333',   # Disabled buttons, table headers, subtle dividers
    'bg_hover':        '#3A3A3A',   # Hover state for buttons and interactive elements

    # ── Text ──
    'text':            '#E0E0E0',   # Primary text
    'text_muted':      '#888888',   # Secondary/help text, descriptions
    'text_disabled':   '#555555',   # Disabled/inactive text

    # ── Borders ──
    'border':          '#333333',   # Standard borders (inputs, panels, dividers)
    'border_light':    '#444444',   # Subtle borders (internal separators)
    'border_focus':    '#d2bc93',   # Focus ring color (gold)

    # ── Accent (Brand Gold) ──
    'accent':          '#d2bc93',   # Primary accent — buttons, links, active states
    'accent_hover':    '#dcc9a3',   # Hover tint
    'accent_pressed':  '#b7a480',   # Pressed/active shade
    'accent_text':     '#000000',   # Text ON accent background (dark on bright gold)

    # ── Semantic Status Colors ──
    'success':         '#28a745',   # Success messages, confirmations
    'error':           '#dc3545',   # Error messages, destructive actions
    'warning':         '#ffc107',   # Warning messages, caution states
    'info':            '#d2bc93',   # Informational messages, output text (gold)

    # ── Selections ──
    'selection_bg':    '#d2bc93',   # Text selection background
    'selection_text':  '#000000',   # Text selection foreground

    # ── Scrollbars ──
    'scrollbar_bg':    '#252525',   # Scrollbar track
    'scrollbar_handle':'#444444',   # Scrollbar thumb (handle)
    #                  '#d2bc93'    # Scrollbar thumb on hover (uses accent)

    # ── Tooltips ──
    'tooltip_border':  '#d2bc93',   # Tooltip border (gold)
    #                  '#2A2A2A'    # Tooltip background (uses bg_secondary)
    #                  '#E0E0E0'    # Tooltip text (uses text)

    # ── Main Window Specific ──
    'window_bg':       '#000000',   # Main window background (pure black)
    'button_bg':       '#1A1A1A',   # Main window button background
    'button_text':     '#E0E0E0',   # Main window button text
    'button_hover_bg': '#333333',   # Main window button hover
    'button_pressed_text': '#000000', # Text when button is pressed (on gold bg)
    'input_bg':        '#1A1A1A',   # Text input background
    'input_text':      '#E0E0E0',   # Text input foreground
    'input_border':    '#333333',   # Text input border
    'label_bg':        '#000000',   # Label background (matches window)
    'label_text':      '#E0E0E0',   # Label text
    'output_text_color':'#d2bc93',  # Output text area accent (gold)
    'border_color':    '#333333',   # Legacy alias for border
    'text_color':      '#E0E0E0',   # Legacy alias for text
}
```

### Light Mode

Used when `theme_manager.current_theme` is `'light'`.

```python
LIGHT = {
    # ── Backgrounds ──
    'bg':              '#F5F5F5',   # Primary surface (dialogs, panels)
    'bg_secondary':    '#FFFFFF',   # Cards, inputs, tooltips, elevated surfaces
    'bg_tertiary':     '#E8E8E8',   # Disabled buttons, table headers, subtle dividers
    'bg_hover':        '#EEEEEE',   # Hover state for buttons and interactive elements

    # ── Text ──
    'text':            '#000000',   # Primary text
    'text_muted':      '#666666',   # Secondary/help text, descriptions
    'text_disabled':   '#AAAAAA',   # Disabled/inactive text

    # ── Borders ──
    'border':          '#CCCCCC',   # Standard borders (inputs, panels, dividers)
    'border_light':    '#DDDDDD',   # Subtle borders (internal separators)
    'border_focus':    '#b19145',   # Focus ring color (dark gold)

    # ── Accent (Brand Gold — Dark Variant) ──
    'accent':          '#b19145',   # Primary accent — buttons, links, active states
    'accent_hover':    '#c4a458',   # Hover tint
    'accent_pressed':  '#8a7236',   # Pressed/active shade
    'accent_text':     '#FFFFFF',   # Text ON accent background (white on dark gold)

    # ── Semantic Status Colors ──
    'success':         '#28a745',   # Success messages, confirmations
    'error':           '#dc3545',   # Error messages, destructive actions
    'warning':         '#ffc107',   # Warning messages, caution states
    'info':            '#b19145',   # Informational messages, output text (dark gold)

    # ── Selections ──
    'selection_bg':    '#b19145',   # Text selection background
    'selection_text':  '#FFFFFF',   # Text selection foreground

    # ── Scrollbars ──
    'scrollbar_bg':    '#E0E0E0',   # Scrollbar track
    'scrollbar_handle':'#AAAAAA',   # Scrollbar thumb (handle)
    #                  '#b19145'    # Scrollbar thumb on hover (uses accent)

    # ── Tooltips ──
    'tooltip_border':  '#b19145',   # Tooltip border (dark gold)
    #                  '#FFFFFF'    # Tooltip background (uses bg_secondary)
    #                  '#000000'    # Tooltip text (uses text)

    # ── Main Window Specific ──
    'window_bg':       '#F5F5F5',   # Main window background
    'button_bg':       '#FFFFFF',   # Main window button background
    'button_text':     '#000000',   # Main window button text
    'button_hover_bg': '#333333',   # Main window button hover
    'button_pressed_text': '#FFFFFF', # Text when button is pressed (on dark gold bg)
    'input_bg':        '#FFFFFF',   # Text input background
    'input_text':      '#000000',   # Text input foreground
    'input_border':    '#CCCCCC',   # Text input border
    'label_bg':        '#F5F5F5',   # Label background (matches window)
    'label_text':      '#000000',   # Label text
    'output_text_color':'#b19145',  # Output text area accent (dark gold)
    'border_color':    '#CCCCCC',   # Legacy alias for border
    'text_color':      '#000000',   # Legacy alias for text
}
```

---

## Image Mode Transparency Values

Image Mode uses the Dark Mode color dictionary but applies semi-transparent overlays so the background image shows through.

| Element | Value | Opacity | Usage |
|---------|-------|---------|-------|
| Text input / Output | `rgba(0, 0, 0, 171)` | 67% | Main text areas |
| Labels | `rgba(0, 0, 0, 171)` | 67% | Info labels over background |
| Dropdown bg | `rgba(26, 26, 26, 191)` | 75% | ComboBox dropdown |
| Info labels | `rgba(0, 0, 0, 171)` | 67% | Status/stats labels |
| Checkbox indicator | `rgba(0, 0, 0, 100)` | 39% | Unchecked checkbox bg |
| Scrollbar track | `rgba(51, 51, 51, 100)` | 39% | Scrollbar background |
| Scrollbar handle | `rgba(80, 80, 80, 150)` | 59% | Scrollbar thumb |
| Scrollbar hover | `rgba(100, 100, 100, 200)` | 78% | Scrollbar thumb hover |
| Drag highlight | `#BFd2bc93` | 75% | Drag-drop border and fill |

---

## Button Systems

The application uses two distinct button systems with different styling approaches.

### Main Window Buttons (ImageButton)

The main window action buttons (Transform, Copy, Load, Save, Settings) use the custom `ImageButton` class. These buttons have **three rendering modes**:

**Image Mode** — Renders custom PNG graphics (`base`, `hover`, `pressed` states). No CSS background or border. The button images themselves are the branding.

```
QPushButton { border: none; background: transparent; }
```

**Dark / Light Text Mode** — Renders as text-only buttons with a **subtle hover** that only changes background. No gold accent on hover — the main window buttons stay neutral to avoid visual competition with the content area.

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `button_bg` | `button_text` | `border_color` |
| Hover | `button_hover_bg` | `button_text` | `border_color` |

Resolved colors (Dark Mode):

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `#1A1A1A` | `#E0E0E0` | `#333333` |
| Hover | `#333333` | `#E0E0E0` | `#333333` |

Resolved colors (Light Mode):

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `#FFFFFF` | `#000000` | `#CCCCCC` |
| Hover | `#333333` | `#000000` | `#CCCCCC` |

### Main Window Theme Toggle Button

The theme toggle button ("Dark Mode" / "Light Mode" / "Image Mode") at the bottom-right corner uses a separate stylesheet builder. It also has a **subtle hover** without gold accent.

| State | Dark/Image Background | Dark/Image Text | Light Background | Light Text |
|-------|-----------------------|-----------------|-----------------|------------|
| Normal | `#1A1A1A` | `#E0E0E0` | `button_bg` | `button_text` |
| Hover | `#333333` | `#E0E0E0` | `button_hover_bg` | `button_text` |
| Pressed | `#333333` | `#000000` | `button_hover_bg` | `button_pressed_text` |

Font size is fixed at `7.5pt` for the theme button.

### Dialog Buttons (DialogStyleManager)

All dialog buttons (Settings, Batch, Export, Find/Replace, Compare, Encoding, Regex, Presets, Watch Folder) use the `DialogStyleManager` base stylesheet. These buttons have the **full gold accent system** — gold text and border on hover, gold background on press.

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `bg_secondary` | `text` | `border` |
| Hover | `bg_hover` | **`accent`** | **`accent`** |
| Pressed | **`accent`** | `accent_text` | `accent` |
| Disabled | `bg_tertiary` | `text_disabled` | `border` |
| Default (focus) | `bg_secondary` | `text` | **`accent`** |

Resolved colors (Dark / Image Mode):

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `#2A2A2A` | `#E0E0E0` | `#333333` |
| Hover | `#3A3A3A` | **`#d2bc93`** | **`#d2bc93`** |
| Pressed | **`#d2bc93`** | `#000000` | `#d2bc93` |
| Disabled | `#333333` | `#555555` | `#333333` |
| Default | `#2A2A2A` | `#E0E0E0` | **`#d2bc93`** |

Resolved colors (Light Mode):

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Normal | `#FFFFFF` | `#000000` | `#CCCCCC` |
| Hover | `#EEEEEE` | **`#b19145`** | **`#b19145`** |
| Pressed | **`#b19145`** | `#FFFFFF` | `#b19145` |
| Disabled | `#E8E8E8` | `#AAAAAA` | `#CCCCCC` |
| Default | `#FFFFFF` | `#000000` | **`#b19145`** |

### Why Two Different Styles?

The main window is a **content workspace** — the buttons (Transform, Copy, Load, Save) are large, frequently-used tools. Subtle hover keeps attention on the text content. The dialogs are **configuration panels** — buttons need clear visual affordance. Gold hover/pressed states provide stronger feedback that helps users navigate options confidently.

---

## Checkbox & Radio Button Colors

Checkboxes and radio buttons use brand gold across all modes — consistent with every other interactive accent in the app.

| Mode | Checked Background | Checked Border | Hover Border | Unchecked Border | Unchecked Background |
|------|-------------------|----------------|--------------|------------------|----------------------|
| Dark | `#d2bc93` | `#d2bc93` | `#d2bc93` | `#555555` | `#1A1A1A` |
| Image | `#d2bc93` | `#d2bc93` | `#d2bc93` | `#555555` | `rgba(0,0,0,100)` |
| Light | `#b19145` | `#b19145` | `#b19145` | `#AAAAAA` | `#FFFFFF` |

---

## Line Number Gutter Colors

Used by the `LineNumberTextEdit` widget.

| Element | Dark / Image Mode | Light Mode |
|---------|-------------------|------------|
| Gutter background | `#1A1A1A` | `#F0F0F0` |
| Line number text | `#666666` | `#999999` |
| Current line background | `#2A2A2A` | `#E8E8E8` |
| Current line number | `#d2bc93` (gold) | `#b19145` (dark gold) |

---

## Find & Replace Highlight Colors

Search match highlighting uses brand gold for visual consistency.

| Mode | Highlight Color |
|------|----------------|
| Dark / Image | `#d2bc93` |
| Light | `#b19145` |

---

## Font System

| Property | Value | Fallback |
|----------|-------|----------|
| Font family | Montserrat Black | Arial |
| Font file | `Montserrat-Black.ttf` | System font |
| Loading | Embedded base64 or file from `resources/fonts/` | — |
| Applied via | `QApplication.setFont()` at startup | — |

Montserrat Black is applied globally via `QApplication.setFont()`. Individual stylesheets reference the font family via `font-family: '{font_family}'` using the runtime-resolved family name.

ImageButton calculates font size dynamically based on button height: `max(8, int(button_height * 0.28))` pt. The theme toggle button uses a fixed `7.5pt`.

---

## Color Hierarchy & Contrast Rules

### Background Layering (Dark Mode)

```
#000000  ── Main window background (deepest)
#1A1A1A  ── Dialog background, inputs, panels, main buttons
#2A2A2A  ── Cards, tooltips, elevated surfaces, dialog buttons
#333333  ── Table headers, disabled states, dividers, hover states
#3A3A3A  ── Dialog button hover states
```

Each step is approximately `+16` in RGB value, creating a subtle but perceptible depth hierarchy.

### Background Layering (Light Mode)

```
#FFFFFF  ── Cards, inputs, elevated surfaces, dialog buttons (brightest)
#F5F5F5  ── Main window, dialog background, main buttons
#EEEEEE  ── Dialog button hover states
#E8E8E8  ── Table headers, disabled states
#E0E0E0  ── Scrollbar tracks
```

### Text on Background Contrast

| Background | Text Color | Contrast Ratio | WCAG |
|-----------|------------|----------------|------|
| `#000000` | `#E0E0E0` | 14.5:1 | AAA |
| `#1A1A1A` | `#E0E0E0` | 11.4:1 | AAA |
| `#2A2A2A` | `#E0E0E0` | 9.1:1 | AAA |
| `#d2bc93` | `#000000` | 10.2:1 | AAA |
| `#F5F5F5` | `#000000` | 18.1:1 | AAA |
| `#FFFFFF` | `#000000` | 21.0:1 | AAA |
| `#b19145` | `#FFFFFF` | 4.0:1 | AA (large text) |

### Accent on Background

| Background | Accent | Result |
|-----------|--------|--------|
| `#1A1A1A` | `#d2bc93` | Gold text/border on dark — high visibility |
| `#2A2A2A` | `#d2bc93` | Gold border on tooltip — clear definition |
| `#FFFFFF` | `#b19145` | Dark gold on white — sufficient contrast |
| `#F5F5F5` | `#b19145` | Dark gold on light gray — clear accent |

---

## Semantic Color Usage

These colors are consistent across all modes:

| Color | Hex | Usage |
|-------|-----|-------|
| Success | `#28a745` | Operation complete, validation pass |
| Error | `#dc3545` | Errors, destructive actions, delete buttons |
| Warning | `#ffc107` | Caution states, deprecation notices |

Info uses brand gold (consistent with accent):

| Mode | Info Color | Hex |
|------|-----------|-----|
| Dark / Image | Brand gold | `#d2bc93` |
| Light | Dark gold | `#b19145` |

---

## All Accent Surfaces (Quick Reference)

Every interactive element uses brand gold — no secondary colors:

| Element | Dark / Image | Light |
|---------|-------------|-------|
| Dialog button hover text & border | `#d2bc93` | `#b19145` |
| Dialog button pressed background | `#d2bc93` | `#b19145` |
| Dialog button default border | `#d2bc93` | `#b19145` |
| Focus border | `#d2bc93` | `#b19145` |
| Checkbox checked | `#d2bc93` | `#b19145` |
| Radio button checked | `#d2bc93` | `#b19145` |
| Text selection background | `#d2bc93` | `#b19145` |
| Scrollbar hover | `#d2bc93` | `#b19145` |
| Tooltip border | `#d2bc93` | `#b19145` |
| Search highlight | `#d2bc93` | `#b19145` |
| Current line number | `#d2bc93` | `#b19145` |
| Output text color | `#d2bc93` | `#b19145` |
| Info status messages | `#d2bc93` | `#b19145` |
| GroupBox title | `#d2bc93` | `#b19145` |
| Tip text | `#d2bc93` | `#b19145` |
| Version label (About) | `#d2bc93` | `#b19145` |

Note: Main window action buttons (Transform, Copy, Load, Save) do **not** use gold on hover — they use subtle background darkening only. See "Button Systems" section above.

---

## Integration Checklist for New RNV Apps

1. **Set Fusion style**: `app.setStyle("Fusion")` before any UI creation
2. **Load Montserrat Black**: via `QFontDatabase.addApplicationFont()` or embedded base64
3. **Apply font globally**: `app.setFont(custom_font)`
4. **Create color dictionaries**: Copy DARK and LIGHT from this document
5. **Wire theme manager**: Return DARK for dark/image mode, LIGHT for light mode
6. **Image mode transparency**: Use `rgba()` overlays from the transparency table
7. **Use brand gold for ALL accents**: `#d2bc93` on dark, `#b19145` on light — no blue, no secondary colors
8. **Choose button style per context**: Subtle hover for workspace buttons, full gold accent for dialog buttons
9. **Implement custom tooltips**: See `RNV_Custom_Tooltip_System.md`
10. **Set window icon**: Use `ResourceLoader.load_app_icon()` in base dialog and standalone dialogs
11. **Test all three modes**: Dark, Light, Image — verify gold accent visibility in each
