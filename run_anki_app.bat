@echo off
REM --- run_anki_app.bat ---

REM This script activates your Python virtual environment and then runs your Anki card generation application.
REM It will automatically create the virtual environment and install dependencies if they don't exist.
REM You can place this file anywhere and run it from any directory.

REM ######################################################################################################
REM ### IMPORTANT: Configure these two variables to match your setup #####################################
REM ######################################################################################################

REM 1. Set PROJECT_ROOT to the absolute path of your project's main directory.
REM    This is the directory that contains both your 'venv' folder and the 'Anki_card_gen_ai' package folder.
set "PROJECT_ROOT=%~dp0"

REM 2. Set VENV_FOLDER_NAME if your virtual environment is named something other than 'venv'.
set "VENV_FOLDER_NAME=venv"

REM ######################################################################################################
REM ### Do not modify below this line unless you know what you're doing #################################
REM ######################################################################################################

set "VENV_PATH=%PROJECT_ROOT%\%VENV_FOLDER_NAME%"
set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"
set "ACTIVATE_SCRIPT=%VENV_PATH%\Scripts\activate.bat"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%\requirements.txt"

echo Checking for virtual environment...
if not exist "%PYTHON_EXE%" (
    echo Virtual environment not found. Creating one...
    python -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment.
        echo Please ensure Python is installed and added to your PATH.
        echo.
        pause
        goto :eof
    )
    echo Virtual environment created.
) else (
    echo Virtual environment found.
)

echo Activating virtual environment...
call "%ACTIVATE_SCRIPT%"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to activate virtual environment.
    echo.
    pause
    goto :eof
)

echo Checking for dependencies...
if exist "%REQUIREMENTS_FILE%" (
    echo Installing/updating dependencies from %REQUIREMENTS_FILE%...
    pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        echo.
        pause
        goto :eof
    )
    echo Dependencies installed.
) else (
    echo No requirements.txt found. Skipping dependency installation.
)

echo.
echo Running Anki_card_gen_ai.main_app...
python -m Anki_card_gen_ai.main_app

echo.
echo Application finished. Deactivating virtual environment...
call deactivate

pause