@echo off
setlocal

:: ==========================================
:: CONFIGURACIÓN DIRECTA Y CORREGIDA
:: ==========================================
set "SCRIPT=anime_tracker.py"
set "EXE_NAME=AnimeTracker"
set "MAIN_ICON=logo.ico"

:: Buscar la ruta de python instalada en el sistema de forma directa
for /f "delims=" %%i in ('where python 2^>nul') do set "PYTHON_PATH=%%i"

if "%PYTHON_PATH%"=="" (
    for /f "delims=" %%i in ('where py 2^>nul') do set "PYTHON_PATH=%%i"
)

if "%PYTHON_PATH%"=="" (
    echo [ERROR] No se encuentra ningun ejecutable de Python valido en el sistema.
    goto :error
)

echo  [*] Usando Python en: %PYTHON_PATH%
echo  [*] Verificando PyInstaller...
"%PYTHON_PATH%" -c "import PyInstaller" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo  [*] Instalando PyInstaller...
    "%PYTHON_PATH%" -m pip install pyinstaller
)

echo  [*] Compilando %SCRIPT% ^-^> %EXE_NAME%.exe con recursos e iconos...
echo.

:: PyInstaller con 'gear.ico' corregido
"%PYTHON_PATH%" -m PyInstaller --onefile --windowed --name "%EXE_NAME%" --icon="%MAIN_ICON%" --add-data "logo.ico;." --add-data "gear.ico;." --add-data "logo.png;." --clean "%SCRIPT%"

echo.
IF EXIST "dist\%EXE_NAME%.exe" (
    echo  [OK] Compilacion exitosa!
    echo  [>>] Ejecutable: dist\%EXE_NAME%.exe
    echo.
    echo  INSTRUCCIONES PORTABLE:
    echo  Copia AnimeTracker.exe a cualquier carpeta con videos y ejecutalo.
    echo  Los archivos .tracker.json y tracker_settings.json se crean ahi mismo.
) else (
    goto :error
)
goto :end

:error
echo.
echo  [ERROR] Revisa los mensajes anteriores de PyInstaller.
echo.

:end
pause
endlocal