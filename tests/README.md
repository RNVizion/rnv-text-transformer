# RNV Text Transformer — Test Suite

The test suite combines two complementary frameworks: a `unittest` suite for the
core regression tests, and a `pytest` suite for the broader test plan covering UI
interactions, property-based tests, snapshot tests, benchmarks, and gap-fill
coverage.

Both suites run under a single coverage report via `run_tests.py`.

---

## Quick start

```bash
# Run everything (both suites + combined coverage report)
python run_tests.py

# Run only the pytest suite, without the benchmarks
python -m pytest tests/ --benchmark-disable

# Run only the unittest suite
python -m unittest test_rnv_text_transformer

# Run a single pytest file
python -m pytest tests/test_main_window.py -v

# Run only the benchmarks (no coverage)
python run_tests.py --benchmark
```

The benchmarks in `test_benchmarks.py` are timed whenever pytest collects them: a plain
`python -m pytest tests/` runs their timing rounds too. `--benchmark-disable` runs each of
them once, untimed, as an ordinary test; `run_tests.py` and CI pass it.

On Windows, `python -m pytest` is required (not `pytest tests/...`) so the
working directory is added to `sys.path`. Everywhere, run the suites with the venv's
Python (`python -m pytest`, `python -m coverage`) rather than a `pytest` or `coverage`
found on PATH: another interpreter's copy has another rnv-brand, and the pin tests fail.

---

## Test inventory

### Regression suite (`unittest`)

| File | Tests | Purpose |
|------|------:|---------|
| `test_rnv_text_transformer.py` | over 300 | Core regression suite — covers logic, file I/O, transformations, exports, error handling. |

### Pytest suite (`tests/`)

| File | Purpose |
|------|---------|
| `test_main_window.py` | MainWindow construction, transformation flow, file ops, undo/redo, cleanup, theme cycling, signal handlers |
| `test_compare_dialog.py` | Compare & merge UI — ChangeWidget signals, navigation, accept/reject all, export, merge signal |
| `test_preset_dialog.py` | StepEditorWidget + PresetDialog + PresetManagerDialog interactions |
| `test_find_replace_dialog.py` | Find/replace modes (literal, case-sensitive, whole-word, regex), navigation, highlighting |
| `test_watch_folder_dialog.py` | RuleEditWidget + WatchFolderDialog — add/remove rules, start/stop watcher, activity log |
| `test_regex_builder_dialog.py` | Pattern validation, flag computation, match/group tables, replace preview |
| `test_encoding_dialog.py` | Encoding detection, mojibake fix, conversion preview, EncodingWidget signal |
| `test_batch_dialog.py` | Source/output browse, file count, start validation, progress + finished handlers |
| `test_dialogs.py` | Construction + signal smoke tests for every dialog |
| `test_widgets.py` | Custom widgets (ImageButton, DragDropTextEdit) |
| `test_workers.py` | QThread workers — FileLoaderThread, TextTransformThread, BatchWorkerThread, FolderWatcher |
| `test_cli.py` | CLI command dispatch, validation errors, output writing, argument parsing |
| `test_logic_gap_fill.py` | Pure-logic coverage gap-fill across FileHandler, DialogHelper, ErrorHandler, PresetManager, FolderWatcher, ExportManager, ThemeManager |
| `test_properties.py` | Hypothesis property-based tests for transformations, cleaning, diffs, statistics |
| `test_snapshots.py` | Syrupy snapshot tests for dialog stylesheets and export formats |
| `test_benchmarks.py` | Performance benchmarks (import time, stylesheet cache, transforms, diff, file loading) |

These are the suite's first files. Files added since are not listed here, apart from the
guard tests below; each opens with a docstring that says what it holds.

**Total: over 1,000 tests** (over 300 unittest tests and over 600 pytest tests, snapshot tests and benchmarks among them)

---

## Coverage

Coverage is measured on every full run. `python run_tests.py --report` prints the current
figure for every module; it differs a little between Windows and Linux. CI prints the report
at the end of each job.

