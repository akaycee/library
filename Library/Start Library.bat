@echo off
REM ============================================================
REM  Start Library — double-click this file to run the system.
REM  It sets things up on the first run, then opens your browser.
REM  Close the window that appears to stop the system.
REM ============================================================
title Library System
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-library.ps1"
echo.
echo The Library system has stopped.
pause
