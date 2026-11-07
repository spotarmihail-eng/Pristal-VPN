@echo off
cd /d "%~dp0"
py -3 PristalVPN.py
if errorlevel 1 (
  echo.
  echo Could not start Pristal VPN.
  echo Install Python 3.10+ from https://www.python.org/downloads/windows/
  pause
)
