@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "DEMO_PORT=8080"
if not "%~1"=="" set "DEMO_PORT=%~1"
echo === Travel Agent Web Demo ===
if exist ".venv\Scripts\python.exe" goto dependencies
py -3 -c "import sys; sys.exit(sys.version_info < (3,11))" >nul 2>&1
if errorlevel 1 goto fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto dependencies
:fallback
python -c "import sys; sys.exit(sys.version_info < (3,11))" >nul 2>&1
if errorlevel 1 goto missing
python -m venv .venv
if errorlevel 1 goto failed
:dependencies
".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3,11))"
if errorlevel 1 goto missing
".venv\Scripts\python.exe" -c "import travel_agent.app, jsonschema" >nul 2>&1
if not errorlevel 1 goto launch
echo Đang cài dependencies. Lần đầu cần Internet...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:launch
".venv\Scripts\python.exe" demo\launch_web.py "%DEMO_PORT%"
if errorlevel 1 goto failed
exit /b 0
:missing
echo Cần cài Python 3.11 trở lên rồi chạy lại.
pause
exit /b 1
:failed
echo Không thể khởi động demo. Xem lỗi phía trên.
pause
exit /b 1
