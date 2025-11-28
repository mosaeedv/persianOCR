@echo off
echo ================================
echo   PDF OCR Service - Starting...
echo ================================
echo.
echo Checking Go installation...
go version
if errorlevel 1 (
    echo ERROR: Go is not installed or not in PATH
    echo Please install Go from https://golang.org/dl/
    pause
    exit /b 1
)
echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.
echo Starting server...
echo.
echo Server will be available at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo.
go run backend_file.go
pause
