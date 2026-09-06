@echo off
REM =================================================================
REM  BUILD SCRIPT - Anime & Video Tracker v2.2
REM  Genera AnimeTracker.exe completamente portable
REM =================================================================
setlocal
SET PYTHON=C:\Users\SVKENIER\AppData\Local\Python\bin\python.exe
SET SCRIPT=anime_tracker.py
SET EXE_NAME=AnimeTracker

echo.
echo  ============================================
echo   Anime ^& Video Tracker v2.2  -  Build Tool
echo  ============================================
echo.

"%PYTHON%" -c "import PyInstaller" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo  [*] Instalando PyInstaller...
    "%PYTHON%" -m pip install pyinstaller
)

echo  [*] Compilando %SCRIPT% ^-^> %EXE_NAME%.exe ...
echo.

"%PYTHON%" -m PyInstaller --onefile --windowed --name "%EXE_NAME%" --clean "%SCRIPT%"

echo.
IF EXIST "dist\%EXE_NAME%.exe" (
    echo  [OK] Compilacion exitosa!
    echo  [>>] Ejecutable: dist\%EXE_NAME%.exe
    echo.
    echo  INSTRUCCIONES PORTABLE:
    echo  Copia AnimeTracker.exe a cualquier carpeta con videos y ejecutalo.
    echo  Los archivos .tracker.json y tracker_settings.json se crean ahi mismo.
) ELSE (
    echo  [ERROR] Revisa los mensajes de PyInstaller arriba.
)
echo.
pause
endlocal
