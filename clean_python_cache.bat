@echo off
REM RNV Text Transformer - Python Cache Cleaner
REM Removes all __pycache__ directories and .pyc files

echo ================================
echo RNV Text Transformer Cache Cleaner
echo ================================
echo.

echo Removing __pycache__ directories...
for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        echo Deleting: %%i
        rd /s /q "%%i"
    )
)

echo.
echo Removing .pyc files...
for /r %%i in (*.pyc) do (
    if exist "%%i" (
        echo Deleting: %%i
        del /f /q "%%i"
    )
)

echo.
echo ================================
echo Cache cleanup complete!
echo ================================
pause
