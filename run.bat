@echo off
cd /d "%~dp0"
echo ============================================
echo   REINO PERSISTENTE - PROTOTIPO WEB
echo ============================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale Python 3.11 ou superior em python.org
  echo Marque a opcao "Add Python to PATH" durante a instalacao.
  pause
  exit /b 1
)
if not exist .venv (
  echo Criando ambiente Python...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Abra http://127.0.0.1:5000 no navegador.
echo Para parar o servidor, volte a esta janela e pressione Ctrl+C.
python app.py
pause
