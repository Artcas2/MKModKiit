@echo off
if exist venv (
  call venv\Scripts\activate.bat
) else (
  if not exist .venv (
    echo Creation d'un environnement virtuel...
    call python -m venv .venv
  )
  call .venv\Scripts\activate.bat
)

pip install -r requirements-dev.txt
pyinstaller --onefile --icon=icon.ico install_tools.py
pause
