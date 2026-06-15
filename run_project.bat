@echo off
echo Starting Deepfake Detection Backend API...
echo =======================================================
echo BACKEND API is running on: http://127.0.0.1:5000
echo =======================================================
echo Checking and installing required dependencies...
python -m pip install -r backend/requirements.txt
python -m backend.app
pause
