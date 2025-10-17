@echo off
REM Startup script for the App Build Deploy System (Windows)

echo Starting App Build Deploy System...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python database\database.py

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.template to .env and configure your settings.
    echo.
    pause
    exit /b 1
)

REM Start services
echo.
echo Starting services...
echo.

REM Start evaluation API in background
echo Starting evaluation API on port 5001...
start "Evaluation API" cmd /k "venv\Scripts\activate && python evaluation_system\evaluation_api.py"

REM Wait a moment for evaluation API to start
timeout /t 3 /nobreak > nul

REM Start student API
echo Starting student API on port 5000...
echo.
echo System is ready!
echo.
echo Student API: http://localhost:5000
echo Evaluation API: http://localhost:5001
echo Health check: http://localhost:5000/health
echo.
python student_api\app.py

REM Cleanup
echo.
echo Shutting down...
pause