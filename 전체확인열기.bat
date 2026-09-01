@echo off
python "%~dp0작업파일\확인서버.py"
if errorlevel 1 (
  echo.
  echo [오류] 위 메시지를 확인하세요.
  pause
)
