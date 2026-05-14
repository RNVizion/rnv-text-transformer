# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for RNV Text Transformer
================================================

Builds a standalone Windows distribution bundle.

Default mode: one-folder (faster startup, easier debugging).
See bottom of file for how to switch to one-file mode.

Usage:
    pyinstaller RNV_Text_Transformer.spec              # standard build
    pyinstaller --clean RNV_Text_Transformer.spec      # clean rebuild
    pyinstaller --noconfirm RNV_Text_Transformer.spec  # skip prompts

Output:
    dist/RNV Text Transformer/RNV Text Transformer.exe
"""

from pathlib import Path

# ==================== PATHS ==================================================

PROJECT_ROOT = Path(SPECPATH).resolve()
RESOURCES_DIR = PROJECT_ROOT / 'resources'

ENTRY_POINT = 'RNV_Text_Transformer.py'
APP_NAME = 'RNV Text Transformer'

# Pick the first available icon in resources/icons/
_icon_candidates = [
    RESOURCES_DIR / 'icons' / 'app.ico',
    RESOURCES_DIR / 'icons' / 'rnv.ico',
    RESOURCES_DIR / 'icons' / 'icon.ico',
]
APP_ICON = next((str(p) for p in _icon_candidates if p.exists()), None)


# ==================== ANALYSIS ===============================================
# Declares what files to include and which imports to resolve.

a = Analysis(
    [ENTRY_POINT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],

    # ---- Data files bundled with the app ------------------------------------
    # Preserves the resources/ folder structure so the runtime path resolution
    # in utils/config.py (BASE_DIR / "resources") continues to work.
    datas=[
        ('resources', 'resources'),
    ],

    # ---- Hidden imports -----------------------------------------------------
    # These modules are imported inside functions (lazy imports for fast
    # cold-start) so PyInstaller's static analyzer cannot detect them.
    hiddenimports=[
        # Document processing (lazy-loaded in file_handler / export_manager)
        'docx',
        'docx.shared',
        'docx.enum.text',
        'pypdf',
        'striprtf',
        'striprtf.striprtf',

        # PDF export (lazy-loaded in export_manager)
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'reportlab.platypus',
        'reportlab.pdfgen',
        'reportlab.pdfbase',

        # Encoding detection
        'chardet',

        # File system monitoring
        'watchdog',
        'watchdog.observers',
        'watchdog.events',

        # PyQt6 modules (usually auto-detected, listed for safety)
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',

        # PIL submodules sometimes missed
        'PIL',
        'PIL.Image',
        'PIL.ImageQt',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # ---- Excludes -----------------------------------------------------------
    # Not used by the app; excluding keeps the bundle size smaller.
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'notebook',
        'pytest',
        'unittest',
    ],

    noarchive=False,
    optimize=0,
)


# ==================== PYZ ====================================================
# Creates the zip archive of pure Python modules.

pyz = PYZ(a.pure)


# ==================== EXE (one-folder mode) ==================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # one-folder mode
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                     # compress if UPX is installed (optional)
    console=False,                # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
    version=None,                 # set to a version info file path if desired
)


# ==================== COLLECT ================================================
# Gathers everything into the final dist folder.

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)


# ==================== ONE-FILE MODE (alternative) ============================
#
# For a single standalone .exe instead of a folder, comment out the EXE and
# COLLECT blocks above and uncomment the block below. Trade-off: slower cold
# start (exe must unpack to a temp directory on every launch).
#
# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.datas,
#     [],
#     name=APP_NAME,
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon=APP_ICON,
# )
