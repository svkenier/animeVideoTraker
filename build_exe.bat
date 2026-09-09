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
    echo  ======================================================
    echo  ANIME TRACKER v3.1.0 COMPILADO CON EXITO
    echo  ======================================================
    echo.
    echo  NOVEDADES DE LA VERSION 3.1.0:
    echo  - Gestor de Trackers integrado para multiples carpetas.
    echo  - Buscador en tiempo real para filtrar series instantaneamente.
    echo  - Favoritos con estrellas personalizables desde configuracion.
    echo.
    echo  INSTRUCCIONES DE USO:
    echo  1. Ejecuta dist\%EXE_NAME%.exe desde cualquier lugar (es portable y autodesbloqueable).
    echo  2. Presiona "Trackers" para abrir el gestor.
    echo  3. Usa el boton "+ Anadir carpeta a traquear" para importar tus series.
    echo  4. Todos tus datos y logs ahora se resguardan de forma segura en %%APPDATA%%.
    echo  ======================================================
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