Modules with lower coverage are documented limitations:
- QThread `run()` bodies don't instrument under `coverage.py` (affects `BatchWorkerThread` in
  `ui/batch_dialog.py`, `DetectionThread` in `ui/encoding_dialog.py`, and the workers in
  `utils/async_workers.py`)
- CSS stylesheet builders in `main_window.py` are exercised transitively but not per-branch
- `drag_drop_text_edit.py` event handlers (Qt drag events are hard to simulate)

---

## Guard tests

Besides the tests of the app's behavior, a set of guard tests holds rules that span the
repository:

| Test | Holds |
|---|---|
| `tests/test_colors_in_sync.py` | the color file and `COLORS.md` are what `brand_map.json` and the pinned brand say |
| `tests/test_register_pin.py` | the installed rnv-brand is the pinned commit |
| `tests/test_atomic_state_writes.py` | every file the app keeps is written atomically |
| `tests/test_status_carried_by_a_word.py` | a status is never shown by color alone: each one has a word or a mark beside it |
| `tests/test_accent_images.py` | `ACCENT_IMAGES.md` matches the images |
| `tests/test_setup_scripts.py` | `in.sh` and `in.ps1` install the same files |
| `tests/test_readme_test_counts.py` | every test count the docs state is a floor that holds |

---

## Conventions

**Fixtures.** Common fixtures live in `tests/conftest.py`:
- `qapp` — the `QApplication`, from pytest-qt; `conftest.py` makes the one instance at the
  start of the session (`_qapplication_singleton`), shared across tests
- `qtbot` — pytest-qt helper (from the plugin)
- `main_window` — fully-constructed `MainWindow` with isolated `QSettings`
- `tmp_settings` — temporary `QSettings` scope so tests don't pollute the user's real settings
- `tmp_workdir` — fresh temporary directory per test

**Modal dialog mocking.** `QFileDialog` and `QMessageBox` are mocked via
`monkeypatch` and `unittest.mock.patch.object` to avoid blocking the test
thread on modal child dialogs.

**QThread handler testing.** Worker threads (`FileLoaderThread`,
`TextTransformThread`, `BatchWorkerThread`, `DetectionThread`) have their
handlers driven directly with hand-emitted signal payloads rather than
spinning up the thread. This sidesteps the `coverage.py` limitation around
QThread bodies while still exercising the dialog's response code paths.

**Snapshot tests.** Use `syrupy` for stylesheets, color dictionaries, export output formats,
and diff renderings.
Re-record snapshots after intentional changes with:

```bash
python -m pytest tests/test_snapshots.py --snapshot-update
```

**Property tests.** Use `hypothesis` with the `default` profile. Re-run a
specific failing seed:

```bash
python -m pytest tests/test_properties.py -k test_name --hypothesis-seed=12345
```

---

## Adding new tests

1. **Smoke tests** for new dialogs → add to `test_dialogs.py`
2. **Interaction tests** for new dialogs → create `test_<dialog_name>.py`
3. **Pure logic** with no Qt dependencies → add to `test_logic_gap_fill.py`
4. **Properties / invariants** → add to `test_properties.py`
5. **New worker threads** → add to `test_workers.py`
6. **CLI commands** → add to `test_cli.py`

Each test file follows the same skeleton: a docstring header summarizing
scope and coverage targets, fixtures at the top, then one test class per
component under test.

---

## Production bugs caught by this suite

| # | Bug | Found by | Severity |
|---|-----|----------|----------|
| 1 | `remove_duplicate_lines` non-idempotent for non-LF separators | Property test | Logic |
| 2 | 4 sibling cleanup functions had the same root cause | Property test | Logic |
| 3 | `preset_dialog._setup_ui` called wrong method name on `TextCleaner` | StepEditorWidget interaction test | Crash |
| 4 | `watch_folder_dialog._load_rule` silently reset `rule.file_patterns` | RuleEditWidget interaction test | **Data loss** |

Each bug has a dedicated regression guard test that fails against the buggy
production code and passes against the fix. See the commit history for
details on each fix.

---

## CI

Tests run on GitHub Actions for both Linux (Ubuntu) and Windows on every push
and pull request. See `.github/workflows/tests.yml`.

Status badges in the project README reflect the most recent CI run per platform.
