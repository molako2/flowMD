@echo off
REM ============================================================
REM  flowMD - Demarrage sous Windows
REM  Cree l'environnement, installe les dependances, telecharge
REM  les modeles au premier lancement, puis ouvre l'interface.
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python est introuvable. Installez Python 3.11 ou plus recent
    echo          depuis https://www.python.org/downloads/ ^(cochez "Add to PATH"^).
    pause
    exit /b 1
)

if not exist .venv (
    echo Creation de l'environnement Python...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM Detection automatique d'une installation Tesseract "portable" a cote de flowMD
if exist "%~dp0Tesseract-OCR\tesseract.exe" (
    set "FLOWMD_TESSERACT_CMD=%~dp0Tesseract-OCR\tesseract.exe"
    echo Tesseract detecte : %~dp0Tesseract-OCR\tesseract.exe
)

python -c "import flowmd" >nul 2>nul
if errorlevel 1 (
    echo Installation de flowMD et de ses dependances ^(quelques minutes^)...
    python -m pip install --upgrade pip
    pip install -e .
)

if not exist data\models\docling (
    echo.
    echo Premier lancement : telechargement des modeles d'analyse ^(~2 Go^).
    echo Cette etape n'a lieu qu'une seule fois.
    echo.
    flowmd setup
)

echo.
echo Demarrage de flowMD sur http://127.0.0.1:8000 ...
flowmd serve --open-browser
