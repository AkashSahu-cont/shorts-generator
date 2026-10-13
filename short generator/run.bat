@echo off
title ShortCraft AI - Creator Studio
echo ========================================================
echo   Launching ShortCraft AI (Client-Side Creator Studio)
echo   Powered by HTML5, CSS3, Modern JavaScript & Canvas
echo ========================================================
echo.

set "INDEX_PATH=%~dp0index.html"

:: Check for Chrome
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app="%INDEX_PATH%" --window-size=1280,940
    exit /b
)

if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --app="%INDEX_PATH%" --window-size=1280,940
    exit /b
)

:: Check for Edge
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app="%INDEX_PATH%" --window-size=1280,940
    exit /b
)

:: Fallback to default browser
start "" "%INDEX_PATH%"
exit /b
