@echo off
C:\Python37\python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt