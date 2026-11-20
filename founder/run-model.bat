@echo off
REM اجرا و تست مدل مالی آتیوار
setlocal
python "%~dp0financial_model.py"
if errorlevel 1 exit /b 1
python "%~dp0test_financial_model.py" -v
if errorlevel 1 exit /b 1
echo.
echo OK — model rebuilt and all tests passed.
