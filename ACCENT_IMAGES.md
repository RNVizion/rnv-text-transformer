# Images that carry the accent

Written by `tools/accent_images.py` (#86 A). Do not edit by hand: after adding or changing an image, run `python tools/accent_images.py`. `tests/test_accent_images.py` fails until this file is what the tool writes.

If the accent ever moves, the code moves it in ten lines; these images do not move with it. **shaded** art is hand-made and is remade by hand (#84). **flat** art could be recolored by swapping exact colors. A **screenshot** is retaken. A **fixture** is a test input. Accent: hue within 6 degrees of `BRAND_GOLD` or `BRAND_DARK_GOLD`, saturation and value at least 0.15; an image carries it from 1% of its pixels; flat means its three commonest accent colors cover at least 90% of them. The tool's docstring says why.

**19 images of art carry the accent, 19 of them distinct.**

| folder | files | shaded | flat | screenshot | fixture | none |
|---|---|---|---|---|---|---|
| `resources/background_images` | 1 | 1 | 0 | 0 | 0 | 0 |
| `resources/button_images` | 15 | 15 | 0 | 0 | 0 | 0 |
| `resources/icons` | 3 | 3 | 0 | 0 | 0 | 0 |
| `resources/screenshots` | 6 | 0 | 0 | 6 | 0 | 0 |

## `resources/background_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `background.png` | 3840x2160 | 100.0% | 13416 | shaded |  |

## `resources/button_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `copy_base.png` | 500x167 | 26.8% | 2148 | shaded |  |
| `copy_hover.png` | 500x167 | 26.7% | 2096 | shaded |  |
| `copy_pressed.png` | 500x167 | 35.6% | 2502 | shaded |  |
| `load_base.png` | 500x167 | 27.1% | 2097 | shaded |  |
| `load_hover.png` | 500x167 | 27.4% | 2296 | shaded |  |
| `load_pressed.png` | 500x167 | 36.9% | 2556 | shaded |  |
| `save_base.png` | 500x167 | 27.4% | 2350 | shaded |  |
| `save_hover.png` | 500x167 | 27.3% | 2095 | shaded |  |
| `save_pressed.png` | 500x167 | 37.3% | 2097 | shaded |  |
| `settings_gear_base.png` | 512x512 | 93.4% | 3390 | shaded |  |
| `settings_gear_hover.png` | 512x512 | 92.9% | 2888 | shaded |  |
| `settings_gear_pressed.png` | 512x512 | 93.1% | 3418 | shaded |  |
| `transform_base.png` | 500x167 | 30.3% | 2178 | shaded |  |
| `transform_hover.png` | 500x167 | 30.9% | 1903 | shaded |  |
| `transform_pressed.png` | 500x167 | 36.7% | 2310 | shaded |  |

## `resources/icons`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `app_icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.png` | 512x512 | 81.1% | 3602 | shaded |  |

## `resources/screenshots`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `batch-processing.png` | 1920x1080 | 65.4% | 17899 | screenshot |  |
| `compare-dialog.png` | 1920x1080 | 38.3% | 21509 | screenshot |  |
| `dark-mode.png` | 1920x1080 | 0.0% | 484 | screenshot |  |
| `image-mode.png` | 1920x1080 | 83.0% | 16824 | screenshot |  |
| `light-mode.png` | 1920x1080 | 0.0% | 435 | screenshot |  |
| `regex-builder.png` | 1920x1080 | 27.7% | 21351 | screenshot |  |
