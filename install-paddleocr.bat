@echo off
REM ============================================================
REM  flowMD - Installation du moteur PaddleOCR (PP-OCRv6)
REM  A lancer APRES start.bat, depuis le dossier flowMD.
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist .venv (
    echo [ERREUR] L'environnement flowMD n'existe pas encore.
    echo          Double-cliquez d'abord sur start.bat, puis relancez ce script.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installation du moteur PaddleOCR PP-OCRv6 ^(~1,5 Go^)...
pip install paddlepaddle paddleocr
if errorlevel 1 (
    echo [ERREUR] L'installation a echoue. Verifiez votre connexion Internet.
    pause
    exit /b 1
)

echo.
echo Telechargement des modeles PaddleOCR...
flowmd setup

echo.
echo Termine ! Relancez start.bat : le moteur "PaddleOCR (PP-OCRv6)"
echo apparaitra dans l'interface et sera choisi par le mode Automatique.
pause
