@echo off
REM ============================================================================
REM RNV Text Transformer - Windows Build Script
REM ============================================================================
REM Builds a standalone Windows distribution using PyInstaller and the bundled
REM RNV_Text_Transformer.spec file.
REM
REM Output: dist\RNV Text Transformer\RNV Text Transformer.exe
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================================
echo   RNV Text Transformer - Windows Build
echo ============================================================================
echo.

REM ── Step 1: Activate venv if present ────────────────────────────────────────
if exist ".venv\Scripts\activate.bat" (
    echo [1/5] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [1/5] No .venv found - using system Python
)

REM ── Step 2: Verify PyInstaller is installed ─────────────────────────────────
echo [2/5] Checking PyInstaller installation...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller is not installed.
    echo.
    echo Install it with:
    echo     pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM ── Step 3: Clean previous build artifacts ──────────────────────────────────
echo [3/5] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM ── Step 4: Run PyInstaller ─────────────────────────────────────────────────
echo [4/5] Running PyInstaller...
echo.
pyinstaller --noconfirm RNV_Text_Transformer.spec
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo   BUILD FAILED
    echo ============================================================================
    echo.
    pause
    exit /b 1
)

REM ── Step 5: Report output location ──────────────────────────────────────────
echo.
echo [5/5] Build complete!
echo.
echo ============================================================================
echo   BUILD SUCCEEDED
echo ============================================================================
echo.
echo Output location:
echo     dist\RNV Text Transformer\RNV Text Transformer.exe
echo.
echo To run the built application:
echo     "dist\RNV Text Transformer\RNV Text Transformer.exe"
echo.
echo To create an installer or zip, package the entire folder:
echo     dist\RNV Text Transformer\
echo.

pause
endlocal
