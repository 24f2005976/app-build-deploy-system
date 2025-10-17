@echo off
echo Testing the App Build Deploy System...
echo.

cd /d "C:\Users\pravijap\OneDrive - Capgemini\Desktop\IITM\app-build-deploy-system"

echo Current directory: %CD%
echo.

echo Files in current directory:
dir /b

echo.
echo Files in student_api:
dir /b student_api

echo.
echo Starting Student API...
python student_api\app.py

pause