@echo off
cd /d "C:\Users\pravijap\OneDrive - Capgemini\Desktop\IITM\app-build-deploy-system"
echo Starting Student API...
echo Current directory: %CD%
python student_api\app.py
pause