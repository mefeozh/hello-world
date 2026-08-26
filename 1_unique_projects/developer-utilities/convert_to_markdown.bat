@echo off
setlocal
:: Change directory to the folder containing this batch script
cd /d "%~dp0"

:: If no arguments are passed, it runs the Python file picker.
:: If a file is dragged & dropped onto this batch script, it passes it as the first argument.
if "%~1" == "" (
    echo Launching file picker...
    .venv\Scripts\python pdf_to_md.py
) else (
    echo Processing dropped file...
    .venv\Scripts\python pdf_to_md.py "%~1"
)

echo.
echo Press any key to exit.
pause >nul
