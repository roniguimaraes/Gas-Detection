@echo off
echo Starting gas leak detection system...

echo.
echo Starting Flask backend in .venv (port 5000)...
start "Backend Server" cmd /c "call .venv\Scripts\activate.bat && python backend\app.py"

echo.
echo Waiting for backend to start...
timeout /t 10 /nobreak > nul

echo.
echo Starting manual alert listener (press 'a' key)...
start "Manual Alert" cmd /k python "backend\\manual alert.py"

echo.
echo Waiting for services to initialize...
timeout /t 3 /nobreak > nul

echo.
echo Starting React frontend (port 3000)...
start "Frontend React" cmd /c "cd frontend && npm start"

echo.
echo System started successfully!
echo - Backend: http://localhost:5000 (internal)
echo - Frontend: http://localhost:3000
echo - Manual alerts: Press 'a' in the 'Manual Alert' terminal window
echo - Assuming .venv and dependencies are pre-configured
echo.
echo Press any key to close this terminal...
pause > nul
