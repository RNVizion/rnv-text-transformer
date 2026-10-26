# RNV Brand Color System

## PyQt6 Theme Guide for RNV Applications

**Brand:** RNV (Chris Vizirov)  
**Font:** Montserrat Black (fallback: Arial)  
**Framework:** Python 3.13 / PyQt6  
**Applications:** RNV Text Transformer, RNV Icon Builder, RNV Color Mixer

This page says which palette key each part of the app takes, and why. It holds no color values.
The values are in [`COLORS.md`](../COLORS.md), which `python tools/sync_colors.py` writes from
`brand_map.json` and the pinned rnv-brand, together with the color lines of `utils/colors.py`.
Contrast figures belong to the rnv-brand register, which owns them; this page does not repeat them.

---

## Why Two Golds?

The RNV brand uses a gold accent across all applications. One gold cannot serve both themes:
the bright brand gold reads clearly on the dark surfaces, but on white and the light grays it
is too light to carry text or even a border. So each palette has its own gold under the same
keys:

- **Dark and Image mode** take the bright gold, `BRAND_GOLD` (rnv-brand's `APP.accent`).
- **Light mode** takes a deeper gold, `BRAND_DARK_GOLD` (rnv-brand's `APP.accent-light-mode`),
  with the same hue. It is the light palette's fill, border and selection gold.

Light mode has one more step, `BRAND_DARK_GOLD_DEEP`, worked out in `utils/colors.py` from
`BRAND_DARK_GOLD`. As text, the light gold is too faint on the gray grounds a dialog uses, so
every key that puts gold *text* on a light ground (`accent_ink`, `info`) takes the deeper step.
The light palette's hover rows (`accent_hover`) take it too, because they carry white text.
Dark mode needs neither: `accent_ink` and `info` are the accent itself, and its `accent_hover`
is a lighter step of the gold.

The pressed gold is the accent itself in both modes (`accent_pressed`). A darker light-mode
gold would no longer carry black text.

Text on gold: the dark palette puts black on it (`accent_text`, `selection_text`). The light
palette puts white on it under the same keys, while the register's rule is black on gold;
which of the two the light palette should use is an open question.

### One Accent, Everywhere

Every interactive accent in the app is the mode's gold: checkboxes, radio buttons, selections,
focused borders, dialog button hover and press, scrollbar hover, Find's highlights, the output
text, tooltips' borders, group box titles, tips and info messages. There are no secondary
accent colors. The main window's action buttons are the one exception, below.

---

## Which Key Each Part Takes

The keys are in `DARK` and `LIGHT` in `utils/colors.py`; `DialogStyleManager.DARK` and
`.LIGHT` serve the same two dictionaries. Dark and Image mode read `DARK`; Light mode reads
`LIGHT`. Image mode adds the `image_*` keys, which are translucent so the background shows
through; they exist in `DARK` only.

### Dialogs (`utils/dialog_styles.py`)

Every dialog built on `BaseDialog` takes this stylesheet. The About dialog builds its own from
the same keys.

| Part | State | Keys |
|------|-------|------|
| Dialog | | ground `bg`, text `text` |
| Group box | | border `border`, title `accent_ink` |
| Line edit, text edit, combo box, spin box | normal | ground `bg_secondary`, text `text`, border `border` |
| | focus | border `border_focus` |
| | disabled | ground `bg_tertiary`, text `text_disabled` |
| | selected text | `selection_bg`, `selection_text` |
| Combo box list | selected row | `selection_bg`, `selection_text` |
| | hovered row | `accent_hover`, text `selection_text` |
| Check box, radio button | indicator | border `border_light`, ground `bg_secondary` |
| | checked | fill and border `accent` |
| | hover | border `accent` |
| | disabled | text `text_disabled` |
| Push button | normal | ground `bg_secondary`, text `text`, border `border` |
| | hover | ground `bg_hover`, text `accent_ink`, border `accent` |
| | pressed | ground `accent`, text `accent_text` |
| | disabled | ground `bg_tertiary`, text `text_disabled`, border `border` |
| | default | border `accent` |
| Tab bar | tab | ground `bg_secondary`, text `text_muted` |
| | selected tab | ground `bg`, text `accent_ink`, underline `accent` |
| | hovered tab | ground `bg_hover`, text `accent_ink`, underline `accent_pressed` |
| Table, list, tree | rows | ground `bg_secondary`, text `text`, border and grid `border` |
| | selected row | `selection_bg`, `selection_text` |
| | hovered row | `accent_hover`, text `selection_text` |
| | header | ground `bg_tertiary`, text `text` |
| Menu | | ground `bg_secondary`, text `text`, border `border` |
| | selected item | `selection_bg`, `selection_text` |
| Scroll bar | | track `scrollbar_bg`, handle `scrollbar_handle`, hover `accent` |
| Progress bar, slider | | ground `bg_secondary`, border `border`, fill or handle `accent`, handle hover `accent_hover` |
| Splitter handle | | `border`, hover `accent` |
| Header, subtitle, description | | `text`; `text_muted` |
| Tip | | `accent_ink`, italic |
| Status text | | `success`, `warning`, `error`, `info`, muted `text_muted` |

### Feature dialogs

| Part | Keys |
|------|------|
| Find & Replace highlights | `accent`, made translucent (`FIND_HIGHLIGHT_ALPHA`) |
| Regex Builder match highlight | `regex_match_bg` |
| Compare & Merge lines | `diff_added_bg`, `diff_removed_bg`, `diff_changed_bg` |
| Compare & Merge change marks (`+`, `-`, `~`) and Accepted / Rejected / Pending | `success`, `error`, `warning`; `success`, `error`, `text_muted` |
| HTML diff report (exported) | the `diff_html_*` keys of `LIGHT` |
| Encoding detection confidence (high, medium, low) | `success`, `warning`, `error`, with the word beside the figure |
| Export dialog: whether the format's library is installed | `success` or `error`, with a ✔ or ✘ |
| HTML export | *Dark theme* on: `DARK`'s `bg`; off: `LIGHT`'s `bg_secondary`; then `text`, line numbers `text_muted`, `accent` |
| Tooltip | ground `bg_secondary`, text `text`, border `tooltip_border` |
| About: version label and credits line | `accent` |

### Main window (`ui/main_window.py`, `ui/image_button.py`)

| Part | Keys |
|------|------|
| Window ground | `window_bg` |
| Labels | text `label_text`, ground `label_bg` (Image: `image_overlay_bg`) |
| Input and output panes, mode combo box | ground `input_bg` (Image: `image_overlay_bg`), text `input_text`, border `input_border`, selected text `selection_bg` and `selection_text` |
| Output text | `output_text_color` |
| Mode list | Dark: `bg`, `text`, `border`; Light: `bg_secondary`, `text`, `border`; hovered and selected row `list_hover_bg`, `list_hover_text`. Image: `image_dropdown_bg`, `image_dropdown_border`, `image_dropdown_selection` |
| Status, *Output:* and statistics labels | ground `input_bg` (Image: `image_overlay_bg_dark`), text `input_text`, border `input_border` |
| Top bar behind the input label | ground `input_bg` (Image: `image_overlay_bg`), border `input_border` |
| Scroll bars | track `scrollbar_bg`, border `border`, handle `scrollbar_handle_main`, hover `accent`. Image: transparent track, `image_scrollbar_border`, `image_scrollbar_handle`, hover `accent` |
| Action buttons (Transform, Copy, Load, Save) in Dark and Light | normal `main_btn_bg`, `main_btn_text`, border `border_color`; hover `main_btn_hover_bg`, `main_btn_hover_text`; pressed `main_btn_pressed_bg`, `main_btn_pressed_text` |
| Theme button | the same `main_btn_*` keys and `border_color`; in Image mode, while held, `bg_tertiary` and `accent_text` |
| Selection everywhere (the application palette) | `selection_bg`, `selection_text` |

In Image mode the action buttons and the settings gear are PNG images in
`resources/button_images/` (base, hover, pressed); the gear is an image in every mode.

### Why two button styles?

The main window is a content workspace. Its action buttons are large and used all the time,
so their hover stays neutral (`main_btn_*`) and leaves the attention on the text. The dialogs
are configuration panels, where buttons need clear feedback, so their buttons take the gold on
hover and press.

---

## Font System

| Property | Value |
|----------|-------|
| Font family | Montserrat Black, falling back to Arial |
| Font file | `resources/fonts/Montserrat-Black.ttf` |
| Loading | `FontManager.load_embedded_font()` in `utils/config.py`: embedded base64 data if `MONT_FONT_BASE64` holds any (it holds a placeholder), else the file, else Arial |
| Applied via | `QApplication.setFont()` at startup |

Stylesheets name the font with `font-family: '{font_family}'`, using the family name resolved at
run time.

`ImageButton` sizes its label from the button's height, `max(8, int(button_height * 0.28))` pt,
and shrinks it further only when the label would not fit the button's width. The theme button
uses a fixed `7.5pt`.

---

## Integration Checklist for New RNV Apps

1. **Set Fusion style**: `app.setStyle("Fusion")` before any UI is created, for consistent widget
   rendering across platforms.
2. **Load Montserrat Black** with `QFontDatabase.addApplicationFont()` and apply it globally with
   `app.setFont(custom_font)`.
3. **Map each color in `brand_map.json`**, at the repository root: a name in rnv-brand (such as
   `APP.accent`), or a value the app owns, with the reason.
4. **Pin rnv-brand** in `tests/requirements-dev.txt`, and install it.
5. **Write the colors with `python tools/sync_colors.py`.** It writes the value on each mapped
   line of `utils/colors.py` and writes `COLORS.md`. Never type a value into `utils/colors.py`
   by hand; a derived step, such as a lighter or translucent gold, stays code there and follows
   its base.
6. **Add `tests/test_colors_in_sync.py`**, which runs `python tools/sync_colors.py --check`, so a
   hand edit fails the suite.
7. **Build `DARK` and `LIGHT` from those names** in `utils/colors.py`, with the same keys in both,
   plus the `image_*` keys in `DARK` for Image mode.
8. **Wire the theme manager**: `DARK` for Dark and Image mode, `LIGHT` for Light mode.
9. **Use the gold keys for every accent**: `accent` for fills, borders and selections,
   `accent_ink` for gold text. No secondary accent colors.
10. **Choose the button style per context**: neutral `main_btn_*` hover for workspace buttons, the
    full gold for dialog buttons.
11. **List the images that carry the gold** with `python tools/accent_images.py`, which writes
    `ACCENT_IMAGES.md`; they are redrawn by hand when the gold moves.
12. **Implement custom tooltips**: see [`RNV_Custom_Tooltip_System.md`](RNV_Custom_Tooltip_System.md).
13. **Set the window icon**: `ResourceLoader.load_app_icon()` in the base dialog and standalone dialogs.
14. **Test all three modes**: Dark, Light, Image.
