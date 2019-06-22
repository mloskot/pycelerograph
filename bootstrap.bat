@echo off
C:\Python36\python -m venv .venv-1.0
call .venv-1.0\Scripts\activate
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt