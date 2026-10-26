# Changelog

All notable changes to RNV Text Transformer are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is
`APP_VERSION` in `utils/config.py`.

## [Unreleased]

Changes since 3.3.0, the version of May 2026. The version number has not moved since.

### Added

- **Colors from the brand, written by a script.** `brand_map.json` names where each of the
  app's colors comes from: a name in rnv-brand or a value the app owns, with the reason.
  `python tools/sync_colors.py` writes the values into `utils/colors.py` and writes
  `COLORS.md`, the chart of the app's colors; `--check` writes nothing and fails when either
  is out of date. A daily `brand-sync` workflow opens a pull request only when a color the app
  uses has moved in rnv-brand.
- **Accent images listed.** `tools/accent_images.py` writes `ACCENT_IMAGES.md`, the list of
  button, background and icon images with the gold drawn into their pixels, which must be
  redrawn by hand when the gold moves. It never changes an image.
- **Atomic preset saves.** `utils/atomic_write.py` writes a temporary file beside the target,
  flushes it to disk and replaces the original in one step, so a crash or a full disk during a
  save leaves the old presets file or the new one, never half of each.
- **Setup scripts.** `in.sh` (Linux and Codespaces; it also installs the Qt system libraries)
  and `in.ps1` (Windows; it makes `.venv` with Python 3.13 if there is none) install
  `requirements.txt` and `tests/requirements-dev.txt`.
- **Guard tests** for rules that span the repository: the colors are in sync with the map and
  the pinned brand (`test_colors_in_sync`), the installed rnv-brand is the pinned commit
  (`test_register_pin`), the presets file is written atomically (`test_atomic_state_writes`),
  no status is shown by color alone (`test_status_carried_by_a_word`), `ACCENT_IMAGES.md`
  matches the images (`test_accent_images`), and the two setup scripts install the same files
  (`test_setup_scripts`). Others hold the contrast of the gold as text and as a fill, the
  button keys, the dependency declarations, the size of the image resources, the workflow
  actions, and the test counts the documents state (`test_readme_test_counts`).
- A `CHANGELOG.md`.

### Changed

- **Python 3.13 is required.** `pyproject.toml` says `requires-python = ">=3.13"`, the entry
  point checks for 3.13, and CI runs 3.13 on Linux and Windows. Earlier releases said 3.10.
- **rnv-brand is pinned.** `tests/requirements-dev.txt` installs rnv-brand from GitHub at a
  fixed commit, and the color tests compare the app's values with it. Installing the dev
  requirements now needs `git` and network access.
- **The palette.** The colors moved into `utils/colors.py`, with the `DARK` and `LIGHT`
  palettes, and are written from the brand. The light gold is now a deeper value that holds
  its contrast on white, and gold text and hover rows in light mode take a deeper step of it.
  The dark text gray, the status colors and the scroll bars follow the brand. Every hex value
  in the source is lower case.
- **Encoding detection** says its confidence in a word (high, medium, low) beside the
  percentage, so it no longer rests on color alone.
- **Smaller images.** The window background is 3840 pixels on the long edge, and the settings
  gear and the app icon were reduced to 512, cutting the download by tens of megabytes.
- **Find and Settings dialogs** take the width their content asks for, so no button or format
  name is cut short.
- **Dependencies.** `tests/requirements-dev.txt` moved under `tests/`, and the dev tool ranges
  are the same in all five RNV apps. `requirements.txt` and `pyproject.toml` declare the same
  ranges.
- **CI** uses the Node 24 versions of its actions, and ends each job by printing the coverage
  report in its own log instead of sending it to an outside service.
- **Maximum recent files** (Settings) is applied. The recent files list keeps that many
  files; it kept ten whatever the setting said. Lowering it drops the oldest files from the
  list at once, *Disabled* (0) keeps none, and the limit is applied again at startup.
- **The documentation** was brought in line with the code: the README's features, keyboard
  shortcuts, CLI options and project tree; ARCHITECTURE's subsystems and links; the test guide;
  the brand color guide, cut to what `COLORS.md` does not hold; and the About dialog and the
  entry point's docstring. `run_tests.py` runs `coverage` through the interpreter running it,
  so it uses the venv's own.

### Fixed

- **Show button tooltips, turned off, stays off.** The setting was saved but not read at
  startup, so the main window's button tooltips came back on at the next start.
- **CLI presets.** `rnv-transform --preset NAME` stopped with
  `PresetExecutor.__init__() takes 1 positional argument but 2 were given` and wrote nothing.
  It applies the preset now.
- **Watch-folder presets.** A watch rule with a preset failed on every file with the same
  error, and wrote nothing. The preset is applied now, the way the main window applies it,
  and a rule's cleanup steps run too.
- **CLI cleanup.** `rnv-transform --cleanup` refused the names it documents, such as
  `trim_whitespace,remove_blank_lines`, and stopped with an error when given a name as the GUI
  shows it. It takes both now. `--list-cleanup` lists every operation `--cleanup` takes, and
  no longer lists four it never had (`reverse_lines`, `number_lines`, `remove_non_ascii`,
  `remove_punctuation`).
- **Built-in presets.** Every cleanup step in the six built-in presets named an operation that
  does not exist, so it did nothing: *Markdown Cleanup* and *Plain Text Export* returned the
  text unchanged. Each step now runs the operation it meant. A preset saved with the old
  names, such as a duplicate of a built-in, is read the same way.
- **One presets folder.** The GUI and the CLI kept presets in different folders, so a preset
  made in the GUI was not listed by the CLI. Both use the GUI's folder now. Presets in the
  CLI's old folder are still read and merged in, and that folder is left as it was.
- **Installed copies have their resources.** A wheel built from the repository (`pip install .`)
  left out `resources/`, so the installed app had no font, icons, button images or background,
  fell back to Arial and offered no Image mode. The wheel carries `resources/` now, beside
  `utils/`, where the app looks for it.
- **Project links.** The homepage, repository and issues links in `pyproject.toml` named an
  `RNVSoftware` organization; they point at `RNVizion/rnv-text-transformer` now.
- **Find & Replace.** The *Search in: Input / Output* choice now decides the pane searched,
  highlighted and replaced, and a replacement in the output joins its undo history. Find Next
  and Replace follow the text as it now is, after typing or a new transform. An option ticked
  after a Find takes effect at once, a plain replacement is no longer read as a regular
  expression's template, and matches after an emoji are highlighted in the right place.
- **Highlights are not edits.** Find's and the Regex Builder's highlights no longer count as
  changes of the text: they no longer re-run Auto-transform, fill the undo history, or travel
  to the clipboard, and clearing them leaves the caret where it was.
- **Theme switches.** Find, Find & Replace, the Regex Builder, Watch Folders and Compare follow
  a theme switch made while they are open, Find's highlights included, and Settings restyles
  itself when it switches the theme.
- **Regex Builder** highlights and selects a match where it is when the text holds an emoji.
- **Cleanup** operations that work line by line no longer drop a final blank line, and give the
  same result when run twice.

### Removed

- The unused line-number widget, `ui/line_number_text_edit.py`, which no part of the app
  created, with its four palette colors. The README's *Considered for Later* section records
  what a rebuilt one would need.
- The CI step that uploaded the coverage report to an outside service.

Earlier history is in the git log.
