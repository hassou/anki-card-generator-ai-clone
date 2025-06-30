@echo off
REM --- run_anki_app.bat ---

REM This script activates your Python virtual environment and then runs your Anki card generation application.
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

echo Activating virtual environment...
call "%PROJECT_ROOT%\%VENV_FOLDER_NAME%\Scripts\activate.bat"

if not exist "%PROJECT_ROOT%\%VENV_FOLDER_NAME%\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found at: "%PROJECT_ROOT%\%VENV_FOLDER_NAME%"
    echo Please ensure PROJECT_ROOT and VENV_FOLDER_NAME are set correctly and the venv exists.
    echo.
    pause
    goto :eof
)

echo.
echo Running Anki_card_gen_ai.main_app...
python -m Anki_card_gen_ai.main_app

echo.
echo Application finished. Deactivating virtual environment...
call deactivate

pause