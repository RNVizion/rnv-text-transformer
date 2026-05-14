# RNV Text Transformer — Test Suite

The test suite combines two complementary frameworks: a `unittest` suite for the
core regression tests (frozen, never edited after each release), and a `pytest`
suite for the broader test plan covering UI interactions, property-based tests,
snapshot tests, benchmarks, and gap-fill coverage.

Both suites run under a single coverage report via `run_tests.py`.

---

## Quick start

```bash
# Run everything (both suites + combined coverage report)
python run_tests.py

# Run only the pytest suite
python -m pytest tests/

# Run only the unittest suite
python -m unittest test_rnv_text_transformer

# Run a single pytest file
python -m pytest tests/test_main_window.py -v

# Run with benchmarks (off by default)
python -m pytest tests/test_benchmarks.py --benchmark-enable
```

On Windows, `python -m pytest` is required (not `pytest tests/...`) so the
working directory is added to `sys.path`.

---

## Test inventory

### Frozen regression suite

| File | Tests | Purpose |
|------|------:|---------|
| `test_rnv_text_transformer.py` | 398 | Core regression suite — covers logic, file I/O, transformations, exports, error handling. Frozen at SHA-256 `404d6b93...`; never edited after release. |

### Pytest suite (`tests/`)

| File | Tests | Purpose |
|------|------:|---------|
| `test_main_window.py` | 42 | MainWindow construction, transformation flow, file ops, undo/redo, cleanup, theme cycling, signal handlers |
| `test_compare_dialog.py` | 22 | Compare & merge UI — ChangeWidget signals, navigation, accept/reject all, export, merge signal |
| `test_preset_dialog.py` | 19 | StepEditorWidget + PresetDialog + PresetManagerDialog interactions |
| `test_find_replace_dialog.py` | 16 | Find/replace modes (literal, case-sensitive, whole-word, regex), navigation, highlighting |
| `test_watch_folder_dialog.py` | 16 | RuleEditWidget + WatchFolderDialog — add/remove rules, start/stop watcher, activity log |
| `test_regex_builder_dialog.py` | 15 | Pattern validation, flag computation, match/group tables, replace preview |
| `test_encoding_dialog.py` | 13 | Encoding detection, mojibake fix, conversion preview, EncodingWidget signal |
| `test_batch_dialog.py` | 12 | Source/output browse, file count, start validation, progress + finished handlers |
| `test_dialogs.py` | 22 | Construction + signal smoke tests for every dialog |
| `test_widgets.py` | 13 | Custom widgets (ImageButton, LineNumberTextEdit, DragDropTextEdit) |
| `test_workers.py` | 18 | QThread workers — FileLoaderThread, TextTransformThread, BatchWorkerThread, FolderWatcher |
| `test_cli.py` | 14 | CLI command dispatch, validation errors, output writing, argument parsing |
| `test_logic_gap_fill.py` | 107 | Pure-logic coverage gap-fill across FileHandler, DialogHelper, ErrorHandler, PresetManager, FolderWatcher, ExportManager, ThemeManager |
| `test_properties.py` | 21 | Hypothesis property-based tests for transformations, cleaning, diffs, statistics |
| `test_snapshots.py` | 27 | Syrupy snapshot tests for dialog stylesheets and export formats |
| `test_benchmarks.py` | 6 | Performance benchmarks (import time, stylesheet cache, transforms, diff, file loading) |

**Total: 786 tests** (398 unittest + 388 pytest including 27 snapshots and 6 benchmarks)

---

## Coverage

The project tracks coverage with `coverage.py` and reports it on every run.

Current landing: **~76% on Windows** (Python 3.13).

Per-module highlights (above 85%):
- `core/text_transformer.py` — 99.4%
- `core/text_statistics.py` — 100%
- `cli/__init__.py` — 100%
- `utils/dialog_styles.py` — 94.2%
- `utils/settings_manager.py` — 91.9%
- `core/regex_patterns.py` — 88.9%
- `utils/dialog_helper.py` — 88.5%
- `ui/find_replace_dialog.py` — 87.0%
- `core/preset_manager.py` — 87.0%
- `ui/watch_folder_dialog.py` — 86.7%
- `core/text_cleaner.py` — 85.6%
- `core/export_manager.py` — 85.7%
- `utils/base_dialog.py` — 86.0%

Modules with lower coverage are documented limitations:
- QThread `run()` bodies don't instrument under `coverage.py` (affects `batch_dialog`, `encoding_dialog`, `compare_dialog` scroll-sync handlers)
- CSS stylesheet builders in `main_window.py` are exercised transitively but not per-branch (~315 statements)
- `drag_drop_text_edit.py` event handlers (Qt drag events are hard to simulate)

---

## Conventions

**Fixtures.** Common fixtures live in `tests/conftest.py`:
- `qapp` — single `QApplication` instance shared across tests
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

**Snapshot tests.** Use `syrupy` for stylesheets and export output formats.
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